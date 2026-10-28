"""Stable commands, forecast confirmation and hour boundaries."""
import unittest
from custom_components.smart_load_manager.regulation import RegulationCadence

class CadenceTests(unittest.TestCase):
    def decision(self, cadence, **changes):
        data = dict(now=101, limit_kwh=10, used_kwh=5, margin_kwh=.3,
                    held_power_kw=10, seconds_to_hour=1000)
        data.update(changes)
        return cadence.decide(**data)

    def running(self):
        c = RegulationCadence()
        c.record_regular(100)
        return c

    def test_live_changes_do_not_move_deadline_or_cause_ordinary_commands(self):
        c = self.running()
        for now in (101, 110, 160, 399):
            self.assertEqual(self.decision(c, now=now), 'hold')
            self.assertEqual(c.next_regular_at, 400)
        self.assertEqual(self.decision(c, now=400), 'regular')

    def test_first_cycle_and_unchanged_cycle_still_schedule_next_five_minutes(self):
        c = RegulationCadence()
        self.assertEqual(self.decision(c), 'regular')
        c.record_regular(101)
        self.assertEqual(c.next_regular_at, 401)

    def test_small_drop_without_horizon_risk_does_not_reduce(self):
        self.assertEqual(self.decision(self.running(), used_kwh=8), 'hold')

    def test_risk_requires_thirty_seconds_but_brief_spike_resets_confirmation(self):
        c = self.running()
        self.assertEqual(self.decision(c, used_kwh=9.5), 'hold')
        self.assertEqual(self.decision(c, used_kwh=9.5, now=120), 'hold')
        self.assertEqual(self.decision(c, used_kwh=9.5, now=131), 'early')
        self.assertEqual(self.decision(c, used_kwh=8, now=132), 'hold')
        self.assertIsNone(c.risk_since)
        self.assertEqual(self.decision(c, used_kwh=9.5, now=133), 'hold')

    def test_budget_exhaustion_and_near_exhaustion_are_immediate(self):
        for used in (9.7, 9.8, 9.69):
            self.assertEqual(self.decision(self.running(), used_kwh=used), 'urgent')

    def test_projection_stops_at_clock_hour_boundary(self):
        self.assertEqual(self.decision(self.running(), used_kwh=9.5, seconds_to_hour=10), 'hold')

    def test_five_minute_hold_after_early_reduction(self):
        c = self.running()
        c.record_early_reduction(131)
        self.assertEqual(c.next_regular_at, 431)
        self.assertEqual(self.decision(c, now=400), 'hold')

    def test_early_reduction_never_consumes_next_hours_budget(self):
        c = self.running()
        self.decision(c, used_kwh=9.5)
        self.assertEqual(self.decision(c, now=140, used_kwh=0, seconds_to_hour=3590), 'hold')
        self.assertIsNone(c.risk_since)
