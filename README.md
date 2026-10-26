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

## Before setup

Install and configure Home Assistant’s **Easee** integration and [EnergyTariff](https://github.com/epaulsen/energytariff). In Smart Load Manager setup, select your Easee charger, the same instantaneous HAN power sensor used by EnergyTariff (unit W or kW), EnergyTariff’s **used this hour** sensor, and a safety margin.

After setup, select **Forbruksgrense** (4.5–20 kWh, in 0.5 kWh steps). This is the Smart Load Manager target.

## Dashboard

- [Norwegian guide](docs/manual_nb.md)
- [English guide](docs/manual_en.md)
- [One charger: complete section card](examples/lovelace/charging_card.yaml).
- [Two chargers: complete section card](examples/lovelace/two_chargers_card.yaml).

Both are single **Manual cards inside an existing section**, not complete views. Replace the old card when moving to two chargers. For ready-to-paste YAML using your actual charger entity IDs, open **Developer tools → Actions**, run **Smart Load Manager: Get dashboard card** (`smart_load_manager.get_dashboard`), and copy the returned `yaml` value into a Manual card. This also handles entity IDs you renamed yourself. The static two-charger example instead needs `CHARGER_SUFFIX` replaced with the `card_suffix` attribute from the new charger's **Phase advice** sensor.

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
