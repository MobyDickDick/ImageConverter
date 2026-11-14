"use strict";
const $ = id => document.getElementById(id);
const jobId = new URLSearchParams(window.location.search).get('job');
let cursor = 0, total = 0, queue = [], paused = false, loading = false;
let job = null, timer, generation = 0, showing = false;

async function request(path) {
  const response = await fetch(path);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Der lokale Server ist nicht erreichbar.');
  return data;
}
function status() {
  $('counter').textContent = `Versuch ${cursor} von ${total}`;
  if (paused) $('status').textContent = 'Anzeige angehalten. Die Konvertierung läuft unabhängig weiter.';
  else if (cursor < total) $('status').textContent = `Versuche laufen durch · ${total - cursor} weitere vorhanden.`;
  else $('status').textContent = job?.status === 'running' || job?.status === 'ready'
    ? 'Live · Warte auf den nächsten Versuch …'
    : 'Alle vorhandenen Versuche angezeigt. Das Ergebnis findest du im Hauptfenster.';
}
async function refresh() {
  if (loading) return;
  loading = true;
  const version = generation;
  try {
    const snapshot = await request(`/api/jobs/${jobId}`);
    if (version !== generation) return;
    job = snapshot;
    total = job.attempt_count || 0;
    $('name').textContent = job.name;
    if (!queue.length && !showing && cursor < total) {
      const page = await request(`/api/jobs/${jobId}/attempts?after=${cursor}`);
      if (version !== generation) return;
      queue = page.attempts;
      total = page.total;
    }
    status();
  } catch (error) { $('status').textContent = `${error.message} Verbindung wird erneut versucht …`; }
  finally { loading = false; }
}
function play() {
  clearTimeout(timer);
  if (!paused && !showing && queue.length) {
    const record = queue.shift(), version = generation;
    showing = true;
    const image = $('attempt');
    image.onload = () => {
      if (version !== generation) return;
      cursor = record.number;
      image.hidden = false;
      $('empty').hidden = true;
      $('phase').textContent = record.phase;
      $('error').textContent = `Mittlerer Pixelfehler: ${record.mse.toFixed(6)}`;
      status();
      showing = false;
      if (!queue.length) refresh();
      timer = setTimeout(play, Number($('speed').value));
    };
    image.onerror = () => {
      if (version !== generation) return;
      // Retry this attempt instead of silently skipping a failed image load.
      queue.unshift(record);
      showing = false;
      $('status').textContent = 'Versuch konnte nicht geladen werden. Erneuter Versuch …';
      timer = setTimeout(play, 1000);
    };
    image.src = `/api/jobs/${jobId}/attempts?number=${record.number}`;
    return;
  }
  timer = setTimeout(play, 100);
}
$('pause').addEventListener('click', () => {
  paused = !paused;
  $('pause').textContent = paused ? 'Weiterlaufen lassen' : 'Anhalten';
  status();
});
$('latest').addEventListener('click', async () => {
  generation++;
  queue = [];
  showing = false;
  cursor = Math.max(0, total - 1);
  paused = false;
  $('pause').textContent = 'Anhalten';
  await refresh();
  play();
});
async function poll() {
  await refresh();
  setTimeout(poll, 500);
}
if (/^[0-9a-f]{32}$/.test(jobId || '')) { poll(); play(); }
else $('status').textContent = 'Kein gültiger Konvertierungsauftrag ausgewählt.';
