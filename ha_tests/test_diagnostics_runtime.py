"""Native HA diagnostics entry point returns JSON with no configuration secrets."""
import json
from types import SimpleNamespace as NS
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock
from smart_load_manager.debug_trace import DebugTrace
from smart_load_manager.diagnostics import async_get_config_entry_diagnostics


class DiagnosticsTests(IsolatedAsyncioTestCase):
    async def test_download_includes_decisions_and_excludes_raw_configuration(self):
        trace = DebugTrace()
        trace.record('decision', 'private', data={'status':'completed'}, target=16, mode='hold')
        c = NS(entry=NS(data={'electrical_connection':'it_3'}), auto_control=True, charging_paused=False,
               data={'status':'completed','han_power_w':1847,'token':'SECRET'})
        site = NS(controllers={'private':c}, debug_trace=trace,
                  pending_reductions={}, _completed_limits={'private':16})
        hass = NS(data={'smart_load_manager':{'site':site}})
        with patch('smart_load_manager.diagnostics.async_get_integration',
                   new=AsyncMock(return_value=NS(version='0.1.1-beta.16'))):
            result = await async_get_config_entry_diagnostics(hass, NS(data={'password':'SECRET'}))
        text = json.dumps(result, allow_nan=False)
        self.assertNotIn('SECRET', text)
        self.assertNotIn('private', text)
        self.assertEqual(result['loads'][0]['completed_allowance_a'],16)
        self.assertEqual(result['trace']['events'][0]['target'],16)
        self.assertEqual(result['slm_version'],'0.1.1-beta.16')
