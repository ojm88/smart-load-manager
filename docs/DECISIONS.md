# Product and technical decisions

This file records durable decisions so work can continue without relying on
chat history. Add a dated entry when a decision changes.

## 2026-10-23 — Project scope and naming

- Use **Smart Load Manager** as the project and integration name. Do not name
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
