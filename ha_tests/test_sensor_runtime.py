"""Regression for coordinator payloads and entity registration under Home Assistant."""

from types import SimpleNamespace
import unittest

from smart_load_manager.sensor import ChargingDiagnosticSensor, SENSORS


class SensorRuntimeTests(unittest.TestCase):
    def test_new_sensor_uses_the_stable_slm_entity_id(self):
        coordinator = SimpleNamespace(data={}, last_update_success=True)
        entry = SimpleNamespace(entry_id="test-entry", title="Smart Load Manager OJM")
        entity = ChargingDiagnosticSensor(
            coordinator, entry, "status", *SENSORS["status"]
        )

        self.assertEqual(entity.entity_id, "sensor.slm_charger_status")

    def test_all_sensors_remain_readable_with_an_empty_coordinator_payload(self):
        fake_hass = SimpleNamespace(config=SimpleNamespace(language="nb"))
        coordinator = SimpleNamespace(data={}, last_update_success=True)
        for key in SENSORS:
            with self.subTest(sensor=key):
                entity = SimpleNamespace(
                    _key=key, coordinator=coordinator, hass=fake_hass
                )
                ChargingDiagnosticSensor.native_value.fget(entity)
                self.assertIn(
                    "explanation",
                    ChargingDiagnosticSensor.extra_state_attributes.fget(entity),
                )

    def test_sensor_exposes_a_localized_explanation(self):
        fake = SimpleNamespace(
            _key="charger_current",
            coordinator=SimpleNamespace(data={}),
            hass=SimpleNamespace(config=SimpleNamespace(language="nb")),
        )
        self.assertIn("Strømmen Easee måler", ChargingDiagnosticSensor.extra_state_attributes.fget(fake)["explanation"])

    def test_single_card_yaml_is_not_a_full_sections_view(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        card = (root / "examples/lovelace/charging_card.yaml").read_text()
        view = (root / "examples/lovelace/charging_view.yaml").read_text()
        self.assertTrue(card.lstrip().startswith("#"))
        self.assertIn("type: vertical-stack", card)
        self.assertNotIn("type: sections", card)
        self.assertTrue(view.lstrip().startswith("#"))
        self.assertIn("type: sections", view)

    def test_other_diagnostics_still_load_if_current_field_is_missing(self):
        data = {
            "electrical": {
                "phase_mode_name": "auto", "output_phase_name": "none",
                "active_phases": 0, "grid_type_name": "unknown",
                "voltage_type": "unknown", "line_voltage_v": None,
                "phase_neutral_voltage_v": None, "confidence": "low",
                "reason": "no phase data", "no_current_reason": "none",
            },
            "status": "disconnected", "minimum_current_a": None,
            "recommended_current_a": 0, "max_current_a": 16,
            "charger_power_w": 0, "han_power_w": 1000,
            "energy_used_kwh": 0, "energy_estimate_kwh": None,
            "control_reason": "disconnected", "auto_control": False,
            "han_age_seconds": 1, "han_fresh": True,
            "schedule_enabled": False, "schedule_reason": "off",
        }
        fake = SimpleNamespace(
            _key="status",
            coordinator=SimpleNamespace(data=data),
            hass=SimpleNamespace(config=SimpleNamespace(language="nb")),
        )

        self.assertEqual(
            ChargingDiagnosticSensor.native_value.fget(fake), "disconnected"
        )


if __name__ == "__main__":
    unittest.main()
