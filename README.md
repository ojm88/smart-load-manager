# Smart Load Manager OJM

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/smart_load_manager/brand/dark_logo@2x.png">
  <img src="custom_components/smart_load_manager/brand/logo@2x.png" alt="Smart Load Manager OJM" width="480">
</picture>

[![Tests](https://github.com/ojm88/smart-load-manager/actions/workflows/tests.yml/badge.svg)](https://github.com/ojm88/smart-load-manager/actions/workflows/tests.yml)
[![Release](https://img.shields.io/github/v/release/ojm88/smart-load-manager?include_prereleases)](https://github.com/ojm88/smart-load-manager/releases)

Home Assistant integration that adjusts one or two Easee chargers to leave room for household consumption within a chosen hourly energy target. This can help avoid a higher grid-tariff capacity step; savings depend on your household and tariff.

[🇳🇴 Norsk brukerveiledning](docs/manual_nb.md) · [English guide](docs/manual_en.md)

[Setup](#configuration) · [Controls](#everyday-controls) · [Dashboard](#ready-made-dashboard-yaml) · [Troubleshooting](#when-charging-waits)

## Why this is useful in Norway

Many Norwegian grid companies use household capacity steps based on hourly consumption peaks. At [Glitre Nett](https://www.glitrenett.no/kunde/nettleie-og-priser/nettleiepriser-privatkunde), the capacity charge is based on the average of the three highest daily hourly peaks in a month. Charging alongside cooking, heating and hot water can push a home into a higher step.

SLM reduces charging when the home needs more power and gives charging more room when household demand falls. The goal is to use the available hourly budget more evenly. This may reduce capacity charges and helps spread demand on the grid; it does not guarantee a lower bill. Check your own grid company's steps and rules. [NVE explains why smoothing consumption matters](https://www.nve.no/reguleringsmyndigheten/kunde/stroemnettet/hva-er-nettleie/).

## Requirements

- Install and configure the [latest Easee integration](https://github.com/nordicopen/easee_hass/releases/latest). Easee v2026.11.0 requires **Home Assistant 2026.10.0 or newer**.
- Easee chargers configured in Home Assistant. On **each** charger, enable **Current (A)** and **Voltage (V)** under **Settings → Devices & services → Easee → charger → Entities**. Show disabled entities, enable both and wait for measured values. Charging power must also be available.
- A HAN power sensor in W or kW.
- A sensor for **energy used since the start of the current clock hour**, in kWh, is required. **[EnergyTariff](https://github.com/epaulsen/energytariff) is recommended** because it supplies this and several other useful sensors. Equivalent sources, such as Tibber’s accumulated consumption current hour, can also be selected. A spot-price sensor cannot replace hourly energy.
- Optional: estimated total consumption for the current clock hour in kWh, from EnergyTariff (`energy_estimate_this_hour`), [Tibber](https://www.home-assistant.io/integrations/tibber/) (**Estimated consumption current hour**) or another compatible integration. Select it during setup or under **Configure → Household**; it is informational and does not replace measured hourly consumption. Existing installations retain `sensor.energy_estimate_this_hour` as the default when no source is selected.

## Installation

### Marketplace

Use Marketplace on **Home Assistant 2026.11 or newer**.

[![Open Smart Load Manager OJM in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=ojm88&repository=smart-load-manager&category=integration)

Use the button above as a shortcut, or add the repository from the Marketplace menu:

1. Open **Settings → Marketplace → ⋮ → Custom repositories**.
2. Connect GitHub if prompted.
3. Paste `https://github.com/ojm88/smart-load-manager`, select **Integration**, and click **Add**.
4. Find **Smart Load Manager OJM** in Marketplace and select **Install**.

After a first install, go straight to **Settings → Devices & services → Add integration** and select **Smart Load Manager OJM**. Home Assistant asks for a restart when updating an integration it has already loaded.

[Home Assistant Marketplace repository guide](https://contributors.home-assistant.io/marketplace/guides/catalog/#the-link-to-your-repository)

### Manual

Download a [release](https://github.com/ojm88/smart-load-manager/releases), copy `custom_components/smart_load_manager` into your HA `config/custom_components/` folder and restart.

## Configuration

1. Open **Settings → Devices & services → Add integration → Smart Load Manager OJM**.
2. Select **Household power (HAN)** and **Energy used this hour**. The hourly estimate is optional. The default **0.3 kWh safety margin** reserves part of the budget for delays and changing consumption; a larger margin leaves less charging capacity.
3. Choose **EV charging – Easee**, select the first charger and confirm its actual supply/wired phases. Finish with one charger or add a second; only unused chargers are offered. At most two chargers are supported.
4. Set the household consumption target on **SLM – Boligen** and check measurement readiness. Disable older automations that adjust the same charging limits, then enable automatic control on each charger you want SLM to regulate. No user-created helpers are required.

Choose **230 V IT/TT – single phase / three phase** or **400/230 V TN – single phase / three phase** for each charger’s actual wiring. This does not set a fixed calculation voltage: SLM uses measured Easee voltages. Phase-mode control appears only for three-phase connections. Confirm existing chargers under **Configure → Chargers → Charger connections** before enabling control.

**SLM – Boligen** contains the shared budget, status, measurement readiness, read-only charging overview and total measured charging power. **Lading / Charging** groups the chargers and their individual controls. Use **Configure → Household sources and safety margin** to change sources, or **Chargers and connections** to add/remove chargers and correct physical wiring. Existing settings are retained; changing physical wiring sends 0 A and disables automation on the affected charger. [Full setup and maintenance guide](docs/manual_en.md#changing-setup-later).

## Choose a realistic household target

**Forbruksgrense** is the home's total hourly energy target, including charging. Choose 4.5–20 kWh in 0.5 kWh steps. It is not a separate charging allowance or an instantaneous fuse limit. For example, 10 kWh during one clock hour corresponds to 10 kW average power over that hour; SLM also reserves the configured safety margin.

Choose a target that fits normal household demand, your grid tariff and how much charging you need. **If it is too low, the home may use nearly the whole budget before charging gets a turn.** With too little room for the charger's minimum charging current, charging waits. Two chargers share the same remaining budget; they do not each receive the full target. The lowest selectable step is therefore not necessarily a useful choice for your home.

## Supported functions

| Function | Behavior |
| --- | --- |
| Shared household budget | Combines hourly energy, current HAN power and a safety margin to adjust charging limits. |
| One or two chargers | Charge both or one at a time, with a selectable first priority. |
| Per-charger controls | Independent schedule, pause, manual current and phase selection. |
| Measurements | Live status, charging power, measured/recommended charging current, active phases and voltage. |
| Actual consumption | After three minutes of stable positive draw, forecasts and settled manual reservations can use measured power +100 W instead of unused offers. Settled observations survive temporary pauses; completion or disconnection starts learning again. |
| Completed sessions | Completed sessions confirmed at zero power release unused capacity and receive no ordinary budget commands. A new request triggers immediate minimum-current assessment. Easee status is displayed as reported. |
| Regulation | Recalculates on source changes. Evaluates connection, schedule boundaries and user start/stop controls immediately. Otherwise adjusts limits every five minutes; forecast risks and invalid measurements can require earlier reductions. |
| Explanations | Separate capacity waits, pending regulation and positive offers awaiting charger/vehicle response. Show minimum charging power, relevant advice and the next ordinary assessment during eligible waiting. |
| Dashboard | `smart_load_manager.get_dashboard` returns a compact Manual card using actual registered entity IDs. Connected/disconnected status is explicit; charging details appear while charging. |

## Everyday controls

Each charger has its own **Automatic load control**, **Charging pause**, **Manual charging current**, **Schedule/start time** and, for three-phase wiring, **Phase selection**. There is no combined automation switch.

- Turning automation **off** requests the lowest valid manual charging current; it is not a stop command. Choose a manual current afterwards if needed. Pause, schedules and measurement guards still apply.
- Use **Charging pause** to stop at 0 A. The manual slider is hidden while unavailable. Existing pauses can be removed even if charging has completed.
- Scheduling allows a daily **12-hour window**, e.g. 23:00–11:00. It also applies to manual charging; disable scheduling to charge without that window.
- With two chargers, choose **Charge both** or **One at a time** and set **First priority**. Both share the remaining household capacity; only eligible automatic chargers participate in this allocation.
- New chargers start with automation off. Saved automation, pause, schedule, manual and household choices survive ordinary restart/update. Easee stores phase mode.

Easee's configured installation/user limits and internal circuit sharing still apply. SLM sets charging offers against the household budget; it does not replace Easee's internal limits or electrical protection. Minimum current is 11 A for measured 230 V three-phase charging, otherwise 6 A. Maximum comes from Easee; do not copy app limits into SLM. A consumption observation is a forecast, not a new electrical maximum. See [how regulation works](docs/manual_en.md#how-charging-is-regulated) for pause/relearning and timing details.

## Sensors and explanations

Household information is grouped under **SLM – Boligen**. Each charger's measurements end with its name, so the two chargers are easy to distinguish.

| Sensor | What it shows |
| --- | --- |
| Load control status | Shared status explaining whether charging runs, waits, is paused or is limited. Attributes provide per-charger explanations used by the dashboard. |
| Measurement status | Whether the shared measurement inputs are ready. Attributes identify source entities and the age of the HAN reading. |
| Charging status | The charger's reported state, such as charging, waiting, completed or disconnected. |
| Power to car | Present charging power in W. |
| Measured charging current | Present current measured by Easee in A. |
| Recommended charging current | The current limit SLM recommends now, in A; this is not measured current or proof that charging is running. |
| Phases in use | Number of phases actually drawing current during charging. |
| Voltage | Charging voltage from relevant Easee measurements. Single-phase TN shows phase–neutral; three-phase TN shows inferred line voltage. The confirmed supply determines which terminal pairs are used. |
| Charging priority | With two chargers, a diagnostic showing first or second priority in SLM. |
| Charging / Total charging power | Read-only overview and measured sum, including manual chargers. Missing readings yield an unknown total. |

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

The generator uses your actual registered entity IDs and charger names, including custom names. Both chargers are named in the **Anbefalt ladestrøm** (recommended charging current) and **Målt ladestrøm** (measured charging current) graph legends. The status card is always Norwegian, even on English HA servers. It combines household explanations, charger measurements and controls. Ready-made [one-charger](examples/lovelace/charging_card.yaml) and [two-charger](examples/lovelace/two_chargers_card.yaml) YAML templates are also available; generating the card avoids manually adapting their entity IDs.

### When to generate the card again

The YAML card is a saved snapshot of the configured layout, entity references and charger labels. It is **not automatically regenerated** when setup changes. Run `smart_load_manager.get_dashboard` again and replace the existing Manual card YAML after:

- Adding, removing or replacing a charger.
- Changing a charger’s physical connection, measurement sources or entity IDs referenced by the card.
- Renaming chargers when their names are used in the card's headings or labels.
- Installing a feature that changes the generated card layout or entities.

Generate new YAML when updating to beta 22 to adopt the revised controls, waiting times and named graph legends.

Normal changes to the consumption target, safety margin, priority, charging mode, schedule, phase selection or pause do **not** require new YAML. Their states and measurements update through the existing entity references. Regenerating the card replaces the generated layout; keep a copy of any manual customizations first.

## When charging waits

| Explanation | What it means / what to check |
| --- | --- |
| Waiting for capacity | The remaining budget cannot support minimum charging power. Reduce other consumption or wait; check that the household target is realistic. |
| Waiting for regulation | A recommendation has changed, but the last sent limit still applies. Check the next ordinary assessment time; this is not a promised charging start. |
| Positive limit sent, Easee still waiting | SLM has offered current. If persistent, check vehicle schedules, charge limits and Easee restrictions. |
| Waiting for measurements | Open Measurement status. Check HAN, measured hourly energy, enabled Easee current/voltage/power and reported limits. |
| Waiting for reduction | New measured confirmation is needed before capacity transfers between chargers. An idle unused charger does not need to repeat unchanged zero readings. |
| Schedule / Pause / Manual | Check that charger's independent controls. |

Valid HAN reports are accepted for up to 120 seconds, including unchanged values reported again. Invalid or missing required inputs hold automatic charging; recovery is assessed immediately. A valid unchanged Easee power reading does not expire just because its timestamp is old. Download diagnostics while a persistent issue is present, before restart/reload: **integration entry → ⋮ → Download diagnostics**. The last 4096 anonymous events are kept in memory. [Detailed troubleshooting](docs/manual_en.md#when-charging-waits).

## Limitations and testing

This project is under development. Physical acceptance of all new behavior, simultaneous two-car operation and actual Companion rendering remains pending. Software tests do not establish hardware acceptance. Automated tests cover calculations, allocation and Home Assistant setup; see [validation status](docs/PROJECT_STATUS.md).

- Automatic control starts **off for new chargers**; saved choices survive restart/update.
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
