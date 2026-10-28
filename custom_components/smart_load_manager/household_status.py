"""Presentation of all controlled loads; never sends commands or allocates power.

Future load adapters contribute rows here. Dashboard Markdown reads this single
household description contract rather than implementing a second control model.
"""
from __future__ import annotations


def build_household_status(loads, *, limit_kwh, mode="both", priority=None, norwegian=True):
    """Describe already calculated decisions in plain language, without mutation."""
    def tr(nb, en):
        return nb if norwegian else en

    names = {load["id"]: load["name"] for load in loads}
    priority_name = names.get(priority)
    rows = []
    any_advice = False
    for load in loads:
        data = load.get("data") or {}
        status = str(data.get("status", "unknown")).lower().replace(" ", "_")
        automatic = bool(data.get("auto_control"))
        paused = bool(data.get("charging_paused"))
        recommended = data.get("recommended_current_a")
        ready = bool(data and data.get("inputs_valid") and data.get("han_fresh")
                     and data.get("site_control_ready", True) and load.get("available", True))
        stage = "waiting"
        if not data or not load.get("available", True):
            explanation = tr("Opplysninger fra laderen mangler. Status kan ikke bekreftes.",
                             "Charger information is missing. Its status cannot be confirmed.")
        elif data.get("electrical_ready") is False:
            explanation = (str(data.get("electrical_error")) if norwegian else
                           "Confirm the physical connection under Configure → Chargers and check Easee voltage measurements.")
        elif paused:
            stage = "paused"
            explanation = tr("Ladingen er satt på pause. Slå av ladepause for å fortsette.",
                             "Charging is paused. Turn off charging pause to continue.")
        elif status == "disconnected":
            stage = "disconnected"
            explanation = tr("Bilen er ikke koblet til laderen.", "The car is not connected.")
        elif status in {"completed", "charged"}:
            stage = "completed"
            explanation = tr("Bilen har avsluttet ladingen.", "The car has stopped requesting charging.")
        elif automatic and not ready:
            explanation = tr("Laststyringen venter på gyldige målinger før ladingen kan reguleres.",
                             "Load control is waiting for valid measurements before adjusting charging.")
        elif automatic and not data.get("schedule_allowed", True):
            start = str(data.get("schedule_start_time", ""))[:5]
            explanation = (tr(f"Ladingen venter på valgt ladetid fra kl. {start}.",
                              f"Charging is waiting for its selected start time of {start}.") if start
                           else tr("Ladingen venter på valgt ladetid.", "Charging is waiting for its scheduled time."))
        elif not automatic:
            stage = "manual"
            explanation = tr("Automatisk laststyring er av. Laderen følger den sist satte strømgrensen.",
                             "Automatic load control is off. The charger follows its last current limit.")
        elif recommended is None or not data.get("kw_per_amp") or not data.get("max_current_a"):
            explanation = tr("Ladingen venter på opplysninger om hvor mye strøm laderen kan bruke.",
                             "Charging is waiting for information about the current the charger can use.")
        elif data.get("awaiting_reduction"):
            explanation = tr("Ladingen justeres. Mer strøm fordeles når reduksjonen er bekreftet.",
                             "Charging is being adjusted. More current is shared once the reduction is confirmed.")
        elif recommended <= 0:
            other_running = any((other.get("data") or {}).get("recommended_current_a", 0) or 0
                                for other in loads if other["id"] != load["id"])
            if priority_name and load["id"] != priority and other_running:
                explanation = (tr(f"{priority_name} får lade først. Denne laderen venter på tur.",
                                  f"{priority_name} charges first. This charger is waiting its turn.")
                               if mode == "one_at_a_time" else
                               tr(f"Det er bare plass til én lader nå. {priority_name} får lade først.",
                                  f"There is room for only one charger now. {priority_name} charges first."))
            else:
                explanation = tr("Ladingen venter for å holde boligen under valgt forbruksgrense.",
                                 "Charging is waiting to keep the home within its selected consumption limit.")
        else:
            stage = "automatic"
            explanation = tr("Ladestrømmen tilpasses slik at resten av boligen også har plass innenfor forbruksgrensen.",
                             "Charging current is adjusted to leave room for the rest of the home within the consumption limit.")
            if status != "charging":
                explanation = tr("Det er satt av strøm til lading, men bilen har ikke startet å lade.",
                                 "Current is available for charging, but the car has not started charging.")
        advice = str(data.get("phase_advice", ""))
        any_advice |= advice.startswith("Enfase på begge")
        rows.append({
            "id": load["id"], "name": load["name"], "load_type": load.get("load_type", "ev_charger"),
            "stage": stage, "status": status, "explanation": explanation,
            "automatic_control": automatic, "paused": paused,
            "first_priority": load["id"] == priority if len(loads) > 1 else None,
            "current_a": data.get("charger_current_a"),
            "power_w": data.get("charger_power_w"),
            "recommended_current_a": recommended,
            "minimum_current_a": data.get("control_minimum_current_a"),
            "maximum_current_a": data.get("max_current_a"),
            "schedule_enabled": bool(data.get("schedule_enabled")),
            "schedule_start": data.get("schedule_start_time"),
            "schedule_allowed": data.get("schedule_allowed"),
            "measurements_ready": ready,
            "easee_reason": data.get("electrical", {}).get("no_current_reason"),
            "control_detail": data.get("control_reason"),
        })
    stages = {row["stage"] for row in rows}
    if not rows or "waiting" in stages:
        state = "waiting"
        summary = tr("En eller flere ladere venter. Årsaken står ved hver lader nedenfor.",
                     "One or more chargers are waiting. Each charger's reason is shown below.")
    elif len(stages) == 1:
        state = next(iter(stages))
        summary = {
            "automatic": tr("Ladingen tilpasses boligens ledige kapasitet.", "Charging follows the home's available capacity."),
            "manual": tr("Automatisk laststyring er av.", "Automatic load control is off."),
            "paused": tr("Ladingen er satt på pause.", "Charging is paused."),
            "disconnected": tr("Ingen bil er koblet til laderne.", "No car is connected to the chargers."),
            "completed": tr("Bilene har avsluttet ladingen.", "The cars have stopped requesting charging."),
        }[state]
    else:
        state = "mixed"
        summary = tr("Laderne har ulik status. Se forklaringen ved hver lader nedenfor.",
                     "The chargers have different states. See each charger's explanation below.")
    distribution = ""
    if len(rows) > 1:
        distribution = (tr("Begge deler ledig ladekapasitet. Er det bare plass til én, får den prioriterte laderen lade først.",
                           "Both share available charging capacity. If only one fits, the priority charger goes first.")
                        if mode == "both" else
                        tr("Én lader om gangen. Den prioriterte laderen får lade først. Den andre kan lade når den første er ferdig, frakoblet, pauset eller utenfor sin ladetid.",
                           "One charger at a time. The priority charger goes first. The other may charge when the first has finished, is disconnected, paused or outside its schedule."))
        distribution += " " + tr("Fordelingen gjelder ladere med automatisk laststyring på.",
                                  "Sharing applies to chargers with automatic load control enabled.")
    advice = tr("Enfase på begge laderne kan gi plass til at begge lader samtidig. Fasevalg endres manuelt hvis bilene støtter det.",
                "Single phase on both chargers may allow both to charge together. Change phase mode manually if the cars support it.") if any_advice else ""
    return state, {"summary": summary, "consumption_limit_kwh": limit_kwh,
                   "charging_mode": mode if len(rows) > 1 else None,
                   "priority_charger": priority_name if len(rows) > 1 else None,
                   "distribution_explanation": distribution, "phase_advice": advice,
                   "controlled_loads": rows}
