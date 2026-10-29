"""Smart Load Manager installation lifecycle."""

from __future__ import annotations
import asyncio
from types import SimpleNamespace
from .const import DOMAIN, PLATFORMS
from .installation import platform_loads, ensure_groups, group_id


async def async_migrate_entry(hass, entry):
    """Consolidate beta.4 chargers without recreating entity/load identities."""
    from homeassistant.helpers import entity_registry as er, device_registry as dr
    from homeassistant.util import slugify
    from .device_info import get_device

    lock = hass.data.setdefault(DOMAIN, {}).setdefault("migration_lock", asyncio.Lock())
    async with lock:
        entries = hass.config_entries.async_entries(DOMAIN)
        parent = next((e for e in entries if "loads" in e.data), None)
        if parent is None:
            parent = next(
                (e for e in entries if not e.data.get("entity_suffix")), entries[0]
            )
            records = []
            options = {}
            suffixes = set()
            for old in [parent] + [e for e in entries if e.entry_id != parent.entry_id]:
                data = dict(old.data)
                device = get_device(dr.async_get(hass), data["charger_device"])
                name = (
                    (device.name_by_user or device.name)
                    if device
                    else old.title.removeprefix("Smart Load Manager OJM – ")
                )
                suffix = slugify(name) or "charger"
                if suffix in suffixes:
                    suffix += "_" + data["charger_device"][:6]
                suffixes.add(suffix)
                data["previous_entity_suffix"] = data.get("entity_suffix", "")
                data["entity_suffix"] = suffix
                data["charger_name"] = name
                records.append({"id": old.entry_id, "title": old.title, "data": data})
                options[old.entry_id] = dict(old.options)
            household = {
                k: parent.data[k]
                for k in ("han_power_entity", "tariff_used_entity", "safety_margin_kwh")
                if k in parent.data
            }
            hass.config_entries.async_update_entry(
                parent,
                data={"loads": records, "household": household},
                options={
                    "loads": options,
                    "site": {
                        k: v
                        for k, v in parent.options.items()
                        if k
                        in {
                            "consumption_limit_kwh",
                            "allocation_mode",
                            "priority_charger",
                        }
                    },
                },
                title="Smart Load Manager OJM",
                version=2,
            )
        ensure_groups(hass, parent)
        ids = {r["id"] for r in parent.data["loads"]}
        registry = er.async_get(hass)
        devices = dr.async_get(hass)
        for entity in list(registry.entities.values()):
            if entity.platform != DOMAIN or entity.config_entry_id not in ids:
                continue
            shared = entity.unique_id.endswith(
                (
                    "_household_status",
                    "_measurement_status",
                    "_consumption_limit",
                    "_allocation_mode",
                    "_priority_charger",
                )
            )
            kind = "household" if shared else "charging"
            registry.async_update_entity(
                entity.entity_id,
                config_entry_id=parent.entry_id,
                config_subentry_id=group_id(parent, kind),
            )
            if entity.device_id:
                if hasattr(dr, "async_setup"):
                    devices.async_update_device(
                        entity.device_id,
                        new_config_entry_id=parent.entry_id,
                        new_config_subentry_id=group_id(parent, kind),
                    )
                else:
                    devices.async_update_device(
                        entity.device_id,
                        add_config_entry_id=parent.entry_id,
                        add_config_subentry_id=group_id(parent, kind),
                    )
        if not hasattr(dr, "async_setup"):
            for device in list(
                dr.async_entries_for_config_entry(devices, parent.entry_id)
            ):
                bindings = device.config_entries_subentries.get(parent.entry_id, set())
                if None in bindings and len(bindings) > 1:
                    devices.async_update_device(
                        device.id,
                        remove_config_entry_id=parent.entry_id,
                        remove_config_subentry_id=None,
                    )
        # Entity ownership is moved before removing redundant config entries.
        # All their settings/identities are already durably saved in parent.
        for old in entries:
            if old.entry_id != parent.entry_id and old.entry_id in ids:
                for device in list(
                    dr.async_entries_for_config_entry(devices, old.entry_id)
                ):
                    if old.entry_id in device.config_entries:
                        devices.async_update_device(
                            device.id, remove_config_entry_id=old.entry_id
                        )
                await hass.config_entries.async_remove(old.entry_id)
        return True


async def async_setup_entry(hass, entry):
    from homeassistant.exceptions import ConfigEntryNotReady
    from .coordinator import ChargingCoordinator
    from .site import get_site
    from .entity_ids import migrate_entity_ids

    if "loads" not in entry.data:
        # A concurrent legacy setup may finish after consolidation removed it.
        return True
    ensure_groups(hass, entry)
    from .installation import reconcile_pair_entities

    reconcile_pair_entities(hass, entry)
    loads = platform_loads(entry)
    from .budget import consumption_limit_value

    if "consumption_limit_kwh" not in entry.options.get("site", {}):
        hass.config_entries.async_update_entry(
            entry,
            options={
                **entry.options,
                "site": {
                    **entry.options.get("site", {}),
                    "consumption_limit_kwh": consumption_limit_value(loads[0]),
                },
            },
        )
    controllers = {}
    try:
        for load in loads:
            controllers[load.entry_id] = ChargingCoordinator(hass, load)
        entry.runtime_data = SimpleNamespace(controllers=controllers)
        for load in loads:
            migrate_entity_ids(hass, load)
            await controllers[load.entry_id].async_config_entry_first_refresh()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception as err:
        site = get_site(hass)
        for key, controller in controllers.items():
            await controller.async_shutdown()
            if site.controllers.get(key) is controller:
                site.controllers.pop(key, None)
            site.pending_reductions.pop(key, None)
            site.manual_requests.pop(key, None)
            site.latest_samples.pop(key, None)
            site._permissions.pop(key, None)
            site._completed_limits.pop(key, None)
        raise ConfigEntryNotReady(str(err)) from err
    from .dashboard import async_register_dashboard_service

    await async_register_dashboard_service(hass)
    return True


async def async_unload_entry(hass, entry):
    runtime = getattr(entry, "runtime_data", None)
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        from .site import get_site

        site = get_site(hass)
        # entry.data already contains the new membership at reload time.
        # Tear down the actual old runtime, including any removed load.
        for key, controller in getattr(runtime, "controllers", {}).items():
            await controller.async_shutdown()
            if site.controllers.get(key) is controller:
                site.controllers.pop(key, None)
            site.pending_reductions.pop(key, None)
            site.manual_requests.pop(key, None)
            site.latest_samples.pop(key, None)
            site._permissions.pop(key, None)
            site._completed_limits.pop(key, None)
    return unloaded
