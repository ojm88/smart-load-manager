"""Beta-only, read-only frontend comparison panel."""

import asyncio
import logging
from pathlib import Path

from .const import DOMAIN

PANEL_PATH = "slm-logo-probe"
MODULE_URL = "/smart_load_manager_beta7/logo-picker-probe.mjs"
_LOGGER = logging.getLogger(__name__)


async def async_register_logo_probe(hass):
    """Expose the packaged test page when the normal HA frontend is enabled."""
    state = hass.data.setdefault(DOMAIN, {}).setdefault("logo_probe", {})
    if "frontend" not in hass.config.components:
        if not hass.is_running and "startup_listener" not in state:
            from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

            async def on_started(event):
                state.pop("startup_listener", None)
                site = hass.data.get(DOMAIN, {}).get("site")
                if site and site.controllers:
                    await async_register_logo_probe(hass)

            state["startup_listener"] = hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED, on_started
            )
        return
    from homeassistant.components.http import StaticPathConfig
    from homeassistant.components.panel_custom import async_register_panel

    lock = state.setdefault("lock", asyncio.Lock())
    async with lock:
        try:
            if not state.get("static_registered"):
                await hass.http.async_register_static_paths(
                    [StaticPathConfig(
                        MODULE_URL,
                        str(Path(__file__).parent / "frontend/logo-picker-probe.mjs"),
                        cache_headers=False,
                    )]
                )
                state["static_registered"] = True
            if not state.get("panel_registered"):
                await async_register_panel(
                    hass,
                    frontend_url_path=PANEL_PATH,
                    webcomponent_name="slm-logo-probe",
                    sidebar_title="SLM velgertest",
                    sidebar_icon="mdi:test-tube",
                    module_url=MODULE_URL,
                    require_admin=True,
                )
                state["panel_registered"] = True
        except Exception:
            # Optional presentation must never prevent the charging integration
            # from loading. A later reload can retry failed panel registration.
            _LOGGER.exception("Could not register the optional SLM picker test panel")


def async_remove_logo_probe(hass):
    """Remove the sidebar entry when the last runtime has unloaded."""
    state = hass.data.get(DOMAIN, {}).get("logo_probe", {})
    if cancel := state.pop("startup_listener", None):
        cancel()
    if state.get("panel_registered"):
        from homeassistant.components import frontend

        frontend.async_remove_panel(hass, PANEL_PATH)
        state["panel_registered"] = False
