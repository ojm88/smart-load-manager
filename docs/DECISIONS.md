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
- EnergyTariff is a prerequisite because its used-this-hour and estimate
  sensors are part of the intended energy-budget setup.

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

- Current beta.4 behavior uses 11 A when three phase conductors are active on
  a 230 V system and 6 A otherwise, based on the user's tests with a Tesla and
  Easee Charge Up / Home chargers.
- Do not identify the connected vehicle by make or model.
- Vehicle-specific automatic learning of the lowest stable current remains an
  open development item; it must be associated with the electrical charging
  configuration, invalidated on phase-count changes, and robust to normal
  voltage variation before it is presented as implemented.

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
