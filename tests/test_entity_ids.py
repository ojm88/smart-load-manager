"""Stable entity ID and manual-control ownership regressions."""

import unittest
import json
from pathlib import Path

from custom_components.smart_load_manager.control import manual_control_is_available
from custom_components.smart_load_manager.entity_ids import (
    ENTITY_OBJECT_IDS,
    SENSOR_OBJECT_IDS,
    suggested_entity_id,
)


class EntityIdTests(unittest.TestCase):
    def test_sensor_ids_use_short_slm_prefix(self):
        self.assertTrue(SENSOR_OBJECT_IDS)
        self.assertTrue(all(value.startswith("slm_") for value in SENSOR_OBJECT_IDS.values()))

    def test_every_translated_sensor_has_a_stable_id(self):
        root = Path(__file__).parents[1] / "custom_components" / "smart_load_manager"
        for language in ("nb", "en"):
            translated_keys = set(
                json.loads((root / "translations" / f"{language}.json").read_text())
                ["entity"]["sensor"]
            )
            self.assertEqual(translated_keys, set(SENSOR_OBJECT_IDS))

    def test_shared_consumption_limit_keeps_agreed_id(self):
        self.assertEqual(
            suggested_entity_id("select", "consumption_limit"),
            "smart_load_manager_ojm_easee_forbruksgrense",
        )

    def test_manual_current_number_has_short_id(self):
        self.assertEqual(
            suggested_entity_id("number", "manual_current_limit"),
            "slm_manual_current",
        )

    def test_manual_current_is_locked_when_automatic_control_owns_it(self):
        self.assertFalse(manual_control_is_available(True))
        self.assertTrue(manual_control_is_available(False))


if __name__ == "__main__":
    unittest.main()

class MultiChargerIdTests(unittest.TestCase):
    def test_second_charger_has_stable_noncolliding_ids(self):
        from types import SimpleNamespace
        entry = SimpleNamespace(data={'entity_suffix': 'carport_abc123'})
        for domain, mapping in ENTITY_OBJECT_IDS.items():
            for key in mapping:
                first = suggested_entity_id(domain,key)
                second = suggested_entity_id(domain,key,entry)
                self.assertNotEqual(first,second)
                self.assertEqual(second, first+'_carport_abc123')
