"""Return a native Manual-card YAML using actual registered entity IDs."""
from .device_info import charger_display_name

from .installation import charger_entries, shared_identity
from pathlib import Path
import re
from homeassistant.core import SupportsResponse
from homeassistant.helpers import entity_registry as er, device_registry as dr
from .const import DOMAIN, CONF_HAN_POWER_ENTITY
from .entity_ids import ENTITY_OBJECT_IDS
from .site import site_entry


async def async_register_dashboard_service(hass):
    if hass.services.has_service(DOMAIN, "get_dashboard"):
        return

    async def get_dashboard(call):
        entries = charger_entries(hass)
        owner = site_entry(hass)
        others = [e for e in entries if e.entry_id != owner.entry_id]
        template = "two.yaml" if others else "one.yaml"
        path = Path(__file__).parent / "dashboard" / template
        text = await hass.async_add_executor_job(path.read_text)
        registry = er.async_get(hass)
        replacements = {
            "sensor.SLM_HAN_POWER_SOURCE": owner.data[CONF_HAN_POWER_ENTITY]
        }
        for entry in [owner] + others:
            if entry.data.get("electrical_connection") not in {"it_3", "tn_3"}:
                import yaml
                parsed = yaml.safe_load(text)
                suffix = "_CHARGER_SUFFIX" if entry.entry_id != owner.entry_id else "_FIRST_CHARGER_SUFFIX"
                target = "select.slm_phase_mode" + suffix
                for card in parsed.get("cards", []):
                    if "entities" in card:
                        card["entities"] = [row for row in card["entities"]
                                            if (row.get("entity") if isinstance(row, dict) else row) != target]
                text = yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False)
            second = entry.entry_id != owner.entry_id
            for domain, mapping in ENTITY_OBJECT_IDS.items():
                for key, base in mapping.items():
                    shared = key in {
                        "household_status",
                        "charging_automatic_control",
                        "measurement_status",
                        "consumption_limit",
                        "allocation_mode",
                        "priority_charger",
                    }
                    if second and shared:
                        continue
                    source = f"{domain}.{base}" + (
                        ""
                        if shared
                        else "_CHARGER_SUFFIX"
                        if second
                        else "_FIRST_CHARGER_SUFFIX"
                    )
                    identity = shared_identity(entry) if shared else entry.entry_id
                    actual = registry.async_get_entity_id(
                        domain, DOMAIN, f"{identity}_{key}"
                    )
                    if actual:
                        replacements[source] = actual
            if entry:
                name = charger_display_name(dr.async_get(hass), entry)
                label = "ny lader" if second else "første lader"
                # Avoid injecting device names into YAML source unescaped.
                import yaml

                # Headings are quoted by the YAML serializer below when needed.
                parsed = yaml.safe_load(text)
                for card in parsed.get("cards", []):
                    if "title" in card:
                        card["title"] = card["title"].replace(
                            label, name or entry.title
                        )
                    for row in card.get("entities", []):
                        if isinstance(row, dict) and "name" in row:
                            row["name"] = row["name"].replace(
                                label, name or entry.title
                            )
                text = yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False)
        if replacements:
            pattern = (
                r"(?<![\w.])("
                + "|".join(
                    re.escape(k) for k in sorted(replacements, key=len, reverse=True)
                )
                + r")(?!\w)"
            )
            text = re.sub(pattern, lambda match: replacements[match.group()], text)
        if "CHARGER_SUFFIX" in text:
            from homeassistant.exceptions import HomeAssistantError

            raise HomeAssistantError(
                "Charger entities are not all registered yet. Reload SLM and generate the card again."
            )
        return {"yaml": text}

    hass.services.async_register(
        DOMAIN, "get_dashboard", get_dashboard, supports_response=SupportsResponse.ONLY
    )
