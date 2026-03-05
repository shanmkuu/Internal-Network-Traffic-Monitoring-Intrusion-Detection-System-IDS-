"""
wazuh/alerts.py — Alert Poller + Correlator
--------------------------------------------
Fetches High/Critical alerts from Wazuh (rule.level > 10),
runs them through the correlation engine (groups bursts from
the same IP into Security Incidents), applies the whitelist,
maps MITRE ATT&CK IDs to human-readable tactics, and returns
a structured "Bento Box" JSON payload for the dashboard.

Color token scheme (for the frontend):
    crimson  — levels 12-15  (Critical)
    amber    — levels 7-11   (High)
    info     — levels 1-6    (kept only for context, hidden by default)
"""

import logging
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import httpx

from .auth import WazuhAuthService, WazuhOfflineError
from .whitelist import is_whitelisted

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# MITRE ATT&CK ID → Tactic + Technique lookup table
# Coverage: the most common technique IDs seen in Wazuh rule sets.
# Extend as needed.
# ------------------------------------------------------------------

MITRE_TACTIC_MAP: dict[str, dict[str, str]] = {
    # Reconnaissance
    "T1595": {"tactic": "Reconnaissance",       "technique": "Active Scanning"},
    "T1592": {"tactic": "Reconnaissance",       "technique": "Gather Victim Host Info"},
    # Resource Development
    "T1587": {"tactic": "Resource Development", "technique": "Develop Capabilities"},
    # Initial Access
    "T1190": {"tactic": "Initial Access",       "technique": "Exploit Public-Facing Application"},
    "T1133": {"tactic": "Initial Access",       "technique": "External Remote Services"},
    "T1078": {"tactic": "Initial Access",       "technique": "Valid Accounts"},
    "T1566": {"tactic": "Initial Access",       "technique": "Phishing"},
    # Execution
    "T1059": {"tactic": "Execution",            "technique": "Command and Scripting Interpreter"},
    "T1203": {"tactic": "Execution",            "technique": "Exploitation for Client Execution"},
    "T1569": {"tactic": "Execution",            "technique": "System Services"},
    "T1204": {"tactic": "Execution",            "technique": "User Execution"},
    # Persistence
    "T1053": {"tactic": "Persistence",          "technique": "Scheduled Task/Job"},
    "T1543": {"tactic": "Persistence",          "technique": "Create or Modify System Process"},
    "T1546": {"tactic": "Persistence",          "technique": "Event Triggered Execution"},
    "T1136": {"tactic": "Persistence",          "technique": "Create Account"},
    # Privilege Escalation
    "T1548": {"tactic": "Privilege Escalation", "technique": "Abuse Elevation Control Mechanism"},
    "T1068": {"tactic": "Privilege Escalation", "technique": "Exploitation for Privilege Escalation"},
    "T1055": {"tactic": "Privilege Escalation", "technique": "Process Injection"},
    # Defense Evasion
    "T1070": {"tactic": "Defense Evasion",      "technique": "Indicator Removal on Host"},
    "T1027": {"tactic": "Defense Evasion",      "technique": "Obfuscated Files or Information"},
    "T1562": {"tactic": "Defense Evasion",      "technique": "Impair Defenses"},
    # Credential Access
    "T1110": {"tactic": "Credential Access",    "technique": "Brute Force"},
    "T1003": {"tactic": "Credential Access",    "technique": "OS Credential Dumping"},
    "T1552": {"tactic": "Credential Access",    "technique": "Unsecured Credentials"},
    # Discovery
    "T1046": {"tactic": "Discovery",            "technique": "Network Service Scanning"},
    "T1082": {"tactic": "Discovery",            "technique": "System Information Discovery"},
    "T1083": {"tactic": "Discovery",            "technique": "File and Directory Discovery"},
    "T1057": {"tactic": "Discovery",            "technique": "Process Discovery"},
    # Lateral Movement
    "T1021": {"tactic": "Lateral Movement",     "technique": "Remote Services"},
    "T1210": {"tactic": "Lateral Movement",     "technique": "Exploitation of Remote Services"},
    "T1534": {"tactic": "Lateral Movement",     "technique": "Internal Spearphishing"},
    # Collection
    "T1005": {"tactic": "Collection",           "technique": "Data from Local System"},
    "T1074": {"tactic": "Collection",           "technique": "Data Staged"},
    "T1560": {"tactic": "Collection",           "technique": "Archive Collected Data"},
    # Command and Control
    "T1071": {"tactic": "Command and Control",  "technique": "Application Layer Protocol"},
    "T1095": {"tactic": "Command and Control",  "technique": "Non-Application Layer Protocol"},
    "T1105": {"tactic": "Command and Control",  "technique": "Ingress Tool Transfer"},
    # Exfiltration
    "T1041": {"tactic": "Exfiltration",         "technique": "Exfiltration Over C2 Channel"},
    "T1048": {"tactic": "Exfiltration",         "technique": "Exfiltration Over Alternative Protocol"},
    # Impact
    "T1499": {"tactic": "Impact",               "technique": "Endpoint Denial of Service"},
    "T1498": {"tactic": "Impact",               "technique": "Network Denial of Service"},
    "T1486": {"tactic": "Impact",               "technique": "Data Encrypted for Impact"},
    "T1490": {"tactic": "Impact",               "technique": "Inhibit System Recovery"},
}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _color_token(level: int) -> str:
    if level >= 12:
        return "crimson"
    if level >= 7:
        return "amber"
    return "info"


def _severity_label(level: int) -> str:
    if level >= 12:
        return "Critical"
    if level >= 7:
        return "High"
    if level >= 4:
        return "Medium"
    return "Low"


def _map_mitre(mitre_ids: list[str]) -> dict[str, str]:
    """Return the first known MITRE tactic/technique from a list of IDs."""
    for mid in mitre_ids:
        entry = MITRE_TACTIC_MAP.get(mid)
        if entry:
            return {"mitre_id": mid, **entry}
    # Unknown or unmapped
    first = mitre_ids[0] if mitre_ids else "N/A"
    return {"mitre_id": first, "tactic": "Unknown", "technique": "Unknown"}


def _extract_source_ip(alert: dict) -> str | None:
    """Extract source IP from various Wazuh alert locations."""
    return (
        alert.get("data", {}).get("srcip")
        or alert.get("data", {}).get("src_ip")
        or alert.get("syscheck", {}).get("path")  # fallback
        or None
    )


def _clean_alert(raw: dict) -> dict:
    """Transform a raw Wazuh alert dict into a UI-ready object."""
    rule = raw.get("rule", {})
    agent = raw.get("agent", {})
    level = int(rule.get("level", 0))
    mitre_ids: list[str] = rule.get("mitre", {}).get("id", [])
    if isinstance(mitre_ids, str):
        mitre_ids = [mitre_ids]

    source_ip = _extract_source_ip(raw)

    return {
        "id": raw.get("id", ""),
        "timestamp": raw.get("timestamp", ""),
        "agent": {
            "id": agent.get("id", "000"),
            "name": agent.get("name", "manager"),
            "ip": agent.get("ip", ""),
        },
        "rule": {
            "id": str(rule.get("id", "")),
            "level": level,
            "description": rule.get("description", ""),
            "severity_label": _severity_label(level),
            "groups": rule.get("groups", []),
        },
        "threat": _map_mitre(mitre_ids),
        "source_ip": source_ip,
        "color_token": _color_token(level),
        "detection_certainty": "confirmed",
        "full_log": raw.get("full_log", ""),
    }


# ------------------------------------------------------------------
# Core fetch function
# ------------------------------------------------------------------

WAZUH_BASE_URL = os.getenv("WAZUH_BASE_URL", "https://localhost:55000").rstrip("/")
INCIDENT_THRESHOLD = 5          # alerts from the same IP within the window = incident
TIMEOUT_SECONDS = 15


async def get_critical_alerts(
    auth: WazuhAuthService,
    time_range: str = "1h",
    max_alerts: int = 200,
) -> dict[str, Any]:
    """
    Fetch High/Critical alerts (level > 10) from Wazuh, correlate, and
    return a Bento Box payload ready for the dashboard.

    Args:
        auth:        WazuhAuthService instance providing JWT headers.
        time_range:  Elasticsearch-style range string: '1h', '30m', '24h'.
        max_alerts:  Max raw alerts to pull per request.

    Returns:
        {
            "summary": { total, critical, high, incidents, whitelisted },
            "alerts":  [ ... cleaned alert objects ... ],
            "incidents": [ ... correlated incident objects ... ]
        }
    """
    headers = await auth.get_headers()
    url = f"{WAZUH_BASE_URL}/alerts"
    params = {
        "limit": max_alerts,
        "sort": "-timestamp",
        "q": "rule.level>10",
        # The Wazuh indexer API supports a 'time_range' or date filter;
        # adjust to your Wazuh version's exact param name if needed.
        "time_range": time_range,
    }

    try:
        async with httpx.AsyncClient(verify=False, timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
        logger.error("Could not fetch alerts from Wazuh: %s", exc)
        raise WazuhOfflineError("Wazuh Manager is offline or unreachable.") from exc
    except httpx.HTTPStatusError as exc:
        logger.error("Wazuh alerts endpoint error %s: %s", exc.response.status_code, exc.response.text)
        raise WazuhOfflineError(f"Wazuh returned HTTP {exc.response.status_code}.") from exc

    raw_alerts: list[dict] = response.json().get("data", {}).get("affected_items", [])

    # ------------------------------------------------------------------
    # Step 1 — Whitelist filtering
    # ------------------------------------------------------------------
    clean_alerts = []
    whitelisted_count = 0
    for raw in raw_alerts:
        if is_whitelisted(raw):
            whitelisted_count += 1
            continue
        clean_alerts.append(_clean_alert(raw))

    # ------------------------------------------------------------------
    # Step 2 — Correlation: group ≥INCIDENT_THRESHOLD alerts per source IP
    # ------------------------------------------------------------------
    ip_buckets: dict[str, list[dict]] = defaultdict(list)
    for alert in clean_alerts:
        if alert["source_ip"]:
            ip_buckets[alert["source_ip"]].append(alert)

    incidents: list[dict] = []
    non_incident_alerts: list[dict] = []

    for ip, bucket in ip_buckets.items():
        if len(bucket) >= INCIDENT_THRESHOLD:
            # Build a single Security Incident object
            timestamps = [a["timestamp"] for a in bucket if a["timestamp"]]
            tactics = list({a["threat"]["tactic"] for a in bucket if a["threat"]["tactic"] != "Unknown"})
            severity_levels = [a["rule"]["level"] for a in bucket]
            incidents.append({
                "source_ip": ip,
                "count": len(bucket),
                "first_seen": min(timestamps) if timestamps else "",
                "last_seen": max(timestamps) if timestamps else "",
                "tactics": tactics,
                "peak_level": max(severity_levels),
                "color_token": _color_token(max(severity_levels)),
                "agent_ids": list({a["agent"]["id"] for a in bucket}),
            })
        else:
            non_incident_alerts.extend(bucket)

    # Also include alerts without a source IP in the list
    for alert in clean_alerts:
        if not alert["source_ip"]:
            non_incident_alerts.append(alert)

    # ------------------------------------------------------------------
    # Step 3 — Summary counts
    # ------------------------------------------------------------------
    critical_count = sum(1 for a in clean_alerts if a["rule"]["level"] >= 12)
    high_count = sum(1 for a in clean_alerts if 7 <= a["rule"]["level"] < 12)

    return {
        "summary": {
            "total": len(clean_alerts),
            "critical": critical_count,
            "high": high_count,
            "incidents": len(incidents),
            "whitelisted_suppressed": whitelisted_count,
        },
        "alerts": non_incident_alerts,
        "incidents": incidents,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "time_range": time_range,
    }
