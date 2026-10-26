"""UI setup flow for Smart Load Manager."""

from __future__ import annotations

import math

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, selector

from .const import (
    CONF_CHARGER_DEVICE,
    CONF_HAN_POWER_ENTITY,
    CONF_SAFETY_MARGIN_KWH,
    CONF_TARIFF_USED_ENTITY,
    DOMAIN,
    TARIFF_USED_ENTITY,
)
from .entity_resolution import resolve_easee_entities
from .calculations import power_to_watts


def _validate_sources(
    hass: HomeAssistant, user_input: dict[str, object]
) -> tuple[str, str]:
    """Validate the selected Easee device, HAN power sensor, and tariff sensors."""

    device_id = str(user_input[CONF_CHARGER_DEVICE])
    resolve_easee_entities(hass, device_id)
    _validate_meter_sources(hass, user_input)
    return device_id, str(user_input[CONF_HAN_POWER_ENTITY])


def _validate_meter_sources(hass, user_input):
    """Validate shared sources independently of charger diagnostics."""
    han_entity = str(user_input[CONF_HAN_POWER_ENTITY])
    han_state = hass.states.get(han_entity)
    if han_state is None or han_state.state in {"unknown", "unavailable"}:
        raise ValueError("HAN-effektsensoren er utilgjengelig")
    try:
        power = power_to_watts(float(han_state.state), str(han_state.attributes.get("unit_of_measurement", "")))
        if not math.isfinite(power) or power <= 0:
            raise ValueError("HAN-effekten må være et positivt, gyldig tall")
    except (TypeError, ValueError) as err:
        raise ValueError(str(err)) from err

    used_entity = str(user_input.get(CONF_TARIFF_USED_ENTITY, TARIFF_USED_ENTITY))
    state = hass.states.get(used_entity)
    if state is None or state.state in {"unknown", "unavailable"}:
        raise ValueError(
            "EnergyTariff må være konfigurert først; mangler " + used_entity
        )
    try:
        used = float(state.state)
        if not math.isfinite(used) or used < 0:
            raise ValueError("EnergyTariff-forbruk må være et gyldig, ikke-negativt tall")
    except (TypeError, ValueError) as err:
        raise ValueError("EnergyTariff-sensoren er ikke numerisk: " + used_entity) from err
    if str(state.attributes.get("unit_of_measurement", "")).lower() != "kwh":
        raise ValueError("EnergyTariff-sensoren må være i kWh: " + used_entity)

    margin = float(user_input.get(CONF_SAFETY_MARGIN_KWH, 0.3))
    if not math.isfinite(margin) or not 0 <= margin <= 3:
        raise ValueError("Sikkerhetsmargin må være mellom 0 og 3 kWh")


class SmartLoadManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the first supported controllable load and meter source."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        existing = self._async_current_entries()
        if len(existing) >= 2:
            return self.async_abort(reason="two_chargers")
        from .site import site_entry
        owner = site_entry(self.hass) if existing else None
        errors: dict[str, str] = {}
        self._error_detail = ""
        if user_input is not None:
            user_input = dict(user_input)
            if owner:
                for field in (CONF_HAN_POWER_ENTITY, CONF_TARIFF_USED_ENTITY, CONF_SAFETY_MARGIN_KWH):
                    user_input[field] = owner.data[field]
            try:
                device_id, _ = _validate_sources(self.hass, user_input)
            except ValueError as err:
                errors["base"] = "invalid_setup"
                self._error_detail = str(err)
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()
                charger = dr.async_get(self.hass).devices.get(device_id)
                charger_name = (charger.name_by_user or charger.name) if charger else device_id[:8]
                title = f"Smart Load Manager OJM – {charger_name}"
                if owner:
                    from homeassistant.util import slugify
                    user_input["entity_suffix"] = f"{slugify(charger_name) or 'charger'}_{device_id[:6]}"
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_CHARGER_DEVICE): selector.DeviceSelector(
                    selector.DeviceSelectorConfig(integration="easee")
                ),
                vol.Required(CONF_HAN_POWER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_TARIFF_USED_ENTITY, default=TARIFF_USED_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_SAFETY_MARGIN_KWH, default=0.3): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=3, step=0.1, unit_of_measurement="kWh", mode="box")
                ),
            }
        )
        if owner:
            schema = vol.Schema({vol.Required(CONF_CHARGER_DEVICE): selector.DeviceSelector(
                selector.DeviceSelectorConfig(integration="easee"))})
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors,
            description_placeholders={"validation_error": getattr(self, "_error_detail", "")},
        )



    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ChargerOptionsFlow()


class ChargerOptionsFlow(config_entries.OptionsFlow):
    """Edit household sources or add a charger without rebuilding the site."""

    async def async_step_init(self, user_input=None):
        # Retain direct add-charger calls used by older clients/tests.
        if user_input is not None and CONF_CHARGER_DEVICE in user_input:
            return await self.async_step_add_charger(user_input)
        menu = ["household"]
        if len(self.hass.config_entries.async_entries(DOMAIN)) < 2:
            menu.append("add_charger")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_household(self, user_input=None):
        from .site import site_entry
        owner = site_entry(self.hass)
        fields = (CONF_HAN_POWER_ENTITY, CONF_TARIFF_USED_ENTITY, CONF_SAFETY_MARGIN_KWH)
        values = {field: owner.data.get(field) for field in fields}
        detail = ""
        errors = {}
        if user_input is not None:
            values.update(user_input)
            try:
                _validate_meter_sources(self.hass, values)
            except (ValueError, TypeError) as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                shared = {field: values[field] for field in fields}
                # Validate everything before changing entries. Existing limits,
                # priorities, charger IDs and per-charger schedules are retained.
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    self.hass.config_entries.async_update_entry(entry, data={**entry.data, **shared})
                return self.async_create_entry(title="", data=dict(self.config_entry.options))
        schema = vol.Schema({
            vol.Required(CONF_HAN_POWER_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_TARIFF_USED_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_SAFETY_MARGIN_KWH): selector.NumberSelector(selector.NumberSelectorConfig(
                min=0, max=3, step=0.1, unit_of_measurement="kWh", mode="box")),
        })
        return self.async_show_form(step_id="household",
            data_schema=self.add_suggested_values_to_schema(schema, values),
            errors=errors, description_placeholders={"validation_error": detail})

    async def async_step_add_charger(self, user_input=None):
        entries = self.hass.config_entries.async_entries(DOMAIN)
        if len(entries) >= 2:
            return self.async_abort(reason="two_chargers")
        detail = ""
        errors = {}
        if user_input is not None:
            result = await self.hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "user"}, data=user_input)
            if result["type"] == "create_entry":
                return self.async_create_entry(title="", data=dict(self.config_entry.options))
            detail = result.get("description_placeholders", {}).get("validation_error", "")
            if result.get("type") == "abort":
                return self.async_abort(reason=result["reason"])
            # A failed nested flow is replaced by this form, not left running.
            if result.get("flow_id"):
                self.hass.config_entries.flow.async_abort(result["flow_id"])
            errors["base"] = "invalid_setup"
        return self.async_show_form(
            step_id="add_charger", data_schema=self.add_suggested_values_to_schema(self._schema(), user_input),
            errors=errors, description_placeholders={"validation_error": detail})

    def _schema(self):
        return vol.Schema({vol.Required(CONF_CHARGER_DEVICE): selector.DeviceSelector(
            selector.DeviceSelectorConfig(integration="easee"))})
