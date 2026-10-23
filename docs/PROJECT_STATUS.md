# Smart Load Manager — project status

Last updated: 2026-10-23

## Goal

Build a Home Assistant integration for coordinating controllable electrical
loads under a shared power or energy budget. Easee EV charging is the first
load type. Hot-water tanks and floor heating are possible later additions.
The project must remain independent of one installation's entity names.

## Current source baseline

The latest stable release is **0.1.0**, based on the tested beta.17 build. The next beta draft is **0.1.1-beta.1** and changes the control-reason sensor's displayed name to **Ladeforklaring**, with a plain-language description. Its entity ID and charging logic stay unchanged. The stable release includes an Easee pause/resume switch, HAN last-update freshness, concise sensor attributes, whole-watt display, and the dashboard card using EnergyTariff's own sensors. Beta 16 added local Home Assistant branding; beta 15 added tolerant sensor reads and single-card YAML validation.
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

The stable beta.17 code passed 40 pure unit tests, Python compilation, JSON validation, YAML parse checks for both dashboard examples, and the Home Assistant runtime/import checks in GitHub Actions. The owner has confirmed it works in the live HA/Easee setup. The 0.1.1-beta.1 draft passes 41 unit tests, compilation, JSON validation, and dashboard YAML parsing locally; Home Assistant runtime/import checks remain pending a GitHub Actions run after publication.

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

The first stable release is deliberately still a single-charger implementation;
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

The owner has tested beta.17 in the live HA/Easee setup and confirmed that it
works. The next step is collecting feedback from family and friends across
their Home Assistant and Easee configurations. Keep one config entry per HA
instance until a genuinely shared budget/allocator exists. Add other loads
only after the owner selects allocation policy.



## Beta 12 control and support boundary

- Setup is designed around EnergyTariff's used-this-hour energy sensor plus the selected instantaneous HAN power sensor; the EnergyTariff estimate is a diagnostic sensor, not a setup field or safety gate.
- The integration's Forbruksgrense select is the calculation target; EnergyTariff's configured target_energy is not read as a replacement target.
- Fasevalg controls Easee's configured mode (Automatic / Single phase / Three phases). Reported phase mode, actual output phase, and measured current-bearing conductors are distinct data.
- Manual ladestrøm is an explicit alternative when automatic load control is off. At 0 A it pauses charging; positive current uses the live Easee maximum and fixed electrical minimum rules.
- Automatic control remains opt-in and defaults off after restart. With it enabled, stale/invalid inputs, missing necessary electrical values, disconnect, or a closed schedule cause 0 A. Disabling automatic control stops new writes and leaves the last Easee dynamic limit in effect, matching time_to_live: 0 behavior in the user's existing automation.
- One load entry per HA instance is an intentional temporary boundary for a truly shared site budget. Multi-charger/master-slave control and hot-water/floor-heating remain future work, with allocation policy not yet selected.

## Release state

Version 0.1.0 is the first stable GitHub release, based on beta.17. The next beta draft updates only the user-facing name and explanation of the control-reason sensor; it preserves the `sensor.slm_control_reason` entity ID and charging logic. It has not been published yet. Future updates will use beta pre-releases for additional testing before stable releases. This implementation supports one configured load entry per Home Assistant installation; multi-charger allocation is future work.
