"""Sigenergy API client."""

from __future__ import annotations

import base64
import json
import time
from typing import Any

import aiohttp

from .const import SIGENERGY_API_BASE, SIGENERGY_API_TIMEOUT, SIGENERGY_TOKEN_EXPIRY


class SigenergyApiError(Exception):
    """Base exception for Sigenergy API errors."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class SigenergyInvalidAuth(SigenergyApiError):
    """Authentication error."""


class SigenergyConnectionError(SigenergyApiError):
    """Connection error."""


class SigenergyClient:
    """Client for the Sigenergy Cloud OpenAPI."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        account_id: str | None = None,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        base_url: str = SIGENERGY_API_BASE,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._account_id = account_id
        self._api_key = api_key
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url.rstrip("/")
        self._access_token: str | None = None
        self._token_expiry: float = 0

    @property
    def is_token_valid(self) -> bool:
        """Check if current token is still valid."""
        return self._access_token is not None and time.time() < (self._token_expiry - 600)

    async def authenticate(self) -> None:
        """Authenticate and obtain an access token."""
        if self._client_id and self._client_secret:
            await self._auth_key()
        else:
            await self._auth_password()

    async def _auth_password(self) -> None:
        """Authenticate using username/password flow."""
        data = await self._raw_post(
            f"{self._base_url}/openapi/auth/login/password",
            {"username": self._username, "password": self._password},
            authenticated=False,
        )
        self._parse_token_response(data)

    async def _auth_key(self) -> None:
        """Authenticate using key/secret flow."""
        key_string = f"{self._client_id}:{self._client_secret}"
        encoded_key = base64.b64encode(key_string.encode()).decode()
        data = await self._raw_post(
            f"{self._base_url}/openapi/auth/login/key",
            {"key": encoded_key},
            authenticated=False,
        )
        self._parse_token_response(data)

    def _parse_token_response(self, data: dict[str, Any]) -> None:
        """Parse token from auth response."""
        code = int(data.get("code", -1))
        if code != 0:
            msg = data.get("msg", "Authentication failed")
            if code in (11002, 11003):
                raise SigenergyInvalidAuth(msg, code=code)
            raise SigenergyApiError(f"{msg} (code {code})", code=code)

        token_data = data.get("data")
        if isinstance(token_data, str):
            token_data = json.loads(token_data)
        if not isinstance(token_data, dict):
            raise SigenergyInvalidAuth("Authentication response missing token data")

        token = token_data.get("accessToken") or token_data.get("access_token")
        if not token:
            raise SigenergyInvalidAuth("Authentication response missing access token")

        expires_in = int(token_data.get("expiresIn", SIGENERGY_TOKEN_EXPIRY))
        self._access_token = token
        self._token_expiry = time.time() + expires_in

    async def _ensure_token(self) -> None:
        if not self.is_token_valid:
            await self.authenticate()

    def _check_response(self, data: dict[str, Any], path: str) -> dict[str, Any]:
        """Check API response body for Sigenergy error codes."""
        code = data.get("code")
        if code is None:
            return data

        code = int(code)
        if code == 0:
            return data
        if code in (11002, 11003):
            raise SigenergyInvalidAuth(data.get("msg", "Auth error"), code=code)
        if code in (1110, 1201):
            raise SigenergyApiError(data.get("msg", "Rate limit / access restriction"), code=code)

        raise SigenergyApiError(f"{data.get('msg', 'API error')} (code {code}) for {path}", code=code)

    async def _raw_post(
        self,
        url: str,
        payload: dict[str, Any],
        authenticated: bool = True,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if authenticated:
            await self._ensure_token()
            headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            async with self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                raise SigenergyInvalidAuth(f"Authentication rejected: {err.status}") from err
            raise SigenergyApiError(f"API request failed: {err}") from err
        except aiohttp.ClientError as err:
            raise SigenergyConnectionError(f"Connection error: {err}") from err

    async def _raw_get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self._ensure_token()
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            async with self._session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientResponseError as err:
            if err.status in (401, 403):
                raise SigenergyInvalidAuth(f"Authentication rejected: {err.status}") from err
            raise SigenergyApiError(f"API request failed: {err}") from err
        except aiohttp.ClientError as err:
            raise SigenergyConnectionError(f"Connection error: {err}") from err

    async def _api_get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        data = await self._raw_get(f"{self._base_url}/{path.lstrip('/')}", params=params)
        return self._check_response(data, path)

    async def _api_post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if payload is None:
            payload = {}
        data = await self._raw_post(f"{self._base_url}/{path.lstrip('/')}", payload)
        return self._check_response(data, path)

    @staticmethod
    def _parse_data(value: Any) -> Any:
        """Parse JSON-encoded string values if necessary."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    async def get_systems(self) -> list[dict[str, Any]]:
        """Get list of all authorized systems."""
        data = await self._api_get("openapi/system")
        raw = self._parse_data(data.get("data", []))
        systems = raw if isinstance(raw, list) else []

        normalized: list[dict[str, Any]] = []
        for system in systems:
            if not isinstance(system, dict):
                continue
            normalized.append(
                {
                    **system,
                    "id": str(system.get("systemId") or system.get("id") or ""),
                    "name": system.get("systemName") or system.get("name") or "Sigenergy System",
                }
            )
        return normalized

    async def get_system_details(self, system_id: str) -> dict[str, Any]:
        """Get details for a specific system."""
        systems = await self.get_systems()
        for system in systems:
            if str(system.get("id")) == str(system_id):
                return system
        return {}

    async def get_system_devices(self, system_id: str) -> list[dict[str, Any]]:
        """Get all devices for a system."""
        data = await self._api_get(
            f"openapi/system/{system_id}/devices",
            {"systemId": system_id},
        )
        raw = self._parse_data(data.get("data", []))
        devices = raw if isinstance(raw, list) else []

        normalized: list[dict[str, Any]] = []
        for device in devices:
            if not isinstance(device, dict):
                continue
            normalized.append(
                {
                    **device,
                    "id": str(device.get("serialNumber") or device.get("id") or ""),
                    "name": (
                        device.get("deviceName")
                        or device.get("deviceAlias")
                        or device.get("name")
                        or f"Device {device.get('serialNumber', '')}"
                    ),
                    "type": str(device.get("deviceType") or device.get("type") or "").lower(),
                }
            )
        return normalized

    async def get_device_data(self, system_id: str, device_id: str) -> dict[str, Any]:
        """Get real-time data for a specific device."""
        data = await self._api_get(
            f"openapi/systems/{system_id}/devices/{device_id}/realtimeInfo",
            {"systemId": system_id, "serialNumber": device_id},
        )
        parsed = self._parse_data(data.get("data", {}))
        return parsed if isinstance(parsed, dict) else {}

    async def set_device_command(
        self,
        system_id: str,
        device_id: str,
        command: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Send command to device."""
        payload = {
            "systemId": system_id,
            "serialNumber": device_id,
            "command": command,
            "parameters": parameters,
        }
        data = await self._api_post(f"openapi/instruction/{system_id}/settings", payload)
        parsed = self._parse_data(data.get("data", {}))
        return parsed if isinstance(parsed, dict) else {}

    async def subscribe_to_telemetry(self, system_ids: list[str]) -> bool:
        """Subscribe to periodic telemetry push topic."""
        await self._ensure_token()
        await self._api_post(
            "openapi/subscription/period",
            {"accessToken": self._access_token, "systemIdList": system_ids},
        )
        return True

    async def subscribe_to_system_data(self, system_ids: list[str]) -> bool:
        """Subscribe to change-data push topic."""
        await self._ensure_token()
        await self._api_post(
            "openapi/subscription/change",
            {"accessToken": self._access_token, "systemIdList": system_ids},
        )
        return True

    async def get_system_energy_flow(self, system_id: str) -> dict[str, Any]:
        """Doc 36: Get realtime energy flow for a system."""
        data = await self._api_get(
            f"openapi/systems/{system_id}/energyFlow",
            {"systemId": system_id},
        )
        parsed = self._parse_data(data.get("data", {}))
        return parsed if isinstance(parsed, dict) else {}

    async def get_system_summary(self, system_id: str) -> dict[str, Any]:
        """Doc 35: Get realtime summary for a system."""
        data = await self._api_get(
            f"openapi/systems/{system_id}/summary",
            {"systemId": system_id},
        )
        parsed = self._parse_data(data.get("data", {}))
        return parsed if isinstance(parsed, dict) else {}
