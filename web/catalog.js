'use strict';
const el = id => document.getElementById(id);
let data = {rows: [], summary: {}, labels: {}}, page = 0, lastReport = '', polling = false, conversionActive = false, conversionAvailable = true;
let legacyLastJob = null;
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
  if (!response.ok) {
    const error = new Error(value.error || 'Die Anfrage ist fehlgeschlagen.');
    error.status = response.status;
    throw error;
  }
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
  el('refresh').disabled = running || conversionActive; el('force').disabled = running || conversionActive;
  el('stop').hidden = !running || conversionActive; el('stop').disabled = job.status === 'cancelling';
  el('conversion-start').disabled = running || conversionActive || !conversionAvailable;
  el('progress').hidden = !running;
  if (p.total) {el('progress').max=p.total;el('progress').value=p.completed;} else el('progress').removeAttribute('value');
  const progress = running && p.total ? ` ${p.completed}/${p.total} Bilder; ${p.measured} neue Paarprüfungen, ${p.cached} wiederverwendet.` : '';
  const message = job.status === 'running' && p.total ? 'Qualitätsprüfung läuft. Die bisherige Liste bleibt verfügbar.' : (job.message || 'Die gespeicherte Qualitätsliste ist verfügbar.');
  el('run-status').textContent = message + progress;
  el('log').hidden = !job.id;
}
function showPreview(id, items) {
  const target = el(id), key = JSON.stringify(items);
  if (target.previewKey === key) return;
  target.previewKey = key;
  target.replaceChildren(...items.map(([title,url]) => {
    const figure = node('figure'); figure.append(node('figcaption',title));
    if (url) {
      const a = node('a'), img = node('img'); a.href = url; a.target = '_blank'; a.rel = 'noopener';
      img.src = url; img.alt = title; a.append(img); figure.append(a);
    } else figure.append(node('p','Kein SVG erzeugt.','hint'));
    return figure;
  }));
}
function showConversionOverview(service) {
  const next = service.next, last = service.last_attempt;
  el('conversion-next-name').textContent = next ? `${next.filename} · Runde ${next.round}, Versuch ${next.attempt}/3` : 'Kein bewertbares offenes Bild in der aktuellen Liste.';
  el('conversion-next-note').textContent = next
    ? `Bisheriger MSE: ${next.mse.toFixed(6)}. ${next.conditional ? 'Voraussichtliche Auswahl, falls das aktuelle Bild weiterhin offen bleibt. ' : ''}${next.provisional ? 'Vorläufig bis zum Abschluss der Qualitätsprüfung.' : 'Auswahl wird nach jedem Prüfergebnis neu berechnet.'}` : '';
  showPreview('conversion-next-preview',next ? [['Original '+next.filename,asset(next.image)]] : []);
  el('conversion-last-name').textContent = last ? `${last.filename} · Runde ${last.round}, Versuch ${last.attempt}/3` : 'Noch kein Hintergrundversuch abgeschlossen.';
  const badge = el('conversion-last-status');
  badge.textContent = !last ? 'Noch kein Ergebnis' : last.checking ? 'SVG-Prüfung läuft …' : last.passed === null ? 'Prüfergebnis noch offen' : last.passed ? 'Erfolgreich · beide Rasterprüfungen erfüllt' : 'Nicht erfolgreich · Rasterprüfung nicht bestanden';
  badge.className = 'badge '+(!last || last.checking || last.passed === null ? '' : last.passed ? 'pixel_pass' : 'pixel_fail');
  showPreview('conversion-last-preview',last ? [['Original',`/api/jobs/${last.job_id}/source`],['Erzeugtes SVG',last.result ? `/api/jobs/${last.job_id}/result` : null]] : []);
  const failures = Object.entries(last?.measurement?.renderers || {}).map(([name,r]) => `${name}: ${r.error || (r.satisfactory ? 'erfüllt' : (r.failures || []).join(', ') || 'verfehlt')}`);
  el('conversion-last-detail').textContent = last ? [last.message,...failures].filter(Boolean).join(' · ') : '';
  const m = metrics({selected:{measurement:last?.measurement}});
  el('conversion-last-metrics').textContent = last && m.mse !== null ? `MSE: ${m.mse.toFixed(6)} · Kanten: ${m.edge?.toFixed(4) ?? '—'} · IoU: ${m.iou?.toFixed(4) ?? '—'}` : '';
  const inspection = service.inspection, p = inspection?.progress || {};
  el('conversion-inspection-status').hidden = !inspection;
  el('conversion-inspection-status').textContent = inspection ? `Vorhandene SVGs werden geprüft: ${p.completed ?? 0}/${p.total || '?'} Bilder · ${p.measured ?? 0} neue Paarprüfungen · ${p.cached ?? 0} wiederverwendet · seit ${Math.round(inspection.elapsed || 0)} s. Danach wird die Konvertierung fortgesetzt.` : '';
  const progress = el('conversion-inspection-progress'); progress.hidden = !inspection;
  if (p.total) {progress.max=p.total;progress.value=p.completed;} else progress.removeAttribute('value');
}
function showConversion(service) {
  showConversionOverview(service);
  conversionAvailable = true;
  conversionActive = ['running','stopping'].includes(service.status);
  el('conversion-start').disabled = conversionActive;
  el('conversion-stop').disabled = !conversionActive || service.status === 'stopping';
  el('conversion-profile').disabled = conversionActive;
  el('conversion-status').textContent = `${service.message || 'Hintergrunddienst ist gestoppt.'} Runde ${service.round || 1} · ${service.completed || 0} Versuche abgeschlossen · ${service.passed || 0} Rastergates erfüllt · ${service.failed || 0} erfolglose Versuche · ${(service.deferred || []).length} Bilder zurückgestellt.`;
  const job = service.job;
  el('conversion-current').textContent = service.filename ? `${service.filename} · Versuch ${service.attempt || 1}/3 in dieser Runde · bisheriger MSE: ${Number(service.mse).toFixed(6)}${job?.elapsed ? ` · Konvertierungszeit: ${job.elapsed} s` : ''}${service.phase === 'convert' && job?.message ? ' · ' + job.message : ''}` : '';
  el('conversion-deferred-title').textContent = `Zurückgestellte Bilder (${(service.deferred || []).length})`;
  el('conversion-deferred').replaceChildren(...(service.deferred || []).map(name => node('li', `${name} · 3 erfolglose Versuche`)));
  el('conversion-log').textContent = service.log || job?.log || (service.phase === 'refresh' ? 'Die Qualitätsprüfung wird vorbereitet …' : 'Noch keine Konvertierung gestartet.');
  const links = [];
  if (job) {
    const a = node('a','Konvertierungsprotokoll öffnen'); a.href = `/api/jobs/${job.id}/log`; a.target = '_blank'; a.rel = 'noopener'; links.push(a);
    if (job.result) {const result = node('a','Letztes SVG öffnen'); result.href = `/api/jobs/${job.id}/result`; result.target = '_blank'; result.rel = 'noopener'; links.push(result);}
  }
  el('conversion-links').replaceChildren(...links);
  el('conversion-history').replaceChildren(...[...(service.history || [])].reverse().map(item => {
    const li = node('li', `${item.filename}: ${item.passed ? 'Rastergates erfüllt' : item.deferred ? 'zurückgestellt' : 'weiterhin offen'} · Runde ${item.round || 1}, Versuch ${item.attempt || 1}/3 · `);
    const a = node('a','Protokoll'); a.href = `/api/jobs/${item.job_id}/log`; a.target = '_blank'; a.rel = 'noopener'; li.append(a); return li;
  }));
}
async function completeServiceOverview(service, catalogJob) {
  // Static pages are updated immediately; a running Python server keeps its
  // code until restart. Existing API data can provide these previews meanwhile.
  if ('next' in service && 'inspection' in service) return service;
  const result = {...service}, history = service.history || [];
  let lastJob = service.job?.status !== 'running' ? service.job : null;
  const previous = history[history.length-1];
  if (!lastJob && previous) {
    if (legacyLastJob?.id !== previous.job_id) legacyLastJob = await api(`/api/jobs/${previous.job_id}`);
    lastJob = legacyLastJob;
  }
  if (lastJob) {
    const row = data.rows.find(r => r.filename === lastJob.name);
    const candidate = row?.candidates.find(c => [c.svg,...(c.all_paths || [])].some(p => p?.includes('/'+lastJob.id+'/')));
    const measurement = candidate?.measurement || {};
    const passed = !lastJob.result ? false : candidate ? !measurement.error && ['mupdf','librsvg'].every(name => measurement.renderers?.[name]?.satisfactory === true && !measurement.renderers[name].error) : null;
    result.last_attempt = {filename:lastJob.name,job_id:lastJob.id,result:!!lastJob.result,
      passed,checking:passed === null && service.phase === 'refresh',message:lastJob.message,
      measurement,round:previous?.job_id === lastJob.id ? previous.round : service.round || 1,
      attempt:previous?.job_id === lastJob.id ? previous.attempt : service.attempt || 1};
  }
  const counts = {...(service.failure_counts || {})};
  const conditional = service.status === 'running' && (service.phase === 'convert' || result.last_attempt?.checking);
  if (conditional && service.filename) counts[service.filename.toLowerCase()] = service.attempt || 1;
  const ranked = data.rows.filter(r => r.role === 'catalog' && r.status === 'pixel_fail' && r.description?.trim() &&
    ['mupdf','librsvg'].every(name => Number.isFinite(r.selected?.measurement?.renderers?.[name]?.metrics?.normalized_mse)));
  let candidates = ranked.filter(r => (counts[r.filename.toLowerCase()] || 0) < 3), round = service.round || 1;
  if (ranked.length && !candidates.length) {candidates = ranked; round++; for (const name of Object.keys(counts)) delete counts[name];}
  candidates.sort((a,b) => metrics(a).mse-metrics(b).mse || a.filename.toLowerCase().localeCompare(b.filename.toLowerCase()));
  const next = candidates[0];
  result.next = next ? {filename:next.filename,image:next.image,mse:metrics(next).mse,
    round,attempt:(counts[next.filename.toLowerCase()] || 0)+1,provisional:service.phase === 'refresh',conditional} : null;
  result.inspection = service.phase === 'refresh' && catalogJob ? {...catalogJob,elapsed:catalogJob.progress?.elapsed_seconds || 0} : null;
  if (result.inspection) {
    const p = result.inspection.progress || {};
    result.log = `Qualitätsprüfung: ${p.completed || 0}/${p.total || '?'} Bilder; ${p.measured || 0} neue Paarprüfungen, ${p.cached || 0} wiederverwendet.`;
  }
  return result;
}
async function poll() {
  if (polling) return; polling = true;
  try {
    const [jobResult, serviceResult] = await Promise.allSettled([api('/api/catalog'),api('/api/catalog/conversion')]);
    if (serviceResult.status === 'fulfilled') {
      showConversion(await completeServiceOverview(serviceResult.value,jobResult.status === 'fulfilled' ? jobResult.value : null));
      if (jobResult.status === 'fulfilled') el('notice').hidden = true;
    } else {
      conversionAvailable = false;
      conversionActive = false;
      el('conversion-start').disabled = true;
      el('conversion-stop').disabled = true;
      el('conversion-profile').disabled = true;
      const error = serviceResult.reason;
      const message = error.status === 404
        ? 'Der laufende Webserver kennt die Hintergrundkonvertierung noch nicht. Bitte alle alten ImageConverter-Webserver beenden, den Webserver neu starten und diese Seite neu laden.'
        : 'Der Status der Hintergrundkonvertierung konnte nicht geladen werden: ' + error.message;
      el('conversion-status').textContent = message;
      notice(new Error(message));
    }
    if (jobResult.status === 'fulfilled') {
      const job = jobResult.value;
      showJob(job);
      if (reportKey(job.summary) !== lastReport) await loadList();
    } else {
      throw jobResult.reason;
    }
  } catch (error) {notice(error);} finally {polling = false;}
}
for (const id of ['search','geometry-class','status','archive','sort','page-size']) el(id).addEventListener(id === 'search' ? 'input' : 'change', () => {page=0;render();});
el('previous').onclick = () => {page--;render();}; el('next').onclick = () => {page++;render();};
el('refresh').onclick = async () => {el('notice').hidden=true;el('refresh').disabled=true;try {showJob(await api('/api/catalog/start',{force:el('force').checked}));} catch(error) {notice(error);await poll();}};
el('stop').onclick = async () => {el('stop').disabled=true;try {showJob(await api('/api/catalog/cancel',{}));} catch(error) {notice(error);await poll();}};
el('conversion-start').onclick = async () => {el('notice').hidden=true;el('conversion-start').disabled=true;try {showConversion(await api('/api/catalog/conversion/start',{profile:el('conversion-profile').value}));} catch(error) {notice(error);} await poll();};
el('conversion-stop').onclick = async () => {el('conversion-stop').disabled=true;try {showConversion(await api('/api/catalog/conversion/stop',{}));} catch(error) {notice(error);} await poll();};
loadList().then(poll).catch(notice);
setInterval(poll,1500);
