"""Small, testable helpers for deciding and sending Easee limits."""

from __future__ import annotations
import math

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


def minimum_manual_current(data):
    """Choose the actual allowed minimum, never a nominal fallback or 10 A."""
    try:
        minimum = float(data['control_minimum_current_a'])
        maximum = float(data['max_current_a'])
        if not all(math.isfinite(v) for v in (minimum, maximum)):
            return 0
        value = math.ceil(minimum)
        return value if 0 < value <= math.floor(maximum) else 0
    except (KeyError, TypeError, ValueError):
        return 0


def charging_controllers(site):
    """Charging category only; future heat adapters must not be toggled here."""
    return [c for c in site.controllers.values()
            if c.entry.data.get('load_type', 'ev_charger') == 'ev_charger']


async def async_set_charging_automation(controllers, enabled):
    """Stage one category/individual command atomically, then validate/apply."""
    if not controllers:
        return
    from .installation import update_load
    site = controllers[0].site
    async with site.lock:
        for c in controllers:
            if c.site is not site:
                raise ValueError('Controllers must share an installation')
            if c.auto_control == enabled:
                continue  # Repeated off must not reset a user-adjusted limit.
            if not enabled:
                try:
                    data = await c._async_sample(calculate=False)
                except Exception:
                    data = {}  # No unverified positive fallback.
                current = minimum_manual_current(data)
                c.manual_current_setting = current
                options = {**c.entry.options, 'manual_current_a': current}
                if c.charging_paused:
                    options['resume_current'] = current
                update_load(c.hass, c.entry, options=options)
                site.manual_requests[c.entry.entry_id] = current
            else:
                site.manual_requests.pop(c.entry.entry_id, None)
            update_load(c.hass, c.entry, options={
                **c.entry.options, 'automatic_control_enabled': bool(enabled)})
            c.auto_control = bool(enabled)
        site.async_request_control()
    requester = controllers[0]
    requester.async_publish_sample(await site.refresh(requester))
    for c in site.controllers.values():
        c.async_update_listeners()


def target_current_for_control(
    *,
    enabled: bool,
    recommendation: int | None,
    connected: bool,
    schedule_allowed: bool,
    sources_valid: bool,
    paused: bool = False,
) -> int | None:
    """Return a command, 0 A pause, or None when the controller is disabled."""
    if paused:
        return 0
    if not enabled:
        return None
    if not connected or not schedule_allowed or not sources_valid or recommendation is None:
        return 0
    return max(0, int(recommendation))


async def async_send_dynamic_limit(hass, device_id: str, current: int) -> None:
    """Send a persistent-until-replaced dynamic current limit via Easee."""
    from .debug_trace import command_trace
    command_trace(hass, device_id, 'current_attempt', target=current)
    try:
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
    except Exception:
        command_trace(hass, device_id, 'current_failed', target=current)
        raise
    command_trace(hass, device_id, 'current_service_success', target=current)



async def async_send_phase_mode(hass, device_id: str, phase_mode: str) -> None:
    """Set the charger phase mode using the Easee integration's service API."""
    if phase_mode not in PHASE_MODE_CODES:
        raise ValueError(f"Unsupported Easee phase mode: {phase_mode}")
    from .debug_trace import command_trace
    command_trace(hass, device_id, 'phase_attempt', mode=phase_mode)
    try:
        await hass.services.async_call(
            EASEE_DOMAIN,
            EASEE_PHASE_MODE_SERVICE,
            {"device_id": device_id, "phase_mode": phase_mode},
            blocking=True,
        )
    except Exception:
        command_trace(hass, device_id, 'phase_failed', mode=phase_mode)
        raise
    command_trace(hass, device_id, 'phase_service_success', mode=phase_mode)



async def async_refresh_control(coordinator):
    """Apply an explicit user control without waiting for ordinary regulation."""
    if hasattr(coordinator.site, 'async_request_control'):
        coordinator.site.async_request_control()
        # Explicit commands must also bypass the coordinator refresh debounce.
        coordinator.async_publish_sample(await coordinator.site.refresh(coordinator))
    else:
        await coordinator.async_request_refresh()
