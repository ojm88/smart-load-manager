# User manual — Smart Load Manager beta.6

## What this beta does

Beta.6 fixes a configuration-flow import error that prevented beta.5 from loading in Home Assistant. It reads Easee, HAN meter, and EnergyTariff values, decodes phase/voltage information, calculates a recommended charging current, and can send a dynamic current limit to Easee. It checks HAN measurement freshness and supports optional clock scheduling. Automatic control is off on first setup and after Home Assistant restarts. This release does not control water heaters or floor heating.

This is still a beta. It has not been validated in a live Home Assistant installation or with a physical charger. Verify the sensors and recommendation before enabling automatic control.

## Before installation

1. Install and configure the Easee integration.
2. Install and configure EnergyTariff. Confirm that `energy_used_this_hour` and `energy_estimate_this_hour` are available numeric sensors.
3. Select the same instantaneous HAN power sensor used by EnergyTariff. Its unit must be W or kW, not kWh.
4. Enable Easee's diagnostic Current and Voltage entities in the Easee device integration options.
5. Make the Smart Load Manager hourly energy limit match EnergyTariff's `target_energy` value.

## Installation

Copy `custom_components/smart_load_manager` into Home Assistant's `custom_components` folder, or install through HACS if you have published this project as a HACS-compatible GitHub repository. Restart Home Assistant. Go to **Settings → Devices & services → Add integration** and select **Smart Load Manager**.

Select the Easee charger, HAN power sensor, EnergyTariff used and estimate sensors, hourly energy limit, maximum current cap, and safety margin. Choose a conservative current cap; the integration also considers positive circuit/charger current limits exposed by Easee.

Clock scheduling is optional. To match the previous automation, select the existing Easee Smartlading switch and the `input_datetime` helper used for the start time. Entity IDs can differ; select them from the setup lists.

If an earlier beta is already installed, open the integration's **Configure** option and choose the schedule switch and time helper there. You do not need to remove and add the integration again.

To create a start-time helper, open **Settings → Devices & services → Helpers → Create helper → Date and/or time**. Select time only (no date), name it, for example, **Smartlading starter kl**, then select its `input_datetime` entity during Smart Load Manager setup.

Alternatively, add it in a YAML package:

```yaml
input_datetime:
  smartlading_starter_kl:
    name: Smartlading starter kl
    has_date: false
    has_time: true
```

This is a time helper, not a measurement sensor. Select the created `input_datetime.smartlading_starter_kl` in setup.

## Easee interpretation

The integration finds Easee sibling entities through device association; you do not enter `sensor.easee_*` IDs. It reads attributes by field name and decodes each Easee enum only within its own field.

- `config_phaseMode`: 1 = locked to one phase, 2 = automatic, 3 = locked to three phases.
- `state_outputPhase`: Easee output configuration. Codes 10–15 are one phase, 20–22 are two phases, and 30 is three-phase TN. Decoded output is shown separately from configured phase mode.
- `config_detectedPowerGridType`: where available, Easee's grid type code (including TN one/two/three phase and IT one/three phase).
- Terminal currents and terminal voltages are used to estimate actual active phase use and voltage class. The aggregate “Voltage” state is not treated as line voltage by itself.
- `state_reasonForNoCurrent` is decoded separately. The same number in a different enum field can mean something else.

Agreed minimum current: 230 V with three active phase currents → 11 A; otherwise → 6 A. Classification follows measured voltage class and active phase use rather than a manual IT/TT selector. Missing, unknown, or contradictory measurements make automatic control send 0 A.

## Controls

### Automatic load control

Enable `Automatisk laststyring` only after checking the diagnostics. It is off by default and resets to off after a Home Assistant restart. When enabled, the recommended limit is recalculated every 30 seconds. Easee receives a new command when the recommendation changes and a refresh at least every five minutes. Commands use `time_to_live: 0`, which the Easee integration defines as indefinite until replaced by another dynamic limit.

The calculation subtracts measured charging power from HAN power to estimate house load, estimates remaining house energy this hour, subtracts EnergyTariff energy already used and the safety margin, then converts remaining energy to amps using the current measured voltage and active phase configuration. If the available current is below the allowed minimum, the integration recommends 0 A instead of sending a below-minimum value.

### Manual current limit

`Manuell ladestrømgrense` sends a limit using the Easee integration's `easee.set_charger_dynamic_limit` service. 0 A means pause. A positive value below the detected minimum is rejected. Turn automatic control off before making manual changes. Easee keeps this dynamic limit until another one replaces it; the installer's persistent maximum is unchanged.

### Clock scheduling

To use the schedule, both `Automatisk laststyring` and the selected Easee Smartlading switch must be on. The first enables current control; the Easee switch enables or disables the clock window. When the Easee switch is **off**, charging follows the hourly energy budget without a clock window. When it is **on**, charging is allowed from the selected `input_datetime` start time for the next 12 hours. After the window ends, active automatic control sends 0 A. The window wraps across midnight and repeats daily. Diagnostic sensors show whether the window is active and why.

The HAN sensor must show positive power, and its state must have changed within the last 60 seconds. If the value stops changing, becomes unavailable, or is zero, active automatic control sends 0 A. This matches the `last_changed` guard in the previous automation. Current calculation resumes when a fresh, valid measurement returns.

## Dashboard

Import or copy `examples/lovelace/charging_view.yaml` into a new Lovelace view. It uses built-in Home Assistant cards. Replace marked example entity IDs with the entities created for your charger and the EnergyTariff sensors selected during setup. Check them before adding the card to a production dashboard.

## First test

1. Leave automatic control off. Check that status, configured phase mode, actual output phase, active phases, voltage, current limit, and recommendation match the Easee app and measurements.
2. Verify the HAN unit is W or kW, that it measures total consumption, and that EnergyTariff values correspond to the current hour.
3. You may test manual 0 A while observing that charging pauses. Resume with a value at or above the detected minimum and below the current cap.
4. Check that the HAN age is below 60 seconds and the validity sensor says Yes. If using clock scheduling, first test with the schedule switch off, then verify the start time and time window before enabling it.
5. Only then enable automatic control while monitoring its recommendation, HAN power, Easee current, and EnergyTariff values.
6. Disable automatic control if data becomes unavailable or disagrees with measurements. When disabled, no new dynamic limits are sent; Easee keeps the last dynamic limit until another limit replaces it. Set a desired manual value or enable automatic control again.

Disable the old **Dynamisk styring av Easee-lader Opptimalisert V3.0** automation before enabling Smart Load Manager automatic control. Both use the same Easee service and could otherwise send conflicting current limits.

## Troubleshooting and limitations

- If Home Assistant reports “Config flow could not be loaded” or “Invalid handler specified,” make sure beta.6 or newer has downloaded and restart Home Assistant. If it continues, retrieve the `custom_components.smart_load_manager.config_flow` log entry from **Settings → System → Logs**.
- Setup fails if selected input entities are unavailable/non-numeric or the HAN power unit is not W/kW.
- If Easee Current/Voltage diagnostic sensors are disabled, enable them and reload the integration.
- Unknown phase or voltage means the integration does not have enough reliable data; automatic control sends 0 A.
- Model compatibility is inferred from available Easee entities and attributes; it is not a certification of every charger SKU.
- EnergyTariff estimate is shown as a cross-check. The first controller calculation uses measured HAN power minus Easee power to estimate house load, because the tariff estimate may include EV energy.
- Tests cover calculation functions, not Home Assistant startup, real Easee responses, or physical charging. Do not use this beta as the only electrical protection or fuse safeguard.
