"use strict";
let nativeFileDialogs = false, preparingPlanB = false, serverNeedsRestart = false;
const $ = (id) => document.getElementById(id);
let current = null;
let activeId = null;
let scale = 1;
let busy = false;
let history = [];
let syncingScroll = false;
let pollTimer;
let saving = false;

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error || "Die Anfrage ist fehlgeschlagen.");
    error.status = response.status;
    throw error;
  }
  return data;
}
function post(path, body) {
  return request(path, { method: "POST", headers: { "Content-Type": "application/json", "X-ImageConverter": "1" }, body: JSON.stringify(body) });
}
function notice(message = "") {
  $("notice").textContent = message;
  $("notice").hidden = !message;
}
function controls() {
  const running = busy || Boolean(activeId);
  $("convert").disabled = running || !current || !$("description").value.trim();
  for (const id of ["description", "profile", "file", "remove-sample"]) $(id).disabled = running;
  $("sample-file").disabled = running || !current;
  $("drop-zone").classList.toggle("busy", running);
  $("drop-zone").tabIndex = running ? -1 : 0;
  $("drop-zone").setAttribute("aria-disabled", String(running));
  $("cancel").hidden = !activeId;
  $("cancel").disabled = busy;
  $("convert").querySelector("span").textContent = activeId ? "Konvertierung läuft …" : current?.sample ? "Sample weiter verbessern" : "In SVG konvertieren";
  for (const id of ["zoom-in", "zoom-out", "fit"]) $(id).disabled = !current;
  for (const button of $("history").querySelectorAll("button")) button.disabled = running;
  $("pick-sample").disabled = running || !current;
  $("use-plan-b").disabled = running || preparingPlanB;
  $("collection-next").disabled = running;
}
function zoom() {
  $("zoom-label").textContent = `${Math.round(scale * 100)} %`;
  for (const prefix of ["source", "sample", "result"]) {
    const img = $(`${prefix}-image`), stage = $(`${prefix}-stage`);
    if (!current || img.hidden) continue;
    const fit = Math.min((stage.clientWidth - 40) / current.width, (stage.clientHeight - 40) / current.height);
    img.style.width = `${Math.round(current.width * fit * scale)}px`;
    img.style.height = `${Math.round(current.height * fit * scale)}px`;
  }
}
function renderJob(job, select = false) {
  if (current?.id !== job.id) { $("save-status").hidden = true; $("save-status").textContent = ""; }
  current = job;
  $("collection-context").hidden = !job.collection_case_id;
  $("collection-category").textContent = job.collection_label || '';
  $("collection-next").hidden = !job.collection_next_case_id;
  if (select) {
    $("description").value = job.description;
    $("profile").value = job.profile;
    $("description-hint").textContent = job.description_origin === "user" ? "Deine zuletzt verwendete Beschreibung dieses Bildes wurde übernommen." : job.description ? "Katalogbeschreibung geladen. Du kannst sie vor der Konvertierung anpassen." : "Beschreibe Formen, Farben und ihre Anordnung, damit der Konverter das passende Modell suchen kann.";
    scale = 1;
  }
  const sourceUrl = `/api/jobs/${job.id}/source`;
  if ($("source-image").getAttribute("src") !== sourceUrl) $("source-image").src = sourceUrl;
  $("source-image").hidden = false;
  $("source-empty").hidden = true;
  $("file-info").textContent = `${job.name} · ${job.width} × ${job.height} px`;
  $("source-meta").textContent = `${job.width} × ${job.height} px`;
  $("sample-figure").hidden = !job.sample;
  $("sample-image").hidden = !job.sample;
  $("sample-info").textContent = job.sample ? job.sample_name : "Gespeichertes SVG zusammen mit dem Original laden und weiter verbessern.";
  $("remove-sample").hidden = !job.sample;
  document.querySelector(".comparison").classList.toggle("with-sample", Boolean(job.sample));
  const sampleUrl = `/api/jobs/${job.id}/sample`;
  if (job.sample && $("sample-image").getAttribute("src") !== sampleUrl) $("sample-image").src = sampleUrl;
  $("result-image").hidden = !job.result;
  $("result-empty").hidden = job.result;
  const resultUrl = `/api/jobs/${job.id}/result`;
  if (job.result && $("result-image").getAttribute("src") !== resultUrl) $("result-image").src = resultUrl;
  $("result-empty").querySelector("strong").textContent = job.status === "running" ? (job.sample ? "Dein Sample wird verbessert …" : "Dein SVG entsteht …") : "Platz für dein SVG";
  $("result-empty").querySelector("p").textContent = job.status === "running" ? "Die Suche läuft. Du kannst den Fortschritt im Protokoll verfolgen." : "Nach der Konvertierung siehst du hier das Ergebnis.";
  $("status").textContent = job.message;
  $("status-dot").className = `status-dot ${job.status === "running" ? "running" : job.quality === "warning" ? "warning" : ["error", "timeout", "interrupted"].includes(job.status) ? "error" : ""}`;
  $("elapsed").textContent = job.elapsed ? `${Math.round(job.elapsed)} s` : "";
  $("log").textContent = job.log || "Das Protokoll erscheint nach dem Start der Konvertierung.";
  $("save-actions").hidden = !job.result;
  $("project-status").hidden = !job.project_save;
  $("project-status").textContent = job.project_save?.message || "";
  $("use-plan-b").hidden = serverNeedsRestart || !job.result || job.quality !== "passed" || job.status !== "done";
  $("download").href = `${resultUrl}?download=1`;
  $("download").download = `${job.name.replace(/\.[^.]*$/, "")}.svg`;
  $("quality").className = `hint ${job.quality === "warning" ? "quality-warning" : job.quality === "passed" ? "quality-passed" : ""}`;
  $("quality").textContent = job.quality === "warning" ? (job.sample ? "Entwurf · Pixel- oder explizite Beschreibungsprüfung noch offen" : "Entwurf · Qualitätsprüfung nicht bestanden") : job.quality === "passed" ? (job.sample ? "Pixelprüfung bestanden · Sample am Original optimiert" : "Qualitätsprüfung bestanden · Bereit zum Herunterladen") : "Original und Ergebnis lassen sich gemeinsam vergrössern.";
  $("sample-metrics").hidden = !job.sample_report;
  if (job.sample_report) {
    const report = job.sample_report;
    const percent = report.initial_mse > 0 ? Math.max(0, (1 - report.final_mse / report.initial_mse) * 100) : 0;
    $("sample-metrics").textContent = `Sample-Vergleich: ${percent.toFixed(1)} % weniger mittlerer Pixelfehler · ${report.evaluations} geprüfte Anpassungen. Vorhandene Formen werden optimiert.`;
  }
  $("result-meta").textContent = job.quality === "warning" ? "SVG · Entwurf" : "Vektorgrafik · SVG";
  controls();
  zoom();
}
const statusLabels = { ready: "Bereit", running: "Wird konvertiert …", done: "SVG erstellt", cancelled: "Abgebrochen", error: "Fehlgeschlagen", timeout: "Zeitlimit erreicht", interrupted: "Unterbrochen" };
function renderHistory() {
  $("history-count").textContent = history.length;
  $("history").replaceChildren();
  for (const job of history.slice(0, 8)) {
    const button = document.createElement("button");
    button.className = `history-item${current?.id === job.id ? " active" : ""}`;
    const img = document.createElement("img");
    img.src = `/api/jobs/${job.id}/source`; img.alt = "";
    const text = document.createElement("span"), name = document.createElement("strong"), status = document.createElement("small");
    name.textContent = job.name;
    status.textContent = job.quality === "warning" ? "SVG-Entwurf · Bitte prüfen" : statusLabels[job.status] || job.status;
    text.append(name, status); button.append(img, text); button.title = job.name;
    button.addEventListener("click", async () => {
      try { notice(); renderJob(await request(`/api/jobs/${job.id}`), true); renderHistory(); } catch (error) { notice(error.message); }
    });
    $("history").append(button);
  }
  controls();
}
async function refreshHistory() {
  history = (await request("/api/jobs?scope=foreground")).filter(job => !job.catalog_background);
  renderHistory();
}
async function update(operation, select = false, input = null) {
  if (busy) return;
  busy = true; controls(); notice();
  try {
    const job = await operation();
    if (!job) return;
    activeId = job.status === "running" ? job.id : null;
    clearTimeout(pollTimer);
    renderJob(job, select);
    await refreshHistory();
    if (activeId) schedulePoll();
  } catch (error) { notice(error.message); }
  finally { busy = false; if (input) $(input).value = ""; controls(); }
}
function sendFile(path, file) {
  return request(`${path}?name=${encodeURIComponent(file.name)}`, { method: "POST", headers: { "X-ImageConverter": "1" }, body: file });
}
function upload(file) {
  if (!file || activeId || busy) return;
  if (file.size > 25 * 1024 * 1024) return notice("Bitte ein Bild mit maximal 25 MB auswählen.");
  return update(() => sendFile("/api/upload", file), true, "file");
}
$("file").addEventListener("change", (event) => upload(event.target.files[0]));
function changeSample(file) {
  if (!current || busy || activeId) return;
  if (file && file.size > 2 * 1024 * 1024) return notice("Die Sample-Datei darf maximal 2 MB gross sein.");
  return update(() => file ? sendFile(`/api/jobs/${current.id}/sample`, file) : post(`/api/jobs/${current.id}/sample/remove`, {}), false, "sample-file");
}
$("sample-file").addEventListener("change", (event) => changeSample(event.target.files[0]));
for (const [input, kind] of [["file", "image"], ["sample-file", "sample"]]) {
  $(input).addEventListener("click", event => {
    if (!nativeFileDialogs) return;
    event.preventDefault();
    if (busy || activeId || (kind === "sample" && !current)) return;
    update(async () => {
      const result = await post("/api/pick", {kind, job_id: current?.id});
      return result.selected ? result.job : null;
    }, kind === "image", input);
  });
}
$("pick-sample").addEventListener("click", () => $("sample-file").click());
$("remove-sample").addEventListener("click", () => changeSample(null));
$("description").addEventListener("input", controls);
$("drop-zone").addEventListener("keydown", (event) => {
  if (["Enter", " "].includes(event.key) && !busy && !activeId) { event.preventDefault(); $("file").click(); }
});
for (const name of ["dragenter", "dragover", "dragleave", "drop"]) {
  $("drop-zone").addEventListener(name, (event) => {
    event.preventDefault();
    $("drop-zone").classList.toggle("dragging", name === "dragenter" || name === "dragover");
    if (name === "drop") upload(event.dataTransfer.files[0]);
  });
}
// Prevent the browser from navigating away if a file is dropped outside the target.
window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("drop", (event) => event.preventDefault());
$("convert").addEventListener("click", () => {
  if (!current || busy || activeId) return;
  return update(() => post(`/api/jobs/${current.id}/start`, { description: $("description").value, profile: $("profile").value }));
});
$("cancel").addEventListener("click", () => {
  if (!activeId || busy) return;
  return update(() => post(`/api/jobs/${activeId}/cancel`, {}));
});
$("save-as").addEventListener("click", async () => {
  if (!current?.result || saving) return;
  const jobId = current.id;
  saving = true;
  $("save-as").disabled = true;
  $("save-as").textContent = "Speicherort wählen …";
  notice();
  try {
    const result = await post(`/api/jobs/${jobId}/save`, {});
    if (current?.id === jobId) {
      $("save-status").textContent = result.saved ? `Gespeichert: ${result.path}` : "Speichern abgebrochen.";
      $("save-status").hidden = false;
    }
  } catch (error) { notice(error.message); }
  finally {
    saving = false;
    $("save-as").disabled = false;
    $("save-as").textContent = "Speichern unter … ↓";
  }
});
function schedulePoll() { clearTimeout(pollTimer); pollTimer = setTimeout(poll, 1000); }
$("use-plan-b").addEventListener("click", async () => {
  if (!current || busy || activeId || preparingPlanB) return;
  preparingPlanB = true; controls(); notice();
  $("use-plan-b").textContent = "Plan-B-Varianten werden vorbereitet …";
  try {
    const report = await post(`/api/jobs/${current.id}/workbench`, {});
    window.location.assign(`/workbench?run=${encodeURIComponent(report.id)}`);
  } catch (error) { notice(error.message); }
  finally {
    preparingPlanB = false; controls();
    $("use-plan-b").textContent = "Als erweiterte Plan-B-Aufgabe verwenden →";
  }
});
async function poll() {
  const id = activeId;
  if (!id) return;
  try {
    const job = await request(`/api/jobs/${id}`);
    if (activeId !== id) return;
    notice();
    if (job.status !== "running") activeId = null;
    renderJob(job);
    if (activeId) schedulePoll();
    else await refreshHistory();
  } catch (error) {
    notice(`Verbindung zum lokalen Server unterbrochen. Erneuter Versuch … ${error.message}`);
    if (activeId === id) schedulePoll();
  }
}
$("zoom-in").addEventListener("click", () => { scale = Math.min(8, scale * 1.25); zoom(); });
$("zoom-out").addEventListener("click", () => { scale = Math.max(0.25, scale / 1.25); zoom(); });
$("fit").addEventListener("click", () => {
  scale = 1; zoom();
  for (const id of ["source-stage", "sample-stage", "result-stage"]) { $(id).scrollTop = 0; $(id).scrollLeft = 0; }
});
window.addEventListener("resize", zoom);
for (const prefix of ["source", "sample", "result"]) {
  $(`${prefix}-image`).addEventListener("load", zoom);
  $(`${prefix}-image`).addEventListener("error", () => notice("Die Bildvorschau konnte nicht geladen werden. Bitte den lokalen Server prüfen."));
  $(`${prefix}-stage`).addEventListener("scroll", () => {
    if (syncingScroll) return;
    syncingScroll = true;
    const from = $(`${prefix}-stage`);
    for (const other of ["source", "sample", "result"]) {
      if (other === prefix) continue;
      const to = $(`${other}-stage`);
      to.scrollLeft = from.scrollLeft; to.scrollTop = from.scrollTop;
    }
    requestAnimationFrame(() => { syncingScroll = false; });
  });
}
async function init() {
  try {
    try {
      const config = await request("/api/config");
      nativeFileDialogs = config.native_file_dialogs;
      if (!config.parallel_background_conversion) {
        serverNeedsRestart = true;
        $("server-version-warning").textContent = "Der laufende Webserver verwendet noch eine ältere Version, die manuelle Konvertierungen während des Hintergrunddienstes blockieren kann. Bitte stopWebServer.cmd und danach startWebServer.cmd ausführen und diese Seite neu laden. Anschliessend den Hintergrunddienst bei Bedarf wieder starten.";
        $("server-version-warning").hidden = false;
      }
    } catch (error) {
      if (error.status !== 404) throw error;
      serverNeedsRestart = true;
      $("server-version-warning").textContent = "Der Webserver läuft noch mit einer älteren Version. Lass laufende Konvertierungen fertig werden und starte ihn danach über startWebServer.cmd neu. Lade anschliessend diese Seite neu, um die neuen Funktionen zu verwenden.";
      $("server-version-warning").hidden = false;
    }
    $("sample-file").hidden = nativeFileDialogs;
    $("pick-sample").hidden = !nativeFileDialogs;
    await refreshHistory();
    const running = history.find((job) => job.status === "running");
    const requestedId = new URLSearchParams(window.location.search).get('job');
    const selected = requestedId ? await request(`/api/jobs/${encodeURIComponent(requestedId)}`) : running || history[0];
    if (selected?.status === 'running') activeId = selected.id;
    if (selected) renderJob(selected, true);
    renderHistory();
    if (activeId) schedulePoll();
  } catch (error) { notice(`Die Oberfläche konnte nicht geladen werden. ${error.message}`); }
}
$("collection-next").addEventListener('click', async () => {
  if (!current?.collection_next_case_id || busy || activeId) return;
  busy = true; controls(); notice();
  try {
    const next = await post(`/api/collection/${current.collection_next_case_id}/load`, {});
    window.location.assign(`/?job=${encodeURIComponent(next.id)}`);
  } catch (error) {notice(error.message);} finally {busy=false;controls();}
});
init();
