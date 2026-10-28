"""Separate live budget recommendations from stable five-minute commands."""
from dataclasses import dataclass
from math import isfinite

REGULATION_SECONDS = 300
RISK_CONFIRM_SECONDS = 30


@dataclass
class RegulationCadence:
    next_regular_at: float | None = None
    risk_since: float | None = None

    def decide(self, *, now, limit_kwh, used_kwh, margin_kwh,
               held_power_kw, seconds_to_hour):
        """Project held limits only as far as the next decision/hour boundary."""
        if self.next_regular_at is None or now >= self.next_regular_at:
            self.risk_since = None
            return 'regular'
        values = (now, limit_kwh, used_kwh, margin_kwh, held_power_kw, seconds_to_hour)
        if not all(isfinite(float(v)) for v in values) or seconds_to_hour <= 0:
            raise ValueError('Invalid regulation forecast')
        remaining = limit_kwh - used_kwh - margin_kwh
        horizon = min(self.next_regular_at - now, seconds_to_hour)
        projected = max(0, held_power_kw) * horizon / 3600
        if projected <= remaining + 1e-9:
            self.risk_since = None
            return 'hold'
        # No debounce when the reserved budget will run out before confirmation.
        urgent_energy = max(0, held_power_kw) * min(RISK_CONFIRM_SECONDS, horizon) / 3600
        if remaining <= urgent_energy + 1e-9:
            return 'urgent'
        if self.risk_since is None:
            self.risk_since = now
        return 'early' if now - self.risk_since >= RISK_CONFIRM_SECONDS else 'hold'

    def record_regular(self, now):
        self.next_regular_at = now + REGULATION_SECONDS
        self.risk_since = None

    def record_early_reduction(self, now):
        # An early reduction cannot immediately be undone at an old deadline.
        self.next_regular_at = max(self.next_regular_at or now, now + REGULATION_SECONDS)
        self.risk_since = None
