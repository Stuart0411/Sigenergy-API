"""Data coordinator for Sigenergy integration."""

from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SigenergySomeClient, SigenergySomeAPIError
from .const import DOMAIN, SCAN_INTERVAL
from .const import DOMAIN, SCAN_INTERVAL, ENERGY_FLOW_INTERVAL, SUMMARY_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SigenergySomeDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for Sigenergy with real-time MQTT support."""

    def __init__(self, hass: HomeAssistant, api_client: SigenergySomeClient):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.api_client = api_client
        self.data: Dict[str, Any] = {
            "systems": [],
            "devices": {},
            "device_data": {},
            "telemetry": {},  # Real-time telemetry from MQTT
            "system_info": {},  # Real-time system data from MQTT
            "alarms": [],  # Active alarms
        }
        
            # Store last update timestamps for energy flow and summary
            self.last_energy_flow_update: Dict[str, float] = {}
            self.last_summary_update: Dict[str, float] = {}
            self.energy_flow_interval = ENERGY_FLOW_INTERVAL
            self.summary_interval = SUMMARY_INTERVAL
        
        # Register callbacks for real-time data
        self.api_client.on_telemetry_data(self._on_telemetry_data)
        self.api_client.on_system_data(self._on_system_data)
        self.api_client.on_alarm(self._on_alarm)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Sigenergy API and subscribe to real-time updates."""
        try:
            # Authenticate if needed
            if not self.api_client.access_token:
                await self.api_client.authenticate()

            # Get all systems
            systems = await self.api_client.get_systems()
            self.data["systems"] = systems
            system_ids = [s.get("id") for s in systems if s.get("id")]

            # Get devices and data for each system
            for system in systems:
                system_id = system.get("id")
                if not system_id:
                    continue

                # Get system details
                system_details = await self.api_client.get_system_details(system_id)
                system["details"] = system_details

                # Get devices
                devices = await self.api_client.get_system_devices(system_id)
                self.data["devices"][system_id] = devices

                # Get data for each device
                self.data["device_data"][system_id] = {}
                for device in devices:
                    device_id = device.get("id")
                    if not device_id:
                        continue
                    try:
                        device_data = await self.api_client.get_device_data(system_id, device_id)
                        self.data["device_data"][system_id][device_id] = device_data
                    except SigenergySomeAPIError as err:
                        _LOGGER.warning(f"Failed to get data for device {device_id}: {err}")
                        self.data["device_data"][system_id][device_id] = {}

            # Subscribe to real-time MQTT data (non-blocking)
            if system_ids:
                # Telemetry subscription (periodic updates, default 5 min)
                await self.api_client.subscribe_to_telemetry(system_ids)
                # System data subscription (immediate updates on change)
                await self.api_client.subscribe_to_system_data(system_ids)
                _LOGGER.debug(f"Subscribed to real-time data for {len(system_ids)} systems")

            return self.data

            # Fetch energy flow data (respecting API rate limits)
            if not "energy_flow" in self.data:
                self.data["energy_flow"] = {}
            for system_id in system_ids:
                if self._should_update("energy_flow", system_id):
                    try:
                        energy_flow = await self.api_client.get_system_energy_flow(system_id)
                        self.data["energy_flow"][system_id] = energy_flow
                        self.last_energy_flow_update[system_id] = self.hass.loop.time()
                    except SigenergySomeAPIError as err:
                        _LOGGER.warning(f"Failed to get energy flow for {system_id}: {err}")

            # Fetch summary data (respecting API rate limits)
            if not "summary" in self.data:
                self.data["summary"] = {}
            for system_id in system_ids:
                if self._should_update("summary", system_id):
                    try:
                        summary = await self.api_client.get_system_summary(system_id)
                        self.data["summary"][system_id] = summary
                        self.last_summary_update[system_id] = self.hass.loop.time()
                    except SigenergySomeAPIError as err:
                        _LOGGER.warning(f"Failed to get summary for {system_id}: {err}")

        except SigenergySomeAPIError as err:
            raise UpdateFailed(f"Failed to fetch Sigenergy data: {err}") from err

    def _should_update(self, data_type: str, system_id: str) -> bool:
        """Check if enough time has passed to update data respecting API rate limits."""
        import time
        now = time.time()
        
        if data_type == "energy_flow":
            last_update = self.last_energy_flow_update.get(system_id, 0)
            return (now - last_update) >= self.energy_flow_interval
        elif data_type == "summary":
            last_update = self.last_summary_update.get(system_id, 0)
            return (now - last_update) >= self.summary_interval
        return False

    def _on_telemetry_data(self, message: Dict[str, Any]) -> None:
        """Handle real-time telemetry data from MQTT."""
        system_id = message.get("systemId")
        device_id = message.get("snCode")
        
        if system_id and device_id:
            if system_id not in self.data["telemetry"]:
                self.data["telemetry"][system_id] = {}
            
            self.data["telemetry"][system_id][device_id] = {
                "timestamp": message.get("statisticsTime"),
                "values": message.get("value", {}),
            }
            
            # Also update device_data for immediate availability
            if system_id in self.data["device_data"] and device_id in self.data["device_data"][system_id]:
                self.data["device_data"][system_id][device_id].update(message.get("value", {}))
            
            # Notify all entities of update
            self.async_set_updated_data(self.data)
            _LOGGER.debug(f"Real-time telemetry updated: {system_id}/{device_id}")

    def _on_system_data(self, message: Dict[str, Any]) -> None:
        """Handle real-time system data changes from MQTT."""
        system_id = message.get("systemId")
        device_id = message.get("snCode")
        
        if system_id:
            if system_id not in self.data["system_info"]:
                self.data["system_info"][system_id] = {}
            
            self.data["system_info"][system_id].update(message.get("value", {}))
            
            # Notify all entities of update
            self.async_set_updated_data(self.data)
            _LOGGER.debug(f"Real-time system data updated: {system_id}")

    def _on_alarm(self, message: Dict[str, Any]) -> None:
        """Handle real-time alarm notifications from MQTT."""
        alarm_code = message.get("alarmCode")
        system_id = message.get("systemId")
        alarm_level = message.get("alarmLevel", "warning")
        
        # Add to alarms list (keep last 100)
        self.data["alarms"].append(message)
        if len(self.data["alarms"]) > 100:
            self.data["alarms"] = self.data["alarms"][-100:]
        
        # Notify all entities
        self.async_set_updated_data(self.data)
        _LOGGER.warning(f"Alarm [{alarm_level}] from {system_id}: {alarm_code} - {message.get('description')}")
