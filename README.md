# Smart Load Manager OJM

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="custom_components/smart_load_manager/brand/dark_logo@2x.png">
  <img src="custom_components/smart_load_manager/brand/logo@2x.png" alt="Smart Load Manager OJM — valgt effekttrinn" width="560">
</picture>

Smart Load Manager OJM helps your home stay within a chosen hourly energy limit. It reads your HAN meter and the energy already used during the hour, then adjusts one or two Easee chargers so there is more room for the rest of the home.

The aim is simple: avoid unnecessary household peaks that can move you into a more expensive grid-tariff step. Whether this saves money depends on your grid company, tariff rules, and household. It is not a guaranteed saving.

![Smart Load Manager OJM — EV charging and household load management](docs/images/smart-load-manager-ojm.jpg)

## Why this project exists

In Norway, the monthly grid charge can depend on how much power a home uses at its busiest times. Grid companies publish different steps and prices. For example, Glitre Nett’s published private-customer tariff shows a substantial monthly price difference between some neighboring steps. The exact rules and prices vary by grid company and can change, so check your own grid company’s current tariff. [Glitre Nett: grid rent and prices](https://www.glitrenett.no/kunde/nettleie-og-priser/nettleiepriser-privatkunde).

The long-term goal is to keep household consumption within the chosen hourly limit by shifting controllable resistive (ohmic) loads, such as electric hot-water heating and floor heating, and adjusting the current available for EV charging. Hot water and heated floors can store heat for later, while EV charging can slow down or wait when the home needs the capacity. Easee EV charging is supported today; hot-water and floor-heating control are planned extensions.

The integration does not try to control every appliance. Lights, cooking, tumble dryers, and air-to-air heat pumps have changing use or need to work when needed. The first supported load is an Easee EV charger. Hot-water and floor-heating control remain planned features.

The focus is the grid-capacity part of the bill, not chasing the cheapest spot-price hour. Optional night scheduling is available because some grid tariffs charge less at night. The same scheduling idea may be useful for other controllable loads later.

## In short

- Choose **Forbruksgrense** once for the home. Smart Load Manager uses it as the hourly energy target.
- It checks the HAN power meter and energy already used this hour, then adjusts the Easee charging limit.
- **Automatic load control** starts off. When it is off, you can set a manual charging current instead.
- Choose single phase, three phases, or automatic phase selection.
- **Ladepause** sends 0 A to Easee. Turning the pause off resumes automatic control, or restores the previous manual limit when it is still safe.
- Optional charging times are included. You do not need to create Home Assistant helpers or YAML automations.

## Installation

### Marketplace — Home Assistant 2026.11 onward

1. Open **Settings → Marketplace**.
2. Add `https://github.com/ojm88/smart-load-manager` as a custom repository,
   category **Integration**, if it is not already listed. A custom repository
   requires a connected GitHub account.
3. Download **Smart Load Manager OJM**. Select a pre-release only to test a beta.
4. Restart Home Assistant when requested.
5. Open **Settings → Devices & services → Add integration**, search for
   **Smart Load Manager OJM**, and follow setup below.

Marketplace is included starting with HA 2026.11. On earlier HA versions, use
manual installation below. See the [official Marketplace guide](https://contributors.home-assistant.io/marketplace/how-it-works/).

### Manual installation

Download the desired [release](https://github.com/ojm88/smart-load-manager/releases).
Copy its `custom_components/smart_load_manager` directory into your Home
Assistant `config/custom_components/` directory. Restart Home Assistant, then
add **Smart Load Manager OJM** under **Settings → Devices & services**.

## Before setup

> **Required for every Easee charger: enable the Voltage sensor first.**
> A working charger in Easee does not mean its diagnostic sensors are enabled.
> Open **Settings → Devices & services → Easee → the charger → Entities**,
> include disabled entities, open **Voltage**, and enable it. Wait until it
> shows a measured value before adding the charger to Smart Load Manager.
> Repeat this for **each charger**, including a second charger added later.


Install and configure Home Assistant’s **Easee** integration and [EnergyTariff](https://github.com/epaulsen/energytariff). In Smart Load Manager setup, select your Easee charger, the same instantaneous HAN power sensor used by EnergyTariff (unit W or kW), EnergyTariff’s **used this hour** sensor, and a safety margin.

After setup, select **Forbruksgrense** (4.5–20 kWh, in 0.5 kWh steps). This is the Smart Load Manager target.

## Dashboard

- [Norwegian guide](docs/manual_nb.md)
- [English guide](docs/manual_en.md)
- [One charger: complete section card](examples/lovelace/charging_card.yaml).
- [Two chargers: complete section card](examples/lovelace/two_chargers_card.yaml).

Both are single **Manual cards inside an existing section**, not complete views. Replace the old card when moving to two chargers. For ready-to-paste YAML using your actual charger entity IDs, open **Developer tools → Actions**, run **Smart Load Manager: Get dashboard card** (`smart_load_manager.get_dashboard`), and copy the returned `yaml` value into a Manual card. This also handles entity IDs you renamed yourself. The static two-charger example instead needs `CHARGER_SUFFIX` replaced with the `card_suffix` attribute from the new charger's **Charging status** sensor.

## Two chargers

Add the first charger normally. Later open **Settings → Devices & services → Smart Load Manager → Configure → Add charger**, and choose the other Easee device. Alternatively use **Add integration → Smart Load Manager** again. The second charger inherits the household meter sources and safety margin. Existing IDs and settings stay intact; new entities receive a stable charger-name/device suffix. Enable automatic control on each charger you want included in distribution.

- **Charging mode / Lad begge:** share available power equally, subject to each charger's minimum and maximum. When only one fits, the selected priority charger receives capacity. If it cannot receive its minimum, charging waits.
- **One at a time / Én om gangen:** the selected priority charger goes first. The other takes over when the vehicle stops requesting charging, disconnects, is manually paused, or is outside its schedule.
- **First priority:** choose the actual charger name. This is a software priority, not Easee's technical master/slave role.
- Each charger has its own phase selection, pause, schedule, manual current and diagnostic sensors. The household **Forbruksgrense** is shared and displayed once.
- **Phase advice** suggests single phase only when the measured available capacity could support both at their single-phase minimum. It never changes the setting automatically. Vehicle compatibility still matters.
- Easee's `Completed` means the vehicle stopped requesting power; it does not reveal battery percentage or prove the battery is full.

Allocation uses the HAN household total and both charger powers. Reductions are sent before increases, and subsequent telemetry must confirm a reduction before capacity is reassigned. Missing/stale required readings pause automatic allocation. Manual charging is outside the selected distribution mode and counts as household load. No manual circuit-fuse configuration is required; Easee's reported limits still apply.

The graph reads EnergyTariff’s own `sensor.energy_used_this_hour`, `sensor.energy_estimate_this_hour`, and `sensor.average_peak_hour_energy` entities directly. Smart Load Manager does not create copies just to display them.

## Sensors and controls

### SLM – Boligen: the household overview

The beta.4 draft has a separate **SLM – Boligen** device for settings and
information shared by the home, independent of charger priority. Forbruksgrense
and the following two sensors belong here, not on an individual charger:

| Sensor | Default entity ID | Purpose |
| --- | --- | --- |
| Load control status | `sensor.slm_status` | Plain-language overview of what SLM is doing and why. This is the information source for both Markdown cards. |
| Measurement status | `sensor.slm_measurement_status` | Shared diagnostic readiness, with source IDs, HAN measurement age and validity as attributes. |

Load control status has a short state plus these attributes:

- `summary`: a short, plain-language household explanation.
- `consumption_limit_kwh`, `han_power_w`, `energy_used_kwh`, `safety_margin_kwh`, `minutes_left`: the household inputs behind the explanation.
- `charging_mode`, `priority_charger`, `distribution_explanation`: how the chargers share available capacity (only relevant with two chargers).
- `phase_advice`: one shared suggestion, only when a phase change could help.
- `controlled_loads`: one row for every configured charger, with its name,
  status, plain-language explanation, current, power, recommended current,
  minimum/maximum, schedule, first-priority flag and measurement readiness.
  Missing peers remain represented rather than disappearing from the overview.

The Markdown cards read only this sensor, so they do not need their own charging
rules. A device measurement reports actual charging; a recommendation is not
proof that the car is already drawing current. Completion does not prove a full
battery. For the [architecture and extension contract](docs/ARCHITECTURE.md),
see the separation between control and household presentation.

### Five main sensors per charger

| Sensor | Default first-charger ID in existing installations | Purpose |
| --- | --- | --- |
| Charging status | `sensor.slm_charger_status` | Disconnected, charging, waiting or finished; electrical details and `card_suffix` are attributes. |
| Charging power | `sensor.slm_charger_power` | Actual power delivered to the vehicle, in whole W. |
| Charging current | `sensor.slm_charger_current` | Actual measured current, also used in the graph. |
| Recommended current | `sensor.slm_recommended_current` | Calculated current; `minimum_current_a` and `maximum_current_a` are attributes. |
| Active phases | `sensor.slm_active_phases` | Number of phases actually drawing current. |

The second charger uses its stable charger suffix. Charger controls remain
automatic control, pause, phase selection, manual current (automatic control
off), schedule and start time. Per-charger Charging explanation and Phase advice
are no longer created in new setups; their information is collected in the
household sensor. Shared on/off status is read from switches instead of copies.
The household card uses the selected HAN source and EnergyTariff sources
directly; SLM does not create extra entities for graph display.

### Upgrading and using the updated cards

Previously registered sensors keep their unique IDs and remain under
**Diagnostics** for existing cards/automations. No existing registry entries
are deleted or automatically disabled. New installations create five main
sensors per charger plus the two shared household sensors. The entity naming
migration requested for beta.4 is still separate pending work; do not assume
existing first-charger IDs have already changed.

Generate the updated card with `smart_load_manager.get_dashboard`. It resolves
actual registered IDs, user-renamed IDs and the configured HAN entity. Static
examples require `sensor.SLM_HAN_POWER_SOURCE` replaced with the HAN source;
the two-charger example also requires `CHARGER_SUFFIX` from the second charger's
**Charging status** sensor. Both are Manual cards inside an existing section.

## Acknowledgements

This project builds on the Home Assistant open-source community and its shared work. Thank you to the maintainers and contributors who make these integrations possible.

- [Home Assistant Easee integration](https://www.home-assistant.io/integrations/easee/) provides the charger entities and controls used by Smart Load Manager.
- [EnergyTariff by Erling Paulsen](https://github.com/epaulsen/energytariff) provides the Norwegian grid-tariff sensors used for hourly energy. EnergyTariff must be installed and configured first. Thank you for making it available to the community.
- [Versatile Thermostat (VTherm)](https://github.com/jmcollin78/versatile_thermostat) is a project to learn from if thermal loads such as hot water or floor heating are explored later. It is not used by this integration today.

These projects remain independently maintained. Mention here is attribution, not an endorsement or claim of affiliation.

## Support the project

If Smart Load Manager is useful to you, you can support continued development with a coffee. **The donation link will be added when the project support account is ready.** Donations are optional.

## Safety and scope

Automatic control is opt-in and starts off after a Home Assistant restart. When active, invalid or stale meter or tariff data, missing electrical information, a closed schedule, or an unavailable Easee current limit makes the integration send 0 A. Easee keeps the last dynamic limit when automatic control is turned off, matching the existing automation’s behavior.

The agreed minimum current is 11 A for measured 230 V three-phase charging, and 6 A otherwise. There is no vehicle learning. This beta supports up to two Easee chargers under one household budget. More chargers and thermal-load control are future work.

## Waiting for charger measurements

Easee reports charging power on changes, so beta.4 preparation does not expire
an available numeric power value solely because its timestamp is old. Published
beta.3 incorrectly applies a 120-second cutoff in two-charger mode.
Missing/unavailable power values still stop automatic distribution, while
successfully read measurements remain visible and Charging explanation names
the source. HAN freshness remains required. Capacity is not transferred after
a reduction until subsequent current/power measurements confirm it. Command
failures remain errors. These changes are not yet published.

## Changing household measurement sources

In the beta.4 draft, **Configure → Household sources and safety margin** lets
you change the HAN sensor, EnergyTariff used-this-hour sensor and safety margin
at any time, including after both chargers have been added. The sources are
validated before they are saved for the installation. Charger identity, budget,
priority and individual schedules are retained. New sources are read on the
next regular coordinator update; no integration restart is required.
**Add charger** is a separate menu choice, offered only below the two-charger
limit. These options changes are prepared locally and are not yet published.
