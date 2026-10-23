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
from .control import manual_control_is_available
from .entity_ids import suggested_entity_id


def _message(hass: HomeAssistant, norwegian: str, english: str) -> str:
    """Return the control error in the configured Home Assistant language."""
    return norwegian if str(hass.config.language or "").startswith("nb") else english


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
        self.entity_id = f"number.{suggested_entity_id('number', 'manual_current_limit')}"
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
    def available(self) -> bool:
        """Disable manual input while automatic control owns the current limit."""
        return super().available and manual_control_is_available(
            self.coordinator.auto_control
        ) and not self.coordinator.charging_paused

    @property
    def native_max_value(self) -> float:
        data = self.coordinator.data or {}
        return float(data.get("max_current_a", 0) or 0.0)

    async def async_set_native_value(self, value: float) -> None:
        data = self.coordinator.data or {}
        requested = int(round(value))
        if self.coordinator.auto_control:
            raise HomeAssistantError(
                _message(
                    self.hass,
                    "Slå av automatisk laststyring før du endrer manuell ladestrøm.",
                    "Turn off automatic load control before changing manual charging current.",
                )
            )
        if self.coordinator.charging_paused:
            raise HomeAssistantError(
                _message(
                    self.hass,
                    "Slå av ladepause før du endrer ladestrømmen.",
                    "Turn off charging pause before changing the current limit.",
                )
            )
        if requested < 0 or requested > self.native_max_value:
            raise HomeAssistantError(
                _message(self.hass, "Strømgrensen er utenfor tillatt område.", "The current limit is outside the allowed range.")
            )
        if requested > 0:
            detected_maximum = float(data.get("max_current_a", 0) or 0)
            if detected_maximum <= 0:
                raise HomeAssistantError(
                    _message(self.hass, "Easee har ikke rapportert en gyldig maksimal strøm ennå.", "Easee has not reported a valid maximum current yet.")
                )
            if requested > detected_maximum:
                raise HomeAssistantError(
                    _message(
                        self.hass,
                        f"Strømgrensen kan ikke overstige Easees grense på {detected_maximum:g} A.",
                        f"The current limit cannot exceed Easee's limit of {detected_maximum:g} A.",
                    )
                )
            if not data.get("han_fresh", False):
                raise HomeAssistantError(
                    _message(self.hass, "HAN-målingen er ugyldig eller eldre enn 60 sekunder.", "The HAN meter reading is invalid or older than 60 seconds.")
                )
            if not data.get("schedule_allowed", True):
                raise HomeAssistantError(
                    _message(self.hass, "Tidsstyringen sperrer lading akkurat nå.", "The charging schedule is blocking charging now.")
                )
            minimum = data.get("control_minimum_current_a")
            if minimum is None:
                raise HomeAssistantError(
                    _message(self.hass, "Nedre strømgrense er ukjent før lading og fasebruk er målt.", "The minimum current is unknown until charging and phase use are measured.")
                )
            if requested < int(minimum):
                raise HomeAssistantError(
                    _message(
                        self.hass,
                        f"Bruk 0 A for pause eller minst {int(minimum)} A for denne ladeformen.",
                        f"Use 0 A to pause, or at least {int(minimum)} A for this charging setup.",
                    )
                )
        await self.coordinator.async_set_current(requested)
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self):
        """Explain when this manual actuator is available and what zero means."""
        norwegian = str(self.hass.config.language or "").startswith("nb")
        return {
            "use_when": "Brukes når automatisk laststyring er av" if norwegian else "Use when automatic load control is off",
            "zero_current": "0 A setter laderen på pause" if norwegian else "0 A pauses charging",
            "positive_current": "Setter dynamisk strømgrense på Easee-laderen" if norwegian else "Sets an Easee dynamic current limit",
            "automatic_control_active": self.coordinator.auto_control,
            "unavailable_reason": (
                "Slå av automatisk laststyring før du endrer verdien"
                if norwegian and self.coordinator.auto_control
                else "Turn off automatic load control before changing this value"
                if self.coordinator.auto_control
                else None
            ),
        }
