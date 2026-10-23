"""Regression tests from captured Easee sensor attribute patterns."""

import unittest
from datetime import datetime

from custom_components.smart_load_manager.calculations import (
    ElectricalSnapshot,
    detect_electrical_setup,
    han_measurement_is_fresh,
    kw_per_ampere,
    power_to_watts,
    recommended_current_a,
    schedule_window_active,
)


class ElectricalCalculationTests(unittest.TestCase):
  def test_schedule_window_handles_midnight_and_exact_end(self):
    active, _ = schedule_window_active(datetime(2026, 10, 22, 23, 0), "20:00:00")
    self.assertTrue(active)
    active, _ = schedule_window_active(datetime(2026, 10, 23, 7, 59), "20:00:00")
    self.assertTrue(active)
    active, _ = schedule_window_active(datetime(2026, 10, 23, 8, 0), "20:00:00")
    self.assertTrue(active)
    active, _ = schedule_window_active(datetime(2026, 10, 23, 8, 0, 1), "20:00:00")
    self.assertFalse(active)
    active, _ = schedule_window_active(datetime(2026, 10, 23, 19, 59), "20:00:00")
    self.assertFalse(active)

  def test_schedule_requires_valid_time(self):
    active, reason = schedule_window_active(datetime(2026, 10, 22, 23, 0), "unavailable")
    self.assertFalse(active)
    self.assertIn("ugyldig", reason)

  def test_han_freshness_requires_positive_recent_measurement(self):
    self.assertTrue(han_measurement_is_fresh(60, 1000))
    self.assertFalse(han_measurement_is_fresh(61, 1000))
    self.assertFalse(han_measurement_is_fresh(10, 0))
    self.assertFalse(han_measurement_is_fresh(None, 1000))

  def test_garage_chargeup_detects_400v_three_phase_from_ln_measurements(self):
    snapshot = ElectricalSnapshot(
        output_phase=30,
        status="charging",
        currents_a={"T2": 0.9, "T3": 16.2, "T4": 16.1, "T5": 16.2},
        voltages_v={"T2T3": 230, "T2T4": 233, "T2T5": 239},
    )

    result = detect_electrical_setup(snapshot)

    self.assertEqual(result.configured_phases, 3)
    self.assertEqual(result.active_phases, 3)
    self.assertEqual(result.effective_phases, 3)
    self.assertEqual(result.voltage_type, "400V")
    self.assertAlmostEqual(result.line_voltage_v, 405.3, delta=1)
    self.assertAlmostEqual(result.phase_neutral_voltage_v, 234, delta=1)
    self.assertAlmostEqual(kw_per_ampere(result), 0.702, delta=0.003)


  def test_three_phase_400v_prefers_measured_line_voltage(self):
    snapshot = ElectricalSnapshot(
        output_phase=30,
        status="charging",
        currents_a={"T3": 16, "T4": 16, "T5": 16},
        voltages_v={
            "T2T3": 230,
            "T2T4": 233,
            "T2T5": 239,
            "T3T4": 403,
            "T3T5": 409,
            "T4T5": 406,
        },
    )

    result = detect_electrical_setup(snapshot)

    self.assertEqual(result.voltage_type, "400V")
    self.assertAlmostEqual(result.line_voltage_v, 406)
    self.assertAlmostEqual(kw_per_ampere(result), 0.703, delta=0.003)


  def test_three_phase_230v_it_uses_measured_line_voltage(self):
    snapshot = ElectricalSnapshot(
        output_phase=30,
        status="charging",
        currents_a={"T3": 12, "T4": 12, "T5": 12},
        voltages_v={"T3T4": 230, "T3T5": 232, "T4T5": 228},
    )

    result = detect_electrical_setup(snapshot)

    self.assertEqual(result.active_phases, 3)
    self.assertEqual(result.voltage_type, "230V")
    self.assertAlmostEqual(result.line_voltage_v, 230)
    self.assertAlmostEqual(kw_per_ampere(result), 0.398, delta=0.002)


  def test_single_phase_230v_uses_measured_phase_neutral_voltage(self):
    snapshot = ElectricalSnapshot(
        output_phase=10,
        status="charging",
        currents_a={"T3": 13, "T4": 0, "T5": 0},
        voltages_v={"T2T3": 229.7, "T2T4": 231, "T2T5": 230},
    )

    result = detect_electrical_setup(snapshot)

    self.assertEqual(result.configured_phases, 1)
    self.assertEqual(result.active_phases, 1)
    self.assertEqual(result.effective_phases, 1)
    self.assertEqual(result.voltage_type, "230V")
    self.assertAlmostEqual(result.line_voltage_v, 230.2, delta=1)
    self.assertAlmostEqual(kw_per_ampere(result), 0.230, delta=0.002)


  def test_idle_charger_reports_configured_and_actual_phases_separately(self):
    snapshot = ElectricalSnapshot(
        output_phase=30,
        status="disconnected",
        currents_a={"T3": 0, "T4": 0, "T5": 0},
        voltages_v={"T2T3": 230, "T2T4": 232, "T2T5": 229},
    )

    result = detect_electrical_setup(snapshot)

    self.assertEqual(result.configured_phases, 3)
    self.assertEqual(result.active_phases, 0)
    self.assertEqual(result.effective_phases, 3)
    self.assertEqual(result.voltage_type, "400V")


  def test_missing_measurements_return_unknown_instead_of_guessing(self):
    result = detect_electrical_setup(ElectricalSnapshot(output_phase=30))

    self.assertEqual(result.voltage_type, "unknown")
    self.assertIsNone(result.line_voltage_v)
    self.assertEqual(result.confidence, "none")

  def test_blank_attribute_values_are_ignored(self):
    result = detect_electrical_setup(
        ElectricalSnapshot(
            output_phase=30,
            status="charging",
            currents_a={"T3": 15, "T4": 15, "T5": 15},
            voltages_v={"T2T3": 230, "T2T4": "", "T2T5": None},
        )
    )

    self.assertEqual(result.voltage_type, "400V")
    self.assertAlmostEqual(result.phase_neutral_voltage_v, 230)

  def test_active_current_count_overrides_configured_phases_while_charging(self):
    result = detect_electrical_setup(
        ElectricalSnapshot(
            output_phase=30,
            status="charging",
            currents_a={"T3": 12, "T4": 0.2, "T5": 0.1},
            voltages_v={"T2T3": 230, "T2T4": 231, "T2T5": 229},
        )
    )

    self.assertEqual(result.configured_phases, 3)
    self.assertEqual(result.active_phases, 1)
    self.assertEqual(result.effective_phases, 1)
    self.assertEqual(result.voltage_type, "230V")


  def test_power_sensor_unit_is_normalized_to_watts(self):
    samples = [
        (4200, "W", 4200),
        (4.2, "kW", 4200),
        (0.23, "KW", 230),
        (-350, "W", -350),
    ]
    for value, unit, expected in samples:
      with self.subTest(value=value, unit=unit):
        self.assertAlmostEqual(power_to_watts(value, unit), expected)


  def test_energy_sensor_is_rejected_as_not_instantaneous_power(self):
    with self.assertRaisesRegex(ValueError, "W eller kW"):
      power_to_watts(12, "kWh")

  def test_230v_three_active_phases_uses_11a_minimum(self):
    result = detect_electrical_setup(ElectricalSnapshot(
        output_phase=22, phase_mode=2, grid_type_code=4,
        status="charging", currents_a={"T3": 12, "T4": 12, "T5": 12},
        voltages_v={"T3T4": 230, "T3T5": 232, "T4T5": 228},
    ))
    self.assertEqual(result.active_phases, 3)
    self.assertEqual(result.minimum_current_a, 11)
    self.assertEqual(result.phase_mode_name, "Automatisk")
    self.assertEqual(result.output_phase_name, "To faser IT (L1+L2, L2+L3)")
    self.assertEqual(result.grid_type_name, "IT, tre faser")

  def test_one_or_two_active_phases_use_6a_minimum(self):
    one_phase = detect_electrical_setup(ElectricalSnapshot(
        output_phase=11, status="charging", currents_a={"T3": 10, "T4": 0, "T5": 0},
        voltages_v={"T3T4": 230},
    ))
    two_phase = detect_electrical_setup(ElectricalSnapshot(
        output_phase=22, status="charging", currents_a={"T3": 10, "T4": 10, "T5": 0},
        voltages_v={"T3T4": 230},
    ))
    self.assertEqual(one_phase.minimum_current_a, 6)
    self.assertEqual(two_phase.minimum_current_a, 6)
    self.assertAlmostEqual(kw_per_ampere(two_phase), 0.46, delta=0.01)

  def test_unknown_phase_or_voltage_never_guesses_minimum(self):
    result = detect_electrical_setup(ElectricalSnapshot(
        output_phase=30, status="charging", currents_a={"T3": 10, "T4": 10, "T5": 10}
    ))
    self.assertIsNone(result.minimum_current_a)

  def test_paused_charger_uses_reported_output_phase_for_safe_resume_minimum(self):
    result = detect_electrical_setup(ElectricalSnapshot(
        output_phase=30, phase_mode=3, status="awaiting_start",
        currents_a={"T3": 0, "T4": 0, "T5": 0},
        voltages_v={"T2T3": 230, "T2T4": 231, "T2T5": 229},
    ))
    self.assertEqual(result.minimum_current_a, 6)

  def test_recommended_current_respects_energy_budget_and_minimum(self):
    args = dict(hourly_limit_kwh=10, energy_used_kwh=5, han_power_w=5000,
                charger_power_w=3000, minutes_left=30, safety_margin_kwh=0.3,
                max_current_a=16, min_current_a=6, kw_per_amp=0.23)
    self.assertEqual(recommended_current_a(**args), 16)
    args["energy_used_kwh"] = 9.8
    self.assertEqual(recommended_current_a(**args), 0)
    args["min_current_a"] = None
    self.assertIsNone(recommended_current_a(**args))


if __name__ == "__main__":
  unittest.main()

