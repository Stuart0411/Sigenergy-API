"""Binary sensor entities for Sigenergy integration."""

from typing import Any, Optional
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SigenergySomeDataUpdateCoordinator
from .entity import SigenergySomeCoordinatorEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sigenergy binary sensors."""
    coordinator: SigenergySomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities = []

    # Create binary sensor entities for system status
    for system in coordinator.data.get("systems", []):
        system_id = system.get("id")
        system_name = system.get("name", f"System {system_id}")

        entities.append(
            SigenergySomeSystemOnlineBinarySensor(
                coordinator=coordinator,
                system_id=system_id,
                device_id=system_id,
                device_name=system_name,
            )
        )

    async_add_entities(entities)


class SigenergySomeSystemOnlineBinarySensor(BinarySensorEntity, SigenergySomeCoordinatorEntity):
    """System online binary sensor."""

    _attr_translation_key = "system_online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool:
        """Return true if system is online."""
        system = next(
            (s for s in self.coordinator.data.get("systems", []) if s.get("id") == self.system_id),
            None,
        )
        if not system:
            return False
        status = system.get("status", "").lower()
        return status == "online" or status == "active"
