"use strict";
let nativeFileDialogs = false, preparingPlanB = false, serverNeedsRestart = false;
let editableSearchSeed = false;
let currentSvgReuse = false;
let imageRecognition = false;
let descriptionCheck = false;
let descriptionAutosave = false, descriptionDirty = false, descriptionSaveTimer, descriptionSaving = null;
const $ = (id) => document.getElementById(id);
let current = null;
let activeId = null;
let scale = 1;
let busy = false;
let history = [];
let syncingScroll = false;
let pollTimer;
let saving = false;
let attemptWindow = null;
function openAttemptWindow() {
  if (!current) return;
  attemptWindow = window.open(`/attempts?job=${current.id}`, 'imageconverter-attempts',
    'popup=yes,width=840,height=760,resizable=yes,scrollbars=yes');
  $("attempt-window-hint").hidden = Boolean(attemptWindow);
}
$("open-attempts").addEventListener("click", openAttemptWindow);
// A display preference applies to every image and can change during a run.
try { $("show-intermediate").checked = localStorage.getItem("imageconverter.showIntermediate") !== "false"; }
catch (_) { $("show-intermediate").checked = true; }
$("show-intermediate").addEventListener("change", () => {
  try { localStorage.setItem("imageconverter.showIntermediate", String($("show-intermediate").checked)); } catch (_) {}
  if ($("show-intermediate").checked && current?.status === 'running') openAttemptWindow();
  if (!$("show-intermediate").checked && attemptWindow && !attemptWindow.closed) attemptWindow.close();
  if (!$("show-intermediate").checked) $("attempt-window-hint").hidden = true;
  if (current) renderJob(current);
});
try { $("use-current-svg").checked = localStorage.getItem("imageconverter.useCurrentSvg") !== "false"; }
catch (_) { $("use-current-svg").checked = true; }
$("use-current-svg").addEventListener("change", () => {
  try { localStorage.setItem("imageconverter.useCurrentSvg",String($("use-current-svg").checked)); } catch (_) {}
});

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
  $("convert").disabled = running || !current || !$("description").value.trim() || !editableSearchSeed || !currentSvgReuse;
  $("recognize").disabled = running || !current || !imageRecognition;
  $("check-description").disabled = running || !current || !descriptionCheck || !$("description").value.trim() || Boolean(descriptionSaving);
  $("save-description").disabled = running || !current || !descriptionAutosave || !descriptionDirty || Boolean(descriptionSaving);
  for (const button of $("recognition-results").querySelectorAll("button")) button.disabled = running;
  for (const id of ["seed", "random-seed"]) $(id).disabled = running || !current || !editableSearchSeed;
  for (const id of ["description", "profile", "file", "remove-sample", "use-current-svg"]) $(id).disabled = running;
  $("use-current-svg").disabled = running || !currentSvgReuse;
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
function draftQuality(job) {
  if (job.status !== "done" || !job.result || job.quality !== "warning") return null;
  const pixels = job.pixel_quality?.passed;
  // Sample workers store their description verdict in the report; older jobs
  // must be explainable on reload without changing their saved acceptance.
  const error = job.description_error || job.sample_report?.description_error || job.recovery_report?.description_error || "";
  const imageSummary = pixels === true ? "Bildqualität bestanden" : pixels === false ? "Bildqualität nicht bestanden" : "Bildprüfung noch offen";
  const parts = [pixels === true ? "Das SVG besteht den Bildvergleich mit dem Original." : pixels === false ? "Das SVG weicht im Bildvergleich noch zu stark vom Original ab." : "Für das SVG liegt keine abgeschlossene Bildprüfung vor."];
  if (error) {
    const direction = /^wrong_described_arrow_direction:(left|right)$/.exec(error);
    const spray = /^missing_described_dashed_spray_rays: expected=(\d+), observed=(\d+)$/.exec(error);
    if (spray) {
      parts.push(`Die Beschreibung fordert ${spray[1]} gestrichelte Linien; im Ergebnis sind ${spray[2]} bestätigt.`);
      parts.push("Die Konvertierung hat diese Vorgabe noch nicht vollständig umgesetzt.");
    } else if (direction) {
      const side = direction[1] === "left" ? "links" : "rechts";
      parts.push(`Die Pfeilrichtung ${side} im Ergebnis stimmt nicht mit der Beschreibung überein.`);
    } else if (error === "invalid_described_arrow_head") {
      parts.push("Eine beschriebene Pfeilspitze fehlt oder hat nicht die geforderte Dreiecksform.");
    } else if (error === "missing_described_horizontal_bar") {
      parts.push("Die beschriebene horizontale Querlinie konnte nicht bestätigt werden.");
    } else {
      parts.push("Das Ergebnis erfüllt die beschriebenen Formen, Farben oder ihre Anordnung noch nicht vollständig.");
    }
    if (!spray) parts.push("Vergleiche die Beschreibung mit dem Original. Falls das Original massgeblich ist, passe die Beschreibung an und starte die Konvertierung erneut.");
  } else if (pixels === true) {
    parts.push("Die vollständige Modell- und Beschreibungsprüfung ist noch offen. Bitte prüfe den Entwurf vor der Verwendung.");
  } else {
    parts.push("Bitte vergleiche Original und Entwurf und prüfe die Beschreibung oder lade ein passendes Sample-SVG.");
  }
  if ((job.recovery_report || job.sample_report)?.stop_reason === "time_limit") {
    parts.push("Das Suchbudget ist ausgeschöpft; dies ist kein zusätzlicher Qualitätsmangel.");
  }
  return {
    summary: `${imageSummary} · ${error ? "Beschreibung nicht erfüllt" : "Gesamtprüfung noch offen"}`,
    message: parts.join(" "),
    history: pixels === true ? `Bildqualität bestanden · ${error ? "Beschreibung prüfen" : "Gesamtprüfung offen"}` : `Entwurf · ${imageSummary}`,
  };
}
function renderDescriptionCheck(job) {
  const container = $("description-check"), report = job?.description_check;
  container.replaceChildren();
  if (!descriptionCheck) {
    container.hidden = false;
    container.textContent = 'Für die Prüfung der Bildbeschreibungen bitte laufende Konvertierungen abschliessen, den Webserver neu starten und die Seite neu laden.';
    return;
  }
  container.hidden = !report;
  if (container.hidden) return;
  container.className = 'description-check';
  if (report.description !== $("description").value) {
    container.textContent = 'Beschreibung geändert. Für diesen Text liegt noch keine aktuelle Prüfung vor.';
    return;
  }
  container.classList.toggle('quality-warning', report.status === 'mismatch');
  const message = document.createElement('strong'); message.textContent = report.message;
  container.append(message);
  for (const check of report.checks || []) {
    const line = document.createElement('p'); line.className = 'hint';
    line.textContent = `${check.status === 'mismatch' ? 'Abweichung' : 'Übereinstimmung'} · ${check.message}`;
    container.append(line);
  }
  if (report.observations) {
    const observed = document.createElement('p'); observed.className = 'hint';
    observed.textContent = `Aus dem Bild erkannt: ${report.observations.description}`;
    container.append(observed);
  }
  const limits = document.createElement('p'); limits.className = 'hint'; limits.textContent = report.limitations;
  container.append(limits);
}
function renderRecognition(job) {
  const recognition = job.recognition;
  $("recognition-status").hidden = !recognition;
  $("recognition-details").hidden = !recognition;
  $("recognition-results").replaceChildren();
  if (!recognition) return;
  $("recognition-status").textContent = `${recognition.message} Vergleichsbasis: ${recognition.reference_count} geprüfte Bildpaare.`;
  function proposal(description, label, match = null) {
    const item = document.createElement('div'); item.className = 'recognition-match';
    const title = document.createElement('strong'); title.textContent = label; item.append(title);
    if (match) {
      const previews = document.createElement('div'); previews.className = 'recognition-previews';
      for (const [url, label] of [[match.source_url, 'Original'], [match.svg_url, 'Geprüftes SVG']]) {
        const figure = document.createElement('figure'), img = document.createElement('img'), caption = document.createElement('figcaption');
        img.src = url; img.alt = `${label}: ${match.filename}`; caption.textContent = label;
        figure.append(img, caption); previews.append(figure);
      }
      item.append(previews);
    }
    const text = document.createElement('p'); text.className = 'hint'; text.textContent = description;
    const button = document.createElement('button'); button.className = 'secondary'; button.type = 'button';
    button.textContent = 'Beschreibung übernehmen';
    button.addEventListener('click', () => {
      if (busy || activeId) return;
      $("description").value = description;
      $("description-hint").textContent = 'Erkennungsvorschlag übernommen. Bitte Unterschiede zum Original ergänzen.';
      descriptionEdited();
    });
    item.append(text, button); $("recognition-results").append(item);
  }
  if (recognition.automatic) proposal(recognition.automatic.description,
    recognition.automatic.kind === 'exact_reference' ? 'Bekannter Bildinhalt' : 'Erkannte Grundform');
  for (const match of recognition.matches) proposal(match.description,
    `${match.filename} · ${match.exact ? 'identische Bildpunkte' : 'ähnliches Bild'}`, match);
}
function renderJob(job, select = false) {
  // Selection, reload and polling must all restore the same active job.
  // Cancellation must not depend on having started it in this page instance.
  if (job.status === "running") {
    activeId = job.id;
    schedulePoll();
  } else if (activeId === job.id) {
    activeId = null;
    clearTimeout(pollTimer);
  }
  if (select || current?.id !== job.id) {
    $("seed").value = job.search_seed ?? randomSeed();
    validateSeed();
    if (job.status === 'running' && typeof job.use_current_svg === 'boolean') $("use-current-svg").checked = job.use_current_svg;
  }
  if (current?.id !== job.id && attemptWindow && !attemptWindow.closed) {
    attemptWindow.location.replace(`/attempts?job=${job.id}`);
  }
  if (current?.id !== job.id) { $("save-status").hidden = true; $("save-status").textContent = ""; }
  current = job;
  $("collection-context").hidden = !job.collection_case_id;
  $("collection-category").textContent = job.collection_label || '';
  $("collection-next").hidden = !job.collection_next_case_id;
  if (select) {
    descriptionDirty = false;
    clearTimeout(descriptionSaveTimer);
    $("description").value = job.description;
    $("description-save-status").textContent = job.description_save?.message || (descriptionAutosave ? 'Änderungen werden automatisch gespeichert.' : 'Zum Speichern von Textkorrekturen bitte den Webserver neu starten.');
    $("profile").value = job.profile;
    $("description-hint").textContent = job.description_origin === "user" ? "Deine zuletzt verwendete Beschreibung dieses Bildes wurde übernommen." : job.description_origin === "recognition" ? "Beschreibung aus der lokalen Bilderkennung ergänzt. Bitte prüfen und bei Bedarf anpassen." : job.description ? "Katalogbeschreibung geladen. Du kannst sie vor der Konvertierung anpassen." : "Bild erkennen lassen oder Formen, Farben und ihre Anordnung beschreiben.";
    scale = 1;
  }
  renderRecognition(job);
  renderDescriptionCheck(job);
  const sourceUrl = `/api/jobs/${job.id}/source`;
  if ($("source-image").getAttribute("src") !== sourceUrl) $("source-image").src = sourceUrl;
  $("source-image").hidden = false;
  $("source-empty").hidden = true;
  $("file-info").textContent = `${job.name} · ${job.width} × ${job.height} px`;
  $("source-meta").textContent = `${job.width} × ${job.height} px`;
  const usingSample = job.sample && job.use_current_svg !== false;
  $("sample-figure").hidden = !usingSample;
  $("sample-image").hidden = !usingSample;
  $("sample-info").textContent = job.sample ? `${job.sample_origin ? job.sample_origin + ': ' : ''}${job.sample_name}${job.use_current_svg === false ? ' · für diesen Versuch deaktiviert' : ' · Drehung und Spiegelung werden automatisch geprüft'}` : "Ein vorhandenes SVG wird beim Start automatisch geladen. Eigene Vorlagen dürfen auch gedreht oder gespiegelt sein.";
  $("remove-sample").hidden = !job.sample;
  document.querySelector(".comparison").classList.toggle("with-sample", Boolean(usingSample));
  const sampleUrl = `/api/jobs/${job.id}/sample`;
  if (job.sample && $("sample-image").getAttribute("src") !== sampleUrl) $("sample-image").src = sampleUrl;
  const running = job.status === "running";
  const canSave = job.export_available ?? Boolean(job.result && !running);
  const exportUrl = job.export_available ? `/api/jobs/${job.id}/export?v=${job.export_revision}` : `/api/jobs/${job.id}/result`;
  const manualDraft = Boolean(job.export_draft && !running);
  $("open-attempts").hidden = !$("show-intermediate").checked;
  const showingPreview = Boolean($("show-intermediate").checked && (job.preview || canSave) && running);
  const showingResult = showingPreview || Boolean(canSave && !running);
  $("result-image").hidden = !showingResult;
  $("result-empty").hidden = showingResult;
  const displayUrl = showingPreview && !job.export_available ? `/api/jobs/${job.id}/preview?v=${job.preview_revision}` : exportUrl;
  if (showingResult && $("result-image").getAttribute("src") !== displayUrl) $("result-image").src = displayUrl;
  $("result-empty").querySelector("strong").textContent = job.status === "running" ? (job.sample ? "Dein Sample wird verbessert …" : "Dein SVG entsteht …") : "Platz für dein SVG";
  $("result-empty").querySelector("p").textContent = running ? ($("show-intermediate").checked ? "Die Suche läuft. Sobald ein erster SVG-Zwischenstand vorliegt, erscheint er hier automatisch." : "Die Suche läuft. Hier erscheint das Endergebnis. Du kannst die Zwischenergebnisse jederzeit einschalten.") : "Nach der Konvertierung siehst du hier das Ergebnis.";
  const draft = draftQuality(job);
  $("status").textContent = draft?.message || job.message;
  if (manualDraft && !job.result) $("status").textContent += " Ein Vektorentwurf ist zur manuellen Beurteilung und zum Speichern verfügbar.";
  $("status-dot").className = `status-dot ${job.status === "running" ? "running" : job.quality === "warning" ? "warning" : ["error", "timeout", "interrupted"].includes(job.status) ? "error" : ""}`;
  $("elapsed").textContent = job.elapsed ? `${Math.round(job.elapsed)} s` : "";
  $("log").textContent = job.log || "Das Protokoll erscheint nach dem Start der Konvertierung.";
  $("save-actions").hidden = !canSave;
  $("project-status").hidden = !job.project_save;
  $("project-status").textContent = job.project_save?.message || "";
  $("use-plan-b").hidden = serverNeedsRestart || !job.result || job.quality !== "passed" || job.status !== "done";
  $("download").href = `${exportUrl}${exportUrl.includes('?') ? '&' : '?'}download=1`;
  $("download").download = `${job.name.replace(/\.[^.]*$/, "")}.svg`;
  $("quality").className = `hint ${job.quality === "warning" ? "quality-warning" : job.quality === "passed" ? "quality-passed" : ""}`;
  $("quality").textContent = running ? (showingPreview ? "Zwischenstand · Suche und Qualitätsprüfung laufen weiter." : "Suche und Qualitätsprüfung laufen.") : draft ? draft.summary : job.quality === "warning" ? "Entwurf · Qualitätsprüfung noch offen" : job.quality === "passed" ? (job.sample ? "Pixelprüfung bestanden · Sample am Original optimiert" : "Qualitätsprüfung bestanden · Bereit zum Herunterladen") : "Original und Ergebnis lassen sich gemeinsam vergrössern.";
  if (canSave && (running || manualDraft)) {
    $("quality").textContent += " Du kannst die aktuelle Version nach eigener Beurteilung speichern.";
    if (manualDraft) $("quality").className = 'hint quality-warning';
  }
  $("sample-metrics").hidden = !job.sample_report;
  if (job.sample_report) {
    const report = job.sample_report;
    const percent = report.initial_mse > 0 ? Math.max(0, (1 - report.final_mse / report.initial_mse) * 100) : 0;
    $("sample-metrics").textContent = `Sample-Vergleich: ${percent.toFixed(1)} % weniger mittlerer Pixelfehler · ${report.evaluations} geprüfte Anpassungen. Vorhandene Formen werden optimiert.`;
  }
  $("result-meta").textContent = showingPreview ? "SVG · Zwischenstand · Suche läuft" : running ? "SVG · Suche läuft" : manualDraft || job.quality === "warning" ? "SVG · Entwurf" : "Vektorgrafik · SVG";
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
    status.textContent = draftQuality(job)?.history || (job.quality === "warning" ? "SVG-Entwurf · Bitte prüfen" : statusLabels[job.status] || job.status);
    text.append(name, status); button.append(img, text); button.title = job.name;
    button.addEventListener("click", async () => {
      try { notice(); await saveDescription(); renderJob(await request(`/api/jobs/${job.id}`), true); renderHistory(); } catch (error) { notice(error.message); }
    });
    $("history").append(button);
  }
  controls();
}
async function refreshHistory() {
  history = (await request("/api/jobs?scope=foreground")).filter(job => !job.catalog_background);
  renderHistory();
}
async function update(operation, select = false, input = null, persistDescription = true) {
  if (busy) return;
  busy = true; controls(); notice();
  let changed = false;
  try {
    if (persistDescription) await saveDescription();
    const job = await operation();
    if (!job) return;
    renderJob(job, select);
    changed = true;
  } catch (error) { notice(error.message); }
  finally { busy = false; if (input) $(input).value = ""; controls(); }
  // History is secondary: a slow request must never lock the stop button.
  if (changed) {
    try { await refreshHistory(); } catch (error) { notice(error.message); }
  }
}
function sendFile(path, file) {
  return request(`${path}?name=${encodeURIComponent(file.name)}`, { method: "POST", headers: { "X-ImageConverter": "1" }, body: file });
}
async function recognizeUpload(job) {
  if (imageRecognition && !job.description) {
    $("recognition-status").hidden = false;
    $("recognition-status").textContent = 'Bild wird lokal untersucht. Beim ersten Mal werden die geprüften Vergleichsbilder eingelesen …';
    try { return await post(`/api/jobs/${job.id}/recognize`, {}); }
    catch (error) { notice(`Bild geladen. Die Erkennung konnte nicht abgeschlossen werden: ${error.message}`); }
  }
  return job;
}
function upload(file) {
  if (!file || activeId || busy) return;
  if (file.size > 25 * 1024 * 1024) return notice("Bitte ein Bild mit maximal 25 MB auswählen.");
  return update(async () => recognizeUpload(await sendFile("/api/upload", file)), true, "file");
}
$("recognize").addEventListener('click', () => {
  if (!current || busy || activeId) return;
  const empty = !$("description").value.trim();
  $("recognition-status").hidden = false;
  $("recognition-status").textContent = 'Bild wird lokal untersucht …';
  return update(async () => {
    const job = await post(`/api/jobs/${current.id}/recognize`, {});
    if (empty && job.recognition?.automatic) $("description").value = job.recognition.automatic.description;
    $("recognition-details").open = true;
    return job;
  });
});
$("check-description").addEventListener('click', async () => {
  if (!current || busy || activeId || !descriptionCheck || descriptionSaving) return;
  clearTimeout(descriptionSaveTimer);
  const text = $("description").value;
  try {
    await update(() => post(`/api/jobs/${current.id}/check`, {description:text}), false, null, false);
  } finally {
    if (descriptionDirty && descriptionAutosave) descriptionSaveTimer = setTimeout(() => saveDescription().catch(error => notice(error.message)), 600);
  }
});
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
      return result.selected ? (kind === 'image' ? recognizeUpload(result.job) : result.job) : null;
    }, kind === "image", input);
  });
}
$("pick-sample").addEventListener("click", () => $("sample-file").click());
$("remove-sample").addEventListener("click", () => changeSample(null));
function descriptionEdited() {
  descriptionDirty = Boolean(current) && $("description").value !== current.description;
  renderDescriptionCheck(current);
  clearTimeout(descriptionSaveTimer);
  $("description-save-status").className = 'hint';
  $("description-save-status").textContent = descriptionDirty
    ? (descriptionAutosave ? 'Wird automatisch gespeichert …' : 'Noch nicht gespeichert. Bitte den Webserver neu starten.')
    : current?.description_save?.message || 'Keine ungespeicherten Änderungen.';
  if (descriptionDirty && descriptionAutosave) descriptionSaveTimer = setTimeout(() => saveDescription().catch(error => notice(error.message)), 600);
  controls();
}
async function saveDescription() {
  clearTimeout(descriptionSaveTimer);
  if (descriptionSaving) {
    await descriptionSaving;
    if (descriptionDirty) return saveDescription();
    return;
  }
  if (!current || !descriptionDirty || !descriptionAutosave) return;
  const jobId = current.id, text = $("description").value;
  $("description-save-status").textContent = 'Beschreibung wird gespeichert …';
  const operation = (async () => {
    try {
      const job = await post(`/api/jobs/${jobId}/description`, {description:text});
      if (current?.id !== jobId) return;
      descriptionDirty = $("description").value !== text;
      renderJob(job);
      if (job.id !== jobId) window.history?.replaceState({}, '', `/?job=${encodeURIComponent(job.id)}`);
      history = [job, ...history.filter(previous => previous.id !== job.id)];
      renderHistory();
      $("description-save-status").className = job.description_save?.warning ? 'hint quality-warning' : 'hint';
      $("description-save-status").textContent = descriptionDirty ? 'Weitere Änderung wird gespeichert …' : job.description_save?.message || 'Beschreibung gespeichert.';
    } catch (error) {
      $("description-save-status").className = 'hint quality-warning';
      $("description-save-status").textContent = 'Nicht gespeichert. Bitte «Text speichern» erneut versuchen.';
      throw error;
    }
  })();
  descriptionSaving = operation; controls();
  try { await operation; } finally { descriptionSaving = null; controls(); }
  if (descriptionDirty) return saveDescription();
}
$("description").addEventListener("input", descriptionEdited);
$("description").addEventListener("blur", () => saveDescription().catch(error => notice(error.message)));
$("save-description").addEventListener("click", () => saveDescription().catch(error => notice(error.message)));
window.addEventListener('pagehide', () => {
  if (!current || !descriptionDirty || !descriptionAutosave || activeId) return;
  fetch(`/api/jobs/${current.id}/description`, {method:'POST', keepalive:true,
    headers:{'Content-Type':'application/json', 'X-ImageConverter':'1'},
    body:JSON.stringify({description:$("description").value})}).catch(() => {});
});
function randomSeed() {
  const words = crypto.getRandomValues(new Uint32Array(2));
  return ((BigInt(words[0]) << 32n) | BigInt(words[1])).toString();
}
function validateSeed() {
  const value = $("seed").value;
  const valid = /^[0-9]{1,20}$/.test(value) && BigInt(value) <= 18446744073709551615n;
  $("seed").setCustomValidity(valid ? "" : "Bitte eine ganze Zahl zwischen 0 und 18446744073709551615 eingeben.");
  return valid;
}
$("seed").addEventListener("input", validateSeed);
$("random-seed").addEventListener("click", () => {
  $("seed").value = randomSeed();
  validateSeed();
});
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
  if (!current || busy || activeId || !editableSearchSeed || !currentSvgReuse) return;
  validateSeed();
  if (!$("seed").reportValidity()) return;
  if ($("show-intermediate").checked) openAttemptWindow();
  return update(() => post(`/api/jobs/${current.id}/start`, { description: $("description").value, profile: $("profile").value, seed: $("seed").value, use_current_svg: $("use-current-svg").checked }));
});
$("cancel").addEventListener("click", () => {
  if (!activeId || busy) return;
  return update(() => post(`/api/jobs/${activeId}/cancel`, {}));
});
$("save-as").addEventListener("click", async () => {
  if (!(current?.export_available ?? current?.result) || saving) return;
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
    const description = $("description").value;
    const report = await post(`/api/jobs/${current.id}/workbench`, {description});
    if (report.source_description !== description.trim()) throw new Error("Der Webserver hat noch die alte Beschreibung übernommen. Bitte nach Abschluss laufender Aufgaben den Webserver neu starten und diese Seite neu laden.");
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
    renderJob(job);
    if (!activeId) await refreshHistory();
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
      editableSearchSeed = config.editable_search_seed === true;
      imageRecognition = config.image_recognition === true;
      descriptionCheck = config.description_check === true;
      descriptionAutosave = config.description_autosave === true;
      currentSvgReuse = config.current_svg_reuse === true;
      if (!config.manual_svg_export) {
        $("server-version-warning").textContent = "Zum Speichern von Zwischenständen und abgelehnten Entwürfen bitte den Webserver nach Abschluss laufender Konvertierungen mit stopWebServer.cmd und startWebServer.cmd neu starten und diese Seite neu laden.";
        $("server-version-warning").hidden = false;
      }
      for (const option of $("profile").querySelectorAll("option")) {
        if (["explore5", "explore10"].includes(option.value)) option.disabled = config.primitive_exploration !== true;
      }
      if (!currentSvgReuse) {
        serverNeedsRestart = true;
        $("server-version-warning").textContent = "Für die automatische SVG-Wiederverwendung muss der Webserver neu gestartet werden. Lass laufende Konvertierungen fertig werden, führe stopWebServer.cmd und danach startWebServer.cmd aus und lade diese Seite neu.";
        $("server-version-warning").hidden = false;
      }
      if (!config.parallel_background_conversion) {
        serverNeedsRestart = true;
        $("server-version-warning").textContent = "Der laufende Webserver verwendet noch eine ältere Version, die manuelle Konvertierungen während des Hintergrunddienstes blockieren kann. Bitte stopWebServer.cmd und danach startWebServer.cmd ausführen und diese Seite neu laden. Anschliessend den Hintergrunddienst bei Bedarf wieder starten.";
        $("server-version-warning").hidden = false;
      }
      if (!editableSearchSeed) {
        serverNeedsRestart = true;
        $("server-version-warning").textContent = "Für editierbare Seeds muss der Webserver neu gestartet werden. Lass laufende Konvertierungen fertig werden, führe stopWebServer.cmd und danach startWebServer.cmd aus und lade diese Seite neu.";
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
    // Retry links can still name the immutable original job. Keep the active
    // foreground conversion reachable even when that old link is reloaded.
    const selected = running || (requestedId ? await request(`/api/jobs/${encodeURIComponent(requestedId)}`) : history[0]);
    if (selected) renderJob(selected, true);
    renderHistory();
  } catch (error) { notice(`Die Oberfläche konnte nicht geladen werden. ${error.message}`); }
}
$("collection-next").addEventListener('click', async () => {
  if (!current?.collection_next_case_id || busy || activeId) return;
  busy = true; controls(); notice();
  try {
    await saveDescription();
    const next = await post(`/api/collection/${current.collection_next_case_id}/load`, {});
    window.location.assign(`/?job=${encodeURIComponent(next.id)}`);
  } catch (error) {notice(error.message);} finally {busy=false;controls();}
});
init();
