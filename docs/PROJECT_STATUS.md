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
JSON validation. The user has installed beta.10 and completed setup; screenshots
confirm the integration entities and disconnected-car status in HA. The config-entry
migration, actual Easee dynamic-limit service calls, and charging behavior have not
been confirmed in the live setup. No physical charging command has been confirmed.

The beta.10 setup no longer asks for an hourly target. A per-entry `select`
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

1. Prepare the next beta around the feedback from beta.10: clearly explain the
   manual current control, add the requested Easee phase-mode control, and
   repair the dashboard example so its setup instructions and entity IDs are
   usable and unambiguous.
2. Preserve the verified beta.10 behavior: Forbruksgrense remains the actual
   calculation target, EnergyTariff used energy is the measured input, the
   estimate is diagnostic, and Easee's configured maximum is read-only.
3. Keep automatic control opt-in and off initially. Test the next beta with the
   old YAML automation disabled, then restore the old automation before
   removing the integration's automatic control.
4. Do not mark phase-mode changes, dynamic current service calls, or charging
   behavior as validated until they are observed in the user's live HA/Easee
   setup.
5. Add multi-charger allocation and other load types only after the first
   charging flow is stable and the owner has selected the allocation policy.

## Release state

Beta.10 is a public development beta, not a production release. It includes the integration-owned Forbruksgrense select, built-in schedule controls, localized setup explanations, and beta.9 value migration. Automated checks pass; live HA and charger validation are still pending.
