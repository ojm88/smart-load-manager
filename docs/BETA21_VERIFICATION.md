# Beta 21 verification — preparation, 2026-11-01

Not published. Manifest remains beta 20. No production HA modifications or physical charger commands performed.

## Reproduction and scope

First paired beta 20 installation: positive calculated targets never reach Easee while zero pause commands do. At 17:36:09 local a pause sends zero; at 17:36:21 pause is removed but a positive target remains blocked. Manual 14 A target is likewise blocked later. At 17:55:01 direct Easee 18 A call is accepted, followed by charging. Retained SLM trace ends at 17:56:02 with both pending flags and one disconnected zero-draw load. Raw uploaded files and identities are not committed.

Actual paired apply code reproduces the global gate for 100 assessments until the unused peer republishes its unchanged zeros. New regressions preserve old current/power timestamps. Valid idle zero-draw samples require no release of measured load; active transfers still need post-command measurements. No timeout, fabricated freshness or unconditional bypass is introduced.

## Validation

- 93 pure tests pass.
- 154 runtime tests pass on HA 2026.10.4/Python 3.14.8 and HA 2026.2.3/Python 3.13.16.
- Four new regressions fail against beta 20: unused peer blocking automatic start; manual and pause/resume; two waiting-car takeover; actual coordinator-control flow with an unused peer.
- Actual coordinator test uses real Home Assistant state objects, separate charger sources and mocked outgoing commands: start, pause, resume, auto-off minimum, manual 12 A and plugging the second charger work without republishing its zero measurements.
- Active-transfer regression still blocks increases on old low measurements while status remains charging, then proceeds only after post-command current and power reports. Existing paired ordering, lower-budget, faults, source recovery, persistence, Completed and single-charger regressions pass.
- Invalid/unknown, positive power and >=1 A samples cannot use the idle exception. No repeat writes for unchanged limits. Diagnostic download covers pending limit/age; transition events record why a wait starts or clears.
- One Node test, Python compilation and whitespace checks pass. Two older platform test fixtures now implement the coordinator pause capability to avoid unrelated fixture errors during native setup.

## Remaining physical acceptance

One and two connected cars, both charger roles, automatic/manual combinations, pause/resume, normal capacity sharing, constrained handover and overnight completion need user acceptance on hardware. Tests prove these code paths with synthetic sources, not compatibility with every source-ordering pattern or all Easee installations. Existing dashboard YAML remains compatible.


## Setup and dashboard refinements

Initial native device selection is retained. Second/add forms use one explicit unused-device SelectSelector: no preselected membership, no configured-device option and no extra selection slot. Backend guards reject duplicate/multi-add input and third-charger step re-entry. Actual HA flow tests verify initial setup, options addition, serialization in the native cloud URL flow, preserved identities, duplicate rejection and two-charger cap. Missing-current setup returns a localized missing_measurements error; current/voltage disabled-source tests cover nb/en instructions and actual source entity IDs.

One-/two-charger templates wrap the two controls independently in native conditional entity rows excluding unknown/unavailable. Generated card tests verify real/renamed entity IDs are replaced in both conditions and nested rows. Existing source-only Markdown, phone-width formatting data, phase-row removal and allocation controls remain covered. Native conditional-row syntax follows https://www.home-assistant.io/dashboards/entities/#conditional. No live browser/iPhone rendering was performed; physical acceptance remains pending. Regenerate get_dashboard YAML after updating to get hiding behavior; old copied cards do not change automatically.

Three new UI/setup regressions fail against the preceding preparation: unused-only single picker, second-step third-slot re-entry, and conditional pause/manual rows. Number availability also follows schedule, HAN freshness and required input validity, so the row hides when a manual positive limit cannot be applied.
