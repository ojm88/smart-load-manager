# Roadmap

## Current focus: finish and test the charging integration

- Complete the beta 8 setup test: logo selection, return to the original dialog, cancellation, and adding a second charger in Safari and Companion.
- Confirm physical charging with one charger and with two sharing the household budget.
- Test both allocation modes, first priority, independent schedules, pause and recovery when required measurements are missing. Confirm that the selected household target leaves useful charging capacity.
- Fix blocking faults before moving to a stable release. Software tests supplement physical acceptance; they do not replace it.

## Next milestone: stable 2.0.0

The owner's target is a stable version 2 after successful two-charger acceptance. There is no fixed release date. The release must retain one-charger behavior and have no known blocking setup or load-control faults. Physical acceptance and release approval remain separate steps.

## Later functionality

- More than two chargers sharing the household budget.
- Hot-water tanks as controllable loads.
- Floor-heating zones through Versatile Thermostat, with appropriate entity selection and integration branding.
- A voluntary coffee-support link when the account is ready.

These are planned directions, not implemented features or delivery commitments.

## Project presentation baseline

The agreed README and repository structure are the baseline. Avoid routine rewrites or rearrangement. Update documentation when agreed functionality is added, when a necessary correction or bug fix changes behavior, or when release/validation status changes. Keep technical decision history in developer documentation.

This freeze does not archive the repository, change access permissions, or stop necessary maintenance.
