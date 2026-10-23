"""Integration-owned charging schedule start-time control."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SCHEDULE_START_TIME, DEFAULT_SCHEDULE_START_TIME, DOMAIN
from .coordinator import ChargingCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the start-time entity for the selected charger."""
    async_add_entities([ChargingScheduleStartTime(entry.runtime_data, entry)])


class ChargingScheduleStartTime(CoordinatorEntity[ChargingCoordinator], TimeEntity):
    """A native HA time entity; users do not need to create an input_datetime."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-start"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_schedule_start_time"
        self._attr_has_entity_name = True
        self._attr_name = "Starttid lading"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Smart Load Manager",
            model="Easee charging control",
            name=entry.title,
        )

    @property
    def native_value(self) -> time:
        """Return the configured daily start time, defaulting to 23:00."""
        value = self.coordinator.entry.options.get(
            CONF_SCHEDULE_START_TIME,
            self.coordinator.entry.data.get(
                CONF_SCHEDULE_START_TIME, DEFAULT_SCHEDULE_START_TIME
            ),
        )
        try:
            return time.fromisoformat(str(value))
        except ValueError:
            return time.fromisoformat(DEFAULT_SCHEDULE_START_TIME)

    async def async_set_value(self, value: time) -> None:
        """Persist the selected start time in this integration's config entry."""
        options = dict(self.coordinator.entry.options)
        options[CONF_SCHEDULE_START_TIME] = value.isoformat(timespec="seconds")
        self.hass.config_entries.async_update_entry(
            self.coordinator.entry, options=options
        )
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
