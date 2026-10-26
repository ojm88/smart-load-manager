"""Resolve Easee sensor entities through the Home Assistant device registry."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


@dataclass(frozen=True, slots=True)
class EaseeEntities:
    status: str
    current: str
    voltage: str
    power: str | None
    current_limits: tuple[str, ...]


def resolve_easee_entities(hass: HomeAssistant, device_id: str) -> EaseeEntities:
    """Find status/current/voltage siblings without relying on entity IDs."""

    registry = er.async_get(hass)
    entries = [
        entry
        for entry in er.async_entries_for_device(registry, device_id)
        if entry.domain == "sensor" and entry.platform == "easee"
    ]
    states = {entry.entity_id: hass.states.get(entry.entity_id) for entry in entries}

    def has_attr(entity_id: str, prefix: str) -> bool:
        state = states[entity_id]
        return state is not None and any(
            key.startswith(prefix) for key in state.attributes
        )

    status = next(
        (entry.entity_id for entry in entries if has_attr(entry.entity_id, "state_outputPhase")),
        None,
    )
    current = next(
        (entry.entity_id for entry in entries if has_attr(entry.entity_id, "state_inCurrentT")),
        None,
    )
    voltage = next(
        (entry.entity_id for entry in entries if has_attr(entry.entity_id, "state_inVoltageT")),
        None,
    )
    power = next(
        (
            entry.entity_id
            for entry in entries
            if states[entry.entity_id]
            and states[entry.entity_id].attributes.get("device_class") == "power"
        ),
        None,
    )
    current_limits = tuple(
        entry.entity_id
        for entry in entries
        if states[entry.entity_id]
        and any(
            key in states[entry.entity_id].attributes
            for key in (
                "config_maxChargerCurrent",
                "config_circuitMaxCurrentP1",
                "config_circuitMaxCurrentP2",
                "config_circuitMaxCurrentP3",
                "circuit_ratedCurrent",
            )
        )
    )

    missing = [name for name, value in (("status", status), ("current", current), ("voltage", voltage)) if value is None]
    if missing:
        language = getattr(getattr(hass, "config", None), "language", "en")
        norwegian = language in {"nb", "nn", "no"}
        details = []
        for name in missing:
            candidates = [entry for entry in entries
                          if getattr(entry, "translation_key", None) == name]
            disabled = [entry.entity_id for entry in candidates
                        if getattr(entry, "disabled_by", None) is not None]
            if disabled:
                details.append(
                    ("Aktiver Easee-sensoren " if norwegian else "Enable the Easee sensor ")
                    + ", ".join(disabled)
                    + (" via Innstillinger → Enheter og tjenester → Easee → laderen → Entiteter. Vis deaktiverte entiteter. Vent til sensoren viser en målt verdi, og prøv igjen." if norwegian
                       else " via Settings → Devices & services → Easee → the charger → Entities. Include disabled entities. Wait for a measured value, then try again.")
                )
            else:
                labels = {"voltage": "spenning", "current": "strøm", "status": "status"}
                label = labels[name] if norwegian else name
                details.append(
                    (f"Mangler aktive Easee-data for {label}. Kontroller at sensoren er aktivert "
                     "og har oppdaterte verdier på den valgte laderen." if norwegian else
                     f"No active Easee {label} data. Check that the sensor is enabled "
                     "and has updated values on the selected charger.")
                )
        raise ValueError(" ".join(details))

    return EaseeEntities(
        status=status,
        current=current,
        voltage=voltage,
        power=power,
        current_limits=current_limits,
    )

