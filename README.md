# Smart Load Manager OJM — beta.13

Home Assistant custom integration for monitoring and opt-in control of electrical loads. Easee charging is the first supported load type; hot-water tanks and floor heating are future expansion targets.

## Beta status

Beta.13 fixes the sensor setup failure caused by the missing measured-current field in the coordinator payload. A regression test now covers this case. The beta.12 feature set gives all diagnostic sensors concise, localized names and stable `sensor.slm_*` entity IDs. Existing entity IDs are migrated on upgrade without changing their unique IDs; the installation-wide Forbruksgrense entity keeps its agreed ID. It also exposes measured charging current and makes the manual current slider unavailable while automatic control is on. A status sensor explains when it is locked. The Lovelace example restores the descriptive Markdown charging summary and graphs alongside the controls.

The beta.11 behavior remains: **Fasevalg** offers Automatic, Single phase, and Three phases through Easee's supported `set_charger_phase_mode` service. The minimum current is fixed at 11 A for measured 230 V three-phase charging with all three phase currents, otherwise 6 A; there is no vehicle learning. **Forbruksgrense** is the installation's hourly target (4.5–20 kWh in 0.5 kWh steps), not a per-load budget. This beta intentionally allows one configured load entry per HA installation so there is only one selector; multi-load support requires the future shared allocator. Manual current is available only when automatic control is off; 0 A pauses charging. Automatic control remains off by default and after Home Assistant restarts. Invalid/stale HAN or tariff-used input, missing electrical data/limit, or a closed schedule sends 0 A while automatic control is active. `time_to_live: 0` leaves the last Easee dynamic limit in place until replaced.

This package has automated unit tests, static validation, and a Lovelace example, but has not been started inside a real Home Assistant instance or tested against physical chargers. Treat it as a beta. Do not enable automatic control until the sensors and calculated values have been checked against the installation.

## Setup

Requires the Easee Home Assistant integration and EnergyTariff to be installed and working first. Select the Easee device, the instantaneous HAN power sensor used by EnergyTariff (W or kW), EnergyTariff's used-this-hour sensor, and a safety margin. After setup, set **Forbruksgrense** (4.5–20 kWh in 0.5 kWh steps). It is the installation-wide hourly target and replaces the old `input_select.forbruksgrense`; EnergyTariff's `target_energy` is not a competing target. The estimate is a diagnostic sensor, not a setup input. Easee maximum current is read-only. Do not select a kWh counter as HAN power. Enable Easee diagnostic Current and Voltage entities if disabled.

Forbruksgrense is the Smart Load Manager control target. EnergyTariff supplies measured energy used so far this hour; its `target_energy` is configured separately and does not override Forbruksgrense. Use the same HAN power meter in both integrations so the measurements agree.

Clock scheduling is optional and is provided by the integration. It creates a `Tidsstyring` switch and a `Starttid lading` time control (default 23:00). When enabled, charging is allowed during the 12-hour daily window beginning at that time, including across midnight. The setting and time persist; automatic current control remains off after restart.

## Easee interpretation

The integration resolves sibling Easee entities by device association, not by hard-coded entity names. It reads `config_phaseMode`, `state_outputPhase`, `config_detectedPowerGridType`, `state_reasonForNoCurrent`, terminal currents, terminal voltages, and relevant current-limit attributes when present. It keeps the raw enum field separate from its meaning because identical integer codes in different enums have different meanings.

The configured phase mode (1/2/3 = one phase/automatic/three phases) is shown separately from the actual output phase. During charging, phase conductors carrying current determine the active phase count. At 230 V with three active phase currents, the agreed minimum is 11 A; otherwise it is 6 A. If phase or voltage data is missing/contradictory, automatic control sends 0 A until the measurements are reliable. Voltage is measured continuously; normal variation of a few volts does not trigger a new configuration or learning cycle.

## Controls and behaviour

- **Automatisk laststyring**: opt-in switch, initially off; when on, the integration computes a recommended current every 30 seconds and sends a new Easee dynamic current limit when it changes, with a five-minute refresh. It does not change Easee's persistent maximum current, wiring configuration, or phase mode.
- **Fasevalg**: Automatic, Single phase, or Three phases. This sets Easee's configured mode; it is not the same as the live active-phase measurement. Verify the reported mode and measured phases after changing. Make phase changes while present and follow the charger.
- **Manuell ladestrøm**: slider routed to `easee.set_charger_dynamic_limit`; use only while Automatic load control is off. `0 A` pauses charging. Positive settings below the detected minimum or above Easee's live maximum are rejected.
- The selected HAN sensor must be positive and its value must have changed within 60 seconds. If it stops changing, becomes unavailable, or is zero while automatic control is active, the controller sends and holds 0 A until valid data returns. Its age and validity are shown in diagnostic sensors.
- Easee documents `time_to_live: 0` as indefinite. This matches the existing automation. Turning automatic control off stops further updates but leaves the last Easee limit in place; set a manual limit or resume automatic control to replace it.
- Disable the old Easee dynamic-current automation before enabling Smart Load Manager automatic control. Both write the same dynamic limit and could otherwise overwrite one another.
- The controller estimates the rest-of-hour house energy from instantaneous HAN power minus charger power, subtracts EnergyTariff's used energy and the configured safety margin, and converts remaining kWh to amps using measured voltage and detected active phases. It caps the result at the lowest positive circuit/charger current limit exposed by Easee. If no valid limit is exposed, control remains at 0 A and manual positive commands are rejected.
- The EnergyTariff estimate is displayed as a diagnostic sensor; this first controller calculation uses measured house load rather than blindly treating an estimate that may include EV energy as house-only usage.

## Included files

- [Norwegian manual](docs/manual_nb.md)
- [English manual](docs/manual_en.md)
- [Complete dashboard view YAML](examples/lovelace/charging_view.yaml)
- [Single card YAML for the card editor](examples/lovelace/charging_card.yaml)
- [Project status and next steps](docs/PROJECT_STATUS.md)
- [Recorded product and technical decisions](docs/DECISIONS.md)
- Regression tests under `tests/`

Codex project instructions are in [`AGENTS.md`](AGENTS.md). Read it together
with the project status and decisions before continuing development.

The complete dashboard view uses `type: sections` and belongs in a dashboard view's raw configuration editor. Do not paste it into the single-card YAML editor. For that editor, use `examples/lovelace/charging_card.yaml`, which is one valid `vertical-stack` card. Both use standard Home Assistant cards and include a status summary, controls, measurements, and history graphs. Sensor entity IDs use the stable `sensor.slm_*` pattern; the Forbruksgrense ID remains `select.smart_load_manager_ojm_easee_forbruksgrense`. It does not require Mushroom or navbar-card.

## Test

From the `smart_load_manager` project directory:

```sh
python -m unittest discover -s tests -v
```

These tests cover electrical calculations, control decisions, and the exact Easee service payload for positive and zero-current commands. GitHub Actions also checks module imports and metadata. They do not replace a test in a running Home Assistant instance or supervised live-charger test.
