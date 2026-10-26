# Smart Load Manager OJM — project status

Updated: 2026-10-26

## Release

Stable: 0.1.0. Last published beta: 0.1.1-beta.2.
Preparing 0.1.1-beta.3 for the owner's requested two-charger test.

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
registry-aware dashboard generation. GitHub Actions must pass before release.

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
