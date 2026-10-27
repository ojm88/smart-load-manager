// Keep setup independent of HA's lazy-loaded form and device-picker bundles.
class SlmChargerPicker extends HTMLElement {
  set hass(value) {
    this._hass = value;
    if (this.isConnected && !this._started) this._start();
  }
  connectedCallback() {
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    if (this._hass && !this._started) this._start();
  }
  async _start() {
    this._started = true;
    this._selected = [];
    this._index = 0;
    this._token = new URL(location.href).searchParams.get('session');
    this._api = 'smart_load_manager/picker/' + encodeURIComponent(this._token || '');
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;padding:24px;max-width:680px;margin:auto;font:16px sans-serif;color:var(--primary-text-color)}
      button{font:inherit;padding:12px;margin:16px 12px 0 0}#picker{margin:24px 0}
      details{border:1px solid var(--divider-color,#888);border-radius:8px}
      summary{cursor:pointer;padding:16px;display:flex;align-items:center;gap:12px}
      summary::after{content:'▾';margin-left:auto}img{width:32px;height:32px;object-fit:contain}
      [role=listbox]{padding:4px}[role=option]{display:flex;align-items:center;gap:12px;
        width:100%;text-align:left;margin:0;border:0;background:transparent;color:inherit;cursor:pointer}
      [role=option]:hover,[role=option]:focus-visible{background:var(--secondary-background-color,#eee)}
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
      const [data, branding] = await Promise.all([
        this._hass.callApi('GET', this._api),
        this._hass.callWS({ type: 'brands/access_token' }).catch(() => null),
      ]);
      this._data = data;
      this._brandToken = branding?.token;
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
    host.replaceChildren();
    const menu = document.createElement('details');
    const summary = document.createElement('summary');
    const label = document.createElement('span');
    label.textContent = 'Velg Easee-lader';
    summary.append(label);
    menu.append(summary);
    const list = document.createElement('div');
    list.setAttribute('role', 'listbox');
    list.setAttribute('aria-label', 'Easee-ladere');
    for (const option of options) {
      const button = document.createElement('button');
      button.type = 'button'; button.setAttribute('role', 'option');
      button.setAttribute('aria-selected', String(option.value === this._selected[this._index]));
      const name = document.createElement('span');
      name.textContent = option.label;
      button.append(this._brand(option.integration), name);
      button.onclick = () => {
        if (!allowed.has(option.value)) return;
        this._selected[this._index] = option.value;
        summary.replaceChildren(this._brand(option.integration), document.createTextNode(option.label));
        for (const item of list.children) item.setAttribute('aria-selected', String(item === button));
        menu.open = false; summary.focus();
        this.shadowRoot.getElementById('message').textContent = 'Valgt: ' + option.label;
        this._buttons();
      };
      list.append(button);
      if (option.value === this._selected[this._index]) {
        summary.replaceChildren(this._brand(option.integration), document.createTextNode(option.label));
      }
    }
    if (!options.length) label.textContent = 'Ingen ledige Easee-ladere';
    menu.append(list); host.append(menu); this._buttons();
  }
  _brand(integration) {
    const domain = /^[a-z0-9_]+$/.test(integration || '') ? integration : 'easee';
    const img = document.createElement('img');
    img.alt = ''; img.width = 32; img.height = 32;
    // HA serves custom integration branding locally on recent versions.
    const image = this._hass.themes?.darkMode ? 'dark_icon.png' : 'icon.png';
    img.src = this._brandToken
      ? '/api/brands/integration/' + domain + '/' + image + '?token=' + encodeURIComponent(this._brandToken)
      : 'https://brands.home-assistant.io/' + domain + '/icon.png';
    img.onerror = () => {
      if (!img.dataset.fallback) {
        img.dataset.fallback = 'true';
        img.src = 'https://brands.home-assistant.io/' + domain + '/icon.png';
      } else { img.hidden = true; img.onerror = null; }
    };
    return img;
  }
}
customElements.define('slm-charger-picker', SlmChargerPicker);
