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
