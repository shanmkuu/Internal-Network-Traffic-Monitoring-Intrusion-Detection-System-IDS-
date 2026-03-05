"""
wazuh/agents.py — Agent Management & Active Response
------------------------------------------------------
Provides:
    - get_agent_summary()       — Live agent count stats from Wazuh
    - get_active_blocks()       — Active IP ban list from Supabase
    - trigger_active_response() — Block an IP with pre-flight checks
                                  and Supabase audit logging

Pre-flight check order (trigger_active_response):
    1. Reject if IP is critical infrastructure (gateway, DNS, DC)
    2. Reject if IP already has an active block in the DB
    3. Send 'firewall-drop' to Wazuh active response
    4. Log the block to Supabase wazuh_blocks table
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException

from .auth import WazuhAuthService, WazuhOfflineError
from .whitelist import is_critical_infrastructure, check_existing_blocks

logger = logging.getLogger(__name__)

WAZUH_BASE_URL = os.getenv("WAZUH_BASE_URL", "https://localhost:55000").rstrip("/")
TIMEOUT_SECONDS = 15


# ======================================================================
# Agent Summary
# ======================================================================

async def get_agent_summary(auth: WazuhAuthService) -> dict[str, Any]:
    """
    Call GET /agents/summary/status and return a clean summary dict.

    Returns:
        {
            "total": int,
            "active": int,
            "disconnected": int,
            "pending": int,
            "never_connected": int
        }
    """
    headers = await auth.get_headers()
    url = f"{WAZUH_BASE_URL}/agents/summary/status"

    try:
        async with httpx.AsyncClient(verify=False, timeout=TIMEOUT_SECONDS) as client:
            resp = await client.get(url, headers=headers)
        resp.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
        raise WazuhOfflineError("Wazuh Manager is offline or unreachable.") from exc
    except httpx.HTTPStatusError as exc:
        raise WazuhOfflineError(f"Wazuh returned HTTP {exc.response.status_code}.") from exc

    data = resp.json().get("data", {})
    connection = data.get("connection", {})

    return {
        "total": data.get("agents_count", 0),
        "active": connection.get("active", 0),
        "disconnected": connection.get("disconnected", 0),
        "pending": connection.get("pending", 0),
        "never_connected": connection.get("never_connected", 0),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# ======================================================================
# Active Blocks — Supabase query
# ======================================================================

async def get_active_blocks(supabase_client) -> list[dict]:
    """
    Fetch the 'wazuh_blocks' table from Supabase and return all active bans.
    Falls back to an empty list if the table doesn't exist yet.
    """
    if supabase_client is None:
        return []
    try:
        resp = (
            supabase_client.table("wazuh_blocks")
            .select("*")
            .eq("status", "active")
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        logger.error("Failed to query wazuh_blocks: %s", exc)
        return []


# ======================================================================
# Active Response — IP Block
# ======================================================================

async def trigger_active_response(
    auth: WazuhAuthService,
    agent_id: str,
    ip_to_block: str,
    supabase_client=None,
    triggered_by: str = "manual",
) -> dict[str, Any]:
    """
    Block an IP on a specific Wazuh agent using the 'firewall-drop'
    active response script.

    Pre-checks (in order):
        1. Refuse if IP is critical infrastructure.
        2. Refuse if IP is already actively blocked (idempotent).
        3. Call PUT /active-response on the Wazuh API.
        4. Log the action to Supabase wazuh_blocks.

    Args:
        auth:            WazuhAuthService providing headers.
        agent_id:        Agent to send the command to (e.g. "001").
        ip_to_block:     IPv4 address to block.
        supabase_client: Optional Supabase client for audit logging.
        triggered_by:    "manual" | "auto" (set to "auto" by orchestrator).

    Returns:
        {"status": "blocked" | "already_mitigated", "ip": ..., "agent_id": ...}
    """

    # ------------------------------------------------------------------
    # Pre-check 1: Critical infrastructure guard
    # ------------------------------------------------------------------
    if is_critical_infrastructure(ip_to_block):
        logger.warning(
            "Active response REFUSED: %s is critical infrastructure.", ip_to_block
        )
        raise HTTPException(
            status_code=403,
            detail=f"Cannot block {ip_to_block}: it is a protected critical infrastructure asset.",
        )

    # ------------------------------------------------------------------
    # Pre-check 2: Already blocked?
    # ------------------------------------------------------------------
    existing_blocks = await get_active_blocks(supabase_client)
    if check_existing_blocks(ip_to_block, existing_blocks):
        logger.info("IP %s is already mitigated — skipping duplicate block.", ip_to_block)
        return {
            "status": "already_mitigated",
            "ip": ip_to_block,
            "agent_id": agent_id,
            "message": f"{ip_to_block} is already actively blocked.",
        }

    # ------------------------------------------------------------------
    # Step 3: Send Wazuh active response command
    # ------------------------------------------------------------------
    headers = await auth.get_headers()
    url = f"{WAZUH_BASE_URL}/active-response"
    payload = {
        "command": "firewall-drop",
        "custom": False,
        "arguments": [ip_to_block],
        "agents_list": [agent_id],
    }

    try:
        async with httpx.AsyncClient(verify=False, timeout=TIMEOUT_SECONDS) as client:
            resp = await client.put(url, headers=headers, json=payload)
        resp.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
        raise WazuhOfflineError("Wazuh Manager is offline — cannot execute active response.") from exc
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Active response failed. HTTP %s: %s",
            exc.response.status_code, exc.response.text
        )
        raise HTTPException(
            status_code=502,
            detail=f"Wazuh returned HTTP {exc.response.status_code} on active-response.",
        ) from exc

    logger.info(
        "Active response 'firewall-drop' sent for IP %s on agent %s (triggered_by=%s).",
        ip_to_block, agent_id, triggered_by,
    )

    # ------------------------------------------------------------------
    # Step 4: Log to Supabase wazuh_blocks
    # ------------------------------------------------------------------
    await _log_block_to_db(supabase_client, ip_to_block, agent_id, triggered_by)

    return {
        "status": "blocked",
        "ip": ip_to_block,
        "agent_id": agent_id,
        "triggered_by": triggered_by,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"firewall-drop command sent for {ip_to_block} on agent {agent_id}.",
    }


# ======================================================================
# Internal helpers
# ======================================================================

async def _log_block_to_db(
    supabase_client,
    ip: str,
    agent_id: str,
    triggered_by: str,
) -> None:
    """Persist the block action to the wazuh_blocks Supabase table."""
    if supabase_client is None:
        logger.warning("No Supabase client — block action not logged to DB.")
        return
    try:
        supabase_client.table("wazuh_blocks").insert({
            "ip": ip,
            "agent_id": agent_id,
            "triggered_by": triggered_by,
            "status": "active",
        }).execute()
        logger.info("Block logged to DB: %s (agent %s, by %s).", ip, agent_id, triggered_by)
    except Exception as exc:
        # Non-fatal — the block was sent, just not logged
        logger.error("Failed to log block to Supabase: %s", exc)
