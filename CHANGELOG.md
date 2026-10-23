# Changelog

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
