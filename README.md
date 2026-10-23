# Smart Load Manager OJM — beta.17

Smart Load Manager OJM helps keep your home’s electricity use within the hourly limit you choose. It uses your HAN meter and EnergyTariff to adjust Easee charging, leaving room for the rest of the home’s consumption.

That can help avoid expensive electricity-demand tiers. Depending on your tariff and household use, avoiding peaks may save thousands of kroner over a year; savings are not guaranteed.

![Smart Load Manager OJM — EV charging and household load management](docs/images/smart-load-manager-ojm.jpg)

## In short

- Choose **Forbruksgrense** once for the home. The integration uses it as the hourly energy target.
- Smart Load Manager checks the HAN power meter and energy already used this hour, then adjusts the Easee charging limit.
- **Automatic load control** starts off. When it is off, you can set a manual charging current instead.
- Choose one phase, three phases, or automatic phase selection.
- **Ladepause** sends 0 A to Easee. Turning the pause off resumes automatic control, or restores the previous manual limit when it is still safe to do so.
- Charging times are optional. No user-created Home Assistant helpers or YAML automations are required.

## Before setup

Install and configure the Home Assistant Easee integration and EnergyTariff. In Smart Load Manager setup, select your Easee charger, the same instantaneous HAN power sensor used by EnergyTariff (unit W or kW), EnergyTariff’s **used this hour** sensor, and a safety margin.

After setup, select **Forbruksgrense** (4.5–20 kWh, in 0.5 kWh steps). This is the Smart Load Manager target. EnergyTariff supplies the energy used and estimate; its own target is not copied into this integration. Automatic control is off until you turn it on.

## Dashboard

- [Norwegian guide](docs/manual_nb.md)
- [English guide](docs/manual_en.md)
- [One card for an existing dashboard section](examples/lovelace/charging_card.yaml) — add a Manual card and paste the complete file.
- [Complete dashboard view](examples/lovelace/charging_view.yaml) — paste into a view’s raw YAML editor.

The card uses standard Home Assistant cards and EnergyTariff’s own `sensor.energy_used_this_hour`, `sensor.energy_estimate_this_hour`, and `sensor.average_peak_hour_energy` entities.

## Safety and scope

Automatic control is opt-in and starts off after a Home Assistant restart. When it is active, invalid meter or tariff data, missing electrical information, a closed schedule, or an unavailable Easee current limit makes the integration send 0 A. The selected Easee dynamic limit remains in place until the integration changes it, matching the previous automation’s behavior.

The agreed minimum current is 11 A for measured 230 V three-phase charging, and 6 A otherwise. There is no vehicle learning. The current beta supports one configured load entry per Home Assistant installation; a shared allocator is needed before multiple chargers or household loads can safely share the same budget.

## Checks

Run the automated tests with `python -m unittest discover -s tests -v`. GitHub Actions also checks Home Assistant imports and runtime behavior. These checks do not replace testing in your own Home Assistant setup and with your charger. Keep the existing automation disabled while testing the integration’s automatic control.
