"""Stable, short Home Assistant entity IDs for Smart Load Manager."""

from __future__ import annotations

from .const import DOMAIN

SENSOR_OBJECT_IDS = {
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
        "automatic_control": "slm_auto_control",
        "schedule_control": "slm_schedule",
    },
    "time": {"schedule_start_time": "slm_charge_start"},
    "select": {
        "consumption_limit": "smart_load_manager_ojm_easee_forbruksgrense",
        "phase_mode_control": "slm_phase_mode",
    },
}


def suggested_entity_id(domain: str, translation_key: str) -> str:
    """Return the stable object ID for an integration entity."""
    object_id = ENTITY_OBJECT_IDS.get(domain, {}).get(translation_key)
    if object_id is None:
        raise KeyError(f"No stable entity ID for {domain}.{translation_key}")
    return object_id


def migrate_entity_ids(hass, entry) -> None:
    """Rename existing registry entities while preserving their unique IDs."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for entity in list(registry.entities.values()):
        if entity.platform != DOMAIN or entity.config_entry_id != entry.entry_id:
            continue
        unique_prefix = f"{entry.entry_id}_"
        if not entity.unique_id.startswith(unique_prefix):
            continue
        translation_key = entity.unique_id[len(unique_prefix) :]
        object_id = ENTITY_OBJECT_IDS.get(entity.domain, {}).get(translation_key)
        if object_id is None:
            continue
        target_entity_id = f"{entity.domain}.{object_id}"
        if entity.entity_id == target_entity_id:
            continue
        collision = registry.entities.get(target_entity_id)
        if collision is not None and collision.unique_id != entity.unique_id:
            # Never take over an entity belonging to the user's existing setup.
            continue
        registry.async_update_entity(
            entity.entity_id, new_entity_id=target_entity_id
        )
