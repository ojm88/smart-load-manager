"""Anonymized owner captures and documented Easee terminal wiring regressions."""
from dataclasses import replace
from math import sqrt
import unittest

from custom_components.smart_load_manager.calculations import (
    ElectricalSnapshot, detect_electrical_setup, kw_per_ampere,
)


class ConnectionTests(unittest.TestCase):
    def test_confirmed_it_capture_ignores_unused_t5_and_pe(self):
        sample = ElectricalSnapshot(connection="it_3", phase_mode=3,
            voltages_v={"T1T2": 1, "T1T3": 231, "T1T4": 238, "T1T5": 237,
                        "T2T3": 238, "T2T4": 242, "T2T5": 238,
                        "T3T4": 242, "T3T5": 403, "T4T5": 409})
        result = detect_electrical_setup(sample)
        self.assertEqual(result.voltage_type, "230V")
        self.assertEqual(result.line_voltage_v, 242)
        self.assertAlmostEqual(kw_per_ampere(result), sqrt(3) * .242)
        self.assertEqual(result.minimum_current_a, 11)

    def test_it_three_phase_second_capture(self):
        result = detect_electrical_setup(ElectricalSnapshot(connection="it_3", phase_mode=3,
            voltages_v={"T2T3": 227, "T2T4": 232, "T3T4": 230}))
        self.assertEqual(result.effective_phases, 3)
        self.assertEqual(result.voltage_type, "230V")
        self.assertAlmostEqual(kw_per_ampere(result), sqrt(3) * .232)

    def test_single_wiring_extra_readings_do_not_create_three_phases(self):
        result = detect_electrical_setup(ElectricalSnapshot(connection="it_1", phase_mode=1,
            voltages_v={"T2T3": 234, "T2T4": 235, "T2T5": 236}))
        self.assertEqual(result.effective_phases, 1)
        self.assertAlmostEqual(kw_per_ampere(result), .234)
        self.assertEqual(result.line_voltage_v, 234)

    def test_tn_capture_keeps_supply_and_mode_separate(self):
        sample = ElectricalSnapshot(connection="tn_3", phase_mode=3,
            voltages_v={"T2T3": 234, "T2T4": 238, "T2T5": 241})
        three = detect_electrical_setup(sample)
        one = detect_electrical_setup(replace(sample, phase_mode=1, output_phase=12))
        self.assertEqual(three.voltage_type, "400V")
        self.assertEqual(one.voltage_type, "400V")
        self.assertAlmostEqual(kw_per_ampere(three), .234 + .238 + .241)
        self.assertAlmostEqual(kw_per_ampere(one), .238)
        self.assertEqual(one.phase_neutral_voltage_v, 238)

    def test_210_volt_is_used_instead_of_nominal_230(self):
        for connection, output, currents in [
            ("tn_1", 10, {"T3": 10}), ("it_1", 11, {"T2": 10, "T3": 10})]:
            with self.subTest(connection=connection):
                result = detect_electrical_setup(ElectricalSnapshot(connection=connection,
                    phase_mode=1, output_phase=output, status="charging",
                    currents_a=currents, voltages_v={"T2T3": 210}))
                self.assertAlmostEqual(kw_per_ampere(result), .210)
                self.assertEqual(result.active_phases, 1)

    def test_tn_uses_the_assigned_phase_not_an_average_of_unused_phases(self):
        result = detect_electrical_setup(ElectricalSnapshot(connection="tn_3", output_phase=14,
            phase_mode=1, voltages_v={"T2T3": 240, "T2T4": 235, "T2T5": 210}))
        self.assertAlmostEqual(kw_per_ampere(result), .210)

    def test_missing_connection_never_infers_from_high_or_multiple_values(self):
        result = detect_electrical_setup(ElectricalSnapshot(phase_mode=3, output_phase=30,
            voltages_v={"T2T3": 230, "T2T4": 230, "T2T5": 230, "T3T4": 400}))
        self.assertIsNone(kw_per_ampere(result))
        self.assertIsNone(result.minimum_current_a)

    def test_missing_required_voltage_and_conflicting_topologies_fail_closed(self):
        sample = ElectricalSnapshot(connection="it_3", phase_mode=3,
            voltages_v={"T2T3": 230, "T2T4": 231, "T3T4": 232})
        for changed in [replace(sample, grid_type_code=1), replace(sample, output_phase=30),
                        replace(sample, grid_type_code=32),
                        replace(sample, voltages_v={"T2T3": 230, "T2T4": 231}),
                        replace(sample, voltages_v={"T2T3": 230, "T2T4": 400, "T3T4": 232}),
                        replace(sample, connection="it_1"),
                        replace(sample, connection="invalid")]:
            with self.subTest(changed=changed):
                result = detect_electrical_setup(changed)
                self.assertIsNone(kw_per_ampere(result))
                self.assertIsNone(result.minimum_current_a)

    def test_it_one_phase_uses_actual_pair_when_charging(self):
        result = detect_electrical_setup(ElectricalSnapshot(connection="it_3", phase_mode=1,
            output_phase=15, status="charging", currents_a={"T3": 12, "T4": 12},
            voltages_v={"T2T3": 240, "T2T4": 238, "T3T4": 210}))
        self.assertEqual(result.active_phases, 1)
        self.assertAlmostEqual(kw_per_ampere(result), .210)

    def test_nonfinite_or_missing_voltage_never_uses_a_nominal_fallback(self):
        for raw in [None, "", float("nan"), float("inf"), 0, -230]:
            result = detect_electrical_setup(ElectricalSnapshot(connection="tn_1", phase_mode=1,
                voltages_v={"T2T3": raw}))
            self.assertIsNone(kw_per_ampere(result))
