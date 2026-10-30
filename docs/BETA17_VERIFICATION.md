# Beta.17 — refined offer policy verification

Reviewed 2026-10-30. Published release remains beta.16. No beta.17 publication or
physical charger test has occurred. This record supersedes the earlier proposal
to classify the origin of completed→waiting feedback.

## Final policy

A positive current limit is an offer, not a forced charging session. Keep the
known positive offer after completed when the live budget permits. An unknown or
zero prior offer must not become a permanent zero ceiling: allow the validated
electrical minimum as a standby offer. Never invent a nominal current if the
electrical minimum is missing. Count the whole possible draw in reserved capacity.

Allocate active sessions first. Ended sessions use only remaining budget; in
one-at-a-time mode they receive no standby allowance while an active allocation
exists. If required budget/data/schedule/pause conditions demand zero, send the
stop once after success. Re-offer when the current budget and permissions allow.

completed→awaiting/ready triggers immediate reassessment but preserves standby
priority. The resulting budgeted target is independent of whether the car or a
previous SLM command caused the transition. Only actual start_charging/charging
returns the session to normal active allocation; measured paired reduction still
precedes any peer increase. Identical targets are not resent. A no-change status
assessment does not postpone the ordinary five-minute deadline.

If a car increases its SOC target while it already has an offer, no extra SLM
start command is necessary. If its offer is zero, a source transition triggers
immediate assessment; no capacity means it remains waiting legitimately. With no
new source transition, normal regulation still reassesses idle capacity, and
measurement/schedule recovery retain their immediate checks. No repeated blind
start/stop probes are used to discover the car's SOC.

## Software evidence

92 pure tests, 129 runtime tests on HA 2026.2.3/Python 3.13 and HA
2026.10.4/Python 3.14 pass. The zero-offer recovery regression fails against the
previous policy and passes against this correction. Existing tests also cover
both allocation modes, preserving active-peer priority, measured reduction before
increase, source ordering, budget reduction/recovery, pause and schedule, failed
commands, fresh-identical HAN and stale-input recovery.

New sequence assertions: complete at zero → repeated waiting/ready/completed
while budget insufficient (no writes) → budget becomes available plus source
transition (one minimum offer) → repeated idle feedback (no further writes/no
deadline movement) → charging (normal active target). Retained-positive offer
permits waiting/ready without needless commands, then active allocation on start.

## Physical acceptance boundary

Need owner test: charge to target → raise target in car app → restart; overnight
quiet completion; household stop/recovery; two chargers. Software validation proves
command policy for these simulated sequences, not hardware latency or an absolute
guarantee of immutable raw Easee status. All real output commands in tests are
mocks. Actual charging-status correctness remains based on Easee reports.

Primary contract: https://developer.easee.com/docs/enumerations. Waiting statuses
do not identify their origin; this policy does not depend on that distinction.
