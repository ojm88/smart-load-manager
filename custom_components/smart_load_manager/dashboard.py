"""Return a native Manual-card YAML using actual registered entity IDs."""
from pathlib import Path
import re
from homeassistant.core import SupportsResponse
from homeassistant.helpers import entity_registry as er, device_registry as dr
from .const import DOMAIN
from .entity_ids import ENTITY_OBJECT_IDS
from .site import site_entry


async def async_register_dashboard_service(hass):
    if hass.services.has_service(DOMAIN, "get_dashboard"):
        return

    async def get_dashboard(call):
        entries = hass.config_entries.async_entries(DOMAIN)
        owner = site_entry(hass)
        others = [e for e in entries if e.entry_id != owner.entry_id]
        template = "two.yaml" if others else "one.yaml"
        path = Path(__file__).parent / "dashboard" / template
        text = await hass.async_add_executor_job(path.read_text)
        registry = er.async_get(hass)
        replacements = {}
        for entry in [owner] + others:
            second = entry.entry_id != owner.entry_id
            for domain, mapping in ENTITY_OBJECT_IDS.items():
                for key, base in mapping.items():
                    source = f"{domain}.{base}" + ("_CHARGER_SUFFIX" if second else "")
                    actual = registry.async_get_entity_id(domain, DOMAIN, f"{entry.entry_id}_{key}")
                    if actual:
                        replacements[source] = actual
            if entry:
                device = dr.async_get(hass).devices.get(entry.data["charger_device"])
                name = (device.name_by_user or device.name) if device else entry.title
                label = "ny lader" if second else "første lader"
                # Avoid injecting device names into YAML source unescaped.
                import yaml
                # Headings are quoted by the YAML serializer below when needed.
                parsed = yaml.safe_load(text)
                for card in parsed.get("cards", []):
                    if "title" in card:
                        card["title"] = card["title"].replace(label, name or entry.title)
                    for row in card.get("entities", []):
                        if isinstance(row, dict) and "name" in row:
                            row["name"] = row["name"].replace(label, name or entry.title)
                text = yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False)
        if replacements:
            pattern = r"(?<![\w.])(" + "|".join(re.escape(k) for k in sorted(replacements, key=len, reverse=True)) + r")(?!\w)"
            text = re.sub(pattern, lambda match: replacements[match.group()], text)
        # Jinja constructs the second ID dynamically inside the Markdown.
        if others:
            suffix = others[0].data.get("entity_suffix", "")
            text = text.replace("CHARGER_SUFFIX", suffix)
        text = text.replace("# Replace " + (others[0].data.get("entity_suffix", "") if others else "CHARGER_SUFFIX") + " with card_suffix from the new charger's Phase advice sensor.\n", "")
        return {"yaml": text}

    hass.services.async_register(DOMAIN, "get_dashboard", get_dashboard,
                                 supports_response=SupportsResponse.ONLY)
