# Smart Load Manager — project status

Last updated: 2026-10-23

## Goal

Build a Home Assistant integration for coordinating controllable electrical
loads under a shared power or energy budget. Easee EV charging is the first
load type. Hot-water tanks and floor heating are possible later additions.
The project must remain independent of one installation's entity names.

## Current source baseline

The current implementation baseline is **0.1.0-beta.7** in this repository.
It includes Easee device selection, HAN power input in W or kW, EnergyTariff
hourly energy inputs, integration-owned clock scheduling, diagnostic entities, and
opt-in dynamic current control. The Norwegian and English manuals and a
standard Lovelace example are included.

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
- The current minimum rule is 11 A for measured 230 V three-phase
  charging and 6 A otherwise. This reflects the user's Tesla/Charge Up tests;
  broader model and vehicle combinations still need validation.
- Normal voltage movement by a few volts updates the calculation and should not
  by itself restart any future learning process. A detected phase-count change
  should invalidate any phase-specific learned minimum.

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

Beta.7 unit tests, static compilation, metadata checks, and Home Assistant runtime imports pass locally. The “Invalid handler specified” report was consistent with beta.5 importing
selectors from the nonexistent `homeassistant.components.selector` module;
beta.6 corrected it. Beta.7 also removes manually configured schedule helpers.
The flow has not yet been retried in the user's HA, and no physical charger
service call has been validated.

## Next work

1. Verify the beta.7 GitHub Actions run.
2. Install beta.7, restart Home Assistant, and confirm the setup form loads. Keep automatic control off; verify entity discovery and displayed status, phase, voltage, current, and recommendation values.
3. Validate schedule behavior and dynamic-limit service calls without the old automation active.
4. Decide how to learn the lowest stable current for an unknown connected vehicle without identifying it; relearn on phase-count changes, not normal voltage variation.
5. Review Easee model/firmware differences and consider other controllable loads after Easee validation.

## Release state

Beta.7 is a public development beta, not a production release and not yet a
published HACS release. It bundles schedule controls and removes manual helper setup. Automated local checks pass; the beta.7 config flow has not yet been retried in the user's HA.
