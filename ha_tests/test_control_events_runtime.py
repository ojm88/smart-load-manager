"""User controls and exact schedule boundaries bypass only ordinary cadence."""
from datetime import UTC, datetime, time, timedelta
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch

from homeassistant.core import HomeAssistant
from smart_load_manager.coordinator import ChargingCoordinator
from smart_load_manager.entity_resolution import EaseeEntities
from smart_load_manager.site import SiteController
from smart_load_manager.switch import AutomaticLoadControl, ChargingAutomationControl
from smart_load_manager.time import ChargingScheduleStartTime


class ControlEventTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = TemporaryDirectory()
        self.hass = HomeAssistant(self.tmp.name)
        from homeassistant.helpers import frame
        frame.async_setup(self.hass)
        self.now = datetime(2026, 10, 28, 21, 0, tzinfo=UTC)
        self.entry = NS(entry_id='first', title='Garage', options={'consumption_limit_kwh':10}, data={
            'charger_device': 'synthetic', 'electrical_connection': 'it_1',
            'han_power_entity': 'sensor.test_han'})
        self.site = SiteController(self.hass)
        easee = EaseeEntities(status='sensor.test_status', current='sensor.test_current',
                             voltage='sensor.test_voltage', power='sensor.test_power', current_limits=())
        patches = [
            patch('smart_load_manager.coordinator.resolve_easee_entities', return_value=easee),
            patch('smart_load_manager.site.get_site', return_value=self.site),
            patch('smart_load_manager.site.charger_entries', return_value=[self.entry]),
            patch('smart_load_manager.coordinator.charger_entries', return_value=[self.entry]),
            patch('smart_load_manager.site.site_entry', return_value=self.entry),
            patch('smart_load_manager.site.dt_util.now', side_effect=lambda: self.now),
            patch('smart_load_manager.coordinator.update_load', side_effect=self.save),
            patch('smart_load_manager.time.update_load', side_effect=self.save),
            patch('smart_load_manager.installation.update_load', side_effect=self.save),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.c = ChargingCoordinator(self.hass, self.entry)
        self.c.auto_control = True
        self.commands = []
        async def send(current):
            self.commands.append(current)
            self.c.last_commanded_current = current
            self.c._last_command_at = self.now.timestamp()
        self.c._async_send_current = send
        self.hass.states.async_set('sensor.test_status', 'awaiting_start', {
            'config_phaseMode': 1, 'state_outputPhase': 0, 'circuit_ratedCurrent': 16})
        self.hass.states.async_set('sensor.test_current', 0, {'state_inCurrentT2': 0, 'state_inCurrentT3': 0})
        self.hass.states.async_set('sensor.test_voltage', 230, {'state_inVoltageT2T3': 230})
        self.hass.states.async_set('sensor.test_power', 0, {'unit_of_measurement': 'W'})
        self.hass.states.async_set('sensor.test_han', 1000, {'unit_of_measurement': 'W'})
        self.hass.states.async_set('sensor.energy_used_this_hour', 1)
        # HA source timestamps are real: keep this synthetic meter explicitly fresh.
        self.c._async_sample_real = self.c._async_sample
        async def sample(**kwargs):
            d = await self.c._async_sample_real(**kwargs)
            d.update(han_fresh=True, inputs_valid=bool(d['electrical_ready'] and d.get('energy_used_kwh') is not None), han_power_w=1000)
            return d
        self.c._async_sample = sample

    def save(self, hass, entry, *, options=None, data=None):
        if options is not None:
            entry.options = options

    async def refresh(self):
        self.c.async_publish_sample(await self.site.refresh(self.c))

    async def asyncTearDown(self):
        await self.c.async_shutdown()
        await self.hass.async_stop(force=True)
        self.tmp.cleanup()

    async def test_pause_resume_applies_immediately_without_refresh_debounce(self):
        await self.refresh()
        self.assertEqual(self.commands, [16])
        self.now += timedelta(seconds=1)
        await self.c.async_set_charging_paused(True)
        self.assertEqual(self.commands[-1], 0)
        self.now += timedelta(seconds=1)
        await self.c.async_set_charging_paused(False)
        self.assertEqual(self.commands, [16, 0, 16])
        self.assertEqual(self.c.data['last_sent_current_a'], 16)
        self.assertEqual(self.site.cadence.next_regular_at, self.now.timestamp()+300)

    async def test_schedule_boundary_runs_without_meter_or_status_update(self):
        self.c.schedule_enabled = True
        self.entry.options['schedule_start_time'] = '21:00:10'
        with patch('smart_load_manager.site.async_call_later', return_value=Mock()) as timer:
            await self.refresh()
            self.assertEqual(self.commands, [0])
            self.assertAlmostEqual(timer.call_args.args[1], 10)
            # Execute the dedicated boundary callback; no source changes arrive.
            self.now += timedelta(seconds=10)
            timer.call_args.args[2](self.now)
            await self.hass.async_block_till_done()
            self.assertEqual(self.commands, [0, 16])
            self.assertEqual(self.site.cadence.next_regular_at, self.now.timestamp()+300)
            self.assertTrue(self.c.data['schedule_allowed'])

    async def test_schedule_disabling_and_time_edit_resume_without_five_minute_wait(self):
        self.c.schedule_enabled = True
        self.entry.options['schedule_start_time'] = '22:00:00'
        await self.refresh()
        self.assertEqual(self.commands, [0])
        self.now += timedelta(seconds=1)
        await self.c.async_set_schedule_enabled(False)
        self.assertEqual(self.commands, [0, 16])
        await self.c.async_set_schedule_enabled(True)
        self.assertEqual(self.commands[-1], 0)
        entity = NS(coordinator=self.c, hass=self.hass, async_write_ha_state=Mock())
        await ChargingScheduleStartTime.async_set_value(entity, time(20, 59))
        self.assertEqual(self.commands[-1], 16)
        self.assertTrue(self.c.data['schedule_allowed'])

    async def test_enabling_automatic_control_applies_immediately(self):
        self.c.auto_control = False
        self.c.last_commanded_current = 0
        await self.refresh()
        entity = NS(coordinator=self.c, async_write_ha_state=Mock())
        await AutomaticLoadControl.async_turn_on(entity)
        self.assertEqual(self.commands, [16])

    async def test_resume_still_respects_pause_and_missing_voltage(self):
        self.c.schedule_enabled = True
        self.entry.options['schedule_start_time'] = '22:00:00'
        await self.refresh()
        await self.c.async_set_charging_paused(True)
        await self.c.async_set_schedule_enabled(False)
        self.assertFalse(any(v > 0 for v in self.commands))
        self.hass.states.async_set('sensor.test_voltage', 'unavailable')
        from homeassistant.helpers.update_coordinator import UpdateFailed
        with self.assertRaises(UpdateFailed):
            await self.c.async_set_charging_paused(False)
        self.assertFalse(any(v > 0 for v in self.commands))

    async def test_end_of_schedule_stops_at_boundary(self):
        self.c.schedule_enabled = True
        self.entry.options['schedule_start_time'] = '09:00:10'
        with patch('smart_load_manager.site.async_call_later', return_value=Mock()) as timer:
            await self.refresh()
            self.assertEqual(self.commands, [16])
            self.assertAlmostEqual(timer.call_args.args[1], 10)
            self.now += timedelta(seconds=10)
            timer.call_args.args[2](self.now)
            await self.hass.async_block_till_done()
            self.assertEqual(self.commands, [16, 0])
            self.assertFalse(self.c.data['schedule_allowed'])

    async def test_resume_checks_current_budget_instead_of_restoring_old_limit(self):
        await self.refresh()
        await self.c.async_set_charging_paused(True)
        self.hass.states.async_set('sensor.energy_used_this_hour', 10)
        await self.c.async_set_charging_paused(False)
        self.assertEqual(self.commands, [16, 0])
        self.assertEqual(self.c.data['recommended_current_a'], 0)
        self.assertEqual(self.c.data['last_sent_current_a'], 0)

    async def test_manual_pause_resume_restores_explicit_limit_immediately(self):
        self.c.auto_control = False
        self.c.last_commanded_current = 12
        await self.refresh()
        await self.c.async_set_charging_paused(True)
        await self.c.async_set_charging_paused(False)
        self.assertEqual(self.commands, [0, 12])

    async def test_editing_future_start_time_cancels_old_boundary(self):
        self.c.schedule_enabled = True
        self.entry.options['schedule_start_time'] = '21:00:10'
        old_cancel = Mock()
        with patch('smart_load_manager.site.async_call_later', return_value=old_cancel) as timer:
            await self.refresh()
            self.assertEqual(timer.call_args.args[1], 10)
            entity = NS(coordinator=self.c, hass=self.hass, async_write_ha_state=Mock())
            await ChargingScheduleStartTime.async_set_value(entity, time(21, 0, 20))
            old_cancel.assert_called_once()
            self.assertEqual(timer.call_args.args[1], 20)
            self.assertEqual(self.commands, [0])

    async def test_auto_off_starts_at_measured_minimum_immediately_and_number_follows(self):
        from smart_load_manager.number import ChargingCurrentLimit
        await self.refresh()
        self.c.last_commanded_current = 0  # Waiting in automatic mode beforehand.
        self.commands.clear()
        entity=NS(coordinator=self.c, async_write_ha_state=Mock())
        await AutomaticLoadControl.async_turn_off(entity)
        self.assertFalse(self.c.auto_control)
        self.assertEqual(self.commands,[6])
        self.assertEqual(self.c.manual_current_setting,6)
        self.assertEqual(self.c.data['last_sent_current_a'],6)
        self.assertEqual(ChargingCurrentLimit.native_value.fget(NS(coordinator=self.c)),6)
        # A later user choice remains; repeated off is idempotent.
        await self.c.async_set_current(12)
        await AutomaticLoadControl.async_turn_off(entity)
        self.assertEqual(self.c.manual_current_setting,12)
        self.assertEqual(self.commands,[6,12])

    async def test_auto_off_on_it_three_phase_chooses_eleven_not_ten(self):
        real=self.c._async_sample
        async def sample(**kwargs):
            d=await real(**kwargs)
            d.update(control_minimum_current_a=11,kw_per_amp=.4)
            return d
        self.c._async_sample=sample
        await self.refresh()
        self.commands.clear()
        await AutomaticLoadControl.async_turn_off(NS(coordinator=self.c,async_write_ha_state=Mock()))
        self.assertEqual(self.commands,[11])
        self.assertEqual(self.c.manual_current_setting,11)

    async def test_auto_off_respects_pause_and_resume_uses_selected_minimum(self):
        await self.refresh()
        await self.c.async_set_charging_paused(True)
        self.commands.clear()
        await AutomaticLoadControl.async_turn_off(NS(coordinator=self.c,async_write_ha_state=Mock()))
        self.assertEqual(self.commands,[])
        self.assertEqual(self.c.manual_current_setting,6)
        self.assertEqual(self.c.last_commanded_current,0)
        await self.c.async_set_charging_paused(False)
        self.assertEqual(self.commands,[6])

    async def test_manual_handover_waits_for_schedule_and_starts_at_exact_open(self):
        self.c.schedule_enabled=True
        self.entry.options['schedule_start_time']='21:00:10'
        with patch('smart_load_manager.site.async_call_later',return_value=Mock()) as timer:
            await self.refresh()
            await AutomaticLoadControl.async_turn_off(NS(coordinator=self.c,async_write_ha_state=Mock()))
            self.assertEqual(self.c.manual_current_setting,6)
            self.assertEqual(self.commands,[0])
            self.assertAlmostEqual(timer.call_args.args[1],10)
            self.now+=timedelta(seconds=10)
            timer.call_args.args[2](self.now)
            await self.hass.async_block_till_done()
            self.assertEqual(self.commands,[0,6])
            self.assertFalse(self.c.auto_control)

    async def test_manual_handover_invalid_sources_never_send_positive_and_recover(self):
        await self.refresh()
        self.hass.states.async_set('sensor.energy_used_this_hour','unavailable')
        self.commands.clear()
        await AutomaticLoadControl.async_turn_off(NS(coordinator=self.c,async_write_ha_state=Mock()))
        self.assertEqual(self.commands,[0])
        self.assertEqual(self.c.manual_current_setting,6)
        self.hass.states.async_set('sensor.energy_used_this_hour',1)
        await self.refresh()
        self.assertEqual(self.commands,[0,6])

    async def test_manual_handover_never_exceeds_live_maximum(self):
        real=self.c._async_sample
        async def sample(**kwargs):
            d=await real(**kwargs)
            d.update(control_minimum_current_a=11,max_current_a=10,kw_per_amp=.4)
            return d
        self.c._async_sample=sample
        self.c.last_commanded_current=16
        await AutomaticLoadControl.async_turn_off(NS(coordinator=self.c,async_write_ha_state=Mock()))
        self.assertEqual(self.commands,[0])
        self.assertEqual(self.c.manual_current_setting,0)

    async def test_charging_category_operates_both_and_preserves_individual_choice(self):
        peer_entry=NS(entry_id='second',title='Carport',options={},data=dict(self.entry.data))
        peer=ChargingCoordinator(self.hass,peer_entry)
        peer.auto_control=True
        peer.last_commanded_current=16
        peer._async_sample=self.c._async_sample
        sent=[]
        async def send(value):
            sent.append(value);peer.last_commanded_current=value;peer._last_command_at=self.now.timestamp()
        peer._async_send_current=send
        group=ChargingAutomationControl(self.c,self.entry)
        group.hass=self.hass
        group.async_write_ha_state=Mock()
        self.c.last_commanded_current=16
        with patch('smart_load_manager.site.charger_entries',return_value=[self.entry,peer_entry]):
            await group.async_turn_off()
            self.assertEqual(self.commands,[6])
            self.assertEqual(sent,[6])
            self.assertFalse(group.is_on)
            self.assertFalse(self.c.auto_control)
            self.assertFalse(peer.auto_control)
            # Mixed state is explicit when an individual charger is enabled.
            peer.auto_control=True
            self.assertTrue(group.is_on)
            self.assertEqual(group.extra_state_attributes['control_mode'],'mixed')
        await peer.async_shutdown()

    async def test_category_startup_off_does_not_start_manual_charging_on_its_own(self):
        self.c.auto_control=False
        group=ChargingAutomationControl(self.c,self.entry)
        group.hass=self.hass
        group.async_write_ha_state=Mock()
        self.assertFalse(group.is_on)
        self.assertIsNone(self.c.manual_current_setting)
        self.assertEqual(self.commands,[])

    async def test_unchanged_han_reports_keep_completed_session_quiet(self):
        # Real sampler, fresh repeated report but an unchanged value for hours.
        # Simulates the overnight sequence without overriding input validity.
        self.c._async_sample = self.c._async_sample_real
        self.c.auto_control = True
        self.c.last_commanded_current = 16
        self.hass.states.async_set('sensor.test_status', 'completed', {
            'config_phaseMode': 1, 'state_outputPhase': 0, 'circuit_ratedCurrent': 16})
        source_get = self.hass.states.get
        han = source_get('sensor.test_han')
        from types import SimpleNamespace as NS
        from datetime import timedelta
        for seconds in (1, 301, 601, 3601, 21601):
            self.now = self.now + timedelta(seconds=seconds)
            report = NS(state=han.state, attributes=han.attributes,
                        last_updated=self.now-timedelta(hours=12), last_reported=self.now)
            with patch.object(type(self.hass.states), 'get', new=lambda machine, key: report if key == 'sensor.test_han' else source_get(key)):
                await self.refresh()
            self.assertTrue(self.c.data['han_fresh'])
            self.assertEqual(self.c.data['han_power_w'], 1000)
            self.assertEqual(self.commands, [])
        # A timestamp alone is not proof of a missing device heartbeat.
        # Keep raw completed and its offer quiet, while honestly marking the
        # numeric reading stale and withholding new allocation.
        report.last_reported = self.now-timedelta(minutes=5)
        with patch.object(type(self.hass.states), 'get', new=lambda machine, key: report if key == 'sensor.test_han' else source_get(key)):
            await self.refresh()
        self.assertFalse(self.c.data['han_fresh'])
        self.assertEqual(self.c.data['han_power_w'], 1000)
        self.assertTrue(self.c.data['completion_hold'])
        self.assertFalse(self.c.data['site_control_ready'])
        self.assertEqual(self.commands, [])
        # Actual wake cannot use the idle exception while HAN is still stale.
        attrs={'config_phaseMode':1,'state_outputPhase':0,'circuit_ratedCurrent':16}
        self.hass.states.async_set('sensor.test_status','charging',attrs)
        with patch.object(type(self.hass.states), 'get', new=lambda machine, key: report if key == 'sensor.test_han' else source_get(key)):
            await self.refresh()
        self.assertEqual(self.commands, [0])
        report.last_reported=self.now
        self.hass.states.async_set('sensor.test_status','ready_to_charge',attrs)
        with patch.object(type(self.hass.states), 'get', new=lambda machine, key: report if key == 'sensor.test_han' else source_get(key)):
            await self.refresh()
        self.assertGreater(self.commands[-1],0)
        self.assertTrue(self.c.data['site_control_ready'])
