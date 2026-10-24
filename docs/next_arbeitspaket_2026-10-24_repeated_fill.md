# P0: wiederholte Füllfarben als alternative Instanzzerlegung

Ausgewählt aus **SEARCH-STRUCTURE-01**, Rang 1/P0 der
[verbindlichen Rangliste](task_priority_2026-10-24.md). Ausgangscommit
`93822e748`; eigener Branch
`codex/search-structure-mixed-inventories-2026-10-24`.

## Ursache und Änderung

Größere gemischte Inventare mit unterschiedlichen Farben funktionieren bereits
im vorhandenen Verlaufskreis-/Struktursuchweg. Die konkrete neue Gegenprobe
enthält sechs teilweise überlappende Kreis-/Rechteckkinder, darunter zwei
räumlich getrennte Kreise derselben Füllfarbe. Der Detektor vereinigte sämtliche
sichtbaren Flächen einer Farbe zu genau einem Instanzvorschlag. Dadurch fehlten
Instanzen oder eine falsche große Ersatzform entstand. Deren Begrenzungsbox
sperrte außerdem die Eckradiusmessung dazwischenliegender Rechtecke.

Die bestehende Vereinigung bleibt die erste Hypothese: Eine einzelne Instanz
kann durch spätere Schichten in mehrere sichtbare Inseln zerfallen. Erst nach
erfolgloser bestehender Suche liefert `split_components` als zweite Hypothese
die einzelnen ausreichend großen Farbkomponenten. Jede braucht weiterhin
eigene sichtbare Kreisbögen beziehungsweise vier beobachtete Rechteckseiten.
Die Fremdflächenmaske für Rundungen verwendet die jeweilige Komponentengruppe.
Sie lässt dadurch keine unbeobachteten Ecken zu.

Die Vorschläge verwenden denselben Scheduler, die beobachtete Zeichenreihenfolge,
bildgebundene negative Evidenz und die vorhandene begrenzte Edit-Suche.
Reihenfolgen bleiben auch bei der Deduplizierung der Split-Vorschläge erhalten.
Höchstens acht Kinder, 96 Edit-Zustände, unveränderte native Objekt-/Relations-,
lokale und globale Rastergates sowie das gemeinsame Bildbudget gelten weiter.
Der Konverter liest keine Referenzvektoren oder Katalogkennungen.

## Kontrollierter Nachweis

Die zwölf synthetischen Entwicklungseingaben wurden mit Seed `527183`, sechs
Kindern, Rundung und hellen Konturen vor der Runtime-Änderung gespeichert.
Die serielle Gegenprobe setzt ausschließlich das produktive Modul temporär auf
den unveränderten Ausgangsstand zurück und stellt es danach wieder her.
Ein zuvor mit laufenden Änderungen überlappender Versuch wird verworfen und
nicht als Baseline gezählt. Die kontrollierte Baseline besteht **0/12**;
Suchzeitabbrüche ohne SVG bleiben im Nenner. Der Nachherlauf verwendet exakt
dieselben Eingabedateien, Suchseed 17 und fünf Sekunden je Bild und besteht
**12/12**. Der zusätzliche Seed `918527` besteht **12/12**; genau eine gekoppelte
Plan-B-Vorlage mit Seed `342781` besteht **17/17**. Alle endgültigen Fälle melden
`satisfactory` innerhalb des gemeinsamen Fünf-Sekunden-Suchbudgets.

Die unabhängige Abnahme prüft die echten CLI-SVGs erneut auf native Instanzen,
Geometrie, Zeichenreihenfolge, lokale Regionen und das vollständige Raster.
Kompakte Messungen, Eingabe-/Ausgabehashes und Laufsteuerung stehen unter
[`artifacts/evaluation/repeated_fill_overlap_v1/`](../artifacts/evaluation/repeated_fill_overlap_v1/README.md).
Generierte Raster, Vektoren und CLI-Bäume sind temporäre Arbeitsdaten.

```powershell
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 527183 --children 6 --repeat-fill --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 918527 --children 6 --repeat-fill --rounded --outlines
.venv/Scripts/python.exe -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 342781 --children 6 --repeat-fill --rounded --outlines --variations
.venv/Scripts/python.exe -m pytest -q tests/test_repeated_fill_overlap.py
```

32 neue Tests prüfen fünf, sechs und acht Kinder mit und ohne Rundung/Konturen,
wiederholte Kreis- und Rechteckfarben, falsche Anzahlen, Zusatzinstanzen gleicher
Farbe, verdeckte Bögen und Fremdtextur. Eine positive Gegenprobe erhält die
Vereinigung der sichtbaren Inseln eines einzelnen verdeckten Kreises.
Ein eigener CI-Job wiederholt diese Tests und die zusätzlichen CLI-Szenen.

Die gemeinsame Regression über die neue Suite, bestehende gemischte Szenen,
Restbild-, Add/Remove/Replace-, Split-, Rundungs-, Überdeckungs-, Scheduler- und
Datenlebenszyklusprüfungen besteht mit **559 Tests und einem Skip**, Exit 0
(384,18 Sekunden). Das Kernprofil besteht **42/42**, Exit 0. Die 32 neuen Tests
sind in den 559 bereits enthalten. Der Skip betrifft die bestehende Prüfung
von Dateisystemlinks, deren Erstellung Windows-Berechtigungen voraussetzt.
Exakte Befehle und Laufzeiten stehen in `checks.json`.

## Grenzen

Dies ist ein synthetischer Teilabschluss. Beliebige Kombinationen aus mehreren
gleichfarbigen Instanzen und gleichzeitig aufgeteilten Sichtbarkeitsinseln sind
noch nicht erschöpfend kombinierbar. Nicht beobachtbare Grenzen werden weiterhin
abgelehnt. Neue unabhängige reale Familien sind nicht abgenommen;
**SEARCH-STRUCTURE-01 bleibt insgesamt offen.** Es wird keine neue Katalogzahl
und keine grüne vollständige Standardsuite beansprucht.

## Sitzungslog

- Getestet: kontrollierter CLI-Vergleich, Zusatzseed, 17 Plan-B-Fälle, Gegenproben und Kernprofil.
- Ergebnis: 0/12 → 12/12, zusätzliche 12/12 und 17/17; Testsignale in `checks.json`.
- Blocker: unabhängige reale Abnahme und beliebige Kombinationen aus Instanzen und Sichtbarkeitsinseln bleiben offen.
- Nächster Schritt: getrennte Instanz- und Inselgruppierungen unter demselben Budget kombinieren und an vorab gesperrten realen Familien prüfen.
- Startbefehl: `python -m tools.run_seeded_scene_check evaluate_mixed_overlap --seed 918527 --children 6 --repeat-fill --rounded --outlines`.
