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
    setCustomValidity(message) {this.validationMessage = message;},
    reportValidity() {return !this.validationMessage;},
    querySelector() {return this.child ||= element();},
    querySelectorAll() {return this.children;}};
}

function popup() {
  return {closed: false, location: {replace() {}}, close() {this.closed = true;}};
}

test('missing spray dashes are explained without asking to change a correct description', () => {
  const context = vm.createContext({
    document: {getElementById: element, createElement: element, querySelector: element},
    window: {location: {search: ''}, addEventListener() {}}, URLSearchParams,
    setTimeout() {}, clearTimeout() {}, fetch: () => new Promise(() => {}),
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8'), context);
  context.job = {status: 'done', result: true, quality: 'warning', pixel_quality: {passed: true},
    description_error: 'missing_described_dashed_spray_rays: expected=15, observed=0'};
  const quality = vm.runInContext('draftQuality(job)', context);
  assert.match(quality.message, /15 gestrichelte Linien/);
  assert.match(quality.message, /0 bestätigt/);
  assert.doesNotMatch(quality.message, /passe die Beschreibung an/);
});

test('incremental native previews refresh while conversion remains active', () => {
  const elements = new Map();
  const opened = [];
  const redirects = [];
  const get = id => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  const context = vm.createContext({
    crypto: require('node:crypto').webcrypto,
    document: {getElementById: get, createElement: element, querySelector: element},
    window: {location: {search: ''}, addEventListener() {}, open() {
      const child = popup();
      child.location.replace = url => redirects.push(url);
      opened.push(child);
      return child;
    }}, URLSearchParams,
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
  assert.equal(opened.length, 1);
  assert.match(get('result-meta').textContent, /Zwischenstand/);
  // A retry gets a new job; the existing popup follows it without another open.
  context.job = {...job, id: 'e'.repeat(32)};
  vm.runInContext('renderJob(job)', context);
  assert.deepEqual(redirects, ['/attempts?job=' + 'e'.repeat(32)]);
  get('show-intermediate').checked = false;
  get('show-intermediate').listeners.change();
  assert.equal(opened[0].closed, true);
  job.status = 'done'; job.result = true;
  context.job = job;
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
    window: {location: {search: ''}, addEventListener() {}, open: popup}, URLSearchParams,
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
    const opened = [];
    const timers = [];
    const context = vm.createContext({
      crypto: require('node:crypto').webcrypto,
      document: {getElementById: get, createElement: element, querySelector: element},
      window: {location: {search: ''}, addEventListener() {},
        open(...args) {opened.push(args); return popup();}}, URLSearchParams,
      setTimeout(fn) {timers.push(fn); return timers.length;}, clearTimeout() {},
      fetch: async (url, options) => {
        calls.push([url, options]);
        let result;
        if (url === '/api/config') result = {native_file_dialogs: false, editable_search_seed: true, current_svg_reuse: true,
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
    assert.equal(get('use-current-svg').checked, true);
    get('use-current-svg').checked = false;
    await get('convert').listeners.click();
    assert.equal(opened.length, 1);
    assert.equal(opened[0][0], `/attempts?job=${manual.id}`);
    assert.match(opened[0][2], /popup=yes/);
    assert.equal(get('notice').textContent, '');
    assert.equal(calls.filter(([url]) => url.endsWith('/start')).length, 1);
    assert.equal(JSON.parse(calls.find(([url]) => url.endsWith('/start'))[1].body).use_current_svg,false);
    assert.equal(get('convert').disabled, true);
    assert.equal(get('cancel').hidden, false);
    assert.equal(timers.length, 1);
  });
}

test('Plan B receives the current editor text even before autosave', async () => {
  const elements = new Map(), calls = [];
  const get = id => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  let destination;
  const context = vm.createContext({
    document: {getElementById: get, createElement: element, querySelector: element},
    window: {location: {search: '', assign(url) {destination = url;}}, addEventListener() {}},
    URLSearchParams, setTimeout() {}, clearTimeout() {},
    fetch: async (url, options) => {
      if (url === '/api/config') return new Promise(() => {});
      calls.push([url, options]);
      return {ok: true, json: async () => ({id: 'b'.repeat(32), source_description: JSON.parse(options.body).description})};
    },
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8'), context);
  vm.runInContext('current = {id: "' + 'a'.repeat(32) + '", description: "Alter Text."};', context);
  get('description').value = 'Aktuelle Beschreibung mit grauem Rahmen.';
  await get('use-plan-b').listeners.click();
  const [url, options] = calls.find(([url]) => url.endsWith('/workbench'));
  assert.equal(url, '/api/jobs/' + 'a'.repeat(32) + '/workbench');
  assert.deepEqual(JSON.parse(options.body), {description: get('description').value});
  assert.equal(destination, '/workbench?run=' + 'b'.repeat(32));
});
