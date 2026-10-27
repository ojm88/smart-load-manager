"""Integration-owned charging schedule start-time control."""

from __future__ import annotations
from .device_info import charger_device_info, name_charger_entity
from .installation import update_load

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SCHEDULE_START_TIME, DEFAULT_SCHEDULE_START_TIME
from .coordinator import ChargingCoordinator
from .entity_ids import suggested_entity_id


async def async_setup_entry(hass, entry, async_add_entities):
    from .installation import platform_loads, add_grouped
    for load in platform_loads(entry):
        coordinator = load.runtime_data
        add_grouped(hass, entry, async_add_entities, [ChargingScheduleStartTime(coordinator, load)], "charging")


class ChargingScheduleStartTime(CoordinatorEntity[ChargingCoordinator], TimeEntity):
    """A native HA time entity; users do not need to create an input_datetime."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-start"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self.entity_id = f"time.{suggested_entity_id('time', 'schedule_start_time', entry)}"
        self._attr_unique_id = f"{entry.entry_id}_schedule_start_time"
        self._attr_has_entity_name = True
        self._attr_translation_key = "schedule_start_time"
        name_charger_entity(self, entry, "time", "schedule_start_time")
        self._attr_device_info = charger_device_info(entry)

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
        update_load(self.hass, self.coordinator.entry, options=options)
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
