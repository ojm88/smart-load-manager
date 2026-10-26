"""One serialized allocator for the household; charger adapters retain telemetry."""
from __future__ import annotations
import asyncio
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from .allocation import Demand, allocate, available_charging_kw
from .budget import consumption_limit_value
from .const import DOMAIN


def site_entry(hass):
    entries = hass.config_entries.async_entries(DOMAIN)
    return next((e for e in entries if not e.data.get("entity_suffix")), entries[0])


def get_site(hass):
    return hass.data.setdefault(DOMAIN, {}).setdefault("site", SiteController(hass))


class SiteController:
    def __init__(self, hass):
        self.hass = hass
        self.controllers = {}
        self.lock = asyncio.Lock()
        self.pending_reductions = {}
        self.manual_requests = {}

    async def refresh(self, requester):
        async with self.lock:
            samples = {}
            try:
                configured = self.hass.config_entries.async_entries(DOMAIN)
                if any(e.entry_id not in self.controllers for e in configured):
                    data = await requester._async_sample()
                    data["recommended_current_a"] = 0
                    data["control_reason"] = "Avventer at begge laderne blir tilgjengelige."
                    for c in self.controllers.values():
                        if c.auto_control or c.charging_paused:
                            await c._async_send_current(0)
                            self.pending_reductions[c.entry.entry_id] = (0, c._last_command_at)
                    return data
                for key, controller in self.controllers.items():
                    samples[key] = await controller._async_sample()
                owner = site_entry(self.hass)
                reference = samples[owner.entry_id]
                if not all(d.get("inputs_valid") and d.get("han_fresh") for d in samples.values()):
                    raise ValueError("Avventer gyldige målinger for begge laderne.")
                # Every charger power must be known before removing it from HAN.
                now = dt_util.now()
                for key, c in self.controllers.items():
                    if str(samples[key]["status"]).lower() == "disconnected":
                        samples[key]["charger_power_w"] = 0
                        continue
                    state = self.hass.states.get(c.easee.power) if c.easee.power else None
                    if state is None or state.state in {"unknown", "unavailable"}:
                        raise ValueError("Avventer ladeeffekt fra begge laderne.")
                    reported = getattr(state, "last_reported", state.last_updated)
                    if (now - reported).total_seconds() > 120:
                        raise ValueError("Avventer oppdatert ladeeffekt fra begge laderne.")
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
                    if not c.auto_control and manual_limit and d.get("kw_per_amp"):
                        expected = manual_limit * d["kw_per_amp"]
                        capacity = max(0, capacity - max(0, expected - d["charger_power_w"] / 1000))
                demands = []
                eligible = []
                for key, d in samples.items():
                    c = self.controllers[key]
                    status = str(d["status"]).lower().replace(" ", "_")
                    can_run = (c.auto_control and not c.charging_paused and d["schedule_allowed"]
                               and status not in {"disconnected", "completed", "charged", "error", "offline", "awaiting_authentication"})
                    if can_run:
                        if not d.get("kw_per_amp") or not d.get("control_minimum_current_a") or d["max_current_a"] <= 0:
                            raise ValueError("Avventer fase, spenning eller strømgrense fra en lader.")
                        demands.append(Demand(key, d["kw_per_amp"], d["control_minimum_current_a"], d["max_current_a"]))
                        eligible.append(key)
                priority = owner.options.get("priority_charger", owner.entry_id)
                mode = owner.options.get("allocation_mode", "both")
                targets = allocate(demands, capacity, mode, priority)
                targets = {key: targets.get(key, 0) for key, c in self.controllers.items()
                           if c.auto_control or c.charging_paused}
                for key, value in list(self.manual_requests.items()):
                    c = self.controllers.get(key)
                    if c is None or c.auto_control:
                        self.manual_requests.pop(key)
                    elif not c.charging_paused:
                        # A pending manual increase reserves capacity before
                        # peer automatic currents are reduced and acknowledged.
                        targets[key] = value
                await self._apply(targets, samples)
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
                        if str(d["status"]).lower() in {"completed", "charged"}:
                            d["control_reason"] = "Bilen har avsluttet ladingen. Kapasiteten kan brukes av den andre laderen."
                        if self.pending_reductions and key in eligible:
                            d["control_reason"] = "Avventer bekreftet reduksjon på laderne før mer strøm fordeles."
                    d["phase_advice"] = phase_advice or "Ingen anbefaling om fasebytte nå."
                    d["site_available_kw"] = round(capacity, 3)
                for key, d in samples.items():
                    c = self.controllers[key]
                    if c is not requester:
                        c.async_set_updated_data(d)
                return samples[requester.entry.entry_id]
            except Exception as err:
                # Do not keep a peer on an old positive command after a failed
                # sample or command. Never let a failed reduction enable a rise.
                for c in self.controllers.values():
                    if c.auto_control or c.charging_paused:
                        try:
                            await c._async_send_current(0)
                            self.pending_reductions[c.entry.entry_id] = (0, c._last_command_at)
                        except Exception:
                            pass
                    if c is not requester:
                        c.async_set_update_error(UpdateFailed(str(err)))
                raise UpdateFailed(str(err)) from err

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
                if (reported > sent_at and kw and d["charger_current_a"] <= limit + .5
                        and d["charger_power_w"] <= limit * kw * 1000 + 100):
                    self.pending_reductions.pop(key)
        for key, target in targets.items():
            c = self.controllers[key]
            measured = samples[key]["charger_current_a"]
            previous = c.last_commanded_current
            pending = self.pending_reductions.get(key)
            needs_reduction = previous is None or target < previous or measured > target + .5
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
