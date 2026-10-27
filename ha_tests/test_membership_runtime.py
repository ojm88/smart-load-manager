"""Actual HA setup -> add -> reload -> remove -> recover regressions."""

import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from homeassistant import loader
from homeassistant.config_entries import ConfigEntry, ConfigEntries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    frame,
    translation,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


class MembershipRuntimeTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = TemporaryDirectory()
        self.hass = HomeAssistant(self.tmp.name)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.hass.config.language = "nb"
        if hasattr(dr, "async_setup"):
            dr.async_setup(self.hass)
        await dr.async_load(self.hass)
        await er.async_load(self.hass)
        self.registry = er.async_get(self.hass)
        self.devices = dr.async_get(self.hass)
        root = Path(__file__).parents[1]
        Path(self.tmp.name, "custom_components").mkdir()
        os.symlink(
            root / "custom_components/smart_load_manager",
            Path(self.tmp.name, "custom_components/smart_load_manager"),
        )
        loader.async_setup(self.hass)
        frame.async_setup(self.hass)
        translation.async_setup(self.hass)
        import custom_components.smart_load_manager.config_flow as flow
        import custom_components.smart_load_manager.coordinator as coordinator
        from custom_components.smart_load_manager.site import get_site

        self.flow_module = flow
        self.shutdowns = []
        shutdowns = self.shutdowns

        class SyntheticCoordinator(DataUpdateCoordinator):
            def __init__(c, hass, entry):
                super().__init__(
                    hass, logging.getLogger(__name__), name="SLM synthetic"
                )
                c.entry = entry
                c.auto_control = False
                c.charging_paused = False
                c.schedule_enabled = bool(entry.options.get("schedule_enabled", False))
                c.last_commanded_current = None
                c._async_send_current = AsyncMock()
                c.site = get_site(hass)
                c.site.controllers[entry.entry_id] = c

            async def _async_update_data(c):
                # Exercise the saved adapter after membership changes too.
                assert c.entry.data["charger_device"]
                return {
                    "status": "disconnected",
                    "charger_power_w": 0,
                    "charger_current_a": 0,
                    "recommended_current_a": 0,
                    "max_current_a": 16,
                    "han_fresh": True,
                    "inputs_valid": True,
                    "site_control_ready": True,
                    "electrical": {"active_phases": 0, "line_voltage_v": 400},
                }

            async def async_shutdown(c):
                shutdowns.append(c)
                await super().async_shutdown()

        self.patches = [
            patch.object(coordinator, "ChargingCoordinator", SyntheticCoordinator),
            patch.object(flow, "resolve_easee_entities"),
        ]
        for p in self.patches:
            p.start()
        self.vendor = self.config_entry("easee", "vendor", {})
        self.a = self.devices.async_get_or_create(
            config_entry_id="vendor", identifiers={("easee", "first")}, name="Garage", manufacturer="Easee", model="Home"
        )
        self.b = self.devices.async_get_or_create(
            config_entry_id="vendor", identifiers={("easee", "second")}, name="Carport", manufacturer="Easee", model="Home"
        )
        self.record = flow._make_loads(self.hass, [self.a.id])[0]
        self.parent = self.config_entry(
            "smart_load_manager",
            "installation",
            {
                "household": {
                    "han_power_entity": "sensor.han",
                    "tariff_used_entity": "sensor.used",
                    "safety_margin_kwh": 0.3,
                },
                "loads": [self.record],
            },
            options={
                "site": {"consumption_limit_kwh": 8},
                "loads": {
                    self.record["id"]: {
                        "schedule_start_time": "02:00:00",
                        "schedule_enabled": True,
                    }
                },
            },
        )
        self.assertTrue(await self.hass.config_entries.async_setup("installation"))
        await self.hass.async_block_till_done()

    async def asyncTearDown(self):
        if self.parent.state.value == "loaded":
            await self.hass.config_entries.async_unload(self.parent.entry_id)
        await self.hass.async_stop(force=True)
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def config_entry(self, domain, identity, data, options=None):
        entry = ConfigEntry(
            domain=domain,
            entry_id=identity,
            version=2,
            minor_version=1,
            title=domain,
            source="user",
            unique_id=identity,
            data=data,
            options=options or {},
            discovery_keys={},
            subentries_data=[],
        )
        self.hass.config_entries._entries[identity] = entry
        return entry

    def flow(self):
        flow = self.flow_module.ChargerOptionsFlow()
        flow.hass = self.hass
        flow.handler = self.parent.entry_id
        return flow

    async def add_second(self):
        result = await self.flow().async_step_add_charger({"charger_device": self.b.id})
        self.assertEqual(result["type"], "create_entry")
        await self.hass.async_block_till_done()
        self.assertEqual(self.parent.state.value, "loaded")

    def assert_visible(self, record):
        for domain, key in [
            ("sensor", "charger_power"),
            ("sensor", "line_voltage"),
            ("switch", "automatic_control"),
        ]:
            identity = self.registry.async_get_entity_id(
                domain, "smart_load_manager", record["id"] + "_" + key
            )
            self.assertIsNotNone(identity)
            self.assertIsNone(self.registry.async_get(identity).disabled_by)
            self.assertNotEqual(self.hass.states.get(identity).state, "unavailable")
        status = self.hass.states.get("sensor.slm_status")
        self.assertIsNotNone(status)
        self.assertNotIn(status.state, {"unknown", "unavailable"})

    async def test_add_only_new_charger_preserves_first_and_native_status_through_reload(
        self,
    ):
        before_ids = {e.unique_id: e.entity_id for e in self.registry.entities.values()}
        old = self.parent.runtime_data.controllers[self.record["id"]]
        old_options = dict(self.parent.options["loads"][self.record["id"]])
        # An intentional user disable must survive every lifecycle operation.
        user_disabled = self.registry.async_get_entity_id(
            "sensor", "smart_load_manager", self.record["id"] + "_charger_current"
        )
        self.registry.async_update_entity(
            user_disabled, disabled_by=er.RegistryEntryDisabler.USER
        )
        await self.hass.async_block_till_done()
        await self.add_second()
        self.assertEqual(self.parent.data["loads"][0], self.record)
        self.assertEqual(len(self.parent.data["loads"]), 2)
        self.assertEqual(self.parent.options["loads"][self.record["id"]], old_options)
        self.assertEqual(self.parent.options["site"]["consumption_limit_kwh"], 8)
        for unique, entity_id in before_ids.items():
            self.assertEqual(
                self.registry.async_get_entity_id(
                    entity_id.split(".")[0], "smart_load_manager", unique
                ),
                entity_id,
            )
        for record in self.parent.data["loads"]:
            self.assert_visible(record)
        self.assertEqual(
            self.registry.async_get(user_disabled).disabled_by,
            er.RegistryEntryDisabler.USER,
        )
        self.assertIn(old, self.shutdowns)
        site = self.parent.runtime_data.controllers[self.record["id"]].site
        self.assertEqual(
            set(site.controllers), {r["id"] for r in self.parent.data["loads"]}
        )
        self.assertTrue(all(not c.auto_control for c in site.controllers.values()))
        # A further ordinary reload must keep the restored measurements available.
        self.assertTrue(
            await self.hass.config_entries.async_reload(self.parent.entry_id)
        )
        await self.hass.async_block_till_done()
        for record in self.parent.data["loads"]:
            self.assert_visible(record)

    async def test_explicit_removal_cleans_actual_old_runtime_and_readd_recovers_same_identity(
        self,
    ):
        await self.add_second()
        old = self.parent.runtime_data.controllers[self.record["id"]]
        # This pending bookkeeping must not survive the old controller.
        site = old.site
        site.pending_reductions[self.record["id"]] = (0, 1)
        site.manual_requests[self.record["id"]] = 6
        site.latest_samples[self.record["id"]] = {"status": "disconnected"}
        result = await self.flow().async_step_remove_charger(
            {"charger_device": self.a.id}
        )
        self.assertEqual(result["type"], "create_entry")
        # The old adapter remains valid until HA completes native unload.
        self.assertEqual(old.entry.data["charger_device"], self.a.id)
        await self.hass.async_block_till_done()
        self.assertEqual(len(self.parent.data["loads"]), 1)
        old._async_send_current.assert_awaited_once_with(0)
        self.assertIn(old, self.shutdowns)
        self.assertNotIn(self.record["id"], site.controllers)
        self.assertNotIn(self.record["id"], site.pending_reductions)
        self.assertNotIn(self.record["id"], site.manual_requests)
        self.assertNotIn(self.record["id"], site.latest_samples)
        self.assert_visible(self.parent.data["loads"][0])
        result = await self.flow().async_step_add_charger({"charger_device": self.a.id})
        self.assertEqual(result["type"], "create_entry")
        await self.hass.async_block_till_done()
        self.assertIn(self.record, self.parent.data["loads"])
        for record in self.parent.data["loads"]:
            self.assert_visible(record)
        self.assertEqual(
            self.parent.options["loads"][self.record["id"]]["schedule_start_time"],
            "02:00:00",
        )

    async def test_add_form_excludes_configured_and_non_easee_devices_without_sensor_probes(
        self,
    ):
        # Same-name SLM devices must never be selectable as the Easee source.
        self.devices.async_get_or_create(
            config_entry_id=self.parent.entry_id,
            identifiers={("slm", "copy")},
            name="Garage",
        )
        for i in range(100):
            self.devices.async_get_or_create(
                config_entry_id=self.parent.entry_id,
                identifiers={("test", str(i))},
                name=f"Other {i}",
            )
        with patch.object(
            self.flow_module,
            "resolve_easee_entities",
            side_effect=AssertionError("Opening a dropdown must not probe sensors"),
        ):
            result = await self.flow().async_step_add_charger()
        field = next(iter(result["data_schema"].schema.values()))
        self.assertEqual(field.selector_type, "device")
        self.assertTrue(field.config["multiple"])
        self.assertEqual(field.config["filter"], [{"manufacturer": "Easee", "model": "Home"}])
        self.assertEqual(next(iter(result["data_schema"].schema)).default(), [self.a.id])
        self.assertEqual(
            [r["id"] for r in self.parent.data["loads"]], [self.record["id"]]
        )

    async def test_stale_or_already_configured_add_is_rejected_without_changes(self):
        original = dict(self.parent.data)
        for bad in [self.a.id, "not_a_device"]:
            result = await self.flow().async_step_add_charger({"charger_device": bad})
            self.assertEqual(result["type"], "form")
            self.assertTrue(result["errors"])
            self.assertEqual(dict(self.parent.data), original)
        await self.add_second()
        result = await self.flow().async_step_add_charger({"charger_device": self.a.id})
        self.assertEqual(result["type"], "abort")
        self.assertEqual(result["reason"], "two_chargers")

    async def test_failed_zero_command_does_not_remove_any_charger_or_settings(self):
        await self.add_second()
        original = dict(self.parent.data)
        controller = self.parent.runtime_data.controllers[self.record["id"]]
        controller.auto_control = True
        controller._async_send_current.side_effect = ValueError("zero command failed")
        result = await self.flow().async_step_remove_charger(
            {"charger_device": self.a.id}
        )
        self.assertEqual(result["type"], "form")
        self.assertIn(
            "zero command failed",
            result["description_placeholders"]["validation_error"],
        )
        self.assertEqual(dict(self.parent.data), original)
        self.assertTrue(controller.auto_control)

    async def test_cancelled_add_and_invalid_voltage_leave_first_running_and_unchanged(
        self,
    ):
        original = dict(self.parent.data)
        before = self.parent.runtime_data.controllers[self.record["id"]]
        await self.flow().async_step_add_charger()
        self.assertIs(self.parent.runtime_data.controllers[self.record["id"]], before)
        with patch.object(
            self.flow_module,
            "resolve_easee_entities",
            side_effect=ValueError("Enable voltage"),
        ):
            result = await self.flow().async_step_add_charger(
                {"charger_device": self.b.id}
            )
        self.assertIn(
            "Enable voltage", result["description_placeholders"]["validation_error"]
        )
        self.assertEqual(dict(self.parent.data), original)
        self.assert_visible(self.record)

    async def begin_fresh_wizard(self):
        self.assertTrue(
            await self.hass.config_entries.async_unload(self.parent.entry_id)
        )
        await self.hass.config_entries.async_remove(self.parent.entry_id)
        self.hass.states.async_set("sensor.han", "1200", {"unit_of_measurement": "W"})
        self.hass.states.async_set("sensor.used", "2", {"unit_of_measurement": "kWh"})
        result = await self.hass.config_entries.flow.async_init(
            "smart_load_manager", context={"source": "user"}
        )
        fid = result["flow_id"]
        self.assertEqual(result["step_id"], "household")
        result = await self.hass.config_entries.flow.async_configure(
            fid,
            {
                "han_power_entity": "sensor.han",
                "tariff_used_entity": "sensor.used",
                "safety_margin_kwh": 0.3,
            },
        )
        self.assertEqual(result["menu_options"], ["charging", "planned"])
        result = await self.hass.config_entries.flow.async_configure(
            fid, {"next_step_id": "charging"}
        )
        self.assertEqual(result["step_id"], "charging")
        field = next(iter(result["data_schema"].schema.values()))
        self.assertEqual(field.selector_type, "device")
        self.assertEqual(field.config["filter"], [{"manufacturer": "Easee", "model": "Home"}])
        self.assertFalse(field.config["multiple"])
        return fid

    async def test_actual_initial_wizard_filters_second_and_keeps_first_until_commit(
        self,
    ):
        fid = await self.begin_fresh_wizard()
        result = await self.hass.config_entries.flow.async_configure(
            fid, {"charger_device": self.a.id}
        )
        self.assertEqual(result["type"], "menu")
        self.assertEqual(
            self.hass.config_entries.async_entries("smart_load_manager"), []
        )
        result = await self.hass.config_entries.flow.async_configure(
            fid, {"next_step_id": "second_charger"}
        )
        field = next(iter(result["data_schema"].schema.values()))
        self.assertTrue(field.config["multiple"])
        self.assertEqual(next(iter(result["data_schema"].schema)).default(), [self.a.id])
        result = await self.hass.config_entries.flow.async_configure(
            fid, {"charger_device": [self.a.id, self.b.id]}
        )
        self.assertEqual(result["type"], "create_entry")
        self.parent = result["result"]
        await self.hass.async_block_till_done()
        self.assertEqual(self.parent.state.value, "loaded")
        self.assertEqual(
            [r["data"]["charger_device"] for r in self.parent.data["loads"]],
            [self.a.id, self.b.id],
        )
        for record in self.parent.data["loads"]:
            self.assert_visible(record)

    async def test_actual_wizard_finish_one_or_cancel_never_creates_partial_entry(self):
        fid = await self.begin_fresh_wizard()
        await self.hass.config_entries.flow.async_configure(
            fid, {"charger_device": self.a.id}
        )
        self.hass.config_entries.flow.async_abort(fid)
        self.assertEqual(
            self.hass.config_entries.async_entries("smart_load_manager"), []
        )
        # Restart the wizard and intentionally finish with one charger.
        result = await self.hass.config_entries.flow.async_init(
            "smart_load_manager", context={"source": "user"}
        )
        fid = result["flow_id"]
        await self.hass.config_entries.flow.async_configure(
            fid,
            {
                "han_power_entity": "sensor.han",
                "tariff_used_entity": "sensor.used",
                "safety_margin_kwh": 0.3,
            },
        )
        await self.hass.config_entries.flow.async_configure(
            fid, {"next_step_id": "charging"}
        )
        await self.hass.config_entries.flow.async_configure(
            fid, {"charger_device": self.a.id}
        )
        result = await self.hass.config_entries.flow.async_configure(
            fid, {"next_step_id": "finish_charging"}
        )
        self.parent = result["result"]
        await self.hass.async_block_till_done()
        self.assertEqual(len(self.parent.data["loads"]), 1)
        self.assert_visible(self.parent.data["loads"][0])

    async def test_cloud_url_setup_stays_in_native_dialog_and_keeps_both_choices(self):
        self.hass.config.external_url = "https://cloud.example.test"
        with patch.object(self.flow_module.SmartLoadManagerConfigFlow, 'async_external_step', side_effect=AssertionError('Setup must stay in-app')):
            fid = await self.begin_fresh_wizard()
            result = await self.hass.config_entries.flow.async_configure(fid, {'charger_device': self.a.id})
            self.assertEqual(result['type'], 'menu')
            self.assertNotIn('url', result)
            result = await self.hass.config_entries.flow.async_configure(fid, {'next_step_id': 'second_charger'})
            self.assertEqual(result['type'], 'form')
            field = next(iter(result['data_schema'].schema.values()))
            self.assertTrue(field.config['multiple'])
            self.assertEqual(next(iter(result['data_schema'].schema)).default(), [self.a.id])
            result = await self.hass.config_entries.flow.async_configure(fid, {'charger_device': [self.a.id, self.b.id]})
        self.parent = result['result']
        await self.hass.async_block_till_done()
        self.assertEqual([r['data']['charger_device'] for r in self.parent.data['loads']], [self.a.id, self.b.id])
        for record in self.parent.data['loads']:
            self.assert_visible(record)

    async def test_cloud_url_add_stays_in_native_dialog_and_preserves_existing(self):
        self.hass.config.external_url = "https://cloud.example.test"
        manager = self.hass.config_entries.options
        result = await manager.async_init(self.parent.entry_id)
        fid = result['flow_id']
        result = await manager.async_configure(fid, {'next_step_id': 'chargers'})
        self.assertEqual(result['menu_options'], ['add_charger'])
        with patch.object(self.flow_module.ChargerOptionsFlow, 'async_external_step', side_effect=AssertionError('Add must stay in-app')):
            result = await manager.async_configure(fid, {'next_step_id': 'add_charger'})
            self.assertEqual(result['type'], 'form')
            self.assertNotIn('url', result)
            field = next(iter(result['data_schema'].schema.values()))
            self.assertTrue(field.config['multiple'])
            self.assertEqual(next(iter(result['data_schema'].schema)).default(), [self.a.id])
            from homeassistant.helpers.data_entry_flow import FlowManagerIndexView
            packet = FlowManagerIndexView(manager)._prepare_result_json(result)
            field_packet = packet['data_schema'][0]
            self.assertEqual(field_packet['default'], [self.a.id])
            self.assertTrue(field_packet['selector']['device']['multiple'])
            self.assertEqual(field_packet['selector']['device']['filter'], [{'manufacturer': 'Easee', 'model': 'Home'}])
            await manager.async_configure(fid, {'charger_device': [self.a.id, self.b.id]})
        await self.hass.async_block_till_done()
        self.assertEqual(self.parent.data['loads'][0], self.record)
        self.assertEqual(len(self.parent.data['loads']), 2)
        for record in self.parent.data['loads']:
            self.assert_visible(record)

    async def test_native_picker_metadata_fallback_and_model_filters(self):
        filters = self.flow_module._native_charger_filter(self.hass)
        self.assertEqual(filters, [{'manufacturer': 'Easee', 'model': 'Home'}])
        self.devices.async_update_device(self.b.id, model='Charge Up')
        self.assertEqual(self.flow_module._native_charger_filter(self.hass), [
            {'manufacturer': 'Easee', 'model': 'Charge Up'},
            {'manufacturer': 'Easee', 'model': 'Home'},
        ])
        self.devices.async_update_device(self.b.id, manufacturer=None)
        self.assertEqual(self.flow_module._native_charger_filter(self.hass), [{'integration': 'easee'}])

    async def test_native_add_rejects_replacement_duplicates_and_extra_choices(self):
        original = dict(self.parent.data)
        for selected in ([self.b.id], [self.a.id], [self.a.id, self.b.id, self.b.id],
                         [self.a.id, self.b.id, 'unknown'], [self.a.id, 'unknown']):
            result = await self.flow().async_step_add_charger({'charger_device': selected})
            self.assertEqual(result['type'], 'form')
            self.assertEqual(result['errors'], {'base': 'invalid_setup'})
            self.assertEqual(dict(self.parent.data), original)
            self.assert_visible(self.record)

    async def test_native_initial_rejects_non_easee_with_same_manufacturer_and_model(self):
        rogue = self.devices.async_get_or_create(
            config_entry_id=self.parent.entry_id, identifiers={('test', 'not-easee')},
            manufacturer='Easee', model='Home', name='Other source',
        )
        # A matching presentation filter is not authorization to become a source.
        flow = self.flow_module.SmartLoadManagerConfigFlow()
        flow.hass = self.hass
        flow.context = {'source': 'user'}
        result = await flow.async_step_charging({'charger_device': rogue.id})
        self.assertEqual(result['type'], 'form')
        self.assertEqual(result['errors'], {'base': 'invalid_setup'})
        self.assertEqual(len(self.parent.data['loads']), 1)

    async def test_native_add_list_cannot_accept_non_easee_matching_metadata(self):
        rogue = self.devices.async_get_or_create(
            config_entry_id=self.parent.entry_id, identifiers={('test', 'matching-model')},
            manufacturer='Easee', model='Home', name='Matching model',
        )
        original = dict(self.parent.data)
        result = await self.flow().async_step_add_charger({'charger_device': [self.a.id, rogue.id]})
        self.assertEqual(result['errors'], {'base': 'invalid_setup'})
        self.assertEqual(dict(self.parent.data), original)
