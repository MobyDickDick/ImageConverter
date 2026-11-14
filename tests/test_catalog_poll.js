'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

function element() {
  return {value: '', hidden: false, disabled: false, textContent: '', children: [],
    append(...items) {this.children.push(...items);},
    replaceChildren(...items) {this.children = items;},
    addEventListener() {}, removeAttribute() {}};
}

test('missing background API preserves catalog polling and recovers after restart', async () => {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  get('sort').value = 'filename';
  get('page-size').value = '25';
  let available = false;
  const context = vm.createContext({
    document: {getElementById: get, createElement: element, createDocumentFragment: element},
    Option: function(text,value) {return {text,value};},
    setInterval() {},
    fetch: async url => {
      let status = 200, value;
      if (url === '/api/catalog/list') value = {rows: [], summary: {}, labels: {}};
      else if (url === '/api/catalog') value = available
        ? {status: 'done', message: 'Liste aktuell.', summary: {}}
        : {status: 'running', progress: {total:10,completed:4,measured:4,cached:0}, summary: {}};
      else if (url === '/api/catalog/conversion') {
        status = available ? 200 : 404;
        value = available ? {status: 'idle',message: 'Dienst bereit.'} : {error: 'Nicht gefunden.'};
      } else throw new Error('Unexpected URL: '+url);
      return {ok: status === 200, status, json: async () => value};
    },
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/catalog.js'),'utf8'),context);
  await new Promise(setImmediate);
  assert.match(get('run-status').textContent,/4\/10 Bilder/);
  assert.equal(get('progress').value,4);
  assert.match(get('notice').textContent,/alten ImageConverter-Webserver beenden/);
  assert.match(get('conversion-status').textContent,/neu starten/);
  assert.equal(get('conversion-start').disabled,true);
  assert.equal(get('conversion-stop').disabled,true);
  available = true;
  await vm.runInContext('poll()',context);
  assert.equal(get('run-status').textContent,'Liste aktuell.');
  assert.match(get('conversion-status').textContent,/Dienst bereit/);
  assert.equal(get('notice').hidden,true);
  assert.equal(get('conversion-start').disabled,false);
  assert.equal(get('conversion-profile').disabled,false);
});
