"""Easee operation states, separate from battery SOC and SLM allocation.

Names follow nordicopen/easee_hass v0.9.74 const.EASEE_STATUS. Unknown future
states do not authorize positive automatic current until explicitly supported.
"""

STATUS_TEXT = {
    'disconnected': ('Bilen er ikke koblet til laderen.', 'The car is not connected.'),
    'awaiting_start': ('Easee venter på ladestart.', 'Easee is waiting to start.'),
    'charging': ('Easee melder at bilen lader.', 'Easee reports charging.'),
    'completed': ('Easee rapporterer at ladingen er fullført.', 'Easee reports charging completed.'),
    'error': ('Easee rapporterer en feil. Kontroller laderen.', 'Easee reports an error. Check the charger.'),
    'ready_to_charge': ('Easee er klar til å lade.', 'Easee is ready to charge.'),
    'awaiting_authorization': ('Easee venter på godkjenning av ladingen.', 'Easee is waiting for charging authorization.'),
    'de_authorizing': ('Easee avslutter godkjenningen av ladeøkten.', 'Easee is ending charging authorization.'),
    'start_charging': ('Easee starter ladingen.', 'Easee is starting charging.'),
    'stop_charging': ('Easee stopper ladingen.', 'Easee is stopping charging.'),
    'offline': ('Easee er frakoblet. Ladestatus kan ikke bekreftes.', 'Easee is offline. Charging status cannot be confirmed.'),
    'awaiting_load_balancing': ('Easee avventer lastbalansering.', 'Easee is waiting for load balancing.'),
    'awaiting_smart_start': ('Easee venter på sin smartladingsstart.', 'Easee is waiting for its smart charging start.'),
    'awaiting_scheduled_start': ('Easee venter på sin egen ladeplan.', 'Easee is waiting for its own charging schedule.'),
    'authenticating': ('Easee kontrollerer godkjenning av ladingen.', 'Easee is authenticating charging.'),
    'paused_due_to_equalizer': ('Easee har satt ladingen på pause på grunn av Equalizer.', 'Easee has paused charging because of Equalizer.'),
    'searching_for_master': ('Easee søker etter hovedladeren i anlegget.', 'Easee is searching for the site master charger.'),
    'erratic_ev': ('Easee rapporterer ustabil kommunikasjon med bilen.', 'Easee reports erratic vehicle communication.'),
    'error_temperature_too_high': ('Easee rapporterer for høy temperatur.', 'Easee reports excessive temperature.'),
    'error_dead_powerboard': ('Easee rapporterer feil på effektkortet.', 'Easee reports a power board fault.'),
    'error_overcurrent': ('Easee rapporterer overstrøm.', 'Easee reports overcurrent.'),
    'error_pen_fault': ('Easee rapporterer PEN-feil.', 'Easee reports a PEN fault.'),
}
# Compatibility aliases retained from earlier SLM versions.
ALIASES = {'charged': 'completed', 'awaiting_authentication': 'awaiting_authorization'}
CHARGE_ELIGIBLE = frozenset({'awaiting_start', 'charging', 'ready_to_charge',
                             'start_charging', 'awaiting_load_balancing'})


def normalize_status(status):
    value = str(status).strip().lower().replace(' ', '_')
    return ALIASES.get(value, value)


def allows_automatic_current(status):
    return normalize_status(status) in CHARGE_ELIGIBLE


def status_explanation(status, *, norwegian=True):
    return STATUS_TEXT.get(normalize_status(status), (
        'Easee rapporterer en ukjent status. Automatisk lading avventer en kjent status.',
        'Easee reports an unknown status. Automatic charging waits for a known state.'
    ))[0 if norwegian else 1]
