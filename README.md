# Smart Load Manager — beta.8

Home Assistant custom integration for monitoring and opt-in control of electrical loads. Easee charging is the first supported load type; hot-water tanks and floor heating are future expansion targets.

## Beta status

Beta.8 removes manual maximum-current setup and uses the live upper current limit reported by Easee. Beta.7 makes clock scheduling self-contained: the integration provides its own schedule switch and start-time control, so users do not create HA helpers. Easee and EnergyTariff remain optional startup-order dependencies; selected entities are validated by the flow. Automatic control is **off by default** and resets to off after a Home Assistant restart. Easee current limits use `time_to_live: 0` (indefinite) and are replaced as conditions change. A stale or invalid HAN reading, unavailable EnergyTariff input, missing electrical data/limit, or closed schedule sends 0 A while automatic control is active.

This package has automated unit tests, static validation, and a Lovelace example, but has not been started inside a real Home Assistant instance or tested against physical chargers. Treat it as a beta. Do not enable automatic control until the sensors and calculated values have been checked against the installation.

## Setup

Requires the Easee Home Assistant integration and EnergyTariff to be installed and working first. In the Smart Load Manager setup flow, select the Easee device, the same instantaneous HAN power sensor used by EnergyTariff (unit W or kW), EnergyTariff's used/estimate sensors, the hourly energy limit, and a safety margin. Maximum current is read from the selected Easee device's circuit/charger limit attributes; no manual maximum is entered. If Easee does not report a valid limit, charging control remains at 0 A. Do not select a kWh energy counter as the HAN power sensor. Enable the Easee diagnostic Current and Voltage entities in the Easee device options if they are disabled.

The selected hourly limit should match EnergyTariff's target-energy setting. The power source should be the same HAN meter used by EnergyTariff, so the meter and tariff estimate agree.

Clock scheduling is optional and is provided by the integration. It creates a `Tidsstyring` switch and a `Starttid lading` time control (default 23:00). When enabled, charging is allowed during the 12-hour daily window beginning at that time, including across midnight. When disabled, charging follows the energy budget without a clock window. The schedule setting and start time are stored by the integration; automatic current control remains off after Home Assistant restarts.

## Easee interpretation

The integration resolves sibling Easee entities by device association, not by hard-coded entity names. It reads `config_phaseMode`, `state_outputPhase`, `config_detectedPowerGridType`, `state_reasonForNoCurrent`, terminal currents, terminal voltages, and relevant current-limit attributes when present. It keeps the raw enum field separate from its meaning because identical integer codes in different enums have different meanings.

The configured phase mode (1/2/3 = one phase/automatic/three phases) is shown separately from the actual output phase. During charging, phase conductors carrying current determine the active phase count. At 230 V with three active phase currents, the agreed minimum is 11 A; otherwise it is 6 A. If phase or voltage data is missing/contradictory, automatic control sends 0 A until the measurements are reliable. Voltage is measured continuously; normal variation of a few volts does not trigger a new configuration or learning cycle.

## Controls and behaviour

- **Automatisk laststyring**: opt-in switch, initially off; when on, the integration computes a recommended current every 30 seconds and sends a new Easee dynamic current limit when it changes, with a five-minute refresh. It does not change Easee's persistent maximum current, wiring configuration, or phase mode.
- **Manuell ladestrømgrense**: slider routed to `easee.set_charger_dynamic_limit`; `0 A` pauses charging. Positive settings below the currently detected minimum are rejected.
- The selected HAN sensor must be positive and its value must have changed within 60 seconds. If it stops changing, becomes unavailable, or is zero while automatic control is active, the controller sends and holds 0 A until valid data returns. Its age and validity are shown in diagnostic sensors.
- Easee documents `time_to_live: 0` as indefinite. This matches the existing automation. Turning automatic control off stops further updates but leaves the last Easee limit in place; set a manual limit or resume automatic control to replace it.
- Disable the old Easee dynamic-current automation before enabling Smart Load Manager automatic control. Both write the same dynamic limit and could otherwise overwrite one another.
- The controller estimates the rest-of-hour house energy from instantaneous HAN power minus charger power, subtracts EnergyTariff's used energy and the configured safety margin, and converts remaining kWh to amps using measured voltage and detected active phases. It caps the result at the lowest positive circuit/charger current limit exposed by Easee. If no valid limit is exposed, control remains at 0 A and manual positive commands are rejected.
- The EnergyTariff estimate is displayed as a cross-check; this first controller calculation uses measured house load rather than blindly treating an estimate that may include EV energy as house-only usage.

## Included files

- [Norwegian manual](docs/manual_nb.md)
- [English manual](docs/manual_en.md)
- [Lovelace dashboard YAML](examples/lovelace/charging_view.yaml)
- [Project status and next steps](docs/PROJECT_STATUS.md)
- [Recorded product and technical decisions](docs/DECISIONS.md)
- Regression tests under `tests/`

Codex project instructions are in [`AGENTS.md`](AGENTS.md). Read it together
with the project status and decisions before continuing development.

The dashboard YAML is built with standard Home Assistant cards. After setup, use the entity picker to replace the clearly marked entity IDs with the IDs created for the selected charger and the EnergyTariff entities chosen during setup. It does not require Mushroom or navbar-card.

## Test

From the `smart_load_manager` project directory:

```sh
python -m unittest discover -s tests -v
```

These tests validate pure calculations and Easee enum mappings only. They do not replace a Home Assistant startup test, service-call test, or supervised live-load test.
