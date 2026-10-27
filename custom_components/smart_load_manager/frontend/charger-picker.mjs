import './logo-picker-probe.mjs';

const Probe = customElements.get('slm-logo-probe');
class SlmChargerPicker extends Probe {
  async _start() {
    this._started = true;
    this._selected = [];
    this._index = 0;
    this._token = new URL(location.href).searchParams.get('session');
    this._api = 'smart_load_manager/picker/' + encodeURIComponent(this._token || '');
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;padding:24px;max-width:680px;margin:auto;font:16px sans-serif;color:var(--primary-text-color)}
      button{font:inherit;padding:12px;margin:16px 12px 0 0}.seed{display:none}#picker{margin:24px 0}
    </style><h1>Velg Easee-ladere</h1><p>Valgene kontrolleres før oppsettet lagres.</p>
      <h2 id="step"></h2><div id="picker"></div><p id="message" role="status"></p>
      <button id="second">Legg til en lader til</button><button id="submit">Bruk valgene</button>
      <button id="cancel">Avbryt oppsettet</button>`;
    const el = (id) => this.shadowRoot.getElementById(id);
    el('second').onclick = () => { this._index = 1; this._render(); };
    el('submit').onclick = async () => {
      this._busy = true; this._buttons();
      try {
        await this._hass.callApi('POST', this._api, { devices: this._selected });
        el('picker').replaceChildren();
        el('message').textContent = 'Valgene er kontrollert. Gå tilbake til oppsettsdialogen for å fullføre.';
        this._done = true;
      } catch (e) { el('message').textContent = e.message || 'Kunne ikke bekrefte valgene. Prøv igjen.'; }
      finally { this._busy = false; this._buttons(); }
    };
    el('cancel').onclick = async () => {
      this._busy = true; this._buttons();
      try {
        await this._hass.callApi('DELETE', this._api);
        this._done = true; el('picker').replaceChildren();
        el('message').textContent = 'Oppsettet er avbrutt. Ingen ladere er lagt til.';
      } catch (e) { el('message').textContent = e.message || 'Kunne ikke avbryte. Lukk den opprinnelige oppsettsdialogen.'; }
      finally { this._busy = false; this._buttons(); }
    };
    this._buttons();
    try {
      this._data = await this._hass.callApi('GET', this._api);
      await this._render();
    } catch (e) { el('message').textContent = e.message || 'Oppsettet er utløpt eller lukket. Start på nytt.'; }
  }
  _buttons() {
    const disabled = this._busy || this._done || this._loading;
    this.shadowRoot.getElementById('second').disabled = disabled || !this._data ||
      this._data.maximum < 2 || this._index === 1 || !this._selected[0] || this._data.options.length < 2;
    this.shadowRoot.getElementById('submit').disabled = disabled || !this._selected[this._index];
    this.shadowRoot.getElementById('cancel').disabled = disabled;
  }
  async _render() {
    if (!this._data || this._done) return;
    const options = this._data.options.filter((o) => this._index === 0 || o.value !== this._selected[0]);
    const allowed = new Set(options.map((o) => o.value));
    this.shadowRoot.getElementById('step').textContent = this._index === 0 ? 'Første lader' : 'Andre lader';
    const host = this.shadowRoot.getElementById('picker');
    this._loading = true;
    host.textContent = 'Laster ladervelger …';
    this._buttons();
    try {
      const picker = await this._nativePicker();
      picker.hass = this._hass; picker.label = 'Easee-lader';
      picker.deviceFilter = (device) => allowed.has(device.id);
      picker.addEventListener('value-changed', (event) => {
        const id = event.detail.value;
        if (!allowed.has(id)) { this._selected.splice(this._index); this._buttons(); return; }
        this._selected[this._index] = id;
        this.shadowRoot.getElementById('message').textContent = 'Valgt: ' + options.find((o) => o.value === id).label;
        this._buttons();
      });
      this._picker = picker; host.replaceChildren(picker);
    } catch (e) { host.textContent = e.message; }
    finally { this._loading = false; this._buttons(); }
  }
}
customElements.define('slm-charger-picker', SlmChargerPicker);
