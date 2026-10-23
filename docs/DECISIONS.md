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
