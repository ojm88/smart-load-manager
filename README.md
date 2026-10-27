# Smart Load Manager OJM

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/smart_load_manager/brand/dark_logo@2x.png">
  <img src="custom_components/smart_load_manager/brand/logo@2x.png" alt="Smart Load Manager OJM" width="480">
</picture>

Keep household consumption within a chosen hourly energy target by adjusting EV charging. This can help avoid a higher grid-tariff capacity step. Savings depend on your household and grid tariff.

**Supported:** one or two Easee chargers, one shared household budget, independent schedules, manual pause and current control. Hot-water tanks and floor heating are planned.

## Requirements

- Home Assistant **2026.2 or newer**.
- Easee devices configured in Home Assistant. **Enable the Voltage sensor on every charger** and wait for a measured value.
- A HAN power sensor in W or kW and [EnergyTariff](https://github.com/epaulsen/energytariff), configured with that meter.

## Install

Download a [release](https://github.com/ojm88/smart-load-manager/releases), copy `custom_components/smart_load_manager` into your Home Assistant `config/custom_components/`, and restart.

From HA 2026.11, **Settings → Marketplace** also supports adding this repository as a custom **Integration**: `https://github.com/ojm88/smart-load-manager`. A GitHub connection is required for custom repositories. See the [official guide](https://contributors.home-assistant.io/marketplace/how-it-works/).

## Set up

1. **Settings → Devices & services → Add integration → Smart Load Manager OJM.**
2. Select the household HAN power, EnergyTariff **used this hour**, and safety margin.
3. Choose **EV charging**, select the first Easee charger, then finish or add a second.
4. Set **Forbruksgrense** on the household device. Ensure only one controller regulates each charger, then enable SLM automatic control deliberately on each charger.

The integration has two native groups: **Boligen / Household** for shared measurements and the budget; **Lading / Charging** for the chargers. Under **Configure**, edit shared sources or choose **Add charger** / **Remove charger**. Adding a charger keeps the existing charger and lists only unused Easee devices. Changing the charger selection reloads SLM and automatic control starts off again.

## How it works

SLM combines the energy used so far this hour with the current HAN power and the safety margin. It adjusts the chargers' dynamic current limits to leave room for other household use. The focus is the capacity tariff; there is no spot-price optimization.

With two chargers, choose **Charge both** to share available power, or **One at a time**. Each charger has a **First priority** switch: choosing one automatically makes the other secondary. These are SLM priorities, not Easee hardware roles. Each charger keeps its own schedule and phase selection.

Required missing measurements stop automatic allocation. Capacity is reassigned only after subsequent measurements confirm a requested reduction. Available, unchanged Easee power readings do not expire just because their timestamp is old. HAN freshness remains required.

## Dashboard and measurements

Run **Developer tools → Actions → `smart_load_manager.get_dashboard`**. Paste the returned `yaml` into a **Manual card** in your existing dashboard. It uses actual registered IDs, including user-renamed entities.

Each charger has six main measurements: status, power, current, recommended current, active phases, and voltage. Names consistently end with the charger name, such as **Volt Garasje** and **Volt Tesla**. The household status explains why chargers run or wait; detailed electrical limits remain attributes. With two chargers, a diagnostic shows each charger's priority.

[Guide in Norwegian](docs/manual_nb.md) · [English guide](docs/manual_en.md) · [Changes](CHANGELOG.md)

Automatic control starts off after restart. Enable it deliberately on each charger. SLM does not replace electrical protection. This project is under development; see [project status](docs/PROJECT_STATUS.md) for validation.

## Next

Hot-water tanks and floor-heating zones under the same household budget. Floor heating is planned through [Versatile Thermostat](https://github.com/jmcollin78/versatile_thermostat); thermal control is not implemented yet.

## Thanks and support

Thanks to [Home Assistant](https://www.home-assistant.io/), the Easee integration maintainers, and [EnergyTariff / Erling Paulsen](https://github.com/epaulsen/energytariff). These projects are independently maintained.

A voluntary coffee-support link will be added when the support account is ready.

## Picker comparison in beta 7

After installation and restart, administrators can open **SLM velgertest** in the sidebar. Compare **Rask liste** with **Velger med logo**, then try a first and a second charger. These are temporary test selections; nothing is saved or sent to chargers. The normal setup continues to use the compact dropdown. No YAML or extra file copying is needed. See [test instructions](experiments/logo-picker/README.md).

## Logo picker in setup

Choose **EV charging – logo picker (test)** to open the native-logo picker in a separate HA page. Choose one or two chargers and confirm, then return to the original setup dialog to finish. Configure → Add/remove charger also offers **Add charger with logo (test)**. The compact picker is available alongside it. Choices are checked again on the server; cancellation creates no installation. Safari/Companion navigation acceptance is pending.
