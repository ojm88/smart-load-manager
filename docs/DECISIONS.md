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
