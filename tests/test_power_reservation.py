import unittest
from custom_components.smart_load_manager.power_reservation import PowerReservations

class ReservationsTests(unittest.TestCase):
    def setUp(self):
        self.r=PowerReservations()
        self.d=dict(status='charging',inputs_valid=True,han_fresh=True,kw_per_amp=.23,charger_power_w=2300,auto_control=True)
    def estimate(self,t,limit=20,command=0):
        return self.r.estimate('a',self.d,offered_a=limit,command_at=command,now=t)
    def test_hidden_app_limit_releases_phantom_forecast_after_settling(self):
        self.assertAlmostEqual(self.estimate(0),4.6)
        self.assertAlmostEqual(self.estimate(179),4.6)
        self.assertAlmostEqual(self.estimate(180),2.4)
    def test_new_offer_and_resumed_consumption_restore_reservation(self):
        self.estimate(0); self.estimate(180)
        self.assertAlmostEqual(self.estimate(181,command=181),4.6)
        self.d['charger_power_w']=4140
        self.assertAlmostEqual(self.estimate(182),4.6)
    def test_no_release_for_waiting_zero_draw_or_invalid_han(self):
        for changes in [dict(status='awaiting_start'),dict(charger_power_w=0),dict(han_fresh=False)]:
            original=dict(self.d);self.estimate(0);self.d.update(changes)
            self.assertAlmostEqual(self.estimate(200),4.6)
            self.d=original
            self.assertAlmostEqual(self.estimate(201),4.6)
    def test_manual_and_unequal_phase_forms_have_same_consumption_contract(self):
        self.d.update(auto_control=False,kw_per_amp=.69,charger_power_w=11040)
        self.estimate(0)
        self.assertAlmostEqual(self.estimate(180),11.14)

    def settle(self):
        self.estimate(0)
        self.assertAlmostEqual(self.estimate(180), 2.4)

    def test_regulation_pause_reuses_confirmed_demand_without_three_minute_wait(self):
        for status in ('awaiting_start', 'awaiting_load_balancing', 'ready_to_charge', 'charging'):
            with self.subTest(status=status):
                self.setUp()
                self.settle()
                # Command arrives before status and power catch up.
                self.estimate(181, limit=0, command=181)
                self.d.update(status=status, charger_power_w=0)
                self.assertEqual(self.estimate(182, limit=0, command=181), 0)
                # A positive offer alone never spends cached capacity.
                self.assertAlmostEqual(self.estimate(183, command=183), 4.6)
                self.d.update(status='charging', charger_power_w=0)
                self.assertAlmostEqual(self.estimate(184, command=183), 4.6)
                self.d['charger_power_w']=2300
                self.assertAlmostEqual(self.estimate(185, command=183), 2.4)
                self.assertAlmostEqual(self.estimate(186, command=183), 2.4)

    def test_waiting_before_zero_command_and_repeated_pauses_keep_observation(self):
        self.settle()
        for t in (200, 400, 600):
            self.d.update(status='awaiting_load_balancing', charger_power_w=2300)
            self.assertAlmostEqual(self.estimate(t),4.6)
            self.d['charger_power_w']=0
            self.assertEqual(self.estimate(t+1,limit=0,command=t),0)
            self.d.update(status='charging',charger_power_w=2300)
            self.assertAlmostEqual(self.estimate(t+2,command=t+2),2.4)

    def test_unsettled_draw_cannot_learn_during_long_pause(self):
        self.estimate(0)
        self.d.update(status='awaiting_start',charger_power_w=0)
        self.estimate(1000,limit=0)
        self.d.update(status='charging',charger_power_w=2300)
        self.assertAlmostEqual(self.estimate(1001,command=1001),4.6)
        self.assertAlmostEqual(self.estimate(1180,command=1001),4.6)
        self.assertAlmostEqual(self.estimate(1181,command=1001),2.4)

    def test_completed_or_disconnected_starts_new_learning_even_without_zero(self):
        for status in ('completed','disconnected','charged'):
            with self.subTest(status=status):
                self.setUp(); self.settle()
                self.d['status']=status
                self.estimate(200)
                self.d['status']='awaiting_start'
                self.estimate(201)
                self.d['status']='charging'
                self.assertAlmostEqual(self.estimate(202),4.6)
                self.assertAlmostEqual(self.estimate(381),4.6)
                self.assertAlmostEqual(self.estimate(382),2.4)

    def test_rebound_or_higher_offer_after_pause_restores_full_reservation(self):
        for power,limit in ((4140,20),(2300,24)):
            with self.subTest(power=power,limit=limit):
                self.setUp(); self.settle()
                self.d.update(status='awaiting_start',charger_power_w=0)
                self.estimate(181,limit=0,command=181)
                self.d.update(status='charging',charger_power_w=power)
                self.assertAlmostEqual(self.estimate(182,limit=limit,command=182),limit*.23)

    def test_pause_does_not_survive_input_fault_phase_or_mode_change(self):
        for change in (dict(han_fresh=False),dict(inputs_valid=False),
                       dict(charger_power_w=float('nan')),dict(status='offline'),
                       dict(phase_mode_code=1),dict(auto_control=False),dict(kw_per_amp=.69)):
            with self.subTest(change=change):
                self.setUp(); self.settle()
                self.d.update(status='awaiting_start',charger_power_w=0)
                self.estimate(181,limit=0)
                self.d.update(change)
                self.estimate(182,limit=0)
                self.d=dict(status='charging',inputs_valid=True,han_fresh=True,
                            kw_per_amp=.23,charger_power_w=2300,auto_control=True)
                self.assertAlmostEqual(self.estimate(183),4.6)

    def test_peer_session_is_independent_and_manual_three_phase_can_resume(self):
        self.d.update(auto_control=False,kw_per_amp=.69,charger_power_w=11040)
        self.estimate(0)
        self.assertAlmostEqual(self.estimate(180),11.14)
        peer=dict(self.d,status='completed')
        self.r.estimate('b',peer,offered_a=20,command_at=0,now=181)
        self.d.update(status='awaiting_start',charger_power_w=0)
        self.estimate(182,limit=0,command=182)
        self.d.update(status='charging',charger_power_w=11040)
        self.assertAlmostEqual(self.estimate(183,command=183),11.14)
