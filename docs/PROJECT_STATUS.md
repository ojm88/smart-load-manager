# Smart Load Manager — project status

Last updated: 2026-10-23

## Goal

Build a Home Assistant integration for coordinating controllable electrical
loads under a shared power or energy budget. Easee EV charging is the first
load type. Hot-water tanks and floor heating are possible later additions.
The project must remain independent of one installation's entity names.

## Current source baseline

The current implementation baseline is **0.1.0-beta.13** in this repository.
Beta 12 assigns short, stable `sensor.slm_*` IDs to diagnostic sensors and migrates existing registry IDs while preserving unique IDs. It adds measured charger current and a manual-control status sensor, disables manual current while automatic control is on, and restores the descriptive Markdown status and graph dashboard. The agreed Forbruksgrense ID is unchanged. As before, one configured load entry per HA installation is allowed until a shared allocator exists.

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

Beta 12 automated local checks pass: 37 unit tests, Python compilation, JSON validation, and Lovelace YAML parsing. A Home Assistant runtime import/config-flow test could not be run in the local development environment because Home Assistant dependencies are not installed; GitHub Actions provides the HA-runtime import check. The user has installed beta.10 and completed setup; screenshots
confirm the integration entities and disconnected-car status in HA. The config-entry
migration, actual Easee dynamic-limit service calls, and charging behavior have not
been confirmed in the live setup. No physical charging command has been confirmed.

The beta.11 setup no longer asks for an hourly target. A per-entry `select`
entity named **Forbruksgrense** provides 4.5–20 kWh in 0.5 kWh steps and is the
authoritative calculation target. A beta.9 entry migrates its prior value to
the new select (values outside the select range are clamped to its nearest
boundary). The EnergyTariff used-this-hour sensor remains the measured-energy
input, while the estimate is diagnostic only. The integration's visible name
is Smart Load Manager OJM; the domain and unique IDs stay stable.

## Extensibility architecture and roadmap

The project must remain load-agnostic beyond its first Easee charger. Each
charger or future controllable load is an independent configured instance with
its own measured inputs, constraints, settings, recommendation, and command
path. Keep device adapters separate from shared site-budget allocation and
from device-specific command handling. Avoid singleton coordinator state and
Easee-specific assumptions in shared policy code.

The current beta is deliberately still the first single-charger implementation;
this is an architectural boundary to preserve, not a claim that multi-load
allocation is already implemented. The planned growth path is:

1. Stabilize the first Easee charger and user experience.
2. Add multiple charger instances with explicit circuit/site membership and
   Easee master/slave relationships. Distinguish master-owned shared circuit
   limits from per-charger dynamic limits.
3. Add separate controllable-load adapters, including hot-water tanks and
   floor heating, then coordinate them through a shared allocator.

No multi-vehicle policy has been chosen. Before implementing a shared allocator,
ask the owner whether chargers should run sequentially, charge simultaneously
under a shared budget, or use configurable priorities, and define how arrivals
and departures affect that policy. Do not silently choose a policy.

For every beta, keep implementation, tests, README, Norwegian and English
manuals, Lovelace example, changelog, decisions, and project status synchronized.

## Next work

Before the next beta, carry the new site-wide budget and naming decisions
through the implementation, tests, both manuals, README, and dashboard example:

1. Install beta.13 with the existing YAML automation disabled, while keeping Smart Load Manager automatic control off initially. Verify the `sensor.slm_*` IDs have migrated and Forbruksgrense retained its agreed ID.
2. Verify that the phase selector changes Easee's configured mode and that reported mode and active phase measurements remain separate.
3. Exercise manual current only with automatic control off; confirm 0 A pause and live Easee bounds. Restore the old automation before removing the integration's automatic control.
4. Do not mark phase-mode changes, dynamic current service calls, or charging behavior as validated until observed in the user's live HA/Easee setup.
5. Keep one config entry per HA instance until a genuinely shared budget/allocator exists. Add other loads only after the owner selects allocation policy.



## Beta 12 control and support boundary

- Setup is designed around EnergyTariff's used-this-hour energy sensor plus the selected instantaneous HAN power sensor; the EnergyTariff estimate is a diagnostic sensor, not a setup field or safety gate.
- The integration's Forbruksgrense select is the calculation target; EnergyTariff's configured target_energy is not read as a replacement target.
- Fasevalg controls Easee's configured mode (Automatic / Single phase / Three phases). Reported phase mode, actual output phase, and measured current-bearing conductors are distinct data.
- Manual ladestrøm is an explicit alternative when automatic load control is off. At 0 A it pauses charging; positive current uses the live Easee maximum and fixed electrical minimum rules.
- Automatic control remains opt-in and defaults off after restart. With it enabled, stale/invalid inputs, missing necessary electrical values, disconnect, or a closed schedule cause 0 A. Disabling automatic control stops new writes and leaves the last Easee dynamic limit in effect, matching time_to_live: 0 behavior in the user's existing automation.
- One load entry per HA instance is an intentional temporary boundary for a truly shared site budget. Multi-charger/master-slave control and hot-water/floor-heating remain future work, with allocation policy not yet selected.

## Release state

Beta.12 is a public development beta, not a production release. It includes the installation-wide Forbruksgrense select, built-in schedule controls, localized setup explanations, manual-current control, Easee phase-mode selection, and beta.9 value migration. Automated tests and static checks pass; live HA/Easee validation of phase writes and charging behavior remains pending. Automated checks pass; live HA and charger validation are still pending.
