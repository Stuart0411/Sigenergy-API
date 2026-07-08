"""Sigenergy API client."""

import aiohttp
import asyncio
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
import logging
import json

_LOGGER = logging.getLogger(__name__)

from .const import (
    SIGENERGY_API_BASE,
    SIGENERGY_MQTT_BROKER,
    SIGENERGY_MQTT_PORT,
    SIGENERGY_API_TIMEOUT,
    SIGENERGY_TOKEN_EXPIRY,
    MQTT_TOPIC_TELEMETRY,
    MQTT_TOPIC_SYSTEM_DATA,
)


class SigenergySomeAPIError(Exception):
    """Base exception for Sigenergy API errors."""

    pass


class SigenergySomeInvalidAuth(SigenergySomeAPIError):
    """Exception for invalid authentication."""

    pass


class SigenergySomeConnectionError(SigenergySomeAPIError):
    """Exception for connection errors."""

    pass


class SigenergySomeClient:
    """Sigenergy API client with OAuth2 and MQTT support."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        account_id: Optional[str] = None,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """Initialize the Sigenergy API client."""
        self.session = session
        self.username = username
        self.password = password
        self.account_id = account_id
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = SIGENERGY_API_BASE
        self.access_token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self._mqtt_client = None
        self._data_callbacks: Dict[str, list[Callable]] = {
            "telemetry": [],
            "system_data": [],
            "alarm": [],
        }

    async def authenticate(self) -> bool:
        """Authenticate with Sigenergy API using OAuth2."""
        try:
            # OAuth2 client credentials flow
            url = f"{self.base_url}/oauth/token"
            
            if self.client_id and self.client_secret:
                # Use client credentials
                payload = {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            elif self.username and self.password:
                # Fallback to resource owner password credentials
                payload = {
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                    "client_id": self.client_id or "home-assistant",
                }
            else:
                raise SigenergySomeInvalidAuth("No valid credentials provided")

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            async with self.session.post(
                url,
                data=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT),
            ) as resp:
                if resp.status == 401:
                    raise SigenergySomeInvalidAuth("Invalid credentials")
                if resp.status != 200:
                    raise SigenergySomeAPIError(f"Authentication failed: {resp.status}")

                data = await resp.json()
                self.access_token = data.get("access_token")
                expires_in = data.get("expires_in", SIGENERGY_TOKEN_EXPIRY)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in)
                _LOGGER.debug("Successfully authenticated with Sigenergy API")
                return True

        except aiohttp.ClientError as err:
            raise SigenergySomeConnectionError(f"Connection error: {err}") from err

    async def _ensure_valid_token(self) -> None:
        """Ensure access token is valid, refresh if needed."""
        if not self.token_expires or datetime.now() >= self.token_expires:
            await self.authenticate()

    async def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def get_systems(self) -> list[Dict[str, Any]]:
        """Get all systems for the account."""
        try:
            url = f"{self.base_url}/systems"
            headers = await self._get_headers()
            async with self.session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT)
            ) as resp:
                if resp.status == 401:
                    await self.authenticate()
                    return await self.get_systems()
                if resp.status != 200:
                    raise SigenergySomeAPIError(f"Failed to get systems: {resp.status}")

                data = await resp.json()
                return data.get("systems", [])

        except aiohttp.ClientError as err:
            raise SigenergySomeConnectionError(f"Connection error: {err}") from err

    async def get_system_details(self, system_id: str) -> Dict[str, Any]:
        """Get details for a specific system."""
        try:
            url = f"{self.base_url}/systems/{system_id}"
            headers = await self._get_headers()
            async with self.session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT)
            ) as resp:
                if resp.status == 401:
                    await self.authenticate()
                    return await self.get_system_details(system_id)
                if resp.status != 200:
                    raise SigenergySomeAPIError(f"Failed to get system details: {resp.status}")

                return await resp.json()

        except aiohttp.ClientError as err:
            raise SigenergySomeConnectionError(f"Connection error: {err}") from err

    async def get_system_devices(self, system_id: str) -> list[Dict[str, Any]]:
        """Get all devices for a system."""
        try:
            url = f"{self.base_url}/systems/{system_id}/devices"
            headers = await self._get_headers()
            async with self.session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT)
            ) as resp:
                if resp.status == 401:
                    await self.authenticate()
                    return await self.get_system_devices(system_id)
                if resp.status != 200:
                    raise SigenergySomeAPIError(f"Failed to get devices: {resp.status}")

                data = await resp.json()
                return data.get("devices", [])

        except aiohttp.ClientError as err:
            raise SigenergySomeConnectionError(f"Connection error: {err}") from err

    async def get_device_data(self, system_id: str, device_id: str) -> Dict[str, Any]:
        """Get real-time data for a device."""
        try:
            url = f"{self.base_url}/systems/{system_id}/devices/{device_id}/data"
            headers = await self._get_headers()
            async with self.session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT)
            ) as resp:
                if resp.status == 401:
                    await self.authenticate()
                    return await self.get_device_data(system_id, device_id)
                if resp.status != 200:
                    raise SigenergySomeAPIError(f"Failed to get device data: {resp.status}")

                return await resp.json()

        except aiohttp.ClientError as err:
            raise SigenergySomeConnectionError(f"Connection error: {err}") from err

    async def set_device_command(
        self, system_id: str, device_id: str, command: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a command to a device."""
        try:
            url = f"{self.base_url}/systems/{system_id}/devices/{device_id}/command"
            headers = await self._get_headers()
            payload = {
                "command": command,
                "parameters": parameters,
            }
            async with self.session.post(
                url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT)
            ) as resp:
                if resp.status == 401:
                    await self.authenticate()
    def on_telemetry_data(self, callback: Callable) -> None:
        """Register callback for telemetry data updates."""
        self._data_callbacks["telemetry"].append(callback)

    def on_system_data(self, callback: Callable) -> None:
        """Register callback for system data updates."""
        self._data_callbacks["system_data"].append(callback)

    def on_alarm(self, callback: Callable) -> None:
        """Register callback for alarm notifications."""
        self._data_callbacks["alarm"].append(callback)

    def _notify_telemetry(self, data: Dict[str, Any]) -> None:
        """Notify all telemetry callbacks."""
        for callback in self._data_callbacks["telemetry"]:
            try:
                callback(data)
            except Exception as err:
                _LOGGER.error(f"Error in telemetry callback: {err}")

    def _notify_system_data(self, data: Dict[str, Any]) -> None:
        """Notify all system data callbacks."""
        for callback in self._data_callbacks["system_data"]:
            try:
                callback(data)
            except Exception as err:
                _LOGGER.error(f"Error in system data callback: {err}")

    def _notify_alarm(self, data: Dict[str, Any]) -> None:
        """Notify all alarm callbacks."""
        for callback in self._data_callbacks["alarm"]:
            try:
                callback(data)
            except Exception as err:
                _LOGGER.error(f"Error in alarm callback: {err}")

    async def subscribe_to_telemetry(self, system_ids: list[str]) -> bool:
        """Subscribe to real-time telemetry data via MQTT.
        
        This enables receiving periodic (default 5-min) telemetry data updates
        containing power, energy, and status metrics.
        """
        try:
            await self._ensure_valid_token()
            url = f"{self.base_url}/openapi/subscription/period"
            headers = await self._get_headers()
            payload = {"accessToken": self.access_token, "systemIdList": system_ids}

            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning(f"Failed to subscribe to telemetry: {resp.status}")
                    return False
                _LOGGER.debug(f"Subscribed to telemetry for systems: {system_ids}")
                return True

        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error subscribing to telemetry: {err}")
            return False

    async def subscribe_to_system_data(self, system_ids: list[str]) -> bool:
        """Subscribe to real-time system data changes via MQTT.
        
        This enables receiving immediate updates when system data changes
        (e.g., battery capacity, max charge/discharge power).
        """
        try:
            await self._ensure_valid_token()
            url = f"{self.base_url}/openapi/subscription/change"
            headers = await self._get_headers()
            payload = {"accessToken": self.access_token, "systemIdList": system_ids}

            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT),
            ) as resp:
                if resp.status != 200:
                    _LOGGER.warning(f"Failed to subscribe to system data: {resp.status}")
                    return False
                _LOGGER.debug(f"Subscribed to system data for systems: {system_ids}")
                return True

        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error subscribing to system data: {err}")
            return False

    def process_telemetry_message(self, message: Dict[str, Any]) -> None:
        """Process incoming telemetry message from MQTT.
        
        Expected format:
        {
            "systemId": "...",
            "snCode": "...",
            "deviceType": "system",
            "statisticsTime": 1234567890,
            "value": {"power": 1000, "soc": 50, ...}
        }
        """
        self._notify_telemetry(message)
        _LOGGER.debug(f"Processed telemetry: {message.get('systemId')}")

    def process_system_data_message(self, message: Dict[str, Any]) -> None:
        """Process incoming system data message from MQTT.
        
        Expected format:
        {
            "systemId": "...",
            "snCode": "...",
            "deviceType": "...",
            "value": {"maxChargePower": 50000, "maxDischargePower": 50000, ...}
        }
        """
        self._notify_system_data(message)
        _LOGGER.debug(f"Processed system data: {message.get('systemId')}")

    def process_alarm_message(self, message: Dict[str, Any]) -> None:
        """Process incoming alarm message from MQTT.
        
        Expected format:
        {
            "systemId": "...",
            "alarmCode": "...",
            "alarmLevel": "warning|error|critical",
            "description": "...",
            "timestamp": 1234567890
        }
        """
        self._notify_alarm(message)
        _LOGGER.warning(f"Alarm received: {message.get('alarmCode')} - {message.get('description')}")

                    return await self.set_device_command(system_id, device_id, command, parameters)
                if resp.status != 200:
                    raise SigenergySomeAPIError(f"Failed to send command: {resp.status}")

                return await resp.json()

        except aiohttp.ClientError as err:
            raise SigenergySomeConnectionError(f"Connection error: {err}") from err

    async def close(self):
        """Close the API client session."""
        if self.session:
            await self.session.close()

    async def get_system_energy_flow(self, system_id: str) -> Dict[str, Any]:
        """Get real-time energy flow data for a system.
        
        Returns power flows: PV, grid, EV, load, heat pump, battery, and battery SOC.
        Note: Limited to once per 5 minutes per device by API.
        """
        try:
            await self._ensure_valid_token()
            url = f"{self.base_url}/openapi/systems/{system_id}/energyFlow"
            headers = await self._get_headers()
            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT),
            ) as resp:
                if resp.status == 401:
                    await self.authenticate()
                    return await self.get_system_energy_flow(system_id)
                if resp.status != 200:
                    raise SigenergySomeAPIError(f"Failed to get energy flow: {resp.status}")

                data = await resp.json()
                return data.get("data", {}) if data.get("code") == 0 else {}

        except aiohttp.ClientError as err:
            raise SigenergySomeConnectionError(f"Connection error: {err}") from err

    async def get_system_summary(self, system_id: str) -> Dict[str, Any]:
        """Get system summary data including power generation stats.
        
        Returns daily, monthly, annual, and lifetime power generation,
        plus environmental impact metrics (CO2, coal, trees).
        Note: Limited to once per 5 minutes per system by API.
        """
        try:
            await self._ensure_valid_token()
            url = f"{self.base_url}/openapi/systems/{system_id}/summary"
            headers = await self._get_headers()
            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=SIGENERGY_API_TIMEOUT),
            ) as resp:
                if resp.status == 401:
                    await self.authenticate()
                    return await self.get_system_summary(system_id)
                if resp.status != 200:
                    raise SigenergySomeAPIError(f"Failed to get summary: {resp.status}")

                data = await resp.json()
                return data.get("data", {}) if data.get("code") == 0 else {}

        except aiohttp.ClientError as err:
            raise SigenergySomeConnectionError(f"Connection error: {err}") from err
