# Smart Load Manager OJM — user guide

SLM adjusts one or two Easee chargers to the home's hourly energy budget. Charging decreases when household demand rises and can resume when capacity becomes available. No user-created helpers or YAML automations are required.

[Setup](#step-by-step-setup) · [Controls](#controls) · [Dashboard](#dashboard) · [Troubleshooting](#when-charging-waits)

## Before you start

- Install and configure the [latest Easee integration](https://github.com/nordicopen/easee_hass/releases/latest). Easee v2026.11.0 requires **Home Assistant 2026.10.0 or newer**.
- Whole-home **HAN power**, in W or kW.
- **Energy used this hour**, in kWh, resetting at every clock-hour boundary. [EnergyTariff](https://github.com/epaulsen/energytariff) is recommended; equivalent Tibber or other measurements can be used. Spot price, daily consumption and lifetime totals cannot replace hourly energy.
- Enable **Current (A)** and **Voltage (V)** on **each** Easee charger: Settings → Devices & services → Easee → charger → Entities. Show disabled entities, enable both and wait for measured values. Charging power must also be available.
- Optional: **estimated total consumption for the current clock hour**, in kWh, such as EnergyTariff `energy_estimate_this_hour` or Tibber **Estimated consumption current hour**. This is informational; missing estimates do not stop charging.

## Installation

Download the desired [release](https://github.com/ojm88/smart-load-manager/releases), copy `custom_components/smart_load_manager` into `config/custom_components/` and restart HA. To update, replace the integration folder and restart. Back up before updating.

Use Marketplace on **Home Assistant 2026.11 or newer**.

[![Open Smart Load Manager OJM in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=ojm88&repository=smart-load-manager&category=integration)

Use the button above as a shortcut, or add the repository from the Marketplace menu:

1. Open **Settings → Marketplace → ⋮ → Custom repositories**.
2. Connect GitHub if prompted.
3. Paste `https://github.com/ojm88/smart-load-manager`, select **Integration**, and click **Add**.
4. Find **Smart Load Manager OJM** in Marketplace and select **Install**.

After a first install, go straight to **Settings → Devices & services → Add integration** and select **Smart Load Manager OJM**. Home Assistant asks for a restart when updating an integration it has already loaded.

[Home Assistant Marketplace repository guide](https://contributors.home-assistant.io/marketplace/guides/catalog/#the-link-to-your-repository)

## Step-by-step setup

1. Open **Settings → Devices & services → Add integration → Smart Load Manager OJM**.
2. Choose **Household power (HAN)** and **Energy used this hour**. Select an hourly estimate if available; otherwise `sensor.energy_estimate_this_hour` is used when present.
3. Choose the **Safety margin**. The default 0.3 kWh is reserved from the hourly budget for measurement delays and consumption changes. A higher margin leaves less room for charging.
4. Choose **EV charging – Easee**, the first charger and its actual physical connection from the table below.
5. Finish with one charger or add a second. Only unused chargers are offered for the second selection. Cancelling before completion creates no partial installation.
6. Set the **Consumption limit** on **SLM – Boligen**. Check measurement readiness and values before enabling control.
7. Disable previous automations that adjust the same charging limits. Enable **Automatic load control** on each charger SLM should regulate. New chargers start with automation off.
8. Generate the dashboard card as described below.

### Choose the physical connection

| Choice | Actual charger wiring |
| --- | --- |
| 230 V IT/TT – single phase | 230 V IT/TT, one charging phase |
| 230 V IT/TT – three phase | 230 V IT/TT, three wired phases |
| 400/230 V TN – single phase | TN, one phase and neutral |
| 400/230 V TN – three phase | TN, three phases and neutral |

This describes the installation; it does not change wiring or fix the calculation voltage to a nominal value. SLM uses relevant measured Easee voltages. Choose the known wiring, not the number of phases the vehicle currently uses. Phase selection appears only for physically three-phase connections. Resolve uncertain wiring before enabling automatic control.

### Choose a realistic consumption limit

The **Consumption limit** applies to the entire home, including charging, per clock hour. Choices are 4.5–20 kWh in 0.5 kWh steps. For example, 10 kWh in one hour equals 10 kW average power; it is not an instantaneous power or fuse limit.

Choose based on normal household demand, grid-tariff steps and charging needs. A 10 kWh target with 0.3 kWh margin gives SLM a 9.7 kWh budget. If the home uses almost all of it, charging must wait. Two chargers share the remaining capacity. SLM can help reduce peaks but does not guarantee savings.

## Controls

**SLM – Boligen** holds the shared budget, status, measurement readiness, charging overview and total charging power. With two chargers, it also contains **Charging mode**. The **Charging** group holds each charger's independent controls and measurements; there is no combined automation toggle.

| Control | Behavior |
| --- | --- |
| Automatic load control | Regulates this charger against the household budget. Its on/off choice survives ordinary restart, reload and update. |
| Automation off / Manual charging current | Turning automation off requests the lowest valid manual charging current. You can then choose a manual limit within the permitted range. Pause, schedule and required measurement guards still apply. Turning automation off is not a stop command. |
| Charging pause | Sends 0 A. Removing pause reassesses automatic charging or restores the manual request when permitted. A new pause cannot be activated while completed/disconnected; an existing pause can still be removed. |
| Schedule and start time | Allows charging in a daily 12-hour window, e.g. 23:00–11:00. Also applies to manual charging. An open window does not guarantee capacity. Turn scheduling off to charge without a time window. |
| Phase selection | Choose single phase, automatic or three phases for three-phase wiring. The setting is sent to Easee. SLM does not switch phase mode automatically. |
| First priority | With two chargers, exactly one has first priority. The switches are complementary. This is SLM allocation priority, not an Easee hardware-master change. |

The dashboard hides manual charging current when unavailable, including automation on, active pause, a closed schedule or missing measurements. Use **Charging pause** to stop rather than choosing 0 A on the slider.

**Charge both** shares available power between eligible chargers within their limits. When only one fits, first priority wins. **One at a time** gives available capacity to the first eligible charger; completion, disconnection, pause or a closed schedule can give the other its turn.

SLM uses a minimum of 11 A for measured 230 V three-phase charging, otherwise 6 A. Maximum current comes from Easee and is not entered in SLM. The vehicle/charger may draw less than offered. Easee's installation and user limits still apply, and Easee handles its internal circuit sharing. SLM controls offers against the household budget and does not replace electrical protection.

## How charging is regulated

- **Measurements and recommended charging current** update on source changes. A check every 30 seconds also follows time and measurement validity.
- **Ordinary limit changes** occur every five minutes. An unchanged limit is normally not resent.
- **Connection, user controls, schedule boundaries and recovered measurements** are assessed immediately, subject to capacity and all permissions.
- **Risk of exhausting the hourly budget** can trigger an earlier reduction after 30 seconds; urgent risks reduce immediately. An early reduction holds ordinary increases for at least five minutes.
- **Two chargers:** Actual active-load reductions require new measured confirmation before capacity is transferred. A known idle charger with zero power and less than 1 A standby current needs no repeated zero heartbeat.
- **Completion:** `completed` with zero power and less than 1 A releases unused capacity without ordinary budget commands to the completed charger. A renewed charging request is assessed immediately. Status does not establish battery percentage.

### Offered current versus actual consumption

New offers reserve their complete power in the forecast. After three minutes of stable positive draw, forecasts and settled manual reservations may use measured power +100 W, avoiding indefinite reservation of unused offers when the vehicle or app limits draw.

A settled observation survives temporary pauses in the same session. Waiting still reserves the full offer; matching positive draw on resume can reuse the observation without another three-minute wait. Completion, disconnection and invalid measurements clear it. Changed phase context, automatic/manual mode, demand or offers above the observed offer require fresh assessment. Observations do not survive restart.

This is a consumption forecast, not a learned electrical maximum. Hidden app limits need not be copied to SLM. Measurement delays and fast demand changes can still cause brief excursions.

## Measurements

| Measurement | Meaning |
| --- | --- |
| Charging status | Easee's reported charging, waiting, completed or disconnected status. |
| Power to car | Measured charging power in W. |
| Measured charging current | Current Easee measures to the vehicle, in A. |
| Recommended charging current | SLM's current recommendation. It can differ from the last sent limit until adjustment and is not measured draw. Minimum and reported maximum are attributes. |
| Phases in use / Voltage | Actual phase use and relevant terminal voltages. TN remains 400/230 V even if the vehicle charges on one phase. |
| Load control status | Shared explanation with a short reason for each charger. |
| Measurement status | Required-source validity, with source IDs and HAN age in attributes. |
| Charging / Total charging power | Read-only overview and sum of measured charging power, including manual chargers. Missing readings yield an unknown total, not zero. |

## Dashboard

1. Open **Settings → Tools → Actions**.
2. Run:

   ```yaml
   action: smart_load_manager.get_dashboard
   data: {}
   ```

3. Copy the returned **`yaml`** value.
4. Edit the dashboard, add a **Manual card** inside an existing section and paste it.

The generator uses registered entity IDs and charger names, including custom names. Both chargers are named in the **Anbefalt ladestrøm** (recommended charging current) and **Målt ladestrøm** (measured charging current) graph legends. The generated status card is always Norwegian, including on English HA servers; other entities follow HA's language. Static [one-charger](../examples/lovelace/charging_card.yaml) and [two-charger](../examples/lovelace/two_chargers_card.yaml) examples require adaptation.

The card shows household measurements/budget followed by each charger's status, Auto/Manual and relevant explanation. It distinguishes **insufficient capacity**, **a positive recommendation awaiting adjustment**, and **a positive sent limit with Easee still waiting**. Budget waits show minimum required power and suggest reducing other consumption. The next ordinary assessment is not a promised charging start. With no cars connected, the display is shorter.

Graphs show charging current and the selected energy/estimate sources for the last 12 hours. **Snitt 3-timer** uses `sensor.average_peak_hour_energy` when available; otherwise remove that row from the card YAML. The displayed estimate can differ from SLM's recommendation because it comes from a separate informational source.

**Regenerate the card** after changing charger membership, charger names, physical wiring, measurement sources, referenced entity IDs or card layout. Copied YAML does not update itself. Ordinary controls for budget, priority, current, phase mode, pause and scheduling need no new YAML. Preserve custom card edits before replacing it. Generate a new card when updating to beta 22.

## Changing setup later

Open **Settings → Devices & services → Smart Load Manager OJM → Configure**.

- **Household sources and safety margin:** Change HAN, measured hourly energy, optional estimate and margin. Sources are validated before saving; charger settings are retained.
- **Chargers and connections → Add charger:** Choose one unused Easee device. Existing charger/settings remain; at most two chargers are supported.
- **Remove charger:** Available with two chargers. A 0 A command is sent before removal; command failure aborts the change. Settings are retained for later re-addition.
- **Charger connections:** Correct the physical connection if needed. The selected charger receives 0 A and its automation is disabled before reload. Check the choice before enabling control again.

Successful 0 A service calls are not measured proof of a physical stop. Ordinary restart/update retains automation, manual settings, pause, schedules and household choices. Easee stores phase selection.

## When charging waits

| Card explanation | What to do |
| --- | --- |
| Waiting for capacity | Check the minimum required charging power. Reduce other household demand or wait for capacity. Use a realistic hourly budget. |
| Waiting for adjustment | A recommendation has changed while the prior limit remains. Check the next ordinary assessment time. |
| Positive limit sent, Easee still waiting | SLM has offered current. If persistent, check vehicle schedules/charge limits and any Easee restrictions. |
| Waiting for measurements | Open Measurement status. Check HAN, measured hourly energy, Easee current/voltage/power and reported maximum. |
| Waiting for reduction | New current/power readings are needed before capacity moves. Download diagnostics if persistent. |
| Waiting for schedule / Paused | Check the charger's time window or turn off Charging pause. |
| Manual control | Automation is off for this charger. Enable it for automatic regulation. |

Valid HAN reports are accepted up to 120 seconds old inclusive, including identical values reported again. Missing/invalid reports trigger a stop command for affected managed chargers. Valid measurements prompt immediate reassessment. An available unchanged Easee power reading does not expire solely because its timestamp is old.

### Download diagnostics

Open the integration entry → **⋮ → Download diagnostics** while the issue is present, before restarting/reloading. Include the observed time, version, expected and actual behavior in the [issue](https://github.com/ojm88/smart-load-manager/issues).

The file contains anonymous measurements, decisions, power reservations and command results. The last 4096 events are held in memory and reset on restart/reload; no fixed time span is guaranteed. Successful service calls do not prove physical charging.

## Limitations

SLM is under development. See [validation status](PROJECT_STATUS.md) for software tests and physical acceptance. There is no spot-price optimization or vehicle battery-percentage control. SLM does not replace protection or Easee's internal limits. Hot water and floor heating are planned, not implemented.
