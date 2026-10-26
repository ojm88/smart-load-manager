# Beta 4 — agreed setup and documentation scope

Status: requirements recorded on 2026-10-26; not implemented or released.
Published version remains 0.1.1-beta.3.

## Setup journey

1. **Household measurements:** explain the common household budget; select the
   instantaneous HAN power sensor, EnergyTariff used-this-hour sensor and margin.
   Configure these once for the installation, not again for every load.
2. **What would you like to control?** Organize setup by load type: EV charging,
   hot-water tanks, and floor heating. Only implemented types may be configured.
   Planned types must be clearly marked as unavailable/planned, with no active
   device selection or claim that control works.
3. **EV charging:** explain the feature and allow one or two distinct Easee
   devices during the same setup journey. Use their existing device names.
   With two chargers, explain Charge both / One at a time and First priority.
4. **Later additions:** reopen configuration to add the second charger without
   recreating the installation or re-entering household measurement sources.
   Shared sources must also be editable centrally.
5. **Future hot water:** an explanatory page followed by selection of tanks,
   once its control rules and supported entities have been agreed.
6. **Future floor heating:** an explanatory page followed by selection of
   heating zones through Versatile Thermostat. The owner identifies VTherm as
   the intended requirement; its control interface and policies still need a
   workshop. No thermal controller is authorized for implementation yet.

## Compatibility and acceptance criteria

- Preserve existing entries, entity identities, user settings and dashboards.
- Keep the working current calculation, minima, allocation, pause and schedule
  behavior; this setup redesign must not silently change charging policy.
- Household budget and sources appear once; charger controls remain per device.
- No duplicate device selection; cancellation/partial failure must not leave an
  actively controlling half-configured installation or duplicated entries.
- Explain one/two-charger selection directly in the wizard, in both languages.
- Verify initial setup with one and two chargers, adding a second later,
  reopening an existing beta.3 setup, and cancellation/error recovery.
- Choose the HA config-entry/subentry implementation after reviewing migration
  and lifecycle behavior; do not assume that a multi-selector alone solves it.

## Repository front page and documentation

Use a concise structure: purpose and supported loads; requirements; installation;
configuration; controls and sensor reference; dashboard; troubleshooting;
acknowledgements and optional support.

- Include Marketplace custom-repository installation for HA 2026.11 onward,
  using https://github.com/ojm88/smart-load-manager, category Integration.
  Older versions use the manual installation instructions.
- Describe Settings > Marketplace separately for HA 2026.11 onward, based on
  the official documentation, not as already available on 2026.10.
- Include manual installation, restart guidance, and Add integration step.
- Explain each existing sensor/control and distinguish household values from
  charger readings and diagnostic details. Keep explanations plain and neutral.
- Keep current instructions accurate until the new wizard is implemented;
  update README, both manuals, cards, changelog and translations in the beta.
- This is the first beta.4 input; do not publish a beta solely from this record.

Sources checked on 2026-10-26:
- https://contributors.home-assistant.io/marketplace/how-it-works/
- https://contributors.home-assistant.io/marketplace/how-it-works/

## Additional beta.4 feedback

- Use Marketplace throughout user-facing documentation; retain required technical
  filenames such as `hacs.json`. Marketplace requires HA 2026.11; do not claim
  that menu exists on older versions.
- Garage fails initial and second-charger setup when no active voltage attributes
  are available. Report disabled sensor IDs when identifiable; preserve detailed
  errors in Configure. Do not guess voltage or confuse Easee master/slave roles
  with SLM software priority. Physical retry pending after enabling diagnostics.

## Compact sensors — approved and implemented locally

- Seven main sensors per charger plus one shared measurement diagnostic.
- Attributes replace new duplicate diagnostics; existing registered entities
  survive as compatibility diagnostics, without deletion/forced disabling.
- Both cards and docs updated; calculation/allocation behavior unchanged.
- Source-level and mocked-runtime verification complete; not released.

## Household device, categories, priority roles and naming — owner feedback

Agreed direction recorded 2026-10-26; implementation pending.

### Household versus charger

- Give shared settings their own SLM household device, independent of either
  charger's priority. Move Forbruksgrense and the shared Measurement status
  there; keep one budget for all current and future load types.
- Place Lademåte and one Master (førsteprioritet) dropdown on that household
  device only when two chargers are configured. Do not create/expose these
  choices for a one-charger installation, including upgraded beta.3 entries.
- Adding the second charger later must add these controls without rebuilding
  the installation; removing it must hide/deactivate the pair controls safely.
  Preserve the saved choice when temporarily unloading/reloading a charger.
- Master means SLM's first-priority charger. Slave is the other charger. One
  dropdown selects an entry ID, with the real charger name as its label; the
  other role is derived. It must be impossible to select two masters/slaves.
- Do not change Easee hardware master/slave configuration. Do not make the
  priority charger the owner of the shared budget/config entry. Allocation
  behavior remains the already agreed Charge both / One at a time policies.
- Give each charger a read-only Charging role sensor when two are configured,
  with localized Primary/Master and Secondary/Slave states, derived from the
  same saved priority used by allocation. Classify it as diagnostic so the
  seven normal charger measurements remain the compact main sensor set.

### Native device page and dashboard grouping

- Household device: common configuration (Forbruksgrense, and two-charger
  distribution/priority when applicable), shared diagnostics (Measurement status).
- Charger Controls: automatic load control, pause and manual current.
- Charger Configuration: phase selection, scheduling and start time.
- Charger Sensors: seven main sensors. Diagnostics: Charging role, plus existing
  compatibility sensors retained from older versions.
- HA supplies its native Controls/Configuration/Sensors/Diagnostics section
  headings; do not promise arbitrary custom native blocks. Use the separate
  household device for isolation and a named household/distribution block in
  the YAML dashboard. Use real charger names on each charger's dashboard block.

### Names and IDs

- Charger identity must be included from the very first charger, not only on
  the second. Default display names must include the Easee device name. Respect
  user-supplied names; do not overwrite deliberate user customizations.
- New per-charger IDs use slm + function + stable charger-name identity from
  the first charger. Preserve a stable disambiguator if names collide; a name
  change must not silently regenerate entity identity.
- Shared IDs do not acquire a charger name. HAN reading age is shared household
  information, now an attribute of Measurement status; it is not charger age.
- The owner specifically requests charger identity in the existing first
  charger's default IDs as well. This revises the earlier unsuffixed-first-ID
  policy. Review a migration of integration-generated IDs only, preserving
  unique IDs/history, custom names, collision safety and a clear old/new mapping.
  ID renaming does not automatically repair arbitrary external YAML/automations.
  Do not claim compatibility aliases unless actually implemented and tested.
  Decide the migration mechanism before changing registry IDs. Update generated
  dashboards, static examples and both manuals as one unit.

### Required checks

- One charger has no pair dropdowns; adding a second exposes exactly one pair.
- Priority change updates both role sensors with complementary states, in both
  allocation modes, and never moves/duplicates the household budget.
- Verify startup/reload/removal/addition, including unavailable peer data, without
  resetting user settings or enabling automatic control unexpectedly.
- Verify per-charger categories/device links, correct real names from the first
  charger, registry customization/collision handling and migrated dashboard IDs.

## Priority toggle revision and per-charger schedules

Latest owner discussion supersedes the single visible Master dropdown proposal:
- Show a Master (first-priority) toggle on each charger only with two configured.
  Both toggles represent one saved priority entry ID, not independent booleans.
  Turning either on makes the other secondary; turning the active master off
  promotes the other, preserving exactly one master. The read-only role sensor
  derives from the same priority. Do not change Easee's hardware roles.
- Retain independent existing schedules/start times; e.g. one charger eligible
  from 22:00, the other from 02:00. Schedule only grants eligibility; it does not
  override pause, budget or guarantee immediate charging. One common start time
  can be achieved by setting both alike, without adding a redundant global clock.
- Forbruksgrense remains a charger-independent household/front-page setting,
  also suitable for a future heating-only installation. The new household
  device and optional pair controls still need implementation.

Implemented locally: Configure now offers Household sources and safety margin
regardless of charger count. Add charger is separate and hidden when two exist.
Validated edits update both entries' shared sources without altering IDs,
budget/priority or schedules. Invalid input leaves entries unchanged. Fresh
sources are sampled on the next regular update; no forced restart/reload.

## Central household explanations — approved and implemented locally

This supersedes the seven-sensor presentation: new chargers now have five main
measurement sensors. Charging explanation and phase advice are collected in
one household Status for laststyring (`sensor.slm_status`). Shared Measurement
status remains separate for diagnostics. Both are on SLM – Boligen, along with
the household budget. Existing legacy informational sensors stay compatible.

Both Markdown cards render only household status, its plain-language summary,
per-load explanations and shared advice. They no longer implement charger
status/control rules. Graph inputs remain unchanged and read EnergyTariff
directly. `docs/ARCHITECTURE.md` documents the presentation extension contract.
Future loads must extend this central explanation path, not duplicate UI logic.

The master toggles, pair-control lifecycle, naming migration and household-first
wizard are still pending. Do not confuse this completed status/device boundary
with a standalone heating-only configuration or implemented thermal control.
