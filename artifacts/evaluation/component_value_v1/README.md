# Definitive Komponenten-Gegenproben

348 echte überwachte Versuche mit 343 gespeicherten SVGs und 230 unabhängigen
Freigaben. Alle 377 Archivpaare bleiben unverändert. Abgeschaltete Bots werden
bereits vor der Konstruktion ausgefiltert; Konstruktor- und Vorschlagswächter
prüfen alle sechs Einzelabschaltungen sowie das vollständig abgeschaltete Portfolio.

- 324 Produktionsversuche: neun Quellen, zwölf Varianten, drei Seeds,
  jeweils fünf Sekunden einschließlich Workerstart und Abschlussprüfung.
- 24 Kontrollen: zwei Quellen, vier Varianten, drei Seeds, fester Ablauf mit
  Vorschlagsbasis 32 und identischem 15-Sekunden-Budget je Kontrollarm.
  Zwei austauschbare Renderer-Zugänge liefern dieselben SVGs; ohne beide gibt
  es keine vollständige Freigabe. Zwei Sekunden Zusatzwartezeit je Worker
  erhalten die SVGs und erhöhen den Aufwand.
- Fünf Versuche ohne gültige Ausgabe bleiben im Nenner. Einer endet vor der
  Schalterbeobachtung; seine Konfiguration und Aktivität werden als unbeobachtet
  ausgewiesen. Ohne Beobachtung kann er keine positive Kontrollabnahme belegen.
- Eine nach einem Reporterfehler aus nativen Artefakten nachgelesene Zelle hat
  für neun Einträge keine aufgezeichnete CLI-Batchdauer und keinen Exitcode.
  Diese Felder bleiben `null`; die echten Bildzeiten und Ausgaben sind erhalten.

Das vollständige Portfolio besteht 18/27 Produktionsfälle. Ohne gemeinsame
Neustarts, ohne Feinregistrierung, nur mit Geometrie sowie nur mit Geometrie
plus Neustarts sind es jeweils 17/27; die anderen Varianten bestehen 18/27.
Alle produktiven Einstufungen bleiben unklar. Es wird keine Komponente entfernt
oder mit Abnahmedaten nachtrainiert. Der getrennte Bestand steht unter
`../component_retention_v1`.

Versioniert sind diese README, `manifest.json`, `checks.json` und `summary.json`.
Die kompakte Zusammenfassung enthält Ergebnisse, Unsicherheiten, Kontrollkriterien,
Quell-/Berichthashes und Testzahlen. Generierte Raster, SVGs, JSONL-Ereignisse,
vollständige Berichte und Testlogs bleiben lokal erhalten und werden von Git
ignoriert. CI-Läufe laden ihre vollständigen Belege als Workflow-Artefakte hoch.

`manifest.json` bindet Raster, Texte und Objekt-Orakel. Das lokale `report.json` enthält
die gesamte Matrix, Einzelmetriken, tatsächliche Registrierer/Suchgewinner,
Schalter, Bild-/Batchzeit und beobachteten Worker-Speicher. `outputs/` und
`telemetry/` enthalten SVGs und Rohereignisse mit SHA-256-Bindungen.

Der Repository-Testlauf lief zeitweise parallel. Einzelne CLI-Batches haben
außerdem extreme Unterbrechungen; die größte aufgezeichnete Batchdauer beträgt
22.587,672 Sekunden. Die Rohzeiten bleiben erhalten. Bildzeiten und Batchzeiten
sind getrennt; daraus folgt keine Garantie für die CLI-Gesamtdauer.

Voruntersuchungen mit gemeinsamem Bot-Setup sowie zwei fehlgeschlagene
Kontrollentwürfe bleiben unter `component_activation_probe_v1`,
`component_retention_activation_probe_v1`, `component_control_timing_probe_v1`
und `component_control_render_delay_v1` lokal im benachbarten Verzeichnis erhalten.
Auch diese generierten Voruntersuchungen werden von Git ignoriert.
Sie ersetzen diese vollständig wiederholte definitive Matrix nicht.

```powershell
.venv/Scripts/python.exe -m tools.run_component_value --output-dir .tmp/component-replay --work-dir .tmp/component-replay-work
.venv/Scripts/python.exe -m tools.run_component_value --verify-only --output-dir .tmp/component-replay
```

Die archivierte lokale Messung lässt sich mit `--verify-only --output-dir
artifacts/evaluation/component_value_v1` prüfen, solange ihre Rohdaten vorliegen.
Ein frischer Checkout enthält nur die kompakten Nachweise; dort zuerst neu messen.
