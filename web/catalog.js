'use strict';
const el = id => document.getElementById(id);
let data = {rows: [], summary: {}, labels: {}}, page = 0, lastReport = '', polling = false;
const reportKey = summary => JSON.stringify([summary.generated_at || '', summary.catalog_statuses || {}]);
const asset = path => '/api/catalog/asset?path=' + encodeURIComponent(path);
function node(tag, text, cls) {
  const result = document.createElement(tag);
  if (text !== undefined) result.textContent = text;
  if (cls) result.className = cls;
  return result;
}
async function api(path, body) {
  const options = body === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json', 'X-ImageConverter': '1'}, body: JSON.stringify(body)};
  const response = await fetch(path, options), value = await response.json();
  if (!response.ok) throw new Error(value.error || 'Die Anfrage ist fehlgeschlagen.');
  return value;
}
function notice(error) { el('notice').textContent = error.message; el('notice').hidden = false; }
function metrics(row) {
  const renderers = Object.values(row.selected?.measurement?.renderers || {});
  const worst = (key, fn) => { const values = renderers.map(r => r.metrics?.[key]).filter(Number.isFinite); return values.length ? fn(...values) : null; };
  return {mse: worst('normalized_mse', Math.max), edge: worst('edge_alignment', Math.min), iou: worst('foreground_iou', Math.min)};
}
function link(text, path) { const a = node('a', text); a.href = asset(path); a.target = '_blank'; a.rel = 'noopener'; return a; }
function render() {
  const search = el('search').value.trim().toLocaleLowerCase('de');
  let rows = data.rows.filter(r => (!search || (r.filename + ' ' + r.description + ' ' + (r.classification?.label || '')).toLocaleLowerCase('de').includes(search)) && (!el('geometry-class').value || r.classification?.class_id === el('geometry-class').value) && (!el('status').value || r.status === el('status').value) && (!el('archive').value || r.archived === (el('archive').value === 'yes')));
  const order = el('sort').value;
  rows.sort((a,b) => {
    if (order.startsWith('mse-')) {
      const x = metrics(a).mse, y = metrics(b).mse;
      if (x === null || y === null) return x === y ? a.filename.localeCompare(b.filename) : x === null ? 1 : -1;
      return (x-y) * (order === 'mse-desc' ? -1 : 1) || a.filename.localeCompare(b.filename);
    }
    return (order === 'status' ? a.status.localeCompare(b.status) : 0) || a.filename.localeCompare(b.filename);
  });
  const size = el('page-size').value === 'all' ? Math.max(1, rows.length) : Number(el('page-size').value);
  const pages = Math.max(1, Math.ceil(rows.length/size)); page = Math.min(page, pages-1);
  el('count').textContent = `${rows.length.toLocaleString('de-CH')} von ${data.rows.length.toLocaleString('de-CH')} Bildern`;
  el('page').textContent = `Seite ${page+1} / ${pages}`;
  el('previous').disabled = page === 0; el('next').disabled = page >= pages-1;
  const body = document.createDocumentFragment();
  for (const row of rows.slice(page*size, (page+1)*size)) {
    const tr = node('tr'), image = node('td');
    image.append(node('strong', row.filename));
    if (row.status !== 'reserved') {
      const thumbs = node('div', undefined, 'thumbs');
      for (const [title, path] of [['Original', row.image], ['SVG', row.selected?.svg]]) {
        if (!path) continue;
        const a = link('', path), img = node('img'); img.src = asset(path); img.alt = title + ' ' + row.filename; img.loading = 'lazy'; a.append(img); thumbs.append(a);
      }
      image.append(thumbs);
    }
    const quality = node('td'); quality.append(node('span', data.labels[row.status] || row.status, 'badge ' + row.status));
    const m = metrics(row), metric = node('td', undefined, 'metric');
    metric.append(node('div', 'MSE: ' + (m.mse === null ? '—' : m.mse.toFixed(6))), node('div', 'Kanten: ' + (m.edge === null ? '—' : m.edge.toFixed(4))), node('div', 'IoU: ' + (m.iou === null ? '—' : m.iou.toFixed(4))));
    const archive = node('td', row.archived ? 'Historisch archiviert' : 'Nicht archiviert');
    if (row.archived) {
      const ar = row.archive;
      if (!ar.source_matches || !ar.image_hash_matches || !ar.svg_hash_matches) archive.append(node('small', 'Prüfsummenabweichung'));
      if (!ar.description_matches_catalog) archive.append(node('small', 'Beschreibung abweichend'));
      if (ar.evidence_exists) archive.append(link('Abnahmebeleg', ar.evidence));
      else archive.append(node('small', 'Abnahmebeleg fehlt'));
    }
    const detail = node('td');
    const classification = row.classification;
    if (classification) {
      detail.append(node('strong', classification.label));
      detail.append(node('small', classification.basis === 'visual_audit' ? 'Zuordnung durch Codex-Sichtprüfung' : classification.basis === 'reservation' ? 'Reserviert' : 'Automatischer Vorschlag aus der Beschreibung'));
      if (classification.basis === 'visual_audit') detail.append(node('div', classification.reason));
      if (classification.description_issue) detail.append(node('small', 'Beschreibung klären: ' + classification.description_issue));
      const models = node('details'); models.append(node('summary', 'Vorhandene Modelle und Grenzen'));
      models.append(node('p', classification.model_modules.join(', ') || 'Kein allgemeines Modell'), node('p', classification.model_limit)); detail.append(models);
    }
    detail.append(node('div', row.description || 'Keine Beschreibung vorhanden.'));
    const more = node('details'); more.append(node('summary', `${row.candidates.length} gespeicherte SVG-Kandidaten · Prüfbefunde`));
    const list = node('ul');
    for (const candidate of row.candidates) {
      const item = node('li'); item.append(link(candidate.svg, candidate.svg));
      const measurement = candidate.measurement;
      if (measurement.error) item.append(node('small', measurement.error));
      for (const [name, value] of Object.entries(measurement.renderers || {})) {
        item.append(node('small', `${name}: ${value.error || (value.satisfactory ? 'Rastergates erfüllt' : (value.failures || []).join(', ') || 'Rastergates verfehlt')}`));
      }
      if (measurement.measured_at) item.append(node('small', 'Gemessen: ' + new Date(measurement.measured_at).toLocaleString('de-CH')));
      list.append(item);
    }
    more.append(list, node('small', 'Vollständige fachliche Neubewertung: nicht durchgeführt.')); detail.append(more);
    tr.append(image, quality, metric, archive, detail); body.append(tr);
  }
  el('rows').replaceChildren(body); el('empty').hidden = rows.length > 0;
}
async function loadList() {
  data = await api('/api/catalog/list');
  const old = el('status').value;
  el('status').replaceChildren(new Option('Alle Qualitätsstände', ''), ...Object.entries(data.labels).map(([key,label]) => new Option(label,key)));
  el('status').value = old;
  const oldClass = el('geometry-class').value;
  el('geometry-class').replaceChildren(new Option('Alle Klassen', ''), ...Object.entries(data.summary.geometry_classes?.classes || {}).map(([key,value]) => new Option(`${value.label} (${value.total})`,key)));
  el('geometry-class').value = oldClass;
  const s = data.summary, counts = s.catalog_statuses || {};
  el('stats').replaceChildren(...[[s.catalog_bitmaps || 0,'Katalogbilder'],[counts.pixel_pass || 0,'Rastergates erfüllt'],[s.archived || 0,'Historisch archiviert'],[counts.pixel_fail || 0,'Rastergates verfehlt'],[(counts.no_svg || 0) + (counts.measurement_error || 0),'Ohne SVG / Messfehler']].map(([value,label]) => {const n=node('div',undefined,'stat');n.append(node('strong',value.toLocaleString('de-CH')),node('span',label));return n;}));
  el('updated').textContent = s.generated_at ? 'Letzte vollständige Prüfung: ' + new Date(s.generated_at).toLocaleString('de-CH') : 'Noch keine vollständige Qualitätsliste vorhanden.';
  lastReport = reportKey(s); render();
}
function showJob(job) {
  const running = ['running','cancelling'].includes(job.status), p = job.progress || {};
  el('refresh').disabled = running; el('force').disabled = running;
  el('stop').hidden = !running; el('stop').disabled = job.status === 'cancelling';
  el('progress').hidden = !running;
  if (p.total) {el('progress').max=p.total;el('progress').value=p.completed;} else el('progress').removeAttribute('value');
  const progress = running && p.total ? ` ${p.completed}/${p.total} Bilder; ${p.measured} neue Paarprüfungen, ${p.cached} wiederverwendet.` : '';
  const message = job.status === 'running' && p.total ? 'Qualitätsprüfung läuft. Die bisherige Liste bleibt verfügbar.' : (job.message || 'Die gespeicherte Qualitätsliste ist verfügbar.');
  el('run-status').textContent = message + progress;
  el('log').hidden = !job.id;
}
async function poll() {
  if (polling) return; polling = true;
  try {
    const job = await api('/api/catalog'); showJob(job);
    if (reportKey(job.summary) !== lastReport) await loadList();
  } catch (error) {notice(error);} finally {polling = false;}
}
for (const id of ['search','geometry-class','status','archive','sort','page-size']) el(id).addEventListener(id === 'search' ? 'input' : 'change', () => {page=0;render();});
el('previous').onclick = () => {page--;render();}; el('next').onclick = () => {page++;render();};
el('refresh').onclick = async () => {el('notice').hidden=true;el('refresh').disabled=true;try {showJob(await api('/api/catalog/start',{force:el('force').checked}));} catch(error) {notice(error);await poll();}};
el('stop').onclick = async () => {el('stop').disabled=true;try {showJob(await api('/api/catalog/cancel',{}));} catch(error) {notice(error);await poll();}};
loadList().then(poll).catch(notice);
setInterval(poll,1500);
