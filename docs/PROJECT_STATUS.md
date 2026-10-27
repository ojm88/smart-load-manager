# Smart Load Manager OJM — current project status

Updated: 2026-10-27

## Version

- Stable: **0.1.0**.
- Published beta: **0.1.1-beta.7** ([release](https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.7)).
- Release code: `c1a43b681aca0891d986a0a83b57154ff0361209`; merged PR #3.
- GitHub Actions [40524396170](https://github.com/ojm88/smart-load-manager/actions/runs/40524396170) passed all four jobs for the merged PR head. Published as a prerelease after owner approval.

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


## Prepared beta.8 logo-flow prototype

Owner verified the beta.7 read-only logo picker was responsive and displayed Easee branding. A new opt-in native external-step bridge now connects the picker to initial setup and additive options setup. The default compact paths remain available. A hidden admin-only HA panel and authenticated admin API serve a short-lived, flow-bound session; source IDs are filtered and validated again, duplicate/stale selections rejected, cancellation cleans sessions, and replay is rejected. No membership is saved until the original native flow finishes. Full UI popup/return/cancellation acceptance in Safari and Companion is pending. Beta.8 is not published. VT control and VT logo acceptance are not implemented.


## Beta.8 sidebar and documentation cleanup

Automatic SLM velgertest sidebar registration is removed at the owner's request. The setup logo picker is still hidden and available only through the opt-in flow. README follows a concise project presentation inspired by merkens/ha-xcomfort-bridge, with a support/limitations section and links to both guides. CI [40534718962](https://github.com/ojm88/smart-load-manager/actions/runs/40534718962) passed all four jobs for prototype commit a5734306062045d29fb21f73d54f7733671289e0. This revision changes sidebar registration/documentation only; new CI is required. Beta.8 is still unpublished, with physical charging and Safari/Companion flow-return validation pending.


README review: remove the frontend experiment paragraph from the project introduction. Restore explicit Settings → Tools → Actions dashboard generation, a sensor meaning table, the required EnergyTariff dependency, Norwegian grid/capacity context with Glitre Nett/NVE source links, and guidance on realistic whole-home hourly targets. No control behavior changes in this revision.


## Presentation baseline and stable release direction

Owner accepts the README structure and requests a documentation/structure freeze except for agreed features and necessary fixes. Clarified when generated dashboard YAML must be replaced, and added ROADMAP.md. Stable 2.0.0 is planned after successful two-charger charging tests, including retained one-charger behavior and no blocking setup/control faults. No physical acceptance, publication date or stable release approval is implied.
