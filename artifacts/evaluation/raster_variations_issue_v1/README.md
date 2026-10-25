# Reproduzierbare Rastervarianten für GitHub-Issue #1980

Der technische Fehler aus [#1980](https://github.com/MobyDickDick/ImageConverter/issues/1980)
ist mit unveränderter Quelle, Beschreibung, vollständigem Seed und Budget
reproduziert. Die Quelle misst im Prüfraster 51 × 5 Pixel. Die ursprünglichen
16 Transformationen erzeugen zusammen mit dem Original nur 15 unterschiedliche
Raster. `probe_11` entspricht `probe_02`; deshalb bricht die Vorbereitung nach
dem bestandenen Original ab. Unterschiedliche Vektoren sind hier kein Beweis
für unterschiedliche Eingabebilder.

Es gibt keine GitHub-Prioritätslabels. Dieser technische Blocker wurde vor
weiteren Änderungen an Konvertierungsmodellen gewählt, weil er die eigentliche
Qualitätsprüfung verhindert. Die allgemeine P0-Struktursuche bleibt separat.

## Hypothesen und Korrektur

1. **Nur den Seed wechseln:** Seed `817263` liefert bereits 17 unterschiedliche
   Raster, Seed `20261025` dagegen nur 13. Ein Seedwechsel garantiert die
   Ausführbarkeit nicht und würde den ursprünglichen Fehlerbeleg ersetzen.
2. **Nur doppelte Raster neu auswählen:** Der ursprüngliche Kandidatenstrom
   bleibt erhalten. Ein eigener deterministischer Zufallsstrom ersetzt
   ausschließlich Duplikate; bereits geeignete Kandidaten bleiben unverändert.
   Auf den drei Seeds entstehen 17 unterschiedliche Raster nach 20, 16 bzw. 24
   Kandidatenprüfungen. Die gemessene Vorbereitung dauert lokal 0,015–0,034 s.

Der Vergleich verwendet ausschließlich Eingaberaster, niemals Konvertierungs-
oder Qualitätswerte. Skalierung (0,94–1,06), Verschiebung (±0,025), Bildmaße und
gekoppelte Beschreibungen bleiben verbindlich. Auch ein Duplikat des Originals
wird abgelehnt. Pro Vorbereitung gelten höchstens 256 Kandidatenprüfungen.
Bei erschöpftem Raum gibt es einen ausdrücklichen Vorbereitungsfehler mit Seed,
Bildgröße und Prüfzahl; ein partieller Lauf wird nicht als Erfolg gewertet.
Der Bericht bewahrt die Anzahl verworfener Kandidaten je akzeptierter Variante.

## Echte CLI-Prüfung und verbleibende Grenze

| Lauf | Vorbereitungsstatus | CLI-Fälle | Qualität bestanden |
| --- | --- | --- | --- |
| Unveränderter Ausgangsstand, Originalseed | Abbruch wegen Duplikat | 1/17 | 1/17 |
| Korrektur, Originalseed | vollständig | 17/17 | 3/17 |
| Korrektur, Zusatzseed 817263 | vollständig | 17/17 | 2/17 |

Alle 34 neuen CLI-Aufrufe schließen ohne Prozessfehler und ohne verbotenen
Referenz-SVG-Zugriff ab. Die Raster sind je Lauf einschließlich Original
17-fach verschieden. Die vorhandenen Qualitätsgrenzen lehnen die verbleibenden
14 bzw. 15 Fälle weiter ab. **Das ist eine Reparatur der Vorbereitung, keine
vollständige fachliche Abnahme von #1980. Das Issue bleibt offen.** Die
Erfolgsarchivzahl wird nicht erhöht und die angehaltene Zufallssuche nicht aktiviert.

Die aktuelle Rasterisierung zeigt trotz der im SVG referenzierten rosa
Gradienten einen weitgehend schwarzen Streifen. Dieser bestehende
Render-/Konvertierungsbefund und die wenig eigenständige Rohr-Familienbeschreibung
benötigen eine getrennte Quellen- und Qualitätskorrektur; die Generatorreparatur
kopiert dafür keine Vektorvorlagen in die Runtime.

## Wiederholung

`manifest.json` bewahrt SHA-256, Beschreibung, vollständigen Seed, Iterations-
und Zeitbudget. `summary.json` enthält Messwerte, Parameter, Hashes, Laufzeiten
und die ausdrücklich negativen Qualitätsresultate aller ausgeführten Fälle.
Vollständige lokale Daten liegen unter `.tmp/issue-1980-before`,
`.tmp/issue-1980-after` und `.tmp/issue-1980-holdout`.

```powershell
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/raster_variations_issue_v1/manifest.json --output-dir .tmp/raster-variations-frozen
.venv/Scripts/python.exe -m tools.replay_plan_b_issue_batch --manifest artifacts/evaluation/raster_variations_issue_v1/manifest.json --output-dir .tmp/raster-variations-holdout --seed 817263
.venv/Scripts/python.exe -m pytest -q tests/detailtests/test_plan_b_variations.py tests/detailtests/test_plan_b_failure_tasks.py tests/test_plan_b_issue_inventory.py
.venv/Scripts/python.exe tools/run_pytest_profile.py core-green
```

Die Replay-Befehle liefern wegen der verbleibenden Qualitätsfehler Exitcode 1;
der Bericht muss jetzt `completed` mit 17 Fällen enthalten. Beide Testbefehle
liefern Exitcode 0 (64 bzw. 42 Tests). Die eigene CI-Prüfung trennt den
technischen Abschluss ausdrücklich vom unveränderten Qualitätsstatus und
bewahrt vollständige CLI-Ergebnisse 14 Tage.
