# Instructions for Codex

Before changing this project, read `README.md`, `docs/PROJECT_STATUS.md`, and
`docs/DECISIONS.md`.

Keep `docs/PROJECT_STATUS.md` current when the beta, validation state, or next
steps change. Add durable product and technical choices to `docs/DECISIONS.md`.
Update `CHANGELOG.md` for user-visible changes and keep both manuals aligned
with the implemented behavior.

Do not present a feature as tested on physical hardware unless the user has
confirmed that test. Clearly distinguish unit tests, Home Assistant startup
validation, service-call validation, and live charger testing. Keep automatic
charger control opt-in and fail safely when required meter or electrical data
is missing or stale.

Do not add installation-specific entity IDs, device IDs, site names, tokens, or
credentials to the integration. Resolve entities through Home Assistant's
device/entity registry and configuration flow.

## Lessons from beta.1–15

Read `docs/RETROSPECTIVE_BETA1_15.md` before planning charging, configuration,
or dashboard changes. Apply its relevant scenario matrix, not a blanket
requirement to run every test for cosmetic/internal documentation changes.

Before implementation, identify the user's full journey, the working behavior
to preserve, uncertain source semantics and the impact of outgoing commands on
subsequent feedback. Do not infer wiring from ambiguous voltage pairs or treat
completed as a pause instruction. Resolve material uncertainty from primary
HA/Easee sources or ask a focused question when evidence cannot resolve it.

Choose regression tests from expected behavior and failure sequences, not just
assertions mirroring the implementation. For control changes consider source
ordering, timers without source events, command feedback loops, wake/reuse and
one/two-charger interactions. For UI changes inspect rendered normal, empty,
waiting/completed and high-value states at phone widths. Structural template
tests alone do not establish actual iPhone rendering.

Report what is established by source inspection, synthetic tests, actual HA,
phone UI and physical charging separately. Test count is coverage context,
not a reliability claim. Keep release records internally consistent and batch
related agreed fixes where useful; do not ask for additional approval for
routine authorized work or publish a new beta merely to validate an assumption.
