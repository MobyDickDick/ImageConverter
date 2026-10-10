# Arbeitspaket – Quadrat mit unterem Griff, Strich und Punkt (2026-10-10)

Branch: `codex/plan-b-failure-tasks-ac0711-2026-10-10`.
Das nächste dokumentierte Ziel `AC0711_1_M` und alle fünf Farb-/Größen-Holdouts
bestehen beide unveränderten regulären Gates ohne Pflichtmetrikregression sowie
die strengeren Plan-B-Pixelgrenzen.

## Ursache und allgemeine Korrektur

Die bisherige Beschreibung verwies auf eine andere Katalogform und verschwieg
die Innenmarkierung. Beide XML-Kataloge beschreiben jetzt eigenständig ein
gefülltes Quadrat mit Kontur, mittigem unterem Griff, einem schrägen Strich von
rechts oben nach links unten und einem kleinen quadratischen Punkt links neben
dem unteren Strichende. Farben und Maße bleiben dem Raster überlassen.

Die vorhandene Quadrat-/Griffregistrierung unterstützt diese Topologie nun
auch mit dem unteren Griff. Körper und Griff werden für die Pixelsuche auf
eine gemeinsame Orientierung abgebildet; Strich und Punkt werden in der
tatsächlich beschriebenen Orientierung beobachtet. Die gespeicherten SVGs
enthalten ein natives Rechteck und drei Pfade, ohne Rasterbilder, Textglyphen
oder SVG-Transformationen. Es gibt keine neue Runtime-Katalogkennung oder
hinterlegte Motivvorlage.

Eine unabhängig konstruierte Vorlage zeigte zunächst einen zusätzlichen
Fehler bei einer kleinen Verschiebung/Skalierung: Ein antialiasierter Pixel
am Körper-/Griffanschluss lag außerhalb der dicht geschätzten Kontur. Die
Prüfung erlaubt jetzt einen angrenzenden Randpixel. Die Prüfung zusätzlicher
Objekte und die Bedingungen für Griff, Strich und Punkt bleiben verbindlich.
Der zuvor gescheiterte Fall ist separat als Regressionstest abgesichert.

## Frische, reproduzierbare Abnahme

Vor der Runtime-Änderung wurden sechs CLI-Ausgaben mit Originalbeschreibungen
und neutralen Dateinamen eingefroren. Der Nachlauf verwendet ausschließlich
anonyme Raster und die eigenständige Beschreibung im `semantic-only`-Modus.
Der Reproduktionsrunner deaktiviert im Vorher-Lauf nur die neue Registrierung
für den unteren Griff. Alle sechs eingefrorenen Vorher-SVGs bleiben bytegleich.
Zwei unabhängige Nachläufe erzeugen dieselben sechs SVG-Bytes und Gateentscheidungen.
Verbotene Referenz-SVG-Zugriffe: null.

| Bild | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| AC0711_1_L | 1962.774170 | 53.976002 |
| AC0711_1_M | 1859.969971 | 45.307144 |
| AC0711_1_S | 2051.538574 | 143.136002 |
| AC0711_L | 6897.869141 | 26.610666 |
| AC0711_M | 6549.112793 | 29.412857 |
| AC0711_S | 6552.482910 | 38.807999 |

**6/6 bestehen Good-Solution- und Quality-Complexity-Gate, null
Pflichtmetrikregressionen; alle sechs bestehen auch die strengeren Pixelgrenzen.**
Manifest, Vorher-/Nachher-Vektoren und JSON-Nachweis stehen unter
`artifacts/evaluation/bottom_stem_marked_square_recheck_v1/`.
Die unabhängige SVG-Vorlage besteht mit Seed `20261010` **17/17** echte
CLI-Plan-B-Fälle. Ihr Bericht und Ursprungsbild stehen unter `plan_b/`.
Die zunächst gescheiterte Probe wurde mit identischem Seed repariert; die
Qualitätsgrenzen und die unabhängige Vorlage wurden nicht verändert.

## Perception-Lerneffekt: generalisiert

Die geprüfte Quadrat-/Griff-/Strich-/Punktstruktur ist `generalisiert`:
Lage, Größe, Konturbreiten und Farben stammen aus Rastermessungen und einer
begrenzten Pixelsuche. Unabhängige Farben, verschobene Lage, doppelte Auflösung
und Pixelphasen sind abgesichert. Umbenennung verändert die Ausgabe nicht;
fehlende Markierungen, falsche Strichrichtung, zusätzliche Objekte, fehlender
Griff, nicht endliche Daten und fehlendes Rendering werden verworfen.
Andere Innenzeichen und beliebige neue Formkombinationen bleiben außerhalb
dieses Nachweises. Die CLI-Restfehlerwarnungen bleiben sichtbar.

## Erfolgsübersicht, Rotation und Reproduktion

Die sechs Paare sind mit Beschreibung, Messwerten und Hashes in der
Erfolgsübersicht aufgenommen; diese enthält jetzt **158** Einträge.
Die frische erneute Konvertierung besteht mit **158/158** Review-Pässen.
Die zuvor dokumentierte Drift älterer Kompatibilitätsfälle bleibt separat
ausgewiesen; die akzeptierten Archivvektoren werden nicht überschrieben.

Der erneuerte Review enthält 1.000 Einträge und 993 renderbare Paare; alle
48 bisherigen Bestenlisteneinträge bleiben unter der Reviewgrenze. Nach
Ausschluss erledigter Pakete folgt **`GE9014_1M`**, dann `GE9012_1M`,
`AC0712_1_S`, `AC0734_1_S` und `GE9012_2M`. Der genaue Review-Aufruf und
sein kompakter Nachweis stehen im Paketverzeichnis.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_top_stem_square_recheck artifacts/evaluation/bottom_stem_marked_square_recheck_v1/manifest.json --output-dir .tmp/bottom-square-reproduction
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/bottom_stem_marked_square_recheck_v1/independent.svg --description-file artifacts/evaluation/bottom_stem_marked_square_recheck_v1/independent.txt --seed 20261010
.venv/Scripts/python.exe -m tools.recheck_satisfactory_archive --output-dir .tmp/bottom-square-archive
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/bottom-square-full-tests
```

Die gekoppelte Verbesserung des CI-Fehlerablaufs und die konkret erstellten
Fehleraufgaben sind in [Plan-B-Fehler als Aufgaben](plan_b_failure_tasks_2026-10-10.md)
dokumentiert. Diese beiden CI-Motivfehler bleiben offen und werden durch die
Abnahme von `AC0711` nicht als behoben markiert.

## Abschlussprüfung

Der vollständige Standardtestlauf besteht mit **2.144 Tests, 30 bestehenden
Profil-/Windows-Skips und null Fehlern** in 1.084,55 Sekunden. Die danach
ergänzten Prüfungen für Infrastrukturdiagnosen und die konkrete Pixelphase
wurden zusätzlich gezielt ausgeführt. Die abschließenden Fehlererfassungstests
bestehen mit 14/14; die Tests für CLI-Fehlerpfade und Logaufbewahrung bestehen
ebenfalls. Die gezielte Quadrat-Suite bestand mit 120 Tests; der Nachlauf
sichert die geänderte Randprüfung und beide Griffrichtungen ab.

Die separaten schweren Bestandsschutz-, Conversion-Smoke- und Weak-Family-
Prüfungen bestehen mit **10 Tests**, einschließlich der bisherigen 31 guten
Varianten. Die vollständige Erfolgsübersicht wurde separat mit 158/158 geprüft;
22 bekannte ältere Kompatibilitätsfälle haben weiterhin höhere Fehler als
ihre archivierten Vektoren. Compileall, CLI-Hilfe, Diff-Prüfung mit Windows-
Zeilenenden und Runtime-ID-Nullprüfung bestehen. Der kompakte Abschlussnachweis
steht in `validation_2026-10-10.json`; ausführliche lokale Logs unter `.tmp/ac0711/`.
