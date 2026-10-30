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
    next_schedule_transition,
)


class ElectricalCalculationTests(unittest.TestCase):
  def test_schedule_window_handles_midnight_and_exact_end(self):
    active, _ = schedule_window_active(datetime(2026, 10, 22, 23, 0), "20:00:00")
    self.assertTrue(active)
    active, _ = schedule_window_active(datetime(2026, 10, 23, 7, 59), "20:00:00")
    self.assertTrue(active)
    active, _ = schedule_window_active(datetime(2026, 10, 23, 8, 0), "20:00:00")
    self.assertFalse(active)
    active, _ = schedule_window_active(datetime(2026, 10, 23, 8, 0, 1), "20:00:00")
    self.assertFalse(active)
    active, _ = schedule_window_active(datetime(2026, 10, 23, 19, 59), "20:00:00")
    self.assertFalse(active)

  def test_schedule_requires_valid_time(self):
    active, reason = schedule_window_active(datetime(2026, 10, 22, 23, 0), "unavailable")
    self.assertFalse(active)
    self.assertIn("ugyldig", reason)

  def test_next_schedule_boundary_uses_seconds_and_midnight(self):
    from datetime import UTC
    now = datetime(2026, 10, 28, 22, 59, 59, tzinfo=UTC)
    self.assertEqual(next_schedule_transition(now, '23:00:00'), now.timestamp()+1)
    at_start = datetime(2026, 10, 28, 23, tzinfo=UTC)
    self.assertEqual(next_schedule_transition(at_start, '23:00:00'),
                     datetime(2026, 10, 29, 11, tzinfo=UTC).timestamp())
    at_end = datetime(2026, 10, 29, 11, tzinfo=UTC)
    self.assertEqual(next_schedule_transition(at_end, '23:00:00'),
                     datetime(2026, 10, 29, 23, tzinfo=UTC).timestamp())
    self.assertIsNone(next_schedule_transition(now, 'invalid'))

  def test_schedule_boundaries_follow_local_time_across_dst(self):
    from zoneinfo import ZoneInfo
    oslo = ZoneInfo('Europe/Oslo')
    for month, day in ((3, 28), (10, 24)):
      now = datetime(2026, month, day, 23, tzinfo=oslo)
      end = datetime(2026, month, day+1, 11, tzinfo=oslo)
      self.assertEqual(next_schedule_transition(now, '23:00:00'), end.timestamp())
      self.assertFalse(schedule_window_active(end, '23:00:00')[0])

  def test_han_freshness_requires_positive_recent_measurement(self):
    self.assertTrue(han_measurement_is_fresh(60, 1000))
    self.assertTrue(han_measurement_is_fresh(61, 1000))
    self.assertTrue(han_measurement_is_fresh(120, 1000))
    self.assertFalse(han_measurement_is_fresh(120.001, 1000))
    self.assertFalse(han_measurement_is_fresh(-1, 1000))
    self.assertFalse(han_measurement_is_fresh(10, 0))
    self.assertFalse(han_measurement_is_fresh(None, 1000))

  def test_garage_chargeup_detects_400v_three_phase_from_ln_measurements(self):
    snapshot = ElectricalSnapshot(connection="tn_3",
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
    snapshot = ElectricalSnapshot(connection="tn_3",
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
    self.assertAlmostEqual(result.line_voltage_v, 405.3)
    self.assertAlmostEqual(kw_per_ampere(result), 0.703, delta=0.003)


  def test_three_phase_230v_it_uses_measured_line_voltage(self):
    result = detect_electrical_setup(ElectricalSnapshot(
        connection="it_3", output_phase=22, phase_mode=3, status="charging",
        currents_a={"T2": 12, "T3": 12, "T4": 12},
        voltages_v={"T2T3": 230, "T2T4": 232, "T3T4": 228}))
    self.assertEqual(result.active_phases, 3)
    self.assertEqual(result.voltage_type, "230V")
    self.assertEqual(result.line_voltage_v, 232)
    self.assertAlmostEqual(kw_per_ampere(result), 0.402, delta=0.002)

  def test_single_phase_230v_uses_measured_phase_neutral_voltage(self):
    snapshot = ElectricalSnapshot(connection="tn_3",
        output_phase=10,
        status="charging",
        currents_a={"T3": 13, "T4": 0, "T5": 0},
        voltages_v={"T2T3": 229.7, "T2T4": 231, "T2T5": 230},
    )

    result = detect_electrical_setup(snapshot)

    self.assertEqual(result.configured_phases, 1)
    self.assertEqual(result.active_phases, 1)
    self.assertEqual(result.effective_phases, 1)
    self.assertEqual(result.voltage_type, "400V")
    self.assertAlmostEqual(result.phase_neutral_voltage_v, 229.7)
    self.assertAlmostEqual(kw_per_ampere(result), 0.230, delta=0.002)


  def test_idle_charger_reports_configured_and_actual_phases_separately(self):
    snapshot = ElectricalSnapshot(connection="tn_3",
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
    result = detect_electrical_setup(ElectricalSnapshot(connection="tn_3", output_phase=30))

    self.assertEqual(result.voltage_type, "400V")
    self.assertIsNone(result.line_voltage_v)
    self.assertEqual(result.confidence, "none")

  def test_blank_attribute_values_are_ignored(self):
    result = detect_electrical_setup(
        ElectricalSnapshot(connection="tn_3",
            output_phase=30,
            status="charging",
            currents_a={"T3": 15, "T4": 15, "T5": 15},
            voltages_v={"T2T3": 230, "T2T4": "", "T2T5": None},
        )
    )

    self.assertEqual(result.voltage_type, "400V")
    self.assertIsNone(kw_per_ampere(result))

  def test_active_current_count_overrides_configured_phases_while_charging(self):
    result = detect_electrical_setup(
        ElectricalSnapshot(connection="tn_3",
            output_phase=30,
            status="charging",
            currents_a={"T3": 12, "T4": 0.2, "T5": 0.1},
            voltages_v={"T2T3": 230, "T2T4": 231, "T2T5": 229},
        )
    )

    self.assertEqual(result.configured_phases, 3)
    self.assertEqual(result.active_phases, 1)
    self.assertEqual(result.effective_phases, 1)
    self.assertEqual(result.voltage_type, "400V")


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
    result = detect_electrical_setup(ElectricalSnapshot(connection="it_3",
        output_phase=22, phase_mode=2, grid_type_code=4,
        status="charging", currents_a={"T2": 12, "T3": 12, "T4": 12},
        voltages_v={"T2T3": 230, "T2T4": 232, "T3T4": 228},
    ))
    self.assertEqual(result.active_phases, 3)
    self.assertEqual(result.minimum_current_a, 11)
    self.assertEqual(result.phase_mode_name, "Automatisk")
    self.assertEqual(result.output_phase_name, "To faser IT (L1+L2, L2+L3)")
    self.assertEqual(result.grid_type_name, "IT, tre faser")

  def test_it_single_path_counts_two_conductors_as_one_phase(self):
    result = detect_electrical_setup(ElectricalSnapshot(
        connection="it_3", output_phase=11, phase_mode=1, status="charging",
        currents_a={"T2": 10, "T3": 10, "T4": 0}, voltages_v={"T2T3": 210}))
    self.assertEqual(result.active_phases, 1)
    self.assertEqual(result.minimum_current_a, 6)
    self.assertAlmostEqual(kw_per_ampere(result), .210)

  def test_unknown_phase_or_voltage_never_guesses_minimum(self):
    result = detect_electrical_setup(ElectricalSnapshot(connection="tn_3",
        output_phase=30, status="charging", currents_a={"T3": 10, "T4": 10, "T5": 10}
    ))
    self.assertIsNone(result.minimum_current_a)

  def test_paused_charger_uses_reported_output_phase_for_safe_resume_minimum(self):
    result = detect_electrical_setup(ElectricalSnapshot(connection="tn_3",
        output_phase=30, phase_mode=3, status="awaiting_start",
        currents_a={"T3": 0, "T4": 0, "T5": 0},
        voltages_v={"T2T3": 230, "T2T4": 231, "T2T5": 229},
    ))
    self.assertEqual(result.minimum_current_a, 6)

  def test_charging_before_current_sensor_updates_uses_validated_connection(self):
    for connection, mode, volts, minimum in (
        ('tn_3', 3, {'T2T3': 235, 'T2T4': 239, 'T2T5': 241}, 6),
        ('tn_3', 1, {'T2T3': 235, 'T2T4': 239, 'T2T5': 241}, 6),
        ('tn_1', 1, {'T2T3': 210}, 6),
        ('it_3', 3, {'T2T3': 210, 'T2T4': 212, 'T3T4': 211}, 11),
        ('it_3', 1, {'T2T3': 210, 'T2T4': 212, 'T3T4': 211}, 6),
        ('it_1', 1, {'T2T3': 210}, 6),
    ):
      with self.subTest(connection=connection, mode=mode):
        args = dict(connection=connection, phase_mode=mode, voltages_v=volts,
                    currents_a={'T2': 0, 'T3': 0, 'T4': 0, 'T5': 0})
        waiting = detect_electrical_setup(ElectricalSnapshot(status='awaiting_start', **args))
        starting = detect_electrical_setup(ElectricalSnapshot(status='charging', **args))
        self.assertEqual(starting.active_phases, 0)
        self.assertEqual(starting.minimum_current_a, minimum)
        self.assertEqual(kw_per_ampere(starting), kw_per_ampere(waiting))
        args['voltages_v'] = {}
        missing = detect_electrical_setup(ElectricalSnapshot(status='charging', **args))
        self.assertIsNone(kw_per_ampere(missing))
        self.assertIsNone(missing.minimum_current_a)

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

