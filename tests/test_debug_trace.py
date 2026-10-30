"""Recorder privacy, bounded history and command outcome guarantees."""
import json
import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock
from custom_components.smart_load_manager.debug_trace import DebugTrace, sample_data
from custom_components.smart_load_manager.control import async_send_dynamic_limit


class DebugTraceTests(unittest.TestCase):
    def test_allowlist_drops_secrets_even_under_known_numeric_keys(self):
        data = {'token': 'SECRET', 'status': 'SECRET', 'han_power_w': 'SECRET',
                'control_reason': 'SECRET', 'electrical': {'name': 'SECRET'},
                'terminal_voltages_v': {'T2T3': 230, 'SECRET': 500},
                'charger_current_a': float('nan'), 'han_fresh': False}
        result = sample_data(data)
        self.assertNotIn('SECRET', json.dumps(result, allow_nan=False))
        self.assertEqual(result['terminal_voltages_v'], {'T2T3': 230})
        self.assertFalse(result['han_fresh'])

    def test_bounded_order_anonymous_identity_and_export_isolation(self):
        trace = DebugTrace(capacity=2)
        for target in (16, 0, 6):
            trace.record('decision', 'private_identity', target=target)
        result = trace.export()
        self.assertEqual(result['dropped_events'], 1)
        self.assertEqual([e['target'] for e in result['events']], [0, 6])
        self.assertEqual([e['sequence'] for e in result['events']], [2, 3])
        self.assertNotIn('private_identity', json.dumps(result))
        result['events'][0]['target'] = 99
        self.assertEqual(trace.export()['events'][0]['target'], 0)


class CommandTraceTests(unittest.IsolatedAsyncioTestCase):
    async def test_service_failure_is_not_logged_as_success(self):
        trace = DebugTrace()
        c = NS(entry=NS(data={'charger_device': 'secret_device'}), data={'han_power_w': 1000})
        service = AsyncMock(side_effect=RuntimeError('SECRET credential failure'))
        hass = NS(data={'smart_load_manager': {'site': NS(debug_trace=trace, controllers={'private_load': c})}},
                  services=NS(async_call=service))
        with self.assertRaises(RuntimeError):
            await async_send_dynamic_limit(hass, 'secret_device', 0)
        service.side_effect = None
        await async_send_dynamic_limit(hass, 'secret_device', 6)
        result = trace.export()
        self.assertEqual([e['event'] for e in result['events']],
            ['current_attempt','current_failed','current_attempt','current_service_success'])
        for secret in ('SECRET', 'secret_device', 'private_load'):
            self.assertNotIn(secret, json.dumps(result))
