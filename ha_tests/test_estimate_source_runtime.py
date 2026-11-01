"""Hourly estimates may come from another provider without controlling charging."""
from types import SimpleNamespace as NS
from unittest import IsolatedAsyncioTestCase, TestCase
from smart_load_manager.config_flow import _validate_meter_sources, _household_schema
from smart_load_manager.coordinator import _hourly_estimate
from smart_load_manager.const import CONF_ESTIMATE_ENTITY


class EstimateSourceTests(TestCase):
    def test_setup_accepts_provider_kwh_but_not_power_or_invalid_estimate(self):
        states={'sensor.han':NS(state='1000',attributes={'unit_of_measurement':'W'}),
                'sensor.used':NS(state='1.2',attributes={'unit_of_measurement':'kWh'}),
                'sensor.estimate':NS(state='2.3',attributes={'unit_of_measurement':'kWh'})}
        hass=NS(states=NS(get=states.get))
        values={'han_power_entity':'sensor.han','tariff_used_entity':'sensor.used'}
        _validate_meter_sources(hass,values)  # Estimate remains optional.
        values[CONF_ESTIMATE_ENTITY]='sensor.estimate'
        _validate_meter_sources(hass,values)
        for state,unit in [('2.3','W'),('unknown','kWh'),('-1','kWh'),('nan','kWh')]:
            states['sensor.estimate']=NS(state=state,attributes={'unit_of_measurement':unit})
            with self.assertRaises(ValueError): _validate_meter_sources(hass,values)
        self.assertIn(CONF_ESTIMATE_ENTITY, [str(k) for k in _household_schema().schema])

    def test_selected_estimate_does_not_silently_use_another_provider(self):
        states={'sensor.provider_estimate':NS(state='2.3',attributes={'unit_of_measurement':'kWh'}),
                'sensor.energy_estimate_this_hour':NS(state='99',attributes={'unit_of_measurement':'kWh'})}
        hass=NS(states=NS(get=states.get))
        entry=NS(data={CONF_ESTIMATE_ENTITY:'sensor.provider_estimate'})
        self.assertEqual(_hourly_estimate(hass,entry),2.3)
        states['sensor.provider_estimate'].state='unavailable'
        self.assertIsNone(_hourly_estimate(hass,entry))
        self.assertEqual(_hourly_estimate(hass,NS(data={})),99)
