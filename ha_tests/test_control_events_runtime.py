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
from smart_load_manager.switch import AutomaticLoadControl
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
            d.update(han_fresh=True, inputs_valid=bool(d['electrical_ready']), han_power_w=1000)
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
