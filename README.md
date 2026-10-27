# Smart Load Manager OJM

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/smart_load_manager/brand/dark_logo@2x.png">
  <img src="custom_components/smart_load_manager/brand/logo@2x.png" alt="Smart Load Manager OJM" width="480">
</picture>

[![Tests](https://github.com/ojm88/smart-load-manager/actions/workflows/tests.yml/badge.svg)](https://github.com/ojm88/smart-load-manager/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/ojm88/smart-load-manager?include_prereleases)](https://github.com/ojm88/smart-load-manager/releases)

Home Assistant integration that adjusts one or two Easee chargers to leave room for household consumption within a chosen hourly energy target. This can help avoid a higher grid-tariff capacity step; savings depend on your household and tariff.

[🇳🇴 Norsk brukerveiledning](docs/manual_nb.md) · [English guide](docs/manual_en.md)

## Requirements

- Home Assistant **2026.2 or newer**.
- Easee chargers configured in Home Assistant, with an enabled **Voltage** sensor and a measured value on each charger.
- A HAN power sensor in W or kW, plus [EnergyTariff](https://github.com/epaulsen/energytariff) reporting energy used during the current hour from that meter.

## Installation

### Marketplace

On HA **2026.11 or newer**, add `https://github.com/ojm88/smart-load-manager` as a custom **Integration** repository in **Settings → Marketplace**. Install Smart Load Manager OJM and restart Home Assistant. See the [Marketplace guide](https://contributors.home-assistant.io/marketplace/how-it-works/).

### Manual

Download a [release](https://github.com/ojm88/smart-load-manager/releases), copy `custom_components/smart_load_manager` into your HA `config/custom_components/` folder and restart.

## Configuration

1. Open **Settings → Devices & services → Add integration → Smart Load Manager OJM**.
2. Select HAN power, EnergyTariff energy used this hour, and the safety margin.
3. Choose EV charging, select the first charger, then finish or add a second.
4. Set the household consumption target on **SLM – Boligen**. Enable automatic control deliberately on each charger, with no competing automation controlling it.

**Boligen / Household** contains the shared budget and status. **Lading / Charging** contains the chargers. Use **Configure** to edit household sources or add/remove a charger while retaining the others.

The optional **logo picker (test)** opens a separate HA page with Easee branding. Confirm the choices, then return to the original dialog to finish. Its Safari/Companion navigation still requires testing. Compact selection is also available. No comparison-test page is added to the sidebar.

## Supported functions

| Function | Behavior |
| --- | --- |
| Shared household budget | Combines hourly energy, current HAN power and a safety margin to adjust charging limits. |
| One or two chargers | Charge both or one at a time, with a selectable first priority. |
| Per-charger controls | Independent schedule, pause, manual current and phase selection. |
| Measurements | Status, power, current, recommended current, active phases and voltage. |
| Explanations | Household status describes why charging runs, waits or is limited. |
| Dashboard | `smart_load_manager.get_dashboard` returns a Manual card using actual registered entity IDs. |

## Limitations and testing

This project is under development. Physical charging validation of the current version, including two-charger operation, is pending. Automated tests cover calculations, allocation and Home Assistant setup; see [validation status](docs/PROJECT_STATUS.md).

- Automatic control starts **off after restart**.
- Missing or stale required meter data pauses automatic allocation. Reductions must be confirmed by subsequent measurements before capacity is reassigned.
- Phase changes are manual. There is no spot-price optimization or vehicle battery control.
- Hot-water and floor-heating control are not implemented. SLM does not replace electrical protection.

## Help and feedback

[Open an issue](https://github.com/ojm88/smart-load-manager/issues) with the integration and HA versions, what you expected, what happened, and relevant log excerpts. Remove credentials and private installation details before attaching logs or screenshots.

[Releases](https://github.com/ojm88/smart-load-manager/releases) · [Changelog](CHANGELOG.md) · [Norwegian guide](docs/manual_nb.md) · [English guide](docs/manual_en.md)

## Planned

More chargers, hot-water tanks and floor-heating zones sharing the household budget. Floor heating is planned through [Versatile Thermostat](https://github.com/jmcollin78/versatile_thermostat). A voluntary coffee-support link will be added when the account is ready.

## Acknowledgements

Thanks to [Home Assistant](https://www.home-assistant.io/), the Easee integration maintainers and [EnergyTariff / Erling Paulsen](https://github.com/epaulsen/energytariff). These projects are independently maintained.
