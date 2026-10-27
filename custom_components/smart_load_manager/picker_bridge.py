"""Authenticated bridge between an optional logo picker and a native HA flow."""

import asyncio
import secrets
import time
from pathlib import Path

from aiohttp import web
from homeassistant.components.http import HomeAssistantView, StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel

from .const import DOMAIN

PANEL = "slm-charger-picker"
URL = "/smart_load_manager_picker/charger-picker.mjs"
TTL = 900


def _state(hass):
    return hass.data.setdefault(DOMAIN, {}).setdefault("picker_bridge", {})


def _session(hass, token):
    state = _state(hass)
    sessions = state.setdefault("sessions", {})
    for key, value in list(sessions.items()):
        if value["expires"] < time.monotonic():
            del sessions[key]
    session = sessions.get(token)
    if not session:
        raise web.HTTPNotFound(reason="Picker expired or closed")
    flow = session["flow"]
    try:
        session["manager"].async_get(flow.flow_id)
    except Exception as err:
        sessions.pop(token, None)
        raise web.HTTPNotFound(reason="Setup has been closed") from err
    return session


def choices(flow, excluded):
    return flow._logo_choices(excluded)


async def register(hass):
    """Set up hosting even before the first SLM installation exists."""
    state = _state(hass)
    lock = state.setdefault("lock", asyncio.Lock())
    async with lock:
        if state.get("ready"):
            return
        if not state.get("static"):
            await hass.http.async_register_static_paths([
                StaticPathConfig("/smart_load_manager_picker", str(Path(__file__).parent / "frontend"), False)
            ])
            state["static"] = True
        if not state.get("view"):
            hass.http.register_view(PickerView(hass))
            state["view"] = True
        await async_register_panel(
            hass, frontend_url_path=PANEL, webcomponent_name="slm-charger-picker",
            module_url=URL, require_admin=True,
        )
        state["ready"] = True


async def begin(flow, manager, excluded=(), maximum=2):
    await register(flow.hass)
    if old := getattr(flow, "_logo_token", None):
        _state(flow.hass).setdefault("sessions", {}).pop(old, None)
    token = secrets.token_urlsafe(32)
    flow._logo_token = token
    _state(flow.hass).setdefault("sessions", {})[token] = {
        "flow": flow, "manager": manager, "excluded": tuple(excluded),
        "maximum": maximum, "expires": time.monotonic() + TTL,
    }
    return "/" + PANEL + "?session=" + token


def take(flow, user_input):
    """Validate the callback again before advancing the native flow."""
    token = getattr(flow, "_logo_token", None)
    session = _session(flow.hass, token)
    if not isinstance(user_input, dict) or user_input.get("token") != token:
        raise ValueError("Invalid picker callback")
    devices = user_input.get("devices")
    if not isinstance(devices, list) or not 1 <= len(devices) <= session["maximum"]:
        raise ValueError("Select one or two chargers")
    if not all(isinstance(d, str) for d in devices) or len(set(devices)) != len(devices):
        raise ValueError("Select distinct chargers")
    allowed = {item["value"] for item in choices(flow, session["excluded"])}
    if any(d not in allowed for d in devices):
        raise ValueError("Charger already selected or no longer available")
    flow._validate_logo_devices(devices)  # Does not save or control.
    return devices


def close(flow):
    if token := getattr(flow, "_logo_token", None):
        _state(flow.hass).setdefault("sessions", {}).pop(token, None)
        flow._logo_token = None


class PickerView(HomeAssistantView):
    url = "/api/smart_load_manager/picker/{token}"
    name = "api:smart_load_manager:picker"
    requires_auth = True

    def __init__(self, hass):
        self.hass = hass

    def session(self, request, token):
        if not request["hass_user"].is_admin:
            raise web.HTTPForbidden()
        return _session(self.hass, token)

    async def get(self, request, token):
        session = self.session(request, token)
        return self.json({"options": choices(session["flow"], session["excluded"]),
                          "maximum": session["maximum"]})

    async def post(self, request, token):
        session = self.session(request, token)
        try:
            data = await request.json()
        except (ValueError, TypeError):
            return self.json_message("Invalid selection", 400)
        if not isinstance(data, dict):
            return self.json_message("Invalid selection", 400)
        async with session.setdefault("lock", asyncio.Lock()):
            session = self.session(request, token)
            try:
                take(session["flow"], {"token": token, "devices": data.get("devices")})
                result = await session["manager"].async_configure(
                    session["flow"].flow_id,
                    {"token": token, "devices": data.get("devices")},
                )
            except ValueError as err:
                return self.json_message(str(err), 400)
            return self.json({"type": result["type"]})

    async def delete(self, request, token):
        session = self.session(request, token)
        session["manager"].async_abort(session["flow"].flow_id)
        close(session["flow"])
        return self.json({"cancelled": True})
