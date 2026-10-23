"""Coordinate selected Easee, HAN, and EnergyTariff entities and control."""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, replace

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from homeassistant.util import dt as dt_util

from .calculations import (
    ElectricalSnapshot,
    detect_electrical_setup,
    han_measurement_is_fresh,
    kw_per_ampere,
    power_to_watts,
    recommended_current_a,
    schedule_window_active,
)
from .const import (
    CONF_HAN_POWER_ENTITY,
    CONF_HOURLY_LIMIT_KWH,
    CONF_SAFETY_MARGIN_KWH,
    CONF_SCHEDULE_START_TIME,
    CONF_SCHEDULE_ENABLED,
    DEFAULT_SCHEDULE_START_TIME,
    HAN_MAX_AGE_SECONDS,
    SCHEDULE_WINDOW_HOURS,
    CONF_TARIFF_USED_ENTITY,
    TARIFF_ESTIMATE_ENTITY,
    TARIFF_USED_ENTITY,
    UPDATE_INTERVAL,
)
from .entity_resolution import resolve_easee_entities
from .budget import consumption_limit_value
from .control import async_send_dynamic_limit, target_current_for_control

_LOGGER = logging.getLogger(__name__)


def _number(state) -> float:
    if state is None or state.state in {"unknown", "unavailable"}:
        raise ValueError("Kildesensoren er utilgjengelig")
    value = float(state.state)
    if not math.isfinite(value):
        raise ValueError("Kildesensoren har en ugyldig tallverdi")
    return value


def _numeric_attributes(attributes, prefix: str) -> dict[str, float]:
    """Extract numeric Easee measurements; ignore empty/unavailable attributes."""
    values: dict[str, float] = {}
    for key, value in attributes.items():
        if not key.startswith(prefix) or value in (None, ""):
            continue
        try:
            values[key.removeprefix(prefix)] = float(value)
        except (TypeError, ValueError):
            continue
    return values


class ChargingCoordinator(DataUpdateCoordinator[dict[str, object]]):
    """Refresh selected sources and manage the opt-in Easee current limit."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name="Smart Load Manager",
            update_interval=UPDATE_INTERVAL,
        )
        self.entry = entry
        self.easee = resolve_easee_entities(
            hass, str(entry.data["charger_device"])
        )
        self.auto_control = False
        self.schedule_enabled = bool(
            entry.options.get(CONF_SCHEDULE_ENABLED, False)
        )
        self.last_commanded_current: int | None = None
        self._last_command_at = 0.0
        self.last_known_minimum_current: int | None = None
        self.last_known_kw_per_amp: float | None = None
        self._last_known_phase_mode: int | None = None
        self._last_known_voltage_type: str | None = None
        self._last_known_grid_type_code: int | None = None
        self._last_known_electrical = None

    async def _async_update_data(self) -> dict[str, object]:
        try:
            status_state = self.hass.states.get(self.easee.status)
            current_state = self.hass.states.get(self.easee.current)
            voltage_state = self.hass.states.get(self.easee.voltage)
            if not all((status_state, current_state, voltage_state)):
                raise ValueError("Easee-sensorene er ikke tilgjengelige")
            if any(
                state.state in {"unknown", "unavailable"}
                for state in (status_state, current_state, voltage_state)
            ):
                raise ValueError("En eller flere Easee-sensorer er utilgjengelige")

            current_attrs = current_state.attributes
            voltage_attrs = voltage_state.attributes
            currents = _numeric_attributes(current_attrs, "state_inCurrent")
            voltages = _numeric_attributes(voltage_attrs, "state_inVoltage")
            phase_code = int(status_state.attributes.get("state_outputPhase", 0) or 0)
            phase_mode = int(status_state.attributes.get("config_phaseMode", 0) or 0)
            grid_type = int(status_state.attributes.get("config_detectedPowerGridType", 0) or 0)
            no_current_reason = int(status_state.attributes.get("state_reasonForNoCurrent", -1) or -1)
            electrical = detect_electrical_setup(
                ElectricalSnapshot(
                    output_phase=phase_code,
                    phase_mode=phase_mode,
                    grid_type_code=grid_type,
                    no_current_reason_code=no_current_reason,
                    status=status_state.state,
                    currents_a=currents,
                    voltages_v=voltages,
                )
            )

            han_entity = str(self.entry.data[CONF_HAN_POWER_ENTITY])
            han_state = self.hass.states.get(han_entity)
            local_now = dt_util.now()
            han_age = (
                (local_now - dt_util.as_local(han_state.last_changed)).total_seconds()
                if han_state is not None else None
            )
            han_w = None
            han_error = ""
            if han_state is None or han_age is None or han_age > HAN_MAX_AGE_SECONDS:
                han_error = f"HAN-målingen er eldre enn {HAN_MAX_AGE_SECONDS} sekunder"
            else:
                try:
                    han_w = power_to_watts(
                        _number(han_state),
                        str(han_state.attributes.get("unit_of_measurement", "")),
                    )
                    if han_w <= 0:
                        han_error = "HAN-effekten er 0 eller negativ"
                except (TypeError, ValueError) as err:
                    han_error = str(err)
            han_fresh = han_measurement_is_fresh(han_age, han_w)
            if not han_fresh and not han_error:
                han_error = f"HAN-målingen er eldre enn {HAN_MAX_AGE_SECONDS} sekunder eller ugyldig"
            used_entity = self.entry.data.get(CONF_TARIFF_USED_ENTITY, TARIFF_USED_ENTITY)
            energy_used = None
            energy_estimate = None
            tariff_error = ""
            try:
                energy_used = _number(self.hass.states.get(used_entity))
            except (TypeError, ValueError) as err:
                tariff_error = str(err)
            # The EnergyTariff estimate is exposed for display and comparison,
            # but it is deliberately not a setup requirement or control input.
            try:
                energy_estimate = _number(self.hass.states.get(TARIFF_ESTIMATE_ENTITY))
            except (TypeError, ValueError):
                energy_estimate = None
            charger_power_w = 0.0
            if self.easee.power:
                power_state = self.hass.states.get(self.easee.power)
                if power_state and power_state.state not in {"unknown", "unavailable"}:
                    charger_power_w = power_to_watts(
                        float(power_state.state),
                        str(power_state.attributes.get("unit_of_measurement", "")),
                    )

            minutes_left = 60 - local_now.minute
            # Keep beta.9's saved value as a migration fallback for existing entries.
            hourly_limit = consumption_limit_value(self.entry)
            safety_margin = float(self.entry.data.get(CONF_SAFETY_MARGIN_KWH, 0.3))
            circuit_limit = float(status_state.attributes.get("circuit_ratedCurrent", 0) or 0)
            observed_limits = [circuit_limit] if circuit_limit > 0 else []
            for entity_id in self.easee.current_limits:
                limit_state = self.hass.states.get(entity_id)
                if limit_state is None:
                    continue
                for key, raw_value in limit_state.attributes.items():
                    if key not in {
                        "config_maxChargerCurrent",
                        "config_circuitMaxCurrentP1",
                        "config_circuitMaxCurrentP2",
                        "config_circuitMaxCurrentP3",
                        "circuit_ratedCurrent",
                    }:
                        continue
                    try:
                        limit = float(raw_value)
                    except (TypeError, ValueError):
                        continue
                    if 0 < limit <= 80:
                        observed_limits.append(limit)
            # The Easee circuit/charger limit is the electrical upper bound.
            # Never invent a positive limit if the integration exposes none.
            max_current = min(observed_limits) if observed_limits else 0.0
            current_minimum = electrical.minimum_current_a
            current_kw_per_amp = kw_per_ampere(electrical)
            if current_minimum is not None and current_kw_per_amp is not None:
                self.last_known_minimum_current = current_minimum
                self.last_known_kw_per_amp = current_kw_per_amp
                self._last_known_phase_mode = phase_mode
                self._last_known_voltage_type = electrical.voltage_type
                self._last_known_grid_type_code = grid_type
                self._last_known_electrical = electrical
            elif (
                self.last_commanded_current == 0
                and self._last_known_phase_mode == phase_mode
                and self._last_known_grid_type_code == grid_type
                and electrical.effective_phases == 0
                and self._last_known_electrical is not None
            ):
                # Auto phase mode may report no output phase while paused. Keep
                # the last measured topology so a self-issued 0 A can resume.
                current_minimum = self.last_known_minimum_current
                current_kw_per_amp = self.last_known_kw_per_amp
                electrical = replace(
                    self._last_known_electrical,
                    active_phases=0,
                    phase_mode_name=electrical.phase_mode_name,
                    output_phase_name=electrical.output_phase_name,
                    grid_type_name=electrical.grid_type_name,
                    no_current_reason=electrical.no_current_reason,
                    confidence="cached",
                    reason="Sist målte fase-/spenningsoppsett beholdes mens ladingen er pauset",
                )
            schedule_start_time = str(
                self.entry.options.get(
                    CONF_SCHEDULE_START_TIME,
                    self.entry.data.get(CONF_SCHEDULE_START_TIME, DEFAULT_SCHEDULE_START_TIME),
                )
            )
            schedule_enabled = self.schedule_enabled
            schedule_allowed = True
            schedule_reason = "Tidsstyring er av; lading følger timebudsjettet"
            if schedule_enabled:
                schedule_allowed, schedule_reason = schedule_window_active(
                    local_now, schedule_start_time, SCHEDULE_WINDOW_HOURS
                )

            invalid_input_reason = han_error or tariff_error
            if invalid_input_reason:
                recommended = 0 if self.auto_control else None
            elif not schedule_allowed:
                recommended = 0 if self.auto_control else 0
            else:
                recommended = recommended_current_a(
                    hourly_limit_kwh=hourly_limit,
                    energy_used_kwh=energy_used,
                    han_power_w=han_w,
                    charger_power_w=charger_power_w,
                    minutes_left=minutes_left,
                    safety_margin_kwh=safety_margin,
                    max_current_a=max_current,
                    min_current_a=current_minimum,
                    kw_per_amp=current_kw_per_amp,
                )
            charger_disconnected = status_state.state.lower() == "disconnected"
            if charger_disconnected:
                recommended = 0

            target_current = target_current_for_control(
                enabled=self.auto_control,
                recommendation=recommended,
                connected=not charger_disconnected,
                schedule_allowed=schedule_allowed,
                sources_valid=not bool(invalid_input_reason),
            )
            if target_current is not None:
                now_ts = local_now.timestamp()
                command_age = now_ts - self._last_command_at
                if (
                    (target_current != self.last_commanded_current or command_age >= 300)
                    and command_age >= 60
                ):
                    await self.async_set_current(target_current)

            if recommended is None and self.auto_control and self.last_commanded_current == 0:
                # Keep the zero limit in coordinator state while phase data is
                # unavailable; never resume on a guess.
                recommended = 0
            if charger_disconnected:
                control_reason = "Bilen er ikke tilkoblet; dynamisk grense settes til 0 A"
            elif invalid_input_reason:
                control_reason = f"Pause: {invalid_input_reason}"
            elif not schedule_allowed:
                control_reason = schedule_reason
            elif max_current <= 0:
                control_reason = "Maksimal kursstrøm er ikke tilgjengelig fra Easee; avventer gyldig grense"
            elif recommended is None:
                control_reason = "Venter på pålitelige fase-, spennings- og strømdata"
            elif recommended == 0 and electrical.minimum_current_a is None and self.last_commanded_current == 0:
                control_reason = "Holder Easee-grensen på 0 A mens fase-/spenningsdata mangler; gjenopptar ikke på gjetning"
            elif recommended == 0 and electrical.minimum_current_a is not None:
                control_reason = (
                    f"Tilgjengelig timebudsjett er lavere enn minstegrensen "
                    f"{electrical.minimum_current_a} A; anbefaler pause (0 A)"
                )
            else:
                control_reason = "Anbefalingen følger timegrense, målt huslast og sikkerhetsmargin"

            return {
                "status": status_state.state,
                "phase_code": phase_code,
                "phase_mode_code": phase_mode,
                "electrical": asdict(electrical),
                "han_power_w": round(han_w, 1) if han_w is not None else None,
                "han_age_seconds": round(han_age, 1) if han_age is not None else None,
                "han_fresh": han_fresh,
                "energy_used_kwh": energy_used,
                "energy_estimate_kwh": energy_estimate,
                "hourly_limit_kwh": hourly_limit,
                "charger_power_w": round(charger_power_w, 1),
                "charger_current_a": round(_number(current_state), 2),
                "recommended_current_a": recommended,
                "control_reason": control_reason,
                "minimum_current_a": current_minimum,
                "control_minimum_current_a": current_minimum,
                "max_current_a": max_current,
                "safety_margin_kwh": safety_margin,
                "minutes_left": minutes_left,
                "auto_control": self.auto_control,
                "schedule_enabled": schedule_enabled,
                "schedule_allowed": schedule_allowed,
                "schedule_start_time": schedule_start_time,
                "schedule_reason": schedule_reason,
                "charger_entities": asdict(self.easee),
                "han_entity": han_entity,
                "terminal_currents_a": currents,
                "terminal_voltages_v": voltages,
                "easee_enum_codes": {
                    "output_phase": phase_code,
                    "phase_mode": phase_mode,
                    "grid_type": grid_type,
                    "reason_for_no_current": no_current_reason,
                },
            }
        except (TypeError, ValueError) as err:
            if self.auto_control:
                try:
                    await self.async_set_current(0)
                except Exception:  # Keep coordinator's original failure visible.
                    _LOGGER.exception("Kunne ikke sende 0 A etter ugyldige kildedata")
            raise UpdateFailed(str(err)) from err

    async def async_set_current(self, current: int) -> None:
        """Send a persistent-until-replaced dynamic limit through Easee."""
        await async_send_dynamic_limit(
            self.hass, str(self.entry.data["charger_device"]), int(current)
        )
        self.last_commanded_current = int(current)
        self._last_command_at = dt_util.now().timestamp()

    async def async_set_schedule_enabled(self, enabled: bool) -> None:
        """Toggle the built-in daily charging window."""
        self.schedule_enabled = bool(enabled)
        options = dict(self.entry.options)
        options[CONF_SCHEDULE_ENABLED] = self.schedule_enabled
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        await self.async_request_refresh()
