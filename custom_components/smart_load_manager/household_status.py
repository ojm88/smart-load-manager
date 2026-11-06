"""Presentation of all controlled loads; never sends commands or allocates power.

Future load adapters contribute rows here. Dashboard Markdown reads this single
household description contract rather than implementing a second control model.
"""
from __future__ import annotations
from math import isfinite
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
        other_running = any((other.get("data") or {}).get("recommended_current_a", 0) or 0
                            for other in loads if other["id"] != load["id"])
        priority_wait = bool(priority_name and load["id"] != priority and other_running)
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
        elif not data.get("schedule_allowed", True):
            start = str(data.get("schedule_start_time", ""))[:5]
            explanation = (tr(f"Tidsstyring holder igjen ladingen til kl. {start}.",
                              f"The charging schedule holds charging until {start}.") if start
                           else tr("Tidsstyring holder igjen ladingen til ladevinduet åpner.", "Charging is waiting for its scheduled time."))
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
            if sent == 0 and recommended > 0:
                explanation = tr(
                    f"SLM holder ladingen på 0 A. Nå er det plass til {recommended} A; avventer neste regulering.",
                    f"SLM is holding charging at 0 A. There is now room for {recommended} A; waiting for the next adjustment.")
            elif recommended <= 0 and priority_wait:
                explanation = tr(
                    f"{priority_name} får lade først. Laderen beholder {sent} A frem til regulering.",
                    f"{priority_name} charges first. The charger keeps {sent} A until adjustment.")
            elif recommended <= 0:
                explanation = tr(
                    f"SLM anbefaler stopp for å holde forbruksgrensen. Laderen beholder {sent} A frem til regulering.",
                    f"SLM recommends stopping to stay within the consumption limit. The set limit remains {sent} A until adjustment.")
            else:
                explanation = tr(
                    f"Anbefalingen er nå {recommended} A. Laderen beholder sist satte grense på {sent} A frem til regulering.",
                    f"The recommendation is now {recommended} A. The charger keeps its last limit of {sent} A until adjustment.")
        elif recommended <= 0:
            if priority_wait:
                explanation = (tr(f"{priority_name} får lade først. Denne laderen venter på tur.",
                                  f"{priority_name} charges first. This charger is waiting its turn.")
                               if mode == "one_at_a_time" else
                               tr(f"Det er bare plass til én lader nå. {priority_name} får lade først.",
                                  f"There is room for only one charger now. {priority_name} charges first."))
            else:
                explanation = tr("Ladingen venter for å holde boligen under valgt forbruksgrense. Starter automatisk når det blir plass.",
                                 "Charging is waiting to keep the home within its selected consumption limit. It resumes automatically when there is room.")
                minimum = data.get("control_minimum_current_a")
                factor = data.get("kw_per_amp")
                if (isinstance(minimum, (int, float)) and isfinite(minimum) and minimum > 0
                        and isinstance(factor, (int, float)) and isfinite(factor) and factor > 0):
                    explanation += tr(
                        f" Minste lading krever {minimum * factor:.1f} kW. Reduser annet forbruk for å frigjøre kapasitet.",
                        f" Minimum charging requires {minimum * factor:.1f} kW. Reduce other consumption to free capacity.")
        else:
            stage = "automatic"
            explanation = tr("Ladestrømmen tilpasses slik at resten av boligen også har plass innenfor forbruksgrensen.",
                             "Charging current is adjusted to leave room for the rest of the home within the consumption limit.")
            if status != "charging":
                sent = data.get("last_sent_current_a")
                explanation = (tr(
                    f"SLM har satt {sent} A. Easee melder fortsatt venting. Kontroller bilens ladeplan eller ladegrense hvis dette vedvarer.",
                    f"SLM has set {sent} A. Easee still reports waiting. Check the vehicle schedule or charge limit if this persists.") if sent is not None and sent > 0 else
                    tr("Avventer bekreftet strømgrense fra SLM.", "Waiting for a confirmed SLM current limit."))
        if (automatic and ready and not paused and data.get('schedule_allowed', True)
                and data.get('electrical_ready') is not False
                and not data.get('awaiting_reduction')
                and status == 'charging' and recommended == 0
                and data.get('last_sent_current_a') == 0):
            explanation = tr(
                "SLM har bedt om 0 A for å holde forbruksgrensen. Avventer at laderen stanser.",
                "SLM requested 0 A to stay within the consumption limit. Waiting for the charger to stop.")
            if priority_wait:
                explanation = tr(
                    f"SLM har bedt om 0 A slik at {priority_name} får lade først. Avventer at laderen stanser.",
                    f"SLM requested 0 A so {priority_name} can charge first. Waiting for the charger to stop.")
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
        elif (not data.get('schedule_allowed', True) and allows_automatic_current(status)
              and data.get('electrical_ready') is not False and (not automatic or ready)):
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
        # Compact detail uses the same decision explanation as the full payload.
        # A live recommendation is not a sent command or proof of physical draw.
        detail = ''
        if status not in {'disconnected', 'completed'}:
            if not data or not load.get('available', True):
                detail = tr('Kontroller tilkoblingen til laderen.', 'Check the charger connection.')
            elif not allows_automatic_current(status):
                detail = explanation
            elif data.get('electrical_ready') is False:
                detail = explanation
            elif paused:
                detail = (tr('Ladepause er aktiv; avventer at laderen stanser.', 'Pause is active; waiting for the charger to stop.')
                          if status == 'charging' else
                          tr('Slå av ladepause for å fortsette.', 'Turn off charging pause to continue.'))
            elif automatic and not ready:
                detail = data.get('control_reason') or explanation
            elif not automatic or not data.get('schedule_allowed', True):
                detail = explanation
            elif (data.get('awaiting_reduction') or recommended is None
                  or not data.get('kw_per_amp') or not data.get('max_current_a')
                  or recommended <= 0 or recommended != data.get('last_sent_current_a')
                  or status != 'charging'):
                detail = explanation
        if (not detail and automatic and ready and status == 'charging'
                and data.get('charger_power_w') == 0):
            detail = tr("Easee melder lading, men målt effekt er 0 W. Avventer oppdaterte lademålinger.",
                        "Easee reports charging, but measured power is 0 W. Waiting for updated charging measurements.")
        if data.get('stop_unconfirmed'):
            detail = tr("Stopp ikke bekreftet. Easee rapporterer fortsatt belastning. Kontroller ladingen i Easee-appen.",
                        "Stop not confirmed. Easee still reports load. Check charging in the Easee app.")
        elif data.get('reserve_stop_pending'):
            detail = tr("Avventer ferske målinger som bekrefter at Easee har stoppet.",
                        "Waiting for fresh measurements confirming that Easee has stopped.")
        elif data.get('reserve_resume_failed'):
            detail = tr("Easee kunne ikke bekrefte gjenopptakelse. Kontroller ladingen i Easee-appen.",
                        "Easee could not confirm resumption. Check charging in the Easee app.")
        compact_regulation = (
            not any(data.get(key) for key in ('stop_unconfirmed', 'reserve_stop_pending', 'reserve_resume_failed'))
            and automatic and ready and status == 'charging' and not paused
            and data.get('schedule_allowed', True)
            and data.get('electrical_ready') is not False
            and not data.get('awaiting_reduction')
            and recommended is not None and (recommended > 0 or not priority_wait)
            and data.get('last_sent_current_a') is not None
            and data['last_sent_current_a'] > 0 and (data.get('charger_power_w') or 0) > 0
            and data.get('kw_per_amp') and data.get('max_current_a')
        )
        regulation_note = ""
        if compact_regulation:
            sent = data['last_sent_current_a']
            measured = data.get('charger_current_a')
            if recommended <= 0:
                regulation_note = tr("For lite plass innenfor timegrensen",
                                     "Insufficient room within the hourly limit")
            elif (data.get('settled_offer_a') == sent
                  and isinstance(measured, (int, float)) and 0 < measured <= sent - 1):
                regulation_note = tr(f"Målt ladestrøm: {measured:.0f} A",
                                     f"Measured charging current: {measured:.0f} A")
        show_waiting_check = bool(automatic and ready and not paused
                                  and data.get('schedule_allowed', True)
                                  and allows_automatic_current(status) and status != 'charging'
                                  and data.get('electrical_ready') is not False
                                  and not data.get('awaiting_reduction')
                                  and recommended is not None and data.get('kw_per_amp')
                                  and data.get('max_current_a') and data.get('next_regulation_at'))
        if (automatic and ready and not paused and data.get('schedule_allowed', True)
                and data.get('electrical_ready') is not False
                and allows_automatic_current(status) and status != 'charging'):
            if data.get('awaiting_reduction'):
                label = tr('Avventer reduksjon', 'Waiting for reduction')
            elif recommended is not None and recommended <= 0:
                label = tr('Venter på kapasitet', 'Waiting for capacity')
            elif recommended and data.get('last_sent_current_a') == 0:
                label = tr('Venter på regulering', 'Waiting for adjustment')
        # One status per load; normal unchanged charging needs no repeated prose.
        advice = str(data.get("phase_advice", ""))
        any_advice |= advice.startswith("Enfase på begge")
        rows.append({
            "id": load["id"], "name": load["name"], "load_type": load.get("load_type", "ev_charger"),
            "source_available": bool(data and load.get("available", True)),
            "stage": stage, "status": status, "status_label": label, "explanation": explanation,
            "automatic_control": automatic, "paused": paused,
            "mode_label": tr("Auto", "Auto") if automatic else tr("Manuell", "Manual"),
            "detail": detail, "show_charging_details": status == "charging",
            "show_waiting_check": show_waiting_check,
            "compact_regulation": bool(compact_regulation),
            "regulation_note": regulation_note,
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


def charging_summary(payload):
    """Read-only category totals from the same snapshot as the household card."""
    import math
    rows = [r for r in payload.get("controlled_loads", []) if r.get("load_type") == "ev_charger"]
    known = [r for r in rows if r.get("source_available") and r.get("status") not in {"unknown", "unavailable", "other"}]
    automatic = [r for r in known if r.get("automatic_control")]
    powers = [r.get("power_w") for r in rows]
    complete = bool(rows) and len(known) == len(rows) and all(
        isinstance(p, (int, float)) and not isinstance(p, bool) and math.isfinite(p) and p >= 0
        for p in powers)
    return {
        "charger_count": len(rows),
        "available_chargers": len(known),
        "charging_chargers": sum(r.get("status") == "charging" for r in known),
        "completed_chargers": sum(r.get("status") == "completed" for r in known),
        "automatic_chargers": len(automatic),
        "automatic_mode": ("unknown" if len(known) != len(rows) else
                           "off" if not automatic else "all" if len(automatic) == len(rows) else "mixed"),
        "automatic_charger_names": [r["name"] for r in automatic],
        "total_power_w": round(sum(powers), 1) if complete else None,
        "power_measurements_complete": complete,
        "capacity_for_automatic_charging_kw": payload.get("site_available_kw"),
        "loads": rows,
    }
