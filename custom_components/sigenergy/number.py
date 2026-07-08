"""Number entities for Sigenergy integration."""

from typing import Any, Optional
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import POWER_WATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SigenergySomeDataUpdateCoordinator
from .entity import SigenergySomeCoordinatorEntity
from .api import SigenergySomeAPIError


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sigenergy number entities."""
    coordinator: SigenergySomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    api_client = hass.data[DOMAIN][entry.entry_id]["api_client"]

    entities = []

    # Create number entities for charging power control
    for system in coordinator.data.get("systems", []):
        system_id = system.get("id")

        for device in coordinator.data.get("devices", {}).get(system_id, []):
            device_id = device.get("id")
            device_name = device.get("name", f"Device {device_id}")
            device_type = device.get("type")

            if device_type == "charger":
                entities.append(
                    SigenergySomeChargerMaxPowerNumber(
                        coordinator=coordinator,
                        api_client=api_client,
                        system_id=system_id,
                        device_id=device_id,
                        device_name=device_name,
                    )
                )

    async_add_entities(entities)


class SigenergySomeChargerMaxPowerNumber(NumberEntity, SigenergySomeCoordinatorEntity):
    """Charger max power number."""

    _attr_translation_key = "charger_max_power"
    _attr_native_unit_of_measurement = POWER_WATT
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 50000
    _attr_native_step = 100

    def __init__(self, api_client, **kwargs):
        """Initialize the number entity."""
        super().__init__(**kwargs)
        self.api_client = api_client

    @property
    def native_value(self) -> Optional[float]:
        """Return the entity value."""
        device_data = (
            self.coordinator.data.get("device_data", {})
            .get(self.system_id, {})
            .get(self.device_id, {})
        )
        return device_data.get("max_charging_power")

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            await self.api_client.set_device_command(
                self.system_id,
                self.device_id,
                "set_max_power",
                {"max_power": int(value)},
            )
            await self.coordinator.async_request_refresh()
        except SigenergySomeAPIError as err:
            raise HomeAssistantError(f"Failed to set charging power: {err}") from err


class HomeAssistantError(Exception):
    """Base Home Assistant error."""
