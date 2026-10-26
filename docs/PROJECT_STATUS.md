# Smart Load Manager OJM — project status

Updated: 2026-10-26

## Release

Stable: 0.1.0. Published beta: 0.1.1-beta.3. Beta.4 publication in progress.
Release: https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.3
Code commit: 293e399a433b5915aea65a8dddbd7b37e09c44e8.

## Implemented in beta.3

- Up to two Easee config entries, added initially or later using Configure.
- One shared Forbruksgrense, HAN source, used-this-hour source and margin.
- Per-charger controls/sensors, stable name/device-suffixed IDs for the new
  charger; existing first-charger unique IDs and entity IDs retained.
- Equal-power charging, priority fallback when both minimums do not fit, or
  sequential charging. Priority uses actual Easee device names.
- First priority may yield when disconnected, manually paused, completed or
  outside its schedule. Completed is not a claim about battery percentage.
- Shared sampling and serialized commands. Current reductions must be
  confirmed by fresh subsequent current/power telemetry before increases.
- Invalid/missing site/charger inputs stop automatic commands at zero.
  HAN limit remains 60 seconds; multi-charger power reports require 120 seconds.
- Manual commands reserve their requested capacity before peer increases;
  manual charging otherwise counts as household demand, outside auto policy.
- Phase advice only; phase changes remain user-selected, never automatic SLM
  topology switching. Minimum remains 11 A measured 230 V three-phase, else 6 A.
- Two complete native Manual-card templates (one/two chargers), replacing the
  full-view template. `smart_load_manager.get_dashboard` supplies YAML with
  actual registered IDs and device names, including renamed entities.
- Approved OJM house/tariff-step/charging icon and wordmark packaged locally.
- README License/Checks removed at owner's request; no license chosen or added.
  Donation URL remains pending from the owner.

## Validation

50 pure unit tests (including a matrix of mixed charging forms and budgets),
14 tests using the installed Home Assistant 2026.2.3 Python runtime, module
imports/compilation, JSON and native dashboard YAML validation pass locally.
These runtime tests exercise sensor payloads, shared sampling, command
ordering, cold-start readiness, completed handover, failure handling and
registry-aware dashboard generation. GitHub Actions passed both jobs before publication:
https://github.com/ojm88/smart-load-manager/actions/runs/40378512066

The owner previously confirmed single-charger operation on physical HA/Easee.
New two-charger functionality has NOT been verified with physical chargers.
No claim of full HA startup/service acceptance or physical validation is made
from the unit/runtime mocks. Runtime CI and supervised owner testing remain
separate validation layers.

## Owner test for beta.3

Keep the working YAML automation intact but disabled during SLM automatic
control. Take a backup. Verify first-charger IDs/settings before adding the
second charger. Enable each charger deliberately. Test both allocation modes,
priority change, insufficient capacity, manual pause, unplugging, completion,
and manual phase changes. Generate the two-charger card and replace the old
card. Stop testing and revert control to the original automation if behavior
is unexpected; do not let both controllers write charger limits together.

## Next scope

More than two chargers and controllable resistive loads (hot water/floor heat)
remain future work. The pure kW allocator is separate from Easee telemetry
and commands. No vehicle integration, battery state, learning or automatic
phase switching is introduced. SLM does not replace installation protection.

## Beta.4 requirements recorded

See [BETA4_PLAN.md](BETA4_PLAN.md) for the household-first wizard, initial
one/two-charger selection, future load-type structure and documentation scope.
README installation and current sensor reference drafted locally. Runtime
remains beta.3; setup redesign has not been implemented, tested or released.

Beta.4 additional draft: Marketplace-only user-facing terminology, actionable
missing/disabled Easee sensor errors, and detailed Configure error propagation.
Garage voltage diagnostics need confirmation in the owner installation.

Two targeted HA-runtime regression tests pass: disabled voltage identification
and propagation of the nested Add charger validation message. Fifty pure unit
tests also pass. No physical retry or beta.4 release has taken place.

Owner confirmed that enabling the Garage Voltage sensor resolved setup on
2026-10-26. README, both manuals, first/second-charger setup descriptions and
disabled-sensor errors now explicitly explain this prerequisite for each
charger. This confirms setup only, not physical two-charger allocation.

## Beta.3 live report: stale power, 2026-10-26

Owner logs at 20:38:16 confirm the 120-second peer power guard caused both SLM
entries to become unavailable. Easee devices were online. This does not prove
whether the upstream power report stopped or is only sent on changes.

Beta.4 local draft handles expected input waits without hiding sampled data;
names stale power source and age; holds automatic/paused targets at zero;
keeps pending reduction timestamps stable; resumes after fresh reports and
acknowledgement. A failed zero command still raises an error after attempting
both chargers. Existing single-charger calculations and two-charger allocation
formula are unchanged. Ten targeted site runtime tests pass, including four
new stale/wait/recovery/failed-stop regressions. No physical validation yet.

Still investigate the actual source entity and its last_reported timestamp in
the owner setup. Do not remove/extend the freshness guard based on online
status, or claim that upstream reporting has been fixed. The broader beta.4
setup redesign remains pending.

## Reporting clarification — supersedes draft 120-second policy

Owner confirms Easee power reports on changes/restart. The beta.4 draft now
removes the power age cutoff; unchanged numeric readings remain valid. Missing
power still causes a visible control wait, not a successful allocation.
HAN freshness and new telemetry confirming reductions remain unchanged.
The earlier statement retaining the 120-second guard is superseded.
Eleven targeted site tests cover this behavior, including a two-day-old unchanged
power reading, missing data, recovery and reduction acknowledgement. Upstream
report frequency is owner-confirmed; physical beta.4 testing remains pending.

## Beta.4 compact sensors implemented locally

Seven main sensors per charger; one primary-entry Measurement status diagnostic.
Legacy sensors are instantiated only when previously registered, categorized
as diagnostics with unchanged unique IDs and no forced disabling/removal.
Relevant attributes are attached only to their owner sensor. Both card templates
show compact charger readings and one household group using source entities.
Dashboard generation resolves the actual HAN entity and registered IDs.

Validation: 50 pure unit tests and 25 mocked Home Assistant runtime tests pass.
Includes first/second sensor counts, retained legacy identity/category, attribute
placement and generated card references. No physical validation or beta.4 release.
The household-first setup redesign remains a separate pending beta.4 task.

## Additional beta.4 UI requirements — pending implementation

Owner requests a separate household device for Forbruksgrense/shared diagnostics,
pair-only mode/priority controls, one first-priority/Master selector with derived
complementary per-charger role diagnostics, and Configuration categorization of
phase/scheduling settings. Charger identity must appear in default names/IDs
from the first charger; shared HAN-age information stays household-level.
See BETA4_PLAN.md for dynamic lifecycle tests and existing-ID migration risks.
No runtime changes for this latest feedback have been made yet.

## Beta.4 Configure fix implemented locally

Configure now shows a menu, with household source/margin editing always offered.
Add charger is only offered below two entries. Editing from either entry
updates shared sources on both after validation, preserving charger identities,
options, Forbruksgrense, priority and schedules. Invalid/NaN/unavailable source
checks do not partially update entries. Sources take effect on regular refresh.
Three new targeted HA-runtime tests pass (five options/resolution tests total).

Latest UI proposal is complementary Master toggles, not a visible Master
select. One persisted priority ID backs both roles; separate schedules are
recommended and already supported. Role/grouping/naming implementation and
household-first initial setup remain outstanding; no beta.4 published.

## Current beta.4 household explanation implementation

The latest local change supersedes the seven-sensor layout: five main charger
measurements, one household Status for laststyring (`sensor.slm_status`) and one
Measurement status diagnostic. Household information and Forbruksgrense/shared
selectors attach to a separate SLM – Boligen device. Both Markdown templates
read only shared summary/controlled_loads attributes. Existing registered
information sensors remain compatibility diagnostics. Control decisions/math
are unchanged by this presenter; graph inputs remain direct sources.

ARCHITECTURE.md documents the single explanation contract and extension path
for future load adapters. Current support is still EV-only. Complete shared
snapshots are saved before publishing peer updates; single mode reads live
coordinator data. Pending peers appear explicitly in household explanations.

Validation: 56 pure tests and 31 HA-runtime mock tests pass, including plain
language states/advice, non-mutation, shared snapshot, household device links,
legacy sensors, compact counts and Markdown rendered solely from site status.
No physical validation or beta.4 publication. Remaining work: initial wizard,
master toggles and role UI, conditional pair-control lifecycle and ID naming
migration. Shared settings storage still uses the primary entry; a household
with only thermal loads is not yet implemented.
