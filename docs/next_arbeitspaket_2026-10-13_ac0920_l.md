# Arbeitspaket – Kreisscheibe mit Q (2026-10-13)

Branch: `codex/ac0920-quality-2026-10-13`.
Das nach `GE9022_2M` dokumentierte Ziel `AC0920_L` und beide Größen-Holdouts
bestehen beide unveränderten regulären Gates und sämtliche strengeren
Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Ursache und allgemeine Korrektur

Die bisherigen Beschreibungen enthalten keine konkreten Primitive und
verweisen teilweise auf einen nicht vorhandenen Griff. Das Raster zeigt eine
hell gefüllte Kreisscheibe mit dünner dunkler Kontur und einem dunklen, fetten,
serifenlosen Großbuchstaben Q. Beide XML-Kataloge beschreiben diese Primitive
jetzt eigenständig. Maße, Lage und Farben bleiben Rasterbefunde.

Die vorhandene generische Badge-Ausgabe verwendet für diesen Buchstaben einen
anderen Buchstabenpfad. Eine neue allgemeine Registrierung misst stattdessen
die Kreispose, Kontur, Flächenfarben und Textregion aus dem Raster. Sie verwendet
den ausdrücklich beschriebenen Einzelbuchstaben als natives SVG-Textobjekt.
Der Produktionsrenderer bestimmt die tatsächlichen Schriftabmessungen.
Eine begrenzte Pixelsuche registriert Kreis, Textlage, Schriftgröße und Farben.
Die Ausgabe enthält genau Hintergrundrechteck, Kreis und Text; keine
Katalogkennung, gespeicherte Motivvorlage, Konturkopie oder Rastereinbettung.

Die Silhouettenprüfung berücksichtigt die Auflösung: Kleine Raster erlauben
eine größere Unsicherheit an antialiasierten Buchstabenkanten, größere Raster
müssen auch ähnliche Buchstaben unterscheiden. Der Nachweis umfasst dunkle
Einzelbuchstaben in hellen, einfarbigen Kreisscheiben auf weißem Hintergrund.
Er ist keine allgemeine OCR-Abnahme. Anschlüsse, Verläufe, mehrere Zeichen und
andere Schriftstile gehören nicht zu diesem Vertrag.

## Frische CLI-Abnahme und Wiederholbarkeit

Die drei Vorlauf-SVGs wurden mit neutralen Namen und Originalbeschreibungen
tatsächlich vor der Runtime-Änderung eingefroren. Wiederholte CLI-Läufe arbeiten
auf Wegwerfkopien, kontrollieren Quellhashes und sperren Referenz-SVG-Zugriffe.
Alle sechs Vorher-/Nachher-SVGs, Messwerte und Gateentscheidungen sind
reproduziert. Die eingefrorenen Vorläufe sind bytegleich mit den Wiederholungen.

| Bild | Mean-Delta² vorher, neutral | Mean-Delta² nachher |
|---|---:|---:|
| AC0920_L | 10145.160156 | 506.664001 |
| AC0920_M | 8681.309570 | 438.420013 |
| AC0920_S | 6381.013184 | 1418.199951 |

**3/3 bestehen beide regulären Gates und alle strengeren Pixelgrenzen;
null Pflichtmetrikregressionen, null Referenz-SVG-Zugriffe.** Die unabhängige
Semantikprüfung verlangt den gefüllten umrandeten Kreis, das exakte native Q,
die zentrale Lage, die Kontrastfarben und die richtigen Abmessungen.
Bewertet wird das erneut mit dem Produktionsrenderer gerenderte gespeicherte
SVG. CLI-Restfehlerwarnungen bleiben sichtbar; Prozessabschluss allein ist
keine Qualitätsabnahme.

Eine getrennte Abnahme verwendet echte Katalognamen und die vollständige
Originalbeschreibungstabelle aus Commit `4e87f5b1d`. Der neue Pfad bleibt für
die Originalbeschreibungen inaktiv. Mit deaktivierter zufälliger Ausgabevariation
(`TINY_ICC_OUTPUT_VARIATION=0`) reproduzieren zwei vollständige Katalogläufe
auch die Vorläufe bytegleich mit den neutralen Ergebnissen. Alle sechs SVGs,
Metriken und Gateentscheidungen stimmen überein. Beide regulären und strengeren
Gates bestehen auch im vollständigen Katalogkontext. Der ältere Diagnosebericht
ohne deaktivierte Ausgabevariation wird separat aufbewahrt; dessen abweichende
Vorlaufwerte sind keine versiegelte Baseline.

## Unabhängige Vorlage und Bestandsschutz

Eine grüne Vorlage mit anderer Auflösung, Geometrie und Farbpalette wurde
unabhängig konstruiert. Original plus 16 Zufallsvarianten bestehen die echte
CLI-Abnahme mit Seed `20261013`. Eingangs-/Ausgangshashes, Pixelmessungen,
Komplexität und Gateentscheidungen sind wiederholt identisch.

Gezielte Rastertests prüfen zusätzlich Q, R, P, D und A, halbe und doppelte
Auflösung sowie verschobene Geometrien. Fehlender Text, falscher Buchstabe,
ein O statt Q bei ausreichender Auflösung, Zusatzmarkierung, Quadrat,
fehlende Kreislinie, ungeeigneter Hintergrund, widersprüchliche Beschreibungen,
fehlendes Rendering und nicht endliche Bilddaten werden verworfen.

Die Erfolgsübersicht enthält **233 Paare**. Alle 230 vorherigen Indexeinträge
bleiben identisch. Die getrennte Archivprüfung besteht mit **233/233** erneuten Review-Pässen.
Alle 230 bisherigen erneut gemessenen Mean-Delta²-Werte und die 22 bekannten
älteren Kompatibilitätsdrifts bleiben exakt unverändert.

Die 35 endgültigen fokussierten Tests und die beiden zusätzlichen
AC08-/AC0100-Smoke-Tests bestehen. Das vollständige Standardprofil prüft
2.499 Tests mit 30 bestehenden Skips; die später ergänzte O/Q-Negativprüfung
ist Bestandteil der vollständigen 35-Test-Nachprüfung auf der finalen Runtime.
Die insgesamt 2.500 unterschiedlichen Standardfälle sind damit abgedeckt,
null ungelöste Fehler. Der frühe isolierte Negativtest verwendete einen vom
Renderer nicht unterstützten XML-Namespace-Präfix; das Fixture wurde korrigiert
und alle Negativfälle erneut bestanden. Ursprüngliche Diagnoselogs und finale
Läufe bleiben getrennt erhalten. Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung
und Diff-Prüfung bestehen. Die genauen Ergebnisse und die Zusammensetzung der
Testabdeckung stehen in `validation_2026-10-13.json`.

## Nächste Rotation und Reproduktion

Der erneuerte Review umfasst 1.000 Einträge und 993 renderbare Paare.
Alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten
Reviewgrenze. Die bisherigen Ausschlüsse und alle drei erledigten AC0920-Größen
werden fortgeschrieben. Es folgen **`AC1000_S`**, `GE0022`, `GE9024_1M`,
`GE0300` und `b_heating1`.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_labeled_disk_recheck artifacts/evaluation/labeled_disk_recheck_v1/manifest.json --output-dir .tmp/labeled-disk-reproduce
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/labeled-disk-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/labeled_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/labeled_disk_recheck_v1/independent.txt --seed 20261013 --output-dir .tmp/labeled-disk-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/labeled-disk-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/labeled-disk-tests-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools artifacts/evaluation/labeled_disk_recheck_v1
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Rechecks benötigen frische Ausgabeverzeichnisse. Manifest, eingefrorene
Vektoren, beide regulären und die strengeren Gates, Katalogkontextvergleich,
unabhängige Vorlage, Plan-B-Eingaben/-Vektoren und reproduzierbare Messwerte
stehen unter `artifacts/evaluation/labeled_disk_recheck_v1/`.
