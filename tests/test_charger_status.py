"""Operation mode coverage follows the public Easee integration mapping."""
import unittest
from custom_components.smart_load_manager.charger_status import (
    STATUS_TEXT, CHARGE_ELIGIBLE, allows_automatic_current, normalize_status, status_explanation)
from custom_components.smart_load_manager.household_status import build_household_status

class ChargerStatusTests(unittest.TestCase):
    def test_every_documented_operation_state_has_a_distinct_explanation(self):
        states = {'disconnected','awaiting_start','charging','completed','error',
                  'ready_to_charge','awaiting_authorization','de_authorizing',
                  'start_charging','stop_charging','offline','awaiting_load_balancing',
                  'awaiting_smart_start','awaiting_scheduled_start','authenticating',
                  'paused_due_to_equalizer','searching_for_master','erratic_ev',
                  'error_temperature_too_high','error_dead_powerboard','error_overcurrent','error_pen_fault'}
        self.assertEqual(set(STATUS_TEXT), states)
        for state in states:
            with self.subTest(state=state):
                self.assertTrue(status_explanation(state))
                self.assertTrue(status_explanation(state, norwegian=False))
                self.assertEqual(allows_automatic_current(state), state in CHARGE_ELIGIBLE)

    def test_unknown_future_state_is_not_authorized_to_charge(self):
        self.assertFalse(allows_automatic_current('future_status'))
        self.assertIn('ukjent', status_explanation('future_status'))

    def test_aliases_and_normalization_preserve_old_states(self):
        self.assertEqual(normalize_status(' Charged '), 'completed')
        self.assertEqual(normalize_status('awaiting_authentication'), 'awaiting_authorization')

    def test_completed_card_uses_completed_text_without_claiming_battery_percentage(self):
        state, data = build_household_status([
            {'id':'a', 'name':'Garasje', 'data':{'status':'completed', 'auto_control':True,
             'recommended_current_a':0, 'charger_power_w':0, 'electrical_ready':False}}
        ], limit_kwh=10)
        self.assertEqual(state, 'completed')
        self.assertEqual(data['summary'], 'Ladingen er fullført.')
        self.assertIn('fullført', data['controlled_loads'][0]['explanation'])
        self.assertNotIn('100', str(data))

    def test_blocked_and_unknown_modes_do_not_get_a_generic_running_explanation(self):
        for status in (set(STATUS_TEXT) - CHARGE_ELIGIBLE - {'completed','disconnected'}) | {'future_status'}:
            with self.subTest(status=status):
                state, data = build_household_status([
                    {'id':'a', 'name':'Garasje', 'data':{'status':status, 'auto_control':True,
                     'recommended_current_a':10, 'inputs_valid':True, 'han_fresh':True}}
                ], limit_kwh=10)
                self.assertEqual(state, 'waiting')
                self.assertEqual(data['controlled_loads'][0]['explanation'], status_explanation(status))
