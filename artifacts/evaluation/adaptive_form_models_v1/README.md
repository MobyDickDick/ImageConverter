# Früher Formmodellvergleich · AP 1 · 21.11.2026

Der produktive Kreis-Pfeil-Fitter vergleicht jetzt zwei beschreibungskonforme
Farbmodelle: einen horizontalen Zweistoppverlauf und einen Verlauf mit zusätzlichem
Mittelstopp. Kreisscheibe, zusammenhängender Schaft und Dreiecksspitze behalten
dieselbe native Geometrie. Beide Farbmodelle stammen aus freiliegenden
Originalpixeln. Eine flache Füllung wäre bei der geforderten Verlaufsbeschreibung
unzulässig und wird nicht erzeugt.

## Auswahl und Budgets

`imageCompositeConverterFormModels.compare_form_models` erhält Modelle samt
Parametern, Konstruktor, Geometriebedingungen und vollständigem SVG-Prüfer.
Jedes Modell erhält zunächst höchstens 24 Renderings. Danach folgt eine feste
Verfeinerungsreihenfolge mit reserviertem Budget für spätere Modelle. Eine
adaptive Aufteilung oder gelerntes Ranking ist Gegenstand von AP 2/3.

Alle Proben und Verfeinerungen teilen im Kreis-Pfeil-Fitter höchstens 417 echte
Renderings, bei kleinerer `--search-budget`-Einstellung entsprechend weniger.
Renderfehler zählen mit, gemeinsame Cachetreffer verursachen kein neues Rendering.
Die bestehende Bilddeadline gilt weiter. Der kooperative Code unterbricht keinen
bereits laufenden nativen Aufruf; die harte Prozessaufsicht bleibt zuständig.

Falsche Richtung, falsche Geometrie oder eine verletzte Beschreibung verhindern
die Auswahl. Unter geometrisch gültigen Kandidaten werden bestandene Pixelgates
erhalten und dann die gemessenen Fehler verglichen. Die bestehende strengere
`preferred_quality`-Marke erlaubt einen frühen Abschluss. Ein bloßer Pixelpass
beendet den Vergleich nicht. Unterhalb der Qualitätsanforderungen bleibt der
Status `satisfactory=false`; ein solcher Fit ist kein bestätigter Erfolg.

`form_model_attempt` und `form_model_comparison_finished` protokollieren Modell,
Phase, echte Renderings, Laufzeit, Fehler, Form-/Pixelstatus und Auswahl.
Produktionsparameter speichern denselben Bericht als `form_model_comparison`.

## Vorher gesicherte Vergleichsmenge

[Manifest](manifest.json) und [gepaarte Messwerte](summary.json) binden Originale,
effektive Katalogbeschreibungen und die vor der Änderung verwendeten Quelldateien
an SHA-256. Die Baseline wurde vor der Runtimeänderung gemessen. Sie umfasst
bekannte gelungene und gescheiterte Regressionen, keine unabhängige Blindabnahme.
Sämtliche verwandten Kreis-Pfeil-Motive und Größen bleiben in der Entwicklung.
Die anderen Formgruppen dienen als unveränderte Kontrollen.

| Gruppe | Einträge | Baseline | Neuer serieller Lauf |
|---|---:|---:|---:|
| Kreis/Pfeil, Entwicklung | 7 | 5 bestanden | 5 bestanden |
| Einfacher Kreis, Kontrolle | 2 | 1 bestanden | 2 bestanden |
| Ausgespartes Diagonalpanel, Kontrolle | 1 | 0 bestanden | 0 bestanden |
| Explizite SVG-Bauteilkomposition | 1 | außerhalb Messpfad | außerhalb Messpfad |

GE0037_M/L besitzen in der aktuellen Beschreibung keinen unterstützten
Kreis-Pfeil-Vertrag und bleiben Ablehnungen. An ihren Beschreibungen wurde für
diesen Vergleich nichts geändert. GE0037_S und GE0039_L wählen im seriellen Lauf
das zusätzliche Farbmodell. Der unveränderte AC0800_M-Registrierer reagiert auf
seine zeitabhängige Verfeinerungsgrenze: er wechselte zwischen den Läufen von
Ablehnung zu Pass. Dieser Kontrollunterschied wird AP 1 nicht als Verbesserung
zugerechnet.

Die gesamten gemessenen Fitterzeiten steigen von 3,531 auf 8,438 Sekunden,
die Renderings von 411 auf 833. Die Kreis-Pfeil-Passzahl bleibt gleich.
Damit ist der funktionale Modellvergleich belegt, aber keine Verbesserung der
Katalogdurchsatzrate oder der zuvor geschätzten Erfolgsquote. Der alte
Einzelfitter besitzt keine neue gemeinsame Mehrmodellgrenze; sämtliche
beobachteten Baselineversuche lagen unter der neuen maximalen Rendergrenze.

AC0152_L wird hier **nicht** als Bauteilkonvertierung ausgeführt. Der Eintrag
steht als explizite Umfangsgrenze im Manifest und gehört nicht in den Nenner
der zehn analytisch gemessenen Fälle. Der erste Vorversuch führte diese Grenze
noch allgemein als nicht unterstützte Beschreibung; der Abschlussbericht
weist sie getrennt aus.

## Prüfung und Reproduktion

Die Baselinequellen sind durch ihre Hashes dokumentiert; lokal liegt zusätzlich
die vor Änderung verwendete Kreis-Pfeil-Datei unter `baseline_disk_arrow.py`.
Ihr Hash wurde nach Rekonstruktion gegen das vorher eingefrorene Manifest
geprüft. Roh-SVGs und Logs sind lokale, nicht versionierte Messprodukte.

```powershell
.venv/Scripts/python.exe -m tools.evaluate_adaptive_form_models --label recheck
.venv/Scripts/python.exe -m pytest -q tests/test_form_model_comparison.py tests/test_disk_arrow_runtime.py tests/test_right_disk_arrow_runtime.py
```

Ein neuer `--label` verhindert das Überschreiben früherer Belege. `--freeze`
legt für eine neue Studie ein neues Manifest an; es darf die vorhandene
Baseline nicht ersetzen. Ein erneuter Lauf mit `--label baseline` verlangt
bytegleiche Baselinequellen.

60 gezielte Tests bestanden. Sie umfassen einen real gerenderten unabhängigen
Dreistoppfall mit späterem Gewinner, eine geometrisch falsche pixelgenaue
Gegenprobe, gemeinsame Rendergrenzen und eine bereits abgelaufene Deadline
sowie die 52 bisherigen Links-/Rechtspfeilregressionen.

Weitere 140 Kreis-, Scheduler-, Portfolio-, Adaptive-Suche- und Sprachregressionen
bestanden. Zusammen sind das 200 bestandene Tests der gezielten AP-1-Prüfung.

Die breitere Suche-/Sprachprüfung hatte 118 bestandene und fünf fehlgeschlagene
Tests. Dieselben fünf `test_search_minimum_effort.py`-Fehler wurden mit dem
unveränderten Registrierer aus `HEAD` reproduziert (dort sieben weitere Pässe).
Sie betreffen frühere Mindestzeitannahmen und sind keine neue Regression.

Die Quellhashes im Abschlussbericht bezeichnen den gemessenen AP-1-Stand.
Während der Abschlussprüfung wurden `imageCompositeConverterFormModels.py` und
`imageCompositeConverterFilledSymbols.py` parallel um fortsetzbare Registrierungen
und adaptive Budgetsteuerung erweitert. Diese späteren Änderungen sind nicht
Bestandteil der hier berichteten AP-1-Test- und Laufzeitabnahme und wurden beim
Abschluss nicht zurückgesetzt. Eine AP-2-Abnahme muss eigene Belege verwenden.

Ein echter überwachter CLI-Lauf für GE0037_S bestand unter zehn Sekunden
Bildbudget und 384 Renderings maximal: 322 Renderings, 4,579 Sekunden
Prozessbericht, RGB-RMSE je Kanal 8,077. Native Richtung und Elementliste
werden weiter geprüft; die Vorschau wurde zusätzlich gesichtet. Ausgabe:
`.tmp/adaptive-form-cli/converted_svgs/GE0037_S.svg`.

Nächstes Paket: AP 2, qualitative und fortschrittsabhängige Budgetverteilung.
Die Erweiterung auf weitere Formfamilien und die unabhängige Katalogabnahme
aus AP 4 bleiben offen. Katalog-SVGs wurden durch diese Arbeit nicht ersetzt.
