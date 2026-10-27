"""UI setup flow for Smart Load Manager."""

from __future__ import annotations
from .device_info import get_device

import math
from collections import Counter

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, selector

from .const import (
    CONF_CHARGER_DEVICE,
    CONF_CONNECTION,
    CONNECTION_OPTIONS,
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
        """Choose chargers entirely within the native setup dialog."""
        errors = {}
        detail = ""
        if user_input is not None:
            try:
                device_id = user_input.get(CONF_CHARGER_DEVICE)
                records = _make_loads(self.hass, [device_id])
                if device_id not in {o["value"] for o in _charger_options(self.hass)}:
                    raise ValueError("Velg en tilgjengelig Easee-lader / Select an available Easee charger")
                records[0]["data"][CONF_CONNECTION] = _connection(user_input)
                self._draft_loads = records
            except ValueError as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                return await self.async_step_charging_next()
        return self.async_show_form(
            step_id="charging",
            data_schema=_charger_schema(self.hass),
            errors=errors,
            description_placeholders={"validation_error": detail},
        )

    async def async_step_charging_next(self, user_input=None):
        return self.async_show_menu(
            step_id="charging_next", menu_options=["finish_charging", "second_charger"]
        )

    async def async_step_second_charger(self, user_input=None):
        errors = {}
        detail = ""
        excluded = {r["data"][CONF_CHARGER_DEVICE] for r in self._draft_loads}
        if user_input is not None:
            try:
                device_id = _new_charger_device(self.hass, user_input, excluded)
                second = _make_loads(self.hass, [device_id], self._draft_loads)
                connection = _connection(user_input)
            except ValueError as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                second[0] = {**second[0], "data": {**second[0]["data"], CONF_CONNECTION: connection}}
                self._draft_loads += second
                return await self.async_step_finish_charging()
        return self.async_show_form(
            step_id="second_charger",
            data_schema=_charger_schema(self.hass, exclude=excluded),
            errors=errors,
            description_placeholders={"validation_error": detail},
        )

    async def async_step_finish_charging(self, user_input=None):
        await self.async_set_unique_id("installation")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title="Smart Load Manager OJM",
            data={"household": self._household, "loads": self._draft_loads},
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
        """Membership actions are explicit; an add never replaces current loads."""
        parent = self.config_entry
        menu = ["connection"]
        if len(parent.data["loads"]) < 2:
            menu.append("add_charger")
        if len(parent.data["loads"]) > 1:
            menu.append("remove_charger")
        return self.async_show_menu(step_id="chargers", menu_options=menu)


    async def async_step_add_charger(self, user_input=None):
        parent = self.config_entry
        active = list(parent.data["loads"])
        if len(active) >= 2:
            return self.async_abort(reason="two_chargers")
        excluded = {r["data"][CONF_CHARGER_DEVICE] for r in active}
        errors = {}
        detail = ""
        if user_input is not None:
            try:
                device_id = _new_charger_device(self.hass, user_input, excluded)
                new = _make_loads(
                    self.hass,
                    [device_id],
                    active + list(parent.data.get("retired_loads", [])),
                )
                connection = _connection(user_input)
                new = [{**r, "data": {**r["data"], CONF_CONNECTION: connection}} for r in new]
            except ValueError as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                # Always keep every existing load and its saved identity/options.
                records = active + new
                retired = [
                    r
                    for r in parent.data.get("retired_loads", [])
                    if r["data"][CONF_CHARGER_DEVICE] != device_id
                ]
                return await self._save_membership(records, retired)
        return self.async_show_form(
            step_id="add_charger",
            data_schema=_charger_schema(self.hass, exclude=excluded),
            errors=errors,
            description_placeholders={"validation_error": detail},
        )

    async def async_step_connection(self, user_input=None):
        """Confirm/edit one load's wiring, retaining all identities and settings."""
        parent = self.config_entry
        active = list(parent.data["loads"])
        errors = {}
        detail = ""
        if user_input is not None:
            record = next((r for r in active if r["data"][CONF_CHARGER_DEVICE] == user_input.get(CONF_CHARGER_DEVICE)), None)
            try:
                connection = _connection(user_input)
                if record is None:
                    raise ValueError("Velg en konfigurert lader / Select a configured charger")
                if record["data"].get(CONF_CONNECTION) == connection:
                    return self.async_create_entry(title="", data=dict(parent.options))
                controller = getattr(getattr(parent, "runtime_data", None), "controllers", {}).get(record["id"])
                if controller is not None:
                    async with controller.site.lock:
                        await controller._async_send_current(0)
                        controller.auto_control = False
                records = [
                    {**r, "data": {**r["data"], CONF_CONNECTION: connection}} if r["id"] == record["id"] else r
                    for r in active
                ]
            except Exception as err:
                errors["base"] = "invalid_setup"
                detail = str(err)
            else:
                return await self._save_membership(records, list(parent.data.get("retired_loads", [])))
        choices = [{"value": r["data"][CONF_CHARGER_DEVICE], "label": r["data"].get("charger_name", r["title"])} for r in active]
        return self.async_show_form(
            step_id="connection",
            data_schema=vol.Schema({
                vol.Required(CONF_CHARGER_DEVICE): _choice_selector(choices),
                vol.Required(CONF_CONNECTION): _connection_selector(),
            }), errors=errors, description_placeholders={"validation_error": detail},
        )

    async def async_step_remove_charger(self, user_input=None):
        parent = self.config_entry
        active = list(parent.data["loads"])
        if len(active) < 2:
            return self.async_abort(reason="one_charger_required")
        errors = {}
        detail = ""
        if user_input is not None:
            device_id = user_input.get(CONF_CHARGER_DEVICE)
            removed = next(
                (r for r in active if r["data"][CONF_CHARGER_DEVICE] == device_id), None
            )
            if removed is None:
                errors["base"] = "invalid_setup"
                detail = "Velg en konfigurert lader / Select a configured charger"
            else:
                try:
                    runtime = getattr(parent, "runtime_data", None)
                    controller = getattr(runtime, "controllers", {}).get(removed["id"])
                    if controller is None:
                        raise ValueError(
                            "Last inn integrasjonen før laderen fjernes / Load the integration before removing a charger"
                        )
                    # Command acknowledgement only; physical stop still requires telemetry.
                    async with controller.site.lock:
                        await controller._async_send_current(0)
                        controller.auto_control = False
                except Exception as err:
                    errors["base"] = "invalid_setup"
                    detail = str(err)
                else:
                    records = [r for r in active if r["id"] != removed["id"]]
                    retired = [
                        r
                        for r in parent.data.get("retired_loads", [])
                        if r["id"] != removed["id"]
                    ] + [removed]
                    return await self._save_membership(records, retired)
        options = [
            {
                "value": r["data"][CONF_CHARGER_DEVICE],
                "label": r["data"].get("charger_name", r["title"]),
            }
            for r in active
        ]
        return self.async_show_form(
            step_id="remove_charger",
            data_schema=vol.Schema(
                {vol.Required(CONF_CHARGER_DEVICE): _choice_selector(options)}
            ),
            errors=errors,
            description_placeholders={"validation_error": detail},
        )

    async def _save_membership(self, records, retired):
        parent = self.config_entry
        self.hass.config_entries.async_update_entry(
            parent, data={**parent.data, "loads": records, "retired_loads": retired}
        )
        # OptionsFlow must finish before reloading. The old runtime is cleaned
        # by its own saved controller identities, not this edited membership.
        self.hass.async_create_task(
            self.hass.config_entries.async_reload(parent.entry_id)
        )
        return self.async_create_entry(title="", data=dict(parent.options))


def _charger_options(hass, exclude=()):
    """Resolve a compact list through Easee's registry index, without I/O."""
    registry = dr.async_get(hass)
    devices = {}
    for config in hass.config_entries.async_entries("easee"):
        for device in dr.async_entries_for_config_entry(registry, config.entry_id):
            if device.id not in exclude and device.disabled_by is None:
                devices[device.id] = device
    labels = {
        key: device.name_by_user or device.name or "Easee"
        for key, device in devices.items()
    }
    counts = Counter(labels.values())
    return [
        {
            "value": key,
            "label": name if counts[name] == 1 else f"{name} ({key[:6]})",
        }
        for key, name in sorted(
            labels.items(), key=lambda item: (item[1].casefold(), item[0])
        )
    ]


def _choice_selector(options, *, multiple=False):
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            multiple=multiple,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _native_charger_filter(hass):
    """Use registry metadata to avoid HA's integration-wide membership lookup.

    DeviceSelector remains responsible for HA branding. Manufacturer/model
    filters are presentation only; submissions are checked against Easee's
    indexed source devices before saving. Missing metadata uses the supported
    integration filter rather than hiding a valid charger.
    """
    registry = dr.async_get(hass)
    devices = [get_device(registry, o["value"]) for o in _charger_options(hass)]
    if not devices or any(not d or not d.manufacturer for d in devices):
        return [{"integration": "easee"}]
    pairs = sorted({(d.manufacturer, d.model or "") for d in devices})
    filters = []
    for manufacturer, model in pairs:
        device_filter = {"manufacturer": manufacturer}
        if model:
            device_filter["model"] = model
        filters.append(device_filter)
    return filters


def _charger_schema(hass, *, exclude=()):
    # HA's supported multi-device picker excludes current values from its ADD
    # dropdown. Preselect existing sources; never replace membership on submit.
    selected = sorted(exclude)
    key = (
        vol.Required(CONF_CHARGER_DEVICE, default=selected)
        if selected else vol.Required(CONF_CHARGER_DEVICE)
    )
    return vol.Schema({
        key: selector.DeviceSelector(selector.DeviceSelectorConfig(
            filter=_native_charger_filter(hass), multiple=bool(selected)
        )),
        vol.Required(CONF_CONNECTION): _connection_selector(),
    })


def _new_charger_device(hass, user_input, existing):
    selected = user_input.get(CONF_CHARGER_DEVICE)
    # Retain compatibility with the old single-choice submission contract.
    if isinstance(selected, str):
        added = [selected]
    else:
        if (
            not isinstance(selected, list)
            or any(not isinstance(item, str) or not item for item in selected)
            or len(set(selected)) != len(selected)
        ):
            raise ValueError("Velg forskjellige ladere / Select distinct chargers")
        if not set(existing).issubset(selected):
            raise ValueError("Behold eksisterende lader som valgt / Keep the existing charger selected")
        added = [device for device in selected if device not in existing]
    allowed = {o["value"] for o in _charger_options(hass, existing)}
    if len(added) != 1 or added[0] not in allowed:
        raise ValueError("Velg én ledig Easee-lader / Select one unused Easee charger")
    return added[0]


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
        or any(not isinstance(device, str) or not device for device in device_ids)
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
        device = get_device(dr.async_get(hass), device_id)
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


def _connection_selector():
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=list(CONNECTION_OPTIONS), translation_key=CONF_CONNECTION,
        mode=selector.SelectSelectorMode.DROPDOWN))


def _connection(user_input):
    value = user_input.get(CONF_CONNECTION)
    if not isinstance(value, str) or value not in CONNECTION_OPTIONS:
        raise ValueError("Bekreft fysisk tilkobling / Confirm the physical connection")
    return value
