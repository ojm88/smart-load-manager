"""Regression for disabled Easee voltage and hidden options-flow errors."""
from types import SimpleNamespace as NS
from unittest import TestCase, IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock
from smart_load_manager.entity_resolution import resolve_easee_entities
from smart_load_manager.config_flow import ChargerOptionsFlow

class ResolutionTests(TestCase):
    def test_disabled_voltage_explains_actual_sensor_to_enable(self):
        entries = [NS(entity_id='sensor.garage_'+k, domain='sensor', platform='easee',
                      translation_key=k, disabled_by='integration' if k=='voltage' else None)
                   for k in ['status','current','voltage']]
        states = {'sensor.garage_status':NS(attributes={'state_outputPhase':30}),
                  'sensor.garage_current':NS(attributes={'state_inCurrentT3':0})}
        hass=NS(config=NS(language='nb'),states=NS(get=states.get))
        with patch('smart_load_manager.entity_resolution.er.async_get',return_value=NS()), patch(
                'smart_load_manager.entity_resolution.er.async_entries_for_device',return_value=entries):
            with self.assertRaisesRegex(ValueError,'Aktiver Easee-sensoren sensor.garage_voltage'):
                resolve_easee_entities(hass,'garage')
            states['sensor.garage_voltage']=NS(attributes={'state_inVoltageT2T3':230})
            self.assertEqual(resolve_easee_entities(hass,'garage').voltage,'sensor.garage_voltage')
