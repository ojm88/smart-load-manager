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
        power = power_to_watts(
            float(han_state.state),
            str(han_state.attributes.get("unit_of_measurement", "")),
        )
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
            raise ValueError(
                "EnergyTariff-forbruk må være et gyldig, ikke-negativt tall"
            )
    except (TypeError, ValueError) as err:
        raise ValueError(
            "EnergyTariff-sensoren er ikke numerisk: " + used_entity
        ) from err
    if str(state.attributes.get("unit_of_measurement", "")).lower() != "kwh":
        raise ValueError("EnergyTariff-sensoren må være i kWh: " + used_entity)

    margin = float(user_input.get(CONF_SAFETY_MARGIN_KWH, 0.3))
    if not math.isfinite(margin) or not 0 <= margin <= 3:
        raise ValueError("Sikkerhetsmargin må være mellom 0 og 3 kWh")


class SmartLoadManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the first supported controllable load and meter source."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        # Preserve direct old-client calls for adding a single charger.
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        return await self.async_step_household(user_input)

    async def async_step_household(self, user_input=None):
        errors = {}
        detail = ""
        if user_input is not None:
            try:
                _validate_meter_sources(self.hass, user_input)
            except (ValueError, TypeError) as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                self._household = dict(user_input)
                return await self.async_step_load_type()
        return self.async_show_form(
            step_id="household",
            data_schema=_household_schema(),
            errors=errors,
            description_placeholders={"validation_error": detail},
        )

    async def async_step_load_type(self, user_input=None):
        return self.async_show_menu(
            step_id="load_type", menu_options=["charging", "planned"]
        )

    async def async_step_planned(self, user_input=None):
        if user_input is not None:
            return await self.async_step_load_type()
        return self.async_show_form(step_id="planned", data_schema=vol.Schema({}))

    async def async_step_charging(self, user_input=None):
        errors = {}
        detail = ""
        if user_input is not None:
            try:
                records = _make_loads(self.hass, user_input.get("chargers", []))
            except ValueError as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                await self.async_set_unique_id("installation")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Smart Load Manager OJM",
                    data={"household": self._household, "loads": records},
                )
        return self.async_show_form(
            step_id="charging",
            data_schema=vol.Schema(
                {
                    vol.Required("chargers"): selector.DeviceSelector(
                        selector.DeviceSelectorConfig(
                            integration="easee", multiple=True
                        )
                    )
                }
            ),
            errors=errors,
            description_placeholders={"validation_error": detail},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ChargerOptionsFlow()


class ChargerOptionsFlow(config_entries.OptionsFlow):
    """Edit household sources or add a charger without rebuilding the site."""

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init", menu_options=["household", "chargers"]
        )

    async def async_step_household(self, user_input=None):
        parent = self.config_entry
        values = dict(parent.data["household"])
        errors = {}
        detail = ""
        if user_input is not None:
            values.update(user_input)
            try:
                _validate_meter_sources(self.hass, values)
            except (ValueError, TypeError) as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                self.hass.config_entries.async_update_entry(
                    parent, data={**parent.data, "household": values}
                )
                return self.async_create_entry(title="", data=dict(parent.options))
        return self.async_show_form(
            step_id="household",
            data_schema=self.add_suggested_values_to_schema(
                _household_schema(), values
            ),
            errors=errors,
            description_placeholders={"validation_error": detail},
        )

    async def async_step_chargers(self, user_input=None):
        parent = self.config_entry
        errors = {}
        detail = ""
        if user_input is not None:
            try:
                records = _make_loads(
                    self.hass,
                    user_input.get("chargers", []),
                    list(parent.data["loads"])
                    + list(parent.data.get("retired_loads", [])),
                )
            except ValueError as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                # Do not drop an actively controlling load. Reload only after
                # its existing actuator has acknowledged 0 A.
                retained = {r["id"] for r in records}
                runtime = getattr(parent, "runtime_data", None)
                for key, controller in getattr(runtime, "controllers", {}).items():
                    if key not in retained:
                        await controller._async_send_current(0)
                retired = {
                    r["data"][CONF_CHARGER_DEVICE]: r
                    for r in list(parent.data.get("retired_loads", []))
                    + list(parent.data["loads"])
                    if r["id"] not in retained
                }
                self.hass.config_entries.async_update_entry(
                    parent,
                    data={
                        **parent.data,
                        "loads": records,
                        "retired_loads": list(retired.values()),
                    },
                )
                # Reload refreshes the pair-only entities and groups. Automatic
                # control remains opt-in after this configuration change.
                self.hass.async_create_task(
                    self.hass.config_entries.async_reload(parent.entry_id)
                )
                return self.async_create_entry(title="", data=dict(parent.options))
        return self.async_show_form(
            step_id="chargers",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required("chargers"): selector.DeviceSelector(
                            selector.DeviceSelectorConfig(
                                integration="easee", multiple=True
                            )
                        )
                    }
                ),
                {
                    "chargers": [
                        r["data"][CONF_CHARGER_DEVICE] for r in parent.data["loads"]
                    ]
                },
            ),
            errors=errors,
            description_placeholders={"validation_error": detail},
        )


def _household_schema():
    return vol.Schema(
        {
            vol.Required(CONF_HAN_POWER_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Required(
                CONF_TARIFF_USED_ENTITY, default=TARIFF_USED_ENTITY
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
            vol.Required(CONF_SAFETY_MARGIN_KWH, default=0.3): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=3, step=0.1, unit_of_measurement="kWh", mode="box"
                )
            ),
        }
    )


def _make_loads(hass, device_ids, existing=()):
    from homeassistant.util import slugify
    from uuid import uuid4

    if (
        not isinstance(device_ids, list)
        or not 1 <= len(device_ids) <= 2
        or len(set(device_ids)) != len(device_ids)
    ):
        raise ValueError(
            "Velg én eller to forskjellige Easee-ladere / Select one or two distinct Easee chargers"
        )
    saved = {r["data"][CONF_CHARGER_DEVICE]: r for r in existing}
    suffixes = {r["data"]["entity_suffix"] for r in existing}
    records = []
    for device_id in device_ids:
        resolve_easee_entities(hass, device_id)
        if device_id in saved:
            records.append(saved[device_id])
            continue
        device = dr.async_get(hass).devices.get(device_id)
        if device is None:
            raise ValueError("Easee device no longer exists")
        name = device.name_by_user or device.name or "Charger"
        suffix = slugify(name) or "charger"
        if suffix in suffixes:
            suffix += "_" + device_id[:6]
        if suffix in suffixes:
            raise ValueError("Charger identity collision; choose distinct device names")
        suffixes.add(suffix)
        records.append(
            {
                "id": uuid4().hex,
                "title": f"Smart Load Manager OJM – {name}",
                "data": {
                    CONF_CHARGER_DEVICE: device_id,
                    "charger_name": name,
                    "entity_suffix": suffix,
                },
            }
        )
    order = {r["id"]: i for i, r in enumerate(existing)}
    return sorted(records, key=lambda r: order.get(r["id"], len(order)))
