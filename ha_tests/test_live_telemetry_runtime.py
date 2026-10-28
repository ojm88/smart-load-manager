"""Source-driven display updates must never drive charging or reset polling."""
import asyncio
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.core import HomeAssistant
from smart_load_manager.coordinator import ChargingCoordinator


class LiveTelemetryTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = TemporaryDirectory()
        self.hass = HomeAssistant(self.tmp.name)
        from homeassistant.helpers import frame
        frame.async_setup(self.hass)
        from homeassistant.helpers.update_coordinator import UpdateFailed
        self.site = NS(lock=asyncio.Lock(), controllers={}, latest_samples={},
                       refresh=AsyncMock(side_effect=UpdateFailed("synthetic unavailable site")))
        from smart_load_manager.entity_resolution import EaseeEntities
        easee = EaseeEntities(status='sensor.source_status', current='sensor.source_current',
                   voltage='sensor.source_voltage', power='sensor.source_power', current_limits=())
        with patch('smart_load_manager.site.get_site', return_value=self.site), patch(
                'smart_load_manager.coordinator.resolve_easee_entities', return_value=easee):
            self.coordinator = ChargingCoordinator(self.hass, NS(
                entry_id='first', data={'charger_device': 'synthetic',
                                       'han_power_entity': 'sensor.source_han'}, options={}))
        self.coordinator.data = {'recommended_current_a': 10, 'status': 'disconnected',
                                 'site_available_kw': 5, 'control_reason': 'saved decision'}
        self.coordinator.last_update_success = True
        self.coordinator._async_send_current = AsyncMock()
        self.coordinator._async_sample = AsyncMock(return_value={
            'status': 'awaiting_start', 'charger_power_w': 0,
            'charger_current_a': 0, 'energy_used_kwh': 7.87,
            'energy_estimate_kwh': 9.49, 'han_power_w': 17339,
            'recommended_current_a': 99, 'control_reason': 'must not replace decision'})

    async def asyncTearDown(self):
        await self.coordinator.async_shutdown()
        await self.hass.async_stop(force=True)
        self.tmp.cleanup()

    async def test_source_event_publishes_without_regulation_or_timer_reset(self):
        c = self.coordinator
        notified = Mock()
        unsub = c.async_add_listener(notified)
        deadline = c._unsub_refresh
        c.async_start_source_updates()
        self.hass.states.async_set('sensor.source_status', 'awaiting_start')
        await self.hass.async_block_till_done()
        self.assertEqual(c.data['status'], 'awaiting_start')
        self.assertEqual(c.data['han_power_w'], 17339)
        self.assertIsNone(c.data['recommended_current_a'])
        self.assertEqual(c.data['control_reason'], 'saved decision')
        self.assertEqual(c._unsub_refresh, deadline)
        c._async_sample.assert_awaited_once_with(calculate=False)
        c._async_send_current.assert_not_awaited()
        self.assertTrue(notified.called)
        unsub()

    async def test_peer_updates_shared_snapshot_and_notifies_owner(self):
        c = self.coordinator
        self.site.latest_samples['first'] = dict(c.data)
        owner = NS(async_update_listeners=Mock())
        self.site.controllers['owner'] = owner
        await c._async_publish_telemetry()
        self.assertEqual(self.site.latest_samples['first']['status'], 'awaiting_start')
        self.assertIsNone(self.site.latest_samples['first']['recommended_current_a'])
        owner.async_update_listeners.assert_called_once()
        c._async_send_current.assert_not_awaited()

    async def test_attributes_and_tariff_events_update_but_unrelated_events_do_not(self):
        c = self.coordinator
        c.async_start_source_updates()
        self.hass.states.async_set('sensor.unrelated', 1)
        await self.hass.async_block_till_done()
        c._async_sample.assert_not_awaited()
        for source in ['sensor.source_voltage', 'sensor.energy_used_this_hour',
                       'sensor.energy_estimate_this_hour', 'sensor.source_han']:
            self.hass.states.async_set(source, 230, {'measured': 1})
            await self.hass.async_block_till_done()
            previous = c._async_sample.await_count
            self.hass.states.async_set(source, 230, {'measured': 2})
            await self.hass.async_block_till_done()
            self.assertGreater(c._async_sample.await_count, previous)

    async def test_shutdown_removes_source_subscription(self):
        c = self.coordinator
        c.async_start_source_updates()
        await c.async_shutdown()
        self.hass.states.async_set('sensor.source_status', 'charging')
        await self.hass.async_block_till_done()
        c._async_sample.assert_not_awaited()

    async def test_real_sampling_does_not_recalculate_or_command(self):
        c = self.coordinator
        c.entry.data['electrical_connection'] = 'it_1'
        c._async_sample = ChargingCoordinator._async_sample.__get__(c)
        self.hass.states.async_set('sensor.source_status', 'awaiting_start', {
            'config_phaseMode': 1, 'state_outputPhase': 0, 'circuit_ratedCurrent': 16})
        self.hass.states.async_set('sensor.source_current', 0, {
            'state_inCurrentT2': 0, 'state_inCurrentT3': 0})
        self.hass.states.async_set('sensor.source_voltage', 210, {'state_inVoltageT2T3': 210})
        self.hass.states.async_set('sensor.source_power', 0, {'unit_of_measurement': 'W'})
        self.hass.states.async_set('sensor.source_han', 17339, {'unit_of_measurement': 'W'})
        self.hass.states.async_set('sensor.energy_used_this_hour', 7.87)
        self.hass.states.async_set('sensor.energy_estimate_this_hour', 9.49)
        with patch('smart_load_manager.site.site_entry', return_value=c.entry), patch(
                'smart_load_manager.coordinator.recommended_current_a') as calculate:
            await c._async_publish_telemetry()
        calculate.assert_not_called()
        c._async_send_current.assert_not_awaited()
        self.assertEqual(c.data['status'], 'awaiting_start')
        self.assertTrue(c.data['electrical'], c.data)
        self.assertEqual(c.data['electrical']['line_voltage_v'], 210)
        self.assertEqual(c.data['han_power_w'], 17339)
        self.assertEqual(c.data['energy_used_kwh'], 7.87)
        self.assertEqual(c.data['energy_estimate_kwh'], 9.49)
        self.assertIsNone(c.data['recommended_current_a'])

    async def test_missing_charger_source_keeps_available_household_readings(self):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        c = self.coordinator
        c._async_sample.side_effect = UpdateFailed('missing charger voltage')
        self.hass.states.async_set('sensor.source_han', 17.339, {'unit_of_measurement': 'kW'})
        self.hass.states.async_set('sensor.energy_used_this_hour', 7.87)
        self.hass.states.async_set('sensor.energy_estimate_this_hour', 9.49)
        await c._async_publish_telemetry()
        self.assertEqual(c.data['han_power_w'], 17339)
        self.assertEqual(c.data['energy_used_kwh'], 7.87)
        self.assertFalse(c.data['inputs_valid'])
        self.assertIsNone(c.data['charger_current_a'])
        c._async_send_current.assert_not_awaited()

    async def test_source_event_recalculates_recommendation_without_ordinary_command(self):
        from smart_load_manager.site import SiteController
        from homeassistant.util import dt as dt_util
        c = self.coordinator
        site = SiteController(self.hass)
        site.controllers[c.entry.entry_id] = c
        c.site = site
        c.auto_control = True
        c.last_commanded_current = 10
        site.cadence.record_regular(dt_util.now().timestamp())
        c._async_sample.return_value.update(
            inputs_valid=True, han_fresh=True, energy_used_kwh=5,
            safety_margin_kwh=.3, minutes_left=30, han_power_w=1000,
            kw_per_amp=.23, schedule_allowed=True, control_minimum_current_a=6,
            max_current_a=16, electrical={})
        self.hass.states.async_set('sensor.source_power', 0)
        notify = Mock()
        unsub = c.async_add_listener(notify)
        deadline = c._unsub_refresh
        c.async_start_source_updates()
        with patch('smart_load_manager.site.charger_entries', return_value=[c.entry]), patch(
                'smart_load_manager.site.site_entry', return_value=c.entry):
            self.hass.states.async_set('sensor.source_status', 'awaiting_start')
            await self.hass.async_block_till_done()
        self.assertEqual(c.data['recommended_current_a'], 16)
        self.assertEqual(c.data['last_sent_current_a'], 10)
        self.assertEqual(c.data['status'], 'awaiting_start')
        c._async_sample.assert_awaited_once_with()
        c._async_send_current.assert_not_awaited()
        self.assertEqual(c._unsub_refresh, deadline)
        self.assertTrue(notify.called)
        unsub()

    async def test_source_change_during_command_wait_is_not_lost(self):
        c = self.coordinator
        entered, release = asyncio.Event(), asyncio.Event()
        count = 0
        async def refresh(requester):
            nonlocal count
            count += 1
            if count == 1:
                entered.set()
                await release.wait()
            return dict(c.data, status='charging' if count > 1 else 'awaiting_start')
        self.site.refresh = refresh
        c.async_start_source_updates()
        self.hass.states.async_set('sensor.source_status', 'awaiting_start')
        await entered.wait()
        self.hass.states.async_set('sensor.source_status', 'charging')
        await asyncio.sleep(0)
        release.set()
        await self.hass.async_block_till_done()
        self.assertEqual(count, 2)
        self.assertEqual(c.data['status'], 'charging')

    async def test_site_deadline_runs_without_new_source_and_is_cancelled_on_shutdown(self):
        from smart_load_manager.site import SiteController
        from homeassistant.util import dt as dt_util
        c = self.coordinator
        site = SiteController(self.hass)
        site.controllers[c.entry.entry_id] = c
        c.site = site
        c.auto_control = True
        c._source_changed = Mock()
        now = dt_util.now().timestamp()
        site.cadence.record_regular(now)
        cancel = Mock()
        with patch('smart_load_manager.site.async_call_later', return_value=cancel) as timer:
            site._arm_check()
            self.assertAlmostEqual(timer.call_args.args[1], 300, delta=1)
            site.cadence.risk_since = now
            site._arm_check()
            self.assertAlmostEqual(timer.call_args.args[1], 30, delta=1)
            self.assertTrue(cancel.called)
            timer.call_args.args[2](dt_util.now())
            c._source_changed.assert_called_once_with(None)
            site._arm_check()
            cancel.reset_mock()
            await c.async_shutdown()
            cancel.assert_called_once()
