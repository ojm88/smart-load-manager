"""Opt-in automatic control. It starts disabled after every HA restart."""

from __future__ import annotations
from .device_info import ChargerNameMixin, charger_device_info, name_charger_entity

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ChargingCoordinator
from .entity_ids import suggested_entity_id


async def async_setup_entry(hass, entry, async_add_entities):
    from .installation import platform_loads, add_grouped, charger_entries
    for load in platform_loads(entry):
        c = load.runtime_data
        entities = [AutomaticLoadControl(c, load), ChargingPauseControl(c, load), ChargingScheduleControl(c, load)]
        if len(charger_entries(hass)) == 2:
            entities.append(ChargingPriorityControl(c, load))
        add_grouped(hass, entry, async_add_entities, entities, "charging")


class AutomaticLoadControl(ChargerNameMixin, CoordinatorEntity[ChargingCoordinator], SwitchEntity):
    """Enable/disable recommended current updates; disabled by default."""

    _attr_icon = "mdi:robot"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_automatic_control"
        self._attr_has_entity_name = True
        self._attr_translation_key = "automatic_control"
        name_charger_entity(self, entry, "switch", "automatic_control")
        self.entity_id = f"switch.{suggested_entity_id('switch', 'automatic_control', entry)}"
        self._attr_device_info = charger_device_info(entry)

    @property
    def is_on(self) -> bool:
        return self.coordinator.auto_control

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.auto_control = True
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.auto_control = False
        # Refresh coordinator listeners so the manual current number becomes
        # available immediately when automatic control releases ownership.
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()


class ChargingScheduleControl(ChargerNameMixin, CoordinatorEntity[ChargingCoordinator], SwitchEntity):
    from homeassistant.const import EntityCategory
    _attr_entity_category = EntityCategory.CONFIG
    """Enable the integration-owned daily charging time window."""

    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_schedule_control"
        self._attr_has_entity_name = True
        self._attr_translation_key = "schedule_control"
        name_charger_entity(self, entry, "switch", "schedule_control")
        self.entity_id = f"switch.{suggested_entity_id('switch', 'schedule_control', entry)}"
        self._attr_device_info = charger_device_info(entry)

    @property
    def is_on(self) -> bool:
        return self.coordinator.schedule_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_schedule_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_schedule_enabled(False)
        self.async_write_ha_state()


class ChargingPauseControl(ChargerNameMixin, CoordinatorEntity[ChargingCoordinator], SwitchEntity):
    """Pause/resume charging through the configured Easee charger."""

    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_charging_pause"
        self._attr_has_entity_name = True
        self._attr_translation_key = "charging_pause"
        name_charger_entity(self, entry, "switch", "charging_pause")
        self.entity_id = f"switch.{suggested_entity_id('switch', 'charging_pause', entry)}"
        self._attr_device_info = charger_device_info(entry)

    @property
    def is_on(self) -> bool:
        return self.coordinator.charging_paused

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_charging_paused(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_charging_paused(False)
        self.async_write_ha_state()


class ChargingPriorityControl(ChargerNameMixin, CoordinatorEntity, SwitchEntity):
    """Two complementary views of one persisted software priority."""
    _attr_icon = "mdi:priority-high"
    _attr_has_entity_name = True
    _attr_translation_key = "charging_priority"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        from .device_info import charger_device_info
        from homeassistant.const import EntityCategory
        self._entry = entry
        name_charger_entity(self, entry, "switch", "charging_priority")
        self._attr_unique_id = f"{entry.entry_id}_charging_priority"
        self.entity_id = f"switch.{suggested_entity_id('switch', 'charging_priority', entry)}"
        self._attr_device_info = charger_device_info(entry)
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self):
        from .site import site_entry
        owner = site_entry(self.hass)
        from .installation import charger_entries
        ids = {e.entry_id for e in charger_entries(self.hass)}
        priority = owner.options.get("priority_charger", owner.entry_id)
        return (priority if priority in ids else owner.entry_id) == self._entry.entry_id

    async def _set(self, enabled):
        from .site import site_entry
        from .installation import charger_entries, update_load
        entries = charger_entries(self.hass)
        if len(entries) != 2:
            raise ValueError("Priority requires two configured chargers")
        owner = site_entry(self.hass)
        priority = self._entry.entry_id if enabled else next(e.entry_id for e in entries if e.entry_id != self._entry.entry_id)
        update_load(self.hass, owner, options={**owner.options, "priority_charger": priority})
        await self.coordinator.async_request_refresh()
        for controller in self.coordinator.site.controllers.values():
            controller.async_update_listeners()

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)
