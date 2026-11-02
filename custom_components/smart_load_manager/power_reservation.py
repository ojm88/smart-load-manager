"""Forecast offered power until sustained charging establishes actual demand.

This is a consumption forecast, never a learned electrical current limit.
"""
from math import isfinite

SETTLE_SECONDS = 180
POWER_TOLERANCE_KW = 0.1


class PowerReservations:
    def __init__(self):
        self.observations = {}

    def estimate(self, key, sample, *, offered_a, command_at, now):
        factor = sample.get('kw_per_amp')
        power = sample.get('charger_power_w')
        valid = (sample.get('inputs_valid') and sample.get('han_fresh')
                 and sample.get('status') == 'charging'
                 and isinstance(power, (int, float)) and isfinite(power) and power > 0
                 and isinstance(factor, (int, float)) and isfinite(factor) and factor > 0
                 and isinstance(offered_a, (int, float)) and isfinite(offered_a) and offered_a > 0)
        offered = (offered_a * factor if isinstance(factor, (int, float)) and isfinite(factor) and factor > 0
                   and isinstance(offered_a, (int, float)) and isfinite(offered_a) and offered_a > 0 else 0)
        if not valid:
            self.observations.pop(key, None)
            return offered
        measured = power / 1000
        signature = (offered_a, command_at, factor, sample.get('auto_control'))
        prior = self.observations.get(key)
        if (prior is None or prior[0] != signature or now < prior[1]
                or abs(measured - prior[2]) > POWER_TOLERANCE_KW):
            prior = (signature, now, measured)
            self.observations[key] = prior
        if now - prior[1] < SETTLE_SECONDS:
            return max(offered, measured)
        return min(offered, max(measured, prior[2]) + POWER_TOLERANCE_KW)
