"""UI setup flow for Smart Load Manager."""

from __future__ import annotations

from datetime import time

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import selector
from homeassistant.config_entries import OptionsFlow
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CHARGER_DEVICE,
    CONF_HAN_POWER_ENTITY,
    CONF_HOURLY_LIMIT_KWH,
    CONF_MAX_CURRENT_A,
    CONF_SAFETY_MARGIN_KWH,
    CONF_SCHEDULE_SWITCH,
    CONF_SCHEDULE_TIME_ENTITY,
    CONF_TARIFF_ESTIMATE_ENTITY,
    CONF_TARIFF_USED_ENTITY,
    DOMAIN,
    TARIFF_ESTIMATE_ENTITY,
    TARIFF_USED_ENTITY,
)
from .entity_resolution import resolve_easee_entities
from .calculations import power_to_watts


def _validate_sources(
    hass: HomeAssistant, user_input: dict[str, object]
) -> tuple[str, str]:
    """Validate the selected Easee device, HAN power sensor, and tariff sensors."""

    device_id = str(user_input[CONF_CHARGER_DEVICE])
    han_entity = str(user_input[CONF_HAN_POWER_ENTITY])
    resolve_easee_entities(hass, device_id)

    han_state = hass.states.get(han_entity)
    if han_state is None or han_state.state in {"unknown", "unavailable"}:
        raise ValueError("HAN-effektsensoren er utilgjengelig")
    try:
        power_to_watts(float(han_state.state), str(han_state.attributes.get("unit_of_measurement", "")))
    except (TypeError, ValueError) as err:
        raise ValueError(str(err)) from err

    used_entity = str(user_input.get(CONF_TARIFF_USED_ENTITY, TARIFF_USED_ENTITY))
    estimate_entity = str(user_input.get(CONF_TARIFF_ESTIMATE_ENTITY, TARIFF_ESTIMATE_ENTITY))
    for entity_id in (used_entity, estimate_entity):
        state = hass.states.get(entity_id)
        if state is None or state.state in {"unknown", "unavailable"}:
            raise ValueError(
                "EnergyTariff må være konfigurert først; mangler " + entity_id
            )
        try:
            float(state.state)
        except ValueError as err:
            raise ValueError("EnergyTariff-sensoren er ikke numerisk: " + entity_id) from err
        if str(state.attributes.get("unit_of_measurement", "")).lower() != "kwh":
            raise ValueError("EnergyTariff-sensoren må være i kWh: " + entity_id)

    _validate_schedule(hass, user_input)

    return device_id, han_entity


def _validate_schedule(hass: HomeAssistant, user_input: dict[str, object]) -> None:
    """Validate the optional switch and time-only helper as a pair."""
    schedule_switch = user_input.get(CONF_SCHEDULE_SWITCH)
    schedule_time = user_input.get(CONF_SCHEDULE_TIME_ENTITY)
    if bool(schedule_switch) != bool(schedule_time):
        raise ValueError("Velg både tidsstyringsbryter og starttid, eller la begge stå tomme")
    if schedule_switch:
        switch_state = hass.states.get(str(schedule_switch))
        time_state = hass.states.get(str(schedule_time))
        if switch_state is None or time_state is None:
            raise ValueError("Tidsstyringen må finnes som en bryter og en input_datetime-hjelper")
        if time_state.state in {"unknown", "unavailable"}:
            raise ValueError("Starttid-hjelperen er utilgjengelig")
        try:
            time.fromisoformat(time_state.state)
        except ValueError as err:
            raise ValueError("Starttid må være en input_datetime-hjelper med kun klokkeslett") from err

class SmartLoadManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the first supported controllable load and meter source."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return SmartLoadManagerOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        self._error_detail = ""
        if user_input is not None:
            try:
                device_id, _ = _validate_sources(self.hass, user_input)
            except ValueError as err:
                errors["base"] = "invalid_setup"
                self._error_detail = str(err)
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                title = f"Smart Load Manager {device_id[:8]}"
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_CHARGER_DEVICE): selector.DeviceSelector(
                    selector.DeviceSelectorConfig(integration="easee")
                ),
                vol.Required(CONF_HAN_POWER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="power"
                    )
                ),
                vol.Required(CONF_HOURLY_LIMIT_KWH, default=15.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=50, step=0.5, unit_of_measurement="kWh", mode="box"
                    )
                ),
                vol.Required(CONF_TARIFF_USED_ENTITY, default=TARIFF_USED_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_TARIFF_ESTIMATE_ENTITY, default=TARIFF_ESTIMATE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_MAX_CURRENT_A, default=16): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=6, max=32, step=1, unit_of_measurement="A", mode="box")
                ),
                vol.Required(CONF_SAFETY_MARGIN_KWH, default=0.3): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=3, step=0.1, unit_of_measurement="kWh", mode="box")
                ),
                vol.Optional(CONF_SCHEDULE_SWITCH): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="switch")
                ),
                vol.Optional(CONF_SCHEDULE_TIME_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="input_datetime")
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors,
            description_placeholders={"validation_error": getattr(self, "_error_detail", "")},
        )


class SmartLoadManagerOptionsFlow(OptionsFlow):
    """Edit clock scheduling on an existing beta config entry."""

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry
        self._error_detail = ""

    async def async_step_init(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                _validate_schedule(self.hass, user_input)
            except ValueError as err:
                errors["base"] = "invalid_schedule"
                self._error_detail = str(err)
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_SCHEDULE_SWITCH: user_input.get(CONF_SCHEDULE_SWITCH),
                        CONF_SCHEDULE_TIME_ENTITY: user_input.get(CONF_SCHEDULE_TIME_ENTITY),
                    },
                )

        current_switch = self.config_entry.options.get(
            CONF_SCHEDULE_SWITCH, self.config_entry.data.get(CONF_SCHEDULE_SWITCH)
        )
        current_time = self.config_entry.options.get(
            CONF_SCHEDULE_TIME_ENTITY, self.config_entry.data.get(CONF_SCHEDULE_TIME_ENTITY)
        )
        schema_fields = {}
        switch_field = vol.Optional(CONF_SCHEDULE_SWITCH)
        time_field = vol.Optional(CONF_SCHEDULE_TIME_ENTITY)
        if current_switch:
            switch_field = vol.Optional(CONF_SCHEDULE_SWITCH, default=current_switch)
        if current_time:
            time_field = vol.Optional(CONF_SCHEDULE_TIME_ENTITY, default=current_time)
        schema_fields[switch_field] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        )
        schema_fields[time_field] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_datetime")
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_fields),
            errors=errors,
            description_placeholders={"validation_error": self._error_detail},
        )

