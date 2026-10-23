# Arbeitspaket – Quadrat mit unterem Griff und T (2026-10-10)

Branch: `codex/ac0721-quality-2026-10-10`.
Das nächste dokumentierte Ziel `AC0721_1_S` und seine fünf Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Qualitätsgates ohne Pflichtmetrikregression.

## Beschreibung und allgemeine Registrierung

Beide XML-Kataloge beschreiben jetzt eigenständig das gefüllte Quadrat mit
Kontur, den mittigen unteren Griff und den kontrastierenden Text `T`. Die alte
Beschreibung verwies auf andere Motive und verschwieg den Buchstaben. Der
vorhandene Parser erhält den ausdrücklich beschriebenen Text; im SVG bleiben
Rechteck, Griffpfad und Text native Vektorelemente.

Die bestehende allgemeine Quadrat-/Griff-/Textregistrierung ermittelt Lage,
Abmessungen, Farben und Strichbreiten aus dem Raster. Bei hellen Konturen kann
die äußere Pixelzeile überwiegend Füllfarbe oder weiße Kantenglättung enthalten.
Nur wenn ihr Median keinen ausreichenden Kontrast zum Körper liefert, wird
der beobachtete dunklere Konturkern verwendet. Bei schlechter Kantenübereinstimmung
werden zusätzlich innere Randbänder und gemeinsam variierte Rechteck-/Konturparameter
geprüft. Eine Verfeinerung wird nur bei besserem bisherigem Optimierungsfehler
und nicht schlechterem quadratischem Fehler, Kantenwert und Hintergrund-relativer
Vordergrund-IoU angenommen. Die Suche bleibt auf maximal 204 Auswertungen begrenzt.
Die sechs bereits abgenommenen P-Varianten behalten ihre exakten SVGs.

Es gibt keine neue Runtime-Katalogkennung oder hinterlegte Vorlage. Diese
Registrierung unterstützt die beschriebene Topologie; beliebige Innenzeichen
oder andere Griffanordnungen sind damit nicht allgemein erschlossen.

## Frische CLI-Abnahme

Der Originalbeschreibung-Vorlauf wurde vor den XML- und Runtime-Änderungen mit
neutralen Namen eingefroren. Sein Zielwert `3282.783936` ist von dem historischen
Reviewwert `13368.759766` zu unterscheiden. Der Reproduktionsrunner verwendet
getrennte Wegwerfkopien für Original- und präzisierte Beschreibung und prüft
Quellhashes sowie verbotene Referenz-SVG-Zugriffe. Die tatsächlich gespeicherten
CLI-SVGs werden mit dem Produktionsrenderer erneut vermessen.

| Bild | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| AC0721_1_S | 3282.783936 | 481.410675 |
| AC0721_1_L | 3473.224854 | 856.510193 |
| AC0721_1_M | 3113.617188 | 535.378601 |
| AC0721_L | 6720.906738 | 1306.613281 |
| AC0721_M | 6521.641602 | 389.584290 |
| AC0721_S | 6067.117188 | 541.640015 |

**6/6 bestehen Good-Solution- und Quality-Complexity-Gate, null
Pflichtmetrikregressionen.** Wiederholte CLI-Abnahmen reproduzieren alle zwölf
Vorher-/Nachher-SVGs; die eingefrorenen Original-SVGs bleiben bytegleich.
Null verbotene Referenz-SVG-Zugriffe. Manifest, beide SVG-Sätze und der
maschinenlesbare Nachweis liegen unter
`artifacts/evaluation/labeled_t_square_recheck_v1/`.

Eine unabhängig entworfene synthetische Vorlage besteht mit den Seeds
`20261010` und `20261011` jeweils **17/17** strenge Plan-B-CLI-Prüfungen.
Weitere Tests variieren Farbe, Kontrastpolarität, Lage, Auflösung und Pixelphasen
und verwerfen fehlenden Text, falschen Text, zusätzliche Objekte und getrennte
oder falsch gerichtete Griffe. Die zusätzliche strengere Plan-B-Prüfung der
Original-JPGs besteht **5/6**. `AC0721_L` verfehlt deren Vordergrund-IoU-Grenze
(`0.799373 < 0.85`); beide regulären Gates bestehen. Die Folgeaufgabe
`AC0721-PB-GREY` bleibt sichtbar, die Qualitätsgrenzen unverändert.

## Erfolgsübersicht, Bestandsschutz und Rotation

Die sechs akzeptierten Bild-/SVG-Paare sind zusätzlich unter
`artifacts/satisfactory_conversions/` abgelegt. Die Sammlung enthält jetzt
**152** Paare: 104 neuere Fälle in `semantic-only`, 48 ältere im dokumentierten
Kompatibilitätsmodus. Das erweiterte Profil konvertiert weiterhin sämtliche
archivierten Eingaben erneut. Die strengeren Paketgates und der separate
31-Fälle-Bestandsschutz bleiben eigenständige Prüfungen.

67 fokussierte Tests bestehen. Die sechs Bestandsschutztests konvertieren alle
31 geschützten Varianten erneut und melden null Regressionen. Syntaxprüfung,
CLI-Hilfe und Runtime-ID-Nullprüfung bestehen. Die erneute Konvertierung der
gesamten Sammlung besteht mit **152/152** Review-Pässen und null verbotenen
Referenz-SVG-Zugriffen. Alle 104 neueren Fälle bleiben unverändert oder verbessern
sich. Die bereits bekannte Drift bei 22 älteren Kompatibilitätsfällen bleibt
offen; die akzeptierten Vektoren werden erhalten. Der aktuelle Nachweis liegt in
`artifacts/satisfactory_conversions/recheck_2026-10-10.json`.
Der kompakte Gesamtnachweis einschließlich beider Plan-B-Seeds, aller vier
CLI-Wiederholungen, Bestandsschutz und Review liegt in
`artifacts/evaluation/labeled_t_square_recheck_v1/summary_2026-10-10.json`.

Der erneuerte Review enthält 1.000 Einträge und 993 renderbare Paare; alle 48
bisherigen Erfolgsvarianten bleiben unter der Reviewgrenze. Der genaue Aufruf
steht in `review_arguments.json`. Nächste reguläre Rotation:
**`AC0711_1_M`**, `GE9014_1M`, `GE9012_1M`, `AC0712_1_S`, `AC0734_1_S`.
Der offene Gesamtpool, ältere Graufälle, U-Bogen-Stresstest und die ältere
Archivdrift bleiben separate Folgeaufgaben.

## Reproduktion

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_labeled_description_recheck artifacts/evaluation/labeled_t_square_recheck_v1/manifest.json --output-dir .tmp/labeled-t-reproduction
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/labeled_t_square_recheck_v1/synthetic_holdout.svg --description-file artifacts/evaluation/labeled_t_square_recheck_v1/synthetic_description.txt --output-dir .tmp/labeled-t-plan-b --seed 20261010 --keep-debug-artifacts
.venv/Scripts/python.exe -m tools.refresh_satisfactory_archive
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/labeled-t-archive
.venv/Scripts/python.exe -m pytest -q tests/test_labeled_t_square_runtime.py tests/test_labeled_square_runtime.py --basetemp=.tmp/labeled-t-tests
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_satisfactory_regression_battery.py --basetemp=.tmp/labeled-t-preservation
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m pytest -q --basetemp=.tmp/labeled-t-full
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
```

Ein frisches Ausgabeverzeichnis ist für jeden Reproduktionslauf erforderlich.
Für den zweiten Plan-B-Seed `20261011` ebenfalls ein neues Verzeichnis verwenden.

## Vollständiger Abschlussnachweis

Der vollständige Standardtestlauf besteht mit **2.116 Tests, 0 Fehlern und
30 Skips** in **1.074,32 Sekunden**. 29 Skips betreffen bestehende Windows-/POSIX-
Unterschiede; ein Skip delegiert die Archivkonvertierung an das erweiterte Profil.
Diese wurde separat vollständig mit 152/152 Review-Pässen ausgeführt.
Die finale Runtime-Fassung ist zusätzlich durch die 67 fokussierten Tests,
sechs Paket-Gate-Abnahmen, beide unabhängigen Plan-B-Seeds und 31
Bestandsschutzvarianten ohne Regression abgesichert.

Alle 152 archivierten Bild-/SVG-Paare stimmen mit ihren gespeicherten Hashes
überein; die 146 älteren Indexeinträge sind unverändert. Syntaxprüfung für
`src`, `tests` und `tools`, CLI-Hilfe, Runtime-ID-Nullprüfung und Diff-Prüfung
bestehen. Die Diff-Prüfung berücksichtigt vorhandene Windows-CRLF-Zeilenenden.
Die genannten offenen strengeren Graufälle, Archivdrift und Stressaufgaben
bleiben ausdrücklich außerhalb dieses regulären Paketabschlusses sichtbar.
