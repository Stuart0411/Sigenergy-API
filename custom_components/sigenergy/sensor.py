"""Sensor platform for Sigenergy integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
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
    """Set up Sigenergy sensors."""
    coordinator: SigenergyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SensorEntity] = []
    for system in coordinator.data.get("systems", []):
        system_id = str(system.get("id"))
        if not system_id:
            continue

        system_name = system.get("name") or f"System {system_id}"

        entities.extend(
            [
                SigenergySystemPowerSensor(coordinator, system_id, system_name),
                SigenergySystemSocSensor(coordinator, system_id, system_name),
                SigenergyPvPowerSensor(coordinator, system_id, system_name),
                SigenergyGridPowerSensor(coordinator, system_id, system_name),
                SigenergyEvPowerSensor(coordinator, system_id, system_name),
                SigenergyLoadPowerSensor(coordinator, system_id, system_name),
                SigenergyBatteryFlowPowerSensor(coordinator, system_id, system_name),
                SigenergyDailyGenerationSensor(coordinator, system_id, system_name),
                SigenergyMonthlyGenerationSensor(coordinator, system_id, system_name),
                SigenergyAnnualGenerationSensor(coordinator, system_id, system_name),
                SigenergyLifetimeGenerationSensor(coordinator, system_id, system_name),
                SigenergyLifetimeCo2Sensor(coordinator, system_id, system_name),
                SigenergyLifetimeCoalSensor(coordinator, system_id, system_name),
                SigenergyLifetimeTreesSensor(coordinator, system_id, system_name),
            ]
        )

    async_add_entities(entities)


class SigenergySystemSensor(SigenergyEntity, SensorEntity):
    """Base class for system-level sensors."""

    def __init__(self, coordinator: SigenergyDataUpdateCoordinator, system_id: str, system_name: str) -> None:
        super().__init__(coordinator, system_id, system_id, system_name)


class SigenergyPowerSensor(SigenergySystemSensor):
    """Base class for power sensors."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT


class SigenergyEnergySensor(SigenergySystemSensor):
    """Base class for energy counters."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING


class SigenergySystemPowerSensor(SigenergyPowerSensor):
    """Current total system power."""

    _attr_translation_key = "system_power"

    @property
    def native_value(self):
        value = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {}).get("loadPower")
        if value is None:
            return None
        return float(value) * 1000


class SigenergySystemSocSensor(SigenergySystemSensor):
    """System battery SOC."""

    _attr_translation_key = "system_soc"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get("energy_flow", {}).get(self.system_id, {}).get("batterySoc")


class SigenergyPvPowerSensor(SigenergyPowerSensor):
    _attr_translation_key = "pv_power"

    @property
    def native_value(self):
        value = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {}).get("pvPower")
        return None if value is None else float(value) * 1000


class SigenergyGridPowerSensor(SigenergyPowerSensor):
    _attr_translation_key = "grid_power"

    @property
    def native_value(self):
        value = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {}).get("gridPower")
        return None if value is None else float(value) * 1000


class SigenergyEvPowerSensor(SigenergyPowerSensor):
    _attr_translation_key = "ev_power"

    @property
    def native_value(self):
        value = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {}).get("evPower")
        return None if value is None else float(value) * 1000


class SigenergyLoadPowerSensor(SigenergyPowerSensor):
    _attr_translation_key = "load_power"

    @property
    def native_value(self):
        value = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {}).get("loadPower")
        return None if value is None else float(value) * 1000


class SigenergyBatteryFlowPowerSensor(SigenergyPowerSensor):
    _attr_translation_key = "battery_power"

    @property
    def native_value(self):
        value = self.coordinator.data.get("energy_flow", {}).get(self.system_id, {}).get("batteryPower")
        return None if value is None else float(value) * 1000


class SigenergyDailyGenerationSensor(SigenergyEnergySensor):
    _attr_translation_key = "daily_power_generation"

    @property
    def native_value(self):
        value = self.coordinator.data.get("summary", {}).get(self.system_id, {}).get("dailyPowerGeneration")
        return None if value is None else float(value) * 1000


class SigenergyMonthlyGenerationSensor(SigenergyEnergySensor):
    _attr_translation_key = "monthly_power_generation"

    @property
    def native_value(self):
        value = self.coordinator.data.get("summary", {}).get(self.system_id, {}).get("monthlyPowerGeneration")
        return None if value is None else float(value) * 1000


class SigenergyAnnualGenerationSensor(SigenergyEnergySensor):
    _attr_translation_key = "annual_power_generation"

    @property
    def native_value(self):
        value = self.coordinator.data.get("summary", {}).get(self.system_id, {}).get("annualPowerGeneration")
        return None if value is None else float(value) * 1000


class SigenergyLifetimeGenerationSensor(SigenergyEnergySensor):
    _attr_translation_key = "lifetime_power_generation"

    @property
    def native_value(self):
        value = self.coordinator.data.get("summary", {}).get(self.system_id, {}).get("lifetimePowerGeneration")
        return None if value is None else float(value) * 1000


class SigenergyLifetimeCo2Sensor(SigenergySystemSensor):
    _attr_translation_key = "lifetime_co2_reduction"
    _attr_native_unit_of_measurement = "t"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        return self.coordinator.data.get("summary", {}).get(self.system_id, {}).get("lifetimeCo2")


class SigenergyLifetimeCoalSensor(SigenergySystemSensor):
    _attr_translation_key = "lifetime_coal_saved"
    _attr_native_unit_of_measurement = "t"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        return self.coordinator.data.get("summary", {}).get(self.system_id, {}).get("lifetimeCoal")


class SigenergyLifetimeTreesSensor(SigenergySystemSensor):
    _attr_translation_key = "lifetime_trees_planted"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        return self.coordinator.data.get("summary", {}).get(self.system_id, {}).get("lifetimeTreeEquivalent")
