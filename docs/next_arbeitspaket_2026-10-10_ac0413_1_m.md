# Arbeitspaket – Kreis mit schrägen Linien und T (2026-10-10)

Basis: `b87b5c73d7db643fc9f632badf518f0fbb675d3f`.
Das nächste dokumentierte Ziel `AC0413_1_M` und acht Farb-/Größenvarianten
bestehen beide unveränderten regulären Qualitätsgates ohne Pflichtmetrikregression.
Manifest, eingefrorene Vorher-SVGs, geprüfte Nachher-SVGs, unabhängiges
synthetisches SVG, Vergleichsbild und JSON-Nachweis stehen unter
`artifacts/evaluation/circle_linework_recheck_v1/`.

## Beschreibung und allgemeine Erkennung

Die neun Raster zeigen einen gefüllten Kreis mit Kontur, zwei schrägen
Kreissehnen und ein T aus einem oberen Querstrich und einem mittigen Strich
nach unten. Die Platzhalterbeschreibungen in beiden XML-Katalogen wurden durch
eine eigenständige Beschreibung dieser Struktur ersetzt. Sie enthalten keine
Bildverweise oder numerischen Geometrieparameter.

Der vorhandene Beschreibungsparser klassifizierte selbst die zutreffende
Linienbeschreibung zunächst als Buchstaben-Badge und setzte ein `M` ein.
Explizit zerlegte Kreis-/Linienbeschreibungen umgehen nun diese Heuristik und
erreichen die normale Rasterregistrierung. Die neue Registrierung in
`imageCompositeConverterCircleLinework.py` ermittelt Kreisposition und Radius
durch Kreisregression, Füll- und Linienfarben durch Rasterkontrast, den oberen
Querstrich durch ein Zeilenprofil und den senkrechten Strich durch mittige
Pixelevidenz. Gewichtete Geradenregressionen bestimmen beide schrägen Linien;
ihre Schnittpunkte mit dem beobachteten Kreis liefern die Endpunkte.

Eine begrenzte Render-/Pixelsuche verfeinert Geometrie, Strichbreiten und Farben
mit höchstens `1 + 16 × 27 = 433` Renderproben. Die Ausgabe enthält einen
nativen Kreis, vier native Linien und den weißen Hintergrund. Rasterkonturen
oder externe Vektoren werden nicht exportiert. Fehlende Linien, zusätzliche
Objekte, falsche Richtung, gefüllte Dreiecke und elliptische Körper werden
verworfen; fehlendes Rendering oder nicht endliche Messwerte führen zu keiner
Annahme.

Eine zusätzliche Zufallsprüfung deckte einen Fehler der Annahme auf: Ein dünner
Strich mittig auf einem Pixel belegte einen kleineren Anteil eines festen
Prüfbandes als derselbe Strich zwischen Pixelmitten. Die Prüfung verlangt jetzt
Rasterunterstützung entlang der analytischen Linie. Alle vier Linien müssen
belegt sein, und die gesamte Innenzeichnung muss durch sie erklärt werden.
Die externen Qualitätsgates bleiben unverändert.

## Frische CLI-Abnahme

Vor der Runtime-Integration wurden neun echte CLI-Ausgaben mit ihren jeweiligen
Originalbeschreibungen unter neutralen Namen eingefroren. Der Reproduktionsrunner
schaltet ausschließlich im Vorher-Lauf die neue Registrierung ab und verwendet
weiterhin die Originalbeschreibung. Die reproduzierten Vorher-SVGs bleiben
bytegleich zum eingefrorenen Vorlauf.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| AC0413_1_L | 7982.025391 | 155.960632 |
| AC0413_1_M | 9107.812500 | 257.785553 |
| AC0413_1_S | 6306.492676 | 207.660004 |
| AC0413_2_L | 6411.799316 | 73.167503 |
| AC0413_2_M | 6587.735352 | 82.720001 |
| AC0413_2_S | 4907.777344 | 152.804993 |
| AC0413_L | 2291.767578 | 103.128754 |
| AC0413_M | 2037.666626 | 165.639999 |
| AC0413_S | 2433.554932 | 106.672501 |

**9/9 bestehen Good-Solution- und Quality-Complexity-Gate ohne
Pflichtmetrikregression.** Der historische Kandidatenwert `13465.694336` ist
vom frischen Vorlauf `9107.812500` getrennt. Die unabhängige Semantikprüfung
verlangt Kreis, zwei nach unten innen gerichtete Sehnen und ein innen liegendes,
zusammenhängendes T. Vorher und nachher verwenden denselben Messvertrag.

Drei unabhängige vollständige CLI-Abnahmen reproduzieren sämtliche 18
Vorher-/Nachher-SVG-Bytes; die letzte umfasst die korrigierte Linienannahme.
Alle melden null verbotene Referenz-SVG-Zugriffe. Die neun gelieferten
Katalogausgaben stimmen nach ausschließlicher Normalisierung der Zeilenenden
mit den tatsächlich geprüften Nachher-SVGs überein; ihre Renderwerte sind identisch.
Ein zusätzlicher normaler Ordnerlauf mit den echten neun Katalognamen und der
vollständigen XML-Tabelle reproduziert dieselben neun SVG-Bytes wie die
anonyme CLI-Abnahme. Auch er meldet null Referenz-SVG-Zugriffe.

## Perception-Lerneffekt, Zufallsprüfung und Grenzen

Die beschriebene Kreis-/Linientopologie ist für die geprüften Fälle
`generalisiert`. Sechs unabhängige synthetische Fälle variieren Lage,
Auflösung, Farben, Kreisradius und Linienwinkel, einschließlich Viertel- und
Halbpixelverschiebungen. Neutrale Namen ergeben identische SVGs und Raster.
Ein perfektes synthetisches SVG kalibriert beide regulären Gates.

Das unabhängige `synthetic_holdout.svg` besteht als echte CLI-Aufgabe mit den
Seeds `20261010` und `20261011` jeweils **17/17** strenge Plan-B-Prüfungen
(Original plus 16 Parametervarianten). Der erste Entwicklungslauf erreichte
12/17; dessen fünf Annahmefehler werden durch die längsgerichtete
Linienevidenz behoben. Die beiden finalen Berichte sind im kompakten
JSON-Nachweis über Seeds, Fälle, Metriken und Hashes belegt.

Die zusätzliche strengere JPG-Prüfung besteht für alle sechs farbigen Raster.
Die drei grauen Raster verfehlen weiterhin die Vordergrund-IoU-Grenze;
dieser getrennte Nachweis bleibt als `AC0413-PB-GREY` offen. Ein regulärer
Gate-Pass bedeutet keine pixelidentische JPEG-Rekonstruktion. Andere
Innenzeichen, beliebige neue Liniengraphen und der Gesamtpool
`PB-POOL-2026-10-07` bleiben außerhalb dieser Abnahme. Der ältere
`GE9023-PB-STRESS` bleibt ebenfalls offen.

## Reproduktion und Tests

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_circle_linework_recheck artifacts/evaluation/circle_linework_recheck_v1/manifest.json --output-dir .tmp/circle-linework-reproduction
.venv/Scripts/python.exe -m tools.evaluate_circle_linework_recheck .tmp/circle-linework-reproduction/manifest.json --output .tmp/circle-linework-gates.json
.venv/Scripts/python.exe -m pytest -q tests/test_circle_linework_runtime.py
.venv/Scripts/python.exe -m pytest -q -ra --basetemp .tmp/circle-linework-full
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_satisfactory_regression_battery.py --basetemp .tmp/circle-linework-preservation
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
35 finale fokussierte Tests und der finale verwandte Nachlauf mit 149 Tests
bestehen. Die sechs Bestandsschutztests bestehen und konvertieren 31
gespeicherte gute Varianten im dokumentierten `standard`-Kompatibilitätsmodus
mit null Regressionen. Die eigene Paketabnahme läuft separat in `semantic-only`.
Syntaxprüfung, CLI-Hilfe, Diff-Prüfung und Runtime-ID-Nullprüfung bestehen.
Der Standard-Gesamttestlauf besteht mit **2.050 Tests, 0 Fehlern und 29
bestehenden Windows-Skips** in 1.000,02 Sekunden, Exit 0. Er wurde vor der
Korrektur der längsgerichteten Linienannahme gestartet; die finale Fassung
ist durch den anschließenden Nachlauf mit 149 Tests, die letzte vollständige
CLI-Abnahme, den echten Katalognamen-Batch und beide finalen Zufallsseeds
geprüft. Die drei Heavy-Module gehören nicht zum Standardprofil; die
Bestandsschutzbatterie wurde gesondert vollständig ausgeführt.

Der erneuerte Review enthält 1.000 Einträge, davon 993 renderbare Paare.
Alle 48 bisherigen Erfolgsvarianten bleiben unter der Reviewgrenze. Die neun
frisch geprüften Fälle sind aus der Kandidatenauswahl ausgeschlossen. Die
nächste reguläre Aufgabe ist **`AC0713_1_L`**, gefolgt von `AC0721_1_S`,
`AC0711_1_M`, `GE9014_1M` und `GE9012_1M`. Der vollständige Review-Aufruf
steht in `review_arguments.json` und im JSON-Nachweis. Vollständige Logs,
JUnit-Dateien und Zufallsprüfungen liegen lokal unter `.tmp/ac0413/`.
