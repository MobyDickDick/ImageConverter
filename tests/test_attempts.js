'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

async function viewer() {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, {hidden: true, value: '40', listeners: {},
      addEventListener(event, handler) {this.listeners[event] = handler;}});
    return elements.get(id);
  };
  const records = [0.1, 0.8, 0.05].map((mse, i) => ({number: i + 1, mse, phase: 'Suche'}));
  const calls = [];
  const context = vm.createContext({
    document: {getElementById: get},
    window: {location: {search: '?job=' + 'a'.repeat(32)}}, URLSearchParams,
    setTimeout() {}, clearTimeout() {},
    fetch: async url => {
      calls.push(url);
      const after = Number(new URL('http://localhost' + url).searchParams.get('after'));
      return {ok: true, json: async () => url.includes('/attempts?')
        ? {total: records.length, attempts: records.filter(item => item.number > after)}
        : {status: 'done', name: 'test.png', attempt_count: records.length}};
    },
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../web/attempts.js'), 'utf8'), context);
  await new Promise(setImmediate);
  return {context, get, calls};
}

test('separate viewer plays every attempt, including worse variants, in order', async () => {
  const {context, get} = await viewer();
  for (let number = 1; number <= 3; number++) {
    vm.runInContext('play()', context);
    assert.match(get('attempt').src, new RegExp(`number=${number}$`));
    get('attempt').onload();
    assert.equal(get('counter').textContent, `Versuch ${number} von 3`);
  }
  assert.equal(get('attempt').hidden, false);
  assert.match(get('status').textContent, /Alle vorhandenen Versuche angezeigt/);
});

test('pause leaves conversion independent and latest explicitly skips the backlog', async () => {
  const {context, get} = await viewer();
  get('pause').listeners.click();
  vm.runInContext('play()', context);
  assert.equal(get('attempt').src, undefined);
  assert.match(get('status').textContent, /Konvertierung läuft unabhängig weiter/);
  await get('latest').listeners.click();
  assert.match(get('attempt').src, /number=3$/);
  get('attempt').onload();
  assert.equal(get('counter').textContent, 'Versuch 3 von 3');
});

test('an image failure retries the same attempt without skipping it', async () => {
  const {context, get} = await viewer();
  vm.runInContext('play()', context);
  get('attempt').onerror();
  vm.runInContext('play()', context);
  assert.match(get('attempt').src, /number=1$/);
  get('attempt').onload();
  vm.runInContext('play()', context);
  assert.match(get('attempt').src, /number=2$/);
});

test('polling during an image load does not enqueue the same attempt twice', async () => {
  const {context, get, calls} = await viewer();
  vm.runInContext('queue = queue.slice(0, 1); play()', context);
  await vm.runInContext('refresh()', context);
  assert.equal(calls.filter(url => url.includes('/attempts?')).length, 1);
  get('attempt').onload();
  await new Promise(setImmediate);
  vm.runInContext('play()', context);
  assert.match(get('attempt').src, /number=2$/);
});
