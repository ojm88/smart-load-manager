"""Hourly consumption-budget helpers shared by the selector and controller."""

from __future__ import annotations

from .const import (
    CONF_CONSUMPTION_LIMIT_KWH,
    CONF_HOURLY_LIMIT_KWH,
    DEFAULT_CONSUMPTION_LIMIT_KWH,
)


CONSUMPTION_LIMIT_VALUES = tuple(value / 2 for value in range(9, 41))
CONSUMPTION_LIMIT_OPTIONS = tuple(f"{value:g}" for value in CONSUMPTION_LIMIT_VALUES)


def consumption_limit_value(entry) -> float:
    """Return a supported limit, migrating the beta.9 config value if needed."""
    raw = entry.options.get(CONF_CONSUMPTION_LIMIT_KWH)
    if raw is None:
        raw = entry.data.get(CONF_HOURLY_LIMIT_KWH, DEFAULT_CONSUMPTION_LIMIT_KWH)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = DEFAULT_CONSUMPTION_LIMIT_KWH
    # Preserve the old selected setpoint when possible. Older beta entries
    # allowed values outside the former input_select's 4.5–20 kWh options.
    value = min(max(value, CONSUMPTION_LIMIT_VALUES[0]), CONSUMPTION_LIMIT_VALUES[-1])
    return round(value * 2) / 2


def consumption_limit_option(entry) -> str:
    """Return the selector state corresponding to the effective setpoint."""
    return f"{consumption_limit_value(entry):g}"
