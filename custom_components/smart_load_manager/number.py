"""User current-limit control, routed through the installed Easee integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ChargingCoordinator
from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ChargingCoordinator = entry.runtime_data
    async_add_entities([ChargingCurrentLimit(coordinator, entry)])


class ChargingCurrentLimit(CoordinatorEntity[ChargingCoordinator], NumberEntity):
    """Dynamic current cap for this charger; 0 means pause charging."""

    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:current-ac"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_manual_current_limit"
        self._attr_has_entity_name = True
        self._attr_translation_key = "manual_current_limit"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Smart Load Manager",
            model="Easee charging control",
            name=entry.title,
        )
        # When Easee has no usable limit, expose a zero-range control rather
        # than implying that an arbitrary positive current is available.
        self._attr_native_max_value = 0.0

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        commanded = self.coordinator.last_commanded_current
        if commanded is not None:
            return float(commanded)
        recommended = data.get("recommended_current_a")
        return float(recommended) if recommended is not None else 0.0

    @property
    def native_max_value(self) -> float:
        data = self.coordinator.data or {}
        return float(data.get("max_current_a", 0) or 0.0)

    async def async_set_native_value(self, value: float) -> None:
        data = self.coordinator.data or {}
        requested = int(round(value))
        if self.coordinator.auto_control:
            raise HomeAssistantError("Slå av automatisk laststyring før manuell strømgrense endres.")
        if requested < 0 or requested > self.native_max_value:
            raise HomeAssistantError("Strømgrensen er utenfor konfigurert område.")
        if requested > 0:
            detected_maximum = float(data.get("max_current_a", 0) or 0)
            if detected_maximum <= 0:
                raise HomeAssistantError("Easee har ikke rapportert en gyldig maksimal kursstrøm ennå.")
            if requested > detected_maximum:
                raise HomeAssistantError(f"Strømgrensen kan ikke overstige Easees kursgrense på {detected_maximum:g} A.")
            if not data.get("han_fresh", False):
                raise HomeAssistantError("HAN-målingen er ugyldig eller eldre enn 60 sekunder.")
            if not data.get("schedule_allowed", True):
                raise HomeAssistantError("Tidsstyringen sperrer lading akkurat nå.")
            minimum = data.get("control_minimum_current_a")
            if minimum is None:
                raise HomeAssistantError("Nedre strømgrense er ukjent før lading og fasebruk er målt.")
            if requested < int(minimum):
                raise HomeAssistantError(
                    f"Bruk 0 A for pause eller minst {int(minimum)} A for denne ladeformen."
                )
        await self.coordinator.async_set_current(requested)
        await self.coordinator.async_request_refresh()
