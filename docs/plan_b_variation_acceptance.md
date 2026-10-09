# Plan-B-Abnahmetest mit neuer Auswahl bei jedem Start

```powershell
python -m tools.run_plan_b_variations
```

Jeder Start zieht zufällig **ein SVG zusammen mit seiner Beschreibung** aus
`artifacts/images_to_convert/samples` und der Beschreibungstabelle
`artifacts/images_to_convert/Finale_Wurzelformen_V3.xml`. Es gibt kein festes
Testmotiv und keinen festen Standard-Seed. Alle zugeordneten Aufgaben sind
wählbar, unabhängig von ihrer bisherigen Konvertierungsqualität.
SVGs ohne zugeordnete Beschreibung werden im Auswahlprotokoll ausgewiesen.
Bildspezifische Beschreibungen aus der Tabelle werden berücksichtigt.

Zuerst wird das **unveränderte Ursprungsbild mit seiner Originalbeschreibung**
als Fall `original` durch den echten CLI-Konverter verarbeitet. Diese Vorprüfung
verwendet dasselbe Suchbudget, denselben Timeout, denselben Schutz vor fremden
SVG-Zugriffen und dieselben festen Qualitätsgrenzen wie die späteren Varianten.
Historische Erfolgsmarkierungen ersetzen diesen aktuellen Konvertierungsversuch
nicht. Das Original ist zugleich der erste Fall der erweiterten Plan-B-Aufgabe.

Besteht die Vorprüfung nicht, werden keine Varianten erzeugt oder konvertiert.
Der Bericht enthält `status: original_not_convertible`,
`original_satisfactory: false`, `variations_started: false` und die konkreten
Fehlergründe bzw. Messwerte des Originals. Der Lauf endet mit Exitcode **1**:
Die erweiterte Abnahme wurde nicht durchgeführt. Es wird kein anderes Motiv
nachgezogen und keine unvollständige Abnahme als bestanden gewertet.

Nur nach bestandener Vorprüfung entstehen genau 16 verschiedene SVGs und 16 veränderte
Beschreibungen: Skalierung ±6 %, Verschiebung horizontal/vertikal ±2,5 % der
Zeichenfläche und unterschiedliche Formulierungen. Die Beschreibung behält
ihre bisherigen Aussagen und ergänzt die passende relative Änderung;
konkrete Koordinaten werden dem Konverter nicht verraten. Ganze Motive werden
gemeinsam verändert; Lagebeziehungen zwischen ihren Bestandteilen bleiben erhalten.
Bei Motiven nahe am Rand kann eine kleine Änderung zu Abschneidung führen.

Die Referenzen werden verlustfrei als PNG rasterisiert. Der **echte CLI-Konverter**
erhält je Fall nur dieses Rasterbild und dessen Beschreibung, unter anonymem
Namen und im Modus `semantic-only`. Jeder Fall hat ein frisches Ausgabe- und
Eingabeverzeichnis. Referenz-SVGs werden nicht als Konvertereingabe übergeben.
Ein Audit-Hook im CLI-Unterprozess blockiert außerdem das Lesen fremder SVGs
(einschließlich Katalogvorlagen und Testreferenzen); erlaubt bleiben ausschließlich
die in diesem Fall selbst erzeugten SVGs. Jeder versuchte Vorlagenzugriff zählt
als Fehler, auch wenn der Konverter ihn intern abfängt. Das Protokoll steht in
`reference_access.json`.

## Verbindliche Abnahme

Das Original und alle 16 Varianten (insgesamt **17 Fälle**) müssen die vorab
festgelegten Grenzen bestehen:

| Messung | Grenze |
| --- | --- |
| Normalisierter mittlerer RGB-Quadratfehler | höchstens 0,01 |
| RGB-Quadratfehler im Vordergrund | höchstens 0,04 |
| Symmetrische Konturübereinstimmung | mindestens 0,72 |
| Vordergrund-Überlappung (IoU) | mindestens 0,85 |
| Intrinsische Bildgröße | identisch zur Eingabe |
| Vektorelemente / Pfadbefehle | höchstens 80 / 160 |
| Eingebettete Rasterbilder | keine |

Der Fehler wird durch `255²` normalisiert und über die drei Farbkanäle gemittelt.
Die Konturmetrik ist der Mittelwert von `exp(-Abstand)` zur jeweils nächsten
Gegenkontur, in Pixeln, mit Canny-Grenzen 50/140. Für die Vordergrundmaske dient
die mediane Randfarbe als Hintergrund; eine Kanalabweichung über 25 zählt als
Vordergrund. Vordergrundfehler und IoU verhindern, dass große leere Flächen
fehlende Motive verstecken. Diese generische Prüfung bewertet sichtbare
Rekonstruktionsqualität, keine vollständige sprachliche Semantik/OCR.

Ein fehlendes/unlesbares Ergebnis, Prozessfehler oder Timeout zählt als Fehler.
Nach bestandener Original-Vorprüfung werden alle 16 Varianten auch bei einem
Variantenfehler abgearbeitet. Ein gutes Mittel über mehrere
Fälle kann einen schlechten Einzelfall nicht ausgleichen. Exitcode **0 bedeutet
17/17**, andernfalls endet der Test mit **1**. Ergebnisse im Fehlgeschlagen-Ordner
des Konverters werden ebenfalls unabhängig vermessen; dessen historische
Erfolgsmarkierung ersetzt die Abnahme nicht.

## Ergebnisse und Wiederholung

Jeder Start legt einen neuen Lauf unter `artifacts/evaluation/plan_b_variations`
an und behält standardmäßig **`report.json` und das Ursprungsbild `source.png`**.
Das PNG ist die unveränderte, verlustfrei rasterisierte Quelle, die der
Original-Vorprüfung übergeben wurde. Sein SHA-256 steht in `source_image_sha256`;
`source_image` verweist auf die Datei relativ zum Bericht.
Der Bericht (Schema `plan_b_variations_v2`) enthält Quelle,
Beschreibung, Seed, Quell-Hashes, Varianten, feste Grenzen, Einzelmetriken und
Fehlergründe sowie den Status der Vorprüfung. `cases` beginnt mit `original`,
gefolgt von den 16 Varianten nach bestandener Vorprüfung. Die Zusammenfassung
verlangt stets 17 Fälle; bei fehlgeschlagenem Original stehen dort ein
abgeschlossener und ein fehlgeschlagener Fall. Sie zählt die nicht gestarteten
Varianten nicht als Konvertierungsfehler.
Der Bericht wird vor der ersten Konvertierung und nach jedem Fall fortgeschrieben.
Referenzen, Variantenraster,
Konverterausgaben und Logs sind Arbeitsdateien und werden anschließend auch bei
Fehlschlägen oder einem abgefangenen Abbruch entfernt. Diese Laufverzeichnisse
sind in `.gitignore` ausgeschlossen; CI lädt den Ergebnisbericht und das
Ursprungsbild hoch. Bei einem abgefangenen Abbruch steht `status: interrupted`
im Bericht; das Ursprungsbild bleibt ebenfalls erhalten.

Nur bei ausdrücklichem Diagnosebedarf behält `--keep-debug-artifacts` außerdem
`manifest.json`, `source.svg`, `source_description.txt`, sämtliche Eingaben,
Konverterlogs, Ergebnis-SVGs und Vergleichsbilder (`comparison.png`).

Gezielt denselben Lauf wiederholen: Beschreibung aus dem Bericht lesen und das
dort ausgewählte ursprüngliche SVG verwenden. Sein Hash muss weiterhin stimmen.

```powershell
python -c "import json; from pathlib import Path; r=json.loads(Path('PFAD/ZUM/LAUF/report.json').read_text(encoding='utf-8')); Path('.tmp/description.txt').write_text(r['source_description'],encoding='utf-8')"
python -m tools.run_plan_b_variations --svg URSPRUENGLICHES_SVG --description-file .tmp/description.txt --seed SEED_AUS_BERICHT
```

Eine feste Auswahl per `--svg` ist nur eine ausdrückliche Wiederholung bzw.
gezielte Diagnose. Der Standardstart wählt immer neu. Gleiche zufällige
Auswahlen in aufeinanderfolgenden Starts sind möglich.

Eigene Aufgabenpools:

```powershell
python -m tools.run_plan_b_variations --svg-dir MEIN_SVG_ORDNER --descriptions-path MEINE_BESCHREIBUNGEN.xml
```

Alternativ kann jedes SVG seine Beschreibung in einer gleichnamigen `.txt`-Datei
haben; diese hat Vorrang vor der Tabelle. Die Tabelle unterstützt wie der
Konverter XML/CSV/TSV. `--timeout-seconds` (Standard 60) begrenzt jeden
Unterprozess, `--iterations` (Standard 64) steuert das Suchbudget.
`--output-dir` muss ein noch nicht vorhandenes Verzeichnis bezeichnen.

Der GitHub-Workflow **Plan B random task acceptance** startet diesen echten
Abnahmetest für Pull Requests, Pushes auf main/master/work und manuelle Starts.
Auch in CI wird bei jedem Start neu ausgewählt. Er bleibt bei Qualitätsfehlern
rot und lädt die Belege auch bei Fehlschlägen hoch. Die schnellen Tests in
`tests/detailtests/test_plan_b_variations.py` sichern Auswahl, Varianten,
Qualitätsmessung und Fehlerpfade ab; sie ersetzen den echten Abnahmelauf nicht.

Der Anspruch gilt für jede ausgewählte Aufgabe: Erst muss das Original, dann
müssen alle 16 Varianten die
gleichen Grenzen bestehen. Eine erfolgreiche Symbolfamilie belegt noch keine
vollständige Abdeckung des Auswahlpools. Scheitert eine andere Familie, bleibt
der Lauf korrekt rot; sie wird mit eingefrorenem Seed und unveränderten Eingaben
zum nächsten Lernfall. Grenzen zu lockern oder ein leichteres Motiv zu wählen
erfüllt diese Aufgabe nicht. Der Runner organisiert und bewertet die Abnahme;
die Rekonstruktionsalgorithmen liegen unter `src/iCCModules`.

## Original-Vorprüfung vom 2026-10-09

Der echte CLI-Lauf mit `AR0030.svg`, Originalbeschreibung und dem eingefrorenen
Seed `2870690750133000144` besteht **17/17**: zuerst das unveränderte Original,
danach dieselben 16 Varianten wie zuvor. Es gab keine verbotenen SVG-Zugriffe.
`source.png` bleibt beim Bericht erhalten; sein Hash entspricht exakt dem
Rastereingang des Originalfalls.

Eine zusätzliche Probe mit einem grünen Kreis und einem Suchbudget von einer
Iteration verfehlt die Vordergrundfehler- und Konturgrenze bereits beim Original.
Der Runner beendet diesen Lauf nach einem Fall mit `original_not_convertible`,
ohne die 16 Varianten zu starten, und behält Bericht und Ursprungsbild.
Die 26 gezielten Tests sichern beide Abläufe, Prozessfehler, Timeout,
Unterbrechungen, Artefaktaufbewahrung und den echten Original-Unterprozess ab.

## Klappensymbol-Abnahme vom 2026-10-07

Der [CI-Ausfall von AR0030](https://github.com/MobyDickDick/ImageConverter/actions/runs/37648964984/job/112886962317)
wurde lokal mit Seed `2870690750133000144` reproduziert: **0/16**.
Nach Verbesserung der allgemeinen elementweisen Rasterregistrierung bestehen
dieselben 16 Eingaben **16/16**; Seed `20261007` besteht weitere **16/16**.
Beschreibung, Quell-SVG, Qualitätsgrenzen sowie alle 16 eingefrorenen
Referenz-/Eingabehashes bleiben identisch. Verbotene SVG-Zugriffe: null;
sechs Vektorelemente je Ausgabe, keine eingebetteten Rasterbilder.

| Seed | Max. RGB-Fehler | Max. Vordergrundfehler | Min. Konturübereinstimmung | Min. IoU |
| --- | --- | --- | --- | --- |
| `2870690750133000144` | `0.000546` | `0.000602` | `0.848184` | `0.868062` |
| `20261007` | `0.001107` | `0.001855` | `0.765197` | `0.851330` |

Die bisherige Suche begrenzte den Kreisradius auf 3,2 Pixel und setzte seinen
Mittelpunkt auf die Bildmitte. Rahmen und Diagonale konnten sich nicht unabhängig
verschieben; der einfache Verlauf bildete das breite Highlight unzureichend ab.
Jetzt werden Kreis, Rahmen, Diagonale und ein kontinuierlicher Verlauf mit
höchstens 17 Stopps aus Rastermessungen registriert und gemeinsam verfeinert.
Zwei rasterbasierte Startschätzungen vermeiden lokale Fehlanpassungen bei
Beschnitt und weißen Rändern; allein der gerenderte Pixelfehler entscheidet.
Die Runtime verwendet keine Katalogkennung und liest keine Referenzvektoren.
Vier schwierige Regressionsproben und drei frei konstruierte Motive mit anderer
Kreisgröße, Lage und Auflösung sichern die Änderung in der bestehenden Testdatei
ab. Alle Diagnoseartefakte werden nach der Prüfung entfernt; es entsteht keine
neue dauerhafte Datei. Diese Abnahme belegt die Klappenfamilie, nicht den gesamten
zufälligen Aufgabenpool.

Prüfung der Testsuite in zwei Gruppen: **1704 vorhandene + 7 neue Tests
bestanden**, 29 bestehende Windows-Skips. Syntaxprüfung, CLI-Hilfe und die
Runtime-ID-Nullprüfung bestehen ebenfalls. Die neuen Prüfungen sichern
pixelbasierte Rekonstruktion und unabhängige Geometrie ab; die vollständigen
16 Varianten je Seed wurden zusätzlich über echte CLI-Unterprozesse abgenommen.

## Stufendiagramm-Abnahme vom 2026-10-07

`AC0538_1L_sia`: vorher 0/16, nach geometrischer Beschreibung und katalogfreier
Rasterregistrierung 16/16 mit dem eingefrorenen Seed `3948009396310964094` sowie
16/16 mit Seed `20261007`. Alle ursprünglichen Raster-/Referenzhashes stimmen;
32 wiederholte SVG-Ausgaben sind bytegleich, verbotene SVG-Zugriffe: null.
Schlechteste Werte: RGB-Fehler `0.000751`, Vordergrundfehler `0.003972`,
Konturübereinstimmung `0.885294`, IoU `0.938086`; sechs Vektorprimitive pro Ausgabe.
Die Registrierung bestimmt Geometrie, Linienbreiten und Farben aus dem Raster
und verbindet beide sichtbaren Diagonalabschnitte über den verdeckenden Kreis.
Die korrigierte Beschreibung allein verfehlt im isolierten Vergleichsfall alle
vier Qualitätsgrenzen. Unabhängige Farb-/Lage-/Größentests bestehen ebenfalls.
Vollständige damalige Prüfung: `1702 passed, 29 skipped`; der sehr kleine
S-JPEG-Fall bleibt wegen unterabgetasteter Stufenkurve offen. Die ausführlichen
Einzelartefakte wurden auf Nutzerwunsch entfernt. Eine Wiederholung verwendet
das Sample-SVG und die geometrische Beschreibung aus seiner aktuellen XML-Zeile.
