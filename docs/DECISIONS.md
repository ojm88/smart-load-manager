## 2026-10-24 — Make the control explanation clear

- Name the control-reason sensor **Ladeforklaring** in Norwegian and **Charging explanation** in English.
- Explain that it tells the user why charging is running, waiting, or reduced.
- Keep the existing `sensor.slm_control_reason` entity ID and all charging decisions unchanged.
- Include the change in beta 0.1.1-beta.1.

## 2026-10-23 — First stable release 0.1.0

- Release the tested beta.17 build as stable version 0.1.0 after the owner confirms it works in the live HA/Easee setup.
- Keep later experimental fixes in numbered beta pre-releases; use stable releases for versions ready for general use.
- Preserve the current one-load-entry limit until the shared allocator and multi-charger policy are designed.

## 2026-10-23 — Beta 17 pause, dashboard, and compact sensor data

- Add an integration-owned pause toggle. Turning pause on must send 0 A to the configured Easee device and keep it at 0 A while paused. Resume recalculates in automatic mode; in manual mode restore the previous limit only if the current meter, schedule, minimum, and Easee maximum checks still pass. Lock manual-current writes during pause.
- Determine HAN freshness from `last_updated`, since an unchanged numeric power value can still be freshly reported. Keep a 60-second validity limit.
- Do not repeat terminal readings, enum codes, entity maps, and HAN source on every sensor. Keep each sensor's short localized explanation, and retain raw calculation inputs in the coordinator rather than exposing duplicate attributes on every entity.
- Display power in whole watts while preserving calculation precision internally.
- Dashboard graph uses `sensor.slm_recommended_current`, `sensor.energy_used_this_hour`, `sensor.slm_charger_current`, `sensor.energy_estimate_this_hour`, and `sensor.average_peak_hour_energy`, named Anbefalt strøm, Brukt, Målt ladestrøm, Timeestimat, and Snitt 3-timer. EnergyTariff entities remain external; do not create SLM copies just for chart display.
- Describe demand-tier savings as a possible outcome that depends on the household and tariff, not a guarantee. Keep Norwegian and English guides short and plain-language.
- Preserve the single-load-entry limit until shared allocation exists. Future entities must be keyed by stable charger identity (configured charger/device label), never arbitrary `_2` suffixes; retain the existing IDs for the current installation during migration. Master/slave and sequential/simultaneous charging policies remain future owner decisions.

## 2026-10-23 — Beta 16 integration branding

- Bundle Smart Load Manager OJM icon and light/dark logo files in `custom_components/smart_load_manager/brand/`, including Home Assistant's standard high-resolution variants.
- This is a custom integration: keep its brand files in the integration repository; do not depend on a pull request to the Home Assistant brands repository. Home Assistant 2026.3+ serves these local assets.
- Keep the large project illustration in the README separate from the compact icon/logo used by the Home Assistant integration UI.

# Product and technical decisions

## 2026-10-23 — Beta 15 sensor explanations and Lovelace paste targets

- Every diagnostic sensor exposes a localized `explanation` attribute in More Info; keep the visible names concise and the entity IDs stable.
- Sensor values must tolerate absent optional coordinator fields. One missing measurement must not prevent the platform from registering unrelated entities; keep an HA-runtime regression for the missing-current case.
- Keep `charging_card.yaml` as a single `vertical-stack` card for the manual card editor inside an existing section. Keep `charging_view.yaml` as a complete `type: sections` view for the raw view editor. Name the exact paste target in both manuals, README, and YAML comments; test the formats.
- Include a project image in the README and repository.

## 2026-10-23 — Beta 14 sensor recovery and entity IDs

- The earlier coordinator payload omitted `charger_current_a` while the sensor platform read it eagerly to build every diagnostic sensor value. One KeyError therefore prevented the entire sensor platform from adding entities. Return the measured current from the coordinator and use a safe `.get()` for this optional diagnostic field; keep a Home Assistant-runtime regression test.
- Beta.12 used `_attr_suggested_object_id`, which Home Assistant does not use as a supported integration attribute. Beta.13 sets the entity's proposed `entity_id` explicitly for stable `slm_*` IDs and tests the sensor ID. Home Assistant currently accepts this with a deprecation/usage warning that is scheduled to become an error in a future core release; recheck the supported entity-ID API before that transition.
- Dashboard examples have two distinct formats: a full `type: sections` view for raw dashboard-view YAML and a `vertical-stack` card for a single-card YAML editor.


This file records durable decisions so work can continue without relying on
chat history. Add a dated entry when a decision changes.

## 2026-10-25 — Project motivation, acknowledgements, and support

- Explain that the project's main goal is reducing avoidable household peaks that can affect the Norwegian grid-capacity tariff. Savings depend on the grid company, tariff, and household; never guarantee a saving.
- The current supported controllable load is an Easee EV charger. Hot-water tanks and floor heating are possible later loads because they can store heat. Do not claim they are implemented. Do not target lights, cooking, tumble dryers, or air-to-air heat pumps as controllable loads.
- The project does not optimize spot-price or Norgespris. Optional night scheduling can take advantage of grid-company night rates where applicable.
- Credit Home Assistant's Easee integration and EnergyTariff by Erling Paulsen as current projects this integration uses. Thank the open-source community. Mention Versatile Thermostat (VTherm) only as a possible future reference for thermal loads, not as a dependency or implemented feature.
- Add voluntary coffee support after the owner provides a real donation URL/account. Do not publish a placeholder or invent a destination.
- The repository currently has no license. Keep this limitation clear and ask the owner to choose a license before describing this repository itself as open source or adding a license file.
- Use neutral, technical wording in the charging-reason sensor. Describe the active control condition and relevant inputs; do not personify the integration or use first-person wording. This changes display text only, not charging behavior or the entity ID.
- Include these documentation and display-text updates in beta 0.1.1-beta.2; no charging behavior or entity ID changes.

## 2026-10-23 — Stable entity IDs and manual control ownership (beta 12)

- Give every Smart Load Manager diagnostic sensor a concise, stable `slm_` object ID. Keep the agreed installation-wide Forbruksgrense entity ID exactly as it is.
- Migrate existing entity-registry IDs on upgrade while preserving Home Assistant unique IDs; never take over a target ID already owned by another entity.
- Manual current is an optional alternative control. It is unavailable while automatic control is enabled, a status sensor explains why, and direct writes are rejected while it is locked.
- Maintain the descriptive Markdown status card, clear control/measurement sections, and charging and energy history graphs in the Lovelace example. Do not hard-code installation-specific Easee IDs.

## 2026-10-23 — Project scope and naming

- Use **Smart Load Manager OJM** as the visible project and integration name. Keep the internal domain `smart_load_manager` stable to preserve existing config entries. Do not name
  the whole project after Easee because later load types may include hot-water
  tanks and floor heating.
- Easee EV charging is the first supported load type.

## 2026-10-23 — Installation-specific configuration

- A user selects the Easee charger device, not a list of per-installation
  `sensor.easee_*` entity IDs or individual attributes.
- Resolve relevant sibling entities through Home Assistant's device and entity
  registries. Keep installation-specific IDs out of the shared integration.
- Require the user to select the instantaneous HAN power sensor used by
  EnergyTariff. Accept W or kW; reject energy counters in kWh.
- EnergyTariff is a prerequisite. Select its used-this-hour sensor for the
  control calculation. The estimate is displayed as an integration sensor,
  but is not a setup requirement or safety gate.

## 2026-10-23 — Electrical detection

- Do not require a manual one-phase/three-phase or voltage selector for the
  charging calculation.
- Read available Easee terminal voltage and current measurements and compute
  voltage class and active phase count from those measurements.
- Keep configured phase mode and measured active phase use as separate facts.
- Do not infer line-to-line voltage from the aggregate voltage state alone.
- Use measured voltage in the power/current calculation so ordinary voltage
  variation is accounted for.

## 2026-10-23 — Minimum charging current

- Use 11 A when measured current is present on all three phase conductors
  during 230 V IT/TT charging; use 6 A otherwise. This is the fixed agreed
  rule based on the user's tests with a Tesla and Easee Charge Up / Home.
- Do not identify the connected vehicle by make or model. Do not perform an
  automatic learning or active minimum-current probing process. The agreed
  electrical premises are implemented directly.

## 2026-10-23 — Control safety and scheduling

- Automatic current control is explicitly opt-in and off by default.
- When automatic control is enabled, stale or invalid HAN input, missing
  required tariff data, or unreliable electrical measurements must not produce
  an unsafe positive current command; beta.4 pauses at 0 A.
- Clock scheduling is optional and is implemented with integration-owned HA
  switch and time entities. Users do not create schedule helpers or depend on
  an Easee Smartlading switch. The daily 12-hour window and start time persist
  across restarts; automatic current control remains off after restart.
- The integration and legacy automation must not control the same dynamic
  current limit at the same time.

## 2026-10-23 — Repository visibility

- The owner chose to make `ojm88/smart-load-manager` public so others can see
  the project. Do not add collaborators or publish releases unless the owner
  asks for that. No open-source license is currently included.

## 2026-10-23 — Integration loading

- Easee and EnergyTariff are ordered as `after_dependencies`, not hard
  `dependencies`. Their entities are required and validated during setup, but
  failure to set up either external integration must not prevent the Smart
  Load Manager configuration flow itself from loading.

## 2026-10-23 — No user-created schedule helpers

- The integration owns the daily schedule switch and native time entity.
- Persist the schedule state and start time with the config entry.
- Do not make setup depend on user-created helpers or installation-specific
  schedule entity IDs.

## 2026-10-23 — Easee maximum current

- Do not ask users to enter a charger maximum in Smart Load Manager setup.
- Derive the allowed upper current from the lowest valid circuit/charger limit
  reported by the selected Easee device.
- If Easee reports no usable limit, keep automatic control at 0 A and reject
  positive manual current commands until a limit is available.

## 2026-10-23 — Beta 9 setup and diagnostics

- Provide Norwegian and English config-flow labels and per-field explanations,
  and localized names/icons for integration entities.
- Do not ask the user to select EnergyTariff's estimate sensor; expose its
  standard sensor value as a read-only diagnostic and do not let an unavailable
  estimate block charging control.
- Expose the live maximum current reported by Easee as a read-only sensor. Do
  not ask for or permit manual configuration of the persistent charger limit.
- Preserve automatic control as opt-in and off after restart. If automatic
  control is on, send 0 A for disconnected charging, closed schedule, invalid
  or stale required sources, or unreliable electrical calculation.
- The user will temporarily disable the existing YAML automation during the
  supervised integration test; do not remove or modify that working automation.

## 2026-10-23 — Forbruksgrense setpoint (beta 10)

- Provide an integration-owned select entity named **Forbruksgrense**, with the former `input_select.forbruksgrense` choices from 4.5 to 20 kWh in 0.5 kWh steps.
- This is the authoritative hourly target used by the Smart Load Manager calculation. Do not ask for it during setup and do not read EnergyTariff's configured `target_energy` as a competing setpoint.
- EnergyTariff remains required as the source of measured energy consumed this hour; its estimate remains a diagnostic sensor.
- When upgrading beta.9 entries, migrate their existing `hourly_limit_kwh` value into the select's initial effective state and persist the user's new selection in config-entry options.

## 2026-10-23 — Extensible load and multi-charger architecture

- Keep **Smart Load Manager OJM** load-agnostic at the project/core level. Easee EV charging is the first load adapter; future adapters may include hot-water tanks and floor heating. Do not let the central budget/controller depend on Easee-specific entity names or APIs.
- Model each charger/load as its own configured instance with isolated telemetry, settings, calculated recommendation, and actuator command. Do not use singleton state that would prevent adding a second or third charger.
- Separate (1) device/load adapters and telemetry, (2) site/shared-budget allocation policy, and (3) device-specific command handling. The current beta remains a single configured Easee charger; prepare clean interfaces without prematurely implementing multi-load scheduling.
- For future multi-charger installs, represent circuit/site membership and Easee master/slave relationships explicitly. Keep circuit-level shared limits distinct from charger-level dynamic limits; a circuit-level command must target the Easee master where required.
- Do not assume whether multiple vehicles charge sequentially or simultaneously. Before implementing allocation, the owner must choose the policy (e.g. priority/sequential, simultaneous sharing, or configurable priorities) and specify how it behaves when a vehicle connects or disconnects.
- Keep the current load as the first implementation; add hot-water and floor-heating devices as independent controllable loads with their own limits/constraints, then let a shared allocator coordinate them. Preserve the existing user-facing name and entity compatibility.
- Record future features and unresolved policy choices here and in project status so they are not lost between beta iterations. Every beta must update code, tests, README, both manuals, Lovelace example, changelog, decisions, and project status as one release unit.


## 2026-10-23 — Site-wide budget and entity naming

- Treat **Forbruksgrense** as one installation/site-wide hourly energy budget,
  shared by every present and future load (chargers, hot water, floor heating).
  It is not a separate target per charger. Individual devices retain their own
  device limits; a future shared allocator must distribute the common budget.
- The beta.10 entity `select.smart_load_manager_ojm_easee_forbruksgrense`
  represents that shared site setting even though its current object ID includes
  `easee`. Do not create a duplicate budget selector when adding another load.
- Keep existing entity IDs/unique IDs stable where possible. If a clearer
  site-level ID is introduced, migrate or preserve the existing entity registry
  mapping so dashboards and automations do not break.
- Use short, consistent, namespaced entity object IDs for new entities (English
  technical IDs, e.g. `slm_ev_power`, `slm_recommended_current`,
  `slm_active_phases`, `slm_site_budget`). Use concise localized Home
  Assistant display names (Norwegian and English translations); avoid long,
  redundant names such as repeating the full product name in every sensor.
- Apply this naming convention consistently to all entities, not only sensors.


## 2026-10-23 — Beta 11 controls and shared budget boundary

- Add an integration-owned phase-mode selector for Easee Automatic, Single phase, and Three phases using the documented Easee service. Keep configured phase mode separate from live measured phase use.
- Keep manual current as a deliberate alternate control, usable only while automatic load control is off. Zero pauses charging; positive commands remain capped by Easee's live maximum and the calculated minimum.
- Preserve the legacy automation's behavior: disabling automatic control stops further writes and leaves Easee's last dynamic limit in place (time_to_live: 0). Invalid/stale required inputs or closed schedule send 0 A only while automatic control is enabled.
- For beta.11, allow one configured load entry per HA installation so there is exactly one installation-wide Forbruksgrense selector. Do not claim multi-charger/shared allocation support yet. Keep extension points load-specific and keep future multi-load policy choices documented; choose sequential/simultaneous/priority behavior with the owner before implementing an allocator.
- Update entity display names, Norwegian and English manuals, dashboard YAML, changelog, status, and tests together for each beta.

## 2026-10-26 — Two-charger workshop, beta.3

These decisions supersede the earlier temporary single-entry/view boundary.

- Support two Easee charger entries under one site budget; inherit household
  sources/margin for later additions. Expose Add charger under Configure.
- Use real device names, not car 1/2 labels. Preserve existing entity IDs;
  suffix new ones with a saved charger-name/device key, not numeric collisions.
- Every charger has the same controls/diagnostics. Keep the budget selector
  single, on the primary entry. No manual fuse-size configuration.
- Offer two dropdowns: Charge both / One at a time, and First priority (device
  names). Equal distribution is in kW, with per-charger amp/minimum constraints.
  If both minima cannot fit, give priority to the selected eligible charger.
  If that minimum cannot fit, wait. Sequential gives all possible capacity
  to the first eligible priority charger until it stops requesting power.
- Manual pause, disconnect, completion or closed schedule allow the other to
  receive capacity. Do not infer battery state or desired charge percentage.
- Suggest single phase via Phase advice and Markdown only when calculations
  support it. The user changes phase mode; no automatic SLM phase switching.
- Serialize site sampling/commands; confirm reductions with measurements newer
  than the command before reallocating power. Do not equate HTTP success to
  actual charger current reduction. Unknown peer inputs fail closed.
- Provide two complete vertical-stack Manual-card examples for existing
  sections. Remove the full-view example. Both Markdown and controls change
  for two chargers. Native graph reads EnergyTariff entities directly.
- Add an optional response action to return ready-to-paste card YAML resolved
  against the actual entity registry, reducing manual sensor-ID replacement.
- Main branding is effect/capacity tariff steps inside a house, with OJM and a
  charging connector. Future project scope includes shiftable ohmic loads and
  adjustable EV current; current thermal control must not be claimed.
- Remove License and Checks sections from README, without changing legal files
  or removing tests. Simplify introductory setup wording as requested.

## 2026-10-26 — Beta.4 installation-first setup

- Replace the charger-first setup journey with household measurements first,
  then load-type selection and explanatory device setup. Select one or two
  Easee chargers during the same journey; permit later additions via Configure.
- Hot water and floor heating remain planned until their workshops define the
  implementation. Versatile Thermostat is the intended floor-heating dependency,
  not a dependency of the current EV integration.
- Preserve existing IDs/settings and charging logic during the setup redesign.
- Improve README installation and sensor/control documentation, distinguishing
  Marketplace through HA 2026.10 from Marketplace starting in HA 2026.11.
- Detailed scope and acceptance criteria: [Beta.4 plan](BETA4_PLAN.md).
  Requirements only; no beta.4 runtime implementation or release yet.

## 2026-10-26 — Required Easee voltage preparation

- Owner confirmed Garage setup works after enabling its Voltage sensor.
- Explain this prerequisite prominently before setup in README and both manuals,
  in initial/add-charger UI, and in actionable errors. Apply it to each charger.
- Wait for real measured values; do not substitute assumed voltage.

## 2026-10-26 — Expected multi-charger measurement waits

- Separate expected missing/stale site inputs from transport/command exceptions.
  Preserve successfully sampled diagnostic values and show a concrete wait
  reason rather than marking all entities unavailable for stale power alone.
- Keep the 120-second power freshness guard pending upstream investigation.
  Hold automatic/paused chargers at zero, never use online status as freshness.
- Avoid resetting an outstanding reduction confirmation with repeated zero
  commands. Recovery still requires fresh measured acknowledgement.

## 2026-10-26 — Easee change-based power reporting (supersedes age guard)

- Owner confirms power updates on value changes or integration restart, not
  periodically. Remove the 120-second power age guard from the beta.4 draft.
- Accept available numeric power values independently of report age. Keep
  missing/unavailable/nonfinite/negative data checks, HAN freshness and
  post-command current/power confirmation before reassigning capacity.
- A heartbeat must not be inferred from the power value's change timestamp.

## 2026-10-26 — Compact sensors approved for beta.4

- Create seven main sensors per charger: status, power, current, recommended
  current, control explanation, active phases and phase advice.
- Move minimum/maximum to recommended-current attributes; electrical details
  to status; Easee/manual/schedule explanations to control explanation.
- Create one household Measurement status diagnostic with sources/HAN age and
  input readiness. Use source HAN/EnergyTariff values directly in cards.
  Reuse switches for on/off states; avoid new duplicate sensors.
- Compatibility: retain only already registered legacy sensors under Diagnostics,
  preserving unique IDs, user renames, enabled/disabled preferences and history.
  Do not create legacy sensors for new entries or automatically disable old ones.
- Update both Manual-card examples, packaged templates, registry-aware generation,
  README and both manuals together. Keep allocator/control math unchanged.

## 2026-10-26 — Shared household settings and priority role visibility

- Owner requests Forbruksgrense isolated from charger Controls, on a shared
  household device. Pair controls belong there and appear only with two chargers.
- A single Master (first-priority) dropdown determines both complementary SLM
  roles. Add read-only per-charger role diagnostics. These are software priority
  roles, not Easee hardware-role reconfiguration or ownership of the budget.
- Separate live charger Controls from Configuration (phase/schedule/start).
  Native HA headings are fixed; custom distribution blocks belong in dashboards.
- Include charger identity in names/default IDs from the first charger. Shared
  household diagnostics stay charger-independent. Existing-ID migration needs
  explicit compatibility handling; no silent overwrite of user customizations.
- Detailed acceptance/migration requirements are in BETA4_PLAN.md. These latest
  UI/role/naming changes are requirements, not yet implemented.

## 2026-10-26 — Complementary priority toggles and editable site sources

- Replace the proposed visible Master dropdown with per-charger complementary
  toggles when two chargers exist, backed by one saved priority entry ID.
  No independent role booleans; no Easee hardware-role changes. Pending UI work.
- Recommend retaining independent schedules for different start times; common
  household budget/source settings remain wholly independent of charger roles.
- Configure must remain accessible with two chargers. Household sources/margin
  edit is now implemented locally; Add charger is a separate conditional choice.
- Validate all sources before saving shared changes across entries; retain all
  charger identity, budget, priority and schedule settings; no forced reload.

## 2026-10-26 — One household explanation contract

- Add Status for laststyring on SLM – Boligen with one summary and structured
  per-load attributes; retain Measurement status separately for diagnostics.
- Move the household budget and shared selectors onto the household device.
- New charger entries have only five main measurements; no separate new
  explanation/advice sensors. Registered old entities remain compatible.
- Markdown renders central attributes only. Extend the central presenter for
  every future load type; never fork control rules into dashboard templates.
- Publish complete site snapshots before peer updates so household presentation
  does not mix sampling cycles. Presentation does not allocate or send commands.
- The previous seven-main-sensor arrangement is superseded. See ARCHITECTURE.md.


## 2026-10-27 — Beta.5 implementation and upgrade contract

- Consolidate charger config entries into one installation with native household and charging subentries. Preserve original load IDs as stable adapter identities, move registry ownership before removing obsolete entries, and retain per-load options. Shared sources/budget/priority are installation-owned, independent of first charger or priority.
- Household-first setup supports one/two Easee devices in one validated completion. Thermal categories remain explanatory only; no thermal policy is implemented.
- Use complementary first-priority switches and role diagnostics only with two chargers. Keep a previously registered priority select as a diagnostic compatibility control. Pair-only entities are lifecycle-disabled at one charger and restored without overriding user-disabled states.
- Restore voltage as a main measurement. Apply function-first display names ending in the source charger name and consistent generated IDs from the first load. Save suffixes so upstream renames never silently regenerate identity. Migrate exact known generated IDs only, preserve customizations, collision safety and unique IDs, and expose a persisted old/new map. External YAML is not automatically rewritten.
- Keep electrical/control/allocation math unchanged. Configuration changes affecting charger membership reload the installation with automatic control off. A removed charger must acknowledge a zero-current command before settings change; this is not measured physical-stop confirmation. Retain removed load records/options for re-addition.
- Declare HA 2026.2 as minimum; native subentry lifecycle and registry behavior are validated in HA 2026.2.3. Downgrade after schema migration requires backup restore. Physical beta.5 acceptance remains separate from software tests.
- Prepare the beta.5 branch and reviewable pull request; publishing a beta still follows the owner's request to approve releases first.


## 2026-10-27 — Current-state documentation and beta.5 publication approval

- Owner approves publishing beta.5.
- README and user guides describe the current integration, setup and behavior. Do not add upgrade histories, sensor-renaming instructions or explanations of the former HACS name. Use Marketplace directly, with its applicable minimum version. Keep technical migration details and validation records in developer documentation.
- The project is in development; avoid presenting it as a launched product with public upgrade obligations.


## 2026-10-27 — Beta.6 setup and reload corrections

- An add action is additive, never replacement of the configured list. Use explicit add/remove actions and single-choice steps. First setup selects one charger then offers finish/add-second; the second list excludes the first. Cancellation creates no partial installation.
- Build compact SelectSelector options from Easee's config-entry device index. Opening the dropdown does not run sensor probes, fetches, budget calculations or commands. Preserve device IDs as values and disambiguate duplicate labels. Phone frontend latency still requires owner testing.
- Unload controllers from the actual saved runtime rather than the already edited membership. Shut down coordinators and clear their snapshots/manual requests/pending reductions. Detached adapters retain their saved record until unload completes. Register a coordinator only after successful resolution/construction.
- Preserve the household and charging groups, original per-load identities/settings, user disabled preferences and opt-in automatic control. Re-adding a saved retired load restores its integration-disabled entities and previous settings; intentional removal is not silently undone.
- Use current indexed device-registry access and current single-owner migration on HA 2026.10 while keeping HA 2026.2 compatibility. Preserve deliberate full function-first names on HA's newer friendly-name builder without overwriting user-supplied names.
- CI now runs the full runtime tests against HA 2026.2.3/Python 3.13 and HA 2026.10.4/Python 3.14. Beta.5's original tests did not exercise the actual add/reload sequence sufficiently. No physical beta.6 validation has occurred; release approval remains separate.


## 2026-10-27 — Isolate logo-picker performance experiment

- Keep beta.6 as the installation baseline. Do not restore the old selector on assumption alone: the cause of phone latency has not been profiled.
- Native DeviceSelector does not expose an exact allowed-device-ID predicate in the supported backend schema. Its underlying frontend device-picker component does expose a deviceFilter function. Test that path in an optional read-only custom panel, without broadening integration control or changing setup behavior.
- Preserve the first/optional-second selection model in the test, with exact ID exclusion. Existing configured chargers are eligible in the initial test list so testing does not require removing the working installation.
- Native picker branding is supplied by HA. Do not claim that a successful custom-panel experiment establishes support inside native config flows, or guarantees VT climate branding. Private frontend APIs and actual phone performance require separate validation.


## 2026-10-27 — Package comparison in beta.7

- Owner requests beta.7 rather than manual YAML/file installation. Package and automatically register the read-only admin comparison panel. Keep normal config flow compact until frontend viability and phone performance are established.
- Optional panel failure must not stop load-management setup. Register static hosting once per process and remove the sidebar item when the final runtime unloads. Do not cache the experimental module.


## 2026-10-27 — Opt-in native external-step bridge for logo selection

- Keep HA's normal config-entry persistence and additive membership logic. Use a supported native external step to open a hidden HA panel with the tested frontend picker, then resume the original flow. Do not inject or patch HA frontend components.
- Offer explicit logo test paths alongside compact setup while Safari/Companion navigation is unverified. Initial flow supports one/two chargers; options flow allows one unused charger and retains the existing load.
- Treat frontend IDs as untrusted: require authenticated administrators, random expiring session bound to an active flow, server-side eligibility and electrical validation, and cancellation/replay cleanup. Never save partial installation or change physical control in the picker callback. Existing final options persistence/reload policy remains unchanged.


## 2026-10-27 — Beta.8 presentation and sidebar

- Owner requests no test page in the left sidebar. Stop automatic registration of the beta.7 comparison panel; the logo picker used by setup remains a hidden panel and does not add a sidebar item. Retain its shared frontend picker code. A full restart removes beta.7's in-memory sidebar registration.
- Structure README around introduction, requirements, installation, configuration, supported functions, limitations, help, future work and credits, inspired by merkens/ha-xcomfort-bridge. Describe current behavior only; keep technical history in developer documentation. No license, donation destination or support guarantee is invented.
- Preserve the beta.2 calculation/control/budget functions and beta.4 allocation formulas. Software tests and retained source do not establish physical beta.8 acceptance or prove two-charger performance.


## 2026-10-27 — README content requested by owner

- Keep experiment/navigation implementation details out of README. Explain the required EnergyTariff input, sensor meanings and ready-made YAML generation via Settings → Tools → Actions.
- Explain Norwegian household capacity-step use using current primary Glitre Nett/NVE sources without hard-coded prices. A whole-home hourly target must be realistic: insufficient budget for minimum charging current causes waiting, and two chargers share the remaining capacity. Distinguish kWh per clock hour from instantaneous kW or fuse protection.


## 2026-10-27 — Freeze project presentation and target stable version 2

- Owner accepts the GitHub presentation as the baseline. Do not routinely rewrite documentation or rearrange the repository. Update for agreed new functionality, required bug/accuracy fixes, or release/validation status; this is not an instruction to archive, restrict access to, or disable the repository.
- Document dashboard regeneration for membership/source/ID/embedded-name/layout changes; runtime control values need no new YAML. Generated Manual cards are snapshots and replacing them can overwrite user customizations.
- Target stable 2.0.0 after successful physical two-charger acceptance and resolution of blocking faults. This is a conditional roadmap milestone, not a release approval or a claim that physical testing is complete.


## 2026-10-27 — Correct beta.8 logo navigation

- Consolidate logo selection into the existing charging/add menu items. Remove the duplicate experimental choices; reuse known translation step IDs.
- External-step URLs must be absolute HTTP(S) URLs from HA's trusted URL helper, with preference for the current connection and then configured external/Cloud URLs. If none is available, retain compact setup. Keep a session stable when the original dialog refreshes.
- Render a lightweight first/second list using integration brand images and a brands access token obtained via HA websocket API. Never send that token to the public CDN. Keep image failures independent of selection. Do not depend on lazy HA form/device-selector bundles being loaded in a newly opened tab.
- Validate frontend behavior with DOM tests and distinguish them from actual Safari/Companion acceptance. Prepare a reviewable correction without republishing beta.8 or claiming phone acceptance.


## 2026-10-27 — Beta.9 publication approval

- Owner explicitly approves publishing the reviewed beta.8 setup correction as 0.1.1-beta.9. Keep stable 0.1.0 and earlier tags unchanged. Phone UI and physical charging acceptance remain pending.


## 2026-10-27 — All setup must remain in Companion

- Owner confirms beta.9 opens Safari and requires the entire setup to stay in the app. This supersedes the external-step logo approach. Do not attempt another browser/deep-link workaround for this requirement.
- Restore fast native name-only selectors with exact exclusions and additive membership. Remove active external flow/hosting code. Logos may return only with a supported solution that preserves native in-app setup, filtering and responsiveness; the logo is secondary to a working setup.
- Add explicit configured-Cloud-URL runtime coverage: a missing-URL fallback test cannot prove the real Companion path. Do not label API/DOM tests as actual phone UI acceptance.


## 2026-10-27 — Publish native in-dialog logos as beta.10

- Owner asks to publish an in-Companion logo solution and accepts testing phone responsiveness. Supersede the unshipped name-only choice with supported native DeviceSelector forms. No external page, browser navigation, custom frontend injection or sidebar test is part of setup.
- Use a single-device first selector and a native multi-device selector with existing sources preselected for additions. HA's own add picker excludes current values. Reject removal/replacement of existing sources and enforce exactly one new enabled Easee source; do not confuse list edits with replacement membership.
- Prefer actual manufacturer/model metadata to avoid the selector's additional integration-membership lookup. Fall back to integration=easee when metadata is missing. Validate Easee membership and electrical sources on the server because presentation metadata is not authoritative. Do not claim a phone speed improvement until the owner measures it.
- Publication of beta.10 is authorized by the current request. Charging/control/budget/allocation algorithms and automatic-control-off policy remain unchanged.


## 2026-10-27 — Confirm wiring per charger, use measured voltage (beta.11)

This supersedes the automatic topology inference decision and the earlier requirement to leave electrical inference unchanged. Owner confirms a physical 230 V three-phase installation reports unrelated T3T5/T4T5 values over 400 V. Other captures demonstrate that populated pair count cannot establish wired phase count; a TN three-phase installation can expose only its three phase–neutral voltages.

- Require one of it_1, it_3, tn_1, tn_3 per charger in native setup/options. Do not guess/migrate old records from phase mode or terminal maxima. Existing records load diagnostics but cannot calculate a positive current until confirmed.
- Follow standard Easee terminal wiring: T1 is PE, TN T2=N with T3/T4/T5 phases, and 230 V IT/TT T2/T3/T4 phases with T5 unused. Never classify supply from the highest reported pair or use PE pairs for charging power.
- Use measured relevant phase–neutral values on TN and phase–phase values on IT/TT. For an unassigned single path or unequal IT voltages, reserve capacity using the highest relevant measured voltage. TN multiphase uses the sum of the relevant measured phase voltages; IT three-phase retains sqrt(3) times measured line voltage. No nominal voltage replaces missing measurements.
- Separate physical supply from configured mode, assigned output and measured phase use. Two active IT conductors represent one charging path. Preserve the agreed 6 A / 11 A minimum policy and shared budget/allocation rules.
- Create phase-mode selector only for confirmed three-phase wiring; lifecycle-disable old ones on single/unknown connections, preserving explicit user disables. Guard direct selector requests. Dashboard generation omits the phase row for those loads.
- Changing wiring is deliberate, sends 0 A when the controller is loaded, and reloads with automatic control off. Preserve peer membership, stable identities, schedules and household settings. Incomplete/failed changes do not save.
- Do not reuse cached electrical factors when fresh required input or confirmed connection is missing/conflicting. Keep known supply type in diagnostics even if voltage measurements are absent, but expose no usable calculation factor.
- Easee v0.9.74 subscribes to detectedPowerGridType internally but does not attach it to the status entity. No live internal value was verified. This implementation uses the owner's confirmed connection and checks the public nettype attribute if available; it does not depend on private Easee objects or extra API calls. User approval of manual wiring supersedes the proposed internal diagnostic investigation.
- Sources: https://developer.easee.com/docs/enumerations, https://developer.easee.com/docs/charger-observation-ids, and the Charge Up installation guide https://download.easee.com/m/3de6f4ad6cf696d2/original/NO_ChargeUp_InstallationGuide.pdf (wiring diagrams, printed page 11). Captured fixtures exclude serial/site/device identifiers.


## 2026-10-28 — Beta.11 publication approval

- Owner explicitly authorizes release of beta.11 after review of PR #7 and its passing checks. Publish as a prerelease; retain stable 0.1.0 and all previous tags.
- Code head 6a9323ece2b062f8723bae0dae24c0c37644b6d1 passes all four CI jobs in runs 40596346688 and 40596306879. This release preparation changes documentation only.
- Physical beta.11 charging and phone acceptance remain pending; automatic control stays off after restart. Existing chargers must confirm actual wiring and regenerate dashboard YAML.


## 2026-10-28 — Live telemetry separate from regulation

- Owner requests source-driven SLM sensor updates while retaining the existing calculation/control frequency. Subscribe only to the resolved Easee status/current/voltage/power/limit sensors and selected HAN/used-energy sources plus the EnergyTariff estimate. Include attribute-only changes; no extra cloud requests.
- Publish measured and derived electrical telemetry without refreshing the coordinator polling timer, changing the saved current recommendation, reallocating capacity or sending commands. Serialize with paired regulation and notify the first coordinator when the second charger updates, so shared Markdown status follows both. Unsubscribe/cancel pending display tasks on shutdown.
- Show meter W, used kWh and estimated kWh compactly in the Markdown header through the household-status attributes. A missing value is a dash, never invented zero. Keep independent household readings visible when charger telemetry is incomplete. Existing dashboard YAML must be regenerated.
- Beta.11 is already published. Prepare this work separately as unreleased; do not alter its tag, assets or version, and do not publish a new beta without owner approval. README presentation remains frozen.

- Owner clarifies that single-charger Markdown must contain no hypothetical two-charger guidance. Use singular waiting/disconnected/completed summaries with one configured load and suppress paired phase advice unless multiple loads are configured.


## 2026-10-28 — Live calculation and five-minute regulation (beta.12)

Owner explicitly approves the proposed command cadence. This supersedes the earlier decision to retain 30-second calculation/regulation and read-only source events.

- Recalculate complete household capacity and recommendations on local HA source/attribute changes. Coalesce bursts but rerun if a source changes while a command is awaiting completion. Keep the 30-second watchdog for elapsed time, schedules and stale inputs. Use fractional remaining minutes through the actual clock-hour boundary.
- Use one household cadence for single and paired charging. Ordinary application is five minutes after a completed regular cycle; avoid unchanged writes. Source publication must not reset the watchdog. Arm an independent next-decision/confirmation callback so changes do not depend on another source event arriving. Cancel it on shutdown.
- Forecast held power conservatively: at least HAN or summed measured charger power, plus the positive gap between each last commanded limit's expected power and measured power. Compare used energy plus projected consumption through the earlier of next regulation or hour boundary against the selected limit minus safety margin. EnergyTariff's estimate remains display-only.
- Require continuous forecast risk for 30 seconds before an early reduction. If the remaining reserved budget can be exhausted within that confirmation window, reduce immediately. Early commands only lower limits; no peer increase. Hold ordinary increases for five minutes after an early reduction. Pause, loss of required inputs, closed schedule, disconnection/completion and a lower physical current limit do not wait. Explicit manual requests retain their existing immediate, budget-serialized behavior.
- Retain the original direct single-charger start on valid measurements. Two chargers still establish a known zero limit at takeover and require subsequent measured reduction confirmation before any capacity reassignment. A service response alone never confirms a paired physical reduction.
- Expose recommendation, last sent current limit, and next regular time separately in Markdown and diagnostic attributes. A falling recommendation alone must not tell the user the still-running car is paused. No new duplicate sensor entities, no private Easee API, no credentials.
- Prepare beta.12 in PR #8; this instruction does not authorize publication or alteration of beta.11. Physical acceptance is pending.


## 2026-10-28 — Complete Easee operation-state handling

Owner capture has raw status completed and a completed household explanation, alongside a nonzero calculated recommendation in beta.11. This is not merely a delayed status refresh: completed is already recognized in the captured view. Display charging completed explicitly and force the recommendation to zero for non-eligible modes; do not translate completed into verified 100% battery SOC.

- Verify const.EASEE_STATUS in Easee v0.9.74 and current master; both expose the same 22 unique state names (23 integer codes). Keep one shared, explicitly tested state map, preserving charged/awaiting_authentication as compatibility aliases.
- Only awaiting_start, charging, ready_to_charge, start_charging and awaiting_load_balancing can receive positive automatic current. Recognize every documented blocking mode with its own Norwegian/English explanation. Unknown future names wait with an explicit unknown-status explanation, rather than being allocated power implicitly.
- Completion/disconnection and specific Easee errors/waits take precedence over generic electrical/SLM waiting prose. Known blocking states stop automatic current without waiting for the five-minute interval. Manual commands retain their separately explicit behavior.
- Source: https://github.com/nordicopen/easee_hass/blob/v0.9.74/custom_components/easee/const.py (EASEE_STATUS); compared against master on 2026-10-28. Software fixtures contain no actual installation identifiers. Physical acceptance pending.


## 2026-10-28 — Beta.12 publication approval

Owner explicitly requests publication of beta.12 after the final review. Publish PR #8 as a prerelease with version/tag 0.1.1-beta.12, retaining stable 0.1.0 and all older tags. Code head d15239cecf1dce24c49bd2fb9131102823aa4fe3 passed all four CI jobs on push and PR (40744557348 / 40744567210). This preparation changes documentation only. Restart HA, generate new dashboard YAML using smart_load_manager.get_dashboard and deliberately enable automatic control after inspecting the measurements. Physical charging and phone acceptance of beta.12 remain pending.


## 2026-10-28 — Immediate plug-in evaluation (beta.13 preparation)

- Owner requests immediate evaluation/start on connection, rather than waiting for the next ordinary regulation. Remember observed disconnected status per charger, including through authorization/offline/unknown waits, and initiate one fresh shared cycle when that car reports an eligible ready/charging state. Do not treat ready-to-charging transitions or routine meter updates as new connections.
- Preserve automatic opt-in, schedules, pause, measurement/electrical validation, shared allocation and minimum current. Missing data never starts charging; retain a pending connection evaluation while required inputs recover. No new external polls or nominal voltage fallback.
- Apply through the existing paired reduction/measurement acknowledgement path. Keep a startup cycle pending until those reductions are confirmed; only then start a fresh five-minute interval. Ordinary live recommendations, forecast reductions and watchdog remain as beta.12. A second car may require reducing the first before it can start.
- Clear connection state on runtime unload. No dashboard layout/entity changes; existing beta.12 YAML continues to work. Prepare separately from the published beta.12 tag; publication of beta.13 is not authorized by this proposal. Physical acceptance is pending.


## 2026-10-28 — Charging status can precede current telemetry

- Owner reports brief starts followed by 0 A while recommendation remains positive. Read-only HA inspection confirms installed version beta.12; PR #9 remains a draft and beta.13 is not published. Current readings alone do not prove the historical stop reason.
- Reproduced the exact command sequence in a real HA source-event test: awaiting_start with valid confirmed TN wiring/voltage sends 16 A; charging arrives with the same zero-current terminal snapshot; _minimum_current selected active_phases=0 and returned None, causing an invalid-input stop and a held 0 A limit. The new test failed with [16, 0] before correction and passes with only the positive startup command afterward. Existing tests missed the asynchronous ordering.
- Use active phase count only when nonzero; otherwise use the already validated effective configuration for the minimum. This is the same measured-voltage/confirmed-wiring path used before startup, not cached or nominal voltage and not invented measured current. Missing voltage still forces 0 A; inconsistent connection/output/current checks remain. Do not remove forecast-risk regulation on the assumption that it caused this observed stop loop.
- Pure regression covers zero-current charging on TN/IT, one/three-phase settings and 210 V measurements; runtime regression includes later current/power arrival and genuine voltage loss. Local validation: 81 pure tests and 89 runtime tests on both supported HA/Python environments pass. No physical charger command, software installation or physical acceptance performed. Include correction in the beta.13 draft without altering beta.12.


## 2026-10-28 — Beta.13 publication approval

Owner explicitly authorizes publication of PR #9 as prerelease 0.1.1-beta.13. Include the reproduced charging-before-current startup correction and immediate new-connection evaluation while retaining beta.12 live calculation, five-minute cadence, forecast reductions and paired measured-reduction acknowledgement. Code head 46bbe57561742a8938f676fd5f76f5e29e421d12 passed all four jobs in CI runs 40751798978 and 40751788952. This preparation changes version and release records only. Restart HA and deliberately enable automatic control after inspecting measurements. Existing beta.12 dashboard YAML remains valid. Physical charging acceptance remains pending.


## 2026-10-28 — Immediate controls and named status headings (beta.14 preparation)

- Owner confirms beta.13 appears to work, but schedule opening and pause/resume can still wait for the ordinary five-minute application gate. Treat user intent/charging permission transitions separately from meter-driven budget changes. Explicit native controls bypass both the gate and the coordinator request debounce; serialize all allocation/commands with the existing site lock. Do not interpret ordinary awaiting_start/charging transitions as new control requests.
- Observe automatic enable, pause, schedule permission, supported Easee permission and reported phase-mode changes. Native start-time/schedule, priority/distribution and phase actions explicitly request a cycle. Stops/completion may free a peer's turn immediately, after measured reductions are confirmed. Inputs/limits/shared budget still determine whether a positive command is possible; automatic mode never blindly restores a saved limit. Manual pause/resume retains its existing explicitly saved limit and checks.
- Persist an increasing request generation until a complete validated cycle finishes, so requests arriving while a command awaits completion are not erased. Missing inputs cannot authorize an increase. Preserve the beta.13 charging-before-current fix, normal five-minute cadence and early forecast reduction behavior.
- Schedule transitions get a dedicated cancellable timer in addition to ordinary/risk deadlines. Calculate the next opening/closing from local wall time, including seconds/midnight/DST. End is exclusive, avoiding the old extra post-boundary charging second. Source updates/edits replace the timer; unload cancels it.
- Markdown exposes a localized status_label per load and renders name – status, e.g. Garasje – Lader / Tesla – Pauset, alongside its own explanation. Only Easee charging status says Lader; a positive recommendation is insufficient. Prefer an explicit SLM device name override, then source override/saved name. Reuse the naming helper for dashboard labels and priority choices without changing entity identities or user entity overrides. Existing YAML must be regenerated for this layout change.
- Prepare a draft for beta.14; no publication approval or physical acceptance is implied. Do not change beta.13 tags/version.


## 2026-10-28 — Owner confirms beta.13 single-charger operation; hold beta.14

Owner confirms beta.13 works and explicitly limits the test to one configured charger. Record this as physical single-charger feedback, not two-charger or exhaustive acceptance. Keep the prepared beta.14 changes in draft PR #10 while collecting additional findings. Do not merge, publish or install beta.14 until separately requested. Existing software test results remain valid; this update changes validation records only.


## 2026-10-29 — Break the completed/pause feedback loop (held beta.14)

- Owner supplied source-status/video evidence: completed followed by awaiting_start within three seconds and repeated ready/waiting transitions during automatic control, unlike fixed manual current. Code inspection confirms completed was removed from demands and forced 0 A; subsequent ready/waiting reports restored demand. Easee documents 0 A as pause. This identifies a command-policy feedback path, not a claim to possess historical cloud command traces.
- Treat completed as an idle session with a ceiling equal to the last commanded allowance at completion (zero if no known positive allowance). Do not grow that ceiling or infer battery SOC. Retain it through ready/waiting states. Clear on actual charging/start_charging, disconnection, removal/unload. Do not rewrite raw Easee status or latch the displayed state.
- Allocate active demands first, then only remaining budget to idle sessions, capped by that ceiling and the live maximum/minimum. In one-at-a-time mode an active allocation leaves no idle allowance. Every positive idle allowance remains part of reserved possible power and the forecast. Household risk/invalid inputs, pause, schedule and blocked states retain their stops. This can legitimately change raw status when a reduction is necessary; the guarantee is no pause solely due to completed, not immutable charger status.
- Remember ended-session priority across pause-induced ready/waiting reports so transferring capacity does not immediately reclaim it. Actual reported charging may be a renewed draw and restores normal active allocation. Safe serial reduction/measurement-before-increase remains required.
- Known idle completed/awaiting_start/ready_to_charge reports below 1 A with exactly zero W are treated as standby for the zero-current comparison. This narrow exception also avoids retrying an unchanged zero and allows paired stop acknowledgement only with both post-command reports. Never apply to positive power, >=1 A, charging, unknown modes or missing telemetry. Do not use this exception to set reported current to zero.
- Physical completion, wake/preheating and two-charger acceptance remain required. No release or installation is authorized by this code-preparation request.


## 2026-10-29 — Beta.14 publication approval

Owner explicitly requests publishing the reviewed PR #10 as prerelease 0.1.1-beta.14. Include budgeted idle handling after completed, the narrow zero-W standby comparison, immediate schedule/user controls and named status headings. Code head ce15ab54b2ce01ee23973649009543bc7234e729 passes all four CI jobs in run 40842357564. This supersedes the earlier hold instruction for this release only. Stable 0.1.0 and older tags remain unchanged. Regenerate dashboard YAML for headings. Physical charger acceptance remains pending; publication does not install or enable automatic control in any HA instance.


## 2026-10-29 — Compact phone Markdown (beta.15 preparation)

- Owner requests three top measurements on one value row at household high values and a short heading on ordinary iPhone widths. Replace the long card title and inline labels with a short content heading and a native HTML table with three header/value columns. Use kW for meter W, one decimal below magnitude 100 and whole values above, MWh for energy >=1000 kWh. Keep units/nonbreaking spaces and do not alter readings or calculation precision. Phone rendering still needs actual owner verification; structural render tests do not prove every viewport/font setting.
- All disconnected: use singular/plural no-car heading, keep household readings/budget, suppress redundant per-load sections and pair-distribution boilerplate. Mixed known connections: show count in the heading, identify connected/disconnected names, retain the disconnected row's short name/status only. Unknown/unavailable is never inferred to mean connected or disconnected.
- Show per-charger power, recommended/last-set current and next-regulation time only for raw charging status. Waiting, paused and completed retain status/reason; no regulation or command policy changes. Keep both packaged templates and ready-made examples synchronized. Existing saved YAML must be regenerated after the future update.
- Prepare beta.15 without changing published beta.14, manifest, tags, HA configuration or physical charger control. No publication is authorized by these suggestions.


## 2026-10-29 — Beta.15 publication approval

Owner explicitly requests release of the compact-card PR #11 as prerelease 0.1.1-beta.15. Code head 8e2345203202cb856b984169b60077d8fa82816c passes all four jobs in CI run 40873366785. This supersedes the earlier draft hold for this release. Preserve beta.14 and all prior tags, keep charging/control logic unchanged and require regenerated YAML for the presentation update. Actual iPhone rendering remains owner acceptance; publication does not install or enable control on any HA instance.

## 2026-10-29 — Retrospective and development discipline

Owner requests a candid review of beta.1–15 after stable 0.1.0 and expects
predictable failures/UX omissions to be found before his hardware tests.
`RETROSPECTIVE_BETA1_15.md` records every beta, avoidable shortcomings,
whole-sequence validation and remaining physical acceptance boundaries.
AGENTS.md now requires relevant scenario-based planning and evidence-based
claims. This is an internal process/documentation change only; no runtime,
release, HA installation or physical charger command changes.


## 2026-10-29 — Approved beta.16 status-card hierarchy

Owner approves the concise mockup: household measurements and budget first, then configured load categories, then named loads with one status and Auto/Manual. Use modest bold headings, category separators and aligned measurement columns. Render a short reason or action only when useful; do not repeat a category-wide charging summary, connection sentence and device status. Charging telemetry/regulation details remain limited to charging rows. Hide unconfigured categories. Floor heating and hot water illustrations are future design references, not implemented thermal controls or measured data. Theme/font/spacing follow Home Assistant; generated mockups are not actual phone validation. No release authorized by design approval.


## 2026-10-30 — Completion cycling and HAN report freshness

Owner reports continued raw Easee cycling after beta.14/15; earlier completion-policy tests were not sufficient hardware acceptance. Inspection finds HAN freshness based on last_updated, which does not advance for identical state/attribute reports. False staleness can send 0 A through MeasurementPending, followed by positive allowance on recovery, independently of the remembered completion ceiling. Use HA last_reported (fallback last_updated) in normal and partial samplers. Do not remove genuine stale-input stops or pin raw charger status. Parse existing numeric HAN readings independently of age for display, expose freshness/age on household status and explicitly mark stale readings in Markdown. Unknown/unavailable values remain missing.

A real HA 2026.10.4 sampler regression covers fresh identical reports across six hours after completed with no writes, then actual stopped reports with a 0 A command and visible stale numeric reading. It fails with previous timestamp handling. This establishes a code fault and reproducible mechanism, not the historical cause of every transition in the owner's installation. Historical command/input traces and owner overnight acceptance remain necessary. No publication, installation or physical commands authorized/performed.


## 2026-10-30 — Native SLM diagnostics and bounded flight recorder

Owner requests whole-SLM downloadable debug evidence for future development. Implement native async_get_config_entry_diagnostics, current anonymous load snapshots, selected electrical connection, completion allowance and pending-reduction flags. Use strict field allowlists: no complete config entries, registries, raw Easee attributes, names, IDs, tokens or arbitrary exception text. Runtime records sample inputs, decision target/mode, measurement waits/control failures, and actual current/phase service attempts, failure or success. A service success is not a physical acknowledgement. Monotonic event sequence plus UTC timestamps supports correlation.

Keep the last 4096 events in memory, disclose dropped count/start time and reset on reload/restart. No cloud traffic capture, historical backfill, disk persistence, new control calls or fixed overnight retention promise. Debug collection is always bounded and available without enabling verbose logs. A download is a snapshot; obtaining it before restart matters. Native HA download hook and privacy/failure/order tests are software validation; actual Companion download acceptance remains pending. Beta.16 stays unpublished.


## 2026-10-30 — Owner-selected two-minute HAN tolerance

Owner accepts HAN reports up to two minutes old. Set the shared freshness limit to 120 seconds inclusive, used by calculations and coordinator error messages. Beta.15 used 60 seconds and last_updated. Beta.16 uses last_reported and permits age <=120 seconds; unknown, nonnumeric, nonpositive and genuinely older input remains invalid. The 30-second watchdog may detect expiry after the exact boundary; do not claim an exact 120-second physical stop. Ordinary five-minute dispatch cadence is unchanged.


## 2026-10-30 — Beta.16 publication authorized

Owner explicitly requests publishing beta.16 with the agreed manual minimum transition, charging-category control, concise status card, 120-second report-based HAN freshness and native diagnostics. Supersedes preparation-only holds for this release. Preserve stable 0.1.0 and prior tags. Regenerate dashboard YAML after update/restart. Publication does not install or enable control in HA; actual overnight completion, two-charger and phone download/render acceptance remain required.


## 2026-10-30 — Observed beta.16 renewed-charge deadlock (beta.17 preparation)

Owner diagnostic trace establishes: 10:11:53 local auto enabled with closed schedule sends 0 A; 10:36:32 schedule opens with fresh valid inputs and standalone recommendation 16 A, but site target remains 0; 10:41:18 resume does not release zero; 10:42:01 manual handover sends 6 A, then 10 A, and charging follows at 10:42:08. Completion memory initialized before takeover stored 0 and never released on renewed control permission. This is distinct from the previously corrected timestamp fault. Active schedule must continue to hold manual/automatic requests outside its window.

Release completion ceilings on explicit permission reopening (auto enable, unpause or schedule opening), with full live budget and pair-reduction validation. Do not clear on ordinary completed/ready/waiting feedback or meter events: that would reintroduce priority/start-stop loops. Remember observed raw status so repeated completed samples during delayed startup do not immediately recreate the cleared ceiling. Raw status remains untouched. Fix diagnostic command context to use current mode/last sent rather than stale published fields. Private uploaded diagnostic/video are not committed. No beta.17 publication or HA actuation authorized.


## 2026-10-30 — One-shot input stop and immediate recovery

Owner clarifies: while required HAN reports are missing/stale, send 0 A once per affected managed charger after successful dispatch, not once per sample. Existing last_commanded_current guard already avoids repeated successful zero writes in MeasurementPending; failed stops must remain retryable. Mark a measurement-wait episode and request immediate regulation once required inputs and peer power become valid again. Preserve schedule/pause, live capacity and paired measured-reduction acknowledgement. Ordinary valid HAN reports still do not bypass the five-minute increase cadence. Regression covers one and two chargers, repeated wait samples, recovery before next regular tick and no repeated unchanged command afterwards.


## 2026-10-30 — Verification gate and ambiguous vehicle restart

Owner requires verification before publication. Official Easee OpMode 109 does not attribute waiting transitions to car versus load balancing. Add immediate reassessment for completed→awaiting/ready only when a positive SLM offer remained unchanged since completion. Record/suppress ambiguous transitions after a SLM command/zero offer. This is deliberately not claimed as solving every car-app target change; retain publication hold until the zero-offer case has a verified independent signal or agreed alternative policy. See BETA17_VERIFICATION.md. Also avoid repeated successful zeros while a configured peer is not yet loaded.


## 2026-10-30 — Refined budgeted offers replace status-origin inference

Owner requests a working refined solution, treating observations as evidence rather than assuming he supplies the implementation. Supersede the preceding ambiguous-zero/status-origin strategy. Preserve known positive completion offers and give unknown/zero completion ceilings a floor equal to the validated electrical minimum. Active demands remain first; idle offers use only remaining budget (none when an active one-at-a-time allocation exists). Budget and reserve the full offered current. No available/valid capacity still means zero.

All completed→awaiting/ready changes request immediate assessment without promoting idle demand or clearing completion memory. Actual start/charging restores active demand and requests immediate coordination. Hence the action is correct for the same electrical state regardless of event origin: no duplicate unchanged commands, no blind probe cycle, no permanent zero ceiling. A control assessment that does not change any current must not shift the ordinary cadence deadline. This also fixes a regression caught by the existing household budget recovery test.

Software: 92 pure and 129 runtime tests on both supported HA/Python versions pass. New zero-offer recovery sequence fails against prior policy. See BETA17_VERIFICATION.md for contract and physical acceptance limits. No new release authorized by this preparation request.


## 2026-10-30 — Beta.17 publication authorized

Owner explicitly requests publishing beta.17 after the refined offer policy and diagnostic coverage review. This supersedes earlier preparation-only publication holds. Publish the tested policy with manifest 0.1.1-beta.17 as a prerelease, preserve prior tags/stable, and verify CI plus the tagged source tree. No installation, automatic-control enablement or physical charging test is implied. Existing beta.16 dashboard YAML needs no regeneration for beta.17.
