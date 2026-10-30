# Beta.18 — quiet completion verification

Release preparation authorized 2026-10-30. Manifest 0.1.1-beta.18; publication verification pending. No HA installation or physical control performed.

Owner accepts testing this bounded correction as beta.18. It does not resolve every measurement-status wait with change-based HAN sources. A further ten-minute read-only observation (61 snapshots, 35 entities) showed ready throughout, matching raw/template power and observed power age at most 59.9 s; the car was disconnected. This did not reproduce or close the general freshness issue. Private observations are not committed.

## Preserved behavior and bounded change

Live calculation, ordinary 300 s dispatch, risk reductions, active-input safety,
explicit pause/schedule controls and measured paired reduction remain. Raw Easee
status is never replaced or pinned. No user MQTT or template changes are made.

Completed alone requests no increase. Normal automatic completed targets may
hold or fall for real budget/peer constraints, but do not bounce upward on later
ticks. Reopened user permission and source waiting/ready states may reassess and
restore current with valid inputs. Actual charging returns to active allocation.

A stale HAN value alone preserves a known offer only when all numeric/electrical/
tariff/peer-power inputs are valid and the automatic completed charger reports
zero W, less than 1 A standby, no pause, open schedule and no lower physical cap.
No increase/new allocation uses stale data. Active peers stop once; actual wake,
positive draw, real invalid source/peer input or explicit stop removes the idle
exception. The existing 120 s active guard is retained, not changed to 180 s.
Keeping an idle offer allows the car to wake; the next source/draw assessment
must enforce the active guard if HAN is still stale. This physical transition
latency still requires hardware acceptance.

Measurement status remains waiting during stale input. Diagnostic hold flags
explain why the ended charger was left untouched; do not claim ready/fresh.
Command traces now use the actual serialized cycle sample, fixing the earlier
old-context discrepancy at 0 A and recovery commands. Privacy allowlisting stays.

## Software evidence

- 93 pure tests pass.
- 133 runtime tests pass on HA 2026.10.4/Python 3.14 and HA 2026.2.3/Python 3.13.
- One Node test, compileall and diff whitespace checks pass.
- Both new quiet-age/recovery feedback and non-restoration regressions fail
  against the published beta.17 site implementation, and pass against this code.
- A real HA sampler/site regression retains fresh-identical report coverage,
  then checks age-only completed hold, actual wake safe stop and immediate valid
  input recovery. Output commands are mocked; this is not a physical charger run.
- Sequence tests cover two chargers (idle offer retained, active peer stopped),
  positive power or >=1 A despite completed, invalid HAN/tariff/electrical/power,
  physical current cap, pause and schedule closure. Existing paired ACK, source
  timing and permission restart suites pass unchanged.

## Remaining acceptance

Owner: overnight completed without SLM-induced pause/restart; raise target in car
app; explicit pause/schedule restart; two chargers with capacity transfer and
input fault/recovery. Necessary control/budget/fault commands may legitimately
change raw Easee status. No promise of immutable status or 100 percent hardware
stability follows from these software checks. The test only resolves the bounded
ended-session problem; active change-based-source liveness is not generally
proved by a value timestamp.
