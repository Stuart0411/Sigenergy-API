"""Binary sensor platform for Sigenergy integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SigenergyDataUpdateCoordinator
from .entity import SigenergyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sigenergy binary sensors."""
    coordinator: SigenergyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[BinarySensorEntity] = []
    for system in coordinator.data.get("systems", []):
        system_id = str(system.get("id"))
        if not system_id:
            continue
        system_name = system.get("name") or f"System {system_id}"
        entities.append(SigenergySystemOnlineBinarySensor(coordinator, system_id, system_name))

    async_add_entities(entities)


class SigenergySystemOnlineBinarySensor(SigenergyEntity, BinarySensorEntity):
    """System connectivity status."""

    _attr_translation_key = "system_online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: SigenergyDataUpdateCoordinator, system_id: str, name: str) -> None:
        super().__init__(coordinator, system_id, system_id, name)

    @property
    def is_on(self) -> bool:
        system = next(
            (
                candidate
                for candidate in self.coordinator.data.get("systems", [])
                if str(candidate.get("id")) == self.system_id
            ),
            None,
        )
        if not system:
            return False
        status = str(system.get("status", "")).lower()
        return status in {"online", "active", "normal"}
