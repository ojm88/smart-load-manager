"""Pure site-budget allocation. All power arithmetic is in kW, never shared A."""
from dataclasses import dataclass
from math import floor, isfinite


@dataclass(frozen=True)
class Demand:
    key: str
    kw_per_amp: float
    minimum_a: int
    maximum_a: float

    @property
    def minimum_kw(self):
        return self.minimum_a * self.kw_per_amp


def available_charging_kw(*, limit_kwh, used_kwh, margin_kwh, minutes_left,
                          han_w, managed_power_w):
    values = (limit_kwh, used_kwh, margin_kwh, minutes_left, han_w, managed_power_w)
    if not all(isfinite(float(v)) for v in values) or minutes_left <= 0:
        raise ValueError("Invalid site budget")
    if used_kwh < 0 or margin_kwh < 0 or managed_power_w < 0:
        raise ValueError("Negative energy or charger reading")
    other_kw = max(0, han_w - managed_power_w) / 1000
    return max(0, (limit_kwh - used_kwh - margin_kwh) * 60 / minutes_left - other_kw)


def allocate(demands, capacity_kw, mode, priority):
    """Equal power with minimum reservation, or strictly one charger at a time."""
    if mode not in {"both", "one_at_a_time"}:
        raise ValueError("Unknown allocation mode")
    if not isfinite(capacity_kw) or capacity_kw < 0:
        raise ValueError("Invalid capacity")
    result = {d.key: 0 for d in demands}
    valid = [d for d in demands if isfinite(d.kw_per_amp) and d.kw_per_amp > 0
             and d.minimum_a > 0 and isfinite(d.maximum_a)
             and floor(d.maximum_a) >= d.minimum_a]
    valid.sort(key=lambda d: d.key != priority)
    if not valid:
        return result
    if mode == "one_at_a_time" or sum(d.minimum_kw for d in valid) > capacity_kw + 1e-9:
        first = valid[0]
        amps = min(floor(first.maximum_a), floor((capacity_kw + 1e-9) / first.kw_per_amp))
        result[first.key] = amps if amps >= first.minimum_a else 0
        return result
    # Water filling in power: lower limits/minima are respected, surplus goes to
    # the remaining charger; integer amp rounding always rounds down.
    powers = {d.key: d.minimum_kw for d in valid}
    remaining = capacity_kw - sum(powers.values())
    while remaining > 1e-9:
        candidates = [d for d in valid if powers[d.key] + 1e-9 < floor(d.maximum_a) * d.kw_per_amp]
        if not candidates:
            break
        low = min(powers[d.key] for d in candidates)
        lowest = [d for d in candidates if powers[d.key] <= low + 1e-9]
        higher = [powers[d.key] for d in candidates if powers[d.key] > low + 1e-9]
        increment = min(remaining / len(lowest),
                        min(floor(d.maximum_a) * d.kw_per_amp - powers[d.key] for d in lowest),
                        min(higher) - low if higher else float("inf"))
        for d in lowest:
            powers[d.key] += increment
        remaining -= increment * len(lowest)
    for d in valid:
        result[d.key] = min(floor(d.maximum_a), floor((powers[d.key] + 1e-9) / d.kw_per_amp))
    return result
