# SLM regression matrix

Run the full automated suite on every functional PR. Use this matrix to decide
what additional cases the change needs. Verify the prior behavior on the same
inputs where the change is expected to preserve it.

| Area | Scenarios to exercise | Evidence in CI |
| --- | --- | --- |
| Installation | One and two chargers, each supported IT/TT and TN wiring choice, mixed connections, add/remove/re-add, reload, interrupted setup, stable entity IDs and saved options | Connection, resolution, installation and membership tests |
| Controls and timing | Automatic and manual, pause/resume, schedule open/close without a sensor event, hour rollover, deadline using latest available readings, unplug/replug, completion and renewed request | Control, regulation and site runtime tests |
| Limits and allocation | No capacity, below/at/above minimum, charger and circuit ceilings, priority, both distribution modes, an idle peer, active peer reduction before increase, hidden demand caps and relearning after a session | Allocation, budget, power reservation and site runtime tests |
| Measurements and service feedback | Valid, stale, missing and invalid HAN, energy and charger inputs, optional estimate unavailable, unknown or conflicting Easee state, delayed/reordered feedback, command failure and recovery | Live telemetry, estimate source, site and diagnostics tests |
| Status card | Each load shows its own cause. Cover schedule in both modes, pause, budget, peer handover, pending adjustment, sent offer, source/wiring errors, Easee/Equalizer wait, offline, disconnected, completed and active charging. Show a next action or time only when supported by the state. | Household status and dashboard rendering tests |

For changed behavior, test the transition into the state, repeated updates
while it persists and recovery when its blocker clears. Include coincident
events when order matters. Check the command and its acknowledgement separately
from the live recommendation and physical draw.

Keep one brief explanation per charger. Retain the meaningful reason when the
view is refreshed and remove it when it no longer applies. Render both dashboard
layouts when shared presentation changes. Record actual phone and physical
charger checks separately from simulations. List gaps in the PR and release
notes so that software test coverage does not imply hardware acceptance.
