# Smart Load Manager — project status

Last updated: 2026-10-23

## Goal

Build a Home Assistant integration for coordinating controllable electrical
loads under a shared power or energy budget. Easee EV charging is the first
load type. Hot-water tanks and floor heating are possible later additions.
The project must remain independent of one installation's entity names.

## Current source baseline

The current implementation baseline is **0.1.0-beta.9** in this repository.
Beta 9 adds localized setup labels/descriptions, removes the EnergyTariff
estimate picker and safety dependency, exposes the estimate and Easee maximum
current as sensors, and adds control/service-payload regression tests. It keeps
Easee selection, W/kW HAN input, used-energy input, integration-owned clock
scheduling, diagnostic entities, and opt-in current control.

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

Beta.7 unit tests, static compilation, metadata checks, and Home Assistant runtime imports passed in GitHub Actions. The “Invalid handler specified” report was consistent with beta.5 importing selectors from the nonexistent `homeassistant.components.selector` module; beta.6 corrected it. Beta.7 also removed manually configured schedule helpers.
Beta 9 has automated regression checks; it has not yet been installed and validated in the user's HA. No physical
charger service call has been validated. Beta 9 removes the estimate input from setup and displays the Easee maximum current as a read-only sensor. It uses the lowest valid live current limit exposed by Easee;
when no such limit is available, automatic control holds 0 A and positive
manual commands are rejected.

## Next work

1. Run the beta.9 Home Assistant test with the old YAML automation disabled and automatic control initially off.
2. Compare sensor and recommendation values, then enable the integration controller under supervision.
3. Record actual Easee service behavior and any differences across charger models/firmware.
4. Consider other controllable loads only after Easee behavior is validated.

## Release state

Beta.9 is a public development beta, not a production release and not yet a
published HACS release. It bundles schedule controls, removes manual helper setup, and adds localized setup explanations. Automated local checks and GitHub Actions must pass before testing in the user's HA.
