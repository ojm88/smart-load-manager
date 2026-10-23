"""Control decision and Easee service payload regression tests."""

import asyncio
import unittest

from custom_components.smart_load_manager.control import (
    async_send_dynamic_limit,
    async_send_phase_mode,
    target_current_for_control,
)


class ControlDecisionTests(unittest.TestCase):
    def target(self, **overrides):
        values = {
            "enabled": True,
            "recommendation": 12,
            "connected": True,
            "schedule_allowed": True,
            "sources_valid": True,
        }
        values.update(overrides)
        return target_current_for_control(**values)

    def test_allowed_charging_sends_recommendation(self):
        self.assertEqual(self.target(), 12)

    def test_disconnected_charger_sends_zero(self):
        self.assertEqual(self.target(connected=False), 0)

    def test_closed_schedule_sends_zero(self):
        self.assertEqual(self.target(schedule_allowed=False), 0)

    def test_invalid_meter_or_tariff_input_sends_zero(self):
        self.assertEqual(self.target(sources_valid=False), 0)

    def test_unknown_recommendation_sends_zero(self):
        self.assertEqual(self.target(recommendation=None), 0)

    def test_disabled_control_does_not_send_a_command(self):
        self.assertIsNone(self.target(enabled=False))

    def test_explicit_pause_sends_zero_even_when_automatic_control_is_off(self):
        self.assertEqual(self.target(enabled=False, paused=True), 0)


class EaseeServicePayloadTests(unittest.TestCase):
    def test_current_and_zero_are_sent_with_indefinite_ttl(self):
        calls = []

        class Services:
            async def async_call(self, domain, service, data, *, blocking):
                calls.append((domain, service, data, blocking))

        class Hass:
            services = Services()

        async def run():
            await async_send_dynamic_limit(Hass(), "charger-device-id", 13)
            await async_send_dynamic_limit(Hass(), "charger-device-id", 0)

        asyncio.run(run())

        self.assertEqual(
            calls,
            [
                ("easee", "set_charger_dynamic_limit", {
                    "device_id": "charger-device-id", "current": 13, "time_to_live": 0
                }, True),
                ("easee", "set_charger_dynamic_limit", {
                    "device_id": "charger-device-id", "current": 0, "time_to_live": 0
                }, True),
            ],
        )

    def test_phase_mode_uses_documented_easee_service_values(self):
        calls = []

        class Services:
            async def async_call(self, domain, service, data, *, blocking):
                calls.append((domain, service, data, blocking))

        class Hass:
            services = Services()

        async def run():
            for mode in ("1_phase", "auto_phase", "3_phase"):
                await async_send_phase_mode(Hass(), "charger-device-id", mode)

        asyncio.run(run())
        self.assertEqual(
            calls,
            [
                ("easee", "set_charger_phase_mode", {"device_id": "charger-device-id", "phase_mode": mode}, True)
                for mode in ("1_phase", "auto_phase", "3_phase")
            ],
        )

    def test_phase_mode_rejects_unsupported_values(self):
        class Hass:
            services = None

        with self.assertRaises(ValueError):
            asyncio.run(async_send_phase_mode(Hass(), "charger-device-id", "2_phase"))


if __name__ == "__main__":
    unittest.main()
