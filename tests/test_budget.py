"""Regression tests for the integration-owned hourly consumption target."""

import unittest
from types import SimpleNamespace

from custom_components.smart_load_manager.budget import (
    CONSUMPTION_LIMIT_OPTIONS,
    consumption_limit_option,
    consumption_limit_value,
)


class ConsumptionBudgetTests(unittest.TestCase):
    def test_options_match_the_former_input_select(self):
        self.assertEqual(len(CONSUMPTION_LIMIT_OPTIONS), 32)
        self.assertEqual(CONSUMPTION_LIMIT_OPTIONS[0], "4.5")
        self.assertEqual(CONSUMPTION_LIMIT_OPTIONS[1], "5")
        self.assertEqual(CONSUMPTION_LIMIT_OPTIONS[-1], "20")

    def test_new_selection_is_authoritative(self):
        entry = SimpleNamespace(options={"consumption_limit_kwh": 7.5}, data={"hourly_limit_kwh": 15})
        self.assertEqual(consumption_limit_value(entry), 7.5)
        self.assertEqual(consumption_limit_option(entry), "7.5")

    def test_beta9_value_is_preserved_on_upgrade(self):
        entry = SimpleNamespace(options={}, data={"hourly_limit_kwh": 12.5})
        self.assertEqual(consumption_limit_value(entry), 12.5)
        self.assertEqual(consumption_limit_option(entry), "12.5")

    def test_legacy_values_outside_selector_range_are_clamped(self):
        too_high = SimpleNamespace(options={}, data={"hourly_limit_kwh": 50})
        too_low = SimpleNamespace(options={}, data={"hourly_limit_kwh": 1})
        self.assertEqual(consumption_limit_value(too_high), 20)
        self.assertEqual(consumption_limit_option(too_high), "20")
        self.assertEqual(consumption_limit_value(too_low), 4.5)
        self.assertEqual(consumption_limit_option(too_low), "4.5")


if __name__ == "__main__":
    unittest.main()
