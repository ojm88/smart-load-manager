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

    def test_manual_charging_shows_schedule_block_and_clears_it_when_open(self):
        load = self.load(auto_control=False, status="awaiting_start",
                         schedule_enabled=True, schedule_allowed=False,
                         schedule_start_time="21:30:00")
        _, payload = build_household_status([load], limit_kwh=10)
        row = payload["controlled_loads"][0]
        self.assertEqual(row["mode_label"], "Manuell")
        self.assertEqual(row["status_label"], "Venter på starttid")
        self.assertIn("Tidsstyring", row["detail"])
        self.assertIn("21:30", row["detail"])
        load["data"]["schedule_allowed"] = True
        _, payload = build_household_status([load], limit_kwh=10)
        self.assertEqual(payload["controlled_loads"][0]["status_label"], "Venter")
        self.assertNotIn("21:30", payload["controlled_loads"][0]["detail"])

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

    def test_capacity_pause_reason_survives_repeated_calculation_periods(self):
        for deadline in (1000,1300,1600,1900):
            _,p=build_household_status([self.load(status='awaiting_start',recommended_current_a=0,
                last_sent_current_a=0,charger_power_w=0,kw_per_amp=.718,
                next_regulation_at=deadline)],limit_kwh=10)
            row=p['controlled_loads'][0]
            self.assertEqual(row['status_label'],'Venter på kapasitet')
            self.assertIn('forbruksgrense',row['detail'])
            self.assertIn('4.3 kW',row['detail'])
            self.assertIn('Reduser annet forbruk',row['detail'])
            self.assertTrue(row['show_waiting_check'])
            self.assertNotIn('bilen starter',row['detail'])

    def test_available_recommendation_is_not_a_sent_restart(self):
        _,p=build_household_status([self.load(status='awaiting_start',recommended_current_a=6,
            last_sent_current_a=0,charger_power_w=0,next_regulation_at=1600)],limit_kwh=10)
        row=p['controlled_loads'][0]
        self.assertEqual(row['status_label'],'Venter på regulering')
        self.assertIn('0 A',row['detail']);self.assertIn('plass til 6 A',row['detail'])
        self.assertIn('neste regulering',row['detail'])
        self.assertNotIn('bilen starter',row['detail'])

    def test_positive_offer_explains_waiting_without_claiming_vehicle_cause(self):
        _,p=build_household_status([self.load(status='awaiting_start',recommended_current_a=6,
            last_sent_current_a=6,charger_power_w=0)],limit_kwh=10)
        row=p['controlled_loads'][0]
        self.assertIn('har satt 6 A',row['detail'])
        self.assertIn('Easee melder fortsatt venting',row['detail'])
        self.assertIn('hvis dette vedvarer',row['detail'])

    def test_live_stop_recommendation_and_stop_feedback_are_visible_while_charging(self):
        for sent,expected in ((10,'beholder 10 A'),(0,'Avventer at laderen stanser')):
            _,p=build_household_status([self.load(recommended_current_a=0,last_sent_current_a=sent)],limit_kwh=10)
            row=p['controlled_loads'][0]
            self.assertEqual(row['status_label'],'Lader')
            self.assertIn(expected,row['detail'])
            self.assertIn('forbruksgrense',row['detail'])

    def test_explanations_cover_controls_faults_priority_and_missing_limits(self):
        for changes,expected in (
            (dict(auto_control=False,status='awaiting_start'),'Automatisk laststyring er av'),
            (dict(schedule_allowed=False,status='awaiting_start',schedule_start_time='02:00'),'02:00'),
            (dict(charging_paused=True,status='awaiting_start'),'Slå av ladepause'),
            (dict(status='error',inputs_valid=False),'Easee rapporterer en feil'),
            (dict(status='awaiting_start',recommended_current_a=None),'opplysninger'),
            (dict(awaiting_reduction=True),'reduksjonen er bekreftet'),
            (dict(inputs_valid=False,control_reason='HAN mangler.'),'HAN mangler.'),
        ):
            with self.subTest(changes=changes):
                _,p=build_household_status([self.load(**changes)],limit_kwh=10)
                self.assertIn(expected,p['controlled_loads'][0]['detail'])
        _,p=build_household_status([self.load(),self.load('b',status='awaiting_start',
            recommended_current_a=0,last_sent_current_a=0)],limit_kwh=10,priority='a',mode='one_at_a_time')
        self.assertIn('Garasje får lade først',p['controlled_loads'][1]['detail'])
        self.assertNotIn('Reduser annet forbruk',p['controlled_loads'][1]['detail'])

    def test_zero_power_feedback_is_explicit_and_idle_stays_compact(self):
        _,p=build_household_status([self.load(charger_power_w=0,last_sent_current_a=7)],limit_kwh=10)
        self.assertIn('målt effekt er 0 W',p['controlled_loads'][0]['detail'])
        for status in ('completed','disconnected'):
            _,p=build_household_status([self.load(status=status)],limit_kwh=10)
            self.assertEqual(p['controlled_loads'][0]['detail'],'')
            self.assertFalse(p['controlled_loads'][0]['show_waiting_check'])

    def test_wait_reasons_across_supported_charger_counts_and_modes(self):
        cases = (
            ("schedule", {"schedule_allowed": False, "schedule_enabled": True,
                          "schedule_start_time": "21:30:00"}, "21:30"),
            ("pause", {"charging_paused": True}, "Slå av ladepause"),
            ("offline", {"status": "offline"}, "frakoblet"),
            ("fault", {"status": "error"}, "Kontroller laderen"),
            ("easee schedule", {"status": "awaiting_scheduled_start"}, "egen ladeplan"),
            ("equalizer", {"status": "paused_due_to_equalizer"}, "Equalizer"),
            ("wiring", {"electrical_ready": False,
                        "electrical_error": "Kontroller tilkoblingen."}, "Kontroller tilkoblingen"),
        )
        automatic_cases = (
            ("stale HAN", {"han_fresh": False}, "gyldige målinger"),
            ("capacity", {"recommended_current_a": 0}, "forbruksgrense"),
            ("transfer", {"awaiting_reduction": True}, "reduksjonen er bekreftet"),
            ("pending increase", {"last_sent_current_a": 0}, "neste regulering"),
            ("sent offer", {"last_sent_current_a": 7}, "SLM har satt 7 A"),
        )
        for count in (1, 2):
            for automatic in (True, False):
                for name, changes, expected in cases + (automatic_cases if automatic else ()):
                    with self.subTest(count=count, automatic=automatic, reason=name):
                        data = {"status": "awaiting_start", "auto_control": automatic,
                                "charger_power_w": 0, "charger_current_a": 0}
                        loads = [self.load(**(data | changes))]
                        if count == 2:
                            loads.append(self.load("b", status="completed"))
                        _, payload = build_household_status(loads, limit_kwh=10)
                        row = payload["controlled_loads"][0]
                        self.assertIn(expected, row["detail"])
                        self.assertFalse(row["show_charging_details"])
                        if count == 2:
                            self.assertEqual(payload["controlled_loads"][1]["status_label"], "Fullført")
