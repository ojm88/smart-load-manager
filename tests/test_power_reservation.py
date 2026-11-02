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
