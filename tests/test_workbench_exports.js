'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function element() {
  return {value: '', hidden: false, disabled: false, textContent: '', listeners: {}, children: [],
    classList: {toggle() {}}, addEventListener(name, handler) {this.listeners[name] = handler;},
    querySelectorAll() {return [];}, replaceChildren() {}, append() {}};
}

function setup(response = {saved: true, path: 'C:\\reports\\report.json'}, ok = true, runs = []) {
  const elements = new Map(), calls = [];
  const get = id => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  const context = vm.createContext({document: {getElementById: get},
    window: {location: {search: ''}}, URLSearchParams, setTimeout() {}, clearTimeout() {},
    fetch: async (url, options) => {
      if (url === '/api/config') return new Promise(() => {});
      calls.push([url, options]);
      return {ok: url.endsWith('/export') ? ok : true, status: ok ? 200 : 400,
        json: async () => url.endsWith('/export') ? response : url === '/api/workbench' ? runs : []};
    }});
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/workbench.js'), 'utf8'), context);
  vm.runInContext('current = {id: "'+'a'.repeat(32)+'", status: "completed"}; nativeFileDialogs = true; nativeExportDialogs = true;', context);
  return {get, calls, context};
}

for (const format of ['report', 'csv', 'bundle']) {
  test(`${format} export opens the native save route and reports the saved path`, async () => {
    const {get, calls} = setup();
    let prevented = false;
    await get(format).listeners.click({preventDefault() {prevented = true;}});
    assert.equal(prevented, true);
    const [url, options] = calls.find(([url]) => url.endsWith('/export'));
    assert.match(url, /\/api\/workbench\/[a-f0-9]{32}\/export$/);
    assert.deepEqual(JSON.parse(options.body), {format});
    assert.equal(options.headers['X-ImageConverter'], '1');
    assert.equal(get('notice').textContent, 'Gespeichert: C:\\reports\\report.json');
    assert.equal(get('file').disabled, false);
  });
}

test('cancelled export leaves the report available and explains cancellation', async () => {
  const {get} = setup({saved: false});
  await get('report').listeners.click({preventDefault() {}});
  assert.match(get('notice').textContent, /abgebrochen.*Bericht bleibt erhalten/);
});

test('export failures are visible without leaving the workbench', async () => {
  const {get} = setup({error: 'Speicherdialog nicht verfügbar.'}, false);
  await get('bundle').listeners.click({preventDefault() {}});
  assert.equal(get('notice').textContent, 'Speicherdialog nicht verfügbar.');
  assert.equal(get('notice').hidden, false);
});

test('other browsers retain ordinary file downloads', () => {
  const {get, context, calls} = setup();
  vm.runInContext('nativeExportDialogs = false;', context);
  get('report').listeners.click({preventDefault() {assert.fail('browser download prevented');}});
  assert.equal(get('report').download, 'report.json');
  assert.equal(calls.filter(([url]) => url.endsWith('/export')).length, 0);
});

test('another running workbench shows its real progress and can be opened directly', async () => {
  const run = {id: 'b'.repeat(32), status: 'running', name: 'panel.svg', active_case: 'probe_09',
    summary: {completed: 9, total: 17}};
  const {get, context} = setup(undefined, true, [run]);
  await vm.runInContext('refreshActivity()', context);
  assert.equal(get('activity').hidden, false);
  assert.equal(get('activity-name').textContent, 'Plan B · panel.svg · probe_09 · 9/17 geprüft');
  assert.equal(get('activity-open').hidden, false);
  assert.equal(get('activity-open').href, `/workbench?run=${run.id}`);
  assert.equal(get('run-all').disabled, true);
  run.status = 'completed';
  await vm.runInContext('refreshActivity()', context);
  assert.equal(get('activity').hidden, true);
  assert.equal(get('run-all').disabled, false);
});
