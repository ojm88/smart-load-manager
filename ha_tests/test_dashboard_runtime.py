"""Ready-to-paste dashboard generation uses registry IDs and safe charger labels."""
from types import SimpleNamespace as NS
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
import asyncio
import yaml
from smart_load_manager.dashboard import async_register_dashboard_service
from smart_load_manager.entity_ids import ENTITY_OBJECT_IDS


class DashboardRuntimeTests(IsolatedAsyncioTestCase):
    async def test_two_charger_card_uses_real_ids_in_markdown_and_controls(self):
        entries=[NS(entry_id='primary',data={'charger_device':'dev_a','han_power_entity':'sensor.actual_han'},title='First'),
                 NS(entry_id='other',data={'charger_device':'dev_b','entity_suffix':'carport_ab1234'},title='Second')]
        callbacks={}
        async def executor(func): return func()
        hass=NS(config_entries=NS(async_entries=lambda _:entries),
                services=NS(has_service=lambda *args:False,
                            async_register=lambda domain,name,fn,**kw:callbacks.update(fn=fn)),
                async_add_executor_job=executor)
        def entity_id(domain,platform,unique):
            for entry in entries:
                prefix=entry.entry_id+'_'
                if unique.startswith(prefix):
                    key=unique[len(prefix):]
                    if entry is entries[1] and key in {'consumption_limit','allocation_mode','priority_charger'}: return None
                    if key in ENTITY_OBJECT_IDS.get(domain,{}):
                        base=ENTITY_OBJECT_IDS[domain][key]
                        # Simulate a user-renamed sensor, not just its proposed ID.
                        return f'{domain}.renamed_reason' if unique=='other_control_reason' else f'{domain}.{base}'+('_carport_ab1234' if entry is entries[1] else '')
        devices=NS(devices={'dev_a':NS(name_by_user='Garasje',name='a'),
                            'dev_b':NS(name_by_user='Carport: "Vest"',name='b')})
        with patch('smart_load_manager.dashboard.er.async_get',return_value=NS(async_get_entity_id=entity_id)), patch('smart_load_manager.dashboard.dr.async_get',return_value=devices):
            await async_register_dashboard_service(hass)
            response=await callbacks['fn'](None)
        text=response['yaml']
        parsed=yaml.safe_load(text)
        self.assertEqual(parsed['type'],'vertical-stack')
        self.assertNotIn('CHARGER_SUFFIX',text)
        self.assertIn('sensor.slm_status',text)
        self.assertNotIn('sensor.renamed_reason',text)
        self.assertIn('select.slm_charging_mode',text)
        self.assertIn('sensor.actual_han',text)
        self.assertNotIn('SLM_HAN_POWER_SOURCE',text)
        self.assertNotIn('sensor.slm_min_current',text)
        self.assertNotIn('sensor.slm_max_current',text)
        self.assertIn('sensor.slm_line_voltage',text)
        self.assertEqual(text.count('name: Målegrunnlag'),1)
        markdown=parsed['cards'][0]['content']
        self.assertNotIn('sensor.slm_charger_status',markdown)
        self.assertNotIn('sensor.slm_control_reason',markdown)
        self.assertNotIn('select.slm_charging_mode',markdown)
        self.assertIn('Carport: "Vest"',text)

    async def test_markdown_renders_from_only_the_household_sensor(self):
        from pathlib import Path
        from jinja2 import Environment
        from smart_load_manager.household_status import build_household_status
        _, payload=build_household_status([{'id':'a','name':'Garasje','data':{
            'status':'awaiting_start','auto_control':True,'han_fresh':True,'inputs_valid':True,
            'site_control_ready':True,'recommended_current_a':0,'kw_per_amp':.23,
            'max_current_a':16,'charger_power_w':0}}],limit_kwh=10)
        env=Environment()
        used=set()
        def attr(entity,key):
            used.add(entity)
            return payload.get(key)
        env.globals.update(states=lambda entity:'waiting',state_attr=attr)
        for file in ['one.yaml','two.yaml']:
            card=yaml.safe_load((Path(__file__).parents[1]/'custom_components/smart_load_manager/dashboard'/file).read_text())
            text=env.from_string(card['cards'][0]['content']).render()
            self.assertIn('Garasje',text)
            self.assertIn('forbruksgrense',text)
            self.assertNotIn('None',text)
        self.assertEqual(used,{'sensor.slm_status'})

    async def test_compact_meter_line_renders_values_and_missing_data(self):
        from pathlib import Path
        from jinja2 import Environment
        env = Environment()
        payload = dict(han_power_w=17339, energy_used_kwh=7.87, energy_estimate_kwh=9.49)
        env.globals.update(states=lambda entity: 'waiting',
                           state_attr=lambda entity, key: payload.get(key))
        for name in ['one.yaml', 'two.yaml']:
            card = yaml.safe_load((Path(__file__).parents[1] /
                'custom_components/smart_load_manager/dashboard' / name).read_text())
            template = env.from_string(card['cards'][0]['content'])
            text = template.render()
            for value in ['17.3&nbsp;kW', '7.9&nbsp;kWh', '9.5&nbsp;kWh']:
                self.assertIn(value, text)
            payload.clear()
            text = template.render()
            self.assertIn('—', text)
            self.assertNotIn('None', text)
            payload.update(han_power_w=17339, energy_used_kwh=7.87, energy_estimate_kwh=9.49)

    async def test_markdown_distinguishes_live_recommendation_from_sent_limit(self):
        from pathlib import Path
        from jinja2 import Environment
        env = Environment()
        env.filters['timestamp_custom'] = lambda value, fmt, local: '18:05'
        row = dict(name='Garasje', status='charging', explanation='Lading', power_w=2300,
                   automatic_control=True, recommended_current_a=8,
                   last_sent_current_a=10, next_regulation_at=1000)
        payload = dict(controlled_loads=[row], summary='Lading', consumption_limit_kwh=10)
        env.globals.update(states=lambda entity: 'automatic',
                           state_attr=lambda entity, key: payload.get(key))
        for name in ['one.yaml', 'two.yaml']:
            card = yaml.safe_load((Path(__file__).parents[1] /
                'custom_components/smart_load_manager/dashboard' / name).read_text())
            text = env.from_string(card['cards'][0]['content']).render()
            self.assertIn('Anbefalt nå: **8 A**', text)
            self.assertIn('Sist satt: **10 A**', text)
            self.assertIn('18:05', text)

    async def test_markdown_shows_name_and_independent_status_for_both_chargers(self):
        from pathlib import Path
        from jinja2 import Environment
        from smart_load_manager.household_status import build_household_status
        data = dict(status='charging', auto_control=True, inputs_valid=True, han_fresh=True,
                    kw_per_amp=.23, max_current_a=16, recommended_current_a=11)
        _, payload = build_household_status([
            dict(id='a', name='Garasje', data=data),
            dict(id='b', name='Carport', data=dict(data, status='awaiting_start', charging_paused=True)),
        ], limit_kwh=10)
        env = Environment()
        env.globals.update(states=lambda entity: 'mixed', state_attr=lambda entity, key: payload.get(key))
        for name in ('one.yaml', 'two.yaml'):
            card = yaml.safe_load((Path(__file__).parents[1] /
                'custom_components/smart_load_manager/dashboard' / name).read_text())
            text = env.from_string(card['cards'][0]['content']).render()
            self.assertIn('Garasje – Lader', text)
            self.assertIn('Carport – Pauset', text)
            self.assertIn('Slå av ladepause', text)

    async def test_charger_name_prefers_slm_user_name_to_generic_easee_name(self):
        from smart_load_manager.device_info import charger_display_name
        entry = NS(entry_id='a', title='EASEE', data={'charger_device':'source', 'charger_name':'EASEE'})
        source = NS(name='EASEE', name_by_user=None)
        managed = NS(name='EASEE', name_by_user='Tesla')
        registry = NS(async_get=lambda identity: source,
                      async_get_device=lambda **kw: managed)
        self.assertEqual(charger_display_name(registry, entry), 'Tesla')
        managed.name_by_user = None
        source.name_by_user = 'Garasje'
        self.assertEqual(charger_display_name(registry, entry), 'Garasje')
        source.name_by_user = None
        self.assertEqual(charger_display_name(registry, entry), 'EASEE')

    async def test_disconnected_cards_hide_charging_details_and_redundant_loads(self):
        from pathlib import Path
        from jinja2 import Environment
        from smart_load_manager.household_status import build_household_status
        env = Environment()
        env.filters['timestamp_custom'] = lambda *args: '13:20'
        raw = dict(status='disconnected', auto_control=True, inputs_valid=True,
                   han_fresh=True, charger_power_w=0, recommended_current_a=0,
                   last_sent_current_a=0, next_regulation_at=1000)
        for count in (1, 2):
            state, payload = build_household_status([
                dict(id=str(i), name='Charger'+str(i), data=raw) for i in range(count)
            ], limit_kwh=10)
            payload.update(han_power_w=17339, energy_used_kwh=99.99, energy_estimate_kwh=123.45)
            env.globals.update(states=lambda _: state, state_attr=lambda _,k: payload.get(k))
            for name in ('one.yaml', 'two.yaml'):
                card = yaml.safe_load((Path(__file__).parents[1] /
                    'custom_components/smart_load_manager/dashboard' / name).read_text())
                self.assertNotIn('title', card['cards'][0])
                text = env.from_string(card['cards'][0]['content']).render()
                self.assertIn('Ingen bil tilkoblet' if count == 1 else 'Ingen biler tilkoblet', text)
                for hidden in ('Ladeeffekt:', 'Anbefalt nå:', 'Sist satt:', 'Neste ordinære', 'Charger0', 'Førsteprioritet:'):
                    self.assertNotIn(hidden, text)
                self.assertIn('17.3&nbsp;kW', text)
                self.assertIn('123&nbsp;kWh', text)

    async def test_only_charging_rows_show_current_power_and_next_regulation(self):
        from pathlib import Path
        from jinja2 import Environment
        from smart_load_manager.household_status import build_household_status
        env = Environment()
        env.filters['timestamp_custom'] = lambda *args: '13:20'
        data = dict(status='charging', auto_control=True, inputs_valid=True, han_fresh=True,
                    kw_per_amp=.23, max_current_a=16, charger_power_w=2530,
                    recommended_current_a=11, last_sent_current_a=11, next_regulation_at=1000)
        for second_status in ('disconnected', 'completed', 'awaiting_start'):
            state, payload = build_household_status([
                dict(id='a', name='Garasje', data=data),
                dict(id='b', name='Tesla', data=dict(data, status=second_status, charger_power_w=0)),
            ], limit_kwh=10)
            env.globals.update(states=lambda _: state, state_attr=lambda _,k:payload.get(k))
            for name in ('one.yaml','two.yaml'):
                card=yaml.safe_load((Path(__file__).parents[1]/
                    'custom_components/smart_load_manager/dashboard'/name).read_text())
                text=env.from_string(card['cards'][0]['content']).render()
                self.assertIn('Garasje – Lader', text)
                self.assertIn('Tesla –', text)
                self.assertEqual(text.count('Ladeeffekt:'),1)
                self.assertEqual(text.count('Neste ordinære regulering:'),1)
                self.assertEqual(text.count('Anbefalt nå:'),1)
                if second_status == 'disconnected':
                    self.assertIn('Bil tilkoblet: Garasje. Frakoblet: Tesla.', text)
                    self.assertIn('1 av 2 biler tilkoblet', text)

    async def test_high_meter_values_stay_in_three_separate_value_cells(self):
        from pathlib import Path
        from jinja2 import Environment
        from html.parser import HTMLParser
        class Cells(HTMLParser):
            def __init__(self):
                super().__init__(); self.cells=[]; self.active=False
            def handle_starttag(self,tag,attrs):
                if tag=='td': self.active=True; self.cells.append('')
            def handle_endtag(self,tag):
                if tag=='td': self.active=False
            def handle_data(self,value):
                if self.active: self.cells[-1]+=value
        for values in ((17339,7.87,9.49),(99999,999.99,1234.56),(999999,9999,10000)):
            payload=dict(han_power_w=values[0],energy_used_kwh=values[1],energy_estimate_kwh=values[2])
            env=Environment();env.globals.update(states=lambda _: 'unknown',state_attr=lambda _,k:payload.get(k))
            for name in ('one.yaml','two.yaml'):
                card=yaml.safe_load((Path(__file__).parents[1]/
                    'custom_components/smart_load_manager/dashboard'/name).read_text())
                text=env.from_string(card['cards'][0]['content']).render()
                parser=Cells();parser.feed(text)
                self.assertEqual(len(parser.cells),3)
                self.assertTrue(all(len(cell.strip())<=9 for cell in parser.cells),parser.cells)
                self.assertNotIn('None',text)
