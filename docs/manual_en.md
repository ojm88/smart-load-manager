# User manual — Smart Load Manager OJM beta.10

## What beta 10 does

The integration creates a **Forbruksgrense** selector with the former helper’s 4.5–20 kWh choices in 0.5 kWh steps. This is the authoritative hourly target for the control calculation. EnergyTariff provides measured energy used so far this hour; its separate `target_energy` does not override Forbruksgrense.

Smart Load Manager OJM reads the Easee charger's status, current, voltage, phase information, and current limits. It uses the HAN power meter and EnergyTariff's energy used this hour to calculate a recommended dynamic current limit. The integration sends the limit to Easee when you enable **Automatic load control**.

Beta 10 adds Norwegian and English setup text, field explanations, an EnergyTariff estimate sensor, and a separate sensor for Easee's maximum current. The maximum current is read-only information from Easee; it is not entered or changed in this integration.

The agreed minimum-current rule is implemented directly, with no learning and no vehicle identification:

- 11 A when Easee measures current on all three phases while charging on a 230 V IT/TT supply.
- 6 A otherwise.

Phase use and voltage are detected from Easee measurements. The measured voltage is used in the calculation, so normal movement of a few volts updates the power calculation without starting any learning process.

This is beta software. It has not been physically tested on your charger until you complete the test below. The integration does not replace circuit protection, fuses, or Easee's built-in safety functions.

## Requirements

1. Install the Easee integration and add your charger to Home Assistant.
2. Install and configure EnergyTariff. Its **energy used this hour** sensor must be available in kWh.
3. Select the same HAN power sensor used by EnergyTariff. It must measure instantaneous power in W or kW, not energy in kWh.
4. Enable Easee diagnostic Current and Voltage entities if they are disabled.
5. Set Forbruksgrense in Smart Load Manager after setup. It is a select entity, not a measurement sensor, and replaces the old `input_select.forbruksgrense`.

## Setup

Install through HACS using the custom repository, or copy `custom_components/smart_load_manager` into Home Assistant's `custom_components` folder. Restart Home Assistant. Select **Settings → Devices & services → Add integration → Smart Load Manager OJM**.

Select the Easee device, HAN power sensor, EnergyTariff energy-used sensor, and safety margin. After setup, select the Smart Load Manager Forbruksgrense entity. It offers 4.5–20 kWh in 0.5 kWh steps and is used directly as the hourly target in the charging calculation. Setup does not ask for an hourly limit, estimate, or maximum charging current:

- The hourly estimate appears after setup as a Smart Load Manager sensor. It is for comparison only and is not required for control.
- Easee's maximum current appears as a read-only sensor and is used as the upper calculation limit.
- If Easee does not report a valid current limit, the recommendation is 0 A and positive manual current commands are blocked.
- If a source is missing or has the wrong unit, setup displays an explanation so you can correct the selection.

Forbruksgrense and the safety margin are stored by the integration. You do not create `input_number`, `input_datetime`, or other helpers.

## Sensors and control

The integration creates a Smart Load Manager device with sensors for charger status, configured phase mode, actual output phase, active phases, measured phase/line voltage, grid type, minimum current, recommended current, Easee maximum current, charging power, HAN power, EnergyTariff used/estimated energy, meter freshness, and the control explanation.

**Automatic load control** is off during setup and after a Home Assistant restart. When enabled, the integration recalculates every 30 seconds. It sends the recommended current when charging is allowed, and 0 A when the car is disconnected, the schedule window is closed, required source data is invalid/stale, or the electrical setup cannot be determined reliably. Easee receives a command when the recommendation changes and a refresh every five minutes. `time_to_live: 0` leaves the last command in place until it is replaced.

The calculation subtracts the charger's measured power from HAN power to estimate house load. It subtracts EnergyTariff energy used so far this hour, projected house energy for the remainder of the hour, and the safety margin from Forbruksgrense. Remaining energy is converted to amps using measured voltage and detected phase use, then capped at Easee's reported maximum current.

Turning **Automatic load control** off stops the integration from sending new commands; Easee keeps the last dynamic limit. This is why the old automation must be re-enabled during rollback. The manual current-limit entity sends a separate Easee command; 0 A pauses charging. Positive manual values cannot exceed Easee's reported limit or fall below the detected minimum current.

### Clock schedule

The integration provides its own **Charging schedule** switch and **Charging start time** entity (default 23:00). When enabled, charging is allowed during a daily 12-hour window from the selected start time. The window crosses midnight. When disabled, the hourly budget applies without a clock restriction. Schedule settings persist after restart; automatic load control still starts off.

## Safe test in a Home Assistant installation that already controls the charger

This test leaves your existing solution intact, except that the automation is temporarily disabled so it cannot compete with the integration.

1. Create a Home Assistant backup. Note how to re-enable **Dynamisk styring av Easee-lader Opptimalisert V3.0**.
2. Disable that automation before sending current limits with the new integration. Do not delete it or edit its YAML.
3. Install beta 10 and restart Home Assistant. Keep **Automatic load control** off.
4. Check the setup form: it must not ask for the EnergyTariff estimate or maximum current. After setup, confirm that the EnergyTariff estimate and Easee maximum current appear as sensors.
5. With automatic control still off, compare measured voltage, active phases, minimum current, Easee maximum current, HAN power, EnergyTariff used energy, and recommended current with the Easee app and your existing measurements. No dynamic limit is sent during this observation stage.
6. Once the sensor values match, enable automatic control while present and watching the charger. Keep the old automation disabled. Confirm that the recommendation and reported Easee limit track each other and that charging responds as expected.
7. Do not deliberately make the meter invalid or close the schedule window while charging needs to continue. Automated tests cover those cases; a real 0 A pause can be tested separately when interrupting charging is acceptable.
8. To roll back, turn off **Automatic load control** and re-enable the old automation. It will send its calculated limit on its next trigger. Do not leave both controllers active at the same time.

If anything looks wrong, turn off automatic control, re-enable the old automation, and capture the sensor values/log before further troubleshooting. Beta 10 does not enable automatic control after restart.

## Dashboard

`examples/lovelace/charging_view.yaml` is an example built with standard Home Assistant cards. It shows the controls, recommended current, minimum current, Easee maximum current, electrical detection, and EnergyTariff sensors. Replace the placeholder entity IDs with those created for your Smart Load Manager device before adding the YAML to a dashboard.

## Validation and limitations

GitHub Actions runs unit tests for electrical calculations, control decisions, and the exact service call for positive current/0 A with `time_to_live: 0`. It compiles the integration modules, checks JSON, and imports the config flow in the Home Assistant runtime. This does not prove that a command reached the physical charger. The supervised Home Assistant test above is needed to validate behavior with your Easee installation.
