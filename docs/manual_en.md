# Smart Load Manager OJM – quick guide

See the [installation instructions](../README.md#installation) for Marketplace, Marketplace and manual installation, and the [sensor reference](../README.md#sensors-and-controls).

## Required Easee preparation

> **Required for every Easee charger: enable the Voltage sensor first.**
> A working charger in Easee does not mean its diagnostic sensors are enabled.
> Open **Settings → Devices & services → Easee → the charger → Entities**,
> include disabled entities, open **Voltage**, and enable it. Wait until it
> shows a measured value before adding the charger to Smart Load Manager.
> Repeat this for **each charger**, including a second charger added later.


## What does it do?

It helps keep your home within the **Forbruksgrense** you choose for each hour. It reads the HAN meter and the energy already used this hour, then adjusts the Easee charging limit to leave room for the rest of the home.

High demand peaks can mean a more expensive electricity tariff tier. Avoiding those peaks may save some households thousands of kroner over a year. The result depends on your tariff and household use; savings are not guaranteed.

### Why it was made

In Norway, the grid charge can rise when a home uses a lot of electricity at the same time. Smart Load Manager can move EV charging to hours when the home has more room under the limit you chose. The goal is to avoid unnecessary peaks, not to promise a specific saving. Tariffs and steps differ between grid companies. [Glitre Nett explains its prices and steps here](https://www.glitrenett.no/kunde/nettleie-og-priser/nettleiepriser-privatkunde).

The project focuses on loads that can wait. Hot water and floor heating may be considered later because they can store heat. For now, the integration controls only Easee charging. It does not try to control lights, cooking, tumble dryers, or heat pumps; people need to use those when needed.

The integration does not try to find the cheapest spot-price hour. Optional scheduling can still place charging at night, when many grid companies charge less for grid use. Norgespris and the electricity price are separate parts of the bill; the main goal here is staying below the chosen capacity-tariff step.

Smart Load Manager builds on open-source work shared by the Home Assistant community. Home Assistant’s Easee integration provides access to the charger, and EnergyTariff by Erling Paulsen provides the hourly energy reading used in the calculation. Thank you to them and to everyone who shares their work. [Versatile Thermostat (VTherm)](https://github.com/jmcollin78/versatile_thermostat) may be useful inspiration if thermal-load control is explored later; it is not part of this integration today.

## Before setup

Install and configure the **Easee** and **EnergyTariff** Home Assistant integrations first. You need an instantaneous HAN power sensor in W or kW and EnergyTariff’s sensor for energy used this hour. Select the same HAN sensor in both integrations.

In setup, choose your charger, HAN meter, EnergyTariff used-this-hour sensor, and a safety margin. After setup, choose **Forbruksgrense** on the Smart Load Manager device. This is the hourly target used by Smart Load Manager.

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

Inside an existing dashboard section, choose **Add card → Manual**, open the YAML editor, and paste the complete `examples/lovelace/charging_card.yaml` file. It is one card.

The graph uses:

- `sensor.slm_recommended_current` – recommended current
- `sensor.energy_used_this_hour` – used
- `sensor.slm_charger_current` – measured charging current
- `sensor.energy_estimate_this_hour` – hourly estimate
- `sensor.average_peak_hour_energy` – three-hour average

The EnergyTariff values are read directly; Smart Load Manager does not create extra copies for the graph.

## Two chargers

Open **Settings → Devices & services → Smart Load Manager → Configure → Add charger** and select the other Easee device. Its name comes from Easee. Meter sources, safety margin and the household consumption limit are shared. Each charger gets its own controls and sensors. Enable automatic control on each participating charger.

- **Charge both:** share available power equally. When only one fits, the selected **First priority** charger receives capacity. If its minimum cannot fit, charging waits.
- **One at a time:** priority charger goes first; the other can charge when the vehicle finishes, disconnects, is manually paused or is outside its schedule.
- **Phase advice:** suggests single phase when it could allow both to charge. You change each charger's phase selection yourself, subject to vehicle compatibility.

Completed means the vehicle stopped requesting power; battery percentage is unknown. Manual pause remains respected. Manual charging with automatic control off counts as other household demand, outside the distribution policy.

Replace the old card with **examples/lovelace/two_chargers_card.yaml**. To get YAML with actual registered IDs, open **Developer tools → Actions**, run `smart_load_manager.get_dashboard`, copy its returned `yaml` value and paste it as one Manual card inside an existing section. Alternatively replace `CHARGER_SUFFIX` in the static example with the `card_suffix` attribute on the new charger's Charging status sensor. The shared Markdown explains the mode, priority and current reason per charger. No complete-view template is provided.

## Safe test

1. Make a Home Assistant backup and note how to re-enable your existing automation.
2. Disable that automation; do not delete or edit it.
3. Install the integration and restart Home Assistant. Leave automatic load control off.
4. Check the meter, energy used, phase/voltage, recommended current, and Easee limits.
5. When present and watching the charger, enable automatic control and confirm its recommendation matches the limit sent to Easee.
6. If anything looks wrong, turn automatic control off and restore your previous automation. Never run both controllers at once.

Automated tests check calculations and service calls. They cannot verify your electrical installation; confirm behavior in Home Assistant and with the Easee charger.

For two-charger testing, check both modes, priority changes, pause, disconnect, and handover when the vehicle finishes. Automated validation does not replace physical two-charger testing.

## Charger cannot be added

If setup reports missing voltage data, open **Settings → Devices & services → Easee → the selected charger → Entities**. Include disabled entities, open **Voltage**, enable it, and wait for updated readings before retrying. An active charger can still have disabled diagnostic sensors. SLM requires measured voltage data; the Easee master/slave role does not determine which charger you can add first.

## Waiting for power reports

Easee reports power on changes. The beta.4 draft accepts an available numeric
power value regardless of timestamp age, correcting beta.3's 120-second cutoff.
Missing or unavailable inputs still pause automatic allocation and identify
the source while successfully read measurements stay visible. HAN freshness
and subsequent measured acknowledgement of reductions remain required.
These changes are not yet published.

## Household status on SLM – Boligen

**Load control status** (`sensor.slm_status`) is the single plain-language
information source for both Markdown cards. It summarizes the household limit,
distribution and priority, every configured charger's explanation, and shared
phase advice. Technical detail lives in attributes. `controlled_loads` includes
one row for every charger, even if its information is missing. Forbruksgrense
and **Measurement status** (sources, HAN age and validity) share the household
device, independently of charging priority.

New setups create five main sensors per charger: Charging status, Charging
power, Charging current, Recommended current and Active phases. Current limits
are attributes of Recommended current; electrical details are attributes of
Charging status. Separate new Charging explanation and Phase advice entities
are replaced by household status. Existing entities remain as compatibility
diagnostics; nothing existing is automatically disabled or deleted.

Generate cards with `smart_load_manager.get_dashboard`. Static templates need
`sensor.SLM_HAN_POWER_SOURCE` replaced with HAN, and `CHARGER_SUFFIX` from the
second charger's **Charging status** `card_suffix` attribute. The graph still
reads EnergyTariff directly. A calculated recommendation is not a measurement;
charging completion does not prove the battery is full.

Prepared locally for beta.4, not yet published. The new initial wizard, master
toggles and naming migration remain separate pending work.

## Editing household sources after setup

The beta.4 draft provides **Configure → Household sources and safety margin**
for changing HAN, EnergyTariff used-this-hour and safety margin, even with two
chargers. It can be opened from either entry. Sources are validated before
saving and updated for both entries, retaining budget, priority and individual
schedules. New readings are used on the next normal update without a restart.
Add charger is a separate menu choice, only while fewer than two are configured.
This change is prepared locally and not yet published.
