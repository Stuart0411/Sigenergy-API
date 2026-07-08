"""Sigenergy API client."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import aiohttp

from .const import SIGENERGY_API_BASE, SIGENERGY_API_TIMEOUT, SIGENERGY_TOKEN_EXPIRY


class SigenergyApiError(Exception):
    """Base exception for Sigenergy API errors."""


class SigenergyInvalidAuth(SigenergyApiError):
    """Exception raised on auth failures."""


class SigenergyConnectionError(SigenergyApiError):
    """Exception raised on connectivity failures."""


class SigenergyClient:
    """Sigenergy API client with OAuth2 token management."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        account_id: str | None = None,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._account_id = account_id
        self._api_key = api_key
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = SIGENERGY_API_BASE.rstrip("/")
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    async def authenticate(self) -> None:
        """Authenticate and cache access token."""
        url = f"{self._base_url}/oauth/token"

        if self._client_id and self._client_secret:
            payload = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
        else:
            payload = {
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
                "client_id": self._client_id or "home-assistant",
            }

        try:
            async with self._session.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT),
            ) as resp:
                if resp.status == 401:
                    raise SigenergyInvalidAuth("Invalid credentials")
                if resp.status != 200:
                    raise SigenergyApiError(f"Authentication failed: {resp.status}")

                data = await resp.json()
        except aiohttp.ClientError as err:
            raise SigenergyConnectionError(str(err)) from err

        token = data.get("access_token")
        if not token:
            raise SigenergyInvalidAuth("Authentication response missing access_token")

        expires_in = int(data.get("expires_in", SIGENERGY_TOKEN_EXPIRY))
        self._access_token = token
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    async def _ensure_token(self) -> None:
        if not self._access_token or not self._token_expires_at:
            await self.authenticate()
            return

        if datetime.utcnow() >= self._token_expires_at:
            await self.authenticate()

    async def _headers(self) -> dict[str, str]:
        if self._api_key:
            return {"Content-Type": "application/json", "X-API-Key": self._api_key}

        await self._ensure_token()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }

    async def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        headers = await self._headers()
        kwargs.setdefault("timeout", aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT))
        kwargs["headers"] = {**headers, **kwargs.get("headers", {})}

        try:
            async with self._session.request(method, url, **kwargs) as resp:
                if resp.status == 401 and not self._api_key:
                    await self.authenticate()
                    headers = await self._headers()
                    kwargs["headers"] = {**headers, **kwargs.get("headers", {})}
                    async with self._session.request(method, url, **kwargs) as retry_resp:
                        if retry_resp.status != 200:
                            raise SigenergyApiError(
                                f"Request failed {method} {path}: {retry_resp.status}"
                            )
                        return await retry_resp.json()

                if resp.status != 200:
                    raise SigenergyApiError(f"Request failed {method} {path}: {resp.status}")
                return await resp.json()
        except aiohttp.ClientError as err:
            raise SigenergyConnectionError(str(err)) from err

    async def get_systems(self) -> list[dict[str, Any]]:
        """Return all systems accessible by this account."""
        data = await self._request_json("GET", "systems")
        return data.get("systems", data.get("data", []))

    async def get_system_details(self, system_id: str) -> dict[str, Any]:
        """Return details for one system."""
        return await self._request_json("GET", f"systems/{system_id}")

    async def get_system_devices(self, system_id: str) -> list[dict[str, Any]]:
        """Return devices within one system."""
        data = await self._request_json("GET", f"systems/{system_id}/devices")
        return data.get("devices", data.get("data", []))

    async def get_device_data(self, system_id: str, device_id: str) -> dict[str, Any]:
        """Return realtime data for one device."""
        return await self._request_json("GET", f"systems/{system_id}/devices/{device_id}/data")

    async def set_device_command(
        self, system_id: str, device_id: str, command: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a command to one device."""
        payload = {"command": command, "parameters": parameters}
        return await self._request_json(
            "POST", f"systems/{system_id}/devices/{device_id}/command", json=payload
        )

    async def subscribe_to_telemetry(self, system_ids: list[str]) -> bool:
        """Subscribe to MQTT telemetry topic (openapi/subscription/period)."""
        await self._ensure_token()
        payload = {"accessToken": self._access_token, "systemIdList": system_ids}
        await self._request_json("POST", "openapi/subscription/period", json=payload)
        return True

    async def subscribe_to_system_data(self, system_ids: list[str]) -> bool:
        """Subscribe to MQTT change topic (openapi/subscription/change)."""
        await self._ensure_token()
        payload = {"accessToken": self._access_token, "systemIdList": system_ids}
        await self._request_json("POST", "openapi/subscription/change", json=payload)
        return True

    async def get_system_energy_flow(self, system_id: str) -> dict[str, Any]:
        """Doc 36: GET openapi/systems/{systemId}/energyFlow."""
        data = await self._request_json("GET", f"openapi/systems/{system_id}/energyFlow")
        return data.get("data", data)

    async def get_system_summary(self, system_id: str) -> dict[str, Any]:
        """Doc 35: GET openapi/systems/{systemId}/summary."""
        data = await self._request_json("GET", f"openapi/systems/{system_id}/summary")
        return data.get("data", data)
