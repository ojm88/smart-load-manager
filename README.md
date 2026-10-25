# Smart Load Manager OJM

Smart Load Manager OJM helps your home stay within a chosen hourly energy limit. It reads your HAN meter and the energy already used during the hour, then adjusts an Easee charger so there is more room for the rest of the home.

The aim is simple: avoid unnecessary household peaks that can move you into a more expensive grid-tariff step. Whether this saves money depends on your grid company, tariff rules, and household. It is not a guaranteed saving.

![Smart Load Manager OJM — EV charging and household load management](docs/images/smart-load-manager-ojm.jpg)

## Why this project exists

In Norway, the monthly grid charge can depend on how much power a home uses at its busiest times. Grid companies publish different steps and prices. For example, Glitre Nett’s published private-customer tariff shows a substantial monthly price difference between some neighboring steps. The exact rules and prices vary by grid company and can change, so check your own grid company’s current tariff. [Glitre Nett: grid rent and prices](https://www.glitrenett.no/kunde/nettleie-og-priser/nettleiepriser-privatkunde).

Some household loads can be moved in time. An electric car can charge when the home has room under its chosen limit. In future, a hot-water tank or floor heating could also be scheduled because they can store heat for later. This project is intended for loads whose use can be planned and whose effect can be estimated.

The integration does not try to control every appliance. Lights, cooking, tumble dryers, and air-to-air heat pumps have changing use or need to work when needed. The first supported load is an Easee EV charger. Other load types and shared control are future work, not current features.

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

After setup, select **Forbruksgrense** (4.5–20 kWh, in 0.5 kWh steps). This is the Smart Load Manager target. EnergyTariff supplies the energy used and estimate; its own target is not copied into this integration. Automatic control stays off until you turn it on.

## Dashboard

- [Norwegian guide](docs/manual_nb.md)
- [English guide](docs/manual_en.md)
- [One card for an existing dashboard section](examples/lovelace/charging_card.yaml) — add a Manual card and paste the complete file.
- [Complete dashboard view](examples/lovelace/charging_view.yaml) — paste into a view’s raw YAML editor.

The graph reads EnergyTariff’s own `sensor.energy_used_this_hour`, `sensor.energy_estimate_this_hour`, and `sensor.average_peak_hour_energy` entities directly. Smart Load Manager does not create copies just to display them.

## Acknowledgements

This project builds on the Home Assistant open-source community and its shared work. Thank you to the maintainers and contributors who make these integrations possible.

- [Home Assistant Easee integration](https://www.home-assistant.io/integrations/easee/) provides the charger entities and controls used by Smart Load Manager.
- [EnergyTariff by Erling Paulsen](https://github.com/epaulsen/energytariff) provides the Norwegian grid-tariff sensors used for hourly energy. EnergyTariff must be installed and configured first. Thank you for making it available to the community.
- [Versatile Thermostat (VTherm)](https://github.com/jmcollin78/versatile_thermostat) is a project to learn from if thermal loads such as hot water or floor heating are explored later. It is not used by this integration today.

These projects remain independently maintained. Mention here is attribution, not an endorsement or claim of affiliation.

## Support the project

If Smart Load Manager is useful to you, you can support continued development with a coffee. **The donation link will be added when the project support account is ready.** Donations are optional.

## License

No license has been selected for this repository yet. Until one is added, the code is publicly viewable, but reuse and redistribution are not explicitly licensed.

## Safety and scope

Automatic control is opt-in and starts off after a Home Assistant restart. When active, invalid or stale meter or tariff data, missing electrical information, a closed schedule, or an unavailable Easee current limit makes the integration send 0 A. Easee keeps the last dynamic limit when automatic control is turned off, matching the existing automation’s behavior.

The agreed minimum current is 11 A for measured 230 V three-phase charging, and 6 A otherwise. There is no vehicle learning. This release supports one configured load entry per Home Assistant installation; a shared allocator is needed before multiple chargers or household loads can safely share the budget.

## Checks

Run the automated tests with `python -m unittest discover -s tests -v`. GitHub Actions also checks Home Assistant imports and runtime behavior. These checks do not replace testing in your own Home Assistant setup and with your charger. Keep any existing automation disabled while testing the integration’s automatic control.
