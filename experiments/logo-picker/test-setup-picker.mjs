import assert from 'node:assert/strict';
import test from 'node:test';
import { parseHTML } from 'linkedom';

const { document, HTMLElement, customElements } = parseHTML('<html><body></body></html>');
Object.assign(globalThis, { document, HTMLElement, customElements,
  location: new URL('https://ha.example.test/slm-charger-picker?session=test-session') });
HTMLElement.prototype.focus = function () {};
await import('../../custom_components/smart_load_manager/frontend/charger-picker.mjs');

async function picker(options, maximum = 2) {
  const calls = [];
  const panel = document.createElement('slm-charger-picker');
  panel.attachShadow({ mode: 'open' });
  panel._hass = { callWS: async () => ({ token: 'test-brand-token' }), callApi: async (...args) => {
    calls.push(args);
    return args[0] === 'GET' ? { options, maximum } : { type: 'external_done' };
  }};
  await panel._start();
  return { panel, calls, root: panel.shadowRoot };
}
const options = [
  { value: 'a', label: 'Garage', integration: 'easee' },
  { value: 'b', label: 'Carport', integration: 'easee' },
];

test('cold page displays branding without any HA form or device-picker component', async () => {
  assert.equal(customElements.get('ha-form'), undefined);
  assert.equal(customElements.get('ha-device-picker'), undefined);
  const { root, calls } = await picker(options);
  assert.equal(root.querySelectorAll('[role=option]').length, 2);
  assert.equal(root.querySelector('img').getAttribute('src'), '/api/brands/integration/easee/icon.png?token=test-brand-token');
  assert.equal(calls.length, 1);
  assert.equal(root.getElementById('submit').disabled, true);
});

test('first/second choices show logos, exclude first, and submit both once', async () => {
  const { panel, root, calls } = await picker(options);
  root.querySelector('[role=option]').onclick();
  assert.equal(root.querySelector('summary').textContent, 'Garage');
  assert.ok(root.querySelector('summary img'));
  root.getElementById('second').onclick();
  const remaining = root.querySelectorAll('[role=option]');
  assert.equal(remaining.length, 1);
  assert.equal(remaining[0].textContent, 'Carport');
  remaining[0].onclick();
  await root.getElementById('submit').onclick();
  assert.deepEqual(calls[1], ['POST', 'smart_load_manager/picker/test-session', { devices: ['a', 'b'] }]);
  assert.equal(panel._done, true);
  assert.equal(root.getElementById('submit').disabled, true);
});

test('one remaining source in additive flow cannot add another charger', async () => {
  const { root, calls } = await picker([options[1]], 1);
  root.querySelector('[role=option]').onclick();
  assert.equal(root.getElementById('second').disabled, true);
  await root.getElementById('submit').onclick();
  assert.deepEqual(calls[1][2], { devices: ['b'] });
});

test('cancel sends no selected devices or service commands', async () => {
  const { root, calls } = await picker(options);
  await root.getElementById('cancel').onclick();
  assert.deepEqual(calls.map((c) => c[0]), ['GET', 'DELETE']);
});

test('labels are text and failed branding never prevents selection', async () => {
  const { root } = await picker([{ value: 'a', label: '<script>bad</script>', integration: 'easee' }]);
  assert.equal(root.querySelector('script'), null);
  const img = root.querySelector('img');
  img.onerror();
  assert.equal(img.getAttribute('src'), 'https://brands.home-assistant.io/easee/icon.png');
  img.onerror();
  assert.equal(img.hidden, true);
  root.querySelector('[role=option]').onclick();
  assert.equal(root.getElementById('submit').disabled, false);
});
