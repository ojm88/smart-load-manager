# Smart Load Manager — project status

Last updated: 2026-10-23

## Goal

Build a Home Assistant integration for coordinating controllable electrical
loads under a shared power or energy budget. Easee EV charging is the first
load type. Hot-water tanks and floor heating are possible later additions.
The project must remain independent of one installation's entity names.

## Current source baseline

The current implementation baseline is **0.1.0-beta.10** in this repository.
Beta 10 adds the integration-owned Forbruksgrense select control (4.5–20 kWh, 0.5 kWh steps), makes it the calculation setpoint, and migrates beta.9 values on upgrade (clamping values outside the new selector range). The visible name is Smart Load Manager OJM while the internal domain remains stable. It keeps EnergyTariff used energy as a required input and its estimate as a diagnostic sensor.

## Electrical interpretation

- Voltage is calculated from the Easee terminal voltage measurements available
  in the selected charger device; the aggregate voltage sensor value alone is
  not treated as line-to-line voltage.
- Configured phase mode, reported output phase, and measured active phase
  conductors are kept distinct. During charging, current measurements are
  used to identify which phase conductors are carrying current.
- The observed Garasje example (about 230 V phase-to-neutral readings and
  current on three phase conductors) should be interpreted as roughly 400 V,
  three-phase charging.
- The fixed minimum rule is 11 A for measured 230 V three-phase charging with
  all three phase currents, and 6 A otherwise, based on the user's Tesla and
  Charge Up/Home tests. No vehicle learning or active probing is implemented
  or planned under the agreed premises.
- Normal voltage movement updates the calculation directly; no learning cycle
  exists to restart.

## Safety and control status

- Automatic control is opt-in and off by default, including after restart.
- The controller sends 0 A when required meter, tariff, or electrical data is invalid,
  unavailable, or stale while automatic control is enabled.
- Optional scheduling uses the integration-owned `Tidsstyring` switch and
  `Starttid lading` time entity. Both settings persist across HA restarts. No
  user-created helper or Easee Smartlading switch is needed.
- `time_to_live: 0` is used for dynamic limits, matching the existing HA
  automation's indefinite-limit behavior.
- The old automation must be disabled before enabling this integration's
  automatic control, so two controllers do not write the same Easee limit.

## Validation

Beta 10 automated local checks pass: 31 unit tests, Python compilation, and
JSON validation. The beta.10 config-entry migration, EnergyTariff entity mapping,
Home Assistant setup, and Easee service calls have not been validated in the
user's live HA instance. No physical charger command has been confirmed.

The beta.10 setup no longer asks for an hourly target. A per-entry `select`
entity named **Forbruksgrense** provides 4.5–20 kWh in 0.5 kWh steps and is the
authoritative calculation target. A beta.9 entry migrates its prior value to
the new select (values outside the select range are clamped to its nearest
boundary). The EnergyTariff used-this-hour sensor remains the measured-energy
input, while the estimate is diagnostic only. The integration's visible name
is Smart Load Manager OJM; the domain and unique IDs stay stable.

## Next work

1. Install beta.10 in HA with the old YAML automation disabled; keep automatic
   control off initially.
2. Confirm the **Forbruksgrense** select appears on the Smart Load Manager
   device, has the expected 4.5–20 kWh options, and changing it updates the
   recommendation after refresh.
3. For an existing beta.9 entry, confirm its former hourly limit appears as
   the initial Forbruksgrense value.
4. Compare diagnostic voltage, active phases, minimum current, HAN power,
   EnergyTariff used energy, estimate, and recommended current against live
   values before enabling control.
5. Only then enable automatic control while present. Confirm the Easee
   dynamic-limit behavior; disable it before restoring the old automation.
6. Consider additional controllable loads only after Easee behavior is
   validated.

## Release state

Beta.10 is a public development beta, not a production release. It includes the integration-owned Forbruksgrense select, built-in schedule controls, localized setup explanations, and beta.9 value migration. Automated checks pass; live HA and charger validation are still pending.
