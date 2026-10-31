"""User current-limit control, routed through the installed Easee integration."""

from __future__ import annotations
import math
from .device_info import ChargerNameMixin, charger_device_info, name_charger_entity

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ChargingCoordinator
from .control import manual_control_is_available, minimum_manual_current
from .entity_ids import suggested_entity_id


def _message(hass: HomeAssistant, norwegian: str, english: str) -> str:
    """Return the control error in the configured Home Assistant language."""
    return norwegian if str(hass.config.language or "").startswith("nb") else english


async def async_setup_entry(hass, entry, async_add_entities):
    from .installation import platform_loads, add_grouped
    for load in platform_loads(entry):
        coordinator = load.runtime_data
        add_grouped(hass, entry, async_add_entities, [ChargingCurrentLimit(coordinator, load)], "charging")


class ChargingCurrentLimit(ChargerNameMixin, CoordinatorEntity[ChargingCoordinator], NumberEntity):
    """Manual current selection within the verified charger limits."""

    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:current-ac"

    def __init__(self, coordinator: ChargingCoordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_manual_current_limit"
        self._attr_has_entity_name = True
        self._attr_translation_key = "manual_current_limit"
        name_charger_entity(self, entry, "number", "manual_current_limit")
        self.entity_id = f"number.{suggested_entity_id('number', 'manual_current_limit', entry)}"
        self._attr_device_info = charger_device_info(entry)
        # When Easee has no usable limit, expose a zero-range control rather
        # than implying that an arbitrary positive current is available.
        self._attr_native_max_value = 0.0

    @property
    def native_value(self) -> float | None:
        selected = getattr(self.coordinator, 'manual_current_setting', None)
        if not self.coordinator.auto_control and selected is not None:
            return float(selected)
        data = self.coordinator.data or {}
        commanded = self.coordinator.last_commanded_current
        if commanded is not None:
            return float(commanded)
        recommended = data.get("recommended_current_a")
        return float(recommended) if recommended is not None else 0.0

    @property
    def available(self) -> bool:
        """Disable manual input while automatic control owns the current limit."""
        return self.native_min_value > 0 and super().available and manual_control_is_available(
            self.coordinator.auto_control
        ) and not self.coordinator.charging_paused

    @property
    def native_min_value(self) -> float:
        return float(minimum_manual_current(self.coordinator.data or {}))

    @property
    def native_max_value(self) -> float:
        data = self.coordinator.data or {}
        return float(data.get("max_current_a", 0) or 0.0)

    async def async_set_native_value(self, value: float) -> None:
        data = self.coordinator.data or {}
        try:
            raw = float(value)
        except (TypeError, ValueError):
            raw = math.nan
        minimum = minimum_manual_current(data)
        if (not math.isfinite(raw) or not raw.is_integer() or minimum <= 0
                or raw < minimum or raw > self.native_max_value):
            raise HomeAssistantError(_message(
                self.hass, "Velg en hel ampere innenfor laderens tillatte grenser. Bruk ladepause for å stoppe.",
                "Choose whole amperes within the charger limits. Use charging pause to stop."))
        requested = int(raw)
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
                    _message(self.hass, "HAN-målingen er ugyldig eller for gammel.", "The HAN meter reading is invalid or stale.")
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
                        f"Velg minst {int(minimum)} A. Bruk ladepause for å stoppe.",
                        f"Choose at least {int(minimum)} A. Use charging pause to stop.",
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
            "pause_control": "Bruk bryteren Ladepause" if norwegian else "Use the Charging pause switch",
            "positive_current": "Setter dynamisk strømgrense på Easee-laderen" if norwegian else "Sets an Easee dynamic current limit",
            "automatic_control_active": self.coordinator.auto_control,
            "last_sent_current_a": self.coordinator.last_commanded_current,
            "unavailable_reason": (
                "Slå av automatisk laststyring før du endrer verdien"
                if norwegian and self.coordinator.auto_control
                else "Turn off automatic load control before changing this value"
                if self.coordinator.auto_control
                else None
            ),
        }
