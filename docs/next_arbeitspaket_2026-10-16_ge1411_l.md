# Arbeitspaket – Achsendiagramm mit Sinuskurve (2026-10-16)

Branch: `codex/ge1411-quality-2026-10-16`, Basis `8a82f90e4`.
`GE1411_L` ist der nach GE9034 dokumentierte nächste reguläre Kandidat.
Alle drei Größen bestehen beide unveränderten regulären Gates und die
strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quellen und allgemeiner Algorithmus

Die Raster zeigen links eine senkrechte und unten eine waagerechte dunkle
Achse sowie darüber eine dünne farbige Sinuskurve mit einem Tal und einem
Berg. Beide Kataloge beschreiben diese Struktur jetzt eigenständig. Die alte
Referenz auf GE1410 entfällt: Dessen drei Raster zeigen zwei entgegengesetzte
gefüllte Dreiecke und sind keine Sinus-Holdouts. Sie bleiben unverändert und
ungeprüft. Ursprüngliche Beschreibung, Rasterhashes und Abmessungen beider
Gruppen stehen in `source_inventory.json`. Alle Rasterquellen bleiben erhalten.

Der allgemeine Registrierer trennt die farbige Kurve anhand des Kanalabstands
von neutralen Achsen und Papier. Gewichtete Spaltenmittel liefern Kurvenpunkte.
Eine begrenzte Wellenlängensuche mit linearer Ausgleichsrechnung für Offset,
Sinus- und Kosinusanteil bestimmt Amplitude, Phase und Wellenlänge. Neutrale
lange Rasterlinien bestimmen Achsenpositionen und Endpunkte. Anschließend
optimiert eine begrenzte Koordinatensuche Geometrie, Strichbreiten und Farben
gegen den tatsächlichen Produktionsrenderfehler. Der gerenderte Startkandidat
bleibt eine harte Fehlerobergrenze.

Die Ausgabe verwendet einen weißen Hintergrund, einen rechtwinkligen
Achsenpfad und einen kompakten kubischen Bézierpfad für die analytische
Sinusfunktion. Sie enthält keine Rastereinbettungen, Pixelkonturen oder
Katalogkoordinaten. Die Runtime verwendet ausschließlich Raster und
Beschreibung. Für eine einzelne farbige Sinuskurve oberhalb neutraler,
rechtwinkliger linker/unterer Achsen ist der Algorithmus `generalisiert`.
Mehrere Kurven, zusätzliche Zeichen, graue Kurven, Pfeilspitzen und andere
Achsentopologien sind nicht abgenommen.

## Echte CLI-Abnahme und unabhängige Fälle

Vor der Runtime-Änderung wurde die echte CLI-Baseline mit ursprünglicher
Beschreibung und neutralen Dateinamen eingefroren. Vorher und Nachher
verwenden getrennte frische Kopien. Die Wiederholung reproduziert die
ursprünglichen SVGs bytegenau. Im vollständigen ursprünglichen und geänderten
XML-Katalog bestehen die echten Dateinamen ihre eigene Vorher-/Nachher-Abnahme;
alle finalen SVGs sind bytegleich zu den neutralen Ausgaben. Verbotene
SVG-Lesezugriffe: null. Alle Metriken stammen aus erneut gerenderten,
gespeicherten SVGs; eine getrennte Semantikprüfung kontrolliert rechte Winkel,
Kurvenkontinuität, monotone x-Koordinaten und die beiden Extrema.

| Quelle | Mean-Delta² vorher (neutral) | Mean-Delta² nachher |
|---|---:|---:|
| GE1411_L.jpg | 8597.085938 | 61.729599 |
| GE1411_M.jpg | 8340.669922 | 71.317497 |
| GE1411_S.jpg | 4610.351074 | 87.342224 |

Die unabhängige blaue Vorlage verändert Zeichenfläche, Achsenlage,
Proportionen, Strichbreiten, Palette, Phase und Wellenlänge. Zwei echte
CLI-Läufe mit Seed `20261016` bestehen jeweils **17/17** Fälle. Der Verifikator
prüft Eingangs-/Ausgangshashes, gespeicherte Metriken und Gateentscheidungen
sowie die Gleichheit beider Läufe. Direkte Tests prüfen außerdem halbe und
doppelte Auflösung, andere Paletten, fehlende Achsen oder Kurven, Zusatzpunkte,
flache und doppelte Kurven, fehlende/falsche Beschreibungen sowie ungültige
Render- und Fehlerwerte.

Die ersten Diagnosen deckten unnötig viele Béziersegmente und eine absolute
Frequenzuntergrenze auf, die verschobene unabhängige Fälle ablehnte. Die
kompakte analytische Kurve und eine auf die sichtbare Spannweite bezogene
Frequenzprüfung korrigieren beides. Diagnoseverzeichnisse `.tmp/wr`, `.tmp/wp1`
und `.tmp/wc` bleiben erhalten und zählen nicht als bestandene Abnahme.
Für die vollständige Größenfamilie verwendet der Katalogtest denselben
Familienstamm als Start und Ende; L/S-Grenzen allein schließen M aus.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält 305 Paare; alle 302 bisherigen Indexeinträge
bleiben unverändert. Die vollständige Standardsammlung besteht mit **3.029 bestandenen Tests, 30 bestehenden Skips und null Fehlern**.
Alle 3.059 gesammelten Testknoten sind genau einmal nachgewiesen.
Die erneute Archivkonvertierung besteht mit **305/305**; alle 302
bisherigen Prüfdatensätze und die 22 bekannten älteren Kompatibilitäts-
abweichungen bleiben unverändert. Die schweren AC08-/AC0100-Smoke-Tests
bestehen mit **2/2**. Abschlusszahlen und Artefakthashes stehen in
`artifacts/evaluation/sine_diagram_recheck_v1/validation_2026-10-16.json`.
Der Review enthält unverändert 1.000 Einträge und 993 renderbare Paare;
alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Ausschließlich die drei abgenommenen GE1411-Größen sind zusätzlich
ausgeschlossen. Die nächste reguläre Rotation lautet `GE0305`, `GE9032_6M`,
`AC0414_2_L`, `GE9033_6M`, `AC0424_2_M`. Bestehende offene Aufgaben bleiben erhalten.

## Reproduktion

CLI-Prüfungen benötigen frische Ausgabeverzeichnisse. Kurze Pfade vermeiden
die bereits dokumentierten Windows-I/O-Probleme langer Archivpfade.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/sine_diagram_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_sine_diagram_recheck artifacts/evaluation/sine_diagram_recheck_v1/manifest.json --output-dir .tmp/w-reproduce
.venv/Scripts/python.exe artifacts/evaluation/sine_diagram_recheck_v1/recheck_catalog_context.py --output-dir .tmp/w-catalog
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/sine_diagram_recheck_v1/independent.svg --description-file artifacts/evaluation/sine_diagram_recheck_v1/independent.txt --seed 20261016 --output-dir .tmp/w-plan-b --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/w-archive
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/w-standard
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_sine_diagram_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/w-focused
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
