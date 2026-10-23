# Smart Load Manager — project status

Last updated: 2026-10-23

## Goal

Build a Home Assistant integration for coordinating controllable electrical
loads under a shared power or energy budget. Easee EV charging is the first
load type. Hot-water tanks and floor heating are possible later additions.
The project must remain independent of one installation's entity names.

## Current source baseline

The current implementation baseline is **0.1.0-beta.5** in this repository.
It includes Easee device selection, HAN power input in W or kW, EnergyTariff
hourly energy inputs, optional clock scheduling, diagnostic entities, and
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
- The current minimum rule in beta.4 is 11 A for measured 230 V three-phase
  charging and 6 A otherwise. This reflects the user's Tesla/Charge Up tests;
  broader model and vehicle combinations still need validation.
- Normal voltage movement by a few volts updates the calculation and should not
  by itself restart any future learning process. A detected phase-count change
  should invalidate any phase-specific learned minimum.

## Safety and control status

- Automatic control is opt-in and off by default, including after restart.
- Beta.4 sends 0 A when required meter, tariff, or electrical data is invalid,
  unavailable, or stale while automatic control is enabled.
- Optional scheduling uses a time-only `input_datetime` and the selected Easee
  Smartlading switch, with the documented repeating 12-hour window.
- `time_to_live: 0` is used for dynamic limits, matching the existing HA
  automation's indefinite-limit behavior.
- The old automation must be disabled before enabling this integration's
  automatic control, so two controllers do not write the same Easee limit.

## Validation

The beta.5 calculation tests pass in the supplied development workspace. This
does **not** establish that the integration has started successfully in a real
Home Assistant instance or that its service calls have been tested against a
physical charger. No such validation is recorded here yet.

## Next work

1. Use a beta.5 package in a controlled Home Assistant test setup with
   automatic control initially off; verify entity discovery and displayed
   status, phase, voltage, current, and recommendation values.
2. Validate schedule behavior and dynamic-limit service calls without the old
   automation active.
3. Decide and test how to learn the lowest stable current for an unknown
   connected vehicle without identifying its make/model. Relearn when the
   active phase count changes; do not relearn for normal voltage fluctuation.
4. Review Easee model/firmware differences against supported entity and
   attribute availability.
5. Consider hot-water and floor-heating load types only after Easee control is
   stable and validated.

## Release state

Beta.5 is a public development beta, not a production release and not yet a
published HACS release. Beta.5 changes dependency loading and corrects the
GitHub Actions metadata paths; it has not yet been retried in the user's HA.
