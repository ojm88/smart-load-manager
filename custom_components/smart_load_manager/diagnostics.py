"""Native HA download: anonymous SLM state and bounded decision/command history."""
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.loader import async_get_integration
from homeassistant.util import dt as dt_util
from .const import DOMAIN
from .debug_trace import sample_data


async def async_get_config_entry_diagnostics(hass, entry):
    site = hass.data.get(DOMAIN, {}).get('site')
    integration = await async_get_integration(hass, DOMAIN)
    result = {'schema_version': 1, 'home_assistant_version': HA_VERSION,
              'slm_version': str(integration.version), 'loads': [],
              'limitations': ['Service success is not physical charger acknowledgement.',
                              'No history from before this recorder started.',
                              'Only SLM decisions/commands, not all Easee cloud traffic.']}
    if site is None:
        result['runtime'] = 'not_loaded'
        return result
    # No awaits while copying the serialized runtime state.
    for key, c in site.controllers.items():
        reduction = site.pending_reductions.get(key)
        result['loads'].append({'load': site.debug_trace.alias(key),
            'automatic': bool(c.auto_control), 'paused': bool(c.charging_paused),
            'sample': sample_data(c.data or {}),
            'pending_reduction': reduction is not None,
            'pending_reduction_limit_a': reduction[0] if reduction else None,
            'pending_reduction_age_seconds': max(0, round(dt_util.utcnow().timestamp()-reduction[1], 1)) if reduction else None,
            'completed_allowance_a': site._completed_limits.get(key),
            'connection': c.entry.data.get('electrical_connection')
                if c.entry.data.get('electrical_connection') in {'it_1','it_3','tn_1','tn_3'} else 'unspecified'})
    from .household_status import charging_summary
    rows = []
    for load, controller in zip(result['loads'], site.controllers.values(), strict=True):
        sample = load['sample']
        rows.append({'name': load['load'], 'load_type': 'ev_charger',
                     'source_available': bool(controller.data) and getattr(controller, 'last_update_success', True), 'status': sample.get('status'),
                     'automatic_control': load['automatic'],
                     'power_w': sample.get('charger_power_w')})
    summary = charging_summary({'controlled_loads': rows})
    summary.pop('loads')
    result['charging_summary'] = summary
    result['trace'] = site.debug_trace.export()
    return result
