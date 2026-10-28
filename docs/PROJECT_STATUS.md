# Smart Load Manager OJM — current project status

Updated: 2026-10-28

## Version

- Stable: **0.1.0**.
- Published beta: **0.1.1-beta.11** ([release](https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.11)).
- Release code: `e5951112d85a7eb257344aefeb8b393b1c1ef167`; merged PR #7.
- GitHub Actions [40639534986](https://github.com/ojm88/smart-load-manager/actions/runs/40639534986) and [40639529486](https://github.com/ojm88/smart-load-manager/actions/runs/40639529486) passed all four jobs for release-preparation head 5dd6dd6bb3ce36591465fda6e27a433a6b21a2f8. Published as a prerelease after explicit owner approval.

## Published beta.6 corrections

Owner tested beta.5 configuration: grouping is approved, but device selection is slow; selecting only a new charger in the replacement-list form retires the first charger, disables its entities, and can leave household status unavailable.

Root causes addressed: the form replaced membership instead of adding; unload traversed the edited config rather than the old runtime, leaving removed controllers registered; detached adapters then lost their saved record. Compact indexed Easee choices replace the frontend's global device picker. First setup now selects one charger, then optionally adds a second with the first excluded. Configure exposes explicit additive add and explicit remove.

**0.1.1-beta.6** is published. It retains both groups and all calculation/allocation formulas. Existing retired loads can be re-added with their saved identities/settings; explicit user-disabled entities are respected. It does not automatically restore deliberately removed loads.

Validation: **56 pure tests** and **46 runtime tests** pass locally, the runtime suite on both HA **2026.2.3** and **2026.10.4**. Added real native setup/add/reload/remove/re-add and full FlowManager first/second/cancel/finish tests. Source/telemetry are synthetic; no physical charger was contacted and no phone frontend timing was measured. GitHub Actions [40503153067](https://github.com/ojm88/smart-load-manager/actions/runs/40503153067) passed all three jobs for code commit `900304213a600878be2f86a237817f19e693bb34`: pure tests plus both HA runtimes.

## Implemented in beta 5

- One installation config entry with native **Household / Boligen** and **Charging / Lading** subentries. The household device no longer sits under the first charger. Both charger devices share the charging group.
- Household-first setup, then supported load type and one/two Easee selection. Planned hot-water/floor-heating information cannot create a thermal controller. Cancellation or failed validation before completion creates no controlling partial entry.
- Beta.4 upgrade consolidates existing entries and transfers registry ownership before removing the redundant entry. Original per-load IDs, unique entity IDs, options and customizations are retained. Shared budget/options are installation-owned and survive removal of the original first charger.
- Complementary first-priority switches backed by a single saved priority; read-only priority diagnostics. Distribution and priority controls appear only with two configured chargers. Existing priority selectors remain compatibility diagnostics.
- Six main measurements per charger, including visible voltage. Function-first display names and consistent saved charger-name suffixes from the first charger. Custom IDs/names are respected; collisions never take over another entity. An old/new ID map is persisted and exposed on Measurement status. Arbitrary external YAML/automations are not rewritten.
- Add/remove chargers through Configure, preserving independent schedules. Removing a charger sends a 0 A command first; failed commands abort configuration changes. Success is a service acknowledgement, not physical stop confirmation. Configuration reload leaves automatic control off. Removed-load identities/settings are retained for later re-addition.
- Central household explanation, stale/change-based power handling and reduction acknowledgement behavior from beta.4 remain. Electrical calculations, control helpers, budget conversion and allocation formulas are unchanged.
- Short current README, aligned Norwegian/English guides and both static/packaged dashboard templates. `get_dashboard` resolves current registered IDs.
- Minimum supported HA version is now declared as 2026.2, the runtime used for acceptance tests.

## Software validation

- **56 pure regression tests** pass.
- **46 runtime tests on HA 2026.2.3 and 2026.10.4** pass, including real device/entity registries, config-entry migration, concurrent old-entry startup, native platform setup/unload, grouped entity registration and translated names. Synthetic telemetry and mocked Easee resolution are used; no real charger is contacted.
- Existing two-charger control regressions cover reduction-before-increase, new telemetry acknowledgements, missing data, recovery and unchanged power readings.
- Native HA startup also exercises the real coordinators against synthetic electrical/HAN measurements, automatic control off.
- Compilation, JSON/YAML validation and patch whitespace checks pass locally. GitHub Actions push workflow [40478887739](https://github.com/ojm88/smart-load-manager/actions/runs/40478887739) passed both jobs for code commit `2880f27d3307cf4135354a65c9d6f8e3827a0a32`.
- `calculations.py`, `control.py` and `budget.py` are identical between beta.2 and beta.4 and remain unchanged in beta.5. `allocation.py` is unchanged from beta.4. Coordinator changes adapt storage/load enumeration rather than rewrite the calculation.

## Owner validation

Owner confirms beta.2 worked with one physical charger. Beta.4 starts with two chargers; physical charging has not yet been tested. Owner has now tested beta.5 setup and reported the membership/reload failures above; physical charging is not confirmed. Recorder history continuity has not been separately integration-tested; registry unique IDs are preserved and only generated object IDs are renamed.

Before installing beta.6, take a full backup. Check migration, one budget, both grouping blocks, names, voltage readings and own customizations. Generate a new dashboard card, update external YAML references from the ID map, then deliberately enable automatic control. Test one charger, both distribution modes, first-priority changes, each schedule, pause, disconnect, completion and insufficient capacity.

Restoring beta.4 after schema migration requires restoring the backup. Do not run the old automation and SLM on the same chargers simultaneously.

## Future work

Live acceptance of beta.6; more than two chargers; supported hot-water tanks; floor-heating zones through Versatile Thermostat; donation account/link. Thermal control, vehicle battery integration, learning and automatic topology switching are not implemented.


## Logo picker experiment (not released)

The owner confirms the beta.6 setup menu renders correctly in Safari; Companion showed stale/missing strings. Both chargers and household status appeared in the owner's recording. This is setup/UI acceptance, not physical charging acceptance.

Branch `experiment-integration-logo-picker` adds an optional read-only custom panel under `experiments/logo-picker`. It compares a plain dropdown with HA's native logo-bearing device picker, using an exact allowed-ID predicate and a transient first/second flow. It never starts a real config flow, saves membership, or sends commands. Beta.6 code/version remain unchanged. Syntax and candidate-filter checks are local; browser rendering, logos, phone latency and applicability to the native setup dialog are unverified. This initial experiment was subsequently packaged and published in beta.7; see below. VT support is not implemented.


## Beta.7 packaging (published)

Owner requests an installable beta instead of manual test-panel files. The integration now packages the read-only module and registers the admin-only SLM velgertest panel automatically when HA frontend is enabled. Normal compact setup, memberships and charging math remain unchanged. Static route is registered once, panel removed on last runtime unload, and reload re-registers it. Beta.7 is published after the owner's request to package the experiment as a beta. Phone rendering and performance acceptance are still pending.

Beta.7 validation: **106 distinct automated tests** pass: 56 pure tests, 49 HA runtime tests (run locally and in CI on both HA 2026.2.3 and 2026.10.4), and one Node candidate-filter test. JavaScript syntax, packaged/source module equality, Python lint, JSON and whitespace checks pass. No live charger command or actual browser logo/latency test was performed.


## Beta.8 logo-flow prototype (published)

Owner verified the beta.7 read-only logo picker was responsive and displayed Easee branding. A new opt-in native external-step bridge now connects the picker to initial setup and additive options setup. The default compact paths remain available. A hidden admin-only HA panel and authenticated admin API serve a short-lived, flow-bound session; source IDs are filtered and validated again, duplicate/stale selections rejected, cancellation cleans sessions, and replay is rejected. No membership is saved until the original native flow finishes. Full UI popup/return/cancellation acceptance in Safari and Companion is pending. Beta.8 is published after explicit owner approval. VT control and VT logo acceptance are not implemented.


## Beta.8 sidebar and documentation cleanup

Automatic SLM velgertest sidebar registration is removed at the owner's request. The setup logo picker is still hidden and available only through the opt-in flow. README follows a concise project presentation inspired by merkens/ha-xcomfort-bridge, with a support/limitations section and links to both guides. CI [40534718962](https://github.com/ojm88/smart-load-manager/actions/runs/40534718962) passed all four jobs for prototype commit a5734306062045d29fb21f73d54f7733671289e0. This revision changes sidebar registration/documentation only; new CI is required. Beta.8 is published; physical charging and Safari/Companion flow-return validation remain pending.


README review: remove the frontend experiment paragraph from the project introduction. Restore explicit Settings → Tools → Actions dashboard generation, a sensor meaning table, the required EnergyTariff dependency, Norwegian grid/capacity context with Glitre Nett/NVE source links, and guidance on realistic whole-home hourly targets. No control behavior changes in this revision.


## Presentation baseline and stable release direction

Owner accepts the README structure and requests a documentation/structure freeze except for agreed features and necessary fixes. Clarified when generated dashboard YAML must be replaced, and added ROADMAP.md. Stable 2.0.0 is planned after successful two-charger charging tests, including retained one-charger behavior and no blocking setup/control faults. No physical acceptance, publication date or stable release approval is implied.


## Approved beta.8 publication

Published 0.1.1-beta.8 from merge commit 8b5a88821fc2955d915d9003b07bde1c3c0128da after owner approval. All 110 distinct automated tests pass (56 pure, 53 HA runtime and one Node test); runtime suites run against HA 2026.2.3 and 2026.10.4. Release is a prerelease. Physical charging and actual external-step navigation/return in Safari/Companion remain unconfirmed. Stable 2.0.0 remains conditional on acceptance; the agreed presentation baseline stays frozen except for agreed features, required fixes and release/validation status.


## Beta.9 setup correction (published)

Owner reports a blank third menu choice and an external-step message with no open button. The bridge supplied a relative URL, which HA's frontend URL sanitizer rejects. The extra choice is removed: normal charging/add actions now open the branded picker. Absolute URLs are resolved with HA's current-request helper, falling back to configured external/Cloud URLs; missing URLs retain compact setup. External refresh retains the existing session. Existing translation step IDs are reused, avoiding dependence on a new menu translation cached by the client.

The setup page now renders a small filtered list with authenticated HA integration brand images, falling back to the brands CDN on older HA versions. It does not depend on cold-loading ha-form/ha-device-picker in a separate tab. Candidate eligibility, additive saves, cancellation and server-side validation remain unchanged. Calculation/control/budget/allocation files are untouched.

Validation: 56 pure tests, 55 HA runtime tests on HA 2026.10.4, and six Node tests (including five DOM interaction regressions). Actual Safari/Companion rendering/navigation and physical charging remain unverified. Browser installation was unavailable in this environment; DOM tests are not visual browser acceptance. The owner has approved publication as beta.9. CI run 40570428801 passed all four jobs for f1984e34171b0682317247cf220176cc64d37e13, including runtime tests on HA 2026.2.3 and 2026.10.4. The release preparation changes only the version and release documentation. Publication and installation on the owner's HA are separate steps.


## Approved beta.9 publication

Published 0.1.1-beta.9 from merge commit 8313556a0f81a23e546444863f72a2fcbdce54be after owner approval. Verified release draft=false, prerelease=true and tag points to the merge commit. All 117 distinct tests pass (56 pure, 55 runtime and six Node tests), with runtime suites on HA 2026.2.3 and 2026.10.4. Phone UI/navigation and physical charging acceptance remain pending. Stable 0.1.0 and all earlier tags remain unchanged.


## Native in-app setup correction (not released)

Owner tested beta.9 and confirms the external logo step leaves iOS Companion for Safari. This violates the requirement to keep the whole setup in the app; seeing the custom page and images does not constitute acceptance of that flow. HA renders external-step links with target=_blank. The fast SelectSelector schema supports value/label pairs, not image options; the supported DeviceSelector does not expose exact selected-device exclusions.

Restore the native compact name dropdown for initial and additive setup, including when an external/Cloud URL is configured. Remove external-step handlers, the hidden setup panel/API bridge and its frontend module. No sidebar page is registered. Preserve indexed options, first/second exclusion, saved records/options, grouping and all calculation/control/allocation files. Keep the unregistered read-only comparison experiment separate from setup.

Validation: 56 pure tests, 51 HA runtime tests on HA 2026.10.4, and one existing Node experiment test pass locally. New real FlowManager regressions configure a Cloud URL, fail on any external-step call, and complete initial two-charger setup and additive second-charger setup entirely with native forms/menus. Actual Companion acceptance and physical charging remain separate. No new release has been published or installed.


## Approved beta.10 native logo selector

Owner explicitly requests publication of a new in-Companion logo solution and will test responsiveness. The unshipped text-only correction is superseded by HA's supported DeviceSelector. Research of HA frontend 20260128.6 (HA 2026.2.3) and 20260930.5 (HA 2026.10.4) confirms the multi-device add picker excludes current values. Initial selection is single-device; second/add forms preselect the existing source and permit exactly one new source on the server. Removing/replacing the existing selection is rejected; use the explicit remove action. Native forms/menus never call an external step, even with a Cloud URL.

Manufacturer/model filters are derived from Easee's indexed devices, avoiding ha-selector-device's additional getDeviceIntegrationLookup path when metadata is complete. The native picker still performs its own normal HA registry/config-entry work and branding requests. Missing manufacturer metadata uses the supported Easee integration filter. Presentation filters are not source authorization: all submitted IDs are validated against enabled Easee registry membership and electrical inputs before saving. Similar-model devices from other integrations, duplicate/replacement/excess additions are rejected. No sensor probes run on form creation and no charging math changes.

Sources reviewed: home-assistant/frontend src/components/ha-selector/ha-selector-device.ts, src/components/device/ha-devices-picker.ts, src/components/device/ha-device-picker.ts and src/data/device/device_registry.ts; core helpers/selector.py. No injected frontend module or sidebar page is used for setup.

Local validation: 56 pure tests, 55 HA runtime tests on HA 2026.10.4 and one Node test. Runtime tests exercise actual flow managers and serialized native selector defaults, plus configured Cloud URLs without external calls. Both HA runtimes are checked in CI before publication. Native logo appearance and responsiveness in the actual iOS app, and physical charging, remain owner acceptance tasks.


## Beta.10 publication verified

Published 0.1.1-beta.10 as a prerelease from merge commit 7c85400f0bc19c5b53d613e703f75b69647cd584 after the owner's explicit request. Verified tag/manifest version and draft=false, prerelease=true. All 112 distinct tests pass (56 pure, 55 runtime and one Node test); CI covers HA 2026.2.3 and 2026.10.4. Native branding appearance, responsiveness and actual Companion acceptance are for owner testing, as agreed; physical charging remains unconfirmed. Stable 0.1.0 and earlier tags are unchanged.


## Beta.11 electrical connection correction (published)

Owner confirms beta.10 installation works without slow setup on a third HA gateway. This is setup acceptance, not charging acceptance. The 230 V three-phase charger is incorrectly shown as 406 V because the old inference takes the average of 403/409 V on unrelated terminal pairs. Captures of a TN supply and two more 230 V chargers establish why neither voltage state, populated pair count nor configured phase mode proves physical wiring.

Owner approves explicit physical wiring per charger with four choices. Native first/second/add forms now require it; Configure → Chargers → Charger connections allows existing installations to confirm/edit it. Single/unknown wiring hides phase control, including registry lifecycle and generated YAML; direct phase-selector writes are rejected. Electrical calculation uses relevant measured terminal pairs, preserves single/three-phase TN behavior, handles IT current on T2, and fails closed for missing/conflicting input without cached-factor recovery. Shared budget/allocation, logo picker, schedules and identity preservation remain intact.

Local validation: **129 distinct tests pass** — 66 pure tests, 62 HA runtime tests (each run on HA 2026.2.3/Python 3.13 and HA 2026.10.4/Python 3.14), and one Node selector regression. Compilation, JSON, YAML and translation checks pass. Runtime regressions cover native initial/add/edit flows, single-phase selector hiding/restoration, preserved user disables/peer settings, failed-stop atomicity, generated cards and missing-connection calculation rejection. At that preparation stage no beta.11 release, live charger command or phone acceptance had occurred; publication is recorded below. GitHub CI results are recorded on the proposed pull request; local results above do not establish physical acceptance. Required acceptance: choose actual wiring on every existing charger, regenerate YAML, verify volts against the selected path, test one-/three-phase TN and IT charging, single-phase control absence and two-charger distribution. Never present these software tests as physical acceptance.


## Approved beta.11 publication preparation

On 2026-10-28 the owner explicitly requests publication of beta.11. PR #7 code head 6a9323ece2b062f8723bae0dae24c0c37644b6d1 passed all four CI jobs in runs [40596346688](https://github.com/ojm88/smart-load-manager/actions/runs/40596346688) and [40596306879](https://github.com/ojm88/smart-load-manager/actions/runs/40596306879). This preparation changes release documentation only; version 0.1.1-beta.11 is already present in the tested manifest. Publication is recorded separately after the release and tag are verified. No physical charging or beta.11 phone acceptance is claimed.


## Beta.11 publication verified

Published 0.1.1-beta.11 on 2026-10-28 from merge commit e5951112d85a7eb257344aefeb8b393b1c1ef167 after explicit owner approval. Verified draft=false, prerelease=true, tag and target commit match, and manifest version is 0.1.1-beta.11. Release-preparation CI passed all four jobs on both push and PR; 129 distinct software tests cover pure calculations, both supported HA runtimes and the selector regression. Stable 0.1.0 and earlier tags remain unchanged.

After installation, restart HA, confirm physical wiring separately for each existing charger under Configure → Chargers → Charger connections, regenerate dashboard YAML, inspect measured voltages and deliberately enable automatic control. No physical beta.11 charging or new phone setup acceptance is claimed.
