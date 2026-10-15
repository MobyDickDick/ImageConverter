# Arbeitspaket – Haus auf Verlaufsscheibe (2026-10-15)

Branch: `codex/ge0346-quality-2026-10-15`, Basis `74c3c83f4`.
`GE0346` ist der nach GE0306 dokumentierte nächste reguläre Kandidat.
Das Hausbild besteht beide unveränderten regulären Gates und die strengeren
Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quelle und allgemeiner Algorithmus

Das Raster zeigt ein gefülltes Haus mit dreieckigem Satteldach und seitlichen
Dachüberständen auf einer Verlaufsscheibe. Die linke helle Tür ist vollständig
in die Fassade eingeschlossen. Das rechte helle Fenster hat einen waagerechten
und einen senkrechten Steg in Hausfarbe. Beide XML-Kataloge beschreiben diese
Primitive eigenständig. Das Quelleninventar erhält ursprüngliche Beschreibung,
Abmessungen und Rasterhash. Es gibt keine weiteren zugeordneten Größenbilder.

Die Registrierung regressiert Kreis und vertikalen Farbverlauf aus dem Raster.
Robuste Farbfeldregression entfernt Vordergrundproben. Zeilenextrema bestimmen
die beiden geraden Dachflanken und die senkrechten Fassadenkanten; ihre
Schnittpunkte liefern ein analytisches Hauspolygon mit sieben Ecken.
Die Tür und vier Fensterflächen bestimmen Öffnungen und Kreuzstege.
Eine begrenzte Pixelsuche verfeinert Geometrie, Strichstärken und Farben.
Der Ausgangsfehler bleibt eine harte Obergrenze. Dachgeraden, Dachinnenfläche,
zusätzliche Komponenten und nicht erklärte Bildbereiche werden geprüft.

Die Ausgabe enthält ein Hintergrundrechteck, einen Kreis mit nativem SVG-Verlauf,
einen Hauspfad und vier Rechtecke für Tür, Fenster und Stege. Gemessene
Pixelkonturen werden nicht als SVG-Punktlisten ausgegeben. Die Runtime speichert
keine Bildkennungen oder gemessenen Bildparameter, bettet kein Raster ein und
liest keine Referenz-SVGs. Für die geprüfte Familie kontrastreicher Häuser mit
Satteldach, linker heller Tür und rechtem Kreuzfenster auf einer vollständig
sichtbaren Verlaufsscheibe ist die Registrierung `generalisiert`. Andere
Haus-/Dachtopologien, zusätzliche Objekte und angeschnittene Kreise gehören
nicht zu dieser Abnahme.

## CLI-Abnahme und unabhängige Fälle

Die echte CLI-Baseline mit Originalbeschreibung und neutralem Dateinamen wurde
vor Änderungen an Runtime und Katalog eingefroren. Beide Seiten erhalten frische
Wegwerfkopien. Quellhashes und fremde SVG-Lesezugriffe werden geprüft.
Eine Wiederholung reproduziert Ausgangs- und finale SVG bytegenau. Der
vollständige Originalkatalog und der revidierte Katalog reproduzieren die
finale Ausgabe unter echtem Dateinamen. Die Katalogbaseline ist eigenständig
eingefroren und geprüft.

Bewertet werden gespeicherte SVGs nach erneutem Rendern mit dem Produktionsrenderer.
Mean-Delta² sinkt von **10410.204102 auf 316.769409**. Beide regulären Gates und
alle strengeren Pixelgrenzen bestehen. Es gibt null Pflichtmetrikregressionen
und null fremde Referenz-SVG-Zugriffe. Die unabhängige Semantikprüfung kontrolliert
Dachform, Überstände, Fassade, Einschluss und Reihenfolge von Tür und Fenster,
die beiden Fensterstege und den vollständigen Einschluss im Kreis.

Die unabhängige Vorlage verändert Canvas, Lage, Proportionen und Palette:
violette Verlaufsscheibe mit dunklem Haus, breiter Fassade und versetztem
Dachfirst. Direkte Rastertests prüfen zusätzlich halbe und doppelte Auflösung,
Verschiebungen, andere Hausfarben, fehlende Primitive, Zusatzmarkierungen,
Schornstein, falsche Türlage, angeschnittenen Kreis, widersprüchliche Texte und
ungültige Messungen. Alle **49 fokussierten Tests** bestehen.

Zwei echte CLI-Läufe mit Seed `20261015` bestehen jeweils **17/17**.
Eingangs-/Ausgangshashes, Metriken, Komplexität und Gateentscheidungen sind
identisch. Die AC08-/AC0100-Smoke-Prüfung besteht mit zwei Tests.

Der erste Diagnoselauf ergab fünf Fehler. Zwei Zufallsvarianten der ersten
unabhängigen Vorlage schnitten den Kreis am Canvasrand ab. Die endgültige
Vorlage hat ausreichend Abstand für sämtliche unveränderten Zufallsänderungen;
ein angeschnittener Kreis ist zusätzlich als Negativfall abgesichert.
Zusatzmarkierung, Fremdobjekt und Schornstein deckten drei zu großzügige
Topologietoleranzen auf. Engere Komponentenprüfung, Dachgeraden-/Flächenprüfung
und eine Prüfung zusammenhängender unerklärter Innenbereiche korrigieren diese
Runtime-Fehler. Die früheren Diagnosen bleiben unter `.tmp/house-*` erhalten.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **264 Paare**. Alle 263 bisherigen Indexeinträge
bleiben unverändert. Die vollständige Archivprüfung in getrennten Prozessen
besteht mit **264/264** erneuten Review-Pässen. Alle 263 bisherigen
Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen bleiben
unverändert. Der frische Review umfasst 1.000 Einträge und 993
renderbare Paare. Alle 48 bisherigen Bestenlisteneinträge bleiben unter der
unveränderten Grenze. Bestehende Ausschlüsse werden fortgeschrieben;
ausschließlich `GE0346.jpg` wird zusätzlich ausgeschlossen. Es folgen
**`AC0850_L`**, `GE0017`, `GE0001_L`, `GE9031_6M` und `GE9034_6M`.
Bestehende offene Aufgaben bleiben erhalten.

Die vollständige Standardsammlung besteht in vier frischen Prozessen mit
**2.805 bestandenen Tests und 30 bestehenden Skips, null Fehlern**. Der Abgleich
der JUnit-Berichte mit dem Sammelplan erfasst alle 2.835 Testknoten genau einmal.

Die vollständigen Abschlusszahlen, Wiederholungen und Artefakthashes stehen in
`artifacts/evaluation/house_disk_recheck_v1/validation_2026-10-15.json`.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/house_disk_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_house_disk_recheck artifacts/evaluation/house_disk_recheck_v1/manifest.json --output-dir .tmp/house-reproduce
.venv/Scripts/python.exe artifacts/evaluation/house_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/house-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/house_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/house_disk_recheck_v1/independent.txt --seed 20261015 --output-dir .tmp/house-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/house-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/house-standard-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_conversion_regression_smoke.py --basetemp .tmp/house-smoke-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse. Das Paket versioniert
Manifest, echte Baselines, finale Vektoren, Quelleninventar, Gateberichte,
unabhängige Vorlage und kompakte Belege der Variationsläufe. Vollständige
Unterprozessartefakte bleiben unter `.tmp/house-*` erhalten.
