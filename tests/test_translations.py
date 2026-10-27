"""Prevent raw translation keys and unexplained setup fields in HA UI."""

import json
import re
import unittest
from pathlib import Path


INTEGRATION = Path(__file__).parents[1] / "custom_components" / "smart_load_manager"


class TranslationCoverageTests(unittest.TestCase):
    def test_all_entities_have_norwegian_and_english_names(self):
        sensor_source = (INTEGRATION / "sensor.py").read_text()
        sensor_keys = set(re.findall(r'^\s+"([a-z_]+)": \(', sensor_source, re.MULTILINE))
        expected = {
            "sensor": sensor_keys,
            "switch": {"automatic_control", "schedule_control", "charging_pause", "charging_priority"},
            "number": {"manual_current_limit"},
            "select": {"consumption_limit", "phase_mode_control", "allocation_mode", "priority_charger"},
            "time": {"schedule_start_time"},
        }
        for language in ("nb", "en"):
            with self.subTest(language=language):
                translation = json.loads((INTEGRATION / "translations" / f"{language}.json").read_text())
                for domain, keys in expected.items():
                    for key in keys:
                        self.assertTrue(
                            translation["entity"][domain][key]["name"],
                            f"Missing {language} name for {domain}.{key}",
                        )

    def test_every_setup_field_has_an_explanation_in_both_languages(self):
        for language in ("nb", "en"):
            with self.subTest(language=language):
                flow = json.loads((INTEGRATION / "translations" / f"{language}.json").read_text())["config"]["step"]["household"]
                self.assertEqual(set(flow["data"]), set(flow["data_description"]))

    def test_control_reason_has_plain_language_name(self):
        expected_names = {"nb": "Ladeforklaring", "en": "Charging explanation"}
        for language, expected_name in expected_names.items():
            with self.subTest(language=language):
                translation = json.loads((INTEGRATION / "translations" / f"{language}.json").read_text())
                self.assertEqual(
                    translation["entity"]["sensor"]["control_reason"]["name"],
                    expected_name,
                )
        sensor_source = (INTEGRATION / "sensor.py").read_text()
        self.assertIn("hvorfor anbefalt ladestrøm justeres", sensor_source)

    def test_control_reason_messages_are_neutral_and_technical(self):
        coordinator_source = (INTEGRATION / "coordinator.py").read_text()
        self.assertNotIn('control_reason = "Jeg ', coordinator_source)
        self.assertIn("målt husforbruk, gjenstående timebudsjett og sikkerhetsmargin", coordinator_source)


if __name__ == "__main__":
    unittest.main()
