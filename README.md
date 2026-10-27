# Smart Load Manager OJM

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/smart_load_manager/brand/dark_logo@2x.png">
  <img src="custom_components/smart_load_manager/brand/logo@2x.png" alt="Smart Load Manager OJM" width="480">
</picture>

[![Tests](https://github.com/ojm88/smart-load-manager/actions/workflows/tests.yml/badge.svg)](https://github.com/ojm88/smart-load-manager/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/ojm88/smart-load-manager?include_prereleases)](https://github.com/ojm88/smart-load-manager/releases)

Home Assistant integration that adjusts one or two Easee chargers to leave room for household consumption within a chosen hourly energy target. This can help avoid a higher grid-tariff capacity step; savings depend on your household and tariff.

[🇳🇴 Norsk brukerveiledning](docs/manual_nb.md) · [English guide](docs/manual_en.md)

## Why this is useful in Norway

Many Norwegian grid companies use household capacity steps based on hourly consumption peaks. At [Glitre Nett](https://www.glitrenett.no/kunde/nettleie-og-priser/nettleiepriser-privatkunde), the capacity charge is based on the average of the three highest daily hourly peaks in a month. Charging alongside cooking, heating and hot water can push a home into a higher step.

SLM reduces charging when the home needs more power and gives charging more room when household demand falls. The goal is to use the available hourly budget more evenly. This may reduce capacity charges and helps spread demand on the grid; it does not guarantee a lower bill. Check your own grid company's steps and rules. [NVE explains why smoothing consumption matters](https://www.nve.no/reguleringsmyndigheten/kunde/stroemnettet/hva-er-nettleie/).

## Requirements

- Home Assistant **2026.2 or newer**.
- Easee chargers configured in Home Assistant, with an enabled **Voltage** sensor and a measured value on each charger.
- A HAN power sensor in W or kW.
- **[EnergyTariff](https://github.com/epaulsen/energytariff) is required.** Set it up with the same HAN meter before configuring SLM. Its **energy used this hour** sensor supplies the hourly consumption needed for the budget calculation; a spot-price sensor cannot replace it.

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

## Choose a realistic household target

**Forbruksgrense** is the home's total hourly energy target, including charging. It is not a separate charging allowance or an instantaneous fuse limit. For example, 10 kWh during one clock hour corresponds to 10 kW average power over that hour; SLM also reserves the configured safety margin.

Choose a target that fits normal household demand, your grid tariff and how much charging you need. **If it is too low, the home may use nearly the whole budget before charging gets a turn.** With too little room for the charger's minimum charging current, charging waits. Two chargers share the same remaining budget; they do not each receive the full target. The lowest selectable step is therefore not necessarily a useful choice for your home.

## Supported functions

| Function | Behavior |
| --- | --- |
| Shared household budget | Combines hourly energy, current HAN power and a safety margin to adjust charging limits. |
| One or two chargers | Charge both or one at a time, with a selectable first priority. |
| Per-charger controls | Independent schedule, pause, manual current and phase selection. |
| Measurements | Status, power, current, recommended current, active phases and voltage. |
| Explanations | Household status describes why charging runs, waits or is limited. |
| Dashboard | `smart_load_manager.get_dashboard` returns a Manual card using actual registered entity IDs. |

## Sensors and explanations

Household information is grouped under **SLM – Boligen**. Each charger's measurements end with its name, so the two chargers are easy to distinguish.

| Sensor | What it shows |
| --- | --- |
| Load control status | Shared status explaining whether charging runs, waits, is paused or is limited. Attributes provide per-charger explanations used by the dashboard. |
| Measurement status | Whether the shared measurement inputs are ready. Attributes identify source entities and the age of the HAN reading. |
| Charging status | The charger's reported state, such as charging, waiting, completed or disconnected. |
| Power to car | Present charging power in W. |
| Current to car | Present current measured by Easee in A. |
| Recommended charging current | The current limit SLM recommends now, in A; this is not measured current or proof that charging is running. |
| Phases in use | Number of phases actually drawing current during charging. |
| Voltage | Measured or inferred line voltage in V, used in the electrical calculations. |
| Charging priority | With two chargers, a diagnostic showing first or second priority in SLM. |

## Ready-made dashboard YAML

Generate a complete card for your configured charger or chargers:

1. Open **Settings → Tools → Actions**.
2. Find and run **`smart_load_manager.get_dashboard`**. In YAML mode, use:

   ```yaml
   action: smart_load_manager.get_dashboard
   data: {}
   ```

3. Copy the **`yaml`** value from the response.
4. Edit your dashboard, add a **Manual card** inside an existing section, and paste the YAML.

The generator uses your actual registered entity IDs, including custom names. The card combines household explanations, charger measurements and controls. Ready-made [one-charger](examples/lovelace/charging_card.yaml) and [two-charger](examples/lovelace/two_chargers_card.yaml) YAML templates are also available; generating the card avoids manually adapting their entity IDs.

### When to generate the card again

The YAML card is a saved snapshot of the configured layout, entity references and charger labels. It is **not automatically regenerated** when setup changes. Run `smart_load_manager.get_dashboard` again and replace the existing Manual card YAML after:

- Adding, removing or replacing a charger.
- Changing the HAN source or entity IDs referenced by the card.
- Renaming chargers when their names are used in the card's headings or labels.
- Installing a feature that changes the generated card layout or entities.

Normal changes to the consumption target, safety margin, priority, charging mode, schedule, phase selection or pause do **not** require new YAML. Their states and measurements update through the existing entity references. Regenerating the card replaces the generated layout; keep a copy of any manual customizations first.

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

See the [roadmap](docs/ROADMAP.md) for the two-charger acceptance milestone and planned stable **2.0.0** release.

More chargers, hot-water tanks and floor-heating zones sharing the household budget. Floor heating is planned through [Versatile Thermostat](https://github.com/jmcollin78/versatile_thermostat). A voluntary coffee-support link will be added when the account is ready.

## Acknowledgements

Thanks to [Home Assistant](https://www.home-assistant.io/), the Easee integration maintainers and [EnergyTariff / Erling Paulsen](https://github.com/epaulsen/energytariff). These projects are independently maintained.
