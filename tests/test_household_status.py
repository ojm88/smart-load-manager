"""Household explanations reflect calculated decisions without controlling loads."""
import unittest
from copy import deepcopy
from custom_components.smart_load_manager.household_status import build_household_status

class HouseholdStatusTests(unittest.TestCase):
    def load(self, key='a', **changes):
        data=dict(status='charging',auto_control=True,inputs_valid=True,han_fresh=True,
                  site_control_ready=True,recommended_current_a=7,kw_per_amp=.23,
                  max_current_a=16,control_minimum_current_a=6,
                  charger_power_w=1600,charger_current_a=7,
                  schedule_enabled=False,schedule_allowed=True)
        data.update(changes)
        return {'id':key,'name':'Garasje' if key=='a' else 'Carport','data':data}

    def test_summary_does_not_modify_or_reallocate(self):
        loads=[self.load(),self.load('b')]
        before=deepcopy(loads)
        state,info=build_household_status(loads,limit_kwh=10,priority='a')
        self.assertEqual(state,'automatic')
        self.assertEqual(info['consumption_limit_kwh'],10)
        self.assertEqual(len(info['controlled_loads']),2)
        self.assertEqual(loads,before)
        self.assertIn('Begge deler',info['distribution_explanation'])

    def test_sequential_wait_names_priority_and_never_claims_full_battery(self):
        loads=[self.load(),self.load('b',status='awaiting_start',recommended_current_a=0)]
        _,info=build_household_status(loads,limit_kwh=10,priority='a',mode='one_at_a_time')
        self.assertIn('Garasje får lade først',info['controlled_loads'][1]['explanation'])
        _,ended=build_household_status([self.load(status='completed')],limit_kwh=10)
        self.assertNotIn('fulladet',ended['controlled_loads'][0]['explanation'])

    def test_missing_peer_is_visible_instead_of_silently_omitted(self):
        state,info=build_household_status([self.load(),{'id':'b','name':'Carport','data':None}],limit_kwh=10)
        self.assertEqual(state,'waiting')
        self.assertEqual(info['controlled_loads'][1]['name'],'Carport')
        self.assertIn('mangler',info['controlled_loads'][1]['explanation'])

    def test_schedule_and_pause_are_distinguished_from_capacity(self):
        _,info=build_household_status([self.load(schedule_allowed=False,schedule_start_time='02:00:00')],limit_kwh=10)
        self.assertIn('02:00',info['controlled_loads'][0]['explanation'])
        state,paused=build_household_status([self.load(charging_paused=True)],limit_kwh=10)
        self.assertEqual(state,'paused')
        self.assertIn('ladepause',paused['controlled_loads'][0]['explanation'])

    def test_phase_advice_is_given_once_and_supports_english(self):
        loads=[self.load(phase_advice='Enfase på begge laderne kan gi plass.'),
               self.load('b',phase_advice='Enfase på begge laderne kan gi plass.')]
        _,info=build_household_status(loads,limit_kwh=10,norwegian=False)
        self.assertIn('Single phase',info['phase_advice'])
        self.assertNotIn('phase_advice',info['controlled_loads'][0])

    def test_wait_for_confirmation_is_not_reported_as_active_allocation(self):
        state,info=build_household_status([self.load(awaiting_reduction=True)],limit_kwh=10)
        self.assertEqual(state,'waiting')
        self.assertIn('bekreftet',info['controlled_loads'][0]['explanation'])

    def test_lower_live_recommendation_does_not_claim_running_car_is_paused(self):
        state, info = build_household_status([
            self.load(status='charging', recommended_current_a=0, last_sent_current_a=10)
        ], limit_kwh=10)
        self.assertEqual(state, 'automatic')
        self.assertIn('beholder', info['controlled_loads'][0]['explanation'])
        self.assertEqual(info['controlled_loads'][0]['last_sent_current_a'], 10)

    def test_each_charger_has_its_own_readable_status_and_reason(self):
        loads = [self.load(), self.load('b', status='awaiting_start',
                 recommended_current_a=0, schedule_allowed=False, schedule_start_time='23:00:00')]
        _, info = build_household_status(loads, limit_kwh=10)
        first, second = info['controlled_loads']
        self.assertEqual((first['name'], first['status_label']), ('Garasje', 'Lader'))
        self.assertEqual((second['name'], second['status_label']), ('Carport', 'Venter på starttid'))
        self.assertIn('23:00', second['explanation'])

    def test_status_labels_never_infer_charging_from_a_recommendation(self):
        for status, changes, label in (
            ('awaiting_start', {}, 'Venter'),
            ('awaiting_start', {'charging_paused': True}, 'Pauset'),
            ('completed', {}, 'Fullført'),
            ('disconnected', {}, 'Frakoblet'),
            ('awaiting_authorization', {}, 'Venter på godkjenning'),
            ('error', {}, 'Feil'),
            ('offline', {}, 'Utilgjengelig'),
        ):
            with self.subTest(status=status, changes=changes):
                _, info = build_household_status([self.load(status=status, **changes)], limit_kwh=10)
                self.assertEqual(info['controlled_loads'][0]['status_label'], label)

    def test_connection_summary_distinguishes_single_pair_and_mixed(self):
        for loads, expected in (
            ([self.load(status='disconnected')], 'Ingen bil er tilkoblet.'),
            ([self.load(status='disconnected'), self.load('b',status='disconnected')], 'Ingen biler er tilkoblet.'),
            ([self.load(), self.load('b',status='disconnected')], 'Bil tilkoblet: Garasje. Frakoblet: Carport.'),
        ):
            _, payload=build_household_status(loads,limit_kwh=10)
            self.assertEqual(payload['summary'],expected)

    def test_unknown_peer_is_never_described_as_connected(self):
        _,payload=build_household_status([self.load(status='disconnected'),self.load('b',status='unknown')],limit_kwh=10)
        self.assertNotIn('Bil tilkoblet:',payload['summary'])
        self.assertNotIn('Ingen biler',payload['summary'])
