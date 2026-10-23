"""Opt-in automatic control. It starts disabled after every HA restart."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ChargingCoordinator
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ChargingCoordinator = entry.runtime_data
    async_add_entities([
        AutomaticLoadControl(coordinator, entry),
        ChargingScheduleControl(coordinator, entry),
    ])


class AutomaticLoadControl(CoordinatorEntity[ChargingCoordinator], SwitchEntity):
    """Enable/disable recommended current updates; disabled by default."""

    _attr_icon = "mdi:robot"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_automatic_control"
        self._attr_has_entity_name = True
        self._attr_translation_key = "automatic_control"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Smart Load Manager",
            model="Easee charging control",
            name=entry.title,
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.auto_control

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.auto_control = True
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.auto_control = False
        self.async_write_ha_state()


class ChargingScheduleControl(CoordinatorEntity[ChargingCoordinator], SwitchEntity):
    """Enable the integration-owned daily charging time window."""

    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_schedule_control"
        self._attr_has_entity_name = True
        self._attr_translation_key = "schedule_control"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Smart Load Manager",
            model="Easee charging control",
            name=entry.title,
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.schedule_enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_schedule_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_schedule_enabled(False)
        self.async_write_ha_state()
