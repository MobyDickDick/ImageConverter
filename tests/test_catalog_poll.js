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
    listeners: {}, attributes: {},
    addEventListener(type, handler) {this.listeners[type] = handler;},
    setAttribute(name, value) {this.attributes[name] = value;}, removeAttribute() {}};
}

test('delete selection survives filtering, reports failures and removes only submitted originals', async () => {
  const elements = new Map(), requests = [];
  const get = id => {
    if (!elements.has(id)) elements.set(id, element());
    return elements.get(id);
  };
  get('sort').value = 'filename'; get('page-size').value = '25';
  let rows = ['first.jpg', 'second.jpg', 'reserved.jpg'].map(filename => ({
    filename, image:'artifacts/images_to_convert/'+filename, description:'',
    status:filename === 'reserved.jpg' ? 'reserved' : 'no_svg', candidates:[], archived:false,
  }));
  let fail = true;
  const context = vm.createContext({
    document:{getElementById:get, createElement:element, createDocumentFragment:element},
    Option:function(text, value) {return {text, value};}, setInterval() {},
    fetch:async (url, options = {}) => {
      if (url === '/api/catalog/delete') {
        const body = JSON.parse(options.body); requests.push(body);
        if (fail) return {ok:false, status:409, json:async () => ({error:'Bitte zuerst stoppen.'})};
        rows = rows.filter(row => !body.filenames.includes(row.filename));
        return {ok:true, json:async () => ({deleted:body.filenames, message:'1 Bild verschoben.'})};
      }
      return {ok:true, json:async () => url === '/api/catalog/list' ? {rows, summary:{}, labels:{}}
        : {status:'idle', summary:{}}};
    },
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/catalog.js'),'utf8'), context);
  await new Promise(setImmediate);
  const firstRow = get('rows').children[0].children[0];
  const checkbox = firstRow.children[0].children[2].children[0];
  assert.equal(checkbox.type, 'checkbox');
  assert.match(checkbox.attributes['aria-label'], /first.jpg/);
  checkbox.checked = true; checkbox.listeners.change();
  assert.equal(get('delete-selected').disabled, false);
  assert.match(get('delete-selected').textContent, /\(1\)/);
  get('search').value = 'second';
  get('search').listeners.input();
  assert.equal(vm.runInContext('deleteSelection.has("first.jpg")', context), true);
  vm.runInContext('showJob({status:"running"})', context);
  assert.equal(get('delete-selected').disabled, true);
  vm.runInContext('showJob({status:"idle"})', context);
  await get('delete-selected').onclick();
  assert.equal(get('delete-status').textContent, 'Bitte zuerst stoppen.');
  assert.equal(get('delete-selected').disabled, false);
  fail = false;
  await get('delete-selected').onclick();
  assert.deepEqual(requests, [{filenames:['first.jpg']}, {filenames:['first.jpg']}]);
  assert.equal(get('delete-status').textContent, '1 Bild verschoben.');
  assert.equal(get('delete-selected').disabled, true);
  assert.equal(vm.runInContext('data.rows.length', context), 2);
  get('search').value = 'reserved'; get('search').listeners.input();
  assert.equal(get('rows').children[0].children[0].children[0].children.length, 1);
});

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

test('overview shows next image, live inspection and actual last SVG outcome', async () => {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id,element());
    return elements.get(id);
  };
  get('sort').value = 'filename'; get('page-size').value = '25';
  const service = {status:'running',phase:'refresh',round:1,
    next:{filename:'AA0010.jpg',image:'artifacts/images_to_convert/AA0010.jpg',mse:.002,
      round:1,attempt:2,provisional:true,conditional:true},
    last_attempt:{filename:'AA0011.jpg',job_id:'a'.repeat(32),round:1,attempt:1,
      result:true,passed:null,checking:true,message:'SVG erzeugt.'},
    inspection:{elapsed:158,progress:{completed:762,total:1787,measured:1284,cached:4}},
    log:'Inventar 762/1787'};
  const context = vm.createContext({
    document:{getElementById:get,createElement:element,createDocumentFragment:element},
    Option:function(text,value) {return {text,value};}, setInterval() {},
    fetch:async url => ({ok:true,status:200,json:async () =>
      url === '/api/catalog/list' ? {rows:[],summary:{},labels:{}} :
      url === '/api/catalog/conversion' ? service : {status:'running',summary:{}}}),
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/catalog.js'),'utf8'),context);
  await new Promise(setImmediate);
  assert.match(get('conversion-next-name').textContent,/AA0010.jpg/);
  assert.match(get('conversion-next-note').textContent,/Vorläufig/);
  assert.match(get('conversion-inspection-status').textContent,/762\/1787/);
  assert.equal(get('conversion-inspection-progress').value,762);
  assert.equal(get('conversion-log').textContent,'Inventar 762/1787');
  assert.match(get('conversion-last-name').textContent,/AA0011.jpg/);
  assert.equal(get('conversion-last-status').textContent,'SVG-Prüfung läuft …');
  const images = get('conversion-last-preview').children;
  assert.equal(images[0].children[1].children[0].src,`/api/jobs/${'a'.repeat(32)}/source`);
  assert.equal(images[1].children[1].children[0].src,`/api/jobs/${'a'.repeat(32)}/result`);
  const nextImage = get('conversion-next-preview').children[0];
  service.last_attempt.checking = false; service.last_attempt.passed = true;
  service.last_attempt.measurement = {renderers:{mupdf:{satisfactory:true,metrics:{normalized_mse:.001}}}};
  await vm.runInContext('poll()',context);
  assert.match(get('conversion-last-status').textContent,/Erfolgreich/);
  assert.match(get('conversion-last-metrics').textContent,/0.001000/);
  assert.equal(get('conversion-next-preview').children[0],nextImage);
  service.inspection.progress = {completed:0,total:1,measured:0,cached:0};
  await vm.runInContext('poll()',context);
  assert.match(get('conversion-inspection-status').textContent,/Nur das neue SVG wird geprüft: 0\/1/);
  service.last_attempt.passed = false; service.last_attempt.result = false;
  await vm.runInContext('poll()',context);
  assert.match(get('conversion-last-status').textContent,/Nicht erfolgreich/);
  assert.equal(get('conversion-last-preview').children[1].children[1].textContent,'Kein SVG erzeugt.');
});

test('a running older server provides previews without interrupting its work', async () => {
  const elements = new Map(), get = id => {
    if (!elements.has(id)) elements.set(id,element());
    return elements.get(id);
  };
  get('sort').value='filename'; get('page-size').value='25';
  const id='b'.repeat(32);
  const measurement = passed => ({renderers:Object.fromEntries(['mupdf','librsvg'].map(name =>
    [name,{satisfactory:passed,metrics:{normalized_mse:.002}}]))});
  const rows=[{filename:'AA0011.jpg',role:'catalog',status:'pixel_pass',description:'Kreis',
    candidates:[{svg:'old.svg',measurement:measurement(true)},
      {svg:`artifacts/converted_images/catalog_background_svgs/${id}/AA0011.svg`,measurement:measurement(false)}]},
    {filename:'AA0012.jpg',image:'artifacts/images_to_convert/AA0012.jpg',role:'catalog',
      status:'pixel_fail',description:'Rechteck',selected:{measurement:measurement(false)}}];
  const service={status:'running',phase:'refresh',round:1,attempt:1,filename:'AA0011.jpg',
    job:{id,name:'AA0011.jpg',status:'done',result:true,message:'SVG erzeugt.'}};
  const context=vm.createContext({
    document:{getElementById:get,createElement:element,createDocumentFragment:element},
    Option:function(text,value) {return {text,value};}, setInterval() {},fixtureRows:rows,
    fetch:async url => ({ok:true,status:200,json:async () =>
      url === '/api/catalog/list' ? {rows:[],summary:{},labels:{}} :
      url === '/api/catalog/conversion' ? service :
        {status:'running',summary:{},progress:{completed:4,total:10,measured:4,cached:0,elapsed_seconds:20}}}),
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/catalog.js'),'utf8'),context);
  await new Promise(setImmediate);
  await vm.runInContext('data.rows=fixtureRows; poll()',context);
  assert.match(get('conversion-next-name').textContent,/AA0012.jpg/);
  assert.match(get('conversion-last-name').textContent,/AA0011.jpg/);
  assert.match(get('conversion-last-status').textContent,/Nicht erfolgreich/);
  assert.match(get('conversion-inspection-status').textContent,/4\/10/);
  assert.match(get('conversion-log').textContent,/Qualitätsprüfung: 4\/10/);
});
