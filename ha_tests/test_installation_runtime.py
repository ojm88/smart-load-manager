"""Real HA registry migration and installation lifecycle acceptance checks."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigEntries
from homeassistant.helpers import entity_registry as er, device_registry as dr
from smart_load_manager import async_migrate_entry
from smart_load_manager.installation import (
    charger_entries,
    update_load,
    group_id,
    reconcile_pair_entities,
)
from smart_load_manager.entity_ids import migrate_entity_ids
from smart_load_manager.switch import ChargingPriorityControl
from smart_load_manager.sensor import ChargingDiagnosticSensor, SENSORS


class InstallationTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = TemporaryDirectory()
        self.hass = HomeAssistant(self.tmp.name)
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.hass.config.language = "nb"
        from homeassistant.helpers import frame

        frame.async_setup(self.hass)
        if hasattr(dr, "async_setup"):
            dr.async_setup(self.hass)
        await dr.async_load(self.hass)
        await er.async_load(self.hass)
        self.registry = er.async_get(self.hass)
        self.devices = dr.async_get(self.hass)

    async def asyncTearDown(self):
        await self.hass.async_stop(force=True)
        self.tmp.cleanup()

    def entry(self, identity, name, suffix=""):
        e = ConfigEntry(
            domain="smart_load_manager",
            entry_id=identity,
            version=1,
            minor_version=1,
            title="Smart Load Manager OJM – " + name,
            source="user",
            unique_id=identity,
            data={
                "charger_device": identity + "_device",
                "electrical_connection": "tn_3",
                "charger_name": name,
                "entity_suffix": suffix,
                "han_power_entity": "sensor.han",
                "tariff_used_entity": "sensor.used",
                "safety_margin_kwh": 0.3,
            },
            options={
                "consumption_limit_kwh": 10,
                "schedule_start_time": "02:00:00",
                "priority_charger": "b",
            },
            discovery_keys={},
            subentries_data=[],
        )
        self.hass.config_entries._entries[e.entry_id] = e
        return e

    async def migrate(self, entries):
        # Actual entity/device registries, with external entry removal isolated.
        # This records which entities would be removed with the old entry.
        async def remove(key):
            self.assertFalse(er.async_entries_for_config_entry(self.registry, key))
            del self.hass.config_entries._entries[key]
            return {"require_restart": False}

        with patch.object(self.hass.config_entries, "async_remove", side_effect=remove):
            await async_migrate_entry(self.hass, entries[0])

    async def test_beta4_consolidation_preserves_unique_ids_preferences_and_history_identity(
        self,
    ):
        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123456")
        for entry in [a, b]:
            device = self.devices.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={("smart_load_manager", entry.entry_id)},
                name=entry.title,
            )
            self.registry.async_get_or_create(
                "sensor",
                "smart_load_manager",
                entry.entry_id + "_charger_current",
                config_entry=entry,
                device_id=device.id,
                suggested_object_id="slm_charger_current"
                + ("_tesla_123456" if entry is b else ""),
            )
        custom = self.registry.async_get_or_create(
            "sensor",
            "smart_load_manager",
            "b_charger_power",
            config_entry=b,
            suggested_object_id="my_custom_power",
            disabled_by=er.RegistryEntryDisabler.USER,
        )
        self.registry.async_update_entity(custom.entity_id, name="My power")
        self.registry.async_get_or_create(
            "sensor",
            "smart_load_manager",
            "a_household_status",
            config_entry=a,
            suggested_object_id="slm_status",
        )
        await self.migrate([a, b])
        self.assertEqual(
            len(self.hass.config_entries.async_entries("smart_load_manager")), 1
        )
        self.assertEqual(a.version, 2)
        loads = charger_entries(self.hass)
        self.assertEqual([e.entry_id for e in loads], ["a", "b"])
        self.assertEqual(loads[1].options["schedule_start_time"], "02:00:00")
        self.assertEqual(
            {s.title for s in a.subentries.values()}, {"Boligen", "Lading"}
        )
        for load in loads:
            migrate_entity_ids(self.hass, load)
        self.assertEqual(
            self.registry.async_get_entity_id(
                "sensor", "smart_load_manager", "a_charger_current"
            ),
            "sensor.slm_charger_current_garasje",
        )
        self.assertEqual(
            self.registry.async_get_entity_id(
                "sensor", "smart_load_manager", "b_charger_current"
            ),
            "sensor.slm_charger_current_tesla",
        )
        saved = self.registry.async_get("sensor.my_custom_power")
        self.assertEqual(saved.name, "My power")
        self.assertEqual(saved.disabled_by, er.RegistryEntryDisabler.USER)
        self.assertEqual(saved.config_entry_id, "a")
        self.assertEqual(saved.config_subentry_id, group_id(a, "charging"))
        household = self.registry.async_get("sensor.slm_status")
        self.assertEqual(household.config_subentry_id, group_id(a, "household"))
        # Idempotent after restart, with no new identities or entity IDs.
        await self.migrate([a])
        for load in charger_entries(self.hass):
            migrate_entity_ids(self.hass, load)
        self.assertEqual(len(a.subentries), 2)
        self.assertEqual(len(self.registry.entities), 4)

    async def test_shared_sources_and_budget_survive_primary_charger_removal(self):
        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123")
        await self.migrate([a, b])
        first, second = charger_entries(self.hass)
        update_load(
            self.hass,
            first,
            options={
                **first.options,
                "consumption_limit_kwh": 8,
                "allocation_mode": "one_at_a_time",
            },
        )
        self.hass.config_entries.async_update_entry(
            a,
            data={
                **a.data,
                "loads": a.data["loads"][1:],
                "household": {
                    **a.data["household"],
                    "han_power_entity": "sensor.new_han",
                },
            },
        )
        remaining = charger_entries(self.hass)[0]
        self.assertEqual(remaining.data["han_power_entity"], "sensor.new_han")
        self.assertEqual(remaining.options["consumption_limit_kwh"], 8)
        self.assertEqual(remaining.options["allocation_mode"], "one_at_a_time")
        self.assertEqual(remaining.options["schedule_start_time"], "02:00:00")

    async def test_priority_toggles_always_complementary_and_roles_agree(self):
        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123")
        await self.migrate([a, b])
        loads = charger_entries(self.hass)
        controllers = {
            e.entry_id: NS(
                entry=e,
                hass=self.hass,
                data={},
                async_request_refresh=AsyncMock(),
                async_update_listeners=lambda: None,
            )
            for e in loads
        }
        for c in controllers.values():
            c.site = NS(controllers=controllers)
        switches = []
        roles = []
        for e in loads:
            sw = ChargingPriorityControl(controllers[e.entry_id], e)
            sw.hass = self.hass
            switches.append(sw)
            role = ChargingDiagnosticSensor(
                controllers[e.entry_id], e, "charging_role", *SENSORS["charging_role"]
            )
            role.hass = self.hass
            roles.append(role)
        self.assertEqual([s.is_on for s in switches], [False, True])
        await switches[0].async_turn_on()
        self.assertEqual([s.is_on for s in switches], [True, False])
        self.assertEqual([s.native_value for s in roles], ["primary", "secondary"])
        await switches[0].async_turn_off()
        self.assertEqual([s.is_on for s in switches], [False, True])
        self.assertEqual(switches[0].name, "Førsteprioritet Garasje")

    async def test_pair_controls_disable_and_restore_without_touching_user_disabled_state(
        self,
    ):
        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123")
        await self.migrate([a, b])
        for key, disabled in [
            ("a_allocation_mode", None),
            ("a_charging_priority", er.RegistryEntryDisabler.USER),
        ]:
            self.registry.async_get_or_create(
                "switch",
                "smart_load_manager",
                key,
                config_entry=a,
                suggested_object_id=key,
                disabled_by=disabled,
            )
        records = a.data["loads"]
        self.hass.config_entries.async_update_entry(
            a, data={**a.data, "loads": records[:1]}
        )
        reconcile_pair_entities(self.hass, a)
        self.assertEqual(
            self.registry.async_get("switch.a_allocation_mode").disabled_by,
            er.RegistryEntryDisabler.INTEGRATION,
        )
        self.hass.config_entries.async_update_entry(
            a, data={**a.data, "loads": records}
        )
        reconcile_pair_entities(self.hass, a)
        self.assertIsNone(
            self.registry.async_get("switch.a_allocation_mode").disabled_by
        )
        self.assertEqual(
            self.registry.async_get("switch.a_charging_priority").disabled_by,
            er.RegistryEntryDisabler.USER,
        )

    async def test_household_first_flow_validates_both_chargers_before_creating_entry(
        self,
    ):
        from smart_load_manager.config_flow import SmartLoadManagerConfigFlow

        flow = SmartLoadManagerConfigFlow()
        flow.hass = self.hass
        flow.context = {"source": "user"}
        first = await flow.async_step_user()
        self.assertEqual(first["step_id"], "household")
        self.hass.states.async_set("sensor.han", "1200", {"unit_of_measurement": "W"})
        self.hass.states.async_set("sensor.used", "2.5", {"unit_of_measurement": "kWh"})
        data = {
            "han_power_entity": "sensor.han",
            "tariff_used_entity": "sensor.used",
            "safety_margin_kwh": 0.3,
        }
        menu = await flow.async_step_household(data)
        self.assertEqual(menu["menu_options"], ["charging", "planned"])
        self.assertEqual(
            self.hass.config_entries.async_entries("smart_load_manager"), []
        )
        invalid = await flow.async_step_charging({"charger_device": None})
        self.assertEqual(invalid["errors"], {"base": "invalid_setup"})
        self.assertEqual(
            self.hass.config_entries.async_entries("smart_load_manager"), []
        )
        with patch(
            "smart_load_manager.config_flow.resolve_easee_entities",
            side_effect=ValueError("Enable sensor.garage_voltage"),
        ):
            result = await flow.async_step_charging({"charger_device": "garage", "electrical_connection": "tn_3"})
        self.assertIn(
            "Enable sensor.garage_voltage",
            result["description_placeholders"]["validation_error"],
        )

    async def test_household_options_are_atomic_and_do_not_reset_load_settings(self):
        from smart_load_manager.config_flow import ChargerOptionsFlow

        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123")
        await self.migrate([a, b])
        before_options = dict(a.options)
        self.hass.states.async_set("sensor.han", "2000", {"unit_of_measurement": "W"})
        self.hass.states.async_set("sensor.used", "nan", {"unit_of_measurement": "kWh"})
        flow = ChargerOptionsFlow()
        flow.hass = self.hass
        flow.handler = "a"
        data = {
            "han_power_entity": "sensor.han",
            "tariff_used_entity": "sensor.used",
            "safety_margin_kwh": 0.5,
        }
        bad = await flow.async_step_household(data)
        self.assertEqual(bad["errors"], {"base": "invalid_setup"})
        self.assertEqual(a.data["household"]["safety_margin_kwh"], 0.3)
        self.hass.states.async_set("sensor.used", "2", {"unit_of_measurement": "kWh"})
        valid = await flow.async_step_household(data)
        self.assertEqual(valid["type"], "create_entry")
        self.assertEqual(a.data["household"]["safety_margin_kwh"], 0.5)
        self.assertEqual(a.options, before_options)
        self.assertEqual(charger_entries(self.hass)[1].data["safety_margin_kwh"], 0.5)
        menu = await flow.async_step_init()
        self.assertEqual(menu["menu_options"], ["household", "chargers"])

    async def test_setup_one_and_two_loads_uses_native_groups_without_duplicate_budget(
        self,
    ):
        from smart_load_manager import sensor, select, switch, number
        from smart_load_manager import time as times

        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123")
        await self.migrate([a, b])

        async def check(count):
            calls = []
            controllers = {
                e.entry_id: NS(
                    entry=e, hass=self.hass, data={}, last_update_success=True
                )
                for e in charger_entries(self.hass)
            }
            a.runtime_data = NS(controllers=controllers)

            def add(entities, **kw):
                calls.extend((e, kw["config_subentry_id"]) for e in entities)

            for platform in [sensor, select, switch, number, times]:
                await platform.async_setup_entry(self.hass, a, add)
            household = [e for e, g in calls if g == group_id(a, "household")]
            self.assertEqual(
                len([e for e in household if e.translation_key == "consumption_limit"]),
                1,
            )
            self.assertEqual(
                len([e for e in calls if e[0].translation_key == "charging_priority"]),
                2 if count == 2 else 0,
            )
            self.assertEqual(
                len([e for e in calls if e[0].translation_key == "allocation_mode"]),
                1 if count == 2 else 0,
            )
            volts = [e for e, g in calls if e.translation_key == "line_voltage"]
            self.assertEqual(len(volts), count)
            self.assertEqual(volts[0].name, "Volt Garasje")
            shared = next(
                e for e in household if e.translation_key == "household_status"
            )
            self.assertEqual(shared.unique_id, "a_household_status")

        await check(2)
        self.hass.config_entries.async_update_entry(
            a, data={**a.data, "loads": a.data["loads"][:1]}
        )
        await check(1)

    async def test_suffix_collision_and_saved_identity_survive_device_rename(self):
        from smart_load_manager.config_flow import _make_loads

        devices = NS(
            devices={
                "d1": NS(name_by_user=None, name="Garage"),
                "d2": NS(name_by_user=None, name="Garage"),
            }
        )
        with (
            patch("smart_load_manager.config_flow.dr.async_get", return_value=devices),
            patch("smart_load_manager.config_flow.resolve_easee_entities"),
        ):
            records = _make_loads(self.hass, ["d1", "d2"])
            self.assertEqual(records[0]["data"]["entity_suffix"], "garage")
            self.assertEqual(records[1]["data"]["entity_suffix"], "garage_d2")
            devices.devices["d1"].name = "New name"
            again = _make_loads(self.hass, ["d2", "d1"], records)
            self.assertEqual(again, records)

    async def test_native_ha_platform_startup_registers_both_groups_and_unloads(self):
        """Actual HA platform/entity setup, with synthetic telemetry only."""
        import os
        from homeassistant import loader
        from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
        import logging

        root = Path(__file__).parents[1]
        Path(self.tmp.name, "custom_components").mkdir(exist_ok=True)
        os.symlink(
            root / "custom_components/smart_load_manager",
            Path(self.tmp.name, "custom_components/smart_load_manager"),
        )
        loader.async_setup(self.hass)
        from homeassistant.helpers import frame, translation

        frame.async_setup(self.hass)
        translation.async_setup(self.hass)
        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123")
        await self.migrate([a, b])

        class FakeCoordinator(DataUpdateCoordinator):
            def __init__(c, hass, entry):
                super().__init__(hass, logging.getLogger(__name__), name="SLM test")
                c.entry = entry
                c.auto_control = False
                c.charging_paused = False
                c.schedule_enabled = False
                c.last_commanded_current = None
                c.site = NS(controllers={}, latest_samples={})

            async def _async_update_data(c):
                return {
                    "status": "disconnected",
                    "charger_power_w": 0,
                    "charger_current_a": 0,
                    "recommended_current_a": 0,
                    "max_current_a": 16,
                    "han_fresh": True,
                    "inputs_valid": True,
                    "electrical": {"active_phases": 0, "line_voltage_v": 400},
                }

        import custom_components.smart_load_manager.coordinator as coordinator_module

        with patch.object(coordinator_module, "ChargingCoordinator", FakeCoordinator):
            result = await self.hass.config_entries.async_setup(a.entry_id)
            await self.hass.async_block_till_done()
        self.assertTrue(
            result, f"{a.state}: {a.reason}; {a.error_reason_translation_key}"
        )
        self.assertEqual(a.state.value, "loaded")
        currents = [
            e
            for e in self.registry.entities.values()
            if e.unique_id.endswith("_charger_current")
        ]
        self.assertEqual(len(currents), 2)
        self.assertEqual(
            {e.config_subentry_id for e in currents}, {group_id(a, "charging")}
        )
        self.assertEqual(
            float(self.hass.states.get("sensor.slm_line_voltage_garasje").state), 400
        )
        self.assertEqual(
            self.hass.states.get("sensor.slm_line_voltage_garasje").attributes[
                "friendly_name"
            ],
            "Volt Garasje",
        )
        self.assertIsNotNone(self.hass.states.get("sensor.slm_status"))
        card = await self.hass.services.async_call(
            "smart_load_manager",
            "get_dashboard",
            {},
            blocking=True,
            return_response=True,
        )
        self.assertNotIn("CHARGER_SUFFIX", card["yaml"])
        self.assertIn("sensor.slm_line_voltage_garasje", card["yaml"])
        self.assertTrue(await self.hass.config_entries.async_unload(a.entry_id))

    async def test_concurrent_beta4_startup_migrates_and_removes_old_peer(self):
        """Actual HA platform/entity setup, with synthetic telemetry only."""
        import os
        from homeassistant import loader
        from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
        import logging

        root = Path(__file__).parents[1]
        Path(self.tmp.name, "custom_components").mkdir(exist_ok=True)
        os.symlink(
            root / "custom_components/smart_load_manager",
            Path(self.tmp.name, "custom_components/smart_load_manager"),
        )
        loader.async_setup(self.hass)
        from homeassistant.helpers import frame, translation

        frame.async_setup(self.hass)
        translation.async_setup(self.hass)
        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123")

        class FakeCoordinator(DataUpdateCoordinator):
            def __init__(c, hass, entry):
                super().__init__(hass, logging.getLogger(__name__), name="SLM test")
                c.entry = entry
                c.auto_control = False
                c.charging_paused = False
                c.schedule_enabled = False
                c.last_commanded_current = None
                c.site = NS(controllers={}, latest_samples={})

            async def _async_update_data(c):
                return {
                    "status": "disconnected",
                    "charger_power_w": 0,
                    "charger_current_a": 0,
                    "recommended_current_a": 0,
                    "max_current_a": 16,
                    "han_fresh": True,
                    "inputs_valid": True,
                    "electrical": {"active_phases": 0, "line_voltage_v": 400},
                }

        import custom_components.smart_load_manager.coordinator as coordinator_module

        with patch.object(coordinator_module, "ChargingCoordinator", FakeCoordinator):
            results = await asyncio.wait_for(
                asyncio.gather(
                    self.hass.config_entries.async_setup(a.entry_id),
                    self.hass.config_entries.async_setup(b.entry_id),
                ),
                10,
            )
            result = results[0]
            await self.hass.async_block_till_done()
        self.assertTrue(
            result, f"{a.state}: {a.reason}; {a.error_reason_translation_key}"
        )
        self.assertEqual(a.state.value, "loaded")
        currents = [
            e
            for e in self.registry.entities.values()
            if e.unique_id.endswith("_charger_current")
        ]
        self.assertEqual(len(currents), 2)
        self.assertEqual(
            {e.config_subentry_id for e in currents}, {group_id(a, "charging")}
        )
        self.assertEqual(
            float(self.hass.states.get("sensor.slm_line_voltage_garasje").state), 400
        )
        self.assertEqual(
            self.hass.states.get("sensor.slm_line_voltage_garasje").attributes[
                "friendly_name"
            ],
            "Volt Garasje",
        )
        self.assertIsNotNone(self.hass.states.get("sensor.slm_status"))
        card = await self.hass.services.async_call(
            "smart_load_manager",
            "get_dashboard",
            {},
            blocking=True,
            return_response=True,
        )
        self.assertNotIn("CHARGER_SUFFIX", card["yaml"])
        self.assertIn("sensor.slm_line_voltage_garasje", card["yaml"])
        self.assertTrue(await self.hass.config_entries.async_unload(a.entry_id))

    async def test_real_coordinators_load_native_platforms_from_synthetic_measurements(
        self,
    ):
        """Actual HA platform/entity setup, with synthetic telemetry only."""
        import os
        from homeassistant import loader

        root = Path(__file__).parents[1]
        Path(self.tmp.name, "custom_components").mkdir(exist_ok=True)
        os.symlink(
            root / "custom_components/smart_load_manager",
            Path(self.tmp.name, "custom_components/smart_load_manager"),
        )
        loader.async_setup(self.hass)
        from homeassistant.helpers import frame, translation

        frame.async_setup(self.hass)
        translation.async_setup(self.hass)
        a = self.entry("a", "Garasje")
        b = self.entry("b", "Tesla", "tesla_123")
        await self.migrate([a, b])
        from smart_load_manager.entity_resolution import EaseeEntities

        for key in ["a", "b"]:
            self.hass.states.async_set(
                "sensor." + key + "_status",
                "charging",
                {
                    "state_outputPhase": 30,
                    "config_phaseMode": 3,
                    "config_detectedPowerGridType": 1,
                    "circuit_ratedCurrent": 16,
                },
            )
            self.hass.states.async_set(
                "sensor." + key + "_current",
                6,
                {
                    "state_inCurrentT2": 0,
                    "state_inCurrentT3": 6,
                    "state_inCurrentT4": 6,
                    "state_inCurrentT5": 6,
                },
            )
            self.hass.states.async_set(
                "sensor." + key + "_voltage",
                400,
                {
                    "state_inVoltageT3T4": 400,
                    "state_inVoltageT4T5": 400,
                    "state_inVoltageT5T3": 400,
                    "state_inVoltageT2T3": 230,
                    "state_inVoltageT2T4": 230,
                    "state_inVoltageT2T5": 230,
                },
            )
            self.hass.states.async_set(
                "sensor." + key + "_power", 4157, {"unit_of_measurement": "W"}
            )
        self.hass.states.async_set("sensor.han", 10000, {"unit_of_measurement": "W"})
        self.hass.states.async_set("sensor.used", 2, {"unit_of_measurement": "kWh"})

        def resolve(hass, device):
            key = device.split("_")[0]
            return EaseeEntities(
                status="sensor." + key + "_status",
                current="sensor." + key + "_current",
                voltage="sensor." + key + "_voltage",
                power="sensor." + key + "_power",
                current_limits=("sensor." + key + "_status",),
            )

        import custom_components.smart_load_manager.coordinator as coordinator_module

        with patch.object(
            coordinator_module, "resolve_easee_entities", side_effect=resolve
        ):
            result = await self.hass.config_entries.async_setup(a.entry_id)
            await self.hass.async_block_till_done()
        self.assertTrue(
            result, f"{a.state}: {a.reason}; {a.error_reason_translation_key}"
        )
        self.assertEqual(a.state.value, "loaded")
        currents = [
            e
            for e in self.registry.entities.values()
            if e.unique_id.endswith("_charger_current")
        ]
        self.assertEqual(len(currents), 2)
        self.assertEqual(
            {e.config_subentry_id for e in currents}, {group_id(a, "charging")}
        )
        self.assertEqual(
            float(self.hass.states.get("sensor.slm_line_voltage_garasje").state), 398.4
        )
        self.assertEqual(
            self.hass.states.get("sensor.slm_line_voltage_garasje").attributes[
                "friendly_name"
            ],
            "Volt Garasje",
        )
        self.assertIsNotNone(self.hass.states.get("sensor.slm_status"))
        card = await self.hass.services.async_call(
            "smart_load_manager",
            "get_dashboard",
            {},
            blocking=True,
            return_response=True,
        )
        self.assertNotIn("CHARGER_SUFFIX", card["yaml"])
        self.assertIn("sensor.slm_line_voltage_garasje", card["yaml"])
        for c in a.runtime_data.controllers.values():
            self.assertFalse(c.auto_control)
            self.assertEqual(c.data["max_current_a"], 16)
            self.assertEqual(c.data["control_minimum_current_a"], 6)
            self.assertAlmostEqual(c.data["kw_per_amp"], 0.69)
        # An old installation with no confirmed wiring must not revive the
        # previously cached TN factor after a zero-current pause.
        records = [dict(r, data=dict(r["data"])) for r in a.data["loads"]]
        records[0]["data"].pop("electrical_connection")
        original_data = dict(a.data)
        self.hass.config_entries.async_update_entry(a, data={**a.data, "loads": records})
        c = a.runtime_data.controllers[records[0]["id"]]
        c.last_commanded_current = 0
        data = await c._async_sample()
        self.assertIsNone(data["kw_per_amp"])
        self.assertIsNone(data["control_minimum_current_a"])
        self.assertFalse(data["inputs_valid"])
        self.assertIn("Bekreft", data["electrical_error"])
        self.hass.config_entries.async_update_entry(a, data=original_data)
        self.assertTrue(await self.hass.config_entries.async_unload(a.entry_id))
