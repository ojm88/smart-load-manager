"""UI setup flow for Smart Load Manager."""

from __future__ import annotations

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
    state = hass.states.get(used_entity)
    if state is None or state.state in {"unknown", "unavailable"}:
        raise ValueError(
            "EnergyTariff må være konfigurert først; mangler " + used_entity
        )
    try:
        float(state.state)
    except (TypeError, ValueError) as err:
        raise ValueError("EnergyTariff-sensoren er ikke numerisk: " + used_entity) from err
    if str(state.attributes.get("unit_of_measurement", "")).lower() != "kwh":
        raise ValueError("EnergyTariff-sensoren må være i kWh: " + used_entity)

    return device_id, han_entity

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
    """Add a charger later through Configure without rebuilding the first."""

    async def async_step_init(self, user_input=None):
        entries = self.hass.config_entries.async_entries(DOMAIN)
        if len(entries) >= 2:
            return self.async_abort(reason="two_chargers")
        if user_input is not None:
            result = await self.hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "user"}, data=user_input)
            if result["type"] == "create_entry":
                return self.async_create_entry(title="", data=dict(self.config_entry.options))
            return self.async_show_form(step_id="init", data_schema=self._schema(),
                                        errors={"base": "invalid_setup"})
        return self.async_show_form(step_id="init", data_schema=self._schema())

    def _schema(self):
        return vol.Schema({vol.Required(CONF_CHARGER_DEVICE): selector.DeviceSelector(
            selector.DeviceSelectorConfig(integration="easee"))})
