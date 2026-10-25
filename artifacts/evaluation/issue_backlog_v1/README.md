# Issue-Bearbeitung vom 25. Oktober 2026

Die GitHub-Abfrage lieferte 92 offene Issues: 68 Originalfehler, 20
Variantenfehler und vier technische Ausführungsfehler. `manifest.json`
gruppiert dieselbe Quelle/Beschreibung getrennt nach Fehlerphase in 80
Untersuchungsgruppen. Das beweist noch keine gemeinsame Ursache und ist
keine Liste von 80 unabhängigen Fehlern. Alle unterschiedlichen Seeds bleiben
als ganze Python-Integer erhalten.

Erstes abgeschlossenes Korrekturpaket: #1966, #1969 und #2030. Bei verschobenen,
eng beschnittenen Verlaufspanels kann die äußerste Spalte bereits Hintergrund
sein. Ein daraus geschätzter heller Rahmen verdeckt falsch platzierte Seiten.
Die bisherige Füllgradprüfung lehnt außerdem gültige sehr helle Panels ab.

Die allgemeine Korrektur verwendet bei verfehlten lokalen Gates eine dunkle
Randbandschätzung, unabhängige Rechteckseiten und 81 gemeinsame Startlagen.
Der aus Rasterzeilen gemessene Verlauf bleibt im Bildkoordinatensystem,
während die Rahmengeometrie gesucht wird. Absolute und quadratische
Pixelverluste bilden zwei getrennte Suchhypothesen. Nur ein Kandidat, der die
unveränderten lokalen Gates besteht, ersetzt den bisherigen Fit. Ohne Erfolg
bleibt das bisherige Ergebnis erhalten. Der bestehende Bild-Timeout gilt auch
für diese begrenzten Suchschritte; Renderzahlen zählen sämtliche Versuche.

## Reproduktion

`replays.json` friert Quellen, Beschreibungen, SHA-256, vollständige Seeds und
das ursprüngliche Budget von 64 Iterationen/60 Sekunden ein. Der Replay-Runner
prüft beide Eingabehashes vor der ersten Konvertierung. Die echte CLI erhält
nur Raster und Beschreibung; Referenz-SVG-Zugriffe bleiben verboten.

```powershell
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --output-dir .tmp/issues-frozen
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --output-dir .tmp/issues-holdout --issues 1969 --seed 942817
.venv/Scripts/python.exe -m pytest -q tests/test_chevron_panel_runtime.py tests/test_plan_b_issue_inventory.py
.venv/Scripts/python.exe tools/run_pytest_profile.py core-green
```

Alle Ausgabeverzeichnisse müssen neu sein. Vollständige SVGs, Raster,
Vergleichsbilder und CLI-Logs bleiben dort erhalten; `summary.json` enthält den
kompakten Vorher-/Nachher-Beleg am Ausgangscommit `da211ee82`. Das ursprüngliche
Paket bestand 45/51 Fälle; die Korrektur besteht 51/51. Die unabhängige
Kontur-/Topologieprüfung und die neun vorhandenen realen Farb-/Größenholdouts
sind weiterhin Teil der Tests. Die Erfolgsarchivzahl wird hierdurch nicht erhöht.

Die drei Issues werden erst mit Übernahme der Korrektur geschlossen. Die 89
weiteren Issues bleiben in diesem Paket unbearbeitet. Die AC0552-Beschreibungsverweise,
weitere Symbolfamilien und die vier technischen Fehler sind Folgepakete.
