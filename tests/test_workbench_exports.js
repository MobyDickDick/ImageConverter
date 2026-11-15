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
  vm.runInContext('current = {id: "'+'a'.repeat(32)+'", status: "completed", source_description: ""}; nativeFileDialogs = true; nativeExportDialogs = true; workbenchDescriptionUpdates = true;', context);
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

test('edited descriptions block stale execution and prepare a new task from the stored SVG', async () => {
  const {get, context, calls} = setup();
  const original = {id: 'a'.repeat(32), status: 'completed', source_description: 'Alter Text.', seed: '472',
    cases: [{case_id: 'original', width: 80, height: 80}], name: 'Quelle.svg'};
  context.original = original;
  vm.runInContext('current = original; selected = new Set(["original"]);', context);
  get('description').value = original.source_description;
  get('seed').value = original.seed;
  vm.runInContext('controls()', context);
  assert.equal(get('prepare').disabled, false); // Stored SVG can be reused without choosing a file.
  assert.equal(get('run-all').disabled, false);
  get('description').value = 'Neue Beschreibung mit Rahmen.';
  get('description').listeners.input();
  assert.equal(get('run-all').disabled, true);
  assert.equal(get('run-selected').disabled, true);
  await vm.runInContext('run(true).catch(error => notice(error.message))', context);
  assert.match(get('notice').textContent, /neu vorbereiten/);
  assert.equal(calls.filter(([url]) => url.endsWith('/start')).length, 0);
  const fresh = {...original, id: 'b'.repeat(32), source_description: get('description').value};
  context.fresh = fresh;
  context.fetch = async (url, options) => {
    calls.push([url, options]);
    return {ok: true, json: async () => url.endsWith('/reprepare') ? fresh : []};
  };
  context.window.history = {replaceState() {}};
  // Table rendering is covered separately; exercise the actual submit handler and controls.
  vm.runInContext('render = report => { current = report; }; history = async () => {};', context);
  await get('prepare').listeners.click();
  const [url, options] = calls.find(([url]) => url.endsWith('/reprepare'));
  assert.equal(url, `/api/workbench/${original.id}/reprepare`);
  assert.deepEqual(JSON.parse(options.body), {description: fresh.source_description, seed: '472'});
  assert.equal(get('description').value, fresh.source_description);
  assert.equal(get('run-all').disabled, false);
});

test('loading the current catalog description requires preparing updated variants', async () => {
  const {get, context} = setup();
  vm.runInContext('current.source_description = "Alter Text.";', context);
  get('description').value = 'Alter Text.';
  context.fetch = async url => ({ok: true, json: async () => url.endsWith('/description')
    ? {description: 'Aktuelle gespeicherte Beschreibung.'} : []});
  await get('load-description').listeners.click();
  assert.equal(get('description').value, 'Aktuelle gespeicherte Beschreibung.');
  assert.equal(get('run-all').disabled, true);
  assert.match(get('description-source').textContent, /alle 17 Fälle/);
});

test('an older server cannot silently reuse the old description when preparing edits', async () => {
  const {get, context, calls} = setup();
  vm.runInContext('workbenchDescriptionUpdates = false;', context);
  get('description').value = 'Neue Beschreibung.';
  await get('prepare').listeners.click();
  assert.match(get('notice').textContent, /Webserver neu starten/);
  assert.equal(calls.filter(([url]) => url.endsWith('/reprepare')).length, 0);
});
