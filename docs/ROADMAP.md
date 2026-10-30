# Roadmap

## Current focus: finish and test the charging integration

- Confirm initial setup, cancellation and adding a second charger entirely in the native Home Assistant dialog, including Companion. Test responsiveness of the native logo-bearing device selector and its preselected first/second flow on the owner’s phone.
- Confirm physical charging with one charger and with two sharing the household budget. Validate the per-charger physical connection choices, measured-voltage calculations on 230 V IT/TT and 400/230 V TN, and phase-control visibility for single/three-phase wiring.
- Test both allocation modes, first priority, independent schedules, pause and recovery when required measurements are missing. Confirm that the selected household target leaves useful charging capacity.
- Fix blocking faults before moving to a stable release. Software tests supplement physical acceptance; they do not replace it.

## Next milestone: stable 2.0.0

The owner's target is a stable version 2 after successful two-charger acceptance. There is no fixed release date. The release must retain one-charger behavior and have no known blocking setup or load-control faults. Physical acceptance and release approval remain separate steps.

## Load-category design

- Charging automation is independent of future hot-water and floor-heating automation. Keep per-load controls, category controls and the shared household budget distinct. Manual loads remain visible and consume capacity.
- Status cards follow household → configured category → named load, with one status and a short useful reason. Do not label the whole home paused because a charger is paused.
- Every future load adapter must extend native diagnostics and the bounded decision/command recorder, including source validity, control mode, reasons and actual service outcomes; add corresponding privacy and scenario tests.

## Later functionality

- More than two chargers sharing the household budget.
- Hot-water tanks as controllable loads.
- Floor-heating zones through Versatile Thermostat, with appropriate entity selection and integration branding.
- A voluntary coffee-support link when the account is ready.

These are planned directions, not implemented features or delivery commitments.

## Project presentation baseline

The agreed README and repository structure are the baseline. Avoid routine rewrites or rearrangement. Update documentation when agreed functionality is added, when a necessary correction or bug fix changes behavior, or when release/validation status changes. Keep technical decision history in developer documentation.

This freeze does not archive the repository, change access permissions, or stop necessary maintenance.
