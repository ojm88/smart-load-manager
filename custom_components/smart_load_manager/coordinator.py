"""Coordinate selected Easee, HAN, and EnergyTariff entities and control."""

from __future__ import annotations
from .installation import charger_entries, update_load

import logging
import math
from dataclasses import asdict

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
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
    next_schedule_transition,
)
from .const import (
    CONF_HAN_POWER_ENTITY,
    CONF_CONNECTION,
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
from .control import async_send_dynamic_limit, async_refresh_control
from .charger_status import allows_automatic_current, normalize_status

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
        from .site import get_site
        self.site = get_site(hass)
        self.easee = resolve_easee_entities(
            hass, str(entry.data["charger_device"])
        )
        self.auto_control = bool(entry.options.get("automatic_control_enabled", False))
        self.charging_paused = bool(entry.options.get("charging_paused", False))
        self.schedule_enabled = bool(
            entry.options.get(CONF_SCHEDULE_ENABLED, False)
        )
        self.last_commanded_current: int | None = None
        self.manual_current_setting = entry.options.get('manual_current_a')
        # Restore desired manual input, never an assumed successful charger command.
        if not self.auto_control and self.manual_current_setting is not None:
            self.site.manual_requests[entry.entry_id] = self.manual_current_setting
        self._last_command_at = 0.0
        self.site.controllers[entry.entry_id] = self
        self._source_unsub = None
        self._telemetry_task = None
        self._telemetry_stopped = False
        self._telemetry_dirty = False

    async def async_config_entry_first_refresh(self):
        await super().async_config_entry_first_refresh()
        self.async_start_source_updates()

    @callback
    def async_start_source_updates(self):
        """Observe local HA changes; command timing belongs to the site policy."""
        if self._source_unsub is not None:
            return
        sources = {self.easee.status, self.easee.current, self.easee.voltage,
                   self.easee.power, *self.easee.current_limits,
                   self.entry.data[CONF_HAN_POWER_ENTITY],
                   self.entry.data.get(CONF_TARIFF_USED_ENTITY, TARIFF_USED_ENTITY),
                   TARIFF_ESTIMATE_ENTITY}
        self._source_unsub = async_track_state_change_event(
            self.hass, [source for source in sources if source], self._source_changed)

    @callback
    def _source_changed(self, event):
        self._telemetry_dirty = True
        if not self._telemetry_stopped and (
                self._telemetry_task is None or self._telemetry_task.done()):
            self._telemetry_task = self.hass.async_create_task(self._async_publish_telemetry())

    async def _async_publish_telemetry(self):
        # Source changes recalculate the complete installation. The site policy
        # decides whether a command is due; publishing never resets polling.
        while not self._telemetry_stopped:
            self._telemetry_dirty = False
            try:
                data = await self.site.refresh(self)
            except UpdateFailed:
                for controller in self.site.controllers.values():
                    if hasattr(controller, '_async_publish_partial_telemetry'):
                        await controller._async_publish_partial_telemetry()
            else:
                self.async_publish_sample(data)
            if not self._telemetry_dirty:
                return

    @callback
    def async_publish_sample(self, data):
        self.data = data
        self.last_update_success = True
        self.async_update_listeners()

    async def _async_publish_partial_telemetry(self):
        # Serialize with paired regulation, but never invoke it. Updating data
        # directly avoids async_set_updated_data resetting the polling deadline.
        async with self.site.lock:
            if self._telemetry_stopped:
                return
            try:
                measured = await self._async_sample(calculate=False)
                self.last_update_success = True
            except UpdateFailed as err:
                def value(entity_id, *, power=False):
                    state = self.hass.states.get(entity_id) if entity_id else None
                    try:
                        number = _number(state)
                        return power_to_watts(number, str(state.attributes.get("unit_of_measurement", ""))) if power else number
                    except (TypeError, ValueError):
                        return None

                han_state = self.hass.states.get(self.entry.data[CONF_HAN_POWER_ENTITY])
                han_age = ((dt_util.now() - dt_util.as_local(getattr(han_state, "last_reported", han_state.last_updated))).total_seconds()
                           if han_state is not None else None)
                han_power = value(self.entry.data[CONF_HAN_POWER_ENTITY], power=True)
                measured = {
                    "status": getattr(self.hass.states.get(self.easee.status), "state", "unavailable"),
                    "charger_current_a": value(self.easee.current),
                    "charger_power_w": value(self.easee.power, power=True),
                    "electrical": {}, "electrical_ready": False,
                    "electrical_error": str(err), "inputs_valid": False,
                    "han_fresh": han_measurement_is_fresh(han_age, han_power),
                    "han_age_seconds": han_age, "han_power_w": han_power,
                    "energy_used_kwh": value(self.entry.data.get(CONF_TARIFF_USED_ENTITY, TARIFF_USED_ENTITY)),
                    "energy_estimate_kwh": value(TARIFF_ESTIMATE_ENTITY),
                }
            live_keys = {
                "status", "charger_current_a", "charger_power_w", "electrical",
                "electrical_ready", "electrical_error", "inputs_valid",
                "phase_code", "phase_mode_code", "han_power_w", "han_age_seconds",
                "han_fresh", "energy_used_kwh", "energy_estimate_kwh",
                "max_current_a", "minimum_current_a", "control_minimum_current_a",
                "kw_per_amp", "terminal_currents_a", "terminal_voltages_v", "easee_enum_codes",
            }
            self.data = {**(self.data or {}),
                         **{k: v for k, v in measured.items() if k in live_keys},
                         'site_control_ready': False,
                         'recommended_current_a': 0 if self.auto_control else None,
                         'last_sent_current_a': self.last_commanded_current,
                         'next_regulation_at': getattr(getattr(self.site, 'cadence', None), 'next_regular_at', None)}
            self.last_update_success = True
            if self.entry.entry_id in self.site.latest_samples:
                self.site.latest_samples[self.entry.entry_id] = dict(self.data)
            # Shared household entities belong to the first coordinator and
            # must also hear updates originating from the second charger.
            for controller in self.site.controllers.values():
                controller.async_update_listeners()

    async def async_shutdown(self):
        self._telemetry_stopped = True
        if hasattr(self.site, "async_cancel_check"):
            self.site.async_cancel_check()
        if self._source_unsub is not None:
            self._source_unsub()
            self._source_unsub = None
        if self._telemetry_task is not None and not self._telemetry_task.done():
            self._telemetry_task.cancel()
            import asyncio
            try:
                await self._telemetry_task
            except asyncio.CancelledError:
                pass
        await super().async_shutdown()

    async def _async_update_data(self) -> dict[str, object]:
        return await self.site.refresh(self)

    async def _async_sample(self, *, calculate=True) -> dict[str, object]:
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
                    connection=self.entry.data.get(CONF_CONNECTION),
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
                # last_reported advances even when a meter republishes exactly
                # the same value and attributes; last_updated does not.
                (local_now - dt_util.as_local(getattr(han_state, "last_reported", han_state.last_updated))).total_seconds()
                if han_state is not None else None
            )
            han_w = None
            han_error = ""
            if han_state is None:
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

            seconds_to_hour = 3600 - (local_now.minute * 60 + local_now.second + local_now.microsecond / 1_000_000)
            minutes_left = seconds_to_hour / 60
            # Keep beta.9's saved value as a migration fallback for existing entries.
            from .site import site_entry
            hourly_limit = consumption_limit_value(site_entry(self.hass))
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

            electrical_error = electrical.reason if current_kw_per_amp is None or current_minimum is None else ""
            invalid_input_reason = han_error or tariff_error or electrical_error
            if not calculate:
                recommended = (self.data or {}).get("recommended_current_a")
            elif invalid_input_reason:
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
            charger_disconnected = normalize_status(status_state.state) == "disconnected"
            if not allows_automatic_current(status_state.state):
                recommended = 0


            if recommended is None and self.auto_control and self.last_commanded_current == 0:
                # Keep the zero limit in coordinator state while phase data is
                # unavailable; never resume on a guess.
                recommended = 0
            if charger_disconnected:
                control_reason = "Bilen er ikke koblet til laderen."
            elif self.charging_paused:
                control_reason = "Ladingen er satt på pause. Easee-grensen er satt til 0 A."
            elif electrical_error:
                control_reason = electrical_error
            elif invalid_input_reason:
                control_reason = "Laststyringen avventer gyldige og oppdaterte måledata."
            elif not schedule_allowed:
                control_reason = "Tidsstyringen hindrer lading frem til valgt starttid."
            elif max_current <= 0:
                control_reason = "Avventer gyldig maksimal strømgrense fra Easee."
            elif recommended is None:
                control_reason = "Ladingen avventer gyldige fase- og spenningsmålinger."
            elif recommended == 0 and electrical.minimum_current_a is None and self.last_commanded_current == 0:
                control_reason = "Fase- eller spenningsgrunnlaget er usikkert. Ladingen avventer gyldige målinger."
            elif recommended == 0 and electrical.minimum_current_a is not None:
                control_reason = "Tilgjengelig timebudsjett er lavere enn laderens minste strøm. Ladingen er satt på pause."
            else:
                control_reason = "Strømgrensen justeres etter målt husforbruk, gjenstående timebudsjett og sikkerhetsmargin."

            return {
                "status": status_state.state,
                "kw_per_amp": current_kw_per_amp,
                "inputs_valid": not bool(invalid_input_reason),
                "electrical_ready": not bool(electrical_error),
                "electrical_error": electrical_error,
                "phase_code": phase_code,
                "phase_mode_code": phase_mode,
                "electrical": asdict(electrical),
                "han_power_w": round(han_w, 1) if han_w is not None else None,
                "han_age_seconds": round(han_age, 1) if han_age is not None else None,
                "han_fresh": han_fresh,
                "han_value_valid": han_w is not None and math.isfinite(han_w) and han_w > 0,
                "tariff_valid": not bool(tariff_error),
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
                "seconds_to_hour": seconds_to_hour,
                "auto_control": self.auto_control,
                "manual_current_setting_a": self.manual_current_setting,
                "charging_paused": self.charging_paused,
                "schedule_enabled": schedule_enabled,
                "schedule_allowed": schedule_allowed,
                "schedule_start_time": schedule_start_time,
                "schedule_reason": schedule_reason,
                "next_schedule_change_at": next_schedule_transition(
                    local_now, schedule_start_time, SCHEDULE_WINDOW_HOURS
                ) if schedule_enabled else None,
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
            raise UpdateFailed(str(err)) from err

    async def async_set_current(self, current: int) -> None:
        multiple = len(charger_entries(self.hass)) > 1
        if not self.auto_control and not self.charging_paused:
            self.manual_current_setting = int(current)
            update_load(self.hass, self.entry, options={**self.entry.options,
                                                      'manual_current_a': int(current)})
        if current > 0 and not self.auto_control:
            async with self.site.lock:
                self.site.manual_requests[self.entry.entry_id] = int(current)
            self.async_publish_sample(await self.site.refresh(self))
            return
        async with self.site.lock:
            self.site.manual_requests.pop(self.entry.entry_id, None)
            await self._async_send_current(current)
            if multiple:
                self.site.pending_reductions[self.entry.entry_id] = (int(current), self._last_command_at)

    async def _async_send_current(self, current: int) -> None:
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
        update_load(self.hass, self.entry, options=options)
        await async_refresh_control(self)

    async def async_set_charging_paused(self, paused: bool) -> None:
        """Pause/resume charging with a persistent Easee dynamic limit."""
        was_paused = self.charging_paused
        if paused and not was_paused:
            resume_current = self.last_commanded_current
        else:
            resume_current = self.entry.options.get("resume_current")
        self.charging_paused = bool(paused)
        options = dict(self.entry.options)
        options["charging_paused"] = self.charging_paused
        if paused and resume_current is not None:
            options["resume_current"] = int(resume_current)
        update_load(self.hass, self.entry, options=options)
        if self.charging_paused:
            await self.async_set_current(0)
        await async_refresh_control(self)
        if not self.charging_paused and not self.auto_control:
            # In manual mode, restore the previous limit only while all current
            # safety checks still pass. Otherwise the charger stays paused.
            current = int(resume_current or 0)
            data = self.data or {}
            minimum = data.get("control_minimum_current_a")
            maximum = float(data.get("max_current_a", 0) or 0)
            if (
                current > 0
                and data.get("han_fresh")
                and data.get("schedule_allowed", True)
                and minimum is not None
                and current >= int(minimum)
                and current <= maximum
            ):
                await self.async_set_current(current)
                await self.async_request_refresh()
