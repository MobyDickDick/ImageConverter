const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');

const app = fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8')
  .replace(/\ninit\(\);\s*$/, '');
const ready = {id:'original', name:'image.png', description:'Ein Kreis.', profile:'quick',
  width:32, height:24, status:'ready', search_seed:'9007199254740993'};
const running = {...ready, id:'retry', status:'running'};

function harness(respond = () => []) {
  const elements = new Map(), timers = new Map(), requests = [];
  let created = 0, timer = 0;
  function element(id) {
    if (!elements.has(id)) elements.set(id, {
      value:'', checked:false, hidden:true, style:{}, listeners:{}, children:[], attributes:{},
      clientWidth:600, clientHeight:400, classList:{toggle() {}},
      addEventListener(type, fn) {this.listeners[type] = fn;},
      querySelector(name) {return element(`${id}/${name}`);},
      querySelectorAll() {return this.children;},
      setAttribute(k,v) {this.attributes[k]=v;}, getAttribute(k) {return this.attributes[k];},
      setCustomValidity(v) {this.error=v;}, reportValidity() {return !this.error;},
      replaceChildren() {this.children=[];}, append(...items) {this.children.push(...items);},
    });
    return elements.get(id);
  }
  const context = vm.createContext({
    document:{getElementById:element, querySelector:element, createElement:tag => element(`${tag}-${++created}`)},
    window:{addEventListener() {}, location:{search:'?job=original'}},
    localStorage:{getItem() {return 'false';}},
    crypto:require('node:crypto').webcrypto, Uint32Array, URLSearchParams,
    setTimeout(fn) {timers.set(++timer, fn); return timer;}, clearTimeout(id) {timers.delete(id);},
    requestAnimationFrame(fn) {fn();},
    fetch:async (url, options = {}) => {
      requests.push({url, body:options.body && JSON.parse(options.body)});
      return {ok:true, json:async () => respond(url, options)};
    },
  });
  return {element, timers, requests, run:code => vm.runInContext(code, context),
    load() {vm.runInContext(app, context);}, context};
}

test('rendering a running job restores cancellation even with an older server', () => {
  const h = harness(); h.load();
  h.context.job = running;
  h.run('renderJob(job, true)');
  assert.equal(h.run('activeId'), running.id);
  assert.equal(h.element('cancel').hidden, false);
  assert.equal(h.element('cancel').disabled, false);
  h.context.job = {...running, status:'cancelled'};
  h.run('renderJob(job)');
  assert.equal(h.run('activeId'), null);
  assert.equal(h.element('cancel').hidden, true);
});

test('reload prefers the running retry over an old job URL and starts polling', async () => {
  const h = harness(url => {
    if (url === '/api/config') return {parallel_background_conversion:true, editable_search_seed:true};
    if (url.startsWith('/api/jobs?')) return [running, {...ready, status:'done'}];
    return {...ready, status:'done'};
  }); h.load();
  await h.run('init()');
  assert.equal(h.run('current.id'), running.id);
  assert.equal(h.element('cancel').hidden, false);
  assert.equal(h.element('cancel').disabled, false);
  assert.equal(h.timers.size, 1);
});

test('selecting a running history entry enables cancellation and polling', async () => {
  const h = harness(() => running); h.load();
  h.context.jobs = [running];
  h.run('history = jobs; renderHistory()');
  await h.element('history').children[0].listeners.click();
  assert.equal(h.run('activeId'), running.id);
  assert.equal(h.element('cancel').hidden, false);
  assert.equal(h.timers.size, 1);
});

test('a slow history refresh cannot disable cancellation after start', async () => {
  const historyRequests = [];
  const h = harness(url => url.startsWith('/api/jobs?')
    ? new Promise(resolve => {historyRequests.push(resolve);})
    : {...running, status:'cancelled'});
  h.load(); h.context.job = running;
  const updating = h.run('update(async () => job)');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.element('cancel').disabled, false);
  assert.equal(h.element('cancel').hidden, false);
  assert.equal(h.timers.size, 1);
  // The actual click must target the retry, not the original from the URL.
  const cancelling = h.element('cancel').listeners.click();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.requests.find(r => r.url.endsWith('/cancel')).url, '/api/jobs/retry/cancel');
  for (const finish of historyRequests) finish([]);
  await cancelling;
  await updating;
  assert.equal(h.element('cancel').hidden, true);
});

test('seed edits keep full precision and remain independent of cancellation', async () => {
  const h = harness(url => url.endsWith('/start') ? running : []); h.load();
  h.context.job = ready;
  h.run('editableSearchSeed = true; renderJob(job, true)');
  h.element('seed').value = '18446744073709551615';
  await h.element('convert').listeners.click();
  assert.equal(h.requests[0].body.seed, '18446744073709551615');
  assert.equal(h.element('seed').disabled, true);
  assert.equal(h.element('cancel').disabled, false);
});
