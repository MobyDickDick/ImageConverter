# Arbeitspaket – rechts offener Bogen neben Verlaufsschaft (2026-10-14)

Branch: `codex/ge9024-quality-2026-10-14`, Basis `f5447bb08`.
Das nach GE0022 dokumentierte Ziel `GE9024_1M` und seine 13 Farb-/Größenvarianten
bestehen beide unveränderten regulären Gates und die strengeren Plan-B-Pixelgrenzen
ohne Pflichtmetrikregression.

## Quellenprüfung und allgemeine Registrierung

Die ursprüngliche Beschreibung nennt ein hellgraues Quadrat. Die 14 Raster zeigen
einen nach rechts offenen Halbkreisbogen rechts neben einem getrennten waagerechten
rechteckigen Schaft. Der Schaft besitzt einen vertikalen Verlauf mit heller Mitte.
Beide XML-Kataloge enthalten jetzt eine eigenständige Beschreibung dieser Primitive.
Abmessungen, Positionen, Strichbreite und Farben werden weiterhin aus dem Raster
ermittelt. Das Quelleninventar enthält die unveränderten Quellhashes und Bildgrößen.

Die vorhandene allgemeine Bogenregistrierung normalisiert die ausdrücklich beschriebene
Rechtsöffnung in ihr oberes Koordinatensystem. Jeder Suchkandidat wird vor dem Rendern
in die tatsächlichen Ausgabekoordinaten zurückgeführt. Die Ausgabe enthält einen
analytischen Halbellipsenpfad, ein Hintergrundrechteck und ein Rechteck mit nativem
SVG-Verlauf. Keine Transformation, Konturkopie, Rastereinbettung oder Katalogkennung
wird als Runtime-Wissen verwendet. Widersprüchliche Beschreibungen, Zusatzobjekte,
falsche Öffnung und unterbrochene Bögen bleiben ausgeschlossen.

Die erste Abnahme bestand für alle 14 regulären Gates. Bei drei hellen Farbvarianten
lag die strengere Vordergrund-IoU jedoch knapp unter 0,85. Die neue Richtung verwendet
deshalb zusätzlich zur Pixel- und Konturabweichung die Übereinstimmung mit der aus dem
Raster bestimmten Vordergrundmaske als Suchziel. Der anfängliche Fehler bleibt eine
harte Obergrenze; sämtliche Abnahmegrenzen bleiben unverändert. Die bisherigen drei
Bogenrichtungen behalten ihre bisherigen Suchentscheidungen.

## CLI-Abnahme und unabhängige Fälle

Alle 14 neutral benannten Vorläufe wurden tatsächlich vor der Runtime- und XML-Änderung
mit der Originalbeschreibung erzeugt und eingefroren. Frische Wegwerfkopien isolieren
beide Seiten. Der Runner prüft Quellhashes, sperrt fremde SVG-Zugriffe und vergleicht
die gespeicherten Vorher-/Nachher-Vektoren bei der Wiederholung bytegenau.
Bewertet wird das auf Platte gespeicherte SVG nach erneutem Rendern mit dem
Produktionsrenderer. Beim Ziel sinkt Mean-Delta² von **11122.661133 auf 177.697495**.
Alle **14/14** bestehen beide regulären Gates, die unabhängige Rechtsbogen-Semantik
und die strengeren Pixelgrenzen; null Pflichtmetrikregressionen und null fremde
Referenz-SVG-Zugriffe.

Zwei neutrale Abnahmen reproduzieren alle 28 eingefrorenen Vektoren, Metriken und Gates.

Die separate Katalogabnahme verwendet die echten Bildnamen und den vollständigen
Originalkatalog aus dem Basiscommit. Die originale Quadratbeschreibung aktiviert
die neue Bogenregistrierung nicht. Beide Baseline-Kontexte bleiben separat erhalten;
alle 14 finalen Katalog-SVGs sind bytegleich mit ihren neutralen Ausgaben.
Zwei deterministische Katalogabnahmen reproduzieren auch die separaten Vorläufe.
Eine frühe Katalogdiagnose enthielt die standardmäßig aktive zufällige Ausgabevariation;
ihr abweichender Vorlauf wurde von der Byteprüfung abgelehnt und zählt nicht als Abnahme.
Die finalen neutralen und Katalogläufe deaktivieren diese Variation ausdrücklich.

Eine unabhängig konstruierte grüne Vorlage verändert Auflösung, Lage, Größenverhältnisse
und Palette gegenüber dem Katalog. Die echte CLI prüft Original und 16 Zufallsvarianten
mit Seed `20261014`: zweimal **17/17**, mit identischen Eingangs-/Ausgangshashes,
Metriken, Komplexität und Gateentscheidungen. Zusätzliche Rastertests prüfen halbe und doppelte Auflösung,
Verschiebung, elliptische Radien, Farben, fehlende Primitive und widersprüchliche Texte.
Der Renderer besitzt richtungsabhängiges Antialiasing: Die Spiegelprüfung verlangt
daher einen geometrisch exakten Hin-/Rückweg, während die Registrierung immer die
direkt gerenderte finale Richtung bewertet.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **251 Paare**. Alle 237 bisherigen Indexeinträge bleiben
identisch. Die vollständige Prüfung in getrennten Familienprozessen besteht mit
**251/251**. Alle 237 bisherigen erneut gemessenen Mean-Delta²-Werte und die
22 bekannten älteren Kompatibilitätsdrifts bleiben exakt unverändert.
Wiederholungs-, Archiv- und Testabnahmen einschließlich tatsächlicher
Testzahlen, Diagnosefehlschläge und Source-Hashes stehen in
`artifacts/evaluation/right_arc_shaft_recheck_v1/validation_2026-10-14.json`.
Diagnoseläufe zählen nicht als finale Abnahme. Die finale fokussierte Suite besteht
mit **213 Tests**, die AC08-/AC0100-Smoke-Prüfung mit zwei Tests.

Der vollständige finale Standardlauf besteht mit **2.587 Tests und 30 bestehenden
Skips, null Fehlern**. Ein früher gestarteter Standardlauf verwendete noch die
inzwischen korrigierte Spiegelungsassertion: 2.586 bestanden, 30 Skips und dieser eine
Testfehler. Sein roher Bericht bleibt separat als Diagnose erhalten. Die finale
213-Test-Suite und der vollständige finale Standardlauf bestehen nach der Korrektur.
Syntaxprüfung, CLI-Hilfe, Runtime-ID-Nullprüfung, Artefakthashes und Diff-Prüfung bestehen.

Der erste Archivlauf bestand in den ersten beiden Gruppen mit 90/90 und brach danach
beim Schreiben von `conversion_bestlist.csv` mit dem bereits dokumentierten Windows-
I/O-Fehler ab. Dieser Lauf zählt nicht als Vollabnahme. Kleinere globale Batchlimits
wurden korrekt abgelehnt, weil die 48 Fälle des Kompatibilitätskontexts zusammenbleiben
müssen. Die abschließende Prüfung nutzt deshalb das vorhandene Verfahren mit einer
semantischen Motivfamilie je Prozess und unverändertem Kompatibilitätskontext.

Der erneuerte Review umfasst 1.000 Einträge und 993 renderbare Paare. Alle 48 bisherigen
Bestenlisteneinträge bleiben unter der unveränderten Grenze. Bisherige Ausschlüsse und
alle 14 abgenommenen Varianten werden fortgeschrieben. Es folgen **`GE0300`**,
`b_heating1`, `AC0421_1_S`, `GE0306` und `GE0346`. Der separate offene Glocken-Quellenpunkt
GE0022-BELL-SOURCE bleibt erhalten.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe -m tools.run_side_arc_shaft_recheck artifacts/evaluation/right_arc_shaft_recheck_v1/manifest.json --output-dir .tmp/right-arc-reproduce
.venv/Scripts/python.exe artifacts/evaluation/right_arc_shaft_recheck_v1/recheck_catalog_context.py --output-dir .tmp/right-arc-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/right_arc_shaft_recheck_v1/independent.svg --description-file artifacts/evaluation/right_arc_shaft_recheck_v1/independent.txt --seed 20261014 --output-dir .tmp/right-arc-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/right-arc-archive-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '0'
.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/right-arc-tests-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse. Das Paket versioniert Manifest,
echte Baselines, finale Vektoren, Quelleninventar, Gateberichte und unabhängige
Vorlage. Vollständige Diagnoseläufe bleiben lokal unter `.tmp/right-arc-*` erhalten.
