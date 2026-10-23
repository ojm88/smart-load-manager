"""Constants for Smart Load Manager."""

from datetime import timedelta

DOMAIN = "smart_load_manager"
PLATFORMS = ["sensor", "number", "switch", "time"]
UPDATE_INTERVAL = timedelta(seconds=30)
HAN_MAX_AGE_SECONDS = 60
SCHEDULE_WINDOW_HOURS = 12

CONF_CHARGER_DEVICE = "charger_device"
CONF_HAN_POWER_ENTITY = "han_power_entity"
CONF_HOURLY_LIMIT_KWH = "hourly_limit_kwh"
CONF_TARIFF_USED_ENTITY = "tariff_used_entity"
CONF_TARIFF_ESTIMATE_ENTITY = "tariff_estimate_entity"
CONF_SAFETY_MARGIN_KWH = "safety_margin_kwh"
CONF_SCHEDULE_START_TIME = "schedule_start_time"
CONF_SCHEDULE_ENABLED = "schedule_enabled"
DEFAULT_SCHEDULE_START_TIME = "23:00:00"

TARIFF_USED_ENTITY = "sensor.energy_used_this_hour"
TARIFF_ESTIMATE_ENTITY = "sensor.energy_estimate_this_hour"

EASEE_DOMAIN = "easee"
EASEE_DYNAMIC_LIMIT_SERVICE = "set_charger_dynamic_limit"
DYNAMIC_LIMIT_TTL_MINUTES = 0  # Easee: zero keeps the command until replaced.

