# Changelog

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
- State explicitly that this version has not been validated inside a running Home Assistant instance and is not published to HACS.

## 0.1.0-beta.1

- Initial isolated diagnostic scaffold.
- Adds setup fields for an Easee device, a W/kW HAN power entity, and an hourly energy limit.
- Discovers Easee status/current/voltage entities through device association and attributes.
- Adds regression-tested phase/voltage inference and W/kW normalization.
- Does not write charger current settings.
