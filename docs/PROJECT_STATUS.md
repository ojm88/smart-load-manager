# Smart Load Manager OJM — current project status

Updated: 2026-10-31

## Beta 20 — release authorized, publication in progress

Owner authorized publication on 2026-10-31. Manifest 0.1.1-beta.20. Code CI run 41198196307 passed for 04dbbac7d4ebb1e7c24f020074c5f51aa8d2c8d2. Release preparation adds only version/docs changes; verify final CI before merging PR #16 and publishing as pre-release. Existing YAML remains compatible.

Persist per-charger automatic control, restore desired manual requests through existing guards, and enforce the verified manual minimum in UI and direct calls. Other UI options already persist; Easee owns phase configuration. New installations remain opt-in. First upgrade requires enabling automation once because beta 19 never saved the choice. Explicit rewiring/removal disables the affected load. Additional correction: block new pause activation for Completed/disconnected/unavailable sources in UI and direct calls; existing pauses remain removable. Rejections are recorded in diagnostics. Ordinary completion/wake allocation is unchanged. Verification includes coordinator recreation and actual HA integration reload with two chargers and mixed saved settings; physical restart/charging remains pending. 93 pure, 142 runtime tests on both supported HA/Python environments and one Node test pass; two regressions fail against beta 19. See [verification](BETA20_VERIFICATION.md).

## Previous release — 0.1.1-beta.19

Owner requests tests and publication of the new completed-session policy. Verified zero-W/sub-amp automatic completed sessions leave capacity allocation and held-offer forecast, and receive no ordinary budget writes. New waiting/ready requests assess the validated minimum immediately; actual charging restores normal allocation. Source feedback latency and retained-limit wake are accepted by the owner. Explicit controls, real faults and active-transfer acknowledgements remain. See BETA19_VERIFICATION.md. Published 2026-10-30 as [Pre-release](https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.19) after owner approval. PR #15 merge/tag dc253af94c2a40a77579e2771b7fbf4b98871c9d; tagged tree e064018c52f3ef0df7b8fa1d975b3615d66f33b7 equals tested tree. All four CI jobs passed in run 41139627386 for 60a86e30c2ea4714b8f7ee732031997d4c39f4d1. 93 pure, 135 runtime tests on each supported HA/Python version and one Node test pass. Two regressions reject beta.18. No HA installation or physical commands performed. Existing YAML remains compatible.

## Previous release — 0.1.1-beta.18

Implemented the owner's approved limited correction: no automatic current restoration while raw completed, age-only HAN holds preserve measured idle completed offers without claiming freshness, source/control restart remains immediate with valid inputs. Real faults and active freshness guards remain; paired capacity transfer remains measured. No MQTT configuration changes. Diagnostic records now use the actual command-cycle sample and expose completion holds.

Validation passes: **93 pure**, **133 runtime** on each supported HA/Python version, plus **1 Node test**. Two new regressions reject beta.17. Details and remaining physical acceptance are in [BETA18_VERIFICATION.md](BETA18_VERIFICATION.md). Published 2026-10-30 after owner approval: [0.1.1-beta.18](https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.18), visibly verified as Pre-release. PR #14 merge/tag commit efd001e9691c4926f6cad7546676e88baa2d76e8, tree 956f40e3098b2ebe4e582b92ce8257dd1395663f equals tested preparation tree. Final CI 41130412214 passed all four jobs for edea81d912de507480ba034b9189bec13488903a; code CI 41111748910 also passed. Manifest beta.18. Not installed. Existing beta.16/17 dashboard YAML remains compatible. General change-based HAN freshness remains unresolved; the owner accepts this beta for further testing. Physical overnight completion, car-app target increase and two-charger acceptance remain pending. Measurement status is not pinned to ready when inputs are stale.

## Previous release — 0.1.1-beta.17

Published **2026-10-30** after owner approval: [0.1.1-beta.17](https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.17), visibly verified as **Pre-release**. Stable remains **0.1.0**.

PR **#13** merge/tag commit **3ecf399c9cb2f57c7f5ff460b5a3555cd4a01f38**. Tagged tree **f11e4cbfee9d6bc77ae356384da0d1f28d245ab6** equals the final release-preparation tree; manifest **0.1.1-beta.17** verified from the fetched tag. All four jobs passed in final CI run **41061957587** for head **9b61bc9b7eb574108be1afaf0337762547ad6f20**. Code CI **41050713570** also passed.

[Verification record](BETA17_VERIFICATION.md): **92 pure tests**, **129 runtime tests** on both HA **2026.2.3/Python 3.13** and **2026.10.4/Python 3.14**, plus **1 Node test**. New zero-offer recovery regression fails against the prior policy. The final policy uses budgeted standby offers, preserves active-peer priority, assesses waiting/control/measurement-recovery transitions immediately, and neither resends unchanged limits nor moves the regular deadline on no-change assessments. Diagnostics capture source measurements, decisions and command results.

Update the integration and restart Home Assistant. Existing **beta.16 dashboard YAML can be retained**. No HA installation or physical charger control was performed during preparation/publication. Physical SOC-target restart, overnight completion and two-charger acceptance remain pending. Download diagnostics promptly if behavior differs, before restart/reload. Prior release tags remain unchanged.

## Earlier beta.17 preparation records (superseded where noted)

## Beta.17 input recovery clarification

A successful input-wait zero is not repeated. Newly valid measurements now explicitly request immediate regulation. One/two-charger regressions pass in the 38-test site suite; no publication or physical command.

## Beta.17 investigation — 2026-10-30

Owner trace/video confirms zero completion ceiling survives schedule opening and pause resume, preventing automatic restart despite valid 16 A recommendation. Local correction releases ceiling only on explicit renewed permission and avoids recapturing repeated completed feedback. Added sequence regressions; 92 pure and 126 runtime tests pass on both supported HA/Python versions. Physical acceptance pending; beta.16 remains published, no beta.17 release authorized. Uploaded trace also contains real HAN gaps and an initial brief invalid value, so earlier freshness theory is not a proven explanation of every transition.

## Previous beta.16 publication record

- Stable: **0.1.0**. Published beta: **0.1.1-beta.16** ([release](https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.16)).
- Published 2026-10-30 after owner approval. PR #12 merge/tag **e3d76cccc710f7c7611f6eabbfbea8bde787716f**. GitHub release visibly verified as Pre-release. Tagged tree **fbf4272760b5410b491b043cd0fbd0bc7f22826d** equals tested code tree; manifest 0.1.1-beta.16. All four jobs in CI run **41029232687** pass for code head **0145ecdc8a6a670fd96f5060774c1518497de7b4**.
- Scope: validated manual-minimum handover; independent charging-category switch; concise grouped Markdown; report-based HAN freshness up to 120 seconds; native anonymous diagnostics with 4096 in-memory events. Existing ordinary five-minute regulation and paired measured reduction safeguards remain.
- Local validation: **92 pure tests**, **124 HA runtime tests** on both **2026.2.3/Python 3.13** and **2026.10.4/Python 3.14**, plus **1 Node test** (217 distinct tests). Includes HA template-engine rendering, source-status/command timing, manual pause/schedule, completion/HAN regression and diagnostics privacy/order/failure tests. Actual iPhone rendering/download and overnight/two-charger hardware acceptance remain pending.
- Update/restart HA, then regenerate YAML with **smart_load_manager.get_dashboard**. No HA instance has been installed or physically controlled during this preparation. Old tags and stable release remain unchanged.

## Earlier release and preparation records

### Beta.15 publication record

- Stable: **0.1.0**.
- Published beta: **0.1.1-beta.15** ([release](https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.15)).
- Published on 2026-10-29 after explicit owner approval. PR #11 merge/tag commit **74b7277b4217ca58d699fd56572dba76b9a08b95**; verified draft=false, prerelease=true and tagged manifest 0.1.1-beta.15.
- Release-preparation CI run **40875261526** passed for **4a8d7efec633930342177e31464b4d00c88af8f9**. The published merge tree equals tested preparation tree **3fc990e71bdc4fcc425b290bf787073a56ef02d7**. Code CI **40873366785** also passed. 200 distinct tests pass, including runtime suites on both supported HA/Python versions.
- Beta.15 changes presentation only; charging calculations, allocation and commands retain beta.14 behavior. Restart HA and regenerate the existing Manual-card YAML using **smart_load_manager.get_dashboard**. No HA instance was installed or controlled by publication. Actual iPhone visual acceptance remains pending. Beta.14 physical completion/wake/two-charger acceptance remains separate. Stable 0.1.0 and prior tags are unchanged.

## HAN tolerance — 2026-10-30

Owner requests two-minute tolerance. Beta.16 accepts reports up to 120 seconds old inclusive, using last_reported; beta.15 used 60 seconds with last_updated. Boundary tests cover 120 and just above 120. Five-minute ordinary dispatch remains unchanged.

## Beta.16 diagnostics preparation — 2026-10-30

Native HA Download diagnostics now exposes versioned, allowlisted anonymous state and a 4096-event memory recorder: samples, decisions, measurement waits/failures and current/phase command attempts/results. Tests cover privacy, bounded ordering, copy isolation, failure-versus-success and the HA diagnostics entry point. Runtime collection resets on reload/restart; not a full historical cloud log. Actual UI download remains unverified; beta.16 not published.

## Completion/HAN investigation — 2026-10-30

Owner confirms beta.14/15 did not resolve overnight source-status cycling. Corrected a reproducible false-staleness path: use HAN last_reported rather than last_updated, retain numeric stale readings for display with explicit freshness warning, preserve real input-failure stops. Regression fails against old timestamp logic and passes against corrected sampler. Local checks: 89 pure tests; 18 control-event, 35 site, 10 live-telemetry and 13 sensor tests in HA 2026.10.4 pass. Full beta.16/dashboard compatibility validation and physical overnight acceptance remain pending. No new release or HA command.

## Beta.16 preparation — approved presentation

Owner approves the concise status-card design: household → category → named load, clear category separators, aligned measurements, one status and relevant short explanation. Packaged templates and examples include this hierarchy. Future hot-water/floor-heating groups are design scope only; current configured chargers remain the actual content. Beta.16 control changes and regression validation are still in progress, not published or hardware tested. Regenerate dashboard YAML when the future update is installed.

## Development review — 2026-10-29

Reviewed beta.1–15 against release records, owner feedback, decisions and relevant tests. [Retrospective](RETROSPECTIVE_BETA1_15.md) identifies predictable source/command-feedback, lifecycle, timing and mobile-UI omissions. AGENTS.md now requires a relevant full-journey/source-contract/regression review and separates software evidence from physical acceptance. No runtime change, new beta, new test execution or physical acceptance occurred in this review. Beta.15 remains published; phone and hardware acceptance still follow the version summary above.

## Approved beta.15 release preparation

Owner explicitly requests publishing beta.15 on 2026-10-29. PR #11 code head **8e2345203202cb856b984169b60077d8fa82816c** passes all four CI jobs in run **40873366785**. Prepare manifest **0.1.1-beta.15** and publish as a prerelease. This supersedes the earlier hold below for this release only. Publication/tag verification is recorded separately. Actual iPhone visual acceptance remains pending. Regenerate dashboard YAML after updating and restarting HA. No charging-control policy changes.

- Owner requests a compact iPhone Markdown layout. Replace the long title with a short connection/status heading and three native table columns (meter kW, used energy, estimate) on one value row. Display-only rounding/scaling bounds high-value strings; source precision and charging/control calculations are untouched.
- All cars disconnected: singular/plural no-car heading, shared meter/budget retained, redundant load sections and pair-distribution text hidden. Known mixed connections identify names and show a count heading. Unknown/unavailable does not imply connection. Per-load power, current recommendation/last sent and next-regulation time appear only for actual Easee charging status; waiting/paused/completed retain their reasons.
- Both packaged cards and ready-made examples use the same Markdown content. At the draft stage, saved dashboard YAML regeneration was required and the manifest remained **0.1.1-beta.14**. Beta.15 was subsequently authorized and published as recorded above.
- Local software validation: **87 pure tests**, **112 HA runtime tests** on both HA **2026.2.3/Python 3.13** and **2026.10.4/Python 3.14**, plus **1 Node test** pass (200 distinct tests). New tests cover singular/plural/mixed/unknown connections, suppressing idle details, retaining charging details, large values in three table cells and missing measurements. JSON/YAML, compilation and whitespace pass. Actual iPhone visual acceptance, including larger accessibility fonts, remains pending; structural tests alone cannot guarantee every display width.

## Approved beta.14 release preparation

Owner explicitly requests publishing beta.14 on 2026-10-29. PR #10 code head ce15ab54b2ce01ee23973649009543bc7234e729 passed all four jobs in CI run 40842357564. Local validation passes 195 distinct tests: 85 pure, 109 HA runtime (both supported HA/Python versions), and one Node test. This preparation changes the manifest version to 0.1.1-beta.14 and release documentation only. Publish as a prerelease; preserve stable 0.1.0 and previous tags. Publication is recorded after release/tag verification. Physical beta.14 completion, wake/preheating and two-charger acceptance remain pending. Restart HA, regenerate dashboard YAML via smart_load_manager.get_dashboard, inspect measurements and deliberately enable automatic control.

## Beta.14 preparation history

- Completion feedback correction (2026-10-29): owner reports beta.13 raw Easee status cycling after completed under automatic control. Implemented budgeted idle allowances instead of a completion-triggered zero. Active sessions receive capacity first; remembered idle ceilings prevent pause-induced ready/waiting reports reclaiming priority. Raw status is never rewritten. Existing pause/schedule/fault/input stops and forecast reductions remain.
- At exactly zero measured W, known idle states below 1 A no longer cause repeated zero writes. Paired stop confirmation still requires both current and power reports newer than the reduction; charging/unknown states, positive W and >=1 A retain the previous strict comparison. Completion state is cleared on actual charging/start/disconnect and unload.
- Updated validation: **85 pure tests**, **109 HA runtime tests** on both HA **2026.2.3 / Python 3.13** and **2026.10.4 / Python 3.14**, plus **1 Node test**, all pass locally (195 distinct software tests). New completion regressions fail against the preceding implementation. Checks cover retained allowance across ticks/status changes, household risk reductions/recovery, paired measured stop before active-peer increase, both allocation modes, blocked inputs/controls and narrow standby tolerance. Compilation/JSON/YAML/whitespace pass. These supersede the earlier beta.14 counts below.
- No physical charger command, beta.14 installation or release performed. Required owner acceptance: automatic completion remains quiet when capacity permits; legitimate budget/peer reductions remain effective; verify wake/preheating and completed-to-new-session behavior, then both chargers. Beta.13's earlier positive one-charger feedback does not resolve this newly reported completion fault.

- Owner confirms beta.13 works with **one configured charger**. This confirms that tested installation only; two-charger physical operation is not yet confirmed. Keep beta.14 changes ready in the draft while the owner tests for further issues. Do not publish until separately requested.
- Schedule opening/closing and explicit controls now trigger immediate validated allocation without waiting for the five-minute gate or coordinator refresh debounce. This includes pause/resume, automatic/schedule switches, start-time edits, phase selection and priority/distribution changes. Normal meter-driven recommendations and forecast reductions retain their cadence. Required measurements, budget/minimums, manual behavior and measured reduction-before-increase remain.
- A dedicated callback wakes the site at the next schedule boundary even without source updates. Windows are half-open (start included, end excluded), use seconds/local wall time and wrap midnight. Callback lifecycle and queued controls are retained through awaited commands.
- Markdown headings now show each charger's preferred SLM user name and actual status, with separate explanations for both loads. A generic source name cannot override an SLM user name. Dashboard generation, priority choices and shared explanations use the same naming helper. Regenerate YAML for the new heading.
- Local validation: **85 pure tests**, **102 HA runtime tests** (both HA **2026.2.3 / Python 3.13** and **2026.10.4 / Python 3.14**) and **1 Node test** pass, 188 distinct software tests. New coverage includes exact boundary callbacks without meter updates, cancellation after time edits, automatic/manual pause-resume, current budget validation, automatic enable, schedule disable/edit, paired measured stop before peer increase, queued requests during command waits and named per-load status rendering. JSON/YAML, compilation and whitespace checks pass. No beta.14 release is authorized or published; manifest and published beta.13 remain unchanged. Physical beta.14 acceptance is pending.

## Published beta.13 (PR #9)

- Reproduced and corrected a beta.12 startup stop loop: charging status arriving before zero-current readings rise caused the minimum-current check to return None and send 0 A. The corrected path uses confirmed wiring and measured voltage until measured phase use exists. A real HA source-event regression fails before the fix and passes after; missing voltage still stops charging. Read-only live inspection confirms beta.12 is installed; beta.13 was subsequently published after explicit owner approval.
- Newly connected cars trigger a shared regulation as soon as Easee reports a supported ready/charging status, without waiting for the existing five-minute deadline. Authorization/offline waits do not start charging. Normal status transitions do not repeatedly reset regulation.
- Retains opt-in, schedule, pause, measured electrical data, minimum/shared capacity and paired reduction confirmation. On completing the startup cycle, the next ordinary regulation is five minutes later. Beta.12 live calculations and early reductions remain. No new dashboard YAML is required for this control-only change.
- Local validation: **81 pure tests** and **89 HA runtime tests** pass; runtime suites pass on both HA **2026.2.3 / Python 3.13** and **2026.10.4 / Python 3.14**. Six new regressions cover immediate/repeated plug-in, authorization waits, policy/budget blocks, missing-input recovery and measured paired reduction acknowledgement. No physical charger commands or acceptance tests performed. Beta.12 remains the published version; Owner explicitly authorized beta.13 publication on 2026-10-28. Code head 46bbe57561742a8938f676fd5f76f5e29e421d12 passed all four CI jobs in runs 40751798978 and 40751788952. Version is prepared as 0.1.1-beta.13; publication is recorded after verification.

## Published beta.12 (PR #8)

- Source events now recalculate complete household capacity and recommendations live; the 30-second watchdog also accounts for elapsed time and freshness. Ordinary automatic current commands are gated at five minutes, with forecast-based reductions earlier after 30 seconds of persistent risk or immediately if the reserved budget cannot wait. Pauses, invalid required measurements and lower physical limits remain immediate. Early reductions cannot raise a peer and block ordinary increases for five minutes.
- Single-charger direct startup remains; paired measured-reduction acknowledgement remains. A dedicated timer handles the next regulation/risk decision even without a new source event, and source events during awaited commands are replayed.
- Markdown includes compact meter W / used kWh / estimated kWh, connected-car indication, live recommendation, last sent limit and next regular time. Single-charger language contains no hypothetical second-charger guidance. Existing YAML must be regenerated.
- Owner screenshot confirms completed was already recognized in beta.11, but a nonzero recommendation made the view confusing. Status handling now covers all 22 documented Easee names, uses explicit positive-current eligibility, blocks unknown modes, and shows completed charging clearly without asserting battery SOC. Tests cover each documented blocked mode and unknown future states.
- Manifest is prepared as **0.1.1-beta.12**. Published beta.11 and stable tags remain unchanged. Owner explicitly approved publication on 2026-10-28. Local validation: **80 pure tests**, **82 HA runtime tests** (both HA **2026.2.3 / Python 3.13** and **2026.10.4 / Python 3.14**) and **1 Node test**, 163 distinct software tests. Compilation, JSON/YAML and whitespace checks pass. New regressions cover held limits across live updates, one/two charger five-minute deadlines, persistent versus transient/urgent forecast risk, no early peer increase, lower physical limits, invalid-source stop, direct single startup, delayed-response coalescing, independent time callbacks and accurate Markdown descriptions. GitHub Actions 40744567210 and 40744557348 passed all four jobs for code head d15239cecf1dce24c49bd2fb9131102823aa4fe3. This release preparation changes documentation only. Physical charging/phone acceptance remains pending; publication will be recorded after tag/release verification.

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


## Beta.12 publication verified

Published 0.1.1-beta.12 on 2026-10-28 from PR #8 merge commit 118bc974c8915c830893503e112cc3a5c4fa1c9d, whose tree matches the tested release-preparation tree 97b1509756bc0a7b577d62d0e847154dd7f8d55c. Verified draft=false, prerelease=true, exact tag/target SHA and tagged manifest version. Release-preparation push and PR runs 40746583042 / 40746588612 passed all four jobs. Stable 0.1.0 and previous tags remain unchanged.

After installation, restart HA, regenerate the Manual card via Settings → Tools → Actions → smart_load_manager.get_dashboard and deliberately enable automatic control after reviewing the measurements. Test physical single/two-charger operation, held limits, forecast reduction, completion and the new card. These physical/phone acceptance checks remain pending.
