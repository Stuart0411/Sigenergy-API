"""Switch entities for Sigenergy integration."""

from typing import Any, Optional
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up Sigenergy switches."""
    coordinator: SigenergySomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    api_client = hass.data[DOMAIN][entry.entry_id]["api_client"]

    entities = []

    # Create switch entities for controllable devices
    for system in coordinator.data.get("systems", []):
        system_id = system.get("id")

        for device in coordinator.data.get("devices", {}).get(system_id, []):
            device_id = device.get("id")
            device_name = device.get("name", f"Device {device_id}")
            device_type = device.get("type")

            if device_type == "charger":
                entities.append(
                    SigenergySomeChargerSwitch(
                        coordinator=coordinator,
                        api_client=api_client,
                        system_id=system_id,
                        device_id=device_id,
                        device_name=device_name,
                    )
                )

    async_add_entities(entities)


class SigenergySomeChargerSwitch(SwitchEntity, SigenergySomeCoordinatorEntity):
    """Charger control switch."""

    _attr_translation_key = "charger_status"

    def __init__(self, api_client, **kwargs):
        """Initialize the switch."""
        super().__init__(**kwargs)
        self.api_client = api_client

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        device_data = (
            self.coordinator.data.get("device_data", {})
            .get(self.system_id, {})
            .get(self.device_id, {})
        )
        status = device_data.get("status", "").lower()
        return status == "charging" or status == "active"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the charger."""
        try:
            await self.api_client.set_device_command(
                self.system_id,
                self.device_id,
                "start_charging",
                {},
            )
            await self.coordinator.async_request_refresh()
        except SigenergySomeAPIError as err:
            raise HomeAssistantError(f"Failed to turn on charger: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the charger."""
        try:
            await self.api_client.set_device_command(
                self.system_id,
                self.device_id,
                "stop_charging",
                {},
            )
            await self.coordinator.async_request_refresh()
        except SigenergySomeAPIError as err:
            raise HomeAssistantError(f"Failed to turn off charger: {err}") from err


class HomeAssistantError(Exception):
    """Base Home Assistant error."""
