"""
wazuh/whitelist.py — False Positive Suppressor
-----------------------------------------------
Loads a list of known-safe IPs and rule IDs from whitelist.json
(in the same directory). Alerts that match are given a
detection_certainty of 'whitelisted' and are excluded before
they reach the UI.

To add exceptions, edit whitelist.json — no code changes needed.

File format (whitelist.json):
{
  "safe_ips":     ["10.0.0.1", "10.0.0.2"],
  "safe_rule_ids": ["100001", "100002"],
  "safe_agent_ids": ["000"]
}
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_WHITELIST_PATH = os.path.join(os.path.dirname(__file__), "whitelist.json")
_CRITICAL_INFRA_PATH = os.path.join(os.path.dirname(__file__), "critical_infrastructure.json")

# ------------------------------------------------------------------
# Load whitelist at module import (fast path on every alert check)
# ------------------------------------------------------------------

def _load_json_safe(path: str, default: dict) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Config file not found: %s — using defaults.", path)
        return default
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse %s: %s — using defaults.", path, exc)
        return default


def _reload() -> tuple[set, set, set, set]:
    wl = _load_json_safe(_WHITELIST_PATH, {})
    ci = _load_json_safe(_CRITICAL_INFRA_PATH, {})
    safe_ips = set(wl.get("safe_ips", []))
    safe_rule_ids = set(str(r) for r in wl.get("safe_rule_ids", []))
    safe_agent_ids = set(str(a) for a in wl.get("safe_agent_ids", []))
    critical_ips = set(ci.get("protected_ips", []))
    return safe_ips, safe_rule_ids, safe_agent_ids, critical_ips


SAFE_IPS, SAFE_RULE_IDS, SAFE_AGENT_IDS, CRITICAL_IPS = _reload()


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def is_whitelisted(alert: dict[str, Any]) -> bool:
    """
    Return True if this alert should be suppressed (known false positive).
    Checks source IP, rule ID, and agent ID.
    """
    source_ip = alert.get("source_ip") or _deep_get(alert, "data", "srcip")
    rule_id = str(_deep_get(alert, "rule", "id") or "")
    agent_id = str(_deep_get(alert, "agent", "id") or "")

    if source_ip in SAFE_IPS:
        logger.debug("Alert suppressed: IP %s is whitelisted.", source_ip)
        return True
    if rule_id and rule_id in SAFE_RULE_IDS:
        logger.debug("Alert suppressed: Rule %s is whitelisted.", rule_id)
        return True
    if agent_id and agent_id in SAFE_AGENT_IDS:
        logger.debug("Alert suppressed: Agent %s is whitelisted.", agent_id)
        return True
    return False


def is_critical_infrastructure(ip: str) -> bool:
    """
    Return True if this IP is a protected asset (gateway, DNS, DC).
    Blocking these should be refused by the active-response endpoint.
    """
    return ip in CRITICAL_IPS


def check_existing_blocks(ip: str, active_blocks: list[dict]) -> bool:
    """
    Return True if `ip` already appears in the active blocks list
    fetched from Supabase. Prevents duplicate firewall rules.
    """
    return any(block.get("ip") == ip and block.get("status") == "active"
               for block in active_blocks)


def reload_whitelist() -> None:
    """Hot-reload whitelist from disk (e.g. after editing whitelist.json)."""
    global SAFE_IPS, SAFE_RULE_IDS, SAFE_AGENT_IDS, CRITICAL_IPS
    SAFE_IPS, SAFE_RULE_IDS, SAFE_AGENT_IDS, CRITICAL_IPS = _reload()
    logger.info(
        "Whitelist reloaded: %d safe IPs, %d safe rules, %d critical IPs.",
        len(SAFE_IPS), len(SAFE_RULE_IDS), len(CRITICAL_IPS),
    )


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

def _deep_get(d: dict, *keys, default=None):
    """Safely traverse a nested dict."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d
