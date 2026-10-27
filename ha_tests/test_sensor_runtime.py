"""Regression for coordinator payloads and entity registration under Home Assistant."""

from types import SimpleNamespace
import unittest

from smart_load_manager.sensor import ChargingDiagnosticSensor, SENSORS


class SensorRuntimeTests(unittest.TestCase):
    def test_new_sensor_uses_the_stable_slm_entity_id(self):
        coordinator = SimpleNamespace(data={}, last_update_success=True, entry=SimpleNamespace(data={}))
        entry = SimpleNamespace(entry_id="test-entry", title="Smart Load Manager OJM")
        entity = ChargingDiagnosticSensor(
            coordinator, entry, "status", *SENSORS["status"]
        )

        self.assertEqual(entity.entity_id, "sensor.slm_charger_status")

    def test_all_sensors_remain_readable_with_an_empty_coordinator_payload(self):
        fake_hass = SimpleNamespace(config=SimpleNamespace(language="nb"))
        coordinator = SimpleNamespace(data={}, last_update_success=True, entry=SimpleNamespace(data={}))
        for key in SENSORS:
            with self.subTest(sensor=key):
                entity = SimpleNamespace(
                    _key=key, coordinator=coordinator, hass=fake_hass
                )
                ChargingDiagnosticSensor.native_value.fget(entity)
                self.assertIn(
                    "explanation",
                    ChargingDiagnosticSensor.extra_state_attributes.fget(entity),
                )

    def test_sensor_exposes_a_localized_explanation(self):
        fake = SimpleNamespace(
            _key="charger_current",
            coordinator=SimpleNamespace(data={}),
            hass=SimpleNamespace(config=SimpleNamespace(language="nb")),
        )
        self.assertIn("Strømmen Easee måler", ChargingDiagnosticSensor.extra_state_attributes.fget(fake)["explanation"])

    def test_sensor_does_not_repeat_raw_charger_attributes(self):
        fake = SimpleNamespace(
            _key="charger_current",
            coordinator=SimpleNamespace(data={}),
            hass=SimpleNamespace(config=SimpleNamespace(language="nb")),
        )
        self.assertEqual(
            set(ChargingDiagnosticSensor.extra_state_attributes.fget(fake)),
            {"explanation"},
        )

    def test_power_sensor_displays_whole_watts(self):
        fake = SimpleNamespace(
            _key="charger_power",
            coordinator=SimpleNamespace(data={"charger_power_w": 3490.4}),
            hass=SimpleNamespace(config=SimpleNamespace(language="nb")),
        )
        self.assertEqual(ChargingDiagnosticSensor.native_value.fget(fake), 3490)

    def test_single_card_yaml_is_not_a_full_sections_view(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        card = (root / "examples/lovelace/charging_card.yaml").read_text()
        two = (root / "examples/lovelace/two_chargers_card.yaml").read_text()
        self.assertTrue(card.lstrip().startswith("#"))
        self.assertIn("type: vertical-stack", card)
        self.assertNotIn("type: sections", card)
        self.assertTrue(two.lstrip().startswith("#"))
        self.assertIn("type: vertical-stack", two)
        self.assertNotIn("type: sections", two)
        self.assertFalse((root / "examples/lovelace/charging_view.yaml").exists())

    def test_other_diagnostics_still_load_if_current_field_is_missing(self):
        data = {
            "electrical": {
                "phase_mode_name": "auto", "output_phase_name": "none",
                "active_phases": 0, "grid_type_name": "unknown",
                "voltage_type": "unknown", "line_voltage_v": None,
                "phase_neutral_voltage_v": None, "confidence": "low",
                "reason": "no phase data", "no_current_reason": "none",
            },
            "status": "disconnected", "minimum_current_a": None,
            "recommended_current_a": 0, "max_current_a": 16,
            "charger_power_w": 0, "han_power_w": 1000,
            "energy_used_kwh": 0, "energy_estimate_kwh": None,
            "control_reason": "disconnected", "auto_control": False,
            "han_age_seconds": 1, "han_fresh": True,
            "schedule_enabled": False, "schedule_reason": "off",
        }
        fake = SimpleNamespace(
            _key="status",
            coordinator=SimpleNamespace(data=data),
            hass=SimpleNamespace(config=SimpleNamespace(language="nb")),
        )

        self.assertEqual(
            ChargingDiagnosticSensor.native_value.fget(fake), "disconnected"
        )


if __name__ == "__main__":
    unittest.main()


class SensorConsolidationTests(unittest.IsolatedAsyncioTestCase):
    async def configured_sensors(self, second=False, legacy=False):
        from unittest.mock import patch
        from smart_load_manager.sensor import async_setup_entry
        from smart_load_manager.entity_ids import SENSOR_OBJECT_IDS
        from types import SimpleNamespace as NS
        coordinator=NS(data={},last_update_success=True)
        first=NS(entry_id='a', title='Driveway',data={},runtime_data=coordinator)
        other=NS(entry_id='b', title='Garage',data={'entity_suffix':'garage_123'},runtime_data=coordinator)
        entry=other if second else first
        coordinator.entry=entry
        hass=NS(config_entries=NS(async_entries=lambda domain:[first,other]))
        registry=NS(async_get_entity_id=lambda domain,platform,unique:
                    ('sensor.custom_name' if legacy and unique==entry.entry_id+'_ln_voltage' else None))
        sensors=[]
        with patch('smart_load_manager.sensor.er.async_get',return_value=registry):
            await async_setup_entry(hass,entry,sensors.extend)
        return sensors

    async def test_new_first_charger_has_six_sensors_and_two_shared_status_entities(self):
        sensors=await self.configured_sensors()
        self.assertEqual(len(sensors),9)
        shared=[s for s in sensors if s._key=='measurement_status']
        self.assertEqual(len(shared),1)
        household=next(s for s in sensors if s._key=='household_status')
        self.assertEqual(household.device_info['identifiers'],{('smart_load_manager','household')})
        self.assertEqual(shared[0].device_info['identifiers'],household.device_info['identifiers'])
        self.assertEqual(shared[0].entity_category.value,'diagnostic')

    async def test_new_second_charger_has_same_six_and_no_household_copies(self):
        from smart_load_manager.sensor import CHARGER_SENSOR_KEYS
        sensors=await self.configured_sensors(second=True)
        self.assertEqual({s._key for s in sensors},set(CHARGER_SENSOR_KEYS) | {"charging_role"})
        self.assertTrue(all(s.entity_id.endswith('_garage_123') for s in sensors))

    async def test_registered_legacy_sensor_is_retained_as_diagnostic(self):
        sensors=await self.configured_sensors(legacy=True)
        old=next(s for s in sensors if s._key=='ln_voltage')
        self.assertEqual(old.unique_id,'a_ln_voltage')
        self.assertEqual(old.entity_category.value,'diagnostic')
        self.assertNotIn('han_power',{s._key for s in sensors})

    async def test_attributes_are_attached_only_to_their_owner(self):
        from types import SimpleNamespace as NS
        data=dict(minimum_current_a=6,max_current_a=16,
                  electrical={'line_voltage_v':400,'confidence':'medium',
                              'phase_mode_name':'3_phase','no_current_reason':'none'},
                  han_age_seconds=12,han_fresh=True,inputs_valid=True,
                  auto_control=True,schedule_reason='Schedule is off')
        def attrs(key):
            entity=NS(_key=key,coordinator=NS(data=data,entry=NS(data={
                'han_power_entity':'sensor.actual_han','tariff_used_entity':'sensor.actual_used'})),
                hass=NS(config=NS(language='nb')))
            return ChargingDiagnosticSensor.extra_state_attributes.fget(entity)
        self.assertEqual(attrs('recommended_current')['minimum_current_a'],6)
        self.assertNotIn('line_voltage_v',attrs('recommended_current'))
        self.assertEqual(attrs('status')['line_voltage_v'],400)
        self.assertNotIn('minimum_current_a',attrs('status'))
        self.assertEqual(attrs('control_reason')['manual_control'],'locked')
        self.assertEqual(attrs('measurement_status')['han_age_seconds'],12)
        self.assertEqual(attrs('measurement_status')['energy_used_sensor'],'sensor.actual_used')
        self.assertNotIn('han_age_seconds',attrs('status'))

    async def test_household_summary_uses_one_complete_site_snapshot(self):
        from types import SimpleNamespace as NS
        owner=NS(entry_id='a',title='Smart Load Manager OJM – Driveway',data={},
                 options={'consumption_limit_kwh':10,'priority_charger':'b'})
        peer=NS(entry_id='b',title='Smart Load Manager OJM – Garage',data={},options={})
        payload=dict(status='charging',auto_control=True,inputs_valid=True,han_fresh=True,
                     site_control_ready=True,recommended_current_a=7,kw_per_amp=.23,
                     max_current_a=16,han_power_w=6000)
        a=NS(entry=owner,data={'status':'disconnected'},last_update_success=True)
        b=NS(entry=peer,data={'status':'disconnected'},last_update_success=True)
        a.site=NS(controllers={'a':a,'b':b},latest_samples={'a':payload,'b':dict(payload)})
        entity=NS(coordinator=a,hass=NS(config=NS(language='nb')))
        state,info=ChargingDiagnosticSensor._household_payload(entity)
        self.assertEqual(state,'automatic')
        self.assertEqual(info['priority_charger'],'Garage')
        self.assertEqual(info['han_power_w'],6000)
        self.assertEqual({r['status'] for r in info['controlled_loads']},{'charging'})

    async def test_shared_budget_uses_the_household_device(self):
        from smart_load_manager.select import ConsumptionLimitSelect
        from types import SimpleNamespace as NS
        entity=ConsumptionLimitSelect(NS(),NS(entry_id='owner',data={}))
        self.assertEqual(entity.device_info['identifiers'],{('smart_load_manager','household')})
        self.assertEqual(entity.device_info['name'],'SLM – Boligen')
