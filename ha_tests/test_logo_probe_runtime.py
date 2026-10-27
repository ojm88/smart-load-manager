"""Real HA frontend panel registration, with HTTP static hosting mocked."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from homeassistant.components import frontend
from homeassistant.core import HomeAssistant
from smart_load_manager.logo_probe import (
    MODULE_URL, PANEL_PATH, async_register_logo_probe, async_remove_logo_probe,
)


class LogoProbeTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = TemporaryDirectory()
        self.hass = HomeAssistant(self.tmp.name)
        self.hass.config.components.add("frontend")
        self.hass.http = SimpleNamespace(async_register_static_paths=AsyncMock())

    async def asyncTearDown(self):
        await self.hass.async_stop(force=True)
        self.tmp.cleanup()

    async def test_admin_panel_and_packaged_module_register_once_across_reloads(self):
        await asyncio.gather(
            async_register_logo_probe(self.hass), async_register_logo_probe(self.hass)
        )
        self.hass.http.async_register_static_paths.assert_awaited_once()
        paths = self.hass.http.async_register_static_paths.await_args.args[0]
        self.assertEqual(paths[0].url_path, MODULE_URL)
        self.assertTrue(Path(paths[0].path).is_file())
        self.assertFalse(paths[0].cache_headers)
        panel = self.hass.data[frontend.DATA_PANELS][PANEL_PATH]
        response = panel.to_response()
        self.assertTrue(response["require_admin"])
        self.assertEqual(response["config"]["_panel_custom"]["module_url"], MODULE_URL)
        async_remove_logo_probe(self.hass)
        self.assertFalse(PANEL_PATH in self.hass.data.get(frontend.DATA_PANELS, {}))
        await async_register_logo_probe(self.hass)
        self.assertTrue(PANEL_PATH in self.hass.data.get(frontend.DATA_PANELS, {}))
        self.hass.http.async_register_static_paths.assert_awaited_once()

    async def test_headless_installation_needs_no_frontend(self):
        self.hass.config.components.remove("frontend")
        await async_register_logo_probe(self.hass)
        self.hass.http.async_register_static_paths.assert_not_awaited()

    async def test_optional_hosting_failure_can_retry_without_breaking_setup(self):
        self.hass.http.async_register_static_paths.side_effect = RuntimeError("test")
        with self.assertLogs("smart_load_manager.logo_probe", level="ERROR"):
            await async_register_logo_probe(self.hass)
        self.assertFalse(PANEL_PATH in self.hass.data.get(frontend.DATA_PANELS, {}))
        self.hass.http.async_register_static_paths.side_effect = None
        await async_register_logo_probe(self.hass)
        self.assertTrue(PANEL_PATH in self.hass.data.get(frontend.DATA_PANELS, {}))
