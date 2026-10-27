# Smart Load Manager OJM — current project status

Updated: 2026-10-27

## Version

- Stable: **0.1.0**.
- Published beta: **0.1.1-beta.5** ([release](https://github.com/ojm88/smart-load-manager/releases/tag/0.1.1-beta.5)).
- Release code: `8b76ac3fc0f9e2bd7174798b1d0a2017490e6763`; merged PR #1.
- GitHub Actions [40484447173](https://github.com/ojm88/smart-load-manager/actions/runs/40484447173) passed both jobs for the released commit. Published as a prerelease after owner approval.

## Prepared beta.6 corrections

Owner tested beta.5 configuration: grouping is approved, but device selection is slow; selecting only a new charger in the replacement-list form retires the first charger, disables its entities, and can leave household status unavailable.

Root causes addressed: the form replaced membership instead of adding; unload traversed the edited config rather than the old runtime, leaving removed controllers registered; detached adapters then lost their saved record. Compact indexed Easee choices replace the frontend's global device picker. First setup now selects one charger, then optionally adds a second with the first excluded. Configure exposes explicit additive add and explicit remove.

The working branch prepares **0.1.1-beta.6**, not published. It retains both groups and all calculation/allocation formulas. Existing retired loads can be re-added with their saved identities/settings; explicit user-disabled entities are respected. It does not automatically restore deliberately removed loads.

Validation: **56 pure tests** and **46 runtime tests** pass locally, the runtime suite on both HA **2026.2.3** and **2026.10.4**. Added real native setup/add/reload/remove/re-add and full FlowManager first/second/cancel/finish tests. Source/telemetry are synthetic; no physical charger was contacted and no phone frontend timing was measured. CI uses both runtimes; branch CI result will be recorded once available.

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
- **38 HA 2026.2.3 runtime tests** pass, including real device/entity registries, config-entry migration, concurrent old-entry startup, native platform setup/unload, grouped entity registration and translated names. Synthetic telemetry and mocked Easee resolution are used; no real charger is contacted.
- Existing two-charger control regressions cover reduction-before-increase, new telemetry acknowledgements, missing data, recovery and unchanged power readings.
- Native HA startup also exercises the real coordinators against synthetic electrical/HAN measurements, automatic control off.
- Compilation, JSON/YAML validation and patch whitespace checks pass locally. GitHub Actions push workflow [40478887739](https://github.com/ojm88/smart-load-manager/actions/runs/40478887739) passed both jobs for code commit `2880f27d3307cf4135354a65c9d6f8e3827a0a32`.
- `calculations.py`, `control.py` and `budget.py` are identical between beta.2 and beta.4 and remain unchanged in beta.5. `allocation.py` is unchanged from beta.4. Coordinator changes adapt storage/load enumeration rather than rewrite the calculation.

## Owner validation

Owner confirms beta.2 worked with one physical charger. Beta.4 starts with two chargers; physical charging has not yet been tested. Owner has now tested beta.5 setup and reported the membership/reload failures above; physical charging is not confirmed. Recorder history continuity has not been separately integration-tested; registry unique IDs are preserved and only generated object IDs are renamed.

Before installing beta.5, take a full backup. Check migration, one budget, both grouping blocks, names, voltage readings and own customizations. Generate a new dashboard card, update external YAML references from the ID map, then deliberately enable automatic control. Test one charger, both distribution modes, first-priority changes, each schedule, pause, disconnect, completion and insufficient capacity.

Restoring beta.4 after schema migration requires restoring the backup. Do not run the old automation and SLM on the same chargers simultaneously.

## Future work

Live acceptance of beta.5; more than two chargers; supported hot-water tanks; floor-heating zones through Versatile Thermostat; donation account/link. Thermal control, vehicle battery integration, learning and automatic topology switching are not implemented.
