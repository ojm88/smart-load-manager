"""Diagnostic sensors for Smart Load Manager."""

from __future__ import annotations
from .device_info import get_device
from .device_info import ChargerNameMixin, charger_device_info, name_charger_entity
from .installation import charger_entries

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers import entity_registry as er
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChargingCoordinator
from .entity_ids import suggested_entity_id


# Charger measurements only. All user-facing explanations live on the household.
CHARGER_SENSOR_KEYS = (
    "status", "charger_power", "charger_current", "recommended_current",
    "active_phases", "line_voltage",
)

SENSORS = {
    "charging_role": (None, SensorDeviceClass.ENUM, "mdi:priority-high"),
    "household_status": (None, SensorDeviceClass.ENUM, "mdi:home-lightning-bolt"),    "measurement_status": (None, SensorDeviceClass.ENUM, "mdi:clipboard-check-outline"),
    "phase_advice": (None, None, "mdi:lightbulb-outline"),
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
    "charging_role": ("Førsteprioritet i SLM, ikke Easees tekniske masterrolle.", "Software priority in SLM, not the Easee hardware master role."),
    "household_status": (
        "Samlet forklaring på hva laststyringen gjør, hvorfor laster lader eller venter, og eventuelle råd. Brukes av Markdown-kortet.",
        "Shared explanation of load control, why loads are charging or waiting, and any advice. Used by the Markdown card.",
    ),    "measurement_status": (
        "Viser om felles målegrunnlag er klart for laststyring. Åpne sensoren for målekilder og alder på HAN-målingen.",
        "Shows whether the shared measurement inputs are ready for load control. Open for source entities and HAN reading age.",
    ),
    "phase_advice": ("Forslag om enfase når det kan gi plass til begge laderne. Fasevalg endres manuelt.", "Suggests single phase when it may make room for both chargers. Change phase mode manually."),
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
        "Spenningssystem for den bekreftede fysiske tilkoblingen.",
        "Voltage system of the confirmed physical connection.",
    ),
    "line_voltage": (
        "Målt spenning for ladingen. Ved enfase TN vises fase–nøytral; ved trefase TN utledes linjespenningen fra målt fasespenning.",
        "Charging voltage from measured terminal values. Single-phase TN shows phase–neutral; three-phase TN shows line voltage inferred from measured phase voltages.",
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
        "Viser hvorfor anbefalt ladestrøm justeres, eller hvorfor ladingen avventer eller er satt på pause.",
        "Explains why the recommended charging current is adjusted, or why charging is waiting or paused.",
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
    from .installation import platform_loads, add_grouped
    from .site import site_entry
    registry = er.async_get(hass)
    for load in platform_loads(entry):
        coordinator = load.runtime_data
        keys = list(CHARGER_SENSOR_KEYS)
        if len(charger_entries(hass)) == 2:
            keys.append("charging_role")
        legacy = [key for key in SENSORS if key not in keys and key not in {"measurement_status", "household_status", "charging_role"}
                  and registry.async_get_entity_id("sensor", DOMAIN, f"{load.entry_id}_{key}")]
        add_grouped(hass, entry, async_add_entities, [
            ChargingDiagnosticSensor(coordinator, load, key, *SENSORS[key], legacy=key in legacy)
            for key in keys + legacy], "charging")
        if site_entry(hass).entry_id == load.entry_id:
            add_grouped(hass, entry, async_add_entities, [
                ChargingDiagnosticSensor(coordinator, load, key, *SENSORS[key])
                for key in ("household_status", "measurement_status")], "household")


class ChargingDiagnosticSensor(ChargerNameMixin, CoordinatorEntity[ChargingCoordinator], SensorEntity):
    """Read-only diagnostic entity sourced from coordinator data."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, unit, device_class, icon, *, legacy=False):
        super().__init__(coordinator)
        self._key = key
        from .installation import shared_identity
        identity = shared_identity(entry) if key in {"household_status", "measurement_status"} else entry.entry_id
        self._attr_unique_id = f"{identity}_{key}"
        self._attr_translation_key = key
        name_charger_entity(self, entry, "sensor", key)
        self.entity_id = f"sensor.{suggested_entity_id('sensor', key, entry)}"
        self._attr_device_info = charger_device_info(entry)
        if key in {"household_status", "measurement_status"}:
            from .device_info import household_device_info
            self._attr_device_info = household_device_info()
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_icon = icon
        if legacy or key in {"measurement_status", "charging_role"}:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if legacy:
            self._attr_entity_registry_enabled_default = False
        if key == "charging_role":
            self._attr_options = ["primary", "secondary"]
            self._attr_state_class = None
        if key == "measurement_status":
            self._attr_options = ["ready", "waiting"]
        if key == "household_status":
            self._attr_options = ["waiting", "automatic", "manual", "paused", "disconnected", "completed", "mixed"]
        if key in {
            "measurement_status", "household_status",
            "phase_advice", "status", "phase_mode", "output_phase", "grid_type", "voltage_type",
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
        attributes = {"explanation": explanation_nb if norwegian else explanation_en}
        data = self.coordinator.data or {}
        electrical = data.get("electrical", {})
        if self._key == "household_status":
            _, payload = ChargingDiagnosticSensor._household_payload(self)
            attributes.update(payload)
        elif self._key == "phase_advice":
            attributes["card_suffix"] = self.coordinator.entry.data.get("entity_suffix", "")
        elif self._key == "recommended_current":
            attributes.update(
                minimum_current_a=data.get("control_minimum_current_a", data.get("minimum_current_a")),
                maximum_current_a=data.get("max_current_a"),
                last_sent_current_a=data.get("last_sent_current_a"),
                next_regulation_at=data.get("next_regulation_at"),
                regulation_reason=data.get("regulation_reason"),
            )
        elif self._key == "status":
            attributes["card_suffix"] = self.coordinator.entry.data.get("entity_suffix", "")
            attributes.update({key: electrical.get(key) for key in (
                "phase_mode_name", "output_phase_name", "grid_type_name", "voltage_type",
                "line_voltage_v", "phase_neutral_voltage_v", "confidence", "reason", "connection",
            )})
        elif self._key == "control_reason":
            attributes.update(
                easee_reason=electrical.get("no_current_reason"),
                manual_control=("locked" if data.get("auto_control") else
                                "paused" if data.get("charging_paused") else "available"),
                schedule_status=data.get("schedule_reason"),
            )
        elif self._key == "measurement_status":
            entry_data = self.coordinator.entry.data
            attributes.update(
                han_sensor=data.get("han_entity", entry_data.get("han_power_entity")),
                energy_used_sensor=entry_data.get("tariff_used_entity"),
                han_age_seconds=data.get("han_age_seconds"),
                entity_id_migrations=getattr(getattr(self.coordinator.entry, "parent", None), "options", {}).get("entity_id_migrations", {}),
                han_valid=data.get("han_fresh", False),
                inputs_valid=data.get("inputs_valid", False),
                allocation_ready=data.get("site_control_ready", data.get("inputs_valid", False)),
            )
        return attributes

    def _household_payload(self):
        from .household_status import build_household_status
        from .budget import consumption_limit_value
        coordinator = self.coordinator
        owner = coordinator.entry
        site = getattr(coordinator, "site", None)
        controllers = getattr(site, "controllers", {}) or {getattr(owner, "entry_id", "local"): coordinator}
        snapshots = getattr(site, "latest_samples", {}) if len(controllers) > 1 else {}
        loads = []
        devices = None
        if hasattr(self.hass, "data"):
            from homeassistant.helpers import device_registry as dr
            devices = dr.async_get(self.hass)
        for key, controller in controllers.items():
            entry = controller.entry
            name = str(getattr(entry, "title", key)).removeprefix("Smart Load Manager OJM – ")
            device = get_device(devices, entry.data.get("charger_device")) if devices is not None else None
            if device:
                name = device.name_by_user or device.name or name
            data = snapshots.get(key, getattr(controller, "data", None))
            loads.append({"id": key, "name": name, "data": data,
                          "available": key in snapshots or getattr(controller, "last_update_success", True)})
        # Include configured peers that are still starting up, so a household
        # overview never silently omits a temporarily unavailable load.
        if hasattr(self.hass, "config_entries"):
            for entry in charger_entries(self.hass):
                if entry.entry_id not in controllers:
                    name = entry.title.removeprefix("Smart Load Manager OJM – ")
                    device = get_device(devices, entry.data.get("charger_device")) if devices is not None else None
                    if device:
                        name = device.name_by_user or device.name or name
                    loads.append({"id": entry.entry_id, "name": name, "data": None, "available": False})
        options = getattr(owner, "options", {})
        priority = options.get("priority_charger", getattr(owner, "entry_id", "local"))
        if priority not in {load["id"] for load in loads}:
            priority = getattr(owner, "entry_id", "local")
        limit = consumption_limit_value(owner) if hasattr(owner, "options") else (coordinator.data or {}).get("hourly_limit_kwh", 15)
        state, payload = build_household_status(loads, limit_kwh=limit,
            mode=options.get("allocation_mode", "both"), priority=priority,
            norwegian=str(self.hass.config.language or "").startswith("nb"))
        reference = snapshots.get(getattr(owner, "entry_id", ""), coordinator.data or {})
        payload.update({key: reference.get(key) for key in (
            "han_power_w", "energy_used_kwh", "energy_estimate_kwh", "safety_margin_kwh", "minutes_left",
        )})
        return state, payload

    def _priority_id(self):
        from .site import site_entry
        if not hasattr(self.hass, "config_entries"):
            return getattr(self.coordinator.entry, "entry_id", None)
        owner = site_entry(self.hass)
        priority = owner.options.get("priority_charger", owner.entry_id)
        return priority if priority in {e.entry_id for e in charger_entries(self.hass)} else owner.entry_id

    @property
    def native_value(self):
        if self._key == "household_status":
            return ChargingDiagnosticSensor._household_payload(self)[0]
        data = self.coordinator.data or {}
        electrical = data.get("electrical", {})
        norwegian = str(self.hass.config.language or "").startswith("nb")
        values = {
            "charging_role": ("primary" if getattr(self.coordinator.entry, "entry_id", None) == ChargingDiagnosticSensor._priority_id(self) else "secondary") if self._key == "charging_role" else None,
            "measurement_status": "ready" if (data.get("inputs_valid") and data.get("han_fresh")
                                                    and data.get("site_control_ready", True)) else "waiting",
            "phase_advice": data.get("phase_advice", "Ingen anbefaling om fasebytte nå."),
            "status": data.get("status", "unknown"),
            "phase_mode": electrical.get("phase_mode_name", "unknown"),
            "output_phase": electrical.get("output_phase_name", "unknown"),
            "active_phases": electrical.get("active_phases"),
            "grid_type": electrical.get("grid_type_name", "unknown"),
            "voltage_type": electrical.get("voltage_type", "unknown"),
            "line_voltage": (electrical.get("phase_neutral_voltage_v")
                             if electrical.get("effective_phases") == 1 and electrical.get("phase_neutral_voltage_v") is not None
                             else electrical.get("line_voltage_v")),
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
