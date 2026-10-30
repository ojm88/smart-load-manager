"""One serialized allocator for the household; charger adapters retain telemetry."""
from __future__ import annotations
from .installation import charger_entries
import asyncio
import math
from homeassistant.helpers.update_coordinator import UpdateFailed
from .debug_trace import DebugTrace
from .allocation import Demand, allocate, available_charging_kw
from .budget import consumption_limit_value
from .const import DOMAIN, HAN_MAX_AGE_SECONDS
from .regulation import RegulationCadence
from .charger_status import allows_automatic_current, normalize_status
from homeassistant.util import dt as dt_util
from homeassistant.core import callback
from homeassistant.helpers.event import async_call_later


class MeasurementPending(ValueError):
    """Expected missing/stale measurements; retain diagnostic visibility."""


def site_entry(hass):
    entries = charger_entries(hass)
    return entries[0]


def get_site(hass):
    data = hass.data.setdefault(DOMAIN, {})
    if "site" not in data:
        data["site"] = SiteController(hass)
    return data["site"]


class SiteController:
    def __init__(self, hass):
        self.hass = hass
        self.debug_trace = DebugTrace()
        self.controllers = {}
        self.lock = asyncio.Lock()
        self.pending_reductions = {}
        self.manual_requests = {}
        self.latest_samples = {}
        self._permissions = {}
        self._completed_limits = {}
        self._observed_status = {}
        self._measurement_waiting = False
        self._completion_resume = set()
        self._completion_holds = set()
        self._released_completed = set()
        self._command_samples = None
        self._control_requested = 0
        self._control_applied = 0
        self.cadence = RegulationCadence()
        self._check_unsub = None
        self._check_at = None

    async def refresh(self, requester):
        async with self.lock:
            samples = {}
            self._command_samples = samples
            try:
                configured = charger_entries(self.hass)
                if any(e.entry_id not in self.controllers for e in configured):
                    data = await requester._async_sample()
                    data["recommended_current_a"] = 0
                    data["control_reason"] = "Avventer at alle konfigurerte ladere blir tilgjengelige."
                    for key, c in self.controllers.items():
                        if (c.auto_control or c.charging_paused or key in self.manual_requests) and c.last_commanded_current != 0:
                            await c._async_send_current(0)
                            self.pending_reductions[c.entry.entry_id] = (0, c._last_command_at)
                    return data
                for key, controller in self.controllers.items():
                    samples[key] = await controller._async_sample()
                    samples[key]['completion_hold'] = False
                    samples[key]['completion_released'] = False
                    samples[key]["last_sent_current_a"] = controller.last_commanded_current
                    self.debug_trace.record("sample", key, data=samples[key])
                self._completed_limits = {key: value for key, value in self._completed_limits.items()
                                          if key in self.controllers}
                for key, d in samples.items():
                    status = normalize_status(d['status'])
                    c = self.controllers[key]
                    previous_status = self._observed_status.get(key)
                    if status in {'disconnected', 'charging', 'start_charging'}:
                        was_idle = key in self._completed_limits
                        self._completed_limits.pop(key, None)
                        if was_idle and status != 'disconnected':
                            # Actual draw/start turns a standby offer into normal
                            # active allocation, with paired reduction guards.
                            self.async_request_control()
                    elif status == 'completed' and key not in self._completed_limits:
                        # Keep the known positive offer. With no known offer,
                        # stage only the measured electrical minimum, not a
                        # permanent zero ceiling or an invented nominal current.
                        self._completed_limits[key] = max(c.last_commanded_current or 0,
                                                         d.get('control_minimum_current_a') or 0)
                        if any(other != key and self.controllers[other].auto_control
                               and normalize_status(value['status']) not in {'completed', 'disconnected'}
                               for other, value in samples.items()):
                            self.async_request_control()  # Serve a waiting/active peer.
                    elif (key in self._completed_limits and status != previous_status
                          and status in {'awaiting_start', 'ready_to_charge'}):
                        # A new source request returns this car to active allocation.
                        self.async_request_control()
                        self.debug_trace.record('standby_status_assessment', key)
                self._observed_status = {key: normalize_status(d['status']) for key, d in samples.items()}
                # Permission/control transitions are independent of meter-driven
                # regulation. Normal ready -> charging transitions stay steady.
                self._permissions = {key: value for key, value in self._permissions.items()
                                     if key in self.controllers}
                for key, d in samples.items():
                    c = self.controllers[key]
                    permission = (c.auto_control, c.charging_paused,
                                  d['schedule_allowed'], self._can_offer(d['status']),
                                  d.get('phase_mode_code'))
                    previous = self._permissions.get(key)
                    self._permissions[key] = permission
                    if previous is not None and permission != previous:
                        self.async_request_control()
                        if ((not previous[0] and permission[0])
                                or (previous[1] and not permission[1])
                                or (not previous[2] and permission[2])):
                            self._completion_resume.add(key)
                # Completion releases the unused offer, without writing a new
                # limit. The owner accepts source-report latency on vehicle wake.
                released = set()
                for key, d in samples.items():
                    c = self.controllers[key]
                    quiet = (c.auto_control and not c.charging_paused
                             and d.get('schedule_allowed') and d.get('inputs_valid')
                             and d.get('han_fresh') and self._quiet_completed(d)
                             and d.get('kw_per_amp') and d.get('control_minimum_current_a')
                             and c.last_commanded_current is not None
                             and c.last_commanded_current <= d.get('max_current_a', 0)
                             and key not in self._completion_resume)
                    d['completion_released'] = bool(quiet)
                    if quiet:
                        released.add(key)
                        if key not in self._released_completed:
                            self.debug_trace.record('completed_capacity_released', key, data=d)
                            self.async_request_control()
                        self.pending_reductions.pop(key, None)
                    elif key in self._released_completed:
                        self.debug_trace.record('completed_control_resumed', key, data=d)
                        self.async_request_control()
                self._released_completed = released
                owner = site_entry(self.hass)
                reference = samples[owner.entry_id]
                if not all(d.get("inputs_valid") and d.get("han_fresh") for d in samples.values()):
                    raise MeasurementPending("Automatisk laststyring avventer gyldige målinger for alle konfigurerte ladere.")
                # Every charger power must be known before removing it from HAN.
                for key, c in self.controllers.items():
                    if str(samples[key]["status"]).lower() == "disconnected":
                        samples[key]["charger_power_w"] = 0
                        continue
                    state = self.hass.states.get(c.easee.power) if c.easee.power else None
                    name = getattr(c.entry, "title", key)
                    source = c.easee.power or "manglende effektsensor"
                    if state is None or state.state in {"unknown", "unavailable"}:
                        raise MeasurementPending(
                            f"Automatisk laststyring avventer ladeeffekt fra {name} ({source}).")
                    # Easee publishes power on changes, not as a heartbeat.
                    # An old timestamp alone does not invalidate its last value.
                    # Reduction acknowledgement below still needs new telemetry.
                    power = samples[key].get("charger_power_w")
                    if power is None or not math.isfinite(power) or power < 0:
                        raise MeasurementPending(
                            f"Automatisk laststyring avventer gyldig ladeeffekt fra {name} ({source}).")
                if self._measurement_waiting:
                    # Recovery is a permission event, not an ordinary meter tick.
                    # Recompute immediately, retaining all input/paired guards.
                    self.async_request_control()
                    self.debug_trace.record('measurements_recovered')
                    self._measurement_waiting = False
                self._completion_holds.clear()
                managed = sum(d["charger_power_w"] for key, d in samples.items()
                              if self.controllers[key].auto_control)
                capacity = available_charging_kw(
                    limit_kwh=consumption_limit_value(owner), used_kwh=reference["energy_used_kwh"],
                    margin_kwh=reference["safety_margin_kwh"], minutes_left=reference["minutes_left"],
                    han_w=reference["han_power_w"], managed_power_w=managed)
                # Manual charging remains outside automatic allocation. Reserve
                # its commanded capacity too while HAN is catching up.
                for key, d in samples.items():
                    c = self.controllers[key]
                    manual_limit = self.manual_requests.get(key, c.last_commanded_current)
                    if key in self.manual_requests:
                        manual_limit = self._manual_target(c, d, manual_limit)
                    if not c.auto_control and manual_limit and d.get("kw_per_amp"):
                        expected = manual_limit * d["kw_per_amp"]
                        capacity = max(0, capacity - max(0, expected - d["charger_power_w"] / 1000))
                demands = []
                eligible = []
                for key, d in samples.items():
                    c = self.controllers[key]
                    status = normalize_status(d["status"])
                    can_run = (c.auto_control and not c.charging_paused and d["schedule_allowed"]
                               and self._can_offer(status))
                    if can_run and key not in self._released_completed:
                        if not d.get("kw_per_amp") or not d.get("control_minimum_current_a") or d["max_current_a"] <= 0:
                            raise MeasurementPending("Automatisk laststyring avventer fase, spenning eller strømgrense fra en lader.")
                        # A renewed request starts at the validated minimum.
                        # Actual charging clears completion memory above.
                        maximum = (d["control_minimum_current_a"] if key in self._completed_limits
                                   else d["max_current_a"])
                        demands.append(Demand(key, d["kw_per_amp"], d["control_minimum_current_a"], maximum))
                        eligible.append(key)
                priority = owner.options.get("priority_charger", owner.entry_id)
                if priority not in {e.entry_id for e in configured}:
                    priority = owner.entry_id
                mode = owner.options.get("allocation_mode", "both")
                targets = allocate(demands, capacity, mode, priority)
                targets = {key: targets.get(key, 0) for key, c in self.controllers.items()
                           if (c.auto_control or c.charging_paused)
                           and key not in self._released_completed}
                for key, value in list(self.manual_requests.items()):
                    c = self.controllers.get(key)
                    if c is None or c.auto_control:
                        self.manual_requests.pop(key)
                    else:
                        # A pending manual increase reserves capacity before
                        # peer automatic currents are reduced and acknowledged.
                        targets[key] = self._manual_target(c, samples[key], value)
                await self._regulated_apply(targets, samples, reference, owner, eligible)
                self._completion_resume = {key for key in self._completion_resume
                                           if key in self.controllers
                                           and not self.controllers[key].last_commanded_current}
                phase_advice = ""
                if mode == "both" and len(demands) == 2 and any(targets.get(d.key, 0) == 0 for d in demands):
                    single_minimum = 0
                    for d in demands:
                        electric = samples[d.key]["electrical"]
                        voltage = electric.get("phase_neutral_voltage_v") or electric.get("line_voltage_v")
                        if voltage is None or not 180 <= voltage <= 260:
                            break
                        single_minimum += 6 * voltage / 1000
                    else:
                        if any(samples[d.key]["electrical"].get("effective_phases", 0) > 1 for d in demands) and capacity >= single_minimum:
                            phase_advice = "Enfase på begge laderne kan gi plass til samtidig lading. Endre fasevalg selv dersom bilen og laderen støtter det."
                for key, d in samples.items():
                    c = self.controllers[key]
                    if c.auto_control:
                        d["recommended_current_a"] = targets.get(key, 0)
                        if key in eligible:
                            if targets.get(key, 0):
                                d["control_reason"] = "Laderen får sin andel av boligens ledige ladekapasitet." if mode == "both" else "Laderen har tur og får boligens ledige ladekapasitet."
                            else:
                                d["control_reason"] = "Laderen venter på kapasitet eller på laderen med førsteprioritet."
                        if key in self._released_completed:
                            d["control_reason"] = "Bilen har avsluttet ladingen. Ledig kapasitet er frigjort til andre laster."
                            d['regulation_reason'] = "Fullført lading reguleres ikke; avventer ny ladeforespørsel."
                        if self.pending_reductions and key in eligible:
                            d["control_reason"] = "Avventer bekreftet reduksjon på laderne før mer strøm fordeles."
                    d["awaiting_reduction"] = bool(self.pending_reductions)
                    d["site_control_ready"] = True
                    d["phase_advice"] = phase_advice or "Ingen anbefaling om fasebytte nå."
                    d["site_available_kw"] = round(capacity, 3)
                for key, d in samples.items():
                    d["last_sent_current_a"] = self.controllers[key].last_commanded_current
                    d["next_regulation_at"] = self.cadence.next_regular_at
                self.latest_samples = samples
                self._arm_check()
                for key, d in samples.items():
                    c = self.controllers[key]
                    if c is not requester:
                        self._publish(c, d)
                return samples[requester.entry.entry_id]
            except MeasurementPending as err:
                self._measurement_waiting = True
                self.debug_trace.record("measurement_wait")
                # Missing input is a control wait, not a loss of every diagnostic
                # entity. Keep real samples visible; never allocate on old data.
                stop_errors = []
                age_only = self._only_han_age_missing(samples)
                for key, c in self.controllers.items():
                    d = samples.get(key, {})
                    held = (age_only and c.auto_control and not c.charging_paused
                            and d.get('schedule_allowed') and key not in self.manual_requests
                            and self._quiet_completed(d)
                            and c.last_commanded_current is not None
                            and c.last_commanded_current <= d.get('max_current_a', 0))
                    d['completion_hold'] = bool(held)
                    if held:
                        if key not in self._completion_holds:
                            self.debug_trace.record('completed_age_hold', key, data=d,
                                                    target=c.last_commanded_current)
                        self._completion_holds.add(key)
                        continue
                    self._completion_holds.discard(key)
                    if c.auto_control or c.charging_paused or key in self.manual_requests:
                        # Do not reset an outstanding confirmation timestamp on
                        # every refresh; that could prevent recovery forever.
                        if c.last_commanded_current != 0:
                            try:
                                await c._async_send_current(0)
                            except Exception as command_error:
                                stop_errors.append(str(command_error))
                            else:
                                self.pending_reductions[key] = (0, c._last_command_at)
                if stop_errors:
                    error = UpdateFailed("Kunne ikke sette lading til 0 A: " + "; ".join(stop_errors))
                    for peer in self.controllers.values():
                        if peer is not requester:
                            peer.async_set_update_error(error)
                    raise error
                for key, d in samples.items():
                    d["recommended_current_a"] = 0
                    d["control_reason"] = str(err)
                    if d.get('completion_hold'):
                        d['control_reason'] = ('Fullført lading beholdes urørt. HAN-målingen er gammel; '
                                               'ny regulering avventer ferske målinger.')
                    d["site_control_ready"] = False
                    d["site_available_kw"] = None
                    d["phase_advice"] = "Faseråd avventer oppdaterte målinger."
                for key, d in samples.items():
                    d["last_sent_current_a"] = self.controllers[key].last_commanded_current
                    d["next_regulation_at"] = self.cadence.next_regular_at
                self.latest_samples = samples
                self._arm_check()
                for key, d in samples.items():
                    if self.controllers[key] is not requester:
                        self._publish(self.controllers[key], d)
                return samples[requester.entry.entry_id]
            except Exception as err:
                self.debug_trace.record("control_failure")
                # Do not keep a peer on an old positive command after a failed
                # sample or command. Never let a failed reduction enable a rise.
                for key, c in self.controllers.items():
                    if (c.auto_control or c.charging_paused or key in self.manual_requests) and c.last_commanded_current != 0:
                        try:
                            await c._async_send_current(0)
                            self.pending_reductions[c.entry.entry_id] = (0, c._last_command_at)
                        except Exception:
                            pass
                    if c is not requester:
                        c.async_set_update_error(UpdateFailed(str(err)))
                raise UpdateFailed(str(err)) from err
            finally:
                self._command_samples = None

    @staticmethod
    def _quiet_completed(data):
        """Require both raw completion and measured no draw; tolerate standby A."""
        power, current = data.get('charger_power_w'), data.get('charger_current_a')
        return (normalize_status(data.get('status')) == 'completed'
                and isinstance(power, (int, float)) and math.isfinite(power) and power == 0
                and isinstance(current, (int, float)) and math.isfinite(current)
                and 0 <= current < 1)

    def _only_han_age_missing(self, samples):
        """A stale timestamp cannot excuse missing numeric/peer/electrical inputs."""
        if set(samples) != set(self.controllers) or not samples:
            return False
        for key, d in samples.items():
            if not (d.get('han_value_valid') and d.get('tariff_valid')
                    and d.get('electrical_ready') and d.get('kw_per_amp')
                    and d.get('control_minimum_current_a') and d.get('max_current_a', 0) > 0):
                return False
            power = d.get('charger_power_w')
            source = self.controllers[key].easee.power
            state = self.hass.states.get(source) if source else None
            if (not isinstance(power, (int, float)) or not math.isfinite(power) or power < 0
                    or state is None or state.state in {'unknown', 'unavailable'}):
                return False
            if not d.get('han_fresh') and not ((d.get('han_age_seconds') or -1) > HAN_MAX_AGE_SECONDS):
                return False
        return any(not d.get('han_fresh') for d in samples.values())

    @callback
    def async_request_control(self):
        """Request one immediate validated cycle, surviving awaited commands."""
        self._control_requested += 1

    @staticmethod
    def _can_offer(status):
        return normalize_status(status) == 'completed' or allows_automatic_current(status)

    @classmethod
    def _manual_target(cls, controller, data, requested):
        """Manual ownership bypasses hourly allocation, not source/charger guards."""
        minimum = data.get('control_minimum_current_a')
        maximum = data.get('max_current_a', 0)
        if (controller.charging_paused or not data.get('schedule_allowed', True)
                or not data.get('inputs_valid') or not data.get('han_fresh')
                or not cls._can_offer(data.get('status')) or not data.get('kw_per_amp')
                or minimum is None or not maximum):
            return 0
        target = min(int(requested), int(maximum))
        return target if target >= minimum else 0

    @staticmethod
    def _current_above_limit(data, limit):
        # Some Easee units report sub-amp standby current at exactly zero W.
        # Only tolerate this known idle combination, never charging/unknown
        # states, positive measured power, or a reading of 1 A or more.
        idle = (limit == 0 and data['charger_power_w'] == 0
                and 0 <= data['charger_current_a'] < 1
                and normalize_status(data.get('status')) in
                {'completed', 'awaiting_start', 'ready_to_charge'})
        return data['charger_current_a'] > limit + .5 and not idle

    @callback
    def async_cancel_check(self):
        if self._check_unsub is not None:
            self._check_unsub()
        self._check_unsub = None
        self._check_at = None

    @callback
    def _arm_check(self):
        # Keep time-driven decisions independent of the arrival of source data.
        # Lightweight synthetic test adapters have no HA event loop.
        if not hasattr(self.hass, 'loop'):
            return
        deadlines = [value for value in (
            self.cadence.next_regular_at,
            self.cadence.risk_since + 30 if self.cadence.risk_since is not None else None,
        ) if value is not None]
        deadlines.extend(d['next_schedule_change_at'] for d in self.latest_samples.values()
                         if d.get('next_schedule_change_at') is not None)
        now = dt_util.now().timestamp()
        future = [value for value in deadlines if value > now]
        deadline = min(future) if future else None
        if (not (any(c.auto_control for c in self.controllers.values()) or any(self.manual_requests.values()))
                or deadline is None or deadline <= now):
            self.async_cancel_check()
            return  # Pending acknowledgements retain the 30-second watchdog.
        if deadline == self._check_at:
            return
        self.async_cancel_check()
        self._check_at = deadline
        self._check_unsub = async_call_later(self.hass, deadline - now, self._deadline)

    @callback
    def _deadline(self, _now):
        self._check_unsub = None
        self._check_at = None
        for controller in self.controllers.values():
            if not getattr(controller, '_telemetry_stopped', False):
                controller._source_changed(None)
                break

    @staticmethod
    def _publish(controller, data):
        if hasattr(controller, 'async_publish_sample'):
            controller.async_publish_sample(data)
        else:
            controller.async_set_updated_data(data)

    async def _regulated_apply(self, targets, samples, reference, owner, eligible):
        now = dt_util.now().timestamp()
        # Reserve the commanded power, even while the vehicle draws less. HAN
        # already includes measured charging and all unmanaged household loads.
        held_kw = max(reference['han_power_w'] / 1000,
                      sum(d['charger_power_w'] for d in samples.values()) / 1000)
        for key, controller in self.controllers.items():
            d = samples[key]
            factor = d.get('kw_per_amp')
            if (factor and controller.last_commanded_current is not None
                    and key not in self._released_completed):
                held_kw += max(0, controller.last_commanded_current * factor
                               - d['charger_power_w'] / 1000)
        mode = self.cadence.decide(
            now=now, limit_kwh=consumption_limit_value(owner),
            used_kwh=reference['energy_used_kwh'], margin_kwh=reference['safety_margin_kwh'],
            held_power_kw=held_kw,
            seconds_to_hour=reference.get('seconds_to_hour', reference['minutes_left'] * 60))
        manual_change = any(value != self.controllers[key].last_commanded_current
                            for key, value in self.manual_requests.items()
                            if key in targets)
        if manual_change:
            mode = 'regular'
        control_generation = self._control_requested
        if control_generation != self._control_applied:
            # Keep this request until paired reductions are measured. New
            # requests received while sending commands must not be cleared.
            mode = 'control'
        allowed = {}
        for key, target in targets.items():
            c = self.controllers[key]
            d = samples[key]
            previous = c.last_commanded_current
            if not c.auto_control:
                allowed[key] = target  # Explicit manual requests/pause stay immediate.
            elif key not in eligible or c.charging_paused:
                allowed[key] = 0
            elif mode in {'regular', 'control'}:
                allowed[key] = target
            elif mode in {'early', 'urgent'}:
                allowed[key] = min(target, previous or 0)  # Never raise a peer early.
            else:
                allowed[key] = previous or 0
            # A lower physical current limit must never wait for the budget timer.
            maximum = int(d.get('max_current_a', 0))
            allowed[key] = min(allowed[key], maximum)
            minimum = d.get('control_minimum_current_a')
            if allowed[key] and (minimum is None or allowed[key] < minimum):
                allowed[key] = 0
        for key, target in allowed.items():
            self.debug_trace.record("decision", key, data=samples[key], target=target, mode=mode)
        before = {key: self.controllers[key].last_commanded_current for key in allowed}
        if len(self.controllers) == 1:
            # No peer receives released capacity: retain the original single-
            # charger startup without requiring a new zero-power heartbeat.
            for key, target in allowed.items():
                c = self.controllers[key]
                retry_due = now - c._last_command_at >= 60
                if target != c.last_commanded_current or (
                        self._current_above_limit(samples[key], target) and retry_due):
                    await c._async_send_current(target)
                self.pending_reductions.pop(key, None)
        else:
            await self._apply(allowed, samples)
        reduced = any(before[key] is not None and
                      self.controllers[key].last_commanded_current < before[key]
                      for key in allowed)
        if mode in {'regular', 'control'} and not self.pending_reductions and any(
                c.auto_control for c in self.controllers.values()):
            # A status assessment with an unchanged offer must not postpone
            # the next ordinary regulation indefinitely as feedback arrives.
            if mode == 'regular' or any(
                    before[key] != self.controllers[key].last_commanded_current for key in allowed):
                self.cadence.record_regular(now)
            self._control_applied = control_generation
        elif mode not in {'regular', 'control'} and reduced:
            self.cadence.record_early_reduction(now)
        for d in samples.values():
            d['regulation_reason'] = {
                'regular': 'Ordinær regulering hvert femte minutt.',
                'control': 'Regulerer straks etter endret ladetillatelse eller brukerkommando.',
                'hold': 'Beholder strømgrensen frem til neste ordinære regulering.',
                'early': 'Reduserer tidligere: vedvarende risiko for å bruke opp timebudsjettet.',
                'urgent': 'Reduserer straks: timebudsjettet kan ikke vente.',
            }[mode]

    async def _apply(self, targets, samples):
        # First confirm every previous reduction using telemetry reported AFTER
        # that command. A successful HTTP/service response alone is not enough.
        for key, (limit, sent_at) in list(self.pending_reductions.items()):
            c = self.controllers[key]
            current = self.hass.states.get(c.easee.current)
            power = self.hass.states.get(c.easee.power)
            d = samples[key]
            if current and power:
                reported = min(getattr(current, "last_reported", current.last_updated).timestamp(),
                               getattr(power, "last_reported", power.last_updated).timestamp())
                kw = d.get("kw_per_amp")
                if (reported > sent_at and kw and not self._current_above_limit(d, limit)
                        and d["charger_power_w"] <= limit * kw * 1000 + 100):
                    self.pending_reductions.pop(key)
        for key, target in targets.items():
            c = self.controllers[key]
            previous = c.last_commanded_current
            pending = self.pending_reductions.get(key)
            needs_reduction = previous is None or target < previous or self._current_above_limit(samples[key], target)
            if needs_reduction and (pending is None or target < pending[0]):
                # At takeover there is no known command. Establish 0 A first.
                reduction = 0 if previous is None else min(target, previous)
                await c._async_send_current(reduction)
                self.pending_reductions[key] = (reduction, c._last_command_at)
        if self.pending_reductions:
            return
        for key, target in targets.items():
            c = self.controllers[key]
            if target != c.last_commanded_current:
                await c._async_send_current(target)
