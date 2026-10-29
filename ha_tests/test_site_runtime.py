"""Exercise command ordering and site coordination in HA's Python runtime."""
from types import SimpleNamespace as NS
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch
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
        self.assertEqual(self.commands,[('b',14)])  # Completion releases the peer's turn immediately.
        deadline = datetime.fromtimestamp(site.cadence.next_regular_at, UTC)
        with patch('smart_load_manager.site.dt_util.now', return_value=deadline):
            await site.refresh(site.controllers['b'])
        self.assertEqual(self.commands,[('b',14)])

    def setup_missing_power(self, automatic=True):
        from datetime import timedelta
        site = self.setup_site()
        self.entries[0].options = {'consumption_limit_kwh':10, 'allocation_mode':'both'}
        self.delivered = {}
        for key, c in site.controllers.items():
            c.auto_control = automatic
            c.entry.title = 'Garage' if key == 'b' else 'Driveway'
            c.async_set_updated_data = lambda data, key=key: self.delivered.update({key:data})
            c._async_sample = AsyncMock(return_value=dict(
                inputs_valid=True, han_fresh=True, energy_used_kwh=5,
                safety_margin_kwh=.3, minutes_left=30, han_power_w=6000,
                charger_power_w=0, kw_per_amp=.23, schedule_allowed=True,
                status='awaiting_start', control_minimum_current_a=6,
                max_current_a=16, electrical={'effective_phases':1,'phase_neutral_voltage_v':230},
                charger_current_a=0, control_reason='normal'))
            stamp = self.now - timedelta(seconds=180) if key == 'b' else self.now
            self.states[key+'_power'] = NS(state='unavailable' if key == 'b' else '0',last_updated=stamp,last_reported=stamp)
        return site

    async def test_missing_power_preserves_samples_and_names_the_source(self):
        site = self.setup_missing_power()
        data = await site.refresh(site.controllers['a'])
        self.assertFalse(data['site_control_ready'])
        self.assertEqual(data['han_power_w'],6000)
        self.assertEqual(data['recommended_current_a'],0)
        self.assertIn('Garage',data['control_reason'])
        self.assertIn('b_power',data['control_reason'])
        self.assertFalse(self.delivered['b']['site_control_ready'])
        self.assertEqual(self.commands,[('a',0),('b',0)])
        pending = dict(site.pending_reductions)
        await site.refresh(site.controllers['a'])
        self.assertEqual(site.pending_reductions,pending)
        self.assertEqual(len(self.commands),2)

    async def test_missing_power_with_auto_off_does_not_write_chargers(self):
        site = self.setup_missing_power(automatic=False)
        data = await site.refresh(site.controllers['a'])
        self.assertFalse(data['site_control_ready'])
        self.assertEqual(self.commands,[])

    async def test_wait_recovers_with_fresh_power_and_acknowledged_zero(self):
        from datetime import timedelta
        site = self.setup_missing_power()
        await site.refresh(site.controllers['a'])
        self.commands.clear()
        for key in ['a','b']:
            stamp = self.now + timedelta(seconds=1)
            self.states[key+'_power'] = NS(state='0',last_updated=stamp,last_reported=stamp)
            self.states[key+'_current'] = NS(last_updated=stamp,last_reported=stamp)
        data = await site.refresh(site.controllers['a'])
        self.assertTrue(data['site_control_ready'])
        self.assertEqual(data['recommended_current_a'],7)
        self.assertEqual(self.commands,[('a',7),('b',7)])

    async def test_failed_stop_attempts_both_and_does_not_claim_ready(self):
        site = self.setup_missing_power()
        site.controllers['a']._async_send_current = AsyncMock(side_effect=RuntimeError('offline'))
        from homeassistant.helpers.update_coordinator import UpdateFailed
        with self.assertRaisesRegex(UpdateFailed,'offline'):
            await site.refresh(site.controllers['a'])
        self.assertEqual(self.commands,[('b',0)])

    async def test_unchanged_available_power_does_not_expire(self):
        from datetime import timedelta
        site = self.setup_missing_power()
        old = self.now - timedelta(days=2)
        for key, c in site.controllers.items():
            c.last_commanded_current = 0
            self.states[key+'_power'] = NS(state='0',last_updated=old,last_reported=old)
        data = await site.refresh(site.controllers['a'])
        self.assertTrue(data['site_control_ready'])
        self.assertEqual(data['recommended_current_a'],7)
        self.assertEqual(self.commands,[('a',7),('b',7)])

    def setup_regulation(self, *, single=False):
        site = self.setup_missing_power()
        if single:
            site.controllers.pop('b')
            self.entries.pop()
        for key, c in site.controllers.items():
            c.last_commanded_current = 10
            d = c._async_sample.return_value
            d.update(charger_power_w=2300, charger_current_a=10,
                     energy_used_kwh=5, seconds_to_hour=1800)
            self.states[key+'_power'] = NS(state='2300', last_updated=self.now)
            self.states[key+'_current'] = NS(state='10', last_updated=self.now)
        site.cadence.record_regular(self.now.timestamp())
        return site

    async def refresh_at(self, site, seconds):
        from datetime import timedelta
        with patch('smart_load_manager.site.dt_util.now', return_value=self.now+timedelta(seconds=seconds)):
            return await site.refresh(next(iter(site.controllers.values())))

    async def test_live_recommendations_do_not_change_limits_between_five_minute_ticks(self):
        for single in (True, False):
            site = self.setup_regulation(single=single)
            for seconds in (1, 10, 60, 299):
                data = await self.refresh_at(site, seconds)
                self.assertGreater(data['recommended_current_a'], 10)
                self.assertEqual(data['last_sent_current_a'], 10)
                self.assertEqual(self.commands, [])
            await self.refresh_at(site, 300)
            self.assertTrue(self.commands)
            self.assertTrue(all(value > 10 for _, value in self.commands))
            sent = list(self.commands)
            await self.refresh_at(site, 301)
            self.assertEqual(self.commands, sent)

    async def test_persistent_forecast_risk_reduces_then_blocks_immediate_rebound(self):
        from datetime import timedelta
        for single in (True, False):
            site = self.setup_regulation(single=single)
            for c in site.controllers.values():
                c._async_sample.return_value['energy_used_kwh'] = 9.5
            await self.refresh_at(site, 1)
            await self.refresh_at(site, 30)
            self.assertEqual(self.commands, [])
            await self.refresh_at(site, 31)
            self.assertEqual(self.commands, [(key, 0) for key in site.controllers])
            self.commands.clear()
            for key, c in site.controllers.items():
                c._async_sample.return_value.update(energy_used_kwh=5, han_power_w=1000,
                                                    charger_current_a=0, charger_power_w=0)
                for suffix in ('power', 'current'):
                    self.states[key+'_'+suffix] = NS(state='0', last_updated=self.now+timedelta(seconds=32))
            await self.refresh_at(site, 32)
            await self.refresh_at(site, 300)
            self.assertEqual(self.commands, [])
            self.assertFalse(site.pending_reductions)
            await self.refresh_at(site, 331)
            self.assertTrue(self.commands)

    async def test_brief_risk_does_not_reduce_and_urgent_risk_does(self):
        site = self.setup_regulation()
        for c in site.controllers.values(): c._async_sample.return_value['energy_used_kwh'] = 9.5
        await self.refresh_at(site, 1)
        for c in site.controllers.values(): c._async_sample.return_value['energy_used_kwh'] = 5
        await self.refresh_at(site, 20)
        self.assertEqual(self.commands, [])
        self.assertIsNone(site.cadence.risk_since)
        for c in site.controllers.values(): c._async_sample.return_value['energy_used_kwh'] = 9.69
        await self.refresh_at(site, 21)
        self.assertEqual(self.commands, [('a', 0), ('b', 0)])

    async def test_lower_physical_current_limit_does_not_wait_five_minutes(self):
        site = self.setup_regulation()
        for c in site.controllers.values(): c._async_sample.return_value['max_current_a'] = 8
        await self.refresh_at(site, 1)
        self.assertEqual(self.commands, [('a', 8), ('b', 8)])

    async def test_unavailable_sources_stop_immediately_between_ticks(self):
        site = self.setup_regulation()
        site.controllers['b']._async_sample.return_value['inputs_valid'] = False
        await self.refresh_at(site, 1)
        self.assertEqual(self.commands, [('a', 0), ('b', 0)])

    async def test_single_charger_start_retains_direct_start_with_valid_measurements(self):
        site = self.setup_regulation(single=True)
        site.cadence.next_regular_at = None
        site.controllers['a'].last_commanded_current = None
        await self.refresh_at(site, 0)
        self.assertEqual(self.commands, [('a', 16)])
        self.assertEqual(site.controllers['a'].last_commanded_current, 16)
        self.assertFalse(site.pending_reductions)

    async def unplug(self, site, key='a', seconds=1):
        c = site.controllers[key]
        c._async_sample.return_value.update(status='disconnected', charger_current_a=0,
                                            charger_power_w=0)
        await self.refresh_at(site, seconds)
        self.commands.clear()

    async def test_plug_in_starts_before_old_deadline_and_restarts_five_minutes(self):
        site = self.setup_regulation(single=True)
        await self.unplug(site)
        c = site.controllers['a']
        c._async_sample.return_value['status'] = 'awaiting_start'
        data = await self.refresh_at(site, 10)
        self.assertEqual(self.commands, [('a', 14)])
        self.assertEqual(site.cadence.next_regular_at, self.now.timestamp()+310)
        self.assertIn('straks', data['regulation_reason'])
        # Normal Easee startup transitions and meter changes are not new starts.
        self.commands.clear()
        c._async_sample.return_value.update(status='charging', max_current_a=20, han_power_w=1000)
        await self.refresh_at(site, 11)
        await self.refresh_at(site, 309)
        self.assertEqual(self.commands, [])
        await self.refresh_at(site, 310)
        self.assertEqual(self.commands, [('a', 20)])

    async def test_plug_in_waits_for_authorization_then_starts_without_timer_wait(self):
        site = self.setup_regulation(single=True)
        await self.unplug(site)
        d = site.controllers['a']._async_sample.return_value
        for status in ('authenticating', 'awaiting_authorization', 'offline', 'future_status'):
            d['status'] = status
            await self.refresh_at(site, 10)
            self.assertEqual(self.commands, [])
        d['status'] = 'ready_to_charge'
        await self.refresh_at(site, 20)
        self.assertEqual(self.commands, [('a', 14)])

    async def test_plug_in_respects_pause_schedule_automatic_off_and_budget(self):
        for blocked in ('pause', 'schedule', 'manual', 'budget'):
            with self.subTest(blocked=blocked):
                site = self.setup_regulation(single=True)
                await self.unplug(site)
                c = site.controllers['a']
                d = c._async_sample.return_value
                d['status'] = 'awaiting_start'
                if blocked == 'pause': c.charging_paused = True
                if blocked == 'schedule': d['schedule_allowed'] = False
                if blocked == 'manual': c.auto_control = False
                if blocked == 'budget': d['energy_used_kwh'] = 10
                await self.refresh_at(site, 10)
                self.assertFalse(any(value > 0 for _, value in self.commands))

    async def test_plug_in_request_survives_invalid_input_until_measurements_ready(self):
        site = self.setup_regulation(single=True)
        await self.unplug(site)
        d = site.controllers['a']._async_sample.return_value
        d.update(status='awaiting_start', inputs_valid=False)
        await self.refresh_at(site, 10)
        self.assertEqual(self.commands, [])
        d['inputs_valid'] = True
        await self.refresh_at(site, 11)
        self.assertEqual(self.commands, [('a', 14)])

    async def test_second_plug_reallocates_only_after_measured_peer_reduction(self):
        from datetime import timedelta
        site = self.setup_regulation()
        await self.unplug(site, 'b')
        # First car keeps its existing 10 A while the other is disconnected.
        self.assertEqual(site.controllers['a'].last_commanded_current, 10)
        site.controllers['b']._async_sample.return_value['status'] = 'awaiting_start'
        # A tighter target requires the running car to give up capacity first.
        for c in site.controllers.values():
            c._async_sample.return_value['han_power_w'] = 8500
        await self.refresh_at(site, 10)
        self.assertEqual(self.commands, [('a', 6)])
        self.assertEqual(site.controllers['b'].last_commanded_current, 0)
        self.commands.clear()
        await self.refresh_at(site, 11)
        self.assertEqual(self.commands, [])  # Old telemetry is not approval.
        for c in site.controllers.values():
            c._async_sample.return_value['han_power_w'] = 7580
        a = site.controllers['a']
        limit = a.last_commanded_current
        a._async_sample.return_value.update(charger_current_a=limit, charger_power_w=limit*230)
        for suffix in ('power', 'current'):
            self.states['a_'+suffix] = NS(state=str(limit), last_updated=self.now+timedelta(seconds=12))
            self.states['b_'+suffix] = NS(state='0', last_updated=self.now+timedelta(seconds=12))
        await self.refresh_at(site, 12)
        self.assertTrue(any(key == 'b' and value > 0 for key, value in self.commands))
        self.assertFalse(site.pending_reductions)
        self.assertEqual(site._control_requested, site._control_applied)
        self.assertEqual(site.cadence.next_regular_at, self.now.timestamp()+312)

    async def test_unplug_replug_triggers_a_new_immediate_cycle(self):
        site = self.setup_regulation(single=True)
        await self.unplug(site)
        d = site.controllers['a']._async_sample.return_value
        d['status'] = 'awaiting_start'
        await self.refresh_at(site, 10)
        await self.unplug(site, seconds=15)
        d['status'] = 'awaiting_start'
        await self.refresh_at(site, 20)
        self.assertEqual(self.commands, [('a', 14)])
        self.assertEqual(site.cadence.next_regular_at, self.now.timestamp()+320)

    async def test_single_charger_does_not_spam_unchanged_limit_during_delayed_reduction(self):
        site = self.setup_regulation(single=True)
        c = site.controllers['a']
        c.last_commanded_current = 16
        c._last_command_at = self.now.timestamp()
        c._async_sample.return_value.update(charger_current_a=18, charger_power_w=4140)
        await self.refresh_at(site, 1)
        await self.refresh_at(site, 30)
        self.assertEqual(self.commands, [])
        await self.refresh_at(site, 60)
        self.assertEqual(self.commands, [('a', 16)])

    async def test_blocked_easee_states_stop(self):
        from smart_load_manager.charger_status import STATUS_TEXT, CHARGE_ELIGIBLE
        for status in (set(STATUS_TEXT) - CHARGE_ELIGIBLE - {'completed'}) | {'future_status'}:
            with self.subTest(status=status):
                site = self.setup_regulation(single=True)
                site.controllers['a']._async_sample.return_value['status'] = status
                data = await self.refresh_at(site, 1)
                self.assertEqual(data['recommended_current_a'], 0)
                self.assertEqual(data['last_sent_current_a'], 0)
                self.assertEqual(self.commands, [('a',0)])

    async def test_pausing_one_charger_releases_peer_only_after_measured_stop(self):
        from datetime import timedelta
        site = self.setup_regulation()
        await self.refresh_at(site, 0)  # Establish each load's permissions.
        site.controllers['a'].charging_paused = True
        await self.refresh_at(site, 1)
        self.assertEqual(self.commands, [('a', 0)])
        await self.refresh_at(site, 2)
        self.assertEqual(self.commands, [('a', 0)])
        site.controllers['a']._async_sample.return_value.update(charger_current_a=0, charger_power_w=0)
        for c in site.controllers.values():
            c._async_sample.return_value['han_power_w'] = 3700
        for suffix in ('power', 'current'):
            self.states['a_'+suffix] = NS(state='0', last_updated=self.now+timedelta(seconds=3))
        await self.refresh_at(site, 3)
        self.assertEqual(self.commands, [('a', 0), ('b', 16)])
        self.assertEqual(site.cadence.next_regular_at, self.now.timestamp()+303)

    async def test_new_control_request_during_awaited_command_is_not_consumed(self):
        site = self.setup_regulation(single=True)
        c = site.controllers['a']
        original_send = c._async_send_current
        async def send(value):
            await original_send(value)
            if value == 16:
                site.async_request_control()
        c._async_send_current = send
        site.async_request_control()
        await self.refresh_at(site, 1)
        self.assertEqual(self.commands, [('a', 16)])
        self.assertNotEqual(site._control_requested, site._control_applied)
        c._async_sample.return_value.update(max_current_a=20, han_power_w=1000)
        await self.refresh_at(site, 2)
        self.assertEqual(self.commands, [('a', 16), ('a', 20)])
        self.assertEqual(site._control_requested, site._control_applied)

    async def test_completion_preserves_single_limit_across_ticks_and_ready_states(self):
        site = self.setup_regulation(single=True)
        c = site.controllers['a']
        d = c._async_sample.return_value
        c.last_commanded_current = 16
        d.update(status='completed', charger_power_w=0, charger_current_a=.65,
                 han_power_w=1000)
        for seconds, status in [(1, 'completed'), (60, 'awaiting_start'),
                                (301, 'ready_to_charge'), (601, 'completed')]:
            d['status'] = status
            data = await self.refresh_at(site, seconds)
            self.assertEqual(data['last_sent_current_a'], 16)
            self.assertEqual(data['status'], status)  # Never invent/pin source status.
            self.assertEqual(self.commands, [])

    async def test_completed_peer_releases_capacity_only_after_measured_reduction(self):
        from datetime import timedelta
        site = self.setup_regulation()
        a = site.controllers['a']._async_sample.return_value
        a.update(status='completed', charger_power_w=0, charger_current_a=.65)
        # Capacity admits one active charger, not both commanded allowances.
        for c in site.controllers.values():
            c._async_sample.return_value['han_power_w'] = 7500
        await self.refresh_at(site, 1)
        self.assertEqual(self.commands, [('a', 0)])
        await self.refresh_at(site, 2)
        self.assertEqual(self.commands, [('a', 0)])
        for suffix in ('power', 'current'):
            self.states['a_'+suffix] = NS(state='0', last_updated=self.now+timedelta(seconds=3))
        a['status'] = 'awaiting_start'
        await self.refresh_at(site, 3)
        self.assertEqual(self.commands, [('a', 0), ('b', 16)])
        await self.refresh_at(site, 303)
        await self.refresh_at(site, 603)
        self.assertEqual(self.commands, [('a', 0), ('b', 16)])

    async def test_completed_allowance_remains_budgeted_and_reduces_for_household(self):
        site = self.setup_regulation(single=True)
        d = site.controllers['a']._async_sample.return_value
        d.update(status='completed', charger_power_w=0, charger_current_a=.65,
                 han_power_w=1000)
        await self.refresh_at(site, 1)
        self.assertEqual(self.commands, [])
        d['energy_used_kwh'] = 9.69
        await self.refresh_at(site, 2)
        self.assertEqual(self.commands, [('a', 0)])
        d['status'] = 'awaiting_start'
        await self.refresh_at(site, 62)
        self.assertEqual(self.commands, [('a', 0)])
        d['energy_used_kwh'] = 5
        await self.refresh_at(site, 302)
        self.assertEqual(self.commands, [('a', 0), ('a', 10)])

    async def test_completion_does_not_override_pause_schedule_or_invalid_inputs(self):
        for block in ('pause', 'schedule', 'inputs', 'voltage'):
            with self.subTest(block=block):
                site = self.setup_regulation(single=True)
                c = site.controllers['a']
                d = c._async_sample.return_value
                d.update(status='completed', charger_power_w=0, charger_current_a=.65)
                if block == 'pause': c.charging_paused = True
                if block == 'schedule': d['schedule_allowed'] = False
                if block == 'inputs': d['inputs_valid'] = False
                if block == 'voltage': d['kw_per_amp'] = None
                await self.refresh_at(site, 1)
                self.assertEqual(self.commands, [('a', 0)])

    async def test_completion_memory_clears_on_actual_charging_or_new_connection(self):
        for next_status in ('charging', 'start_charging', 'disconnected'):
            with self.subTest(status=next_status):
                site = self.setup_regulation(single=True)
                d = site.controllers['a']._async_sample.return_value
                d.update(status='completed', charger_power_w=0, charger_current_a=.65)
                await self.refresh_at(site, 1)
                self.assertIn('a', site._completed_limits)
                d['status'] = next_status
                await self.refresh_at(site, 2)
                self.assertNotIn('a', site._completed_limits)

    async def test_standby_exception_never_accepts_charging_power_or_large_current(self):
        for status, amps, watts in [('charging', .65, 0), ('awaiting_start', .65, 1),
                                     ('completed', 1, 0), ('future_status', .65, 0)]:
            with self.subTest(status=status, amps=amps, watts=watts):
                self.assertTrue(SiteController._current_above_limit(
                    dict(status=status, charger_current_a=amps, charger_power_w=watts), 0))

    async def test_completed_idle_allowance_never_consumes_active_allocation(self):
        for mode in ('both', 'one_at_a_time'):
            with self.subTest(mode=mode):
                site = self.setup_regulation()
                self.entries[0].options['allocation_mode'] = mode
                a = site.controllers['a']._async_sample.return_value
                a.update(status='completed', charger_power_w=0, charger_current_a=.65)
                for c in site.controllers.values():
                    c._async_sample.return_value['han_power_w'] = 5000
                data = await self.refresh_at(site, 1)
                peer = self.delivered['b']
                self.assertEqual(peer['recommended_current_a'], 16)
                expected_idle = 10 if mode == 'both' else 0
                self.assertEqual(data['recommended_current_a'], expected_idle)
                self.assertLessEqual((expected_idle + 16) * .23, data['site_available_kw'])

    async def test_full_completion_cycle_does_not_regrant_finished_peer_priority(self):
        site = self.setup_regulation()
        self.entries[0].options['allocation_mode'] = 'one_at_a_time'
        a = site.controllers['a']._async_sample.return_value
        a.update(status='completed', charger_power_w=0, charger_current_a=0)
        for c in site.controllers.values():
            c._async_sample.return_value['han_power_w'] = 5000
        await self.refresh_at(site, 1)
        # The pause caused by transferring the turn must not create a new demand.
        a['status'] = 'awaiting_start'
        data = await self.refresh_at(site, 301)
        self.assertEqual(data['recommended_current_a'], 0)
        self.assertEqual(self.delivered['b']['recommended_current_a'], 16)
        self.assertNotIn(('a', 10), self.commands)
