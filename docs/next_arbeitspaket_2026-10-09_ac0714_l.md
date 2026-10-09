# Arbeitspaket – Quadrat mit rechtem Griff, Strich und Punkt (2026-10-09)

Branch: `codex/ac0714-quality-2026-10-09`, Basis `5726e87b8`.
Das nächste dokumentierte Ziel `AC0714_L` und alle fünf Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Qualitätsgates ohne Pflichtmetrikregression.
Alle sechs bestehen zusätzlich die strengeren Plan-B-Pixelgrenzen.
Die Ergebnis-SVGs sind unter `artifacts/evaluation/marked_square_recheck_v1/converted_svgs/`
gespeichert; `comparison_2026-10-09.png` zeigt Raster und frische Ausgabe.

## Ursache und allgemeine Korrektur

Die bisherige Beschreibung verwies auf einen anderen Katalogeintrag und eine
relative Drehung; die Innenmarkierungen waren unbeschrieben. Die vorhandene
Quadrat-/Griff-Erkennung verlangt eine gleichmäßige Füllfläche und verwirft
solche kontrastreichen Befunde. Der nachfolgende Ersatzpfad verlor die
Innenmarkierung; bei den grauen Rastern wählte er zusätzlich eine falsche Füllung.

Beide XML-Kataloge beschreiben jetzt eigenständig das Quadrat links, den mittig
rechts anschließenden waagerechten Griff, einen nach rechts ansteigenden schrägen
Strich und einen kleinen quadratischen Punkt links neben dessen unterem Ende.
Die Beschreibung enthält keine numerischen Formparameter.

Die bestehende `imageCompositeConverterSquareStem.py` registriert diese zwei
Innenbefunde zusätzlich, sobald die Beschreibung sie nennt. Kontrast gegenüber
der Medianfüllung liefert zwei Komponenten; die größere muss einen schlanken,
schrägen Verlauf zeigen, die kleinere ein benachbartes quadratisches Profil.
Lage, Abmessungen, Neigung und gemeinsame Farbe stammen aus diesem Raster.
Beide Kontrastpolaritäten sind möglich. Fehlende oder zusätzliche Komponenten,
eine unpassende Topologie oder eine ausdrücklich ausgeschlossene Markierung
werden verworfen. Der unmarkierte Pfad behält sein bisheriges Suchbudget.

Eine begrenzte Grob-zu-fein-Suche registriert Körper, Griff und Markierungen
gemeinsam. Für diese kleinen antialiasierten Konturen minimiert sie den
quadratischen Farbfehler; der absolute Fehler der aufrufenden Runtime bleibt
die abschließende Annahmeprüfung. Maximal 1.441 Renderproben plus die
Ausgangsmessung sind möglich, mit frühem Ende unveränderter Suchrunden.
Die zusätzliche gemeinsame Feinregistrierung vermeidet einen zu breiten
linken Rand im kleinsten roten Raster. Gespeichert werden vier native
Vektorelemente mit insgesamt zwölf Pfadbefehlen. Es gibt keine OCR-Annahme,
geladenen Schriftkonturen oder bildspezifischen Runtime-Parameter.

## Frische CLI-Abnahme

Vor der Runtime-Änderung wurden sechs echte CLI-Ausgaben mit Originalbeschreibung
und neutralen Dateinamen eingefroren. Der vorhandene Quadrat-Recheck-Runner
kann den damaligen Fitter aus der vollständigen Basis-Commit-ID reproduzieren;
die Runtime-Konvertierung selbst erhält weiterhin ausschließlich Raster und
Beschreibung. Vorher und nachher verwenden Seed 0, `semantic-only`, getrennte
frische Eingabekopien und denselben abschließenden Renderer.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| AC0714_1_L | 7636.669434 | 107.850670 |
| AC0714_1_M | 5074.134277 | 42.948570 |
| AC0714_1_S | 2155.690674 | 88.965332 |
| AC0714_L | 33066.082031 | 24.314667 |
| AC0714_M | 31093.931641 | 23.459999 |
| AC0714_S | 29215.839844 | 21.704000 |

**6/6 bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression.** Die Erweiterung der Semantikprüfung verlangt die
beiden vollständig im Körper liegenden Innenprimitive einschließlich ihrer
Lagebeziehung. Dieselbe Prüfung wird vor und nach der Änderung angewendet.
Numerische Toleranzen berücksichtigen die drei Nachkommastellen der nativen
SVG-Serialisierung. Pixel-, Kanten-, Masken- und Komplexitätsgrenzen bleiben
unverändert. Die separat strengere Plan-B-Pixelprüfung besteht ebenfalls 6/6.

Zwei unabhängige CLI-Läufe reproduzieren sämtliche zwölf Vorher-/Nachher-SVGs
und Gateentscheidungen. Ihre Vorher-SVGs stimmen außerdem bytegenau mit dem
originalen, vor der Änderung eingefrorenen CLI-Lauf überein. Alle Läufe haben
null verbotene Referenz-SVG-Zugriffe. Die historischen Sammelausgaben bleiben
als Vergleich erhalten. Die tatsächlich geprüften neuen SVGs sind Ergebnisse
der Abnahme und dienen nicht als Runtime-Eingabe.

## Perception-Lerneffekt und Grenzen

Der Lerneffekt ist für die beschriebene Quadrat-/Griff-/Strich-/Punkt-Topologie
`generalisiert`. Unabhängige synthetische Vektoren variieren Lage, Farbe,
Kontrastpolarität und Auflösung. Umbenennung, fehlende/zusätzliche Befunde,
Beschreibungseinschränkungen, nicht endliche Fehler und der Vorrang vor
Sample- beziehungsweise Panel-Ersatzpfaden sind geprüft. Ein perfektes
synthetisches SVG kalibriert die Qualitätsmessung.

Andere Innenzeichen, beliebige Buchstaben, weitere Griffausrichtungen und
Verlaufsfüllungen gehören zu späteren Aufgaben. Für diese Familie existiert
keine SVG-Vorlage im Sample-Pool; ein 16-Varianten-Vorlagen-Roundtrip wird daher
nicht behauptet. `PB-POOL-2026-10-07` bleibt offen. Die CLI-Restfehlerwarnungen
über örtlich konzentrierte Differenzen bleiben sichtbar; ein Gate-Pass ist
keine pixelidentische Rekonstruktion.

## Reproduktion und Abschluss

Versioniert sind Manifest, sechs Ergebnis-SVGs, Vergleichsbild und kompakter
JSON-Nachweis unter `artifacts/evaluation/marked_square_recheck_v1/`.
Vollständige Eingabekopien, SVGs, Logs und Reviewtabellen liegen lokal unter
`.tmp/ac0714/`. Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0,
PyMuPDF 1.26.7; direktes Rendering ist ausdrücklich gewählt.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_right_stem_square_recheck artifacts/evaluation/marked_square_recheck_v1/manifest.json --output-dir .tmp/marked-square-reproduction
.venv/Scripts/python.exe -m tools.evaluate_right_stem_square_recheck .tmp/marked-square-reproduction/manifest.json --output .tmp/marked-square-gates.json
.venv/Scripts/python.exe -m pytest -q tests/test_marked_square_runtime.py tests/test_right_stem_square_runtime.py tests/test_diagonal_square_kelle_runtime.py tests/test_rotated_square_kelle_runtime.py
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q -ra
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Die fokussierte Abnahme besteht mit **63 Tests**, davon 19 neue Tests.
Syntaxprüfung, CLI-Hilfe und Runtime-ID-Nullprüfung (`0 occurrences`) bestehen.
Die vollständige Suite einschließlich der drei Heavy-Module besteht mit
**2.324 bestandenen Tests, 0 Fehlern und 29 bestehenden Windows-Skips**,
insgesamt 2.353 Tests und Exit 0. Die Bestandsschutzbatterie konvertiert 31
bereits akzeptierte Varianten im dokumentierten `standard`-Kompatibilitätsmodus
neu und meldet null Qualitätsregressionen. Der frische Zwei-Quellen-Nachweis
für das aktuelle Paket läuft separat in `semantic-only`. Testprotokolle und
JUnit-Hashes stehen im kompakten JSON-Nachweis.

Der bestehende Template-Transfer-Test protokolliert die bereits im vorherigen
Quadratpaket dokumentierte native Windows-Diagnose `0xc0000008`. Er besteht
im Gesamtprofil und im separaten Kontrolllauf mit Exit 0; die Diagnose wird
hier nicht als behoben bezeichnet. Kontrollprotokoll und Testname sind im
Nachweis erfasst.

Der erneuerte Review enthält 1.000 Einträge, davon 993 renderbare Paare.
Alle 48 gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze;
104 historische renderbare Einträge überschreiten sie. Die sechs frisch
belegten Pässe sind aus der Kandidatenauswahl ausgeschlossen. Der genaue
Review-Aufruf steht unter `review.reproduction_arguments` im JSON-Nachweis.
Die nächste reguläre Aufgabe ist **`GE0032`**, gefolgt von `GE9023_6M`,
`AC0413_1_M`, `AC0713_1_L` und `AC0721_1_S`.
