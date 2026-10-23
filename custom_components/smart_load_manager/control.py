"""Small, testable helpers for deciding and sending Easee limits."""

from __future__ import annotations

from .const import DYNAMIC_LIMIT_TTL_MINUTES, EASEE_DOMAIN, EASEE_DYNAMIC_LIMIT_SERVICE


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
