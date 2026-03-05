"""
wazuh/orchestrator.py — Push-Based Automation Engine
------------------------------------------------------
WazuhOrchestrator runs as an asyncio background task started on
FastAPI startup. Every POLL_INTERVAL_SECONDS it:

    1. Fetches High/Critical alerts from Wazuh.
    2. For any alert at Level 15 (Wazuh's maximum):
         a. Checks whitelist — skip if whitelisted.
         b. Checks DB — skip if already blocked.
         c. Auto-triggers firewall-drop via active response.
         d. Logs the action with triggered_by='auto'.
    3. Sleeps until the next cycle.

On Wazuh offline — logs a warning and retries on the next cycle;
does NOT crash the FastAPI app.

Usage (in main.py startup_event):
    orchestrator = WazuhOrchestrator(supabase_client)
    asyncio.create_task(orchestrator.run())
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from .auth import wazuh_auth, WazuhOfflineError
from .alerts import get_critical_alerts
from .agents import trigger_active_response, get_active_blocks
from .whitelist import is_whitelisted

logger = logging.getLogger(__name__)

# Poll Wazuh every 15 seconds
POLL_INTERVAL_SECONDS = 15

# Only auto-block at the highest Wazuh severity level (15 = critical threat)
AUTO_BLOCK_LEVEL_THRESHOLD = 15


class WazuhOrchestrator:
    """
    Async background worker that implements push-based automated response.
    Instantiate once and await orchestrator.run() as an asyncio task.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self._running = False
        self._cycle_count = 0
        self._auto_blocks_this_session = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Main polling loop. Call via asyncio.create_task(orchestrator.run())."""
        self._running = True
        logger.info(
            "WazuhOrchestrator started. Poll interval: %ds, Auto-block threshold: Level %d.",
            POLL_INTERVAL_SECONDS, AUTO_BLOCK_LEVEL_THRESHOLD,
        )

        while self._running:
            self._cycle_count += 1
            try:
                await self._poll_and_respond()
            except Exception as exc:
                # Safety net — never let an unhandled exception kill the loop
                logger.error(
                    "Orchestrator cycle %d encountered an unexpected error: %s",
                    self._cycle_count, exc, exc_info=True,
                )
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    def stop(self) -> None:
        """Graceful shutdown — the current sleep will be the last one."""
        logger.info("WazuhOrchestrator stopping after current cycle.")
        self._running = False

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "cycles": self._cycle_count,
            "auto_blocks_this_session": self._auto_blocks_this_session,
            "poll_interval_seconds": POLL_INTERVAL_SECONDS,
            "auto_block_level_threshold": AUTO_BLOCK_LEVEL_THRESHOLD,
        }

    # ------------------------------------------------------------------
    # Internal logic
    # ------------------------------------------------------------------

    async def _poll_and_respond(self) -> None:
        """Single orchestration cycle."""
        logger.debug("Orchestrator cycle %d: fetching alerts ...", self._cycle_count)

        try:
            payload = await get_critical_alerts(wazuh_auth, time_range="15m")
        except WazuhOfflineError as exc:
            logger.warning(
                "Orchestrator cycle %d: Wazuh is offline — %s. Will retry.",
                self._cycle_count, exc,
            )
            return

        alerts = payload.get("alerts", [])
        incidents = payload.get("incidents", [])

        # Evaluate individual alerts at Level 15
        for alert in alerts:
            await self._evaluate_alert(alert)

        # Evaluate correlated incidents — if an incident peak level = 15, auto-block
        for incident in incidents:
            if incident.get("peak_level", 0) >= AUTO_BLOCK_LEVEL_THRESHOLD:
                await self._evaluate_incident(incident)

    async def _evaluate_alert(self, alert: dict) -> None:
        """Check a single alert and auto-block if it meets the threshold."""
        level = alert.get("rule", {}).get("level", 0)
        if level < AUTO_BLOCK_LEVEL_THRESHOLD:
            return

        source_ip = alert.get("source_ip")
        if not source_ip:
            logger.debug("Level 15 alert has no source IP — cannot auto-block.")
            return

        agent_id = alert.get("agent", {}).get("id", "001")
        rule_desc = alert.get("rule", {}).get("description", "")

        logger.warning(
            "Orchestrator: Level 15 alert detected! "
            "source_ip=%s agent=%s rule='%s'. Auto-blocking...",
            source_ip, agent_id, rule_desc,
        )

        await self._auto_block(source_ip, agent_id)

    async def _evaluate_incident(self, incident: dict) -> None:
        """Auto-block the source IP of a correlated incident."""
        source_ip = incident.get("source_ip")
        agent_ids = incident.get("agent_ids", ["001"])
        agent_id = agent_ids[0] if agent_ids else "001"

        logger.warning(
            "Orchestrator: Critical incident detected! "
            "source_ip=%s count=%d peak_level=%d. Auto-blocking...",
            source_ip, incident.get("count", 0), incident.get("peak_level", 0),
        )

        await self._auto_block(source_ip, agent_id)

    async def _auto_block(self, ip: str, agent_id: str) -> None:
        """Invoke active response and handle errors gracefully."""
        try:
            result = await trigger_active_response(
                auth=wazuh_auth,
                agent_id=agent_id,
                ip_to_block=ip,
                supabase_client=self.supabase,
                triggered_by="auto",
            )
            if result.get("status") == "blocked":
                self._auto_blocks_this_session += 1
                logger.warning(
                    "AUTO-BLOCK SUCCESS: %s blocked on agent %s at %s.",
                    ip, agent_id, datetime.now(timezone.utc).isoformat(),
                )
            else:
                logger.info("Auto-block skipped for %s: %s", ip, result.get("status"))
        except Exception as exc:
            # 403 (critical infra) or 503 (offline) — log and move on
            logger.error("Auto-block FAILED for %s: %s", ip, exc)
