// Read-only comparison. This panel never starts a config flow or calls a service.
export function candidates(devices, configEntries, selected = []) {
  const easee = new Set(configEntries.filter((e) => e.domain === "easee")
    .map((e) => e.entry_id));
  const excluded = new Set(selected);
  return devices.filter((d) => !d.disabled_by && !excluded.has(d.id) &&
    d.config_entries?.some((id) => easee.has(id)))
    .map((d) => ({ id: d.id, name: d.name_by_user || d.name || "Easee" }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

const Base = globalThis.HTMLElement || class {};
class SlmLogoProbe extends Base {
  set hass(value) {
    this._hass = value;
    if (this._picker) this._picker.hass = value;
    if (this._seed) this._seed.hass = value;
    if (this.isConnected && !this._started) this._start();
  }
  connectedCallback() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    if (this._hass && !this._started) this._start();
  }
  async _wait(name) {
    let timer;
    try {
      await Promise.race([customElements.whenDefined(name), new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(
          `Kunne ikke laste ${name}. Åpne Innstillinger → Enheter og tjenester, og gå tilbake hit.`
        )), 15000);
      })]);
    } finally { clearTimeout(timer); }
  }
  async _start() {
    this._started = true;
    this._selected = [];
    this._mode = "compact";
    this._message = "Dette er en visningstest. Ingen laderinnstillinger lagres.";
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;padding:24px;max-width:720px;margin:auto;color:var(--primary-text-color);font:16px sans-serif}
      button,select{font:inherit;padding:12px;margin:8px 8px 8px 0} select{width:100%}
      #picker{margin:24px 0;min-height:64px} button{cursor:pointer}
      #status{line-height:1.6;white-space:pre-line} .seed{display:none}
    </style><h1>SLM – test av ladervelger</h1><p>Lesetest: samme ladere, to ulike velgere.</p>
      <button id="compact">Rask liste</button><button id="native">Velger med logo</button>
      <button id="reset">Start testen på nytt</button><h2 id="step"></h2>
      <div id="picker"></div><button id="next">Legg til lader to</button>
      <button id="finish">Fullfør testen</button><p id="status"></p>`;
    for (const mode of ["compact", "native"]) this.shadowRoot.getElementById(mode)
      .addEventListener("click", () => { this._mode = mode; this._render(); });
    this.shadowRoot.getElementById("reset").addEventListener("click", () => {
      this._selected = []; this._second = false; this._done = false;
      this._message = "Testen er nullstilt. Ingen innstillinger er endret."; this._render();
    });
    this.shadowRoot.getElementById("next").addEventListener("click", () => {
      this._second = true; this._render();
    });
    this.shadowRoot.getElementById("finish").addEventListener("click", () => {
      this._done = true;
      this._message = "Test fullført. Valgene er bare beholdt på denne testsiden.\n" +
        this._selected.map((id) => this._all.find((d) => d.id === id)?.name).join("\n");
      this._render();
    });
    try {
      const [devices, entries] = await Promise.all([
        this._hass.callWS({ type: "config/device_registry/list" }),
        this._hass.callWS({ type: "config_entries/get" }),
      ]);
      this._all = candidates(devices, entries);
      this._render();
    } catch (e) { this.shadowRoot.getElementById("status").textContent = e.message; }
  }
  async _nativePicker() {
    if (!customElements.get("ha-device-picker")) {
      // Let HA load its own device-selector module; no external scripts or URLs.
      await this._wait("ha-form");
      const seed = document.createElement("ha-form");
      seed.className = "seed"; seed.hass = this._hass; seed.data = {};
      seed.schema = [{ name: "probe", selector: { device: {} } }];
      this._seed = seed; this.shadowRoot.append(seed);
      try { await this._wait("ha-device-picker"); }
      finally { seed.remove(); this._seed = undefined; }
    }
    return document.createElement("ha-device-picker");
  }
  async _render() {
    if (!this._all) return;
    const revision = this._revision = (this._revision || 0) + 1;
    const index = this._second ? 1 : 0;
    const excluded = this._second ? this._selected.slice(0, 1) : [];
    const available = this._all.filter((d) => !excluded.includes(d.id));
    const allowed = new Set(available.map((d) => d.id));
    this.shadowRoot.getElementById("step").textContent = this._done ? "Ferdig" :
      `${this._second ? "Andre" : "Første"} lader – ${this._mode === "native" ? "med logo" : "rask liste"}`;
    const host = this.shadowRoot.getElementById("picker");
    host.replaceChildren(); this._picker = undefined;
    this.shadowRoot.getElementById("status").textContent = this._message;
    this.shadowRoot.getElementById("next").disabled = this._done || this._second ||
      !this._selected[0] || this._all.length < 2;
    this.shadowRoot.getElementById("finish").disabled = this._done || !this._selected[index];
    if (this._done) return;
    const select = (id) => {
      if (!allowed.has(id)) return;
      this._selected[index] = id;
      this._message = "Valgt: " + available.find((d) => d.id === id).name +
        "\nIngen kommandoer er sendt til laderen.";
      // Keep the native picker mounted while selecting.
      this.shadowRoot.getElementById("status").textContent = this._message;
      this.shadowRoot.getElementById("next").disabled = this._second || this._all.length < 2;
      this.shadowRoot.getElementById("finish").disabled = false;
    };
    if (this._mode === "compact") {
      const input = document.createElement("select");
      input.setAttribute("aria-label", "Easee-lader");
      input.add(new Option("Velg lader", ""));
      for (const d of available) input.add(new Option(d.name, d.id));
      input.value = this._selected[index] || "";
      input.addEventListener("change", () => select(input.value));
      host.append(input); return;
    }
    host.textContent = "Laster Home Assistants velger …";
    try {
      const picker = await this._nativePicker();
      if (revision !== this._revision || !this.isConnected) return;
      picker.hass = this._hass; picker.label = "Easee-lader";
      picker.value = this._selected[index];
      // Exact ID membership, without integration/entity filters in the frontend.
      picker.deviceFilter = (device) => allowed.has(device.id);
      picker.addEventListener("value-changed", (e) => select(e.detail.value));
      this._picker = picker; host.replaceChildren(picker);
    } catch (e) { if (revision === this._revision) host.textContent = e.message; }
  }
}
if (globalThis.customElements && !customElements.get("slm-logo-probe"))
  customElements.define("slm-logo-probe", SlmLogoProbe);
