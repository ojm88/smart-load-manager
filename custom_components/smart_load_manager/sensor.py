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
from .entity_ids import suggested_entity_id


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
    "charger_current": ("A", SensorDeviceClass.CURRENT, "mdi:current-ac"),
    "charger_power": ("W", SensorDeviceClass.POWER, "mdi:ev-station"),
    "han_power": ("W", SensorDeviceClass.POWER, "mdi:home-lightning-bolt"),
    "energy_used": ("kWh", SensorDeviceClass.ENERGY, "mdi:lightning-bolt"),
    "energy_estimate": ("kWh", SensorDeviceClass.ENERGY, "mdi:chart-timeline-variant"),
    "confidence": (None, None, "mdi:check-decagram-outline"),
    "reason": (None, None, "mdi:text-box-check-outline"),
    "control_reason": (None, None, "mdi:comment-question-outline"),
    "manual_control_status": (None, None, "mdi:lock-outline"),
    "no_current_reason": (None, None, "mdi:alert-circle-outline"),
    "auto_control": (None, None, "mdi:robot"),
    "han_age": ("s", SensorDeviceClass.DURATION, "mdi:timer-outline"),
    "han_fresh": (None, None, "mdi:check-network-outline"),
    "schedule_enabled": (None, None, "mdi:clock-check-outline"),
    "schedule_reason": (None, None, "mdi:clock-alert-outline"),
}


SENSOR_EXPLANATIONS = {
    "status": (
        "Viser om bilen er frakoblet, lader eller venter.",
        "Shows whether the car is disconnected, charging, or waiting.",
    ),
    "phase_mode": (
        "Faseinnstillingen laderen er satt til.",
        "The phase setting selected on the charger.",
    ),
    "output_phase": (
        "Viser hvilken fase Easee har koblet til ladeuttaket.",
        "Shows which phase Easee has assigned to the charging output.",
    ),
    "active_phases": (
        "Antall faser som faktisk trekker strøm under lading.",
        "Number of phases actually drawing current while charging.",
    ),
    "grid_type": (
        "Strømnettypen Easee rapporterer.",
        "The grid type reported by Easee.",
    ),
    "voltage_type": (
        "Beregnet spenningssystem ut fra målt spenning.",
        "Voltage system inferred from measured voltage.",
    ),
    "line_voltage": (
        "Målt eller beregnet spenning mellom fasene.",
        "Measured or inferred voltage between phases.",
    ),
    "ln_voltage": (
        "Målt spenning mellom fase og nøytral.",
        "Measured voltage between a phase and neutral.",
    ),
    "minimum_current": (
        "Laveste strøm som denne målte ladeformen tillater.",
        "Minimum current allowed for the detected charging setup.",
    ),
    "recommended_current": (
        "Strømgrensen laststyringen anbefaler akkurat nå.",
        "Current limit recommended by load control right now.",
    ),
    "max_current": (
        "Høyeste strømgrense Easee rapporterer for laderen eller kursen.",
        "Highest current limit Easee reports for the charger or circuit.",
    ),
    "charger_current": (
        "Strømmen Easee måler til bilen nå.",
        "Current Easee measures going to the car.",
    ),
    "charger_power": (
        "Effekten laderen leverer til bilen nå.",
        "Power the charger is delivering to the car now.",
    ),
    "han_power": (
        "Øyeblikkelig effekt fra den valgte HAN-måleren.",
        "Instantaneous power from the selected HAN meter.",
    ),
    "energy_used": (
        "Energi brukt hittil i denne timen, levert av EnergyTariff.",
        "Energy used so far this hour, supplied by EnergyTariff.",
    ),
    "energy_estimate": (
        "EnergyTariffs anslag for totalt forbruk denne timen. Vises kun til informasjon.",
        "EnergyTariff's estimate of total use this hour. Informational only.",
    ),
    "confidence": (
        "Hvor sikkert fase- og spenningsgrunnlaget kan bestemmes.",
        "Confidence in the detected phase and voltage information.",
    ),
    "reason": (
        "Kort forklaring på hvordan fase og spenning ble tolket.",
        "Brief explanation of how phase and voltage were interpreted.",
    ),
    "control_reason": (
        "Forklarer med en enkel tekst hvorfor bilen lader, venter eller får mindre strøm.",
        "In plain language, explains why charging is running, waiting, or reduced.",
    ),
    "manual_control_status": (
        "Viser om manuell ladestrøm kan endres. Den er låst når automatisk laststyring er på.",
        "Shows whether manual current can be changed. It is locked while automatic control is on.",
    ),
    "no_current_reason": (
        "Easees rapporterte årsak dersom laderen ikke trekker strøm.",
        "Reason reported by Easee when the charger is not drawing current.",
    ),
    "auto_control": (
        "Viser om automatisk laststyring er slått på.",
        "Shows whether automatic load control is enabled.",
    ),
    "han_age": (
        "Sekunder siden HAN-måleren sist oppdaterte verdien.",
        "Seconds since the HAN meter last updated its value.",
    ),
    "han_fresh": (
        "Viser om HAN-målingen er oppdatert og gyldig for styring.",
        "Shows whether the HAN reading is fresh and valid for control.",
    ),
    "schedule_enabled": (
        "Viser om tidsstyring begrenser når lading kan starte.",
        "Shows whether the charging time schedule is enabled.",
    ),
    "schedule_reason": (
        "Forklarer om tidsvinduet tillater lading akkurat nå.",
        "Explains whether the schedule currently allows charging.",
    ),
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
        self.entity_id = f"sensor.{suggested_entity_id('sensor', key)}"
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
            "manual_control_status", "auto_control", "han_fresh",
            "schedule_enabled", "schedule_reason",
        }:
            self._attr_state_class = None

    @property
    def extra_state_attributes(self):
        """Give the user one short explanation, without repeating raw data."""
        norwegian = str(self.hass.config.language or "").startswith("nb")
        explanation_nb, explanation_en = SENSOR_EXPLANATIONS[self._key]
        return {"explanation": explanation_nb if norwegian else explanation_en}

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        electrical = data.get("electrical", {})
        norwegian = str(self.hass.config.language or "").startswith("nb")
        values = {
            "status": data.get("status", "unknown"),
            "phase_mode": electrical.get("phase_mode_name", "unknown"),
            "output_phase": electrical.get("output_phase_name", "unknown"),
            "active_phases": electrical.get("active_phases"),
            "grid_type": electrical.get("grid_type_name", "unknown"),
            "voltage_type": electrical.get("voltage_type", "unknown"),
            "line_voltage": electrical.get("line_voltage_v"),
            "ln_voltage": electrical.get("phase_neutral_voltage_v"),
            "minimum_current": data.get("minimum_current_a"),
            "recommended_current": data.get("recommended_current_a"),
            "max_current": data.get("max_current_a"),
            "charger_current": data.get("charger_current_a"),
            "charger_power": round(data["charger_power_w"]) if data.get("charger_power_w") is not None else None,
            "han_power": round(data["han_power_w"]) if data.get("han_power_w") is not None else None,
            "energy_used": data.get("energy_used_kwh"),
            "energy_estimate": data.get("energy_estimate_kwh"),
            "confidence": electrical.get("confidence", "unknown"),
            "reason": electrical.get("reason", "unknown"),
            "control_reason": data.get("control_reason", "unknown"),
            "manual_control_status": (
                (
                    "Låst – slå av automatisk laststyring for å endre"
                    if norwegian
                    else "Locked – turn off automatic control to change"
                )
                if data.get("auto_control", False)
                else (
                    "Klar – automatisk laststyring er av"
                    if norwegian
                    else "Ready – automatic control is off"
                )
            ),
            "no_current_reason": electrical.get("no_current_reason", "unknown"),
            "auto_control": "on" if data.get("auto_control", False) else "off",
            "han_age": data.get("han_age_seconds"),
            "han_fresh": "on" if data.get("han_fresh", False) else "off",
            "schedule_enabled": "on" if data.get("schedule_enabled", False) else "off",
            "schedule_reason": data.get("schedule_reason", "unknown"),
        }
        return values[self._key]
