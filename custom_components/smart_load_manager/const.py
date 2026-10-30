"""Constants for Smart Load Manager."""

from datetime import timedelta

DOMAIN = "smart_load_manager"
PLATFORMS = ["sensor", "select", "number", "switch", "time"]
UPDATE_INTERVAL = timedelta(seconds=30)
HAN_MAX_AGE_SECONDS = 120
SCHEDULE_WINDOW_HOURS = 12

CONF_CHARGER_DEVICE = "charger_device"
CONF_CONNECTION = "electrical_connection"
CONNECTION_OPTIONS = ("it_1", "it_3", "tn_1", "tn_3")
CONF_HAN_POWER_ENTITY = "han_power_entity"
CONF_HOURLY_LIMIT_KWH = "hourly_limit_kwh"
CONF_CONSUMPTION_LIMIT_KWH = "consumption_limit_kwh"
DEFAULT_CONSUMPTION_LIMIT_KWH = 15.0
CONF_TARIFF_USED_ENTITY = "tariff_used_entity"
CONF_SAFETY_MARGIN_KWH = "safety_margin_kwh"
CONF_SCHEDULE_START_TIME = "schedule_start_time"
CONF_SCHEDULE_ENABLED = "schedule_enabled"
DEFAULT_SCHEDULE_START_TIME = "23:00:00"

TARIFF_USED_ENTITY = "sensor.energy_used_this_hour"
TARIFF_ESTIMATE_ENTITY = "sensor.energy_estimate_this_hour"

EASEE_DOMAIN = "easee"
EASEE_DYNAMIC_LIMIT_SERVICE = "set_charger_dynamic_limit"
EASEE_PHASE_MODE_SERVICE = "set_charger_phase_mode"
PHASE_MODE_OPTIONS = ("1_phase", "auto_phase", "3_phase")
PHASE_MODE_CODES = {"1_phase": 1, "auto_phase": 2, "3_phase": 3}
PHASE_MODE_FROM_CODE = {value: key for key, value in PHASE_MODE_CODES.items()}
DYNAMIC_LIMIT_TTL_MINUTES = 0  # Easee: zero keeps the command until replaced.

