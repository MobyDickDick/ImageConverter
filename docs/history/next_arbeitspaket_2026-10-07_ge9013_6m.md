# Arbeitspaket – GE9013_6M Verlaufspfeil nach unten (2026-10-07)

Umgesetzt auf `codex/ge9013-quality-2026-10-07`, ausgehend von
`073d8eea2`. Die deterministische Pfeilabnahme besteht; der gekoppelte
randomisierte Plan-B-Lauf bleibt ausdrücklich rot.

## Ursache und allgemeine Korrektur

Die gemeinsame XML beschrieb die 14 Farb-/Größenvarianten als hellgraues
Quadrat. Die Bilder zeigen einen vertikalen Verlaufsschaft und darunter eine
gefüllte Dreieckspitze mit weißem Abstand. Die eigenständige Beschreibung
benennt diese Topologie ohne Katalogreferenzen, Maße oder feste Farben.

Die vorhandene rastergestützte Pfeilregistrierung unterstützt jetzt auch
eine ausdrücklich nach unten gerichtete Spitze. Das Raster wird für die
Geometriesuche vertikal normalisiert; jedes Probe-SVG wird vor dem Rendern
in die beschriebene Richtung zurückgeführt. Der Fehler wird somit gegen das
tatsächlich gerenderte Ergebnis gemessen. Die Ausgabe enthält native
Polygon-/Rechteckprimitive und einen horizontalen Linearverlauf. Die
Koordinaten und protokollierten Parameter stehen im Originalbildraum;
SVG-Transformationen und eingebettete Raster sind unnötig.

Lage, Kontur und Farben stammen aus dem Raster. Die begrenzte deterministische
Suche übernimmt nur endliche Verbesserungen und erhält Dreieck, schmaleren
Schaft und Abstand. Widersprüchliche Richtungsangaben, fehlende Teile, Löcher,
flache Schaftfarben, zusätzliche Kreise und Text werden verworfen. Gedrehte
Pfeile nach links/rechts, gekrümmte Schäfte und beliebige Hintergründe bleiben
außerhalb dieser Abnahme.

## Harte Abnahme und Perception-Lerneffekt: generalisiert

14 anonym benannte Bilder laufen mit Seed 0 und `semantic-only` durch die
echte CLI. Der kontrollierte Vorlauf verwendet die ursprüngliche Beschreibung
und deaktiviert die Pfeilregistrierung; der Nachlauf verwendet die neue
Beschreibung und Rasterregistrierung. Bewertet wird jeweils das gespeicherte,
erneut gerenderte SVG mit unveränderten Gates.

| Variante | mean_delta2 vorher | mean_delta2 nachher |
|---|---:|---:|
| GE9013_1M | 12989.524414 | 486.205841 |
| GE9013_1S | 10389.526367 | 379.209991 |
| GE9013_2M | 12618.219727 | 457.530823 |
| GE9013_2S | 8247.813477 | 317.940002 |
| GE9013_3M | 7984.934082 | 279.169159 |
| GE9013_3S | 4896.350098 | 224.220001 |
| GE9013_4M | 2803.008301 | 127.795830 |
| GE9013_4S | 2378.906738 | 87.919998 |
| GE9013_5M | 8144.414062 | 306.337494 |
| GE9013_5S | 6167.503418 | 286.000000 |
| GE9013_6M | 15279.816406 | 488.706665 |
| GE9013_6S | 10754.243164 | 466.203339 |
| GE9013_7M | 12574.087891 | 228.477493 |
| GE9013_7S | 11125.736328 | 196.473328 |

Alle Fälle bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression. Zwei unabhängige Läufe erzeugen exakt dieselben 28
SVGs und Gateentscheidungen. Zusätzliche synthetische Tests prüfen andere
Farben, verschobene Lage, doppelte Größe, Umbenennungsinvarianz sowie den
Verzicht auf Sample-Zugriff. Die bestehenden CLI-Restfehlerwarnungen bleiben
sichtbar. Ein perfektes gespeichertes PNG/SVG-Paar kalibriert alle Metriken
auf ihre Idealwerte; falsche Richtung, Überlappung, Verlaufsachse, flache Farbe,
Transformation und Raster-Embedding scheitern am Semantikcheck.

## Gekoppelte randomisierte Plan-B-Aufgabe

Der Standardstart zieht `AC0538_1L_sia.svg` aus dem gesamten beschriebenen
Pool mit Seed `3948009396310964094`. Es wurde kein leichterer Fall nachgezogen.
Die 16 Fälle haben ausschließlich anonym benanntes Raster und Beschreibung
als CLI-Eingabe; der SVG-Zugriffsschutz bleibt aktiv.

Der erste Lauf scheitert technisch an einer inkompatiblen NumPy-Version aus
der historischen Windows-Virtualenv. Der Runner startet seinen Worker jetzt
isoliert und lädt vor der Runtime die bereits im Elternprozess verwendeten
Bibliotheken. Das behebt den ABI-Konflikt, ohne Auswahl, Qualitätsgrenzen,
Iterationsbudget oder Zugriffsschutz zu ändern. Ein echter Unterprozesstest
prüft den Start trotz absichtlich kaputtem `PYTHONPATH`.

Die Wiederholung derselben Auswahl und desselben Seeds beendet alle 16
Konvertierungen mit Exit 0 und ohne verbotenen SVG-Zugriff. **0/16 bestehen
die Qualitätsgrenzen**: normalisierter Fehler, Vordergrundfehler,
Konturübereinstimmung und Vordergrund-IoU schlagen fehl. Die Quellbeschreibung
bezeichnet das Motiv lediglich als unklassifizierte Wurzelform. Die Referenz
zeigt Kreis, Verbindung, gerahmtes Diagramm und helle Stufenkurve; die erzeugte
Geometrie rekonstruiert diese Struktur nicht ausreichend.

**Offen: PB-RANDOM-2026-10-07.** Zuerst eine zutreffende eigenständige
Beschreibung und katalogfreie Geometrie-/Relationsrekonstruktion für diese
Topologie erarbeiten, dann denselben eingefrorenen Lauf erneut prüfen. Dieser
Befund ist kein Pass und wird durch die grüne Pfeilabnahme nicht verdeckt.

Der kompakte versionierte Beleg steht in
`artifacts/evaluation/downward_gradient_arrow_recheck_v1/summary_2026-10-07.json`
unter `random_plan_b`.
Die vollständigen generierten Läufe bleiben gemäß `.gitignore` lokal unter
`artifacts/evaluation/plan_b_variations/ge9013-package-2026-10-07[-replay]/`.

## Reproduktion

```powershell
python -m tools.run_downward_gradient_arrow_recheck artifacts/evaluation/downward_gradient_arrow_recheck_v1/manifest.json --output-dir .tmp/downward-arrow-reproduction
python -m tools.evaluate_downward_gradient_arrow_recheck .tmp/downward-arrow-reproduction/manifest.json --output .tmp/downward-arrow-gates.json
python -c "import json; from pathlib import Path; d=json.loads(Path('artifacts/evaluation/downward_gradient_arrow_recheck_v1/summary_2026-10-07.json').read_text(encoding='utf-8')); Path('.tmp/random-description.txt').write_text(d['random_plan_b']['source_description'], encoding='utf-8')"
python -m tools.run_plan_b_variations --svg artifacts/images_to_convert/samples/AC0538_1L_sia.svg --description-file .tmp/random-description.txt --seed 3948009396310964094 --output-dir .tmp/random-plan-b-reproduction
python -m pytest -q tests/test_downward_gradient_arrow_runtime.py tests/test_gradient_arrow_runtime.py tests/detailtests/test_plan_b_variations.py
python -m compileall -q src tests tools
python -m pytest -q
python -m src.imageCompositeConverter --help
python -m tools.check_no_new_image_id_hardcoding
```

Die lokale Toolchain ist CPython 3.12.14, NumPy 2.5.3, OpenCV 4.14.0 und
PyMuPDF 1.26.7. Ein temporärer Bootstrap lädt diese Bibliotheken vor der alten
Virtualenv. Versioniert werden nur `manifest.json` und
`summary_2026-10-07.json` unter
`artifacts/evaluation/downward_gradient_arrow_recheck_v1/`. Das Manifest enthält
Eingaben und Quellhashes; die Zusammenfassung bewahrt Metriken, Gateentscheidungen,
SVG-/Eingabehashes, Testsignale, Zufallsbefund und den vollständigen Review-Aufruf.
Die 28 CLI-SVGs, Logs, versiegelte Baseline und vollständigen Review-Tabellen
bleiben lokal und sind von Git ausgeschlossen. Der erste Reprobefehl erzeugt
die SVGs, Baseline und vollständigen Gates in einem frischen Verzeichnis;
die folgenden Befehle benötigen keine unversionierten Originalausgaben.
Vor dem Zufalls-Replay sind die Quellhashes mit der Zusammenfassung abzugleichen.

Der verkleinerte Commit umfasst 14 Dateien. 45 generierte Belegdateien bleiben
lokal erhalten. Ein erneuter CLI-Lauf aus dem versionierten Manifest bestätigt
alle 28 SVG-Hashes, Metriken und Gateentscheidungen gegenüber der Zusammenfassung.

## Testabschluss

90 fokussierte Tests und vier Unterprozess-Umgebungstests sind grün. Das
vollständige Defaultprofil meldet `1681 passed, 29 skipped`
ohne Warnungen; die bestehenden Windows-Skips betreffen POSIX-Shell-Integration.
Syntaxprüfung, CLI-Help und Runtime-ID-Nullprüfung sind grün (`0 occurrences`).
Die genaue Toolchain und Testsignale stehen unter `completion` in
`summary_2026-10-07.json`.

Der erste Gesamtlauf hatte drei Fehler: Der neue echte Worker-Test erbte den
Pytest-Marker und aktivierte damit die separate Renderer-Probe pro Versuch;
zwei bestehende Importtests verwendeten einen POSIX-Doppelpunkt im
Windows-`PYTHONPATH`. Der Worker-Test prüft jetzt den Produktionsstart ohne
diesen Marker. Ein getrennt erhaltener Bootstrap-Pfadeintrag behebt die
lokale Importumgebung. Der erneute vollständige Lauf besteht.

Getestet: Pfeilabnahme, Zufallsauswahl, Fokus-/Gesamttests und Abschlusschecks.

Ergebnis: 14/14 Pfeil-Pässe, 1681 Tests grün.

Blocker: Zufällige Diagramm-/Stufenkurvenaufgabe weiterhin 0/16.

Nächster Schritt: `PB-RANDOM-2026-10-07` oder reguläre frische Kandidatenbaseline.

Startbefehl: Wiederholungsbefehl für Seed `3948009396310964094` aus diesem Dokument.

## Rotation

Der erneuerte Review enthält 956 Einträge, davon 950 renderbare Paare; sechs
fehlende Paare bleiben sichtbar. Alle zuvor separat belegten Pässe und die
14 aktuellen Pfeilvarianten sind aus der Kandidatenauswahl ausgeschlossen.
Der reproduzierbare Aufruf steht unter `review.reproduction_arguments` in
`summary_2026-10-07.json`; die vollständigen Review-Ausgaben bleiben lokal.
Die nächste reguläre Rotation beginnt mit `AC0554_1_L`, gefolgt von `DLG0031`,
`DLG0021`, `GE1420_S` und `AC0704_1_L`. Vor weiteren Änderungen ist eine frische
CLI-Baseline zu prüfen. Die randomisierte Folgeaufgabe bleibt unabhängig offen.
