# Smart Load Manager OJM – quick guide

## What does it do?

It helps keep your home within the **Forbruksgrense** you choose for each hour. It reads the HAN meter and the energy already used this hour, then adjusts the Easee charging limit to leave room for the rest of the home.

High demand peaks can mean a more expensive electricity tariff tier. Avoiding those peaks may save some households thousands of kroner over a year. The result depends on your tariff and household use; savings are not guaranteed.

## Before setup

Install and configure the **Easee** and **EnergyTariff** Home Assistant integrations first. You need an instantaneous HAN power sensor in W or kW and EnergyTariff’s sensor for energy used this hour. Select the same HAN sensor in both integrations.

In setup, choose your charger, HAN meter, EnergyTariff used-this-hour sensor, and a safety margin. After setup, choose **Forbruksgrense** on the Smart Load Manager device. This is the hourly target used by Smart Load Manager. EnergyTariff provides energy used and its estimate; its own target is not copied into this integration.

You do not need to create Home Assistant helpers or YAML automations.

## How to control charging

- **Automatic load control:** Turn it on when you want the integration to adjust Easee to the hourly limit. It is off after setup and after a Home Assistant restart.
- **Forbruksgrense:** Choose the energy amount for the whole home this hour (4.5–20 kWh).
- **Phase selection:** Choose single phase, three phases, or let Easee choose automatically.
- **Manual charging current:** Use this when automatic load control is off. The slider sets Easee’s limit directly. 0 A pauses charging.
- **Charging pause:** Controls Easee. Turning it on sends 0 A. Turning it off lets automatic control calculate a fresh limit. In manual mode, it restores the previous limit only if current readings and Easee limits still allow it.
- **Schedule:** Optional; allows charging for a 12-hour window starting at the selected time.

Easee keeps the last dynamic limit when automatic control is turned off. Disable your old automation while testing automatic control so the two controllers do not send competing limits.

## Minimum current

The agreed fixed rule is **11 A** for measured 230 V three-phase charging, and **6 A** otherwise. The integration does not learn vehicle behavior.

If the HAN reading, EnergyTariff data, or Easee limits are missing or invalid, automatic control holds the charger at 0 A. The dashboard card explains why charging is waiting or limited.

The **Charging explanation** sensor uses plain language to say why the car is charging, waiting, or receiving less current.

## Dashboard card

Inside an existing dashboard section, choose **Add card → Manual**, open the YAML editor, and paste the complete `examples/lovelace/charging_card.yaml` file. It is one card. Do not paste `charging_view.yaml` into the card editor.

The graph uses:

- `sensor.slm_recommended_current` – recommended current
- `sensor.energy_used_this_hour` – used
- `sensor.slm_charger_current` – measured charging current
- `sensor.energy_estimate_this_hour` – hourly estimate
- `sensor.average_peak_hour_energy` – three-hour average

The EnergyTariff values are read directly; Smart Load Manager does not create extra copies for the graph.

## Safe test

1. Make a Home Assistant backup and note how to re-enable your existing automation.
2. Disable that automation; do not delete or edit it.
3. Install the integration and restart Home Assistant. Leave automatic load control off.
4. Check the meter, energy used, phase/voltage, recommended current, and Easee limits.
5. When present and watching the charger, enable automatic control and confirm its recommendation matches the limit sent to Easee.
6. If anything looks wrong, turn automatic control off and restore your previous automation. Never run both controllers at once.

Automated tests check calculations and service calls. They cannot verify your electrical installation; confirm behavior in Home Assistant and with the Easee charger.
