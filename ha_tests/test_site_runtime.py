"""Exercise command ordering and site coordination in HA's Python runtime."""
from types import SimpleNamespace as NS
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock
from datetime import datetime, UTC
from smart_load_manager.site import SiteController


class SiteRuntimeTests(IsolatedAsyncioTestCase):
    def setup_site(self):
        self.now = datetime.now(UTC)
        self.states = {}
        self.entries = [NS(entry_id='a', data={}, options={}), NS(entry_id='b', data={}, options={})]
        hass = NS(states=NS(get=lambda key: self.states.get(key)),
                  config_entries=NS(async_entries=lambda _: self.entries))
        site = SiteController(hass)
        self.commands = []
        for key in ['a', 'b']:
            c = NS(entry=NS(entry_id=key), auto_control=True, charging_paused=False,
                   last_commanded_current=10, _last_command_at=0,
                   easee=NS(current=key+'_current', power=key+'_power'),
                   async_set_updated_data=lambda data: None,
                   async_set_update_error=lambda error: None)
            async def send(value, c=c, key=key):
                self.commands.append((key, value))
                c.last_commanded_current = value
                c._last_command_at = self.now.timestamp()
            c._async_send_current = send
            site.controllers[key] = c
        return site

    async def test_no_increase_until_reduction_confirmed_by_new_measurement(self):
        site = self.setup_site()
        sample = {key: {'charger_current_a': 10, 'charger_power_w': 2300, 'kw_per_amp': .23} for key in ['a','b']}
        await site._apply({'a': 6, 'b': 14}, sample)
        self.assertEqual(self.commands, [('a', 6)])
        # Low readings with an old timestamp are not a confirmation.
        from datetime import timedelta
        for suffix in ['current','power']:
            self.states['a_'+suffix] = NS(last_updated=self.now-timedelta(seconds=1))
        sample['a'].update(charger_current_a=6, charger_power_w=1380)
        await site._apply({'a':6, 'b':14}, sample)
        self.assertEqual(self.commands, [('a',6)])
        for suffix in ['current','power']:
            self.states['a_'+suffix] = NS(last_updated=self.now+timedelta(seconds=1))
        await site._apply({'a':6, 'b':14}, sample)
        self.assertEqual(self.commands, [('a',6),('b',14)])

    async def test_new_takeover_first_establishes_zero(self):
        site = self.setup_site()
        for c in site.controllers.values(): c.last_commanded_current = None
        sample = {key: {'charger_current_a': 0, 'charger_power_w':0, 'kw_per_amp':.23} for key in ['a','b']}
        await site._apply({'a':8, 'b':8}, sample)
        self.assertEqual(self.commands, [('a',0),('b',0)])

    async def test_lower_budget_can_reduce_further_while_waiting(self):
        site = self.setup_site()
        samples = {key: {'charger_current_a':10, 'charger_power_w':2300, 'kw_per_amp':.23} for key in ['a','b']}
        await site._apply({'a':6,'b':14}, samples)
        await site._apply({'a':0,'b':0}, samples)
        self.assertEqual(self.commands, [('a',6),('a',0),('b',0)])

    async def test_missing_peer_during_startup_does_not_block_entity_setup(self):
        site = self.setup_site()
        site.controllers.pop('b')
        c = site.controllers['a']
        c._async_sample = AsyncMock(return_value={})
        result = await site.refresh(c)
        self.assertEqual(result['recommended_current_a'],0)
        self.assertEqual(self.commands,[('a',0)])

    async def test_bad_peer_measurement_stops_all_without_positive_writes(self):
        site = self.setup_site()
        for c in site.controllers.values():
            c._async_sample = AsyncMock(side_effect=ValueError('bad reading'))
        with self.assertRaises(Exception):
            await site.refresh(site.controllers['a'])
        self.assertEqual(self.commands,[('a',0),('b',0)])

    async def test_refresh_allocates_once_for_both_and_finished_releases_turn(self):
        site = self.setup_site()
        self.entries[0].options = {'consumption_limit_kwh':10, 'allocation_mode':'both'}
        def sample(key):
            return dict(inputs_valid=True, han_fresh=True, energy_used_kwh=5,
                        safety_margin_kwh=.3, minutes_left=30, han_power_w=6000,
                        charger_power_w=0, kw_per_amp=.23, schedule_allowed=True,
                        status='awaiting_start', control_minimum_current_a=6,
                        max_current_a=16, electrical={'effective_phases':1,'phase_neutral_voltage_v':230},
                        charger_current_a=0, control_reason='')
        for key,c in site.controllers.items():
            c.last_commanded_current=0
            c._async_sample=AsyncMock(return_value=sample(key))
            self.states[key+'_power']=NS(state='0',last_updated=self.now)
        result=await site.refresh(site.controllers['a'])
        self.assertEqual(result['recommended_current_a'],7)
        self.assertEqual(self.commands,[('a',7),('b',7)])
        # Now only b wants energy: a has completed, and b may take the capacity.
        self.entries[0].options['allocation_mode']='one_at_a_time'
        site.controllers['a']._async_sample.return_value['status']='completed'
        site.controllers['a'].last_commanded_current=0
        site.controllers['b'].last_commanded_current=0
        self.commands.clear()
        result=await site.refresh(site.controllers['b'])
        self.assertEqual(result['recommended_current_a'],14)
        self.assertEqual(self.commands,[('b',14)])
