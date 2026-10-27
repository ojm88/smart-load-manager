"""Stable, short Home Assistant entity IDs for Smart Load Manager."""

from __future__ import annotations

from .const import DOMAIN

SENSOR_OBJECT_IDS = {
    "charging_role": "slm_charging_role",
    "household_status": "slm_status",
    "measurement_status": "slm_measurement_status",
    "phase_advice": "slm_phase_advice",
    "status": "slm_charger_status",
    "phase_mode": "slm_charger_phase_mode",
    "output_phase": "slm_output_phase",
    "active_phases": "slm_active_phases",
    "grid_type": "slm_grid_type",
    "voltage_type": "slm_voltage_system",
    "line_voltage": "slm_line_voltage",
    "ln_voltage": "slm_phase_neutral_voltage",
    "minimum_current": "slm_min_current",
    "recommended_current": "slm_recommended_current",
    "max_current": "slm_max_current",
    "charger_current": "slm_charger_current",
    "charger_power": "slm_charger_power",
    "han_power": "slm_home_power",
    "energy_used": "slm_energy_used_hour",
    "energy_estimate": "slm_energy_estimate_hour",
    "confidence": "slm_detection_confidence",
    "reason": "slm_phase_detection_reason",
    "control_reason": "slm_control_reason",
    "manual_control_status": "slm_manual_control_status",
    "no_current_reason": "slm_charger_pause_reason",
    "auto_control": "slm_auto_control_status",
    "han_age": "slm_meter_age",
    "han_fresh": "slm_meter_valid",
    "schedule_enabled": "slm_schedule_active",
    "schedule_reason": "slm_schedule_status",
}

ENTITY_OBJECT_IDS = {
    "sensor": SENSOR_OBJECT_IDS,
    "number": {"manual_current_limit": "slm_manual_current"},
    "switch": {
        "charging_priority": "slm_priority",
        "automatic_control": "slm_auto_control",
        "charging_pause": "slm_charging_pause",
        "schedule_control": "slm_schedule",
    },
    "time": {"schedule_start_time": "slm_charge_start"},
    "select": {
        "consumption_limit": "smart_load_manager_ojm_easee_forbruksgrense",
        "phase_mode_control": "slm_phase_mode",
        "allocation_mode": "slm_charging_mode",
        "priority_charger": "slm_priority_charger",
    },
}


def suggested_entity_id(domain: str, translation_key: str, entry=None) -> str:
    """Return the stable object ID for an integration entity."""
    object_id = ENTITY_OBJECT_IDS.get(domain, {}).get(translation_key)
    if object_id is None:
        raise KeyError(f"No stable entity ID for {domain}.{translation_key}")
    shared = (domain, translation_key) in {
        ("sensor", "household_status"), ("sensor", "measurement_status"),
        ("select", "consumption_limit"), ("select", "allocation_mode"), ("select", "priority_charger"),
    }
    suffix = "" if shared else getattr(entry, "data", {}).get("entity_suffix", "")
    return f"{object_id}_{suffix}" if suffix else object_id


def migrate_entity_ids(hass, entry) -> None:
    """Rename existing registry entities while preserving their unique IDs."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for entity in list(registry.entities.values()):
        if entity.platform != DOMAIN or entity.config_entry_id != getattr(getattr(entry, "parent", None), "entry_id", entry.entry_id):
            continue
        unique_prefix = f"{entry.entry_id}_"
        if not entity.unique_id.startswith(unique_prefix):
            continue
        translation_key = entity.unique_id[len(unique_prefix) :]
        object_id = ENTITY_OBJECT_IDS.get(entity.domain, {}).get(translation_key)
        if object_id is None:
            continue
        target_entity_id = f"{entity.domain}.{suggested_entity_id(entity.domain, translation_key, entry)}"
        if entity.entity_id == target_entity_id:
            continue
        # Exact old generated IDs only. A user rename is never inferred from
        # a broad prefix; unique IDs/history stay unchanged.
        previous = entry.data.get("previous_entity_suffix", "")
        old_object = f"{object_id}_{previous}" if previous else object_id
        generated = {f"{entity.domain}.{old_object}"}
        if entity.entity_id not in generated:
            continue
        if entity.name is not None:
            continue
        collision = registry.entities.get(target_entity_id)
        if collision is not None and collision.unique_id != entity.unique_id:
            # Never take over an entity belonging to the user's existing setup.
            continue
        mapping = hass.data.setdefault(DOMAIN, {}).setdefault("entity_id_migrations", {})
        mapping[entity.entity_id] = target_entity_id
        parent = getattr(entry, "parent", None)
        if parent is not None:
            saved = {**parent.options.get("entity_id_migrations", {}), **mapping}
            hass.config_entries.async_update_entry(parent, options={**parent.options, "entity_id_migrations": saved})
        registry.async_update_entity(entity.entity_id, new_entity_id=target_entity_id)
