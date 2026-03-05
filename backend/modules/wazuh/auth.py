"""
wazuh/auth.py — WazuhAuthService
---------------------------------
Handles JWT authentication with the Wazuh Manager REST API.
Uses httpx.AsyncClient (non-blocking) and caches the token to
avoid hammering the auth endpoint on every call.

Environment variables required:
    WAZUH_BASE_URL   e.g. https://192.168.1.100:55000
    WAZUH_USERNAME   e.g. wazuh-wui
    WAZUH_PASSWORD   your password

⚠  verify=False is intentional — Wazuh ships with a self-signed cert.
   Replace with verify="/path/to/ca.pem" in production.
"""

import os
import time
import logging
import httpx

logger = logging.getLogger(__name__)


class WazuhOfflineError(Exception):
    """Raised when the Wazuh Manager cannot be reached."""
    pass


class WazuhAuthError(Exception):
    """Raised when Wazuh rejects credentials."""
    pass


class WazuhAuthService:
    """
    Singleton-style service that manages JWT tokens for the Wazuh API.
    Tokens are cached and automatically renewed when they expire.
    Default token lifetime is 900 seconds (15 min); we renew 60s early.
    """

    TOKEN_LIFETIME_SECONDS = 900
    RENEW_BEFORE_EXPIRY_SECONDS = 60
    TIMEOUT_SECONDS = 10

    def __init__(self):
        self.base_url: str = os.getenv("WAZUH_BASE_URL", "https://localhost:55000").rstrip("/")
        self.username: str = os.getenv("WAZUH_USERNAME", "wazuh-wui")
        self.password: str = os.getenv("WAZUH_PASSWORD", "")
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def get_token(self) -> str:
        """Return a valid JWT token, fetching a new one if necessary."""
        if self._token and time.time() < self._token_expires_at:
            return self._token
        return await self._fetch_token()

    async def get_headers(self) -> dict:
        """Return Authorization headers ready for any Wazuh API call."""
        token = await self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _fetch_token(self) -> str:
        """Authenticate with Wazuh and cache the returned JWT."""
        url = f"{self.base_url}/security/user/authenticate"
        logger.info("Fetching new Wazuh JWT token from %s", url)

        import base64
        auth_str = f"{self.username}:{self.password}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_auth}"}

        try:
            async with httpx.AsyncClient(verify=False, timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.post(
                    url,
                    headers=headers,
                )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.error("Wazuh Manager unreachable: %s", exc)
            raise WazuhOfflineError(
                "Wazuh Manager is offline or unreachable."
            ) from exc

        if response.status_code == 401:
            logger.error("Wazuh authentication failed — check credentials.")
            raise WazuhAuthError("Wazuh rejected the provided credentials.")

        if response.status_code != 200:
            logger.error("Unexpected auth response %s: %s", response.status_code, response.text)
            raise WazuhOfflineError(
                f"Wazuh auth endpoint returned HTTP {response.status_code}."
            )

        data = response.json()
        self._token = data["data"]["token"]
        self._token_expires_at = (
            time.time() + self.TOKEN_LIFETIME_SECONDS - self.RENEW_BEFORE_EXPIRY_SECONDS
        )
        logger.info("Wazuh JWT token acquired. Valid for ~%ds.", self.TOKEN_LIFETIME_SECONDS)
        return self._token

    async def get_wazuh_version(self) -> str:
        """Return the Wazuh Manager version string (used by /health)."""
        url = f"{self.base_url}/"
        try:
            headers = await self.get_headers()
            async with httpx.AsyncClient(verify=False, timeout=self.TIMEOUT_SECONDS) as client:
                resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json().get("data", {}).get("title", "Wazuh Manager")
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            raise WazuhOfflineError("Wazuh Manager is offline.") from exc


# Module-level singleton — import this everywhere.
wazuh_auth = WazuhAuthService()
