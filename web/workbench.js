"use strict";
const $ = id => document.getElementById(id);
let current = null, activeCase = null, selected = new Set(), busy = false, timer = null;
let logUrl = null;
let loadedSource = null, previewUrl = null;
const labels = {prepared: "Vorbereitet", running: "Läuft", completed: "Abgeschlossen", cancelled: "Abgebrochen", interrupted: "Unterbrochen", error: "Ausführungsfehler"};
async function request(path, body) {
  const response = await fetch(path, body === undefined ? {} : {method: "POST", headers: {"Content-Type": "application/json", "X-ImageConverter": "1"}, body: JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Anfrage fehlgeschlagen.");
  return data;
}
function notice(text = "") { $("notice").textContent = text; $("notice").hidden = !text; }
function asset(path, download = false) { return `/api/workbench/${current.id}/asset?path=${encodeURIComponent(path)}${download ? "&download=1" : ""}`; }
function controls() {
  const running = current?.status === "running";
  const unpreparedSource = loadedSource && loadedSource.preparedId !== current?.id;
  for (const id of ["file", "description", "seed", "iterations", "timeout"]) $(id).disabled = busy || running;
  $("prepare").disabled = busy || running || !loadedSource || !$("description").value.trim();
  $("run-selected").disabled = busy || running || unpreparedSource || !current || !selected.size;
  $("run-all").disabled = busy || running || unpreparedSource || !current;
  $("select-all").disabled = busy || running || !current;
  $("cancel").hidden = !running; $("cancel").disabled = busy;
  $("save-note").disabled = busy || running; $("note").disabled = busy || running;
  for (const checkbox of $("cases").querySelectorAll("input")) checkbox.disabled = busy || running;
  for (const button of $("history").querySelectorAll("button")) button.disabled = busy || running;
  $("bundle").hidden = running;
}
function textCell(row, text) { const cell = row.insertCell(); cell.textContent = text; return cell; }
function thumbnail(caseId, path, label) {
  const button = document.createElement("button"); button.className = "case-thumbnail";
  button.type = "button"; button.title = `${label} · ${caseId} vergleichen`;
  button.setAttribute("aria-label", button.title);
  const img = document.createElement("img"); img.src = asset(path); img.alt = "";
  img.loading = "lazy"; img.decoding = "async"; img.width = 48; img.height = 48;
  const caption = document.createElement("span"); caption.textContent = label;
  button.append(img, caption);
  button.addEventListener("click", () => { showCase(caseId); $("detail").scrollIntoView({block: "start"}); });
  return button;
}
function sourcePreview(url, info) {
  if (previewUrl) { URL.revokeObjectURL(previewUrl); previewUrl = null; }
  if (url.startsWith("blob:")) previewUrl = url;
  $("source-preview").hidden = false;
  $("source-info").textContent = info;
  $("source-loading").hidden = false;
  $("source-loading").textContent = "SVG wird geladen …";
  $("source-image").hidden = false;
  $("source-image").src = url;
}
function restoreSource(report) {
  loadedSource = null; $("file").value = "";
  $("description").value = report.source_description;
  $("seed").value = report.seed;
  $("description-source").textContent = "Beschreibung aus dieser gespeicherten Aufgabe geladen. Für eine neue Aufgabe ein SVG auswählen.";
  const original = report.cases[0];
  sourcePreview(`/api/workbench/${report.id}/asset?path=source.svg`, `${report.name} · ${original.width} × ${original.height} px`);
}
async function loadSource() {
  const file = $("file").files[0];
  loadedSource = null;
  $("description").value = "";
  $("source-image").hidden = true;
  if (previewUrl) { URL.revokeObjectURL(previewUrl); previewUrl = null; }
  $("source-image").removeAttribute("src");
  $("source-preview").hidden = !file;
  if (!file) { $("description-source").textContent = "Bitte ein SVG auswählen."; return; }
  $("source-info").textContent = file.name;
  $("source-loading").hidden = false; $("source-loading").textContent = "SVG wird geprüft …";
  $("description-source").textContent = "Beschreibung wird in den vorhandenen Dateien gesucht …";
  try {
    if (file.size > 2 * 1024 * 1024) throw new Error("Bitte ein SVG mit maximal 2 MB wählen.");
    const text = await file.text();
    const result = await request("/api/workbench/inspect", {svg: text, name: file.name});
    loadedSource = {file, text};
    $("description").value = result.description;
    $("description-source").textContent = result.description
      ? `Beschreibung aus ${result.description_source} (Schlüssel ${result.description_key}) geladen. Du kannst sie bearbeiten.`
      : `Keine passende Beschreibung gefunden. Gesucht in: ${result.description_searched.join("; ")}. Bitte eine Beschreibung eingeben.`;
    if (result.description_warnings.length) $("description-source").textContent += ` Hinweise: ${result.description_warnings.join("; ")}`;
    sourcePreview(URL.createObjectURL(new Blob([result.preview_svg], {type: "image/svg+xml"})), `${file.name} · ${result.width} × ${result.height} px`);
  } catch (error) {
    $("source-loading").textContent = "Die SVG-Vorschau konnte nicht geladen werden.";
    $("description-source").textContent = "Keine Beschreibung geladen.";
    throw error;
  }
}
function setImage(id, path) {
  const img = $(id); img.hidden = !path;
  if (path && img.getAttribute("src") !== asset(path)) img.src = asset(path);
  if (!path) img.removeAttribute("src");
}
function showCase(caseId, resetNote = false) {
  const changed = activeCase !== caseId;
  activeCase = caseId;
  const c = current.cases.find(c => c.case_id === caseId), r = c.result;
  $("detail").hidden = false; $("case-title").textContent = `Fallvergleich · ${caseId}`;
  $("case-description").textContent = c.description;
  setImage("target", `${caseId}/target.png`);
  setImage("output", r?.output_svg ? `${r.artifact_root}/${r.output_svg}` : null);
  setImage("difference", r?.output_svg ? `${r.artifact_root}/${caseId}/difference.png` : null);
  $("output-empty").hidden = Boolean(r?.output_svg);
  $("output-download").hidden = !r?.output_svg;
  if (r?.output_svg) $("output-download").href = asset(`${r.artifact_root}/${r.output_svg}`, true);
  $("metrics").textContent = r?.metrics ? Object.entries(r.metrics).map(([k, v]) => `${k}: ${v.toFixed(6)}`).join(" · ") + ` · ${r.elapsed_seconds} s` : "Noch keine Messwerte vorhanden.";
  const attempt = r && current.attempts.find(a => r.artifact_root.endsWith(`/${a.id}`));
  if (attempt) $("metrics").textContent += ` · ${attempt.id} · ${attempt.iterations} Iterationen · Limit ${attempt.timeout_seconds} s`;
  $("failures").textContent = r ? (r.satisfactory ? "Feste Qualitätsgrenzen bestanden. Sichtprüfung ergänzen." : `Befund: ${r.failures.join(", ")}${r.error ? " · " + r.error : ""}`) : "";
  if (changed || resetNote) { $("note").value = current.notes[caseId] || ""; $("note-status").textContent = ""; }
  const runningAttempt = current.status === "running" && current.active_case === caseId ? current.attempts.at(-1) : null;
  const nextLog = runningAttempt ? asset(`attempts/${runningAttempt.id}/${caseId}/converter.log`) : r ? asset(`${r.artifact_root}/${caseId}/converter.log`) : null;
  if (logUrl !== nextLog || runningAttempt) {
    logUrl = nextLog;
    $("log").textContent = "Noch kein Suchprotokoll.";
    if (nextLog) fetch(nextLog).then(response => response.ok ? response.text() : "Protokoll nicht verfügbar.").then(text => { if (logUrl === nextLog) $("log").textContent = text; }).catch(() => { if (logUrl === nextLog) $("log").textContent = "Protokoll nicht erreichbar."; });
  }
  for (const row of $("cases").rows) row.classList.toggle("selected-row", row.dataset.caseId === caseId);
}
function render(report, reset = false) {
  current = report;
  if (reset) { selected = new Set(report.cases.map(c => c.case_id)); activeCase = null; logUrl = null; }
  const s = report.summary;
  $("run-info").textContent = `${report.name} · Seed ${report.seed}`;
  $("summary").textContent = `${labels[report.status] || report.status}${report.active_case ? " · " + report.active_case : ""} · ${s.completed}/${s.total} geprüft · ${s.passed} bestanden · ${s.quality_failed} Qualitätsfehler · ${s.execution_failed} Ausführungsfehler · ${report.attempts.length} Versuche`;
  $("cases").replaceChildren();
  for (const c of report.cases) {
    const row = document.createElement("tr"); row.dataset.caseId = c.case_id;
    const checkbox = document.createElement("input"); checkbox.type = "checkbox"; checkbox.checked = selected.has(c.case_id); checkbox.setAttribute("aria-label", `${c.case_id} auswählen`);
    checkbox.addEventListener("change", () => { checkbox.checked ? selected.add(c.case_id) : selected.delete(c.case_id); $("select-all").checked = selected.size === current.cases.length; controls(); });
    row.insertCell().append(checkbox);
    const button = document.createElement("button"); button.className = "text-button"; button.textContent = c.case_id; button.addEventListener("click", () => showCase(c.case_id));
    row.insertCell().append(button);
    textCell(row, `${(c.variation.scale * 100).toFixed(2)} %`);
    textCell(row, `${(c.variation.relative_x * 100).toFixed(2)} / ${(c.variation.relative_y * 100).toFixed(2)} %`);
    const r = c.result;
    textCell(row, report.active_case === c.case_id ? "Läuft …" : !r ? "Offen" : r.satisfactory ? "Bestanden" : r.metrics ? "Qualitätsfehler" : "Ausführungsfehler");
    textCell(row, r?.metrics?.normalized_mse?.toFixed(6) ?? "—");
    const previews = document.createElement("div"); previews.className = "case-thumbnails";
    previews.append(thumbnail(c.case_id, `${c.case_id}/target.png`, "Eingabe"));
    if (r?.output_svg) previews.append(thumbnail(c.case_id, `${r.artifact_root}/${r.output_svg}`, "Ergebnis"));
    row.insertCell().append(previews);
    $("cases").append(row);
  }
  $("select-all").checked = selected.size === current.cases.length;
  $("exports").hidden = false;
  for (const name of ["report", "csv", "bundle"]) $(name).href = `/api/workbench/${report.id}/${name}`;
  showCase(activeCase || report.cases[0].case_id, reset); controls();
}
function schedule() {
  clearTimeout(timer);
  if (current?.status === "running") timer = setTimeout(async () => {
    try { render(await request(`/api/workbench/${current.id}`)); if (current.status !== "running") await history(); }
    catch (error) { notice(error.message); }
    schedule();
  }, 1200);
}
async function history() {
  const runs = await request("/api/workbench"); $("history").replaceChildren();
  for (const r of runs) {
    const button = document.createElement("button"); button.className = "history-item";
    const name = document.createElement("span"), status = document.createElement("small"); name.textContent = r.name; status.textContent = `${r.summary.passed}/${r.summary.total} · ${labels[r.status] || r.status}`;
    button.append(name, status); button.addEventListener("click", () => operation(async () => { const report = await request(`/api/workbench/${r.id}`); restoreSource(report); render(report, true); schedule(); })); $("history").append(button);
  }
  if (!runs.length) $("history").textContent = "Noch keine Aufgaben vorbereitet.";
  controls(); return runs;
}
async function operation(callback) {
  if (busy) return; busy = true; notice(); controls();
  try { await callback(); } catch (error) { notice(error.message); }
  finally { busy = false; controls(); }
}
$("description").addEventListener("input", controls);
$("file").addEventListener("change", () => operation(loadSource));
$("source-image").addEventListener("load", () => { $("source-loading").hidden = true; });
$("source-image").addEventListener("error", () => { $("source-image").hidden = true; $("source-loading").hidden = false; $("source-loading").textContent = "Die SVG-Vorschau konnte nicht angezeigt werden."; });
$("prepare").addEventListener("click", () => operation(async () => {
  const source = loadedSource; if (!source) throw new Error("Bitte zuerst ein SVG auswählen.");
  const seedText = $("seed").value.trim();
  // JSON numbers lose precision for large replay seeds. Send their exact decimal string.
  if (seedText && !/^\d+$/.test(seedText)) throw new Error("Bitte einen nichtnegativen ganzzahligen Seed eingeben.");
  const report = await request("/api/workbench/prepare", {svg: source.text, name: source.file.name, description: $("description").value, seed: seedText || null});
  source.preparedId = report.id;
  render(report, true);
  await history();
}));
$("select-all").addEventListener("change", () => { selected = new Set($("select-all").checked ? current.cases.map(c => c.case_id) : []); render(current); });
async function run(all) {
  const iterations = Number($("iterations").value), timeout = Number($("timeout").value);
  if (!Number.isInteger(iterations) || iterations < 1 || iterations > 4096 || timeout < 1 || timeout > 600) throw new Error("Bitte gültige Iterationen (1–4096) und ein Zeitlimit (1–600 Sekunden) eingeben.");
  render(await request(`/api/workbench/${current.id}/start`, {cases: all ? current.cases.map(c => c.case_id) : [...selected], iterations, timeout})); schedule();
}
$("run-selected").addEventListener("click", () => operation(() => run(false)));
$("run-all").addEventListener("click", () => operation(() => run(true)));
$("cancel").addEventListener("click", () => operation(async () => { render(await request(`/api/workbench/${current.id}/cancel`)); await history(); }));
$("save-note").addEventListener("click", () => operation(async () => { render(await request(`/api/workbench/${current.id}/note`, {case_id: activeCase, note: $("note").value})); $("note-status").textContent = "Gespeichert."; }));
history().then(async runs => { if (runs.length && !loadedSource && !busy) { const report = await request(`/api/workbench/${runs[0].id}`); if (!loadedSource && !busy) { restoreSource(report); render(report, true); schedule(); } } }).catch(error => notice(error.message));
