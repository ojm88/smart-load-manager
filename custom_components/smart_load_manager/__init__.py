"""Smart Load Manager integration entry point."""

from __future__ import annotations

from .const import DOMAIN, PLATFORMS


async def async_setup_entry(hass, entry) -> bool:
    """Set up one Smart Load Manager charging controller."""
    from homeassistant.exceptions import ConfigEntryNotReady

    from .coordinator import ChargingCoordinator

    try:
        coordinator = ChargingCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
    except (ValueError, ConfigEntryNotReady) as err:
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry) -> bool:
    """Unload the integration cleanly."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

