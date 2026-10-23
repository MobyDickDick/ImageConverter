# Arbeitspaket – diagonales Kreuz auf Kreisscheibe (2026-10-15)

Branch: `codex/ge0017-quality-2026-10-15`, Basis `795df0882`.
`GE0017` ist der nach AC0850 dokumentierte nächste reguläre Kandidat.
Das Ziel besteht beide unveränderten regulären Gates und die strengeren
Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quelle und allgemeiner Algorithmus

Das Raster zeigt eine rote Kreisscheibe mit einem hellen diagonalen Kreuz aus
zwei geraden, an den Enden abgerundeten Strichen. Die bisherige Beschreibung
benannte das Fehlerzeichen unpräzise und enthielt Schreibfehler. Beide Kataloge
beschreiben die sichtbaren Primitive jetzt eigenständig. Quelleninventar,
ursprüngliche Beschreibung, Abmessungen und Rasterhash bleiben erhalten.
Es gibt keine weiteren zugeordneten Größenbilder.

Die allgemeine Registrierung bestimmt den Hintergrund aus den Randpixeln
und regressiert den Kreis aus der äußeren Silhouette. Farbkontrast trennt
die Kreuzstriche vom Kreis. Die freien Arme liefern über Hauptachsenregression
zwei Geraden; Projektionen bestimmen Endpunkte und Strichbreiten. Die
Verjüngung an den Enden grenzt ausreichend aufgelöste runde von eckigen
Kappen ab. Komponenten, Kapselüberdeckung und nicht erklärte Bildbereiche
werden geprüft. Eine begrenzte Pixelsuche verfeinert Geometrie und Farben;
die anfängliche Produktionsfehlermetrik bleibt eine harte Obergrenze.
Unter den zulässigen Iterationen wird die beste Pixelsuche beibehalten.

Die Ausgabe enthält ein Hintergrundrechteck, einen gefüllten Kreis und zwei
native SVG-Linien mit runden Enden. Es gibt keine Rastereinbettung, keine
exportierten Pixelkonturen, keine Runtime-Bildkennungen und keine gespeicherten
Bildparameter. Der Konverter erhält ausschließlich Raster und Beschreibung.

## Abnahme

Die echte CLI-Baseline mit ursprünglicher Beschreibung und neutralem Dateinamen
wurde vor Runtime- und Katalogänderung eingefroren. Beide Seiten verwenden
frische Wegwerfkopien. Zwei neutrale Wiederholungen reproduzieren Baseline,
finale SVG und Gateentscheidungen. Zwei Wiederholungen im vollständigen
ursprünglichen beziehungsweise geänderten Katalog reproduzieren ihre eigene
Baseline; die finale Ausgabe ist bytegleich zur neutralen Konvertierung.
Alle Quellen bleiben unverändert, fremde SVG-Lesezugriffe sind null.

Die gespeicherte SVG wird mit dem Produktionsrenderer erneut gerendert.
Der mittlere Pixelfehler sinkt von **10078.861328 auf 490.495758**.
Konturausrichtung, Masken-IoU und Semantik verbessern sich ohne
Pflichtmetrikregression. Die unabhängige Semantikprüfung verlangt einen
gefüllten Kreis und zwei sich schneidende diagonale Linien mit runden Enden.

Eine unabhängig konstruierte violette Kreisscheibe verändert Canvas,
Kreisposition, Radius, Kreuzendpunkte, Strichbreiten und Palette. Zwei echte
CLI-Läufe mit Seed `20261015` bestehen jeweils **17/17** mit identischen
Eingangs-/Ausgangshashes, Metriken, Komplexität und Gateentscheidungen.
Die fokussierte Suite besteht mit **40 Tests**, einschließlich halber und
doppelter Auflösung, Verschiebung, anderen Paletten, fehlenden Primitiven,
eckigen Enden, Lücken, zusätzlichen Objekten, widersprüchlichen Beschreibungen
und ungültigen Messungen. Die zwei schweren AC08-/AC0100-Smoke-Tests bestehen.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält **268 Paare**. Alle 267 bisherigen Indexeinträge
bleiben unverändert. Der erneuerte Review umfasst 1.000 Einträge und 993
renderbare Paare; alle 48 bisherigen Bestenlisteneinträge bleiben unter der
unveränderten Grenze. Alle Ausschlüsse bleiben erhalten; ausschließlich
`GE0017` wird zusätzlich ausgeschlossen. Es folgen **`GE0001_L`**,
`GE9031_6M`, `GE9034_6M`, `GE1411_L` und `GE0305`.
Bestehende offene Folgeaufgaben bleiben erhalten.

Die vollständige Archivkonvertierung besteht mit **268/268**. Alle 267
bisherigen Prüfdatensätze und die 22 bekannten älteren
Kompatibilitätsabweichungen bleiben unverändert.

Die vollständige Standardsammlung besteht mit **2.848 bestandenen Tests,
30 bestehenden Skips und null Fehlern**. Alle 2.878 gesammelten Testknoten
wurden anhand der JUnit-Berichte genau einmal nachgewiesen. Die gesonderte
Runtime-Helfersammlung besteht mit 84 Tests. Syntaxprüfung, CLI-Hilfe und
Image-ID-Hardcoding-Nullprüfung bestehen ebenfalls.

Die maschinenlesbaren Abschlusszahlen und Artefakthashes stehen unter
`artifacts/evaluation/diagonal_cross_disk_recheck_v1/validation_2026-10-15.json`.

## Reproduktion

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/diagonal_cross_disk_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_diagonal_cross_disk_recheck artifacts/evaluation/diagonal_cross_disk_recheck_v1/manifest.json --output-dir .tmp/cross-disk-reproduce
.venv/Scripts/python.exe artifacts/evaluation/diagonal_cross_disk_recheck_v1/recheck_catalog_context.py --output-dir .tmp/cross-disk-catalog-reproduce
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/diagonal_cross_disk_recheck_v1/independent.svg --description-file artifacts/evaluation/diagonal_cross_disk_recheck_v1/independent.txt --seed 20261015 --output-dir .tmp/cross-disk-plan-b-reproduce --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/cross-disk-archive-reproduce
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/cross-disk-standard-reproduce
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_diagonal_cross_disk_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/cross-disk-focused-reproduce
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```

Das Paket versioniert Manifest, Baselines, finale Vektoren, Quelleninventar,
Gateberichte, unabhängige Vorlage und kompakte Belege beider Variationsläufe.
Vollständige Unterprozessartefakte bleiben unter `.tmp/cross-disk-*` erhalten.
