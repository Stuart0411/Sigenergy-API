"""Switch platform for Sigenergy integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SigenergyApiError, SigenergyClient
from .const import DOMAIN
from .coordinator import SigenergyDataUpdateCoordinator
from .entity import SigenergyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sigenergy switch entities."""
    coordinator: SigenergyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client: SigenergyClient = hass.data[DOMAIN][entry.entry_id]["client"]

    entities: list[SwitchEntity] = []
    for system in coordinator.data.get("systems", []):
        system_id = str(system.get("id"))
        for device in coordinator.data.get("devices", {}).get(system_id, []):
            if str(device.get("type", "")).lower() != "charger":
                continue

            device_id = str(device.get("id"))
            device_name = device.get("name") or f"Charger {device_id}"
            entities.append(SigenergyChargerSwitch(coordinator, client, system_id, device_id, device_name))

    async_add_entities(entities)


class SigenergyChargerSwitch(SigenergyEntity, SwitchEntity):
    """Switch controlling charger start/stop."""

    _attr_translation_key = "charger_status"

    def __init__(
        self,
        coordinator: SigenergyDataUpdateCoordinator,
        client: SigenergyClient,
        system_id: str,
        device_id: str,
        name: str,
    ) -> None:
        super().__init__(coordinator, system_id, device_id, name)
        self._client = client

    @property
    def is_on(self) -> bool:
        payload = self.coordinator.data.get("device_data", {}).get(self.system_id, {}).get(self.device_id, {})
        status = str(payload.get("status", "")).lower()
        return status in {"charging", "active", "on"}

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self._client.set_device_command(self.system_id, self.device_id, "start_charging", {})
        except SigenergyApiError as err:
            raise HomeAssistantError(f"Failed to start charging: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self._client.set_device_command(self.system_id, self.device_id, "stop_charging", {})
        except SigenergyApiError as err:
            raise HomeAssistantError(f"Failed to stop charging: {err}") from err
        await self.coordinator.async_request_refresh()
