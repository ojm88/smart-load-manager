"""Opt-in automatic control. It starts disabled after every HA restart."""

from __future__ import annotations
from .device_info import ChargerNameMixin, charger_device_info, name_charger_entity

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ChargingCoordinator
from .control import async_refresh_control, async_set_charging_automation, charging_controllers
from .entity_ids import suggested_entity_id


async def async_setup_entry(hass, entry, async_add_entities):
    from .installation import platform_loads, add_grouped, charger_entries
    loads = platform_loads(entry)
    for load in loads:
        c = load.runtime_data
        entities = [AutomaticLoadControl(c, load), ChargingPauseControl(c, load), ChargingScheduleControl(c, load)]
        if len(charger_entries(hass)) == 2:
            entities.append(ChargingPriorityControl(c, load))
        add_grouped(hass, entry, async_add_entities, entities, "charging")
    if loads:
        add_grouped(hass, entry, async_add_entities,
                    [ChargingAutomationControl(loads[0].runtime_data, loads[0])], 'charging')


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
        await async_refresh_control(self.coordinator)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await async_set_charging_automation([self.coordinator], False)
        self.async_write_ha_state()


class ChargingAutomationControl(CoordinatorEntity[ChargingCoordinator], SwitchEntity):
    """Category control, independent of future water/floor heating categories."""
    _attr_icon = 'mdi:ev-station'
    _attr_has_entity_name = True
    _attr_translation_key = 'charging_automatic_control'

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        from .installation import shared_identity
        from .const import DOMAIN
        from homeassistant.helpers.device_registry import DeviceInfo
        self._attr_unique_id = f'{shared_identity(entry)}_charging_automatic_control'
        self.entity_id = 'switch.slm_charging_auto_control'
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, 'charging_category')}, name='SLM – Lading',
            manufacturer='Smart Load Manager OJM', model='Charging category control')

    @property
    def is_on(self):
        return any(c.auto_control for c in charging_controllers(self.coordinator.site))

    @property
    def extra_state_attributes(self):
        members = charging_controllers(self.coordinator.site)
        enabled = sum(c.auto_control for c in members)
        return {'load_type': 'ev_charger', 'charger_count': len(members),
                'automatic_chargers': enabled,
                'control_mode': 'off' if not enabled else 'all' if enabled == len(members) else 'mixed'}

    async def async_turn_on(self, **kwargs):
        await async_set_charging_automation(charging_controllers(self.coordinator.site), True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await async_set_charging_automation(charging_controllers(self.coordinator.site), False)
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
        await async_refresh_control(self.coordinator)
        for controller in self.coordinator.site.controllers.values():
            controller.async_update_listeners()

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)
