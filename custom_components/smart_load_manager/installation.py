"""One installation with household and charging groups, preserving load identities."""

from __future__ import annotations
from types import MappingProxyType
from .const import DOMAIN


class LoadEntry:
    """A saved load identity; settings are persisted in its installation entry."""

    def __init__(self, parent, identity):
        self.parent = parent
        self.entry_id = identity
        self._saved_record = next(
            r for r in parent.data["loads"] if r["id"] == identity
        )

    @property
    def record(self):
        return next(
            (r for r in self.parent.data["loads"] if r["id"] == self.entry_id),
            self._saved_record,
        )

    @property
    def data(self):
        return {**self.record["data"], **self.parent.data.get("household", {})}

    @property
    def options(self):
        return {
            **self.parent.options.get("loads", {}).get(self.entry_id, {}),
            **self.parent.options.get("site", {}),
        }

    @property
    def title(self):
        return self.record["title"]

    @property
    def runtime_data(self):
        return self.parent.runtime_data.controllers[self.entry_id]


def charger_entries(hass):
    result = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if "loads" in entry.data:
            result.extend(LoadEntry(entry, r["id"]) for r in entry.data["loads"])
        else:
            result.append(entry)
    return result


def update_load(hass, entry, *, options=None, data=None):
    if not isinstance(entry, LoadEntry):
        kwargs = {}
        if options is not None:
            kwargs["options"] = options
        if data is not None:
            kwargs["data"] = data
        hass.config_entries.async_update_entry(entry, **kwargs)
        return
    parent = entry.parent
    if options is not None:
        saved = dict(parent.options.get("loads", {}))
        shared_keys = {"consumption_limit_kwh", "allocation_mode", "priority_charger"}
        site = {
            **parent.options.get("site", {}),
            **{k: v for k, v in options.items() if k in shared_keys},
        }
        saved[entry.entry_id] = {
            k: v for k, v in options.items() if k not in shared_keys
        }
        hass.config_entries.async_update_entry(
            parent, options={**parent.options, "loads": saved, "site": site}
        )
    if data is not None:
        records = [dict(r) for r in parent.data["loads"]]
        for record in records:
            if record["id"] == entry.entry_id:
                record["data"] = dict(data)
        hass.config_entries.async_update_entry(
            parent, data={**parent.data, "loads": records}
        )


def group_id(entry, kind):
    return next(
        s.subentry_id for s in entry.subentries.values() if s.subentry_type == kind
    )


def ensure_groups(hass, entry):
    from homeassistant.config_entries import ConfigSubentry

    nb = str(hass.config.language).startswith("nb")
    for kind, title in (
        ("household", "Boligen" if nb else "Household"),
        ("charging", "Lading" if nb else "Charging"),
    ):
        if not any(s.subentry_type == kind for s in entry.subentries.values()):
            hass.config_entries.async_add_subentry(
                entry,
                ConfigSubentry(
                    data=MappingProxyType({}),
                    subentry_type=kind,
                    title=title,
                    unique_id=kind,
                ),
            )


def add_grouped(hass, parent, add, entities, kind):
    """Use native HA subentries rather than invented device-page sections."""
    if "loads" in parent.data:
        add(entities, config_subentry_id=group_id(parent, kind))
    else:
        add(entities)


def platform_loads(entry):
    if "loads" in getattr(entry, "data", {}):
        return [LoadEntry(entry, r["id"]) for r in entry.data["loads"]]
    return [entry]


def reconcile_pair_entities(hass, parent):
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    pair = len(parent.data["loads"]) == 2
    keys = (
        "_charging_priority",
        "_charging_role",
        "_allocation_mode",
        "_priority_charger",
    )
    retained = {r["id"] for r in parent.data["loads"]}
    disabled = set(parent.options.get("lifecycle_disabled", []))
    for entity in er.async_entries_for_config_entry(registry, parent.entry_id):
        if entity.platform != DOMAIN or entity.config_entry_id != parent.entry_id:
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
        removed = not shared and not any(
            entity.unique_id.startswith(key + "_") for key in retained
        )
        should_disable = removed or (not pair and entity.unique_id.endswith(keys))
        if should_disable and entity.disabled_by is None:
            registry.async_update_entity(
                entity.entity_id, disabled_by=er.RegistryEntryDisabler.INTEGRATION
            )
            disabled.add(entity.unique_id)
        elif (
            not should_disable
            and entity.unique_id.endswith("_line_voltage")
            and entity.disabled_by == er.RegistryEntryDisabler.INTEGRATION
        ):
            # Voltage is a main measurement again. Restore the old diagnostic's
            # integration default, while preserving an explicit user disable.
            registry.async_update_entity(entity.entity_id, disabled_by=None)
            disabled.discard(entity.unique_id)
        elif not should_disable and entity.unique_id in disabled:
            if entity.disabled_by == er.RegistryEntryDisabler.INTEGRATION:
                registry.async_update_entity(entity.entity_id, disabled_by=None)
            disabled.discard(entity.unique_id)
    if disabled != set(parent.options.get("lifecycle_disabled", [])):
        hass.config_entries.async_update_entry(
            parent, options={**parent.options, "lifecycle_disabled": sorted(disabled)}
        )


def shared_identity(entry):
    return getattr(getattr(entry, "parent", None), "entry_id", entry.entry_id)
