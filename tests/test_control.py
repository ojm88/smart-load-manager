"""Control decision and Easee service payload regression tests."""

import asyncio
import unittest

from custom_components.smart_load_manager.control import (
    async_send_dynamic_limit,
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


if __name__ == "__main__":
    unittest.main()
