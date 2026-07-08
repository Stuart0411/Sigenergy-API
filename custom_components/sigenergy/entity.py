"""Base entity classes for Sigenergy integration."""

from typing import Any, Dict, Optional
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.const import ATTR_ATTRIBUTION

from .const import DOMAIN
from .coordinator import SigenergySomeDataUpdateCoordinator


class SigenergySomeEntity(Entity):
    """Base class for Sigenergy entities."""

    _attr_attribution = "Data provided by Sigenergy"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SigenergySomeDataUpdateCoordinator,
        system_id: str,
        device_id: str,
        device_name: str,
    ):
        """Initialize the entity."""
        self.coordinator = coordinator
        self.system_id = system_id
        self.device_id = device_id
        self.device_name = device_name

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"{self.system_id}_{self.device_id}")},
            "name": self.device_name,
            "manufacturer": "Sigenergy",
            "model": "Unknown",
        }

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{DOMAIN}_{self.system_id}_{self.device_id}"

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class SigenergySomeCoordinatorEntity(SigenergySomeEntity):
    """Sigenergy entity with coordinator."""

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self._handle_coordinator_update)
        )

    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update."""
        self.async_write_ha_state()
