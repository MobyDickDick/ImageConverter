# Arbeitspaket – Warndreieck auf Verlaufsscheibe (2026-10-15)

Branch: `codex/ge0001-quality-2026-10-15`, Basis `6b3b56290`.
`GE0001_L` ist der nach GE0017 dokumentierte nächste reguläre Kandidat.
Alle sechs zugeordneten roten und blauen Größenvarianten bestehen beide
unveränderten regulären Gates und die strengeren Plan-B-Pixelgrenzen ohne
Pflichtmetrikregression.

## Quelle und allgemeiner Algorithmus

Die Raster zeigen eine Verlaufsscheibe mit hellem Rand und einem aufrechten
Warndreieck. Das Dreieck hat einen breiten dunklen Rand mit gerundeten Ecken
und eine helle Innenfläche. Darin stehen ein dunkler senkrechter Strich mit
runden Enden und ein getrennter runder Punkt. Beide XML-Kataloge beschreiben
diese Primitive eigenständig. Quelleninventar, ursprüngliche Beschreibung,
Abmessungen und Rasterhashes bleiben erhalten.

Die Registrierung bestimmt den Hintergrund aus den Randpixeln und regressiert
den Kreis aus der äußeren Silhouette. Eine robuste Farbfeldregression trennt
den vertikalen Verlauf vom Vordergrund. Die eingeschlossene Innenfläche
identifiziert den Dreiecksrand. Zeilenextrema regressieren die beiden schrägen
Kanten; ihre Schnittpunkte mit der Grundlinie liefern analytische Dreiecke.
Die äußeren und inneren Kanten bestimmen Mittellinie und Randbreite.
Zwei getrennte Innenkomponenten liefern Strich und Punkt. Eine begrenzte
Pixelsuche verfeinert Geometrie, Strichbreiten und Farben. Die anfängliche
Produktionsfehlermetrik bleibt eine harte Obergrenze. Nicht erklärte
zusammenhängende Bildbereiche werden nach der Registrierung verworfen.

Die Ausgabe enthält Hintergrundrechteck, Kreis mit nativem SVG-Verlauf,
geschlossenen Dreieckspfad, eine native SVG-Linie mit runden Enden und einen
Punktkreis. Pixelkonturen werden nicht als Punktlisten ausgegeben. Die Runtime
enthält keine Bildkennungen, gespeicherten Bildparameter oder Referenz-SVGs
und bettet kein Raster ein. Der Konverter erhält ausschließlich Raster und
Beschreibung. Für die geprüfte Familie kontrastreicher aufrechter Warndreiecke
mit Strich und getrenntem Punkt auf einer vollständig sichtbaren vertikalen
Verlaufsscheibe ist die Registrierung `generalisiert`. Andere Zeichen,
Dreiecksrichtungen und angeschnittene Kreise gehören nicht zu dieser Abnahme.

Ein vorgelagerter Parserfehler deutete den senkrechten Innenstrich als
Badge-Anschluss und erfand einen Buchstaben. Explizit beschriebene Dreiecke
mit Ausrufezeichen behalten nun ihre Topologie für die Rasterregistrierung.
Diese Entscheidung verwendet ausschließlich den Beschreibungstext.

## CLI-Abnahme und unabhängige Fälle

Die echte CLI-Baseline mit ursprünglicher Beschreibung und neutralen
Dateinamen wurde vor Runtime- und Katalogänderung eingefroren. Beide Seiten
erhalten frische Wegwerfkopien. Baseline und finale SVGs werden bytegenau
reproduziert. Die vollständigen ursprünglichen und geänderten Kataloge
reproduzieren unter echten Dateinamen ihre eigene Baseline und dieselben
finalen SVGs wie die neutrale Konvertierung. Alle Quellen bleiben unverändert;
fremde SVG-Lesezugriffe sind null.

Gespeicherte SVGs werden mit dem Produktionsrenderer erneut gerendert.
Die unabhängige Semantikprüfung kontrolliert Verlaufskreis, aufrechtes
geschlossenes Dreieck, helle Innenfläche, gerundeten Rand, getrennten Strich
und Punkt sowie deren Einschluss und Reihenfolge.

| Quelle | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| GE0001_L | 10026.326172 | 278.354492 |
| GE0001_M | 9638.921875 | 252.756393 |
| GE0001_S | 9591.837891 | 267.593597 |
| GE0001_1_L | 8480.231445 | 356.290802 |
| GE0001_1_M | 11913.210938 | 284.183899 |
| GE0001_1_S | 7944.395020 | 251.509598 |

Die unabhängige violette Vorlage verändert Canvas, Lage, Proportionen,
Dreieck, Innenzeichen und Palette. Zwei echte CLI-Läufe mit Seed `20261015`
bestehen jeweils **17/17**. Eingangs-/Ausgangshashes, Metriken, Komplexität und
Gateentscheidungen sind identisch. Direkte Tests prüfen zusätzlich halbe
und doppelte Auflösung, Verschiebungen, andere Verlaufspaletten, fehlende
Primitive, zusätzliche Markierungen, gedrehte Dreiecke, verbundene Innenzeichen,
angeschnittene Kreise, widersprüchliche Texte und ungültige Messungen.
Alle **48 fokussierten Tests** sowie die beiden schweren AC08-/AC0100-Smoke-Tests
bestehen.

Die ersten zusätzlichen Palettentests deckten eine zu hohe Kontrastschwelle
auf: Dunkle Verlaufsscheiben unterbrachen den erkannten Dreiecksrand.
Die korrigierte allgemeine Kontrasttrennung besteht diese Fälle. Frühere
Diagnoseläufe bleiben unter `.tmp/warning-*` erhalten.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **274 Paare**; alle 268 bisherigen Indexeinträge
bleiben unverändert. Der erneuerte Review umfasst 1.000 Einträge und 993
renderbare Paare. Alle 48 bisherigen Bestenlisteneinträge bleiben unter der
unveränderten Grenze. Bestehende Ausschlüsse bleiben erhalten; nur die sechs
abgenommenen GE0001-Varianten kommen hinzu. Es folgen **`GE9031_6M`**,
`GE9034_6M`, `GE1411_L`, `GE0305` und `GE9032_6M`.
Bestehende offene Aufgaben bleiben erhalten.

Die vollständige Archivkonvertierung besteht mit **274/274**. Alle 268
bisherigen Prüfdatensätze und die 22 bekannten älteren
Kompatibilitätsabweichungen bleiben unverändert. Ein früherer Diagnoselauf
brach beim Schreiben seines Zwischenberichts mit einem Windows-I/O-Fehler ab;
der vollständige frische Abschlusslauf besteht ohne diesen Fehler.

Die vollständige Standardsammlung ergibt **2.896 bestandene Tests,
30 bestehende Skips und null verbleibende Fehler**. Der erste Lauf in vier
Prozessen enthielt noch die drei oben beschriebenen Palettenfehler. Nach
der Korrektur wurde das gesamte betroffene Modul mit allen 48 Tests erneut
ausgeführt. Der zusammengeführte Abschlussbericht ersetzt ausschließlich
dieses Modul durch seine endgültigen Resultate; die ersten vier Berichte
bleiben separat erhalten. Der Abgleich mit dem Sammelplan weist alle 2.926
Testknoten im Abschlussbericht genau einmal nach. Syntaxprüfung, CLI-Hilfe
und Image-ID-Hardcoding-Nullprüfung bestehen ebenfalls.

Maschinenlesbare Abschlusszahlen und Artefakthashes stehen unter
`artifacts/evaluation/warning_disk_recheck_v1/validation_2026-10-15.json`.

## Reproduktion

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/warning_disk_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_warning_disk_recheck artifacts/evaluation/warning_disk_recheck_v1/manifest.json --output-dir .tmp/warning-reproduce
.venv/Scripts/python.exe artifacts/evaluation/warning_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/warning-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/warning_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/warning_disk_recheck_v1/independent.txt --seed 20261015 --output-dir .tmp/warning-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/warning-archive-reproduce
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/warning-standard-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_warning_disk_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/warning-focused-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

Das Paket versioniert Manifest, Baselines, finale Vektoren, Quelleninventar,
Gateberichte, unabhängige Vorlage und kompakte Belege beider Variationsläufe.
Vollständige Unterprozessartefakte bleiben unter `.tmp/warning-*` erhalten.
