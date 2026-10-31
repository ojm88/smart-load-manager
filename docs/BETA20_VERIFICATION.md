# Beta 20 preparation — 2026-10-31

Not published. Manifest remains beta 19 until release preparation.

## Scope

Persist per-load automatic enablement, restore desired manual requests through existing guards, and enforce actual minimum current for the manual number. Category state derives from saved members. Existing schedule enable/time, pause, manual current and shared budget/allocation/priority use persistent entry options. Phase configuration belongs to Easee, not a resettable SLM cache. Explicit rewiring/removal durably disables the affected load; ordinary reload preserves it. No completion/wake-policy changes.

Beta 19 did not store automation enablement. The first update therefore needs one activation; subsequent restart/update preserves it. Unknown limits disable manual input, without inventing a minimum. Internal zero-current stop commands remain available. Existing dashboard YAML remains compatible.

## Verification

- 93 pure tests pass.
- 139 runtime tests pass on HA 2026.10.4/Python 3.14.8 and HA 2026.2.3/Python 3.13. Actual native platform setup and integration reload use synthetic telemetry, mocked outgoing charger calls and a mixed two-charger configuration; saved options and native number minimum survive reload.
- New coordinator recreation test covers saved automatic on/off, pause, schedule/time and manual selection, without restoring command acknowledgement.
- Restored manual input waits for valid measurements and resumes on recovery. Number rejects zero, negative, fractional/below-minimum, non-finite and unknown-limit requests; 6 A and 11 A minima covered. Valid minimum remains selectable and the separate pause still sends 0 A.
- Two new regressions fail against beta 19 source: missing saved automation flag and number minimum of zero.
- One Node probe test passes; Python compilation and diff whitespace check pass.

No production HA restart, firmware update, phone slider rendering or physical charging was performed. Software persistence uses HA ConfigEntry options; the runtime test verifies integration reload, not a physical HA host restart. User's ongoing car-app restart test is separate and remains unresolved without diagnostics covering the failed attempt.
