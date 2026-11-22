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
      requests.push({url, body:typeof options.body === 'string' ? JSON.parse(options.body) : options.body});
      return {ok:true, json:async () => respond(url, options)};
    },
  });
  return {element, timers, requests, run:code => vm.runInContext(code, context),
    load() {
      vm.runInContext(app, context);
      // Most tests start after init, with a server supporting SVG reuse.
      vm.runInContext('currentSvgReuse = true', context);
    }, context};
}

test('live drafts can be saved during a search without stopping it', async () => {
  const h = harness(() => ({saved:true, path:'chosen.svg'})); h.load();
  h.context.job = {...running, result:false, preview:true, preview_revision:'1',
    export_available:true, export_draft:true, export_revision:'1'};
  h.run('renderJob(job, true)');
  assert.equal(h.element('save-actions').hidden, false);
  assert.match(h.element('download').href, /\/export\?v=1&download=1$/);
  await h.element('save-as').listeners.click();
  assert.equal(h.requests[0].url, '/api/jobs/retry/save');
  assert.equal(h.run('activeId'), running.id);
  assert.equal(h.element('cancel').hidden, false);
  assert.match(h.element('save-status').textContent, /chosen.svg/);
});

test('rejected and stopped drafts remain visible and downloadable with a warning', () => {
  for (const status of ['error', 'cancelled', 'timeout', 'interrupted']) {
    const h = harness(); h.load();
    h.context.job = {...ready, status, result:false, quality:'warning',
      export_available:true, export_draft:true, export_revision:'2'};
    h.run('renderJob(job, true)');
    assert.equal(h.element('result-image').hidden, false);
    assert.match(h.element('result-image').src, /\/export\?v=2$/);
    assert.equal(h.element('save-actions').hidden, false);
    assert.match(h.element('quality').textContent, /eigener Beurteilung speichern/);
    assert.equal(h.element('quality').className, 'hint quality-warning');
  }
});

test('saving stays hidden until an SVG exists', () => {
  const h = harness(); h.load(); h.context.job = {...running, export_available:false};
  h.run('renderJob(job, true)');
  assert.equal(h.element('save-actions').hidden, true);
});

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

test('recognition keeps typed descriptions and requires explicit adoption of neighbours', async () => {
  const recognized = {...ready, recognition:{message:'Ähnliches Bild', reference_count:507, automatic:null,
    matches:[{filename:'reference.png', description:'Ein roter Kreis.', source_url:'/source', svg_url:'/svg', exact:false}]}};
  const h = harness(url => url.endsWith('/recognize') ? recognized : []); h.load();
  h.context.job = ready;
  h.run('imageRecognition = true; renderJob(job, true)');
  h.element('description').value = 'Meine ungespeicherte Beschreibung';
  await h.element('recognize').listeners.click();
  assert.equal(h.element('description').value, 'Meine ungespeicherte Beschreibung');
  assert.equal(h.element('recognition-results').children.length, 1);
  const proposal = h.element('recognition-results').children[0];
  proposal.children.at(-1).listeners.click();
  assert.equal(h.element('description').value, 'Ein roter Kreis.');
});

test('empty descriptions are filled by automatic recognition through the real upload flow', async () => {
  const empty = {...ready, description:''};
  const recognized = {...ready, description_origin:'recognition', recognition:{message:'Kreis erkannt', reference_count:0,
    automatic:{kind:'plain_shape', description:ready.description}, matches:[]}};
  const h = harness(url => url.startsWith('/api/upload') ? empty : url.endsWith('/recognize') ? recognized : []);
  h.load(); h.run('imageRecognition = true; editableSearchSeed = true');
  await h.run("upload({name:'renamed.png', size:100})");
  assert.equal(h.element('description').value, ready.description);
  assert.equal(h.element('convert').disabled, false);
  assert.ok(h.requests.some(request => request.url.endsWith('/recognize')));
});

test('text corrections are saved without starting a conversion', async () => {
  const h = harness((url, options) => url.endsWith('/description')
    ? {...ready, description:JSON.parse(options.body).description, description_origin:'user',
      description_save:{scope:'catalog', message:'Im Katalog gespeichert.'}} : []);
  h.load(); h.context.job = ready;
  h.run('descriptionAutosave = true; renderJob(job, true)');
  h.element('description').value = 'Korrigierter Text ohne Konvertierung';
  h.element('description').listeners.input();
  await h.run('saveDescription()');
  assert.equal(h.requests[0].url, '/api/jobs/original/description');
  assert.equal(h.requests[0].body.description, 'Korrigierter Text ohne Konvertierung');
  assert.equal(h.run('descriptionDirty'), false);
  assert.equal(h.element('description-save-status').textContent, 'Im Katalog gespeichert.');
});

test('edits made during a save are serialized and the newest text survives', async () => {
  let finish;
  const h = harness((url, options) => {
    const job = {...ready, description:JSON.parse(options.body).description};
    return h.requests.length === 1 ? new Promise(resolve => {finish = () => resolve(job);}) : job;
  });
  h.load(); h.context.job = ready;
  h.run('descriptionAutosave = true; renderJob(job, true)');
  h.element('description').value = 'Erste Korrektur';
  h.element('description').listeners.input();
  const pending = h.run('saveDescription()');
  await new Promise(resolve => setImmediate(resolve));
  h.element('description').value = 'Zweite Korrektur';
  h.element('description').listeners.input();
  finish(); await pending;
  assert.deepEqual(h.requests.map(request => request.body.description), ['Erste Korrektur', 'Zweite Korrektur']);
  assert.equal(h.run('current.description'), 'Zweite Korrektur');
  assert.equal(h.element('description').value, 'Zweite Korrektur');
});

test('switching to another image waits until its edited text is saved', async () => {
  const h = harness((url, options) => url.endsWith('/description')
    ? {...ready, description:JSON.parse(options.body).description}
    : url.startsWith('/api/upload') ? {...ready, id:'next'} : []);
  h.load(); h.context.job = ready;
  h.run('descriptionAutosave = true; renderJob(job, true)');
  h.element('description').value = 'Vor Bildwechsel sichern';
  h.element('description').listeners.input();
  await h.run("upload({name:'next.png', size:100})");
  assert.equal(h.requests[0].url, '/api/jobs/original/description');
  assert.ok(h.requests[1].url.startsWith('/api/upload'));
  assert.equal(h.run('current.id'), 'next');
});

test('a failed text save keeps the edit and prevents a premature conversion', async () => {
  const h = harness(() => {throw new Error('Speicher nicht verfügbar');});
  h.load(); h.context.job = ready;
  h.run('descriptionAutosave = true; editableSearchSeed = true; renderJob(job, true)');
  h.element('description').value = 'Darf nicht verloren gehen';
  h.element('description').listeners.input();
  await h.element('convert').listeners.click();
  assert.equal(h.run('descriptionDirty'), true);
  assert.equal(h.element('description').value, 'Darf nicht verloren gehen');
  assert.equal(h.element('save-description').disabled, false);
  assert.ok(h.element('description-save-status').textContent.startsWith('Nicht gespeichert'));
  assert.ok(h.requests.every(request => !request.url.endsWith('/start')));
});

test('description check sends the current text without saving or starting conversion', async () => {
  const text = 'Ein rotes Dreieck.';
  const report = {description:text, status:'mismatch', message:'Abweichung erkannt.',
    checks:[{status:'mismatch', message:'Grundform: Dreieck statt Kreis.'}], limitations:'Begrenzte Prüfung.'};
  const h = harness(url => url.endsWith('/check') ? {...ready, description_check:report} : []);
  h.load(); h.context.job = ready;
  h.run('descriptionCheck = true; descriptionAutosave = true; renderJob(job, true)');
  h.element('description').value = text;
  h.element('description').listeners.input();
  await h.element('check-description').listeners.click();
  assert.equal(h.requests[0].url, '/api/jobs/original/check');
  assert.equal(h.requests[0].body.description, text);
  assert.ok(h.requests.every(r => !r.url.endsWith('/description') && !r.url.endsWith('/start')));
  assert.equal(h.element('description').value, text);
  assert.equal(h.run('descriptionDirty'), true);
  assert.equal(h.element('description-check').hidden, false);
  assert.equal(h.element('description-check').children[0].textContent, report.message);
  h.element('description').value = 'Ein grauer Kreis.';
  h.element('description').listeners.input();
  assert.equal(h.element('description-check').children.length, 0);
  assert.match(h.element('description-check').textContent, /keine aktuelle Prüfung/);
});

test('description checks are unavailable during conversion and on an older server', () => {
  const h = harness(); h.load(); h.context.job = ready;
  h.run('renderJob(job, true)');
  assert.equal(h.element('check-description').disabled, true);
  assert.match(h.element('description-check').textContent, /Webserver neu starten/);
  h.run('descriptionCheck = true; controls()');
  assert.equal(h.element('check-description').disabled, false);
  h.run('descriptionSaving = Promise.resolve(); controls()');
  assert.equal(h.element('check-description').disabled, true);
  h.run('descriptionSaving = null');
  h.context.job = running;
  h.run('renderJob(job)');
  assert.equal(h.element('check-description').disabled, true);
});
