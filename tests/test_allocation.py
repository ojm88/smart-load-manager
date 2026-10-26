"""Shared-budget regressions with unequal charging forms and limited capacity."""
import unittest
from custom_components.smart_load_manager.allocation import Demand, allocate, available_charging_kw


class AllocationTests(unittest.TestCase):
    def test_two_single_phase_chargers_fit_with_six_kw_house(self):
        capacity = available_charging_kw(limit_kwh=10, used_kwh=5, margin_kwh=.3,
            minutes_left=30, han_w=6000, managed_power_w=0)
        self.assertAlmostEqual(capacity, 3.4)
        result = allocate([Demand('a', .23, 6, 16), Demand('b', .23, 6, 16)], capacity, 'both', 'a')
        self.assertEqual(result, {'a': 7, 'b': 7})

    def test_minimums_that_do_not_fit_give_priority_to_selected(self):
        demands = [Demand('a', .692, 6, 16), Demand('b', .692, 6, 16)]
        self.assertEqual(allocate(demands, 6, 'both', 'b'), {'a': 0, 'b': 8})
        self.assertEqual(allocate(demands, 3, 'both', 'b'), {'a': 0, 'b': 0})

    def test_sequential_and_finished_priority(self):
        ds = [Demand('a', .23, 6, 16), Demand('b', .23, 6, 16)]
        self.assertEqual(allocate(ds, 8, 'one_at_a_time', 'a'), {'a': 16, 'b': 0})
        self.assertEqual(allocate(ds[1:], 8, 'one_at_a_time', 'a'), {'b': 16})

    def test_equal_power_not_equal_ampere_and_unused_capacity(self):
        ds = [Demand('a', .23, 6, 16), Demand('b', .69, 6, 16)]
        result = allocate(ds, 9, 'both', 'a')
        self.assertEqual(result, {'a': 16, 'b': 7})

    def test_budget_subtracts_both_chargers_from_han_once(self):
        capacity = available_charging_kw(limit_kwh=10, used_kwh=5, margin_kwh=.3,
            minutes_left=30, han_w=10000, managed_power_w=4000)
        self.assertAlmostEqual(capacity, 3.4)

    def test_matrix_never_overallocates_or_issues_below_minimum(self):
        for coeff_a in [.23, .398, .692]:
            for coeff_b in [.23, .398, .692]:
                ds = [Demand('a', coeff_a, 6 if coeff_a != .398 else 11, 16),
                      Demand('b', coeff_b, 6 if coeff_b != .398 else 11, 10)]
                for units in range(0, 301):
                    cap = units / 20
                    for mode in ['both', 'one_at_a_time']:
                        for priority in ['a', 'b']:
                            result = allocate(ds, cap, mode, priority)
                            self.assertLessEqual(sum(result[d.key] * d.kw_per_amp for d in ds), cap + 1e-8)
                            for d in ds:
                                self.assertTrue(result[d.key] == 0 or d.minimum_a <= result[d.key] <= d.maximum_a)

    def test_invalid_values_fail_closed(self):
        with self.assertRaises(ValueError):
            allocate([], float('nan'), 'both', 'a')
        with self.assertRaises(ValueError):
            available_charging_kw(limit_kwh=10, used_kwh=-1, margin_kwh=.3,
                minutes_left=30, han_w=6000, managed_power_w=0)
