"""Sensor entities for Sigenergy integration."""

from typing import Any, Dict, Optional
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import POWER_WATT, PERCENTAGE, ENERGY_WATT_HOUR
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
    """Set up Sigenergy sensors."""
    coordinator: SigenergySomeDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities = []

    # Create sensor entities for each system and device
    for system in coordinator.data.get("systems", []):
        system_id = system.get("id")
        system_name = system.get("name", f"System {system_id}")

        # Add system-level power sensor
        entities.append(
            SigenergySomeSystemPowerSensor(
                coordinator=coordinator,
                system_id=system_id,
                device_id=system_id,
                device_name=system_name,
            )
        )

        # Add system-level SOC sensor
        entities.append(
            SigenergySomeSystemSOCSensor(

                        # Add energy flow sensors
                        entities.append(
                            SigenergySomePVPowerSensor(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeGridPowerSensor(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeEVPowerSensor(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeLoadPowerSensor(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeBatteryPowerFlowSensor(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )

                        # Add summary sensors
                        entities.append(
                            SigenergySomeDailyPowerGeneration(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeMonthlyPowerGeneration(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeAnnualPowerGeneration(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeLifetimePowerGeneration(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeLifetimeCO2Reduction(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeLifetimeCoalSaved(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                        entities.append(
                            SigenergySomeLifetimeTreesPlanted(
                                coordinator=coordinator,
                                system_id=system_id,
                                device_id=system_id,
                                device_name=system_name,
                            )
                        )
                coordinator=coordinator,
                system_id=system_id,
                device_id=system_id,
                device_name=system_name,
            )
        )

        # Add sensors for each device
        for device in coordinator.data.get("devices", {}).get(system_id, []):
            device_id = device.get("id")
            device_name = device.get("name", f"Device {device_id}")
            device_type = device.get("type")

            if device_type == "battery":
                entities.append(
                    SigenergySomeBatteryPowerSensor(
                        coordinator=coordinator,
                        system_id=system_id,
                        device_id=device_id,
                        device_name=device_name,
                    )
                )
            elif device_type == "charger":
                entities.append(
                    SigenergySomeChargerStatusSensor(
                        coordinator=coordinator,
                        system_id=system_id,
                        device_id=device_id,
                        device_name=device_name,
                    )
                )

    async_add_entities(entities)


class SigenergySomePowerSensorBase(SensorEntity, SigenergySomeCoordinatorEntity):
    """Base class for power sensors."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = POWER_WATT
    _attr_state_class = SensorStateClass.MEASUREMENT


class SigenergySomeSystemPowerSensor(SigenergySomePowerSensorBase):
    """System power sensor."""

    _attr_translation_key = "system_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        device_data = (
            self.coordinator.data.get("device_data", {})
            .get(self.system_id, {})
            .get(self.device_id, {})
        )
        # Adjust key based on actual API response
        return device_data.get("total_power")


class SigenergySomeSystemSOCSensor(SensorEntity, SigenergySomeCoordinatorEntity):
    """System state of charge sensor."""

    _attr_translation_key = "system_soc"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        device_data = (
            self.coordinator.data.get("device_data", {})
            .get(self.system_id, {})
            .get(self.device_id, {})
        )
        return device_data.get("soc")


class SigenergySomeBatteryPowerSensor(SigenergySomePowerSensorBase):
    """Battery power sensor."""

    _attr_translation_key = "battery_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        device_data = (
            self.coordinator.data.get("device_data", {})
            .get(self.system_id, {})
            .get(self.device_id, {})
        )
        return device_data.get("power")


class SigenergySomeChargerStatusSensor(SensorEntity, SigenergySomeCoordinatorEntity):
    """Charger status sensor."""

    _attr_translation_key = "charger_status"

    @property
    def native_value(self) -> Optional[str]:
        """Return the sensor value."""
        device_data = (
            self.coordinator.data.get("device_data", {})
            .get(self.system_id, {})
            .get(self.device_id, {})
        )
        return device_data.get("status")


# Energy Flow Sensors (from Doc 36 endpoint)

class SigenergySomePVPowerSensor(SigenergySomePowerSensorBase):
    """PV power sensor."""

    _attr_translation_key = "pv_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        energy_flow = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {})
        return energy_flow.get("pvPower")


class SigenergySomeGridPowerSensor(SigenergySomePowerSensorBase):
    """Grid power sensor (positive=export, negative=import)."""

    _attr_translation_key = "grid_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        energy_flow = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {})
        return energy_flow.get("gridPower")


class SigenergySomeEVPowerSensor(SigenergySomePowerSensorBase):
    """EV charger power sensor."""

    _attr_translation_key = "ev_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        energy_flow = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {})
        return energy_flow.get("evPower")


class SigenergySomeLoadPowerSensor(SigenergySomePowerSensorBase):
    """Load power sensor."""

    _attr_translation_key = "load_power"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        energy_flow = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {})
        return energy_flow.get("loadPower")


class SigenergySomeBatteryPowerFlowSensor(SigenergySomePowerSensorBase):
    """Battery power flow sensor (positive=charging, negative=discharging)."""

    _attr_translation_key = "battery_power_flow"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        energy_flow = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {})
        return energy_flow.get("batteryPower")


# Power Generation Sensors (from Doc 35 endpoint)

class SigenergySomeEnergySensorBase(SensorEntity, SigenergySomeCoordinatorEntity):
    """Base class for energy sensors."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = ENERGY_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING


class SigenergySomeDailyPowerGeneration(SigenergySomeEnergySensorBase):
    """Daily power generation sensor."""

    _attr_translation_key = "daily_power_generation"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value in Wh (API returns kWh)."""
        summary = self.coordinator.data.get("summary", {}).get(self.system_id, {})
        value = summary.get("dailyPowerGeneration")
        return value * 1000 if value else None  # Convert kWh to Wh


class SigenergySomeMonthlyPowerGeneration(SigenergySomeEnergySensorBase):
    """Monthly power generation sensor."""

    _attr_translation_key = "monthly_power_generation"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value in Wh (API returns kWh)."""
        summary = self.coordinator.data.get("summary", {}).get(self.system_id, {})
        value = summary.get("monthlyPowerGeneration")
        return value * 1000 if value else None  # Convert kWh to Wh


class SigenergySomeAnnualPowerGeneration(SigenergySomeEnergySensorBase):
    """Annual power generation sensor."""

    _attr_translation_key = "annual_power_generation"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value in Wh (API returns kWh)."""
        summary = self.coordinator.data.get("summary", {}).get(self.system_id, {})
        value = summary.get("annualPowerGeneration")
        return value * 1000 if value else None  # Convert kWh to Wh


class SigenergySomeLifetimePowerGeneration(SigenergySomeEnergySensorBase):
    """Lifetime power generation sensor."""

    _attr_translation_key = "lifetime_power_generation"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value in Wh (API returns kWh)."""
        summary = self.coordinator.data.get("summary", {}).get(self.system_id, {})
        value = summary.get("lifetimePowerGeneration")
        return value * 1000 if value else None  # Convert kWh to Wh


class SigenergySomeEnvironmentalSensorBase(SensorEntity, SigenergySomeCoordinatorEntity):
    """Base class for environmental impact sensors."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING


class SigenergySomeLifetimeCO2Reduction(SigenergySomeEnvironmentalSensorBase):
    """Lifetime CO2 reduction sensor."""

    _attr_translation_key = "lifetime_co2_reduction"
    _attr_native_unit_of_measurement = "t"
    _attr_icon = "mdi:leaf"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        summary = self.coordinator.data.get("summary", {}).get(self.system_id, {})
        return summary.get("lifetimeCo2")


class SigenergySomeLifetimeCoalSaved(SigenergySomeEnvironmentalSensorBase):
    """Lifetime coal saved sensor."""

    _attr_translation_key = "lifetime_coal_saved"
    _attr_native_unit_of_measurement = "t"
    _attr_icon = "mdi:cloud-off-outline"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        summary = self.coordinator.data.get("summary", {}).get(self.system_id, {})
        return summary.get("lifetimeCoal")


class SigenergySomeLifetimeTreesPlanted(SigenergySomeEnvironmentalSensorBase):
    """Lifetime equivalent trees planted sensor."""

    _attr_translation_key = "lifetime_trees_planted"
    _attr_icon = "mdi:tree"

    @property
    def native_value(self) -> Optional[float]:
        """Return the sensor value."""
        summary = self.coordinator.data.get("summary", {}).get(self.system_id, {})
        return summary.get("lifetimeTreeEquivalent")
