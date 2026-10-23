# Arbeitspaket – Gefülltes Abwärts-Dreieck im Kreis (2026-10-09)

Branch: `codex/ac0403-quality-2026-10-09`, Basis `2f9bd54cc`.
Das nächste dokumentierte Ziel `AC0403_1_L` und alle 18 roten, grünen und
grauen Größen-/SIA-Varianten bestehen beide unveränderten regulären Gates.
Die frische CLI-Baseline besteht bereits vor der Beschreibungskorrektur.
Dieses Paket verbessert daher keine Runtime-Algorithmen.

## Altbestand und frische Baseline

Das historische Ziel-SVG zeigt nur einen Kreis; das Dreieck fehlt. Sein
erneut gemessener `mean_delta2` beträgt `13989.019531`, der semantische Score
ist `0`. Das frische SVG besteht aus Ellipse und Dreieckspolygon und erreicht
`mean_delta2=93.733124`, `edge_alignment=0.948990`,
`object_mask_iou=0.979070`, `semantic_score=1` und korrekte Dimensionen.
Die frischen 18 Varianten liegen bei `mean_delta2=93.733124..415.928894`.

Der aktuelle Gesamt-Review enthält 1.000 Einträge, davon 993 renderbare Paare.
104 renderbare Einträge überschreiten die Reviewgrenze
`normalized_mse=0.045945679`. Alle 48 gespeicherten Erfolgsvarianten bestehen
weiterhin. Diese Bestandsmessung stützt die Beobachtung, dass viele alte
Sammelausgaben schlecht sind; sie ist kein Nachweis, dass der heutige Konverter
bei allen diesen Fällen noch dieselben schlechten Resultate erzeugt.

## Eigenständige Beschreibung und Zwei-Quellen-Nachweis

Beide XML-Kataloge beschreiben jetzt eigenständig den gefüllten Kreis mit
Randkontur, das kontrastierende gefüllte Dreieck und die absolute Richtung
nach unten. Der bisherige Katalogverweis mit relativer 180°-Drehung entfällt.
Geometrie und Farben werden weiterhin aus dem jeweiligen Raster ermittelt.

Die originale Beschreibung wurde vor der Änderung in einem separaten
CLI-Lauf vermessen. Zwei weitere unabhängige CLI-Läufe vergleichen die
Originalbeschreibung mit der präzisierten Beschreibung. Alle 108 erzeugten
Vorher-/Nachher-SVGs sind je Fall bytegleich; die beiden Abnahmeläufe liefern
identische Gate-Records. Es gibt keine Pflichtmetrikregression.
Die Beschreibungskorrektur ist eine Datenpräzisierung, keine behauptete
Qualitätsverbesserung gegenüber der frischen Baseline.

Die Runtime erhält neutrale Dateinamen, ausschließlich Raster und
Beschreibung, Seed 0 und `semantic-only`. Die Zugriffssperre meldet in allen
Läufen null verbotene SVG-Zugriffe. Die Runtime-Quellen sind bytegleich zu
`HEAD`; ihre SHA-256-Hashes stehen im Nachweis.

## Ergebnisse und Grenzen

Die tatsächlich erzeugten 18 SVGs sind unter
`artifacts/evaluation/down_pump_recheck_v1/converted_svgs/` gespeichert.
Ihre Hashes stimmen mit den geprüften CLI-Ergebnissen überein. Das Vergleichsbild
`comparison_2026-10-09.png` zeigt Rasterquelle, historische Sammelausgabe und
frische Konvertierung. Die historische Sammelausgabe bleibt als Vergleichsbasis
erhalten; die neuen Ergebnis-SVGs sind Abnahmeausgaben und keine Runtime-Inputs.

Die separate strengere Plan-B-Pixelprüfung besteht bei 11/18 JPG-Varianten.
`AC0403_1_L`, `AC0403_1_M`, `AC0403_2_L`, `AC0403_L`, `AC0403_L_sia`,
`AC0403_M` und `AC0403_S_sia` verfehlen deren Vordergrund-IoU-Grenze.
Die regulären Gates verwenden einen anderen dokumentierten Maskenvertrag.
Grenzen und Bewertungsfunktionen wurden nicht geändert; ein vollständiger
strenger Plan-B-Pass wird nicht behauptet. `PB-POOL-2026-10-07` bleibt offen.
Im Sample-Pool existiert keine `AC0403`-SVG-Vorlage; ein Vorlagen-Roundtrip
wird daher ebenfalls nicht behauptet. Die bestehenden synthetischen
Pumpentests prüfen zusätzliche Farben, Auflösungen und vier Richtungen.

## Reproduktion und Prüfung

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_pump_recheck artifacts/evaluation/down_pump_recheck_v1/manifest.json --output-dir .tmp/down-pump-reproduction
.venv/Scripts/python.exe -m tools.evaluate_pump_recheck .tmp/down-pump-reproduction/manifest.json --output .tmp/down-pump-gates.json
$env:TEMP = "$PWD/.tmp/down-pump-test-temp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
.venv/Scripts/python.exe -m pytest -q -ra --basetemp=.tmp/down-pump-pytest
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
Direktes Rendering ist explizit gewählt. Lokale vollständige Protokolle,
Baseline und Wiederholung liegen unter `.tmp/ac0403-20261009/`.
Der versionierte JSON-Nachweis enthält die Abnahme, Originalbaseline- und
Wiederholungshashes, den separaten strengen Gatebefund und den frischen Review.

20 neue Prüfungen sichern die 18 anonymen Rasterfälle und beide XML-Kataloge;
zusammen mit den vorhandenen Pumpenprüfungen bestehen 95 fokussierte Tests.
Die vollständige reguläre Suite besteht mit **1.896 Tests, 0 Fehlern und
29 bestehenden Windows-Skips**, insgesamt 1.925 Tests in 676,74 Sekunden,
Exit 0. Die Skips betreffen POSIX-Shelltests unter Windows.
Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung (0 Vorkommen) und
Whitespaceprüfung unter Erhalt der vorhandenen CRLF-Dateien bestehen.
Testzahlen und JUnit-/Loghashes stehen in `summary_2026-10-09.json`.
Heavy-Konvertierungsmodule sind in diesem Paket ohne Runtime-Änderung nicht
aktiviert.

Die frische Rotation beginnt mit `AC0714_L`, gefolgt von `GE0032`,
`GE9023_6M`, `AC0413_1_M` und `AC0713_1_L`. Die Änderung der Reihenfolge
folgt dem seit dem letzten Paket erweiterten Diff-Inventar. Vor dem nächsten
Paket ist wieder eine frische CLI-Baseline erforderlich.
