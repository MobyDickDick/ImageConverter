# P0: Kreis- und Rechteckinstanzen gemeinsam überdecken

Ausgewählt aus **SEARCH-STRUCTURE-01**, dem höchsten Rang der
[priorisierten Aufgabenliste](task_priority_2026-10-24.md). Ausgangscommit:
`0927496bb`. Separater Branch:
`codex/search-structure-mixed-primitives-2026-10-24`.

## Änderung und Abnahmeumfang

Der vorhandene Verlaufskreis-/Struktursuchweg kombiniert jetzt teilweise
überlappende, verschiedenfarbige Kreis- und Rechteckkinder. Rechtecke dürfen
weiterhin leicht gerundete Ecken haben. Es entstehen native `circle`- und
`rect`-Elemente; es gibt keine Familienkennung, Konturpfade oder gelesenen
Referenzvektoren im Konvertierungsprozess.

Der Kreisvorschlag verwendet die vorhandene robuste Bogenanpassung aus der
Szenenfusion. Nur sichtbare, dem gemessenen Elternverlauf zugewandte Grenzen
liefern Bogenpunkte. Mindestens ein halber Kreisumfang muss die Hypothese
stützen; Schnittkanten an fremder Farbe liefern keine versteckten Radien.
Sichtbare Kantenglättung verfeinert Mittelpunkt und Radius vor der Registrierung.
In den zusätzlich untersuchten 20 Kreisen des Rundungsseeds `983147` sinkt der
maximale Boxfehler der Startschätzung auf etwa `0,0232` Pixel. Zwei gezielte
Tests sichern die Subpixelmessung ohne Registrierung.

Die beobachtete Überdeckungsreihenfolge und ihre abschließende Tiefenprüfung
verwenden für gemischte Kinder tatsächliche native Silhouetten. Schnittflächen
von Kreis-Boundingboxen außerhalb der Füllung sind keine Tiefenbelege. Spätere
Schichten werden mit ihrer Silhouette aus dem Paarbeleg entfernt. Die bisherige
Rechteckabnahme bleibt erhalten. Das gemeinsame Bildbudget, die Agenda mit
höchstens 96 Zuständen sowie Objekt-, Relations-, lokale und globale Rastergates
gelten weiter. Abgelehnte und doppelte Vorschläge bleiben sichtbar.

## Vergleich und Reproduktion

Zwölf synthetische Szenen mit zwei, drei und vier inneren Formen, beiden
Verlaufsachsen und unterschiedlichen Zeichenreihenfolgen wurden **vor** der
Runtime-Änderung mit Generatorseed `486213` gespeichert. Auf der unveränderten
Basis bestehen **0/12**, in der ersten Implementierung **12/12** über die echte
überwachte CLI. Suchseed `17`, fünf Sekunden je Bild; alle Eingaben und nativen
Markierungen bleiben identisch. Der endgültige Wiederholungslauf und kompakte
Prüfsummen stehen unter
[`mixed_overlap_v1/summary.json`](../artifacts/evaluation/mixed_overlap_v1/summary.json).

Der erste zusätzliche gerundete CLI-Lauf mit Seed `983147` erreicht **11/12**.
Ein Fall liefert während gleichzeitiger Regressionstests keine Ausgabe im
Fünf-Sekunden-Budget; die direkte Gegenprobe besteht. Anschließend wird die
Kreisstartgeometrie aus beobachteter Kantenglättung verfeinert. Der Fehlversuch
bleibt im Bericht; eine Wiederholung ersetzt diesen Nenner nicht.

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 486213
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 983147 --rounded
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 624819 --rounded --variations
.venv/Scripts/python.exe -m pytest -q tests/test_mixed_overlap_composition.py tests/test_observed_depth_order.py
.venv/Scripts/python.exe tools/run_pytest_profile.py core-green
```

Die CLI läuft mit Schreib-/Leseaudit; der unabhängige Prüfer rastert die
tatsächlich gespeicherten SVGs neu und prüft Instanzzahl, Formklasse, Geometrie,
Eltern-/Tiefenrelationen und lokale/globale Pixelwerte. Wiederholbare Zusatzläufe
speichern zuerst ihre Seeds und entfernen die erzeugten Arbeitsdaten auch nach
Fehlern. Die neue CI-Gruppe verwendet denselben Ablauf.

## Grenzen

Geprüft werden synthetische Entwicklungsszenen mit zwei bis vier inneren Formen
und eine zusätzliche Zwei-Kreise-Gegenprobe. Die gemeinsame Inventargrenze von
acht Kindern ist keine neue Abnahme aller gemischten Fünf-bis-acht-Kinder-Szenen.
Helle Konturen bei verdeckten inneren Kreisen bleiben ausdrücklich unsupported;
ihre beiden Radien werden nicht aus verdeckten Grenzen erfunden. Gleiche Farben,
fehlende Formen, Ellipsen, Rechteckersatz für Kreise, Fremdtextur, falsche Tiefe,
fehlende sichtbare Bögen und nur scheinbar überlappende Boxen bleiben Gegenproben.

Keine neue reale Familien-/Katalogabnahme. **SEARCH-STRUCTURE-01 bleibt als
Gesamtaufgabe offen**: weitere Kompositionen und unabhängige reale Übertragung
fehlen. Die archivierten 379 Paare werden nicht erweitert oder neu bewertet.
Es wird keine vollständige Standardsuite beansprucht; die ausgeführten
Testsignale einschließlich erster Fehlläufe stehen in `checks.json`.

## Abschließende Prüfung und Sitzungslog

Der endgültige serielle CLI-Lauf besteht **12/12** unveränderte Vergleichsfälle,
**12/12** zusätzliche Rundungsszenen und **17/17** gekoppelte Plan-B-Variationen.
Die anfänglichen 11/12 der Rundungsserie bleiben separat erhalten. Der letzte
gezielte Testlauf besteht **46/46** (Exit 0), das schnelle Kernprofil **42/42**
(Exit 0). Alle 758 Archiv-Prüfsummen der 379 Paare sind unverändert.

Die breitere Testgruppe endet zuerst mit **327 bestanden, drei fehlgeschlagen,
einem Skip** (Exit 1). Die gezielte Wiederholung endet mit **89 bestanden,
drei fehlgeschlagen** (Exit 1). Betroffen sind vorhandene Acht-Rechteck-Szenen
mit Rundung und Konturen bei Seed `527183`, Indizes 0, 1 und 3. In einer
seriellen Gegenprobe scheitern auch Indizes 1 und 3 mit dem unveränderten
Ausgangsmodul vor der ersten Rasterauswertung am Fünf-Sekunden-Budget.
Erkannte Instanzen und Reihenfolge sind gleich; eine getrennte 20-Sekunden-
Diagnose für Index 1 liefert bytegleiche SVGs. Das ist keine nachträgliche
Abnahme mit gelockertem Budget. Die bestehende Zeit-/Teststabilitätsgrenze
bleibt bei TB/FP; keine grüne Gesamtsuite wird behauptet.

- Getestet: echte überwachte CLI, unabhängige Objekt-/Regions-/Pixelgates, 46 neue Tests, Kernprofil und angrenzende Überdeckungstests.
- Ergebnis: 0/12 auf 12/12; zusätzliche 12/12 und 17/17; Archiv unverändert.
- Blocker: bestehende Fünf-Sekunden-Testgrenze bei großen gerundeten Konturinventaren; unabhängige reale Abnahme fehlt.
- Nächster Schritt: verdeckte Kreiskonturen und weitere Kompositionen nur mit beobachtbaren Grenzen entwickeln; reale Prüffamilien vor realer Entwicklung sperren.
- Morgiger Startbefehl: `.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 983147 --rounded`.
