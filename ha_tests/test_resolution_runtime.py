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

class OptionsTests(IsolatedAsyncioTestCase):
    async def test_add_charger_keeps_validation_detail_and_selection(self):
        flow=ChargerOptionsFlow()
        nested=NS(async_init=AsyncMock(return_value={
            'type':'form','flow_id':'nested',
            'description_placeholders':{'validation_error':'Enable sensor.garage_voltage'}}),
            async_abort=lambda fid: aborted.append(fid))
        aborted=[]
        flow.hass=NS(config_entries=NS(async_entries=lambda _: [NS()],flow=nested))
        result=await flow.async_step_init({'charger_device':'garage'})
        self.assertEqual(result['description_placeholders']['validation_error'],
                         'Enable sensor.garage_voltage')
        self.assertEqual(aborted,['nested'])
        self.assertEqual(result['errors'],{'base':'invalid_setup'})

class HouseholdOptionsTests(IsolatedAsyncioTestCase):
    def setup_flow(self):
        entries=[NS(entry_id='a',data={'charger_device':'first','han_power_entity':'sensor.old',
                 'tariff_used_entity':'sensor.old_used','safety_margin_kwh':.3},
                 options={'consumption_limit_kwh':10,'priority_charger':'b'}),
                 NS(entry_id='b',data={'charger_device':'second','entity_suffix':'garage_abc',
                 'han_power_entity':'sensor.old','tariff_used_entity':'sensor.old_used',
                 'safety_margin_kwh':.3},options={'schedule_start_time':'02:00:00'})]
        states={'sensor.new_han':NS(state='1200',attributes={'unit_of_measurement':'W'}),
                'sensor.new_used':NS(state='2.5',attributes={'unit_of_measurement':'kWh'})}
        def update(entry, **changes):
            for key,value in changes.items():setattr(entry,key,value)
        flow=ChargerOptionsFlow()
        flow.handler='b'
        flow.hass=NS(config_entries=NS(async_entries=lambda _:entries,
              async_get_known_entry=lambda key:next(e for e in entries if e.entry_id==key),
              async_update_entry=update),states=NS(get=states.get))
        return flow,entries,states

    async def test_two_chargers_still_offer_household_configuration(self):
        flow,entries,states=self.setup_flow()
        result=await flow.async_step_init()
        self.assertEqual(result['type'],'menu')
        self.assertIn('household',result['menu_options'])
        self.assertNotIn('add_charger',result['menu_options'])
        entries.pop()
        result=await flow.async_step_init()
        self.assertIn('add_charger',result['menu_options'])

    async def test_edit_from_second_updates_both_without_losing_charger_settings(self):
        flow,entries,states=self.setup_flow()
        value={'han_power_entity':'sensor.new_han','tariff_used_entity':'sensor.new_used',
               'safety_margin_kwh':.5}
        result=await flow.async_step_household(value)
        self.assertEqual(result['type'],'create_entry')
        for entry in entries:
            for key,val in value.items():self.assertEqual(entry.data[key],val)
        self.assertEqual(entries[0].data['charger_device'],'first')
        self.assertEqual(entries[1].data['entity_suffix'],'garage_abc')
        self.assertEqual(entries[0].options['consumption_limit_kwh'],10)
        self.assertEqual(entries[0].options['priority_charger'],'b')
        self.assertEqual(result['data'],{'schedule_start_time':'02:00:00'})

    async def test_invalid_source_does_not_partially_change_the_site(self):
        flow,entries,states=self.setup_flow()
        original=[dict(e.data) for e in entries]
        for bad in ['unavailable','nan','-1']:
            states['sensor.new_used'].state=bad
            result=await flow.async_step_household({'han_power_entity':'sensor.new_han',
                'tariff_used_entity':'sensor.new_used','safety_margin_kwh':.5})
            self.assertEqual(result['type'],'form')
            self.assertTrue(result['errors'])
            self.assertEqual([e.data for e in entries],original)
