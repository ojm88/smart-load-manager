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
        entries=[NS(entry_id='primary',data={'charger_device':'dev_a','han_power_entity':'sensor.actual_han','tariff_used_entity':'sensor.provider_used','energy_estimate_entity':'sensor.provider_estimate'},title='First'),
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
                        return ('number.renamed_manual' if unique == 'other_manual_current_limit' else
                                f'{domain}.renamed_reason' if unique=='other_control_reason' else f'{domain}.{base}'+('_carport_ab1234' if entry is entries[1] else ''))
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
        self.assertIn('sensor.provider_used',text)
        self.assertIn('sensor.provider_estimate',text)
        self.assertNotIn('sensor.energy_estimate_this_hour',text)
        self.assertNotIn('sensor.energy_used_this_hour',text)
        self.assertNotIn('switch.slm_charging_auto_control', text)
        self.assertNotIn('Lading – automatikk', text)
        self.assertNotIn('SLM_HAN_POWER_SOURCE',text)
        self.assertNotIn('sensor.slm_min_current',text)
        self.assertNotIn('sensor.slm_max_current',text)
        self.assertIn('sensor.slm_line_voltage',text)
        self.assertEqual(text.count('name: Målegrunnlag'),1)
        wrappers = [row for card in parsed['cards'] for row in card.get('entities', [])
                    if isinstance(row, dict) and row.get('type') == 'conditional']
        self.assertEqual(len(wrappers), 4)
        self.assertIn('number.renamed_manual', [row['row']['entity'] for row in wrappers])
        for row in wrappers:
            self.assertTrue(all(c['entity'] == row['row']['entity'] for c in row['conditions']))

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
        from smart_load_manager.household_status import build_household_status
        data = dict(status='charging', auto_control=True, inputs_valid=True,
                    han_fresh=True, kw_per_amp=.23, max_current_a=16,
                    charger_power_w=2600, last_sent_current_a=12,
                    next_regulation_at=1000)
        for name in ['one.yaml', 'two.yaml']:
            card = yaml.safe_load((Path(__file__).parents[1] /
                'custom_components/smart_load_manager/dashboard' / name).read_text())
            template = env.from_string(card['cards'][0]['content'])
            for current, power in ((0, 0), (12, 200), (0, 200), (12, 800), (0, 800), (10, 2600)):
                with self.subTest(layout=name, recommended=current):
                    state, payload = build_household_status([
                        dict(id='a', name='Garasje', data=dict(data, recommended_current_a=current, charger_power_w=power)),
                    ], limit_kwh=10)
                    env.globals.update(states=lambda _: state,
                                       state_attr=lambda _, key: payload.get(key))
                    text = template.render()
                    self.assertIn(f'Anbefalt: **{current} A** · Satt: **12 A**', text)
                    self.assertIn('Regulering: **18:05**', text)
                    self.assertNotIn('Laderen beholder', text)
                    self.assertNotIn('For lite plass innenfor timegrensen', text)
                    self.assertNotIn('Avventer oppdaterte lademålinger', text)

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
            self.assertIn('Garasje · **Lader**', text)
            self.assertIn('Carport · **Pauset**', text)
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
                self.assertIn('Garasje · **Lader**', text)
                self.assertIn('Tesla · **', text)
                self.assertEqual(text.count('Effekt:'),1)
                self.assertEqual(text.count('Regulering:'),1)
                self.assertEqual(text.count('Anbefalt:'),1)
                if second_status == 'disconnected':
                    self.assertIn('Tesla · **Frakoblet**', text)
                    self.assertNotIn('Bilen er koblet til', text)

    async def test_markdown_shows_stable_draw_below_the_sent_limit(self):
        from pathlib import Path
        from jinja2 import Environment
        from smart_load_manager.household_status import build_household_status
        from smart_load_manager.power_reservation import PowerReservations

        for name, sent in (('one.yaml', 25), ('two.yaml', 20)):
            env = Environment()
            env.filters['timestamp_custom'] = lambda *args: '13:20'
            card = yaml.safe_load((Path(__file__).parents[1] /
                'custom_components/smart_load_manager/dashboard' / name).read_text())
            template = env.from_string(card['cards'][0]['content'])
            tracker = PowerReservations()
            data = dict(status='charging', auto_control=True, inputs_valid=True, han_fresh=True,
                        site_control_ready=True, kw_per_amp=.4, max_current_a=sent,
                        charger_power_w=6400, charger_current_a=16,
                        recommended_current_a=sent, last_sent_current_a=sent)
            for now in (0, 180):
                reserved = tracker.estimate('a', data, offered_a=sent, command_at=0, now=now)
                if reserved < sent * data['kw_per_amp']:
                    data['settled_offer_a'] = sent
                loads = [dict(id='a', name='Garasje', data=data)]
                if name == 'two.yaml':
                    loads.append(dict(id='b', name='Carport', data=dict(data, status='disconnected')))
                state, payload = build_household_status(loads, limit_kwh=10)
                env.globals.update(states=lambda _: state, state_attr=lambda _, k: payload.get(k))
                self.assertEqual(template.render().count('Målt ladestrøm: 16 A'), int(now == 180))

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

    async def test_short_status_and_stale_han_warning_render_once(self):
        from pathlib import Path
        from jinja2 import Environment
        from smart_load_manager.household_status import build_household_status
        for status, extra, label in [('awaiting_start', {'charging_paused':True}, 'Pauset'),
                ('awaiting_start', {'schedule_allowed':False, 'schedule_start_time':'22:00'}, 'Venter på starttid'),
                ('completed', {}, 'Fullført')]:
            data = dict(status=status, auto_control=True, inputs_valid=True, han_fresh=True,
                        electrical_ready=True, kw_per_amp=.23, max_current_a=16, recommended_current_a=6)
            data.update(extra)
            state, payload=build_household_status([dict(id='a',name='Tesla',data=data)],limit_kwh=10)
            payload.update(han_power_w=1000,han_fresh=False)
            env=Environment();env.globals.update(states=lambda _:state,state_attr=lambda _,k:payload.get(k))
            for name in ('one.yaml','two.yaml'):
                card=yaml.safe_load((Path(__file__).parents[1]/'custom_components/smart_load_manager/dashboard'/name).read_text())
                text=env.from_string(card['cards'][0]['content']).render()
                self.assertEqual(text.count('Tesla · **'+label+'**'),1)
                self.assertEqual(text.count('HAN-målingen er ikke oppdatert'),1)
                self.assertNotIn('Bilen er koblet til',text)
                self.assertNotIn('Regulering:',text)
                self.assertIn('1.0&nbsp;kW',text)

    async def test_card_renders_in_actual_home_assistant_template_engine(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from homeassistant.core import HomeAssistant
        from homeassistant.helpers.template import Template
        from smart_load_manager.household_status import build_household_status
        with TemporaryDirectory() as directory:
            hass=HomeAssistant(directory)
            try:
                _, payload=build_household_status([dict(id='a',name='Tesla',data=dict(
                    status='charging', auto_control=True, inputs_valid=True, han_fresh=True,
                    electrical_ready=True, kw_per_amp=.23, max_current_a=16,
                    charger_power_w=2300, recommended_current_a=10, last_sent_current_a=10))],limit_kwh=10)
                payload.update(han_power_w=99999, energy_used_kwh=999.9,
                               energy_estimate_kwh=1000,han_fresh=True)
                hass.states.async_set('sensor.slm_status','automatic',payload)
                for name in ('one.yaml','two.yaml'):
                    content=yaml.safe_load((Path(__file__).parents[1]/'custom_components/smart_load_manager/dashboard'/name).read_text())['cards'][0]['content']
                    rendered=Template(content,hass).async_render(parse_result=False)
                    self.assertIn('Tesla · **Lader** · Auto',rendered)
                    self.assertIn('Anbefalt: **10 A** · Satt: **10 A**',rendered)
                    self.assertNotIn('HAN-målingen er ikke oppdatert',rendered)
            finally:
                await hass.async_stop(force=True)

    async def test_pause_and_manual_rows_hide_unavailable_controls_independently(self):
        from pathlib import Path
        for name, count in [('one.yaml', 2), ('two.yaml', 4)]:
            parsed = yaml.safe_load((Path(__file__).parents[1]/
                'custom_components/smart_load_manager/dashboard'/name).read_text())
            rows = [r for c in parsed['cards'] for r in c.get('entities', [])
                    if isinstance(r, dict) and r.get('type') == 'conditional']
            self.assertEqual(len(rows), count)
            for wrapper in rows:
                entity = wrapper['row']['entity']
                self.assertTrue(entity.startswith(('switch.slm_charging_pause_', 'number.slm_manual_current_')))
                self.assertEqual(wrapper['conditions'], [
                    {'entity':entity, 'state_not':'unavailable'},
                    {'entity':entity, 'state_not':'unknown'}])
                # Availability is independent per entity, not per charger/card.
                for state in ('unavailable', 'unknown', 'on', 'off', '6', '12'):
                    visible = all(state != c['state_not'] for c in wrapper['conditions'])
                    self.assertEqual(visible, state not in ('unavailable', 'unknown'))

    async def test_rendered_waiting_sequence_keeps_cause_and_next_assessment(self):
        from pathlib import Path
        from jinja2 import Environment
        from smart_load_manager.household_status import build_household_status
        env=Environment()
        env.filters['timestamp_custom']=lambda value,*args: {1000:'23:09',1300:'23:14',1600:'23:19'}.get(value,'23:24')
        base=dict(status='awaiting_start',auto_control=True,inputs_valid=True,han_fresh=True,
                  site_control_ready=True,electrical_ready=True,schedule_allowed=True,
                  kw_per_amp=.718,max_current_a=16,control_minimum_current_a=6,
                  charger_power_w=0,charger_current_a=.06,recommended_current_a=0,
                  last_sent_current_a=0,next_regulation_at=1000)
        # Anonymous numeric reproduction of the uploaded 23:04–23:19 wait.
        sequence=[({},'forbruksgrense','23:09'),
                  ({'next_regulation_at':1300},'forbruksgrense','23:14'),
                  ({'recommended_current_a':6,'next_regulation_at':1600},'plass til 6 A','23:19'),
                  ({'recommended_current_a':6,'last_sent_current_a':6},'har satt 6 A','23:09'),
                  ({'auto_control':False,'schedule_enabled':True,'schedule_allowed':False,
                    'schedule_start_time':'21:30:00'},'Tidsstyring holder igjen ladingen til kl. 21:30.',None)]
        root=Path(__file__).parents[1]
        paths=[root/'custom_components/smart_load_manager/dashboard'/n for n in ('one.yaml','two.yaml')]
        paths += [root/'examples/lovelace'/n for n in ('charging_card.yaml','two_chargers_card.yaml')]
        for changes,reason,clock in sequence:
            for count in (1,2):
                state,payload=build_household_status([
                    dict(id='a',name='Garasje',data=dict(base,**changes))]+([
                    dict(id='b',name='Ute',data=dict(base,status='disconnected'))] if count==2 else []),limit_kwh=10)
                env.globals.update(states=lambda _:state,state_attr=lambda _,k:payload.get(k))
                for path in paths:
                    text=env.from_string(yaml.safe_load(path.read_text())['cards'][0]['content']).render()
                    self.assertIn(reason,text)
                    if clock is None:
                        self.assertIn('Venter på starttid', text)
                        self.assertIn('Manuell', text)
                        self.assertNotIn('Neste vurdering:', text)
                    else:
                        self.assertIn('Neste vurdering:',text)
                        self.assertIn(clock,text)
                    self.assertNotIn('Venter på at bilen starter',text)
                    self.assertNotIn('None',text)
                    if reason=='forbruksgrense':
                        self.assertIn('4.3 kW',text)
                        self.assertIn('Reduser annet forbruk',text)

    async def test_generated_graph_names_every_charger_with_consistent_current_labels(self):
        # Include YAML punctuation and the old placeholder words in real names.
        # The second pass must not rewrite an already inserted first name.
        names={'first':'Garasje: "ny lader"','second':'Ute – første lader'}
        for count in (1,2):
            with self.subTest(count=count):
                entries=[NS(entry_id=key,data={'charger_device':'dev_'+key,
                    'charger_name':'Saved '+key,'han_power_entity':'sensor.han',
                    'electrical_connection':'tn_3'},options={},title=key)
                    for key in list(names)[:count]]
                callbacks={}
                async def executor(func):return func()
                hass=NS(config_entries=NS(async_entries=lambda _:entries),
                    services=NS(has_service=lambda *args:False,
                        async_register=lambda domain,name,fn,**kw:callbacks.update(fn=fn)),
                    async_add_executor_job=executor)
                def entity_id(domain,platform,unique):
                    for entry in entries:
                        prefix=entry.entry_id+'_'
                        if unique.startswith(prefix):
                            key=unique[len(prefix):]
                            if key in ENTITY_OBJECT_IDS.get(domain,{}):
                                return f'{domain}.renamed_{entry.entry_id}_{key}'
                devices=NS(devices={'dev_'+key:NS(name='Easee',name_by_user=None) for key in names},
                    async_get_device=lambda *,identifiers:NS(name_by_user=names[next(iter(identifiers))[1]]))
                with patch('smart_load_manager.dashboard.er.async_get',return_value=NS(async_get_entity_id=entity_id)), patch('smart_load_manager.dashboard.dr.async_get',return_value=devices):
                    await async_register_dashboard_service(hass)
                    response=await callbacks['fn'](None)
                card=yaml.safe_load(response['yaml'])
                graph=next(c for c in card['cards'] if c['type']=='history-graph')
                actual={row['entity']:row['name'] for row in graph['entities']}
                for entry in entries:
                    for key,label in (('recommended_current','Anbefalt ladestrøm'),('charger_current','Målt ladestrøm')):
                        self.assertEqual(actual[f'sensor.renamed_{entry.entry_id}_{key}'],f'{label} – {names[entry.entry_id]}')
                self.assertNotIn('Anbefalt strøm',response['yaml'])
                self.assertNotIn('Strøm til bilen',response['yaml'])
                self.assertNotIn('CHARGER_SUFFIX',response['yaml'])
