# Beta.19 — release completed capacity

Owner authorizes tests and publication, 2026-10-30. Manifest 0.1.1-beta.19.

## Contract

A known automatic completed session at exactly zero W and below 1 A standby,
with valid inputs, open schedule, no pause and no lower physical current cap,
leaves allocation and held-offer forecast. It receives no ordinary capacity
command, even when available capacity is below minimum or the hourly budget is
exhausted. Its last physical current limit remains unchanged. The other charger
may use the released capacity immediately without an artificial zero/ACK cycle
for the already measured completed charger.

A new awaiting_start/ready_to_charge request triggers immediate allocation at the
validated electrical minimum, subject to current measurements, capacity, chosen
priority and measured reductions on active peers. Actual charging/start clears
completion memory and restores normal allocation immediately. Repeated same
states/limits do not resend commands. Explicit renewed user permission can
reassess a completed session. Existing pause/schedule closure, real missing
measurements, active HAN timeout and physical cap enforcement remain. Beta.18's
age-only completed hold is retained; measurement status is not forced ready.

Owner accepts that a vehicle can draw the retained physical limit before delayed
Easee feedback reaches SLM. The hourly margin is kWh, not an instantaneous power
reserve or guaranteed reaction-time cover. Neither the code nor these tests
claims otherwise. No new direct car API, MQTT setting or heartbeat is required.

## Evidence

- 93 pure tests, 135 runtime tests on each HA 2026.10.4/Python 3.14 and
  HA 2026.2.3/Python 3.13, plus one Node test; compileall/diff checks pass.
- Two behavior regressions fail against published beta.18, pass with beta.19:
  completed at 16 A / 0 W with less than 6 A capacity gets no pause command;
  completed peer capacity is released without writing zero to it.
- The first regression reproduces the owner's numeric budget situation with
  generalized test adapters, advances ordinary/urgent timer paths through six
  simulated hours, then verifies capacity-denied wake and immediate minimum
  restart on a later valid request. Private trace/installation IDs are absent.
- Other sequences cover delayed positive power after completed, fresh/stale HAN
  recovery, one/two chargers, both distribution modes, new-request priority,
  minimum startup, actual-draw reallocation, explicit pause/resume/schedule,
  invalid inputs and physical caps. Paired active-transfer acknowledgements stay.
- Diagnostics expose completion_released, completed_capacity_released and
  completed_control_resumed. The native measurement sensor adds a release flag.
  Existing cards are compatible; no YAML regeneration is required.

## Acceptance still required

No HA installation or real command performed in this preparation. Physical
completion without later ordinary writes, car-app target increase, delayed
source feedback and two-charger wake/transfer require owner acceptance. This
change does not universally solve change-based HAN freshness waits.
