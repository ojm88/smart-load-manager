# Smart Load Manager OJM – user guide

SLM adjusts charging to a shared hourly household energy target. It can help avoid a higher grid-capacity tariff step; savings are not guaranteed. It does not optimize spot prices.

## Requirements and installation

Use Home Assistant 2026.2 or newer, configured Easee devices, and EnergyTariff with a HAN power sensor in W or kW. **Enable the Voltage sensor on every Easee charger** under Settings → Devices & services → Easee → charger → Entities. Include disabled entities and wait for measured values.

Download a GitHub release, copy `custom_components/smart_load_manager` into `config/custom_components/`, then restart Home Assistant. From HA 2026.11 you can also add `https://github.com/ojm88/smart-load-manager` as a custom Integration in **Settings → Marketplace**; custom repositories require a GitHub connection.

## Setup

1. Add **Smart Load Manager OJM** under Devices & services.
2. Select household HAN power, EnergyTariff **used this hour**, and a safety margin.
3. Choose EV charging and the first Easee charger. Then finish with one or add a second; the second list excludes the first choice.
4. Set **Consumption limit / Forbruksgrense** on the household device (4.5–20 kWh per hour, 0.5 steps).
5. Disable older automation controlling these chargers, then deliberately enable SLM automatic control for each charger.

No custom helpers or YAML automation are required. Hot water and floor heating are explanatory planned features, not working controls.

## Household and charging groups

**Household** contains the shared budget, status, measurement diagnostics, and charging mode when two chargers exist. **Charging** contains each charger with its own controls and measurements.

| Control | Behavior |
| --- | --- |
| Automatic load control | Adjusts the dynamic current limit. Starts off after restart. Switching off selects the allowed manual minimum; pause, schedule and measurement guards remain. |
| Automatic control – charging | Toggles automation for all chargers together. Individual charger switches remain available; future thermal categories are independent. |
| Charging pause | Sends 0 A. Resume recalculates automatically or restores the previous manual limit when current measurements and limits permit. |
| Manual current | Available when automatic control and pause are off; capped by Easee's reported maximum. |
| Phase selection | Changes Easee's phase setting. SLM never automatically changes topology. |
| Schedule and start time | Independent daily 12-hour windows. An open window grants eligibility, not guaranteed charging. |
| First priority | Two complementary switches backed by one saved priority. Turning the active switch off promotes the other charger. These are SLM software roles, not Easee hardware roles. |

**Charge both** shares available power equally within each charger's bounds; when both minimums cannot fit, the eligible priority charger goes first. **One at a time** gives the eligible priority charger its turn, allowing handover on disconnection, completion, manual pause or a closed schedule.

Minimum current is 11 A for measured 230 V three-phase charging, otherwise 6 A. Maximum current comes from Easee and cannot be manually configured in SLM. SLM does not identify the vehicle. Easee Completed does not prove a full battery.

## Connection and phase control

Confirm the actual connection for each charger: **230 V IT/TT – single phase**, **230 V IT/TT – three phase**, **400/230 V TN – single phase** or **400/230 V TN – three phase**. This describes physical wiring, not the desired charging mode. Calculations use the relevant measured Easee voltages, including values such as 210 V; no fixed nominal voltage replaces measurements. IT/TT calculations use the highest relevant measured pair voltage when multiple paths are involved, to avoid granting too many amperes.

Three-phase connections retain single/automatic/three-phase mode control. Single-phase connections hide the control and reject direct phase-control requests. Missing required measurements or conflicting Easee information prevents positive current regulation.

Confirm existing chargers under **Configure → Chargers → Charger connections**. Edits preserve identities/settings, send 0 A to the loaded charger and reload SLM with automatic control off. An acknowledgement is not measured physical-stop confirmation. Generate dashboard YAML again after a connection change; single-phase cards omit phase control.

The Voltage sensor shows phase–neutral for single-phase TN, inferred line voltage for three-phase TN, and measured phase–phase for IT/TT. Nominal TN supply remains 400/230 V even when the car uses one phase. Charging status exposes the confirmed connection and electrical details.

## Measurements and dashboard

Each charger has a **name – status** heading, such as **Garage – Charging** or **Tesla – Paused**, with its own explanation. An explicit SLM device name takes precedence over a generic Easee name. Charging follows Easee's status; a positive recommendation alone does not establish charging. Regenerate dashboard YAML for this heading.

Schedule opening/closing and user controls are evaluated immediately: start-time edits, schedule/automatic-control toggles, pause/resume, phase selection and priority/distribution choices. The daily window opens at the start time and closes exactly 12 hours later. Starting still requires permission, valid measurements and enough capacity. With two chargers, measured reduction confirmation may be required first. Ordinary meter-driven regulation resumes its five-minute cadence after the control cycle completes.

Easee **completed** displays **Charging is completed**. Completion alone does not send a pause command: an existing positive allowance may remain when the hourly budget permits. Its full possible consumption remains reserved, even at 0 W. Another car still requesting charging receives capacity first; in one-at-a-time mode its turn takes over. Necessary reductions require new measured confirmation before the other charger increases. Ready/waiting states after that pause do not restore priority to the ended session. Actual charging/start or disconnection clears this treatment. Schedule, pause, faults and invalid-input stops still apply. This is not a battery SOC measurement. Authorization waits, Easee scheduling, Equalizer pauses and faults have explicit explanations. Unknown states block positive automatic allocation until a supported state is reported.

Measurements and charging status follow HA source changes. Easee may report charging before current measurements rise from 0 A; this alone does not stop charging when confirmed wiring and measured voltages are valid. Capacity and recommended current recalculate on source changes, with a 30-second elapsed-time and freshness watchdog. When Easee reports a newly connected car ready to charge, SLM evaluates charging immediately. Automatic control must be enabled, the schedule must allow charging, pause must be off, and required measurements and capacity must be available. With two chargers, necessary reductions must be measured before capacity is reassigned. The next ordinary regulation is five minutes after the startup cycle completes. Automatic limits otherwise normally update every five minutes; unchanged limits are not resent. A forecast from used energy, meter power and held current limits checks the budget until the next update or hour boundary. Risk persisting for 30 seconds can trigger an earlier reduction; imminent exhaustion bypasses confirmation. Pause, invalid required input and lower physical current limits remain immediate. An early reduction blocks ordinary increases for at least five minutes. The card distinguishes the current recommendation, last sent limit and measured current. The Markdown card has a compact meter power (W), energy used this hour (kWh), and estimated hourly energy (kWh) line. Missing values display as —. Regenerate the card to adopt this layout.

Each charger has six main measurements: status, charging power, measured current, recommended current, active phases and voltage. Names use function followed by the charger name, consistently from the first charger. Voltage follows the confirmed connection and charging mode; phase–neutral voltage and electrical details remain status attributes. Recommended current includes minimum and maximum attributes. A diagnostic priority sensor appears with two chargers.

The household status explains why each load runs or waits and provides phase advice. Measurement status contains shared source IDs, HAN age and input validity.

Run **Settings → Tools → Actions → `smart_load_manager.get_dashboard`**, then paste the returned `yaml` into a **Manual card inside an existing section**. The generator resolves actual registered IDs, including your own renames. The graph reads EnergyTariff directly. Static [one](../examples/lovelace/charging_card.yaml) and [two](../examples/lovelace/two_chargers_card.yaml) charger examples are templates; generating the card is recommended.

## Configuration

**Configure → Household sources and safety margin** validates all inputs before saving and retains load settings. Updated sources are read at the next regular refresh.

**Configure → Chargers → Add charger** lists only unused Easee devices and keeps the existing charger. **Remove charger** is a separate choice when two chargers are configured. Membership changes reload SLM. Enable automatic control again afterwards. Before removal, SLM sends a 0 A command to the removed charger; a failed command aborts the change. Command success does not confirm a physical stop. Saved settings are retained if the device is added again.

## Waiting or troubleshooting

Read household status and Measurement status first. Check HAN freshness, EnergyTariff, enabled Easee Voltage sensors, reported current limits, pause and schedules. HAN must be valid and at most 120 seconds old. An available unchanged Easee power value remains valid despite an old timestamp. Capacity moves between chargers only after subsequent current/power readings confirm a reduction.

SLM does not replace installation protection. Turning automatic control off stops further automatic writes and leaves Easee's last dynamic limit in place. Use Charging pause to explicitly send 0 A.

## Charger selection

Complete setup in Home Assistant's normal dialog, including Companion. Choose **EV charging – Easee**, select the first charger in HA's device selector with integration branding, then finish or add a second.

When adding a charger, the first is already selected. Keep it selected and use the empty field below to choose one new charger. Home Assistant excludes selected devices from that add field. Confirm in the same dialog. Use **Remove charger** to remove a configured charger; adding never replaces the existing setup.

For later additions, use Configure → Chargers → **Add charger**. The existing charger and settings are preserved. Cancelling initial setup before completion creates no partial installation.

### When to regenerate the dashboard card

Run `smart_load_manager.get_dashboard` and replace the existing Manual card YAML after adding/removing/replacing a charger, changing physical charger connections, the HAN source or referenced entity IDs, changing charger names used in headings, or adopting a feature that changes the card layout. YAML is not automatically regenerated. Normal changes to the consumption target, safety margin, priority, charging mode, schedule, phase selection and pause update through existing entity references and require no new card. Preserve manual customizations before replacing the YAML.

The card uses a short heading and three compact columns: meter power in kW, energy used and estimate. Rounding affects display only; calculations retain precision. Very large energy values use MWh. With no cars connected, redundant per-charger sections are hidden. Mixed connections identify the connected and disconnected chargers. Power, recommended/last-set current and the next regulation time appear only while Easee reports charging. Waiting, paused and completed states retain their explanations. Regenerate dashboard YAML to adopt this layout.


## Status card in beta 16

The card shows household measurements and budget first, followed by load category and individual load names. Each load has one status and Auto/Manual. A short reason or action appears only when relevant. Separators distinguish configured categories; unconfigured categories are hidden. Power, current limit and next regulation appear during charging. Floor heating and hot water in mockups are planned functionality. Regenerate YAML with `smart_load_manager.get_dashboard` after the future update.


An unchanged HAN value remains fresh when the meter reports it again. If reports stop, automatic control stops at the existing age limit. The card retains a readable numeric value with an explicit stale warning; it is not used as fresh control input. Unknown/unavailable sources have no numeric display. Raw Easee status is preserved.


## Diagnostic download in beta 16

Open **Settings → Devices & services → Smart Load Manager OJM → integration entry → ⋮ → Download diagnostics**. Download while the problem is present, before restarting or reloading, and attach the file with the observed time. It contains anonymous load state, calculation inputs, regulation decisions and current/phase service attempts/results. The last 4096 events are held in memory; overwritten events are counted. No fixed retention period is guaranteed. Restart/reload resets history; older events cannot be recovered. Service success does not establish physical charging. Credentials, names and source identifiers are excluded. Available from beta 16.


Beta 16 accepts valid HAN reports up to **120 seconds** old, inclusive. Beta 15 used 60 seconds. Freshness is based on the last report, including identical values. Older or invalid measurements stop automatic charging at the next control check.


Schedule opening, resume after pause and enabling automation must reassess an ended session against current capacity. The upcoming correction addresses a beta 16 zero-limit deadlock. An enabled schedule still applies to manual current too; disable scheduling to charge outside its window.


Missing HAN reports trigger one successful 0 A stop per affected managed charger. Recovery immediately reassesses permitted current instead of waiting for the normal five-minute tick. Pause, schedule, capacity and paired reduction acknowledgement still apply. Failed stop commands remain retryable.


Beta 17 verification: A completed-to-waiting/ready transition is reassessed immediately when SLM has retained an unchanged positive offer. At zero, the same feedback may follow an SLM pause; automatic restart after increasing the car-app target is not yet verified. Beta 17 remains unpublished pending this requirement.


Refined beta 17 policy: Preserve a budgeted offer after completion. A zero or unknown prior limit can offer the validated electrical minimum when capacity permits. The car draws only when it requests energy. Active cars receive capacity first. Waiting/ready reports reassess immediately without inferring their cause; actual charging restores active allocation. Unchanged limits are not resent. This supersedes the earlier requirement to identify status origin. Physical acceptance remains pending.


Beta 17: Update the integration and restart Home Assistant. Existing beta 16 dashboard YAML remains compatible; beta 17 does not change the card layout. Test renewed charging after raising the target in the car app and download diagnostics promptly if behavior differs.
