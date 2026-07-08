"""Entity helpers for Sigenergy integration."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SigenergyDataUpdateCoordinator


class SigenergyEntity(CoordinatorEntity[SigenergyDataUpdateCoordinator]):
    """Base class for all Sigenergy entities."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by Sigenergy"

    def __init__(
        self,
        coordinator: SigenergyDataUpdateCoordinator,
        system_id: str,
        device_id: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self.system_id = system_id
        self.device_id = device_id
        self._attr_name = name

    @property
    def unique_id(self) -> str:
        """Return unique id for this entity."""
        return f"{DOMAIN}_{self.system_id}_{self.device_id}_{self.__class__.__name__.lower()}"

    @property
    def device_info(self) -> dict:
        """Return device metadata."""
        return {
            "identifiers": {(DOMAIN, f"{self.system_id}_{self.device_id}")},
            "name": self._attr_name,
            "manufacturer": "Sigenergy",
        }
