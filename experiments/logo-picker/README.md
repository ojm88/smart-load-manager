# Read-only logo picker comparison

Experimental read-only panel, packaged in **beta 7**, separate from normal SLM setup.
It compares a plain dropdown with Home Assistant's native `ha-device-picker`.
The native component supplies the integration branding. An exact device-ID
predicate replaces the selector's integration/entity filters. This is possible
in a custom panel; the normal Python config-flow DeviceSelector does not expose
that predicate. Success here does not establish that it can be inserted unchanged
into the normal setup dialog.

No SLM data is updated, no config flow is started, and no services or charger
commands are called. First/second selections are transient and exclude the first
device from the second list. Existing configured chargers are deliberately shown
in the first list so the owner can compare the same devices without removing SLM.
This panel has no access to tokens beyond the normal authenticated HA frontend.

## Run the packaged beta 7 test

Install beta 7 normally, restart HA and open **SLM velgertest** in the administrator sidebar. No manual YAML, panel registration or extra file copy is needed. Keep the existing chargers configured.

Choose **Rask liste**, open the list, select the first charger, then **Legg til lader to**. Only the other source charger should remain. Finish or reset; repeat with **Velger med logo** using the same devices. No actual setup is saved. If a frontend component has not loaded, visit Settings → Devices & services once and return.

Record the first open and five repeated opens for each picker in Safari and Companion. Report missing logos, extra devices, freezes and whether both choices remain named correctly. Compare cold opens with cold opens and warmed opens with warmed opens.

The plain dropdown uses browser-native styling; it is a lightweight baseline,
not an exact rendering of HA's SelectSelector. The native logo picker still uses
HA's device registry and loads config-entry metadata. No claim of equal speed
is made until actual browser/device testing. Private frontend component APIs may
change; this panel is an experiment, not a supported long-term interface.

The sidebar panel is removed when the SLM integration is unloaded. Returning to beta 6 and restarting removes the packaged experiment.
VT climate selection is not implemented. A later test must cover VT's entity and
device ownership, including climates without a dedicated device; an entity picker
does not necessarily show an integration logo.

## Local checks

`node --check experiments/logo-picker/logo-picker-probe.mjs`

`node --test experiments/logo-picker/test-probe.mjs`

These verify module syntax and candidate filtering, not actual browser rendering,
logo loading or phone latency. All require separate owner acceptance.
