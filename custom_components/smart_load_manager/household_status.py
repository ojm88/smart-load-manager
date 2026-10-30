"""Presentation of all controlled loads; never sends commands or allocates power.

Future load adapters contribute rows here. Dashboard Markdown reads this single
household description contract rather than implementing a second control model.
"""
from __future__ import annotations
from .charger_status import normalize_status, allows_automatic_current, status_explanation


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
        status = normalize_status(data.get("status", "unknown"))
        automatic = bool(data.get("auto_control"))
        paused = bool(data.get("charging_paused"))
        recommended = data.get("recommended_current_a")
        ready = bool(data and data.get("inputs_valid") and data.get("han_fresh")
                     and data.get("site_control_ready", True) and load.get("available", True))
        stage = "waiting"
        if not data or not load.get("available", True):
            explanation = tr("Opplysninger fra laderen mangler. Status kan ikke bekreftes.",
                             "Charger information is missing. Its status cannot be confirmed.")
        elif status == "disconnected":
            stage = "disconnected"
            explanation = status_explanation(status, norwegian=norwegian)
        elif status == "completed":
            stage = "completed"
            explanation = status_explanation(status, norwegian=norwegian)
        elif not allows_automatic_current(status):
            explanation = status_explanation(status, norwegian=norwegian)
        elif data.get("electrical_ready") is False:
            explanation = (str(data.get("electrical_error")) if norwegian else
                           "Confirm the physical connection under Configure → Chargers and check Easee voltage measurements.")
        elif paused:
            stage = "paused"
            explanation = tr("Ladingen er satt på pause. Slå av ladepause for å fortsette.",
                             "Charging is paused. Turn off charging pause to continue.")
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
        elif data.get("last_sent_current_a") is not None and recommended != data["last_sent_current_a"]:
            sent = data["last_sent_current_a"]
            stage = "automatic" if sent > 0 and status == "charging" else "waiting"
            explanation = tr(
                f"Anbefalingen er nå {recommended} A. Laderen beholder sist satte grense på {sent} A frem til regulering.",
                f"The recommendation is now {recommended} A. The charger keeps its last limit of {sent} A until regulation.")
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
        # Actual Easee charging is visible even while a stop is being applied.
        if not data or not load.get('available', True):
            label = tr('Utilgjengelig', 'Unavailable')
        elif status == 'charging':
            label = tr('Lader', 'Charging')
        elif status == 'completed':
            label = tr('Fullført', 'Completed')
        elif status == 'disconnected':
            label = tr('Frakoblet', 'Disconnected')
        elif status == 'offline':
            label = tr('Utilgjengelig', 'Offline')
        elif status.startswith('error') or status == 'erratic_ev':
            label = tr('Feil', 'Fault')
        elif stage == 'paused':
            label = tr('Pauset', 'Paused')
        elif automatic and not data.get('schedule_allowed', True):
            label = tr('Venter på starttid', 'Waiting for schedule')
        elif status in {'authenticating', 'awaiting_authorization', 'de_authorizing'}:
            label = tr('Venter på godkjenning', 'Waiting for authorization')
        elif status == 'paused_due_to_equalizer':
            label = tr('Pauset av Equalizer', 'Paused by Equalizer')
        elif status == 'awaiting_scheduled_start':
            label = tr('Venter på Easee-ladeplan', 'Waiting for Easee schedule')
        elif status == 'start_charging':
            label = tr('Starter', 'Starting')
        elif not allows_automatic_current(status):
            label = tr('Venter', 'Waiting')
        elif data.get('electrical_ready') is False or (automatic and not ready):
            label = tr('Avventer målinger', 'Waiting for measurements')
        else:
            label = tr('Venter', 'Waiting')
        # One status per load. The compact detail adds a cause/action only;
        # generic repeated stage and connection sentences stay out of Markdown.
        detail = ''
        if status not in {'disconnected', 'completed'}:
            if not data or not load.get('available', True):
                detail = tr('Kontroller tilkoblingen til laderen.', 'Check the charger connection.')
            elif data.get('electrical_ready') is False:
                detail = explanation
            elif paused:
                detail = (tr('Ladepause er aktiv; avventer at laderen stanser.', 'Pause is active; waiting for the charger to stop.')
                          if status == 'charging' else
                          tr('Slå av ladepause for å fortsette.', 'Turn off charging pause to continue.'))
            elif not ready:
                detail = data.get('control_reason') or tr('Avventer gyldige målinger.', 'Waiting for valid measurements.')
            elif not data.get('schedule_allowed', True):
                start = str(data.get('schedule_start_time', ''))[:5]
                detail = tr(f'Starttid kl. {start}.' if start else 'Kontroller valgt ladetid.',
                            f'Start time {start}.' if start else 'Check the selected schedule.')
            elif data.get('awaiting_reduction'):
                detail = tr('Avventer bekreftet reduksjon før mer strøm tildeles.',
                            'Waiting for confirmed reduction before assigning more current.')
            elif not allows_automatic_current(status):
                detail = explanation
            elif automatic and recommended is not None and recommended <= 0 and status != 'charging':
                detail = explanation
            elif status != 'charging':
                detail = tr('Venter på at bilen starter.', 'Waiting for the car to start.')
        advice = str(data.get("phase_advice", ""))
        any_advice |= advice.startswith("Enfase på begge")
        rows.append({
            "id": load["id"], "name": load["name"], "load_type": load.get("load_type", "ev_charger"),
            "stage": stage, "status": status, "status_label": label, "explanation": explanation,
            "automatic_control": automatic, "paused": paused,
            "mode_label": tr("Auto", "Auto") if automatic else tr("Manuell", "Manual"),
            "detail": detail, "show_charging_details": status == "charging",
            "manual_current_setting_a": data.get("manual_current_setting_a"),
            "first_priority": load["id"] == priority if len(loads) > 1 else None,
            "current_a": data.get("charger_current_a"),
            "power_w": data.get("charger_power_w"),
            "recommended_current_a": recommended,
            "last_sent_current_a": data.get("last_sent_current_a"),
            "next_regulation_at": data.get("next_regulation_at"),
            "regulation_reason": data.get("regulation_reason"),
            "minimum_current_a": data.get("control_minimum_current_a"),
            "maximum_current_a": data.get("max_current_a"),
            "schedule_enabled": bool(data.get("schedule_enabled")),
            "schedule_start": data.get("schedule_start_time"),
            "schedule_allowed": data.get("schedule_allowed"),
            "measurements_ready": ready,
            "easee_reason": data.get("electrical", {}).get("no_current_reason"),
            "control_detail": data.get("control_reason"),
        })
    single = len(rows) == 1
    stages = {row["stage"] for row in rows}
    if not rows or "waiting" in stages:
        state = "waiting"
        summary = (tr("Laderen venter. Årsaken står nedenfor.", "The charger is waiting. Its reason is shown below.")
                   if single else tr("En eller flere ladere venter. Årsaken står ved hver lader nedenfor.",
                                     "One or more chargers are waiting. Each charger's reason is shown below."))
    elif len(stages) == 1:
        state = next(iter(stages))
        summary = {
            "automatic": tr("Ladingen tilpasses boligens ledige kapasitet.", "Charging follows the home's available capacity."),
            "manual": tr("Automatisk laststyring er av.", "Automatic load control is off."),
            "paused": tr("Ladingen er satt på pause.", "Charging is paused."),
            "disconnected": (tr("Bilen er ikke koblet til laderen.", "The car is not connected to the charger.") if single
                             else tr("Ingen bil er koblet til laderne.", "No car is connected to the chargers.")),
            "completed": (tr("Ladingen er fullført.", "Charging is completed.") if single
                          else tr("Begge ladeøktene er fullført.", "Both charging sessions are completed.")),
        }[state]
    else:
        state = "mixed"
        summary = tr("Laderne har ulik status. Se forklaringen ved hver lader nedenfor.",
                     "The chargers have different states. See each charger's explanation below.")
    disconnected = [row for row in rows if row['status'] == 'disconnected']
    if len(disconnected) == len(rows) and rows:
        summary = tr('Ingen bil er tilkoblet.' if single else 'Ingen biler er tilkoblet.',
                     'No car is connected.' if single else 'No cars are connected.')
    elif disconnected:
        connected = [row['name'] for row in rows if row['status'] in
                     {'awaiting_start', 'charging', 'ready_to_charge', 'completed',
                      'start_charging', 'awaiting_load_balancing', 'awaiting_authorization'}]
        if connected:
            summary = tr(f"Bil tilkoblet: {', '.join(connected)}. Frakoblet: {', '.join(row['name'] for row in disconnected)}.",
                         f"Car connected: {', '.join(connected)}. Disconnected: {', '.join(row['name'] for row in disconnected)}.")
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
                "Single phase on both chargers may allow both to charge together. Change phase mode manually if the cars support it.") if len(rows) > 1 and any_advice else ""
    return state, {"summary": summary, "consumption_limit_kwh": limit_kwh,
                   "charging_mode": mode if len(rows) > 1 else None,
                   "priority_charger": priority_name if len(rows) > 1 else None,
                   "distribution_explanation": distribution, "phase_advice": advice,
                   "controlled_loads": rows, "load_groups": group_load_rows(rows, norwegian=norwegian)}


def group_load_rows(rows, *, norwegian=True):
    """Group normalized presentation rows; future adapters supply their own rows.

    This is presentation only. It neither creates heating loads nor decides
    heating status or control permissions from EV states.
    """
    labels = {
        'ev_charger': ('Lading', 'Charging'),
        'water_heater': ('Varmtvann', 'Hot water'),
        'floor_heating': ('Gulvvarme', 'Floor heating'),
    }
    grouped = {}
    for row in rows:
        kind = row.get('load_type', 'ev_charger')
        grouped.setdefault(kind, []).append(row)
    result = []
    for kind in list(labels) + sorted(set(grouped) - set(labels)):
        if kind not in grouped:
            continue
        members = grouped[kind]
        empty_message = ''
        if kind == 'ev_charger' and all(r['status'] == 'disconnected' for r in members):
            empty_message = (('Ingen bil tilkoblet' if len(members) == 1 else 'Ingen biler tilkoblet')
                             if norwegian else 'No cars connected')
        result.append({'load_type': kind, 'name': labels.get(kind, ('Andre laster', 'Other loads'))[0 if norwegian else 1],
                       'loads': members, 'empty_message': empty_message})
    return result
