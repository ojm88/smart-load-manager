"""Device boundary for settings shared by all present and future loads."""
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN


def household_device_info():
    """Household identity is independent of charger identity and priority."""
    return DeviceInfo(identifiers={(DOMAIN, 'household')},
                      name='SLM – Boligen', manufacturer='Smart Load Manager OJM',
                      model='Household load management')
