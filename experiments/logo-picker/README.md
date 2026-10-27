# Read-only logo picker comparison

Experimental development panel, **not a beta release** and not part of SLM setup.
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

## Run on the owner's HA installation

1. Keep beta 6 installed. Copy `logo-picker-probe.mjs` to
   `/config/www/slm-logo-picker-probe.mjs` using your usual file editor.
2. Add this panel to `configuration.yaml` (merge into an existing `panel_custom`
   list if present):

   ```yaml
   panel_custom:
     - name: slm-logo-probe
       sidebar_title: SLM velgertest
       sidebar_icon: mdi:test-tube
       url_path: slm-logo-probe
       module_url: /local/slm-logo-picker-probe.mjs
       require_admin: true
   ```

3. Validate the HA configuration and restart. Open Settings → Devices & services
   once, then open **SLM velgertest** in the sidebar. The settings visit ensures
   HA's form component is loaded; the panel reports an error if it is unavailable.
4. Choose **Rask liste**, open the list, select the first charger, then **Legg til
   lader to**. Verify only the other charger appears. Finish or reset. Repeat with
   **Velger med logo** using the same devices. No actual setup is saved.
5. Record both runs in Safari and Companion. Compare first-open and five repeated
   opens for each picker. Report missing logos, extra devices, freeze duration,
   and whether both choices remain named correctly. Do not compare a cold first
   open of one picker with a warmed repeated open of the other.

The plain dropdown uses browser-native styling; it is a lightweight baseline,
not an exact rendering of HA's SelectSelector. The native logo picker still uses
HA's device registry and loads config-entry metadata. No claim of equal speed
is made until actual browser/device testing. Private frontend component APIs may
change; this panel is an experiment, not a supported long-term interface.

Remove the panel YAML and local module, then restart, to remove the experiment.
VT climate selection is not implemented. A later test must cover VT's entity and
device ownership, including climates without a dedicated device; an entity picker
does not necessarily show an integration logo.

## Local checks

`node --check experiments/logo-picker/logo-picker-probe.mjs`

`node --test experiments/logo-picker/test-probe.mjs`

These verify module syntax and candidate filtering, not actual browser rendering,
logo loading or phone latency. All require separate owner acceptance.
