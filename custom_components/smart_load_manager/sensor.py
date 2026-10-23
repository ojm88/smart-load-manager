"""Diagnostic sensors for Smart Load Manager."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChargingCoordinator


SENSORS = {
    "status": (None, None, "mdi:ev-station"),
    "phase_mode": (None, None, "mdi:current-ac"),
    "output_phase": (None, None, "mdi:sine-wave"),
    "active_phases": (None, None, "mdi:transmission-tower"),
    "grid_type": (None, None, "mdi:transmission-tower"),
    "voltage_type": (None, None, "mdi:flash"),
    "line_voltage": ("V", SensorDeviceClass.VOLTAGE, "mdi:flash-outline"),
    "ln_voltage": ("V", SensorDeviceClass.VOLTAGE, "mdi:flash-outline"),
    "minimum_current": ("A", SensorDeviceClass.CURRENT, "mdi:current-ac"),
    "recommended_current": ("A", SensorDeviceClass.CURRENT, "mdi:current-ac"),
    "max_current": ("A", SensorDeviceClass.CURRENT, "mdi:current-ac"),
    "charger_power": ("W", SensorDeviceClass.POWER, "mdi:ev-station"),
    "han_power": ("W", SensorDeviceClass.POWER, "mdi:home-lightning-bolt"),
    "energy_used": ("kWh", SensorDeviceClass.ENERGY, "mdi:lightning-bolt"),
    "energy_estimate": ("kWh", SensorDeviceClass.ENERGY, "mdi:chart-timeline-variant"),
    "hourly_limit": ("kWh", SensorDeviceClass.ENERGY, "mdi:counter"),
    "confidence": (None, None, "mdi:check-decagram-outline"),
    "reason": (None, None, "mdi:text-box-check-outline"),
    "control_reason": (None, None, "mdi:comment-question-outline"),
    "no_current_reason": (None, None, "mdi:alert-circle-outline"),
    "auto_control": (None, None, "mdi:robot"),
    "han_age": ("s", SensorDeviceClass.DURATION, "mdi:timer-outline"),
    "han_fresh": (None, None, "mdi:check-network-outline"),
    "schedule_enabled": (None, None, "mdi:clock-check-outline"),
    "schedule_reason": (None, None, "mdi:clock-alert-outline"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up read-only sensors for one configured charger."""
    coordinator: ChargingCoordinator = entry.runtime_data
    async_add_entities(
        [ChargingDiagnosticSensor(coordinator, entry, key, *details) for key, details in SENSORS.items()]
    )


class ChargingDiagnosticSensor(CoordinatorEntity[ChargingCoordinator], SensorEntity):
    """Read-only diagnostic entity sourced from coordinator data."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, unit, device_class, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Smart Load Manager",
            model="Easee charging control",
            name=entry.title,
        )
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        if key in {
            "status", "phase_mode", "output_phase", "grid_type", "voltage_type",
            "confidence", "reason", "control_reason", "no_current_reason",
            "auto_control", "han_fresh", "schedule_enabled", "schedule_reason",
        }:
            self._attr_state_class = None

    @property
    def extra_state_attributes(self):
        """Expose raw Easee measurements and selected source in More Info."""
        data = self.coordinator.data or {}
        return {
            "terminal_currents_a": data.get("terminal_currents_a", {}),
            "terminal_voltages_v": data.get("terminal_voltages_v", {}),
            "easee_enum_codes": data.get("easee_enum_codes", {}),
            "easee_entities": data.get("charger_entities", {}),
            "han_power_entity": data.get("han_entity"),
        }

    @property
    def native_value(self):
        data = self.coordinator.data
        electrical = data["electrical"]
        values = {
            "status": data["status"],
            "phase_mode": electrical["phase_mode_name"],
            "output_phase": electrical["output_phase_name"],
            "active_phases": electrical["active_phases"],
            "grid_type": electrical["grid_type_name"],
            "voltage_type": electrical["voltage_type"],
            "line_voltage": electrical["line_voltage_v"],
            "ln_voltage": electrical["phase_neutral_voltage_v"],
            "minimum_current": data["minimum_current_a"],
            "recommended_current": data["recommended_current_a"],
            "max_current": data["max_current_a"],
            "charger_power": data["charger_power_w"],
            "han_power": data["han_power_w"],
            "energy_used": data["energy_used_kwh"],
            "energy_estimate": data["energy_estimate_kwh"],
            "hourly_limit": data["hourly_limit_kwh"],
            "confidence": electrical["confidence"],
            "reason": electrical["reason"],
            "control_reason": data["control_reason"],
            "no_current_reason": electrical["no_current_reason"],
            "auto_control": "on" if data["auto_control"] else "off",
            "han_age": data["han_age_seconds"],
            "han_fresh": "on" if data["han_fresh"] else "off",
            "schedule_enabled": "on" if data["schedule_enabled"] else "off",
            "schedule_reason": data["schedule_reason"],
        }
        return values[self._key]
