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
    connection: str | None = None


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
    charging_kw_per_amp: float | None = None
    connection: str | None = None


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
    """Use confirmed wiring to interpret terminal measurements, never their maximum.

    Standard Easee wiring: TN T2=N and T3/T4/T5=L1/L2/L3;
    IT/TT 230 V T2/T3/T4 are phase conductors (T5 is unused).
    The configured connection is required; phase mode cannot establish wiring.
    """
    connection = snapshot.connection
    tn = connection in {"tn_1", "tn_3"}
    supported = connection in {"it_1", "it_3", "tn_1", "tn_3"}
    supply_phases = 3 if connection in {"it_3", "tn_3"} else 1
    currents = _valid_values(snapshot.currents_a)
    voltages = _valid_values(snapshot.voltages_v)
    output = int(snapshot.output_phase)
    mode = int(snapshot.phase_mode)
    charging = snapshot.status.lower() == "charging"
    if not supported:
        configured = 0
    elif mode == 1:
        configured = 1
    elif mode == 3:
        configured = supply_phases
    else:
        configured = _OUTPUT_PHASES.get(output, supply_phases)
    active_terminals = {key for key, value in currents.items() if value >= 1}
    phase_terminals = {"T3", "T4", "T5"} if tn else {"T2", "T3", "T4"}
    count = len(active_terminals & phase_terminals)
    # In IT, one charging path draws current in TWO phase conductors.
    active = count if tn else (3 if count == 3 else 1 if count == 2 else 0)
    effective = active if charging and active else configured
    voltage_type = "400V" if tn else "230V"

    def result(reason, *, line=None, neutral=None, factor=None):
        valid = factor is not None and effective in {1, 2, 3}
        return ElectricalResult(
            configured_phases=configured, active_phases=active,
            effective_phases=effective, voltage_type=voltage_type if supported else "unknown",
            line_voltage_v=round(line, 1) if line is not None else None,
            phase_neutral_voltage_v=round(neutral, 1) if neutral is not None else None,
            confidence="configured_measured" if valid else "none", reason=reason,
            phase_mode_name=PHASE_MODE_NAMES.get(mode, f"Ukjent ({mode})"),
            output_phase_name=OUTPUT_PHASE_NAMES.get(output, f"Ukjent ({output})"),
            grid_type_name=GRID_TYPE_NAMES.get(snapshot.grid_type_code, f"Ikke rapportert ({snapshot.grid_type_code})"),
            no_current_reason=NO_CURRENT_REASONS.get(snapshot.no_current_reason_code, f"Ukjent Easee-kode ({snapshot.no_current_reason_code})"),
            minimum_current_a=_minimum_current(voltage_type, active, effective, charging) if valid else None,
            charging_kw_per_amp=factor if valid else None, connection=connection,
        )

    if not supported:
        return result("Bekreft laderens fysiske tilkobling under Konfigurer → Ladere")
    expected_grids = {"tn_1": {3}, "tn_3": {1}, "it_1": {5}, "it_3": {4}}[connection]
    grid = snapshot.grid_type_code
    if grid and grid not in expected_grids:
        return result("Easees rapporterte nettype avviker fra bekreftet tilkobling")
    tn_outputs = {10, 12, 14, 20, 21, 30}
    it_outputs = {11, 13, 15, 22}
    if output and output not in (tn_outputs if tn else it_outputs):
        return result("Easees utgangskobling avviker fra bekreftet tilkobling")
    if supply_phases == 1 and (mode == 3 or _OUTPUT_PHASES.get(output, 0) > 1):
        return result("Easee melder flerfasemodus på en bekreftet énfasetilkobling")
    if charging and (active_terminals - phase_terminals - ({"T2"} if tn else set())):
        return result("Målt strøm på terminal utenfor bekreftet tilkobling")
    if supply_phases == 1 and active > 1:
        return result("Målt fasebruk avviker fra bekreftet énfasetilkobling")
    if not tn and charging and count == 1:
        return result("Mangler sammenhengende strømmålinger fra IT-faselederne")

    def measured(pair):
        value = voltages.get(pair)
        return value if value is not None and 180 <= value <= 300 else None

    if tn:
        phases = ["T3", "T4", "T5"] if supply_phases == 3 else ["T3"]
        # Use actual active phase voltages during charging. Before assignment,
        # reserve the highest possible phase voltage for one-/two-phase starts.
        if charging and active:
            phases = [key for key in phases if key in active_terminals]
        elif effective == 1 and output in {10, 12, 14}:
            phases = [{10: "T3", 12: "T4", 14: "T5"}[output]]
        elif effective == 2 and output in {20, 21}:
            phases = ["T3", "T4"] if output == 20 else ["T4", "T5"]
        if any(key not in ({"T3", "T4", "T5"} if supply_phases == 3 else {"T3"}) for key in phases):
            return result("Tildelt Easee-fase finnes ikke i bekreftet tilkobling")
        values = [measured("T2" + key) for key in phases]
        if not values or any(value is None for value in values):
            return result("Mangler gyldig målt TN-spenning på nødvendige terminalpar")
        selected = sorted(values, reverse=True)[:effective]
        neutral = sum(selected) / len(selected)
        # Supply class stays TN even when only one phase is used by the car.
        line = neutral * sqrt(3)
        factor = sum(selected) / 1000
        return result("Bekreftet TN-tilkobling; målt fase–nøytral spenning", line=line,
                      neutral=neutral, factor=factor)

    pairs = ["T2T3", "T2T4", "T3T4"] if supply_phases == 3 else ["T2T3"]
    single_pairs = {11: "T2T3", 13: "T2T4", 15: "T3T4"}
    if effective == 1:
        if charging and count == 2:
            pairs = ["".join(sorted(active_terminals & phase_terminals))]
        elif output in single_pairs:
            pairs = [single_pairs[output]]
        if supply_phases == 1 and pairs != ["T2T3"]:
            return result("Tildelt Easee-fase finnes ikke i bekreftet tilkobling")
    values = [measured(pair) for pair in pairs]
    if not values or any(value is None for value in values):
        return result("Mangler gyldig målt IT/TT-spenning på nødvendige terminalpar")
    # Highest relevant measured voltage avoids granting too many amperes on
    # an unassigned path or uneven supply. No nominal 230 V is substituted.
    line = max(values)
    factor = (sqrt(3) if effective == 3 else effective) * line / 1000
    return result("Bekreftet IT/TT-tilkobling; målt spenning mellom faseledere",
                  line=line, factor=factor)


def _minimum_current(
    voltage_type: str, active_phases: int, effective_phases: int, charging: bool
) -> int | None:
    """Use measured phase use, or validated configuration before current rises.

    Easee can report charging before its separate current sensor updates. Zero
    measured phases does not invalidate confirmed wiring and measured voltage.
    The caller only exposes this minimum after validating that electrical path.
    """
    phase_count = active_phases if charging and active_phases else effective_phases
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
    """Return kW/A only from a validated connection and measured voltage."""
    return result.charging_kw_per_amp


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
