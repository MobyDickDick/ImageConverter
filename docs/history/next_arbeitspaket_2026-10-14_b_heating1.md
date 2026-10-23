# Arbeitspaket – verschachtelte Flammen auf Verlaufsscheibe (2026-10-14)

Branch: `codex/b-heating1-quality-2026-10-14`, Basis `fea318a81`.
`b_heating1` ist der nach GE0300 dokumentierte nächste reguläre Kandidat.
Das gespeicherte finale SVG besteht beide unveränderten regulären Gates und
die strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quellenprüfung und allgemeine Registrierung

Der Katalogeintrag enthält genau ein Bild. Seine bisherige Beschreibung
verweist nur auf andere Katalogbilder. Das Raster zeigt eine Kreisscheibe mit
hellem Rand und vertikalem Verlauf sowie eine aufrechte gefüllte Flamme mit
asymmetrischen spitzen Zungen und rundem Bauch. Eine kleinere helle Flamme
liegt im unteren Inneren. Beide XML-Kataloge beschreiben diese Primitive jetzt
eigenständig. Das Quelleninventar hält Bildhash und Abmessungen unverändert fest.

Die neue allgemeine Registrierung schätzt den Hintergrund aus dem Bildrand,
regressiert den Kreis und ermittelt das vertikale Farbfeld aus freien seitlichen
Scheibenbereichen. Farbkontrast und zusammenhängende Komponenten trennen die
beiden Flammen. Eine begrenzte Anzahl geometrischer Eckmerkmale segmentiert
die Messungen für Geradenregressionen; eine kurze antialiasierte Spitze wird
als gemeinsamer Scheitel geschätzt. Die Ausgabe verwendet je Flamme eine
polygonale Krone mit höchstens 15 Eckmerkmalen und zwei kubische Viertelbögen
für den gerundeten Bauch. Eine begrenzte Pixelsuche verfeinert Geometrie und
Farben; der Ausgangsfehler bleibt eine harte Obergrenze.

Der analytische Kreis und sein nativer SVG-Verlauf bleiben erhalten. Es werden
keine Raster eingebettet, Referenz-SVGs gelesen oder Katalogkennungen und
Bildparameter in der Runtime gespeichert. Die Registrierung ist für die
geprüften verschachtelten, aufrechten Flammen `generalisiert`; andere
Flammentopologien und kontrastarme Innenformen bleiben außerhalb dieser Abnahme.
Fehlende Primitive, glatte Kronen, umgedrehte Flammen, getrennte Zusatzobjekte,
Innenmarkierungen, Unterbrechungen und widersprüchliche Texte werden geprüft.

## CLI-Abnahme und unabhängige Fälle

Der echte neutrale CLI-Vorlauf mit Originalbeschreibung wurde vor der Runtime-
und XML-Änderung eingefroren. Frische Wegwerfkopien isolieren beide Seiten.
Der Runner prüft Quellhashes, sperrt fremde SVG-Zugriffe und vergleicht die
Vorher-/Nachher-SVGs bei Wiederholung bytegenau. Bewertet wird das gespeicherte
SVG nach erneutem Rendern mit dem Produktionsrenderer. Mean-Delta² sinkt von
**10226.132812 auf 726.417908**. Beide regulären Gates, die unabhängige
Flammen-/Einschlusssemantik und alle strengeren Pixelgrenzen bestehen.
Null Pflichtmetrikregressionen und null fremde Referenz-SVG-Zugriffe.

Die separate Katalogprüfung verwendet den echten Namen und den vollständigen
Originalkatalog aus dem Basiscommit. Ihr ursprünglicher Vektor ist bytegleich
mit dem neutralen Vorlauf; die finale Ausgabe ist bytegleich mit dem neutralen
Ergebnis. Die Wiederholungen prüfen beide eingefrorenen Kontexte.

Die unabhängige Vorlage verändert Canvas, relative Lage, Proportionen,
Zungenanordnung und Palette: grüne Scheibe, violette Außenflamme und helle
Innenflamme. Zwei echte CLI-Läufe mit Seed `20261014` bestehen jeweils
**17/17** Fälle. SVG- und Eingangshashes, Metriken, Komplexität und
Gateentscheidungen sind identisch. Direkte Rastertests prüfen zusätzlich
halbe und doppelte Auflösung, Verschiebungen und weitere Paletten.

Ein früher fokussierter Diagnoselauf bestand 35 Tests mit sieben Fehlern
und einem absichtlich abgewählten Evidenztest. Er zeigte zu enge Farbtrennung,
empfindliche Ecksegmentierung sowie fehlende Abgrenzung umgedrehter Flammen
und kleiner Zusatzobjekte. Diese Ursachen wurden in der allgemeinen Erkennung
korrigiert. Zusätzliche Ziel-Diagnosen prüften JPEG-bedingt abgeflachte Spitzen.
Frühe oder wegen Codekorrekturen abgebrochene Gesamt-, Archiv- und CLI-Läufe
zählen nicht als finale Abnahme. Die Pixel- und Qualitätsgrenzen blieben unverändert.
Der frühe Testbericht bleibt als `diagnostic_focused_1.log` erhalten; nur
Zeilenenden und nachgestellte Leerzeichen seiner versionierten Kopie sind
normalisiert. Der vollständige Rohlog bleibt lokal unverändert.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **253 Paare**. Alle 252 bisherigen Indexeinträge
bleiben identisch. Die vollständige Prüfung in getrennten Familienprozessen
besteht mit **253/253**. Die bisherigen erneut gemessenen
Mean-Delta²-Werte und die 22 bekannten älteren Kompatibilitätsabweichungen
bleiben unverändert. Die fokussierte Suite besteht mit **43 Tests**, die
AC08-/AC0100-Smoke-Prüfung mit zwei Tests. Der vollständige Standardlauf
besteht mit **2673 Tests und 30 bestehenden Skips, null Fehlern**.
Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung, Artefakthashes und Diff-Prüfung
bestehen. Die tatsächlichen Zahlen und Hashnachweise stehen in
`artifacts/evaluation/flame_disk_recheck_v1/validation_2026-10-14.json`.

Der erneuerte Review umfasst 1.000 Einträge und 993 renderbare Paare.
Alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Bisherige Ausschlüsse werden fortgeschrieben; ausschließlich das abgenommene
Bild wird zusätzlich ausgeschlossen. Es folgen **`AC0421_1_S`**, `GE0306`,
`GE0346`, `AC0850_L` und `GE0017`. Bestehende offene Aufgaben einschließlich
des separaten Glocken-Quellenpunkts GE0022-BELL-SOURCE bleiben erhalten.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_flame_disk_recheck artifacts/evaluation/flame_disk_recheck_v1/manifest.json --output-dir .tmp/flame-reproduce
.venv/Scripts/python.exe artifacts/evaluation/flame_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/flame-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/flame_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/flame_disk_recheck_v1/independent.txt --seed 20261014 --output-dir .tmp/flame-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/flame-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/flame-tests-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_conversion_regression_smoke.py --basetemp .tmp/flame-smoke-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse. Das Paket versioniert
Manifest, echte Baselines, finale Vektoren, Quelleninventar, Gateberichte,
unabhängige Vorlage und Belege beider Plan-B-Läufe. Vollständige lokale
Diagnosen und Unterprozessartefakte bleiben unter `.tmp/flame-*` erhalten.
