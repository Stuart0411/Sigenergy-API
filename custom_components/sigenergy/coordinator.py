"""Data coordinator for Sigenergy integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from time import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SigenergyApiError, SigenergyClient
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SigenergyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator fetching data from Sigenergy APIs."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: SigenergyClient,
        energy_flow_interval: int,
        summary_interval: int,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.client = client
        self.energy_flow_interval = max(300, energy_flow_interval)
        self.summary_interval = max(300, summary_interval)

        self._last_energy_flow_fetch: dict[str, float] = {}
        self._last_summary_fetch: dict[str, float] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Sigenergy APIs."""
        try:
            systems = await self.client.get_systems()
            data: dict[str, Any] = {
                "systems": systems,
                "devices": {},
                "device_data": {},
                "energy_flow": {},
                "summary": {},
            }

            system_ids = [str(system.get("id")) for system in systems if system.get("id")]

            for system in systems:
                system_id = str(system.get("id"))
                if not system_id:
                    continue

                devices = await self.client.get_system_devices(system_id)
                data["devices"][system_id] = devices
                data["device_data"][system_id] = {}

                for device in devices:
                    device_id = str(device.get("id"))
                    if not device_id:
                        continue
                    try:
                        data["device_data"][system_id][device_id] = await self.client.get_device_data(
                            system_id, device_id
                        )
                    except SigenergyApiError:
                        data["device_data"][system_id][device_id] = {}

                if self._should_fetch(system_id, "energy_flow"):
                    try:
                        data["energy_flow"][system_id] = await self.client.get_system_energy_flow(
                            system_id
                        )
                        self._last_energy_flow_fetch[system_id] = time()
                    except SigenergyApiError:
                        data["energy_flow"][system_id] = {}

                if self._should_fetch(system_id, "summary"):
                    try:
                        data["summary"][system_id] = await self.client.get_system_summary(system_id)
                        self._last_summary_fetch[system_id] = time()
                    except SigenergyApiError:
                        data["summary"][system_id] = {}

            if system_ids:
                try:
                    await self.client.subscribe_to_telemetry(system_ids)
                    await self.client.subscribe_to_system_data(system_ids)
                except SigenergyApiError:
                    pass

            return data
        except SigenergyApiError as err:
            raise UpdateFailed(f"Error communicating with Sigenergy API: {err}") from err

    def _should_fetch(self, system_id: str, data_type: str) -> bool:
        now = time()
        if data_type == "energy_flow":
            last = self._last_energy_flow_fetch.get(system_id, 0)
            return (now - last) >= self.energy_flow_interval

        last = self._last_summary_fetch.get(system_id, 0)
        return (now - last) >= self.summary_interval
