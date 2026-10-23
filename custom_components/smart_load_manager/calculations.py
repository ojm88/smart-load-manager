"""Pure calculations for Smart Load Manager.

Keep electrical inference independent from Home Assistant entity handling so it
can be unit-tested from captured Easee attribute snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from math import isfinite, sqrt
from typing import Mapping


def schedule_window_active(
    now: datetime, start_text: str, duration_hours: int = 12
) -> tuple[bool, str]:
    """Check a daily wall-clock start and duration, including midnight wrap."""
    try:
        start_time = time.fromisoformat(start_text)
    except (TypeError, ValueError):
        return False, "Starttid mangler eller er ugyldig"
    local_now = now.replace(tzinfo=None, microsecond=0)
    stop_time = (datetime.combine(local_now.date(), start_time) + timedelta(hours=duration_hours)).time()
    for day_offset in (0, -1):
        start = datetime.combine(local_now.date() + timedelta(days=day_offset), start_time)
        if start <= local_now <= start + timedelta(hours=duration_hours):
            return True, f"Innenfor tidsvinduet {start_time.strftime('%H:%M')}–{stop_time.strftime('%H:%M')}"
    return False, f"Utenfor {duration_hours}-timersvinduet fra {start_time.strftime('%H:%M')}"


def han_measurement_is_fresh(age_seconds: float | None, power_w: float | None, max_age: int = 60) -> bool:
    """Require a positive meter reading updated within the allowed age."""
    return (
        age_seconds is not None
        and 0 <= age_seconds <= max_age
        and power_w is not None
        and isfinite(power_w)
        and power_w > 0
    )


@dataclass(frozen=True, slots=True)
class ElectricalSnapshot:
    """Normalized subset of Easee status/current/voltage data."""

    output_phase: int = 0
    phase_mode: int = 0
    grid_type_code: int = 0
    no_current_reason_code: int = 0
    status: str = "unknown"
    currents_a: Mapping[str, float] | None = None
    voltages_v: Mapping[str, float] | None = None


@dataclass(frozen=True, slots=True)
class ElectricalResult:
    """Detected supply characteristics for diagnostics and calculation."""

    configured_phases: int
    active_phases: int
    effective_phases: int
    voltage_type: str
    line_voltage_v: float | None
    phase_neutral_voltage_v: float | None
    confidence: str
    reason: str
    phase_mode_name: str
    output_phase_name: str
    grid_type_name: str
    no_current_reason: str
    minimum_current_a: int | None


_OUTPUT_PHASES = {
    10: 1,
    11: 1,
    12: 1,
    13: 1,
    14: 1,
    15: 1,
    20: 2,
    21: 2,
    22: 2,
    30: 3,
}

# Easee enum values are scoped to their own fields: the same integer may mean
# something entirely different in another enum. Keep each lookup separate.
PHASE_MODE_NAMES = {0: "Ikke rapportert", 1: "Låst til én fase", 2: "Automatisk", 3: "Låst til tre faser"}
OUTPUT_PHASE_NAMES = {
    0: "Ikke tildelt",
    10: "Én fase TN (N+L1)", 11: "Én fase IT (L1+L2)",
    12: "Én fase TN (N+L2)", 13: "Én fase IT (L1+L3)",
    14: "Én fase TN (N+L3)", 15: "Én fase IT (L2+L3)",
    20: "To faser TN (N+L1, N+L2)", 21: "To faser TN (N+L2, N+L3)",
    22: "To faser IT (L1+L2, L2+L3)",
    30: "Tre faser TN (N+L1, N+L2, N+L3)",
}
GRID_TYPE_NAMES = {
    1: "TN, tre faser", 2: "TN, to faser", 3: "TN, én fase",
    4: "IT, tre faser", 5: "IT, én fase",
    30: "Varsel: TN, to faser (pinnekonfigurasjon)",
    31: "Varsel: TN, én fase (nøytral på pinne 3)",
    32: "Varsel: IT, jordfeil på tre faser",
    33: "Varsel: IT, jordfeil på én fase",
    34: "Varsel: IT, jordfeil på tre faser (L3)",
    35: "Varsel: IT, jordfeil på én fase (L3)",
    36: "Varsel: TN, to faser (pinnekonfigurasjon)",
    37: "Varsel: TN, jordfeil på tre faser",
    38: "Varsel: TN, jordfeil på to faser",
    50: "Feil: fant ikke gyldig nettype",
    51: "Feil: TN 400 V-nøytral på feil pinne",
    52: "Feil: IT-jord koblet til pinne 2 eller 3",
}
NO_CURRENT_REASONS = {
    -1: "Ikke rapportert",
    0: "Laderen melder ingen begrensning",
    1: "Kursens maksimale strøm er for lav",
    2: "Dynamisk kursgrense fra ekstern laststyring er for lav",
    3: "Dynamisk offline-kursgrense er for lav",
    4: "Kursens sikringsgrense er for lav",
    5: "Venter i lastbalanseringskø",
    6: "Venter i kø etter fullført lading",
    7: "Feil ved automatisk deteksjon av nettype",
    8: "Mangler strømforespørsel fra sekundærenhet/bil",
    9: "Kommunikasjon med master er tapt",
    10: "Equalizer har gitt for lav strømgrense",
    11: "Ingen strøm: fase er ikke tilkoblet",
    25: "Begrenset av kurssikring", 26: "Begrenset av kursens maksgrense",
    27: "Begrenset av dynamisk kursgrense", 28: "Begrenset av Equalizer",
    29: "Begrenset av lastbalansering på kurs", 30: "Begrenset av offline-innstilling",
    50: "Sekundærlader ber ikke om strøm", 51: "Laderens maksgrense er for lav",
    52: "Laderens dynamiske maksgrense er for lav", 53: "Lader er deaktivert",
    54: "Venter på planlagt lading", 55: "Venter på autorisering",
    56: "Laderen er i feiltilstand", 57: "Uregelmessig respons fra bilen",
    75: "Begrenset av ladekabel", 76: "Begrenset av ladeplan",
    77: "Begrenset av laderens maksstrøm", 78: "Begrenset av dynamisk ladergrense",
    79: "Bilen lader ikke", 80: "Midlertidig lokal strømjustering",
    81: "Begrenset av bilen", 100: "Udefinert Easee-feil",
}


def _valid_values(values: Mapping[str, float] | None) -> dict[str, float]:
    if not values:
        return {}
    valid: dict[str, float] = {}
    for key, raw_value in values.items():
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if isfinite(value) and 0 < value < 1000:
            valid[key] = value
    return valid


def detect_electrical_setup(snapshot: ElectricalSnapshot) -> ElectricalResult:
    """Infer phase count and nominal voltage without assuming a fixed supply.

    Easee terminal measurements use T2 as neutral on TN installations and T3-T5
    as phase conductors. Explicit phase-to-phase measurements are preferred;
    on TN, line voltage can be inferred as sqrt(3) times measured L-N voltage.
    """

    currents = _valid_values(snapshot.currents_a)
    voltages = _valid_values(snapshot.voltages_v)
    configured = _OUTPUT_PHASES.get(int(snapshot.output_phase), 0)
    if configured == 0:
        # When Easee has not assigned an output phase yet, use its reported
        # grid topology or a fixed one-/three-phase mode if available.
        configured = {
            1: 1,
            3: 3,
        }.get(int(snapshot.phase_mode), {
            1: 3, 2: 2, 3: 1, 4: 3, 5: 1
        }.get(int(snapshot.grid_type_code), 0))

    # T2 is neutral for the Easee attributes used in TN installations.
    phase_currents = {
        key: value
        for key, value in currents.items()
        if key in {"T3", "T4", "T5"} and value >= 1.0
    }
    active = len(phase_currents)
    effective = (
        active
        if snapshot.status.lower() == "charging" and active
        else configured
    )

    ll_values = [
        value
        for key, value in voltages.items()
        if key in {"T3T4", "T3T5", "T4T5", "T1T3", "T1T4", "T1T5"}
    ]
    ln_values = [
        value
        for key, value in voltages.items()
        if key in {"T2T3", "T2T4", "T2T5"}
    ]

    # Pair readings above 350 V identify a 400 V class supply directly.
    high_ll = [value for value in ll_values if value >= 350]
    low_ll = [value for value in ll_values if 180 <= value < 300]
    if high_ll:
        line_v = sum(high_ll) / len(high_ll)
        ln_v = (sum(ln_values) / len(ln_values)) if ln_values else line_v / sqrt(3)
        voltage_type = "400V"
        confidence = "high"
        reason = "Målt linjespenning mellom faselederne"
    elif low_ll:
        line_v = sum(low_ll) / len(low_ll)
        ln_v = None
        voltage_type = "230V"
        confidence = "high"
        reason = "Målt omtrent 230 V mellom aktive faseledere"
    elif ln_values and effective == 0:
        return ElectricalResult(
            configured_phases=configured,
            active_phases=active,
            effective_phases=effective,
            voltage_type="unknown",
            line_voltage_v=None,
            phase_neutral_voltage_v=None,
            confidence="none",
            reason="Fasespenningsmålinger finnes, men faseoppsettet er ikke kjent",
            phase_mode_name=PHASE_MODE_NAMES.get(snapshot.phase_mode, f"Ukjent ({snapshot.phase_mode})"),
            output_phase_name=OUTPUT_PHASE_NAMES.get(snapshot.output_phase, f"Ukjent ({snapshot.output_phase})"),
            grid_type_name=GRID_TYPE_NAMES.get(snapshot.grid_type_code, f"Ikke rapportert ({snapshot.grid_type_code})"),
            no_current_reason=NO_CURRENT_REASONS.get(snapshot.no_current_reason_code, f"Ukjent Easee-kode ({snapshot.no_current_reason_code})"),
            minimum_current_a=None,
        )
    elif ln_values:
        ln_v = sum(ln_values) / len(ln_values)
        if effective >= 2:
            line_v = ln_v * sqrt(3)
            voltage_type = "400V"
            confidence = "medium"
            reason = "230 V klasse fase-nøytral; linjespenning utledet med √3"
        else:
            line_v = ln_v
            voltage_type = "230V"
            confidence = "medium"
            reason = "Målt fase-nøytral spenning på én aktiv fase"
    else:
        return ElectricalResult(
            configured_phases=configured,
            active_phases=active,
            effective_phases=effective,
            voltage_type="unknown",
            line_voltage_v=None,
            phase_neutral_voltage_v=None,
            confidence="none",
            reason="Mangler gyldige Easee-spenningsmålinger",
            phase_mode_name=PHASE_MODE_NAMES.get(snapshot.phase_mode, f"Ukjent ({snapshot.phase_mode})"),
            output_phase_name=OUTPUT_PHASE_NAMES.get(snapshot.output_phase, f"Ukjent ({snapshot.output_phase})"),
            grid_type_name=GRID_TYPE_NAMES.get(snapshot.grid_type_code, f"Ikke rapportert ({snapshot.grid_type_code})"),
            no_current_reason=NO_CURRENT_REASONS.get(snapshot.no_current_reason_code, f"Ukjent Easee-kode ({snapshot.no_current_reason_code})"),
            minimum_current_a=_minimum_current(
                voltage_type="unknown", active_phases=active,
                effective_phases=effective,
                charging=snapshot.status.lower() == "charging",
            ),
        )

    return ElectricalResult(
        configured_phases=configured,
        active_phases=active,
        effective_phases=effective,
        voltage_type=voltage_type,
        line_voltage_v=round(line_v, 1),
        phase_neutral_voltage_v=round(ln_v, 1) if ln_v is not None else None,
        confidence=confidence,
        reason=reason,
        phase_mode_name=PHASE_MODE_NAMES.get(snapshot.phase_mode, f"Ukjent ({snapshot.phase_mode})"),
        output_phase_name=OUTPUT_PHASE_NAMES.get(snapshot.output_phase, f"Ukjent ({snapshot.output_phase})"),
        grid_type_name=GRID_TYPE_NAMES.get(snapshot.grid_type_code, f"Ikke rapportert ({snapshot.grid_type_code})"),
        no_current_reason=NO_CURRENT_REASONS.get(snapshot.no_current_reason_code, f"Ukjent Easee-kode ({snapshot.no_current_reason_code})"),
        minimum_current_a=_minimum_current(
            voltage_type=voltage_type, active_phases=active,
            effective_phases=effective,
            charging=snapshot.status.lower() == "charging",
        ),
    )


def _minimum_current(
    voltage_type: str, active_phases: int, effective_phases: int, charging: bool
) -> int | None:
    """Use measured phases while charging, output-phase config while paused."""
    phase_count = active_phases if charging else effective_phases
    if phase_count not in {1, 2, 3} or voltage_type not in {"230V", "400V"}:
        return None
    if voltage_type == "230V" and phase_count == 3:
        return 11
    return 6


def power_to_watts(value: float, unit: str) -> float:
    """Convert an instantaneous power value in W or kW to W."""

    numeric_value = float(value)
    if not isfinite(numeric_value):
        raise ValueError("Effektsensoren må gi en gyldig effektverdi")
    normalized_unit = unit.strip().lower()
    if normalized_unit == "w":
        return numeric_value
    if normalized_unit == "kw":
        return numeric_value * 1000
    raise ValueError(f"Effektsensor må være oppgitt i W eller kW, ikke {unit!r}")


def kw_per_ampere(result: ElectricalResult) -> float | None:
    """Return nominal charging kW per A for supported electrical setups."""

    if result.effective_phases == 1 and result.phase_neutral_voltage_v:
        return result.phase_neutral_voltage_v / 1000
    if result.effective_phases == 2 and result.line_voltage_v:
        # Two phases in a 400 V TN system use two phase-neutral conductors.
        if result.voltage_type == "400V" and result.phase_neutral_voltage_v:
            return 2 * result.phase_neutral_voltage_v / 1000
        # Easee IT two-phase output uses two 230 V line-pair charging paths.
        return 2 * result.line_voltage_v / 1000
    if result.effective_phases == 3 and result.line_voltage_v:
        return sqrt(3) * result.line_voltage_v / 1000
    return None


def recommended_current_a(
    *,
    hourly_limit_kwh: float,
    energy_used_kwh: float,
    han_power_w: float,
    charger_power_w: float,
    minutes_left: int,
    safety_margin_kwh: float,
    max_current_a: float,
    min_current_a: int | None,
    kw_per_amp: float | None,
) -> int | None:
    """Calculate a conservative current for the remainder of the current hour.

    The house-load estimate excludes the EVSE's measured power. Unknown phase,
    voltage, or minimum-current information returns None so automation cannot
    send a guessed value to the charger.
    """
    if (
        minutes_left <= 0
        or min_current_a is None
        or kw_per_amp is None
        or kw_per_amp <= 0
        or max_current_a <= 0
    ):
        return None
    house_kw = max(0.0, han_power_w - max(0.0, charger_power_w)) / 1000
    projected_house_kwh = house_kw * minutes_left / 60
    remaining_kwh = max(
        0.0,
        hourly_limit_kwh - energy_used_kwh - projected_house_kwh - safety_margin_kwh,
    )
    allowed_kw = remaining_kwh * 60 / minutes_left
    amp_limit = min(max_current_a, allowed_kw / kw_per_amp)
    result = int(amp_limit)
    if result < min_current_a:
        return 0
    return result
