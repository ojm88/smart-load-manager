"""Anonymized owner captures and documented Easee terminal wiring regressions."""
from dataclasses import replace
from math import sqrt
import unittest

from custom_components.smart_load_manager.calculations import (
    ElectricalSnapshot, detect_electrical_setup, kw_per_ampere, recommended_current_a,
)


class ConnectionTests(unittest.TestCase):
    def test_it_startup_handles_one_conductor_crossing_threshold_first(self):
        sample = ElectricalSnapshot(
            connection="it_3", phase_mode=3, output_phase=22, status="charging",
            starting=True, currents_a={"T2": 0, "T3": .3, "T4": 1.9},
            voltages_v={"T2T3": 232, "T2T4": 236, "T3T4": 235},
        )
        self.assertAlmostEqual(kw_per_ampere(detect_electrical_setup(sample)), sqrt(3) * .236)
        self.assertIsNone(kw_per_ampere(detect_electrical_setup(replace(sample, starting=False))))
        self.assertIsNone(kw_per_ampere(detect_electrical_setup(
            replace(sample, currents_a={"T4": 8}))))
        self.assertIsNone(kw_per_ampere(detect_electrical_setup(
            replace(sample, voltages_v={}))))

    def test_it_budget_replays_cabin_recovery_without_25_amp_offer(self):
        sample = ElectricalSnapshot(
            connection="it_3", phase_mode=3, output_phase=22, status="charging",
            starting=True, voltages_v={"T2T3": 232, "T2T4": 237, "T3T4": 236},
        )
        # Easee reported the second conductor 0.16 s after the first.
        readings = (
            ({"T2": 5.5, "T3": .2, "T4": .2}, 0),
            ({"T2": 5.5, "T3": 5.5, "T4": .2}, 158),
            ({"T2": 5.5, "T3": 5.5, "T4": 5.5}, 158),
            ({"T2": 5.5, "T3": 5.5, "T4": .2}, 158),
        )
        offers = []
        for currents, power in readings:
            electrical = detect_electrical_setup(replace(sample, currents_a=currents))
            offers.append(recommended_current_a(
                hourly_limit_kwh=10, energy_used_kwh=3.81, han_power_w=5008,
                charger_power_w=power, minutes_left=26.04, safety_margin_kwh=.3,
                max_current_a=25, min_current_a=electrical.minimum_current_a,
                kw_per_amp=kw_per_ampere(electrical),
            ))
        self.assertEqual(offers, [None, 21, 21, 21])
        self.assertEqual(electrical.active_phases, 1)

        missing_voltage = replace(sample, currents_a=readings[1][0],
                                  voltages_v={"T2T3": 232})
        self.assertIsNone(kw_per_ampere(detect_electrical_setup(missing_voltage)))

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
