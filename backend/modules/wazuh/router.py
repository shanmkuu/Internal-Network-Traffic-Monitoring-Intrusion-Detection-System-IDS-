"""
wazuh/router.py — FastAPI APIRouter for Wazuh endpoints
---------------------------------------------------------
Mount with:
    from backend.modules.wazuh.router import wazuh_router
    app.include_router(wazuh_router)

All endpoints are async, use httpx under the hood, and return
HTTP 503 on WazuhOfflineError so the UI can display a clean
"Wazuh Manager Offline" state instead of a 500.

Endpoints:
    GET  /api/wazuh/health            — Dual health check (FastAPI + Wazuh)
    GET  /api/wazuh/alerts            — Correlated Bento Box alert feed
    GET  /api/wazuh/agents/summary    — Agent count summary
    GET  /api/wazuh/blocks            — Active IP ban list
    POST /api/wazuh/active-response   — Block an IP with pre-checks
    POST /api/wazuh/whitelist/reload  — Hot-reload whitelist.json from disk
    GET  /api/wazuh/orchestrator/stats — Automation engine stats
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .auth import wazuh_auth, WazuhOfflineError
from .alerts import get_critical_alerts
from .agents import get_agent_summary, get_active_blocks, trigger_active_response
from .whitelist import reload_whitelist

logger = logging.getLogger(__name__)

wazuh_router = APIRouter(prefix="/api/wazuh", tags=["Wazuh IDS"])

# Orchestrator instance reference — set by main.py after it is created
_orchestrator_ref = None


def set_orchestrator(orchestrator):
    """Called by main.py so the router can expose orchestrator stats."""
    global _orchestrator_ref
    _orchestrator_ref = orchestrator


# ------------------------------------------------------------------
# Dependency: Supabase client from main app state
# ------------------------------------------------------------------

def get_supabase():
    """
    Import the Supabase client that was initialised in main.py.
    Falls back to None gracefully if not configured.
    """
    try:
        # main.py assigns this after creating the FastAPI app
        from main import supabase  # noqa: PLC0415
        return supabase
    except ImportError:
        try:
            from backend.main import supabase  # noqa: PLC0415
            return supabase
        except ImportError:
            return None


# ------------------------------------------------------------------
# Pydantic request/response models
# ------------------------------------------------------------------

class ActiveResponseRequest(BaseModel):
    agent_id: str = Field(..., description="Wazuh agent ID to send the command to, e.g. '001'")
    ip: str = Field(..., description="IPv4 address to block via firewall-drop")


class HealthResponse(BaseModel):
    fastapi: str = "ok"
    wazuh: str
    wazuh_version: Optional[str] = None
    message: Optional[str] = None


# ------------------------------------------------------------------
# Shared error handler
# ------------------------------------------------------------------

def _raise_503(exc: WazuhOfflineError) -> None:
    raise HTTPException(
        status_code=503,
        detail=str(exc) or "Wazuh Manager is offline or unreachable.",
    )


# ==================================================================
# Endpoints
# ==================================================================

@wazuh_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check — FastAPI + Wazuh connectivity",
)
async def health_check():
    """
    Returns the liveness status of both the API server and the Wazuh Manager.
    Safe to poll from monitoring tools (e.g. UptimeRobot).
    """
    try:
        version = await wazuh_auth.get_wazuh_version()
        return HealthResponse(
            fastapi="ok",
            wazuh="online",
            wazuh_version=version,
        )
    except WazuhOfflineError as exc:
        # Don't raise — return a 200 with an offline indicator so
        # the UI gets a clean status, not an error page.
        return HealthResponse(
            fastapi="ok",
            wazuh="offline",
            message=str(exc),
        )


@wazuh_router.get(
    "/alerts",
    summary="Fetch High/Critical alerts — Bento Box format",
)
async def get_alerts(
    time_range: str = Query(
        default="1h",
        description="Time window for alert query: '30m', '1h', '6h', '24h'",
    ),
    max_alerts: int = Query(
        default=200,
        ge=10,
        le=1000,
        description="Maximum raw alerts to retrieve from Wazuh",
    ),
):
    """
    Returns alerts with rule.level > 10 (High and Critical only).
    Alerts from the same source IP are correlated into Security Incidents.
    Whitelist-filtered alerts are suppressed before reaching the response.
    """
    try:
        return await get_critical_alerts(wazuh_auth, time_range=time_range, max_alerts=max_alerts)
    except WazuhOfflineError as exc:
        _raise_503(exc)


@wazuh_router.get(
    "/agents/summary",
    summary="Agent count summary",
)
async def agents_summary():
    """
    Returns live agent status counts from the Wazuh Manager:
    total, active, disconnected, pending, never_connected.
    """
    try:
        return await get_agent_summary(wazuh_auth)
    except WazuhOfflineError as exc:
        _raise_503(exc)


@wazuh_router.get(
    "/blocks",
    summary="Active IP ban list",
)
async def active_blocks(supabase=Depends(get_supabase)):
    """
    Returns all IPs currently in the 'active' state in the wazuh_blocks table.
    Includes whether the block was triggered manually or automatically.
    """
    blocks = await get_active_blocks(supabase)
    return {"count": len(blocks), "blocks": blocks}


@wazuh_router.post(
    "/active-response",
    summary="Block an IP via Wazuh active response (firewall-drop)",
)
async def active_response(
    body: ActiveResponseRequest,
    supabase=Depends(get_supabase),
):
    """
    Sends a `firewall-drop` active response to a specific Wazuh agent.

    Pre-checks performed before executing:
    1. Refuses if the IP is a protected critical infrastructure asset.
    2. Returns 'already_mitigated' if the IP is already actively blocked.

    The action is logged to the `wazuh_blocks` Supabase table for audit.
    """
    try:
        return await trigger_active_response(
            auth=wazuh_auth,
            agent_id=body.agent_id,
            ip_to_block=body.ip,
            supabase_client=supabase,
            triggered_by="manual",
        )
    except WazuhOfflineError as exc:
        _raise_503(exc)
    # HTTPException from pre-checks (403) propagates naturally


@wazuh_router.post(
    "/whitelist/reload",
    summary="Hot-reload whitelist.json without restarting the server",
)
async def reload_whitelist_endpoint():
    """
    Re-reads whitelist.json and critical_infrastructure.json from disk.
    No server restart required after editing these files.
    """
    reload_whitelist()
    return {"status": "ok", "message": "Whitelist reloaded from disk."}


@wazuh_router.get(
    "/orchestrator/stats",
    summary="Automation engine statistics",
)
async def orchestrator_stats():
    """
    Returns runtime statistics for the WazuhOrchestrator background task:
    cycle count, auto-blocks issued this session, running status.
    """
    if _orchestrator_ref is None:
        return {"status": "not_started", "detail": "Orchestrator has not been initialised."}
    return _orchestrator_ref.stats
