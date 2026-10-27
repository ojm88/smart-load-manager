# Changelog

## 0.1.1-beta.8 (prepared)

- Remove automatic comparison-test sidebar entry; setup logo selection remains available through its hidden panel.
- Restructure README into concise installation, setup, functions, limitations and support sections.

- Optional Easee-logo selection linked to initial and additive setup through a native external step; compact selection remains available.
- Authenticated, flow-bound selection with server validation, cancellation and replay protection. Return to the original native dialog to finish. Safari/Companion navigation remains unverified.

## 0.1.1-beta.7

- Package an administrator-only SLM velgertest page comparing the compact charger list with HA native integration logos, without manual YAML or file copying.
- Read-only first/second test selections exclude the first source device; no membership or charger commands are changed. Normal setup and load-control calculations remain unchanged.
- Native frontend logo rendering and actual phone latency require owner verification.

## 0.1.1-beta.6

- Add a charger without removing or disabling the existing one. Explicit add/remove actions and filtered first/second-charger lists.
- Compact dropdown options resolved through Easee registry indexes, avoiding the global frontend device picker.
- Cleanly shut down the actual old controllers on reload and clear stale allocator state; preserve detached records until unload completes.
- Keep household status, saved identities/settings and user-disabled preferences through membership changes and re-addition.
- Current Home Assistant registry access and full function-first display names; runtime CI on HA 2026.2.3 and 2026.10.4.

## 0.1.1-beta.5

- Separate native household and charging groups, with both chargers in the charging group. Upgrade existing entries while retaining per-load settings and unique sensor identities.
- Household-first wizard with one/two Easee selection and clear planned thermal categories.
- Complementary first-priority switches; distribution/role controls only with two chargers.
- Restore voltage measurements. Consistent function-first names and charger suffixes from the first charger; preserve custom names/IDs and expose an old/new ID mapping. Update external YAML references and regenerate the dashboard card.
- Add/remove chargers centrally, retaining independent settings. Configuration reload keeps automatic control off.
- Shorten README and align both manuals/dashboard templates. Require HA 2026.2 or newer.
- Retain beta.4 control behavior and calculations. Back up before upgrade; restoring beta.4 requires restoring the backup after config-schema migration. Live beta.5 charging remains untested.

## 0.1.1-beta.4

Prepared features are released in this beta. The household-first initial wizard,
complementary master toggles, conditional pair-control lifecycle and charger-ID
migration remain pending; the existing setup and priority selector still apply.

- Keep Configure accessible with two chargers. Add a household source/margin
  editor and offer Add charger only when fewer than two are configured.
  Validate before saving and retain existing charger options and identity.

- Add one household Load control status sensor with plain-language summary,
  per-load explanations, sharing policy and phase advice. Keep Measurement
  status separate. Move shared entities onto the SLM – Boligen device.
- Reduce new charger main sensors to five measurements; keep already registered
  informational sensors as compatibility diagnostics. Store current limits and
  electrical details as attributes.
- Make both Markdown cards render only household status attributes; display
  household measurements once and keep the source graph inputs unchanged.
- Remove the two-charger 120-second power cutoff: Easee reports power on
  change. Keep required HAN freshness and measured reduction acknowledgement.
- Keep sampled diagnostics visible when required power data is unavailable;
  identify the source in Charging explanation and hold automatic currents at
  zero. Preserve outstanding reduction confirmation timestamps.

- Highlight required Easee Voltage sensor activation for every charger in setup, errors and guides.

- Use Marketplace terminology and document HA 2026.11 requirement.
- Identify disabled required Easee sensors and retain detailed Add charger errors.

- Document the agreed household-first setup redesign; implementation is pending.
- Add Marketplace, forthcoming HA 2026.11 Marketplace and manual installation guidance.
- Add a current sensor reference and link it from both manuals.

## 0.1.1-beta.3

- Add a second Easee charger later through Configure; keep existing charger IDs and settings.
- Share one household budget between two chargers with equal-power or sequential allocation and a named priority selector.
- Confirm reductions with new telemetry before increasing the other charger; fail closed on missing required data.
- Give each charger its own controls, measurements and phase advice. Phase changes remain manual.
- Replace the full-view YAML with complete one-/two-charger Manual cards. Add a dashboard-YAML action using actual entity IDs.
- Update local HA/Marketplace artwork with the approved OJM house, tariff steps and charging connector.

- Clarify the long-term focus on shifting controllable resistive loads and adjusting EV charging to stay within the household hourly limit; display the project logo in the README.

- Remove the License and Checks sections from the README.

- Shorten the integration description by removing the EnergyTariff target comparison and automatic-control default wording from the introductory text. Control behavior is unchanged.

## 0.1.1-beta.2

- Explain in plain language why the integration focuses on Norwegian grid-capacity tariffs, which loads it can schedule, and what it does not control.
- Credit Home Assistant's Easee integration and EnergyTariff, and describe Versatile Thermostat (VTherm) as a possible future reference only.
- Expand the README and both user guides with the project's background and scope.
- Replace first-person charging explanations with neutral descriptions of the active control decision and its inputs.
- Add a support section; add the actual donation destination when the project owner provides its URL.

## 0.1.1-beta.1

- Rename the control reason sensor to **Ladeforklaring** and explain in plain language why charging is running, waiting, or reduced. Keep its entity ID stable so existing dashboards and automations continue to work.

## 0.1.0

First stable release, based on the tested beta.17 build. Includes automatic Easee charging adjustment using the home's Forbruksgrense, manual charging when automatic control is off, phase selection, optional schedule, charging pause/resume, clear status sensors, and the ready-to-paste dashboard card with EnergyTariff graphs. The first release supports one configured load entry per Home Assistant installation.

## 0.1.0-beta.17

- Add a persistent **Ladepause** control that sends 0 A to the configured Easee charger. Resume recalculates automatically or restores the previous manual limit only when safety checks still pass; manual current is locked during pause.
- Use the HAN sensor's last update time for freshness, so a steady power value does not become stale merely because its number has not changed.
- Remove repeated raw Easee/HAN diagnostic blocks from every sensor; retain a short explanation per sensor and show power rounded to whole watts.
- Rebuild the dashboard card with plain-language status, pause control, and the requested 12-hour graph names. Read EnergyTariff's used, estimate, and three-hour average sensors directly.
- Explain waiting, pause, and budget-limit states in simpler Norwegian on the dashboard.
- Simplify the README and English/Norwegian manuals, explaining peak-tariff savings as possible and dependent on the household and tariff.
- Keep one load entry per installation until a shared allocator exists; document per-charger identity as the path for future expansion.

## 0.1.0-beta.16

- Add Smart Load Manager OJM integration branding (square icon and light/dark logos, including high-resolution files) under the custom integration so Home Assistant 2026.3+ can show it without relying on a separate brands repository.
- Keep the README project illustration and add the compact integration logo preview.
- Update both manuals, project status, and recorded decisions.

## 0.1.0-beta.15

- Make diagnostic sensor values tolerant of missing coordinator keys so a partial/unavailable reading cannot prevent the sensor platform from loading.
- Add a concise Norwegian or English `explanation` attribute to every diagnostic sensor while retaining raw Easee/HAN diagnostic attributes.
- Clarify that `charging_card.yaml` is a single `vertical-stack` card for an existing section, while `charging_view.yaml` is a full `sections` view for raw view configuration. Add a regression test for the distinction.
- Refresh README, both manuals, project status, and decisions together; add a project image.


## 0.1.0-beta.14

- Ensure the coordinator always publishes measured charger current and make sensor rendering tolerant of a missing optional current value, preventing one missing field from blocking all diagnostic sensors.
- Run the Home Assistant-dependent sensor regression in the HA-runtime CI job, separate from pure unit tests.
- Verify stable `sensor.slm_*` entity registration and the sensor payload fallback in Home Assistant runtime tests.


## 0.1.0-beta.13

- Fix diagnostic sensors failing to load when the coordinator omitted measured charger current.
- Add a safe fallback for that optional current value so it cannot prevent unrelated sensors from loading.
- Set stable `slm_*` IDs through Home Assistant's entity ID registration path for the sensors and controls; add a runtime assertion.
- Add a Home Assistant runtime regression test for the missing-field case.

## 0.1.0-beta.12

- Give every diagnostic sensor a short, stable `sensor.slm_*` entity ID and migrate existing registry IDs on upgrade while preserving unique IDs and history. Keep the agreed Forbruksgrense ID unchanged.
- Simplify and localize all sensor names; add measured charger current and a clear manual-control status sensor.
- Make manual current unavailable while automatic load control is on; refresh it immediately when automatic control is turned off, and reject service/UI writes while locked.
- Restore the dashboard's descriptive Markdown charging status, clear control and measurement sections, and graphs for recommended versus measured charging current, hourly energy, and power.
- Update both manuals, setup guidance, changelog, and beta validation steps.

## 0.1.0-beta.11

- Add an integration-owned phase selector (Automatic / Single phase / Three phases) using Easee's `set_charger_phase_mode` service.
- Enforce one configured load entry per Home Assistant installation in this beta, keeping **Forbruksgrense** genuinely installation-wide until shared multi-load allocation exists.
- Keep configured phase mode distinct from measured active phases and voltage. Preserve the agreed fixed 11 A minimum for measured 230 V three-phase charging, and 6 A otherwise; no car identification, probing, or learning.
- Clarify that Forbruksgrense is the installation-wide hourly target and that EnergyTariff `target_energy` is not a competing setting.
- Clarify manual current as an intentional alternate mode while automatic control is off; 0 A pauses charging, and positive current remains bounded by Easee and the detected minimum.
- Shorten and localize entity display names; update the standard Lovelace example, Norwegian/English manuals, and regression tests.
- Keep automatic control opt-in/off after restart, preserve existing entities and legacy automation behavior, and update the full beta checklist.

## 0.1.0-beta.10

- Add an integration-owned **Forbruksgrense** select control with the former `input_select.forbruksgrense` options (4.5–20 kWh, 0.5 kWh steps); use this setpoint directly in the charging calculation.
- Migrate the beta.9 hourly limit into the select on upgrade; values within 4.5–20 kWh are retained, and out-of-range legacy values are clamped to the nearest supported boundary.
- Remove hourly-limit entry from setup. EnergyTariff remains the source for measured energy used this hour; its `target_energy` is separate and does not override Forbruksgrense.
- Rename the visible integration/config-entry name to **Smart Load Manager OJM** while retaining the internal `smart_load_manager` domain and existing entries.
- Update Norwegian and English manuals, setup wording, and dashboard example; add budget migration and selector regression tests.

## 0.1.0-beta.9

- Add Norwegian and English setup translations, field explanations, entity names, and clearer icons.
- Remove the EnergyTariff estimate from setup and from safety gating. Keep it as an integration diagnostic sensor; only the used-this-hour sensor is selected for the calculation.
- Expose Easee's reported maximum current as a read-only sensor and show no positive manual range while the live limit is unavailable.
- Add regression tests for control decisions and the exact Easee dynamic-limit service payload, including 0 A, with the existing indefinite TTL behavior.
- Update both manuals, the dashboard example, and project decisions to reflect the agreed fixed 11 A / 6 A minimum rules without current learning.

## 0.1.0-beta.8

- Remove the manually entered maximum-current value from setup. The controller now caps charging at the lowest valid circuit/charger current limit reported by the selected Easee device.
- Fail safely when Easee does not expose a valid maximum current: automatic control holds 0 A and positive manual current commands are rejected until the limit becomes available.
- Keep the manual current control bounded by the live Easee limit and update setup guidance in both languages.

## 0.1.0-beta.7

- Make clock scheduling self-contained: add an integration-owned schedule switch and native start-time entity; no user-created helpers or Easee Smartlading helper are required.
- Persist schedule enablement and start time in the integration entry. Automatic load control remains opt-in and resets off after restart.
- Remove obsolete setup validation and documentation for external schedule helpers; update the dashboard example and both manuals.


## 0.1.0-beta.6

- Fix config-flow import: load Home Assistant selectors from `homeassistant.helpers`, the module where the selector API is provided. Beta.5 used a nonexistent `homeassistant.components.selector` import, which prevented the setup handler from loading and produced “Invalid handler specified”.
- Keep Easee and EnergyTariff as `after_dependencies`; entity availability is validated by the setup flow.

## 0.1.0-beta.5

- Fix configuration-flow loading: Easee and EnergyTariff are ordered as `after_dependencies`, so a setup failure in either integration does not prevent Smart Load Manager's form from opening. Selected devices and sensors are still validated before creating an entry.
- Fix GitHub Actions metadata-validation paths after the integration domain was renamed to `smart_load_manager`.

## 0.1.0-beta.4

- Add a 60-second HAN freshness and positive-power guard; active automatic control pauses with 0 A on stale or invalid meter/tariff input or missing electrical data.
- Add optional scheduling using the selected Easee Smartlading switch and time-only `input_datetime` helper, with a repeating 12-hour window that crosses midnight.
- Add an options flow so existing installations can configure or clear scheduling without removing and re-adding the integration.
- Use Easee dynamic limit `time_to_live: 0` to retain a commanded limit until replaced, matching the previous automation's behavior.
- Expose HAN measurement age/validity and schedule state/reason as diagnostic entities.
- Expand Norwegian and English setup, schedule, testing, and persistence instructions.

## 0.1.0-beta.3

- Add opt-in Easee dynamic current control, off by default, with temporary commands and expiry.
- Add a manual current-limit entity; 0 A pauses, and positive values below the detected minimum are rejected.
- Decode Easee phase mode, output phase, grid type, and no-current reason while keeping the enum fields distinct.
- Infer voltage class and phase use from terminal measurements; use 11 A for measured 230 V three-phase charging and 6 A otherwise.
- Add EnergyTariff/HAN configuration, current/energy diagnostics, Norwegian and English manuals, and a standard-card Lovelace example.
- Keep water-heater and floor-heating control out of this beta.

## 0.1.0-beta.2

- Rename the project and integration domain to Smart Load Manager / `smart_load_manager` so it can grow beyond Easee charging.
- Document the supplied Easee sensor and attribute map, separating diagnostic inputs from future safety limits.
- Clarify the 400 V TN example: roughly 230 V phase-neutral readings with three active phase conductors imply roughly 400 V phase-phase.
- Keep the implementation read-only. No charger command, learned current limit, active power recommendation, water heater control, or floor-heating control is included yet.
- State explicitly that this version has not been validated inside a running Home Assistant instance and is not published to Marketplace.

## 0.1.0-beta.1

- Initial isolated diagnostic scaffold.
- Adds setup fields for an Easee device, a W/kW HAN power entity, and an hourly energy limit.
- Discovers Easee status/current/voltage entities through device association and attributes.
- Adds regression-tested phase/voltage inference and W/kW normalization.
- Does not write charger current settings.
