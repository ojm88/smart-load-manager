"""Diagnostic sensors for Smart Load Manager."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ChargingCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up diagnostic sensors for one charger config entry."""
    coordinator: ChargingCoordinator = entry.runtime_data
    async_add_entities(
        [
            ChargingDiagnosticSensor(coordinator, entry, "status", "Laderstatus"),
            ChargingDiagnosticSensor(coordinator, entry, "phase_mode", "Valgt fasemodus"),
            ChargingDiagnosticSensor(coordinator, entry, "output_phase", "Easee utgangsfase"),
            ChargingDiagnosticSensor(coordinator, entry, "active_phases", "Aktive faser"),
            ChargingDiagnosticSensor(coordinator, entry, "grid_type", "Easee detektert nettype"),
            ChargingDiagnosticSensor(coordinator, entry, "voltage_type", "Detektert spenningssystem"),
            ChargingDiagnosticSensor(coordinator, entry, "line_voltage", "Beregnet linjespenning", "V", SensorDeviceClass.VOLTAGE),
            ChargingDiagnosticSensor(coordinator, entry, "ln_voltage", "Målt fase-nøytral spenning", "V", SensorDeviceClass.VOLTAGE),
            ChargingDiagnosticSensor(coordinator, entry, "minimum_current", "Nedre ladestrømgrense", "A", SensorDeviceClass.CURRENT),
            ChargingDiagnosticSensor(coordinator, entry, "recommended_current", "Anbefalt ladestrøm", "A", SensorDeviceClass.CURRENT),
            ChargingDiagnosticSensor(coordinator, entry, "charger_power", "Ladeeffekt", "W", SensorDeviceClass.POWER),
            ChargingDiagnosticSensor(coordinator, entry, "han_power", "HAN-effekt normalisert", "W", SensorDeviceClass.POWER),
            ChargingDiagnosticSensor(coordinator, entry, "energy_used", "EnergyTariff brukt denne timen", "kWh", SensorDeviceClass.ENERGY),
            ChargingDiagnosticSensor(coordinator, entry, "energy_estimate", "EnergyTariff estimat denne timen", "kWh", SensorDeviceClass.ENERGY),
            ChargingDiagnosticSensor(coordinator, entry, "hourly_limit", "Timegrense", "kWh", SensorDeviceClass.ENERGY),
            ChargingDiagnosticSensor(coordinator, entry, "confidence", "Deteksjonssikkerhet"),
            ChargingDiagnosticSensor(coordinator, entry, "reason", "Deteksjonsgrunnlag"),
            ChargingDiagnosticSensor(coordinator, entry, "control_reason", "Styringens forklaring"),
            ChargingDiagnosticSensor(coordinator, entry, "no_current_reason", "Easee årsak til begrensning"),
            ChargingDiagnosticSensor(coordinator, entry, "auto_control", "Automatisk styring aktiv"),
            ChargingDiagnosticSensor(coordinator, entry, "han_age", "HAN-måling alder", "s", SensorDeviceClass.DURATION),
            ChargingDiagnosticSensor(coordinator, entry, "han_fresh", "HAN-måling gyldig"),
            ChargingDiagnosticSensor(coordinator, entry, "schedule_enabled", "Tidsstyring aktiv"),
            ChargingDiagnosticSensor(coordinator, entry, "schedule_reason", "Tidsstyring status"),
        ]
    )


class ChargingDiagnosticSensor(CoordinatorEntity[ChargingCoordinator], SensorEntity):
    """Read-only diagnostic entity sourced from coordinator data."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, key, name, unit=None, device_class=None):
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_has_entity_name = True
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Smart Load Manager",
            model="Easee charging control",
            name=entry.title,
        )
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if key in {"status", "phase_mode", "output_phase", "grid_type", "voltage_type", "confidence", "reason", "control_reason", "no_current_reason", "auto_control", "han_fresh", "schedule_enabled", "schedule_reason"}:
            self._attr_state_class = None

    @property
    def extra_state_attributes(self):
        """Expose underlying terminal readings for inspection in More Info."""
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
            "han_fresh": "Ja" if data["han_fresh"] else "Nei",
            "schedule_enabled": "on" if data["schedule_enabled"] else "off",
            "schedule_reason": data["schedule_reason"],
        }
        return values[self._key]

