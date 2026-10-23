"""Small, testable helpers for deciding and sending Easee limits."""

from __future__ import annotations

from .const import (
    DYNAMIC_LIMIT_TTL_MINUTES,
    EASEE_DOMAIN,
    EASEE_DYNAMIC_LIMIT_SERVICE,
    EASEE_PHASE_MODE_SERVICE,
    PHASE_MODE_CODES,
)


def manual_control_is_available(automatic_control: bool) -> bool:
    """Manual charging current is editable only when automatic control is off."""
    return not automatic_control


def target_current_for_control(
    *,
    enabled: bool,
    recommendation: int | None,
    connected: bool,
    schedule_allowed: bool,
    sources_valid: bool,
) -> int | None:
    """Return a command, 0 A pause, or None when the controller is disabled."""
    if not enabled:
        return None
    if not connected or not schedule_allowed or not sources_valid or recommendation is None:
        return 0
    return max(0, int(recommendation))


async def async_send_dynamic_limit(hass, device_id: str, current: int) -> None:
    """Send a persistent-until-replaced dynamic current limit via Easee."""
    await hass.services.async_call(
        EASEE_DOMAIN,
        EASEE_DYNAMIC_LIMIT_SERVICE,
        {
            "device_id": device_id,
            "current": int(current),
            "time_to_live": DYNAMIC_LIMIT_TTL_MINUTES,
        },
        blocking=True,
    )


async def async_send_phase_mode(hass, device_id: str, phase_mode: str) -> None:
    """Set the charger phase mode using the Easee integration's service API."""
    if phase_mode not in PHASE_MODE_CODES:
        raise ValueError(f"Unsupported Easee phase mode: {phase_mode}")
    await hass.services.async_call(
        EASEE_DOMAIN,
        EASEE_PHASE_MODE_SERVICE,
        {"device_id": device_id, "phase_mode": phase_mode},
        blocking=True,
    )
