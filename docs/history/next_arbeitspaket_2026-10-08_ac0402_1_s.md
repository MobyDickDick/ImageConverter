# Arbeitspaket – Gefülltes Rechts-Dreieck im Kreis (2026-10-08)

Branch: `codex/ac0402-quality-2026-10-08`, Basis `fee9f9d4d`.
Das nach dem Quadrat-/Griffpaket dokumentierte Ziel `AC0402_1_S` besteht
mit allen 18 gefüllten roten, grünen und grauen Größen-/SIA-Varianten beide
unveränderten regulären Qualitätsgates ohne Pflichtmetrikregression.
`PB-POOL-2026-10-07` bleibt offen.

## Ursache und Beschreibung

Die gemeinsame XML verwies auf eine andere Katalogform und beschrieb einen
Kompressor nach oben. Die Raster zeigen ein gefülltes Rechts-Dreieck im Kreis.
Die eigenständige Beschreibung benennt jetzt Kreis, Randkontur, kontrastierende
Dreiecksfläche und absolute Richtung. Lage, Größe, Konturbreite und Farben
werden aus dem jeweiligen Raster ermittelt.

Die vorhandene allgemeine Kreis-/Dreieckregistrierung kann diese Fälle bereits
rekonstruieren, sobald die Beschreibung die zutreffende Topologie aktiviert.
**Der Runtime-Algorithmus ist unverändert.** Der Nachweis enthält die
bytegleichen Runtime-Quellen und ihre Hashes; es wird kein neuer
Erkennungsalgorithmus oder bildspezifischer Entscheidungszweig eingeführt.

Drei weitere Raster (`AC0402`, `AC0402_1`, `AC0402_2`) haben ein ungefülltes
einbeschriebenes Konturdreieck und eine einheitliche Innenfarbe. Beide
XML-Dateien weisen ihnen eine eigene Beschreibung zu. Sie gehören nicht zum
Abnahmenachweis der 18 gefüllten Varianten; eine zufriedenstellende
Konturdreieck-Rekonstruktion wird hier nicht behauptet. Die ursprüngliche
21-Fall-Diagnose bleibt lokal unter `.tmp/ac0402/baseline01/` erhalten.

## Frische CLI-Abnahme

Vor der XML-Korrektur wurde die echte CLI-Baseline unter neutralen Dateinamen
eingefroren. Der Vorlauf verwendet die ursprüngliche Beschreibung, der
Nachlauf die eigenständige Beschreibung. Beide verwenden Seed 0,
`semantic-only`, dieselbe Toolchain und denselben abschließenden Renderer.
Bewertet wird jeweils das gespeicherte, erneut gerenderte SVG.

| Eingabe | mean_delta2 vorher | mean_delta2 nachher |
| --- | ---: | ---: |
| Ziel AC0402_1_S | 14019.147461 | 262.637512 |
| AC0402_1_L | 16512.408203 | 120.334999 |
| AC0402_2_L | 7841.204590 | 323.283752 |
| AC0402_L | 6671.793945 | 135.487503 |
| AC0402_1L_sia | 20322.873047 | 104.105621 |

**18/18 bestehen Good-Solution- und Quality-Complexity-Gate und verbessern
sich ohne Pflichtmetrikregression.** Die Ausgabe enthält jeweils eine Ellipse
und ein Dreieckspolygon, ohne Rastereinbettung. Zwei unabhängige CLI-Läufe
reproduzieren alle 36 Vorher-/Nachher-SVGs und Gateentscheidungen. Alle
ursprünglichen 18 Baseline-SVGs bleiben bytegleich. Verbotene SVG-Zugriffe:
null. Die bestehende CLI-Warnung über konzentrierte Restfehler bleibt sichtbar;
der historische Batch-Erfolgsstatus ersetzt die unabhängigen Gates nicht.

13/18 JPG-Ausgaben bestehen zusätzlich die separate strengere Plan-B-Abnahme.
`AC0402_1_L`, `AC0402_1_M`, `AC0402_2_M`, `AC0402_L` und `AC0402_S_sia`
verfehlen deren Vordergrund-IoU-Grenze. Dieser engere Nachweis bleibt offen;
Grenzen und Qualitätsberechnung wurden nicht verändert.

## Vorlagen-Roundtrip und Generalisierung

Die vorhandene SVG-Vorlage `AC0402_L.svg` zeigt ebenfalls ein gefülltes
Rechts-Dreieck im Kreis. Sie wird mit der eigenständigen Beschreibung
rasterisiert; die Runtime erhält ausschließlich Raster und Beschreibung.
Mit Seeds `20261008` und `20261009` bestehen jeweils **16/16** unveränderte
Plan-B-Gates. Ein wiederholter Lauf mit dem ersten Seed reproduziert alle
16 SVG-Bytes und Qualitätsmetriken. Alle 48 Unterprozesse haben null verbotene
SVG-Zugriffe. Dieser Nachweis belegt die geprüfte Familie, nicht den gesamten
zufälligen Aufgabenpool.

Der Perception-Lerneffekt ist `generalisiert` durch Wiederverwendung des
bestehenden katalogfreien Fitters: 18 reale Farb-/Größenvarianten, neutrale
Dateinamen und variierte Lage/Größe im Vorlagen-Roundtrip. Die bestehenden
synthetischen Prüfungen decken zusätzliche Farben, Auflösungen, Richtungen
und falsche Innenformen ab. Es wird kein neuer Perception-Lerneffekt durch
Algorithmusänderung behauptet.

## Runner und Reproduktion

Der bestehende Pumpen-Recheck setzt jetzt explizite Namensgrenzen; damit fordert
die CLI keine interaktive Eingabe an. Er verwendet die vorhandene
SVG-Zugriffssperre, prüft vorhandene Quellhashes und doppelte Namen und verwirft
bereits existierende Ausgabeordner. Unveränderliche Messraster und getrennte
Arbeitskopien verhindern, dass das Verschieben eines Eingabebildes durch einen
CLI-Lauf den anderen Lauf verändert. Alte Manifeste mit eingefrorener
Fitter-Revision bleiben unterstützt.

Versioniert sind Manifest und kompakter JSON-Nachweis unter
`artifacts/evaluation/right_pump_recheck_v1/`. SVGs, Raster, CLI-Protokolle,
JUnit und vollständige Reviewtabellen bleiben lokal unter `.tmp/ac0402/`.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_pump_recheck artifacts/evaluation/right_pump_recheck_v1/manifest.json --output-dir .tmp/right-pump-reproduction
.venv/Scripts/python.exe -m tools.evaluate_pump_recheck .tmp/right-pump-reproduction/manifest.json --output .tmp/right-pump-gates.json
.venv/Scripts/python.exe -c "import json; from pathlib import Path; m=json.loads(Path('artifacts/evaluation/right_pump_recheck_v1/manifest.json').read_text(encoding='utf-8')); Path('.tmp/right-pump-description.txt').write_text(m['description'],encoding='utf-8')"
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/images_to_convert/samples/AC0402_L.svg --description-file .tmp/right-pump-description.txt --seed 20261008 --output-dir .tmp/right-pump-roundtrip
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
$env:TEMP = "$PWD/.tmp/right-pump-test-temp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
.venv/Scripts/python.exe -m pytest -q -ra --basetemp=.tmp/right-pump-pytest
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
```

Toolchain: CPython 3.10.11, NumPy 2.2.6, OpenCV 4.14.0, PyMuPDF 1.26.7.
Direktes Rendering ist ausdrücklich gewählt; ein zusätzlicher vollständiger
Lauf mit automatischer Prozessisolation wird durch diesen Nachweis nicht belegt.

## Testabschluss und Rotation

Alle 24 neuen Prüfungen und insgesamt 92 fokussierte Tests bestehen.
Die vollständige Suite einschließlich der drei Heavy-Module und der
Satisfactory-Bestandsschutzbatterie besteht: **2.285 bestanden, 0 fehlgeschlagen,
29 übersprungen**, insgesamt 2.314 Tests in 851,80 Sekunden mit Exit 0.
Die Skips betreffen die bestehenden POSIX-Shelltests unter Windows.
Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung (`0 occurrences`) und
Diff-Whitespace-Prüfung bestehen. Testzahlen und Protokoll-/JUnit-Hashes stehen
im JSON-Nachweis. Vollständige lokale Protokolle: `.tmp/ac0402/completion.log`
und `completion.xml`.

Ein bestehender Unterprozess-Integrationstest scheitert im Sandbox-Temp-Ordner;
mit dem oben dokumentierten Repository-Temp-Verzeichnis bestehen sowohl die
92 fokussierten Prüfungen als auch die vollständige Suite. Der unveränderte
Template-Transfer-Test protokolliert weiterhin die native Windows-Diagnose
`0xc0000008`, besteht aber in der Suite und im isolierten Kontrolllauf mit
Exit 0. Auch der Kontrolllauf reproduziert die Diagnose. Diese bestehende
Diagnose wird durch das Beschreibungspaket nicht als behoben bezeichnet;
Testname und Kontrollprotokoll-Hash sind im Nachweis festgehalten.

Der erneuerte Review enthält 956 Einträge, davon 950 renderbare Paare. Alle
48 gespeicherten Erfolgsvarianten bleiben unter der Reviewgrenze. Die neuen
18 Rasterpässe sind aus der Auswahl ausgeschlossen. Historische Sammel-SVGs
werden nicht überschrieben. Der genaue Aufruf steht unter
`review.reproduction_arguments` im JSON-Nachweis.

Die nächste reguläre Rotation beginnt mit **`AC0403_1_L`**, gefolgt von
`GE0032`, `AC0413_1_M`, `AC0713_1_L` und `AC0721_1_S`.
Vor Änderungen ist erneut eine frische CLI-Baseline erforderlich.
