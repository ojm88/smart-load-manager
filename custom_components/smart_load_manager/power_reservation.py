"""Forecast consumption, keeping confirmed demand through a session's pauses.

Observations never set electrical limits or bypass measured transfer guards.
"""
from dataclasses import dataclass
from math import isfinite

from .charger_status import normalize_status

SETTLE_SECONDS = 180
POWER_TOLERANCE_KW = 0.1
PAUSE_STATES = frozenset({
    'awaiting_start', 'ready_to_charge', 'awaiting_load_balancing',
    'start_charging', 'stop_charging', 'paused_due_to_equalizer',
    'awaiting_smart_start', 'awaiting_scheduled_start',
})


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


@dataclass
class Observation:
    context: tuple
    signature: tuple
    since: float
    power: float
    offered: float
    settled: bool = False
    paused: bool = False


class PowerReservations:
    def __init__(self):
        self.observations = {}

    def estimate(self, key, sample, *, offered_a, command_at, now):
        factor = sample.get('kw_per_amp')
        power = sample.get('charger_power_w')
        status = normalize_status(sample.get('status'))
        offer_valid = _number(factor) and factor > 0 and _number(offered_a) and offered_a >= 0
        offered = offered_a * factor if offer_valid else 0
        valid = (sample.get('inputs_valid') and sample.get('han_fresh')
                 and offer_valid and _number(power) and power >= 0)
        context = (factor, sample.get('auto_control'), sample.get('phase_mode_code'))
        prior = self.observations.get(key)
        if (not valid or status not in PAUSE_STATES | {'charging'}
                or (prior is not None and (prior.context != context or now < prior.since))):
            self.observations.pop(key, None)
            prior = None
            if not valid or status not in PAUSE_STATES | {'charging'}:
                return offered
        measured = power / 1000
        if status != 'charging' or power == 0 or offered_a == 0:
            # A pause cannot teach demand. Keep only a previously settled value,
            # and reserve the complete offer until positive charging confirms it.
            if prior is not None and prior.settled:
                prior.paused = True
            else:
                self.observations.pop(key, None)
            return max(offered, measured)
        signature = (offered_a, command_at)
        if (prior is not None and prior.settled and prior.paused
                and offered <= prior.offered
                and abs(measured - prior.power) <= POWER_TOLERANCE_KW):
            # A zero/resume command is expected during load regulation. It does
            # not invalidate matching positive demand in this same session.
            prior.signature = signature
            prior.paused = False
        elif (prior is None or prior.signature != signature
              or abs(measured - prior.power) > POWER_TOLERANCE_KW):
            prior = Observation(context, signature, now, measured, offered)
            self.observations[key] = prior
        if not prior.settled and now - prior.since >= SETTLE_SECONDS:
            prior.settled = True
        if not prior.settled:
            return max(offered, measured)
        return min(offered, max(measured, prior.power) + POWER_TOLERANCE_KW)
