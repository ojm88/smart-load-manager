"""Device boundary for settings shared by all present and future loads."""

from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN


def household_device_info():
    """Household identity is independent of charger identity and priority."""
    return DeviceInfo(
        identifiers={(DOMAIN, "household")},
        name="SLM – Boligen",
        manufacturer="Smart Load Manager OJM",
        model="Household load management",
    )


def charger_device_info(entry):
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=getattr(entry, "data", {}).get(
            "charger_name", entry.title.removeprefix("Smart Load Manager OJM – ")
        ),
        manufacturer="Smart Load Manager OJM",
        model="Easee charging control",
    )


def name_charger_entity(entity, entry, domain, key):
    """Full names put function before charger; registry user overrides win."""
    if key in {
        "household_status",
        "measurement_status",
        "consumption_limit",
        "allocation_mode",
        "priority_charger",
    }:
        return
    data = getattr(entry, "data", {})
    name = data.get("charger_name")
    if not name:
        return  # Pre-beta.5 mocks/entries without a saved name retain HA translation.
    language = (
        "nb" if str(entity.coordinator.hass.config.language).startswith("nb") else "en"
    )
    label = ENTITY_LABELS[language][domain][key]["name"]
    entity._attr_name = f"{label} {name}"
    entity._attr_has_entity_name = False


# Tiny packaged translation tables, loaded once outside the event loop.
import json
from pathlib import Path

ENTITY_LABELS = {
    language: json.loads(
        (Path(__file__).parent / "translations" / f"{language}.json").read_text()
    )["entity"]
    for language in ("nb", "en")
}


def get_device(registry, device_id):
    """Use the supported indexed lookup; tolerate lightweight legacy test doubles."""
    if hasattr(registry, "async_get"):
        return registry.async_get(device_id)
    return registry.devices.get(device_id)


class ChargerNameMixin:
    """Keep deliberate full charger names on HA versions that compose device names."""

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        from homeassistant.helpers import entity_registry as er

        # HA's new legacy-friendly-name builder otherwise prepends the device
        # to an already complete function-first name. A user override wins.
        if (
            hasattr(er, "async_get_legacy_friendly_name")
            and getattr(self, "_attr_has_entity_name", True) is False
            and getattr(self, "_attr_name", None)
        ):
            registry = er.async_get(self.hass)
            registered = registry.async_get(self.entity_id)
            if registered is not None and registered.name is None:
                registry.async_update_entity(self.entity_id, name=self._attr_name)
