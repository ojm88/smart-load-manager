"""Smart Load Manager integration entry point."""

from __future__ import annotations

from .budget import consumption_limit_value
from .const import (
    CONF_CONSUMPTION_LIMIT_KWH,
    DOMAIN,
    PLATFORMS,
)


async def async_setup_entry(hass, entry) -> bool:
    """Set up one Smart Load Manager charging controller."""
    from homeassistant.exceptions import ConfigEntryNotReady

    from .coordinator import ChargingCoordinator

    try:
        coordinator = ChargingCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
    except (ValueError, ConfigEntryNotReady) as err:
        raise ConfigEntryNotReady(str(err)) from err

    # Keep existing beta.9 entries visible under the new product name and
    # migrate their former setup value into the integration-owned select.
    options = dict(entry.options)
    if CONF_CONSUMPTION_LIMIT_KWH not in options:
        options[CONF_CONSUMPTION_LIMIT_KWH] = consumption_limit_value(entry)
    title = entry.title
    if not title.startswith("Smart Load Manager OJM"):
        title = title.replace("Smart Load Manager", "Smart Load Manager OJM", 1)
    if options != dict(entry.options) or title != entry.title:
        hass.config_entries.async_update_entry(entry, options=options, title=title)

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry) -> bool:
    """Unload the integration cleanly."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

