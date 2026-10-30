"""Bounded, memory-only flight recorder with a strict export allowlist."""
from collections import deque
from datetime import datetime, UTC
from math import isfinite

NUMBER_FIELDS = ('han_power_w', 'han_age_seconds', 'energy_used_kwh',
    'energy_estimate_kwh', 'minutes_left', 'safety_margin_kwh', 'hourly_limit_kwh',
    'charger_current_a', 'charger_power_w', 'max_current_a',
    'control_minimum_current_a', 'kw_per_amp', 'recommended_current_a',
    'last_sent_current_a', 'next_regulation_at', 'site_available_kw',
    'phase_code', 'phase_mode_code')
BOOL_FIELDS = ('han_fresh', 'inputs_valid', 'electrical_ready', 'schedule_allowed',
               'auto_control', 'charging_paused', 'site_control_ready', 'awaiting_reduction',
               'han_value_valid', 'tariff_valid', 'completion_hold')
STATUSES = {'disconnected','charging','start_charging','completed','awaiting_start',
            'ready_to_charge','error','unknown','unavailable'}


def sample_data(data):
    """Never copy arbitrary config, attributes, errors, names or entity IDs."""
    result = {k: v for k in NUMBER_FIELDS if
              isinstance((v := data.get(k)), (float, int)) and not isinstance(v, bool) and isfinite(v)}
    result.update({k: data[k] for k in BOOL_FIELDS if isinstance(data.get(k), bool)})
    result['status'] = data.get('status') if data.get('status') in STATUSES else 'other'
    for field in ('terminal_currents_a', 'terminal_voltages_v'):
        values = data.get(field) or {}
        result[field] = {k: v for k, v in values.items() if
            k in {'T2','T3','T4','T5','T1T2','T1T3','T1T4','T1T5','T2T3','T2T4','T2T5','T3T4','T3T5','T4T5'}
            and isinstance(v, (int,float)) and not isinstance(v,bool) and isfinite(v)}
    return result


class DebugTrace:
    def __init__(self, capacity=4096):
        self.events = deque(maxlen=capacity)
        self.total = 0
        self.started_at = datetime.now(UTC).isoformat()
        self.aliases = {}

    def alias(self, key):
        if key not in self.aliases:
            self.aliases[key] = f'load_{len(self.aliases)+1}'
        return self.aliases[key]

    def record(self, event, key=None, *, data=None, target=None, mode=None):
        self.total += 1
        row = {'sequence': self.total, 'at': datetime.now(UTC).isoformat(), 'event': event}
        if key is not None:
            row['load'] = self.alias(key)
        if data is not None:
            row['sample'] = sample_data(data)
        if isinstance(target, (int,float)) and not isinstance(target,bool) and isfinite(target):
            row['target'] = target
        if mode in {'regular','control','hold','early','urgent','single_phase','three_phase','auto','one','three'}:
            row['mode'] = mode
        self.events.append(row)

    def export(self):
        from copy import deepcopy
        return {'started_at': self.started_at, 'capacity': self.events.maxlen,
                'dropped_events': max(0, self.total-len(self.events)),
                'persistence': 'memory_only_reset_on_reload_or_restart',
                'events': deepcopy(list(self.events))}


def command_trace(hass, device_id, event, *, target=None, mode=None):
    from .const import DOMAIN
    site = getattr(hass, 'data', {}).get(DOMAIN, {}).get('site')
    if site is None or not hasattr(site, 'debug_trace'):
        return
    for key, controller in site.controllers.items():
        if controller.entry.data.get('charger_device') == device_id:
            cycle_sample = (getattr(site, '_command_samples', None) or {}).get(key)
            data = {**(cycle_sample if cycle_sample is not None else controller.data or {}),
                    'auto_control': controller.auto_control,
                    'charging_paused': controller.charging_paused,
                    'last_sent_current_a': controller.last_commanded_current}
            site.debug_trace.record(event, key, data=data, target=target, mode=mode)
            break
