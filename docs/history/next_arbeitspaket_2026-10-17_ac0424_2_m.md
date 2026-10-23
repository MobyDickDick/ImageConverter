# Arbeitspaket – gerichtete Sehnen und Spirale auf Kreisscheibe (2026-10-17)

Basis: `4a72a18a9`. `AC0424_2_M` ist der nach GE9033 dokumentierte nächste
reguläre Kandidat. Alle neun Farb-/Größenvarianten bestehen beide unveränderten
regulären Gates ohne Pflichtmetrikregression. Die sechs farbigen JPGs bestehen
zusätzlich die strengeren Plan-B-Pixelgrenzen. Der graue IoU-Folgepunkt bleibt
ausdrücklich offen.

## Quellen und allgemeiner Algorithmus

Die neun Raster zeigen eine gefüllte Kreisscheibe, zwei zum linken Rand hin
konvergierende Sehnen und eine offene, gegen den Uhrzeigersinn nach innen
laufende Spirale. Beide XML-Kataloge enthalten jetzt eine eigenständige
Beschreibung dieser sichtbaren Struktur. Die ursprünglichen Platzhaltertexte
beider Kataloge und die Rasterprüfsummen bleiben in
`artifacts/evaluation/oriented_spiral_disk_recheck_v1/source_inventory.json`
erhalten. Kein Quellraster wurde verändert.

Der vorhandene Spiralfit wird für die vier Hauptrichtungen normalisiert.
Kreis, Farben, Strichstärken, Sehnen und Spiralparameter werden aus dem
jeweiligen Raster geschätzt und gemeinsam verfeinert. Jeder Kandidat wird im
ursprünglichen Bildrahmen gerendert und bewertet. Die Ausgabe enthält native
Kreis-/Linienkoordinaten und kubische Spiralabschnitte einschließlich gedrehter
Kontrollpunkte; sie benötigt keine SVG-Transformation und keine Rastereinbettung.
Die bisherigen aufwärts gerichteten Ergebnisse bleiben erhalten.

Ein zusätzlicher Zusammenhangstest weist kleine zusammenhängende Innenflächen
zurück, die vom erkannten Linien-/Spiralmodell nicht erklärt werden. Ein
Negativtest mit zusätzlichem Zeichen bestand zunächst trotz des prozentualen
Restpixelspielraums; nach der Korrektur wird er abgelehnt. Die normale
Parameteranpassung und alle Qualitätsgrenzen bleiben unverändert.

Die Runtime enthält keine Bildkennungen, Katalogkoordinaten oder Referenz-SVGs.
Der Lerneffekt ist für diese gerichtete Topologie **generalisiert**. Dies ist
weiterhin ein begrenzter Topologieregistrierer mit expliziten sprachlichen
Voraussetzungen, keine allgemeine Szenen- oder Spracherkennung.

## CLI-Abnahme und unabhängige Fälle

Vor der Runtime-Änderung wurden neun echte CLI-Baselines mit den ursprünglichen
Beschreibungen unter neutralen Dateinamen eingefroren. Ein erneuter Lauf
reproduziert die Baseline- und Ergebnis-SVGs bytegenau. Vorher und nachher
verwenden dieselbe CLI-Konfiguration und `semantic-only`: zunächst 64 angeforderte
Iterationen und acht Validierungsrunden, bei automatisch ausgewählten
Nachbesserungen 65 Iterationen und sieben Runden. Die Logs erhalten beide
Durchgänge. Die analytische Registrierung hat wie bisher ihre eigene begrenzte
Rendersuche. Verbotene SVG-Lesezugriffe: null.

| Quelle | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| AC0424_2_M | 6342.274414 | 128.702225 |
| AC0424_1_L | 8196.925781 | 150.581253 |
| AC0424_1_M | 8207.170898 | 204.273331 |
| AC0424_1_S | 7081.640137 | 285.829987 |
| AC0424_2_L | 6372.099609 | 106.055626 |
| AC0424_2_S | 5513.752441 | 196.582504 |
| AC0424_L | 2804.923096 | 100.260002 |
| AC0424_M | 2675.483398 | 167.300003 |
| AC0424_S | 2919.090088 | 172.717499 |

Beim Ziel sinkt der quadratische Pixelfehler um **97,97 Prozent**. Das ist eine
Fehlerreduktion, keine Prozentangabe zur wahrgenommenen Bildqualität.
Die echten Dateinamen bestehen im vollständigen ursprünglichen und korrigierten
Katalog ihre eigene Abnahme; alle finalen SVGs sind zur neutralen Ausgabe
bytegleich. Der unabhängige Verifikator prüft Kreis, zwei Randsehnen und die
offene Spiralrichtung am gespeicherten Vektor und rendert ihn neu.

Eine unabhängig konstruierte violette Vorlage verändert Zeichenfläche, Lage,
Sehnenwinkel, Spiralsteigung, Strichstärken und Palette. Zwei echte
CLI-Batterien mit unterschiedlichen Seeds (`20261017`, `20261018`) bestehen
jeweils **17/17** Fälle bei 64 angeforderten Iterationen. Die Referenzvorlage
wird ausschließlich vom Prüftreiber rasterisiert und nicht vom Konverter gelesen.
Die endgültigen Läufe nach dem Zusammenhangstest reproduzieren die Ergebnisse
der jeweiligen früheren Batterie.

51 neue Tests behandeln alle neun Raster, alle vier Richtungen auf einer
rechteckigen Zeichenfläche, halbe und doppelte Auflösung, andere Farben,
Subpixelpositionen, fehlende Formen, zusätzliche Zeichen, falsche Drehrichtung,
widersprüchliche Beschreibungen und fehlerhafte Renderer-/Messwerte.
Die 41 bisherigen Spiraltests bleiben Teil der Prüfung.

Die drei grauen JPGs verfehlen ausschließlich die zusätzliche strengere
Vordergrund-IoU-Grenze `0.85`: L `0.711278`, M `0.734266`, S `0.696203`.
Die helle Füllung und JPEG-Abweichungen liegen an der unveränderten
Vordergrundschwelle. Diese verbleibende Einschränkung wird als
`AC0424-PB-GREY` geführt; beide regulären Gates sind für alle neun bestanden.
Keine Quelle und keine Grenze wurde für die Abnahme angepasst.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält jetzt **352 Paare**. Alle 343 bisherigen
Indexeinträge und gespeicherten Bestresultate bleiben unverändert. Der
vollständige Archivlauf und die Standardsammlung sind unter
`artifacts/evaluation/oriented_spiral_disk_recheck_v1/validation_2026-10-17.json`
mit ihren Einzelberichten und Prüfsummen nachgewiesen. Die Archivprüfung gegen
die bisherige absolute Pixelgrenze ist von einem Vergleich mit historischen
Bestresultaten zu unterscheiden; bekannte Kompatibilitätsabweichungen werden
separat ausgewiesen.

Alle **352/352** Neukonvertierungen bestehen diese absolute Archivgrenze.
Die SVG-Bytes und sämtliche gemessenen Qualitätswerte aller 343 bisherigen
Neukonvertierungen stimmen mit dem vorherigen Archivnachweis überein.
330 Läufe erreichen mindestens ihr gespeichertes Bestresultat; dieselben
22 historischen Kompatibilitätsfälle bleiben schlechter als ihr gespeicherter
Beststand. Es ist keine neue Abweichung hinzugekommen. Die gespeicherten
Bestresultate wurden nicht überschrieben. Die erneut erzeugten Vektoren und
der Vergleich sind mit `archive_recheck.json` aufbewahrt und werden vom
Verifikator unabhängig neu vermessen.

Die vollständige normale Sammlung und die abschließende Wiederholung beider
betroffenen Spiralmodule decken alle **3.321 Testknoten** ab: **3.291 bestanden,
30 regulär übersprungen, null verbleibende Fehler**. Der vollständige Lauf
hatte den Zusatzzeichen-Test noch mit dem vorher geladenen Registrierer
ausgeführt und dessen bekannte Fehlfreigabe bestätigt. Die 92 Tests beider
Spiralmodule bestehen mit der endgültigen Korrektur. Vier Richtungstests
wurden anschließend mit einer richtungsneutralen Beschreibung des Spiralstarts
erneut ausgeführt und bestehen ebenfalls. Der zusammengeführte XML-Nachweis
enthält jeden gesammelten Test genau einmal; die ursprünglichen vier
Teilberichte bleiben als Diagnose erhalten. Zusätzlich bestehen die zwei
schweren AC08-/AC0100-Smoke-Tests, `compileall`, CLI-Hilfe,
Bild-ID-Hardcoding-Nullprüfung und `git diff --check`.

Der erneuerte Review enthält 1.000 Datensätze und 993 renderbare Paare.
Alle 48 bisherigen Bestenlisteneinträge bleiben unter derselben Reviewgrenze.
Bisherige Ausschlüsse bleiben erhalten; nur die neun regulär abgenommenen
AC0424-Varianten kommen hinzu. Nächste Rotation: `AC0840_S`, `AC0840_M`,
`SE0082`, `AC0411_1_M`, `AC0910_L`. Die offenen grauen Nachweise und
GENERAL-SCENE-01 bleiben erhalten.

## Reproduktion

CLI-Läufe benötigen frische, kurze Ausgabepfade. Der Verifikator benötigt keine
Neukonvertierung und prüft die gespeicherten Ergebnisse unabhängig.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/oriented_spiral_disk_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_oriented_spiral_disk_recheck artifacts/evaluation/oriented_spiral_disk_recheck_v1/manifest.json --output-dir .tmp/os-reproduction
.venv/Scripts/python.exe artifacts/evaluation/oriented_spiral_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/os-catalog-reproduction
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/oriented_spiral_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/oriented_spiral_disk_recheck_v1/independent.txt --seed 20261017 --output-dir .tmp/os-independent-reproduction --keep-debug-artifacts
.venv/Scripts/python.exe -m pytest -q tests/test_spiral_disk_runtime.py tests/test_oriented_spiral_disk_runtime.py --basetemp .tmp/os-tests-reproduction
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/os-archive-reproduction
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/os-standard-reproduction
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
