# Smart Load Manager OJM – user guide

SLM adjusts charging to a shared hourly household energy target. It can help avoid a higher grid-capacity tariff step; savings are not guaranteed. It does not optimize spot prices.

## Requirements and installation

Use Home Assistant 2026.2 or newer, configured Easee devices, and EnergyTariff with a HAN power sensor in W or kW. **Enable the Voltage sensor on every Easee charger** under Settings → Devices & services → Easee → charger → Entities. Include disabled entities and wait for measured values.

Download a GitHub release, copy `custom_components/smart_load_manager` into `config/custom_components/`, then restart Home Assistant. From HA 2026.11 you can also add `https://github.com/ojm88/smart-load-manager` as a custom Integration in **Settings → Marketplace**; custom repositories require a GitHub connection. This menu is not available on HA 2026.10.

## Setup

1. Add **Smart Load Manager OJM** under Devices & services.
2. Select household HAN power, EnergyTariff **used this hour**, and a safety margin.
3. Choose EV charging and one or two distinct Easee chargers.
4. Set **Consumption limit / Forbruksgrense** on the household device (4.5–20 kWh per hour, 0.5 steps).
5. Disable older automation controlling these chargers, then deliberately enable SLM automatic control for each charger.

No custom helpers or YAML automation are required. Hot water and floor heating are explanatory planned features, not working controls.

## Household and charging groups

**Household** contains the shared budget, status, measurement diagnostics, and charging mode when two chargers exist. **Charging** contains each charger with its own controls and measurements.

| Control | Behavior |
| --- | --- |
| Automatic load control | Adjusts the dynamic current limit. Starts off after restart. |
| Charging pause | Sends 0 A. Resume recalculates automatically or restores the previous manual limit when current measurements and limits permit. |
| Manual current | Available when automatic control and pause are off; capped by Easee's reported maximum. |
| Phase selection | Changes Easee's phase setting. SLM never automatically changes topology. |
| Schedule and start time | Independent daily 12-hour windows. An open window grants eligibility, not guaranteed charging. |
| First priority | Two complementary switches backed by one saved priority. Turning the active switch off promotes the other charger. These are SLM software roles, not Easee hardware roles. |

**Charge both** shares available power equally within each charger's bounds; when both minimums cannot fit, the eligible priority charger goes first. **One at a time** gives the eligible priority charger its turn, allowing handover on disconnection, completion, manual pause or a closed schedule.

Minimum current is 11 A for measured 230 V three-phase charging, otherwise 6 A. Maximum current comes from Easee and cannot be manually configured in SLM. SLM does not identify the vehicle. Easee Completed does not prove a full battery.

## Measurements and dashboard

Each charger has six main measurements: status, charging power, measured current, recommended current, active phases and voltage. Names use function followed by the charger name, consistently from the first charger. Voltage is measured or inferred line-to-line voltage; phase-neutral voltage and electrical details remain status attributes. Recommended current includes minimum and maximum attributes. A diagnostic priority sensor appears with two chargers.

The household status explains why each load runs or waits and provides phase advice. Measurement status contains shared source IDs, HAN age and the old/new entity-ID migration mapping.

Run **Developer tools → Actions → `smart_load_manager.get_dashboard`**, then paste the returned `yaml` into a **Manual card inside an existing section**. The generator resolves actual registered IDs, including your own renames. The graph reads EnergyTariff directly. Static [one](../examples/lovelace/charging_card.yaml) and [two](../examples/lovelace/two_chargers_card.yaml) charger examples are templates; generating the card is recommended.

## Configuration and upgrade

**Configure → Household sources and safety margin** validates all inputs before saving and retains load settings. Updated sources are read at the next regular refresh.

**Configure → Add or remove charger** changes the one/two-charger selection and reloads SLM. Enable automatic control again afterwards. Before removal, SLM sends a 0 A command to the removed charger; a failed command aborts the change. Command success does not confirm a physical stop. Saved settings are retained if the device is added again.

Back up before beta 5. Existing charger entries consolidate into one installation with household and charging groups. Unique sensor identities and settings are retained. Generated entity IDs gain a saved charger-name suffix; custom IDs and display names are respected. Name collisions use stable disambiguation and existing IDs are never taken over. **External YAML and automations are not rewritten.** Check the mapping on Measurement status and generate a new card. Returning to beta 4 requires restoring the backup.

## Waiting or troubleshooting

Read household status and Measurement status first. Check HAN freshness, EnergyTariff, enabled Easee Voltage sensors, reported current limits, pause and schedules. HAN must be valid and at most 60 seconds old. An available unchanged Easee power value remains valid despite an old timestamp. Capacity moves between chargers only after subsequent current/power readings confirm a reduction.

SLM does not replace installation protection. Turning automatic control off stops further automatic writes and leaves Easee's last dynamic limit in place. Use Charging pause to explicitly send 0 A.
