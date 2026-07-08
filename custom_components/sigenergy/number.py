"""Number platform for Sigenergy integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
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
    """Set up Sigenergy number entities."""
    coordinator: SigenergyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client: SigenergyClient = hass.data[DOMAIN][entry.entry_id]["client"]

    entities: list[NumberEntity] = []
    for system in coordinator.data.get("systems", []):
        system_id = str(system.get("id"))
        for device in coordinator.data.get("devices", {}).get(system_id, []):
            if str(device.get("type", "")).lower() != "charger":
                continue

            device_id = str(device.get("id"))
            device_name = device.get("name") or f"Charger {device_id}"
            entities.append(
                SigenergyChargerMaxPowerNumber(coordinator, client, system_id, device_id, device_name)
            )

    async_add_entities(entities)


class SigenergyChargerMaxPowerNumber(SigenergyEntity, NumberEntity):
    """Max charger power control."""

    _attr_translation_key = "charger_max_power"
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_native_min_value = 0
    _attr_native_max_value = 50000
    _attr_native_step = 100

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
    def native_value(self):
        payload = self.coordinator.data.get("device_data", {}).get(self.system_id, {}).get(self.device_id, {})
        return payload.get("max_charging_power")

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self._client.set_device_command(
                self.system_id,
                self.device_id,
                "set_max_power",
                {"max_power": int(value)},
            )
        except SigenergyApiError as err:
            raise HomeAssistantError(f"Failed to set max charging power: {err}") from err
        await self.coordinator.async_request_refresh()
