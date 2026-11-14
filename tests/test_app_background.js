'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function element() {
  return {value: '', hidden: false, disabled: false, textContent: '', children: [],
    clientWidth: 400, clientHeight: 300, attributes: {}, listeners: {},
    classList: {toggle() {}}, style: {},
    append(...items) {this.children.push(...items);},
    replaceChildren(...items) {this.children = items;},
    addEventListener(name, handler) {this.listeners[name] = handler;},
    getAttribute(name) {return this.attributes[name];},
    setAttribute(name, value) {this.attributes[name] = value;},
    querySelector() {return this.child ||= element();},
    querySelectorAll() {return this.children;}};
}

test('incremental native previews refresh while conversion remains active', () => {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  const context = vm.createContext({
    document: {getElementById: get, createElement: element, querySelector: element},
    window: {location: {search: ''}, addEventListener() {}}, URLSearchParams,
    setTimeout() {}, clearTimeout() {}, fetch: () => new Promise(() => {}),
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8'), context);
  const job = {id: 'c'.repeat(32), name: 'draft.png', status: 'running', description: 'Zwei Pfeile.',
    width: 40, height: 140, quality: 'warning', preview: true, preview_revision: 1, result: false};
  context.job = job;
  vm.runInContext('renderJob(job)', context);
  assert.equal(get('result-image').hidden, false);
  assert.equal(get('result-empty').hidden, true);
  assert.equal(get('save-actions').hidden, true);
  assert.match(get('result-image').src, /\/preview\?v=1$/);
  job.preview_revision = 2;
  vm.runInContext('renderJob(job)', context);
  assert.match(get('result-image').src, /\/preview\?v=2$/);
  // The switch works immediately, including a result collected between phases.
  job.result = true;
  get('show-intermediate').checked = false;
  get('show-intermediate').listeners.change();
  assert.equal(get('result-image').hidden, true);
  assert.equal(get('result-empty').hidden, false);
  assert.equal(get('save-actions').hidden, true);
  assert.match(get('result-empty').querySelector('p').textContent, /Endergebnis/);
  get('show-intermediate').checked = true;
  get('show-intermediate').listeners.change();
  assert.equal(get('result-image').hidden, false);
  assert.match(get('result-meta').textContent, /Zwischenstand/);
  get('show-intermediate').checked = false;
  job.status = 'done'; job.result = true;
  vm.runInContext('renderJob(job)', context);
  assert.match(get('result-image').src, /\/result$/);
  assert.equal(get('save-actions').hidden, false);
});

test('intermediate display preference survives a reload', () => {
  const storage = new Map([['imageconverter.showIntermediate', 'false']]);
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  const context = vm.createContext({
    document: {getElementById: get, createElement: element, querySelector: element},
    window: {location: {search: ''}, addEventListener() {}}, URLSearchParams,
    localStorage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value)},
    setTimeout() {}, clearTimeout() {}, fetch: () => new Promise(() => {}),
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8'), context);
  assert.equal(get('show-intermediate').checked, false);
  get('show-intermediate').checked = true;
  get('show-intermediate').listeners.change();
  assert.equal(storage.get('imageconverter.showIntermediate'), 'true');
});

for (const parallel of [false, true]) {
  test(`manual conversion stays usable with background jobs (parallel server: ${parallel})`, async () => {
    const elements = new Map();
    const get = id => {
      if (!elements.has(id)) elements.set(id, element());
      return elements.get(id);
    };
    const manual = {id: 'a'.repeat(32), name: 'manual.png', status: 'ready',
      description: 'Ein Kreis.', profile: 'quick', width: 32, height: 24};
    const background = {id: 'b'.repeat(32), status: 'running', catalog_background: true};
    const calls = [];
    const timers = [];
    const context = vm.createContext({
      document: {getElementById: get, createElement: element, querySelector: element},
      window: {location: {search: ''}, addEventListener() {}}, URLSearchParams,
      setTimeout(fn) {timers.push(fn); return timers.length;}, clearTimeout() {},
      fetch: async (url, options) => {
        calls.push([url, options]);
        let result;
        if (url === '/api/config') result = {native_file_dialogs: false,
          ...(parallel ? {parallel_background_conversion: true} : {})};
        // An older server ignores scope=foreground and returns both lanes.
        else if (url === '/api/jobs?scope=foreground') result = [background, manual];
        else if (url === `/api/jobs/${manual.id}/start`) result = {...manual, status: 'running'};
        else throw new Error(`Unexpected URL: ${url}`);
        return {ok: true, json: async () => result};
      },
    });
    vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8'), context);
    await new Promise(setImmediate);
    assert.equal(get('notice').textContent, '');
    assert.equal(get('file-info').textContent, 'manual.png · 32 × 24 px');
    assert.equal(get('history-count').textContent, 1);
    assert.equal(get('convert').disabled, false);
    assert.equal(get('file').disabled, false);
    assert.equal(get('cancel').hidden, true);
    assert.equal(timers.length, 0); // The background job is never adopted as activeId.
    if (!parallel) {
      assert.equal(get('server-version-warning').hidden, false);
      assert.match(get('server-version-warning').textContent, /stopWebServer.cmd/);
    }
    await get('convert').listeners.click();
    assert.equal(get('notice').textContent, '');
    assert.equal(calls.filter(([url]) => url.endsWith('/start')).length, 1);
    assert.equal(get('convert').disabled, true);
    assert.equal(get('cancel').hidden, false);
    assert.equal(timers.length, 1);
  });
}
