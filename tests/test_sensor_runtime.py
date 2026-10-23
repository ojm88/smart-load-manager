"""Regression for a coordinator payload missing the measured-current field."""

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

        self.assertEqual(ChargingDiagnosticSensor.native_value.fget(fake), "disconnected")


if __name__ == "__main__":
    unittest.main()
