"""Integration-owned controls for the hourly household energy budget."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .budget import CONSUMPTION_LIMIT_OPTIONS, consumption_limit_option
from .const import (
    CONF_CONSUMPTION_LIMIT_KWH,
    DOMAIN,
    PHASE_MODE_CODES,
    PHASE_MODE_FROM_CODE,
    PHASE_MODE_OPTIONS,
)
from .coordinator import ChargingCoordinator
from .control import async_send_phase_mode
from .entity_ids import suggested_entity_id


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the per-charger consumption budget selector."""
    from .site import site_entry
    entities = [ChargerPhaseModeSelect(entry.runtime_data, entry)]
    if entry.entry_id == site_entry(hass).entry_id:
        entities += [ConsumptionLimitSelect(entry.runtime_data, entry),
                     SiteChoiceSelect(entry.runtime_data, entry, "allocation_mode"),
                     SiteChoiceSelect(entry.runtime_data, entry, "priority_charger")]
    async_add_entities(entities)



class ConsumptionLimitSelect(
    CoordinatorEntity[ChargingCoordinator], SelectEntity
):
    """The maximum desired household energy consumption per clock hour."""

    _attr_options = CONSUMPTION_LIMIT_OPTIONS
    _attr_icon = "mdi:meter-electric-outline"
    _attr_has_entity_name = True
    _attr_translation_key = "consumption_limit"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self.entity_id = f"select.{suggested_entity_id('select', 'consumption_limit', entry)}"
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_consumption_limit"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Smart Load Manager OJM",
            model="Household load control",
            name=entry.title,
        )

    @property
    def current_option(self) -> str:
        """Return the saved option, migrating the beta.9 value when present."""
        return consumption_limit_option(self._entry)

    async def async_select_option(self, option: str) -> None:
        """Persist the selected threshold and refresh the current recommendation."""
        if option not in self._attr_options:
            raise ValueError(f"Unsupported consumption limit: {option}")
        options = dict(self._entry.options)
        options[CONF_CONSUMPTION_LIMIT_KWH] = float(option)
        self.hass.config_entries.async_update_entry(self._entry, options=options)
        await self.coordinator.async_request_refresh()


class ChargerPhaseModeSelect(CoordinatorEntity[ChargingCoordinator], SelectEntity):
    """Configure Easee's phase mode through its supported integration service."""

    _attr_options = PHASE_MODE_OPTIONS
    _attr_icon = "mdi:current-ac"
    _attr_has_entity_name = True
    _attr_translation_key = "phase_mode_control"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self.entity_id = f"select.{suggested_entity_id('select', 'phase_mode_control', entry)}"
        self._attr_unique_id = f"{entry.entry_id}_phase_mode_control"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Smart Load Manager OJM",
            model="Easee charging control",
            name=entry.title,
        )

    @property
    def current_option(self) -> str | None:
        """Reflect the phase mode reported by Easee, not an optimistic value."""
        data = self.coordinator.data or {}
        code = data.get("phase_mode_code")
        try:
            return PHASE_MODE_FROM_CODE.get(int(code))
        except (TypeError, ValueError):
            return None

    async def async_select_option(self, option: str) -> None:
        """Ask the Easee integration to change the configured phase mode."""
        if option not in PHASE_MODE_CODES:
            raise ValueError(f"Unsupported Easee phase mode: {option}")
        await async_send_phase_mode(
            self.hass,
            str(self.coordinator.entry.data["charger_device"]),
            option,
        )
        await self.coordinator.async_request_refresh()


class SiteChoiceSelect(CoordinatorEntity[ChargingCoordinator], SelectEntity):
    """Persistent household allocation choices; labels come from charger names."""
    _attr_has_entity_name = True
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self.entity_id = f"select.{suggested_entity_id('select', key)}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    def _names(self):
        from homeassistant.helpers import device_registry as dr
        entries = self.hass.config_entries.async_entries(DOMAIN)
        devices = dr.async_get(self.hass)
        names = {}
        for entry in entries:
            device = devices.devices.get(entry.data["charger_device"])
            name = (device.name_by_user or device.name) if device else entry.title
            names[entry.entry_id] = name or entry.title
        # Duplicate names must still allow an unambiguous selection.
        return {key: f"{name} ({key[:6]})" if list(names.values()).count(name) > 1 else name
                for key, name in names.items()}

    @property
    def options(self):
        return ["both", "one_at_a_time"] if self._key == "allocation_mode" else list(self._names().values())

    @property
    def current_option(self):
        if self._key == "allocation_mode":
            return self._entry.options.get(self._key, "both")
        names = self._names()
        return names.get(self._entry.options.get(self._key, self._entry.entry_id), names.get(self._entry.entry_id))

    async def async_select_option(self, option):
        if option not in self.options:
            raise ValueError("Unknown charging choice")
        value = option if self._key == "allocation_mode" else next(key for key, name in self._names().items() if name == option)
        options = dict(self._entry.options)
        options[self._key] = value
        self.hass.config_entries.async_update_entry(self._entry, options=options)
        await self.coordinator.async_request_refresh()
