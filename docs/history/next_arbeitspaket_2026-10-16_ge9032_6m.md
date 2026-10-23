# Arbeitspaket – T-Verzweigung mit Schaft nach rechts (2026-10-16)

Branch: `codex/ge9032-quality-2026-10-16`, Basis `3818f05cd`.
`GE9032_6M` ist der nach GE0305 dokumentierte nächste reguläre Kandidat.
Alle 14 Farb-/Größenvarianten bestehen beide unveränderten regulären Gates
und die strengeren Plan-B-Pixelgrenzen ohne Pflichtmetrikregression.

## Quellen und allgemeiner Algorithmus

Die Raster zeigen einen senkrechten Balken mit mittig nach rechts
anschließendem waagerechtem Schaft. Beide Arme sind verbunden und besitzen
quer zu ihrer Längsrichtung einen Farbverlauf mit heller Mitte und dunkleren
Rändern. Die gemeinsame Beschreibung „hellgraues Quadrat“ war falsch.
Beide XML-Kataloge beschreiben nun eigenständig die tatsächliche T-Struktur.
Ursprünglicher Text, Quellhashes und Abmessungen aller Varianten bleiben im
`source_inventory.json` erhalten. Kein Quellraster wurde verändert.

Die vorhandene allgemeine Richtungsnormalisierung verarbeitet diese
Schaftrichtung bereits. Zwei unabhängige Probleme erfordern eine Korrektur:
JPEG-Ringing verbreitert bei der mittleren grauen Variante unmittelbar neben
dem Balken eine einzelne Schaftzeile. Die Uniformitätsprüfung misst jetzt,
wie das Farbprofil, außerhalb dieser Übergangszeile. Die vollständige
Silhouette, Außenreste und Innenabweichungen werden weiterhin geprüft;
zusätzliche Elemente und Löcher bleiben Ablehnungsfälle.

Zwei unabhängige Subpixelvarianten decken außerdem auf, dass Canny-Kanten bei
quantisierten Farbverlaufskanten nicht invariant unter Vierteldrehungen sind.
Der Registrierer misst die endgültige Kontur in der ursprünglichen
Bildrichtung. Unterschreitet sie die unveränderte Grenze 0,72, folgt eine
zusätzliche begrenzte Suche mit Kantenbewertung im ursprünglichen Bildrahmen.
Sie ersetzt das Ergebnis nur bei besserer tatsächlicher Konturübereinstimmung;
der gerenderte Startkandidat bleibt dieselbe harte Produktionsfehlerobergrenze.
Bereits ausreichende Registrierungen behalten ihre ursprünglichen Vektoren.

Das SVG enthält einen weißen Hintergrund, ein Rechteck, ein fünfeckiges
Schaftpolygon mit Gehrungsübergang und zwei native lineare Farbverläufe.
Die Runtime erhält nur Raster und Beschreibung, ohne Bildkennungen,
Katalogmaße oder Referenz-SVGs. Die Registrierung ist für T-Verzweigungen in
allen vier Hauptrichtungen `generalisiert`. Andere Topologien und zusätzliche
Innenzeichen gehören nicht zu dieser Abnahme.

## Echte CLI-Abnahme und unabhängige Fälle

Die echte neutrale CLI-Baseline mit ursprünglicher Beschreibung wurde vor der
Runtime-Änderung eingefroren. Der Abnahmelauf verwendet frische Wegwerfkopien
für beide Seiten und reproduziert sämtliche eingefrorenen Baselines bytegenau.
Die ursprüngliche Quadratbeschreibung aktiviert den T-Registrierer nicht.
Im vollständigen ursprünglichen und geänderten XML-Katalog bestehen die
echten Dateinamen ihre eigene Vorher-/Nachher-Abnahme; alle finalen Vektoren
sind bytegleich zur neutralen Ausgabe. Verbotene SVG-Lesezugriffe: null.
Gespeicherte SVGs werden erneut mit dem Produktionsrenderer vermessen.
Eine getrennte richtungsabhängige Semantikprüfung kontrolliert T-Geometrie,
Verbindung, Gehrung, native Gradienten und hellere Profilmitten.

| Quelle | Mean-Delta² vorher | Mean-Delta² nachher |
|---|---:|---:|
| GE9032_6M | 9501.930664 | 97.358749 |
| GE9032_1M | 7218.884277 | 109.613129 |
| GE9032_1S | 4958.877441 | 89.610001 |
| GE9032_2M | 6853.910645 | 133.306870 |
| GE9032_2S | 4760.750000 | 77.952499 |
| GE9032_3M | 4688.806152 | 75.356247 |
| GE9032_3S | 2215.780029 | 60.970001 |
| GE9032_4M | 2849.294434 | 52.542500 |
| GE9032_4S | 1813.619995 | 31.105000 |
| GE9032_5M | 5397.437012 | 59.326874 |
| GE9032_5S | 3984.667480 | 65.364998 |
| GE9032_6S | 6733.667480 | 104.105003 |
| GE9032_7M | 4729.069824 | 47.025623 |
| GE9032_7S | 3121.537598 | 63.097500 |

Die unabhängig konstruierte violette Vorlage verändert Zeichenfläche, Lage,
Proportionen und Palette. Zwei echte CLI-Läufe mit Seed `20261016` bestehen
jeweils **17/17** Fälle. Der Verifikator prüft Eingangs-/Ausgangshashes,
gespeicherte Metriken und Gateentscheidungen sowie die Gleichheit beider Läufe.
45 neue direkte Tests prüfen die komplette Katalogfamilie, alle unabhängigen
Verschiebungen, halbe und doppelte Auflösung, andere Farben, falsche und
widersprüchliche Beschreibungen, fehlende Arme, zusätzliche Punkte, Löcher
und flache Verläufe. Die bisherigen Richtungs- und T-Tests bleiben erhalten.

Diagnosen unter `.tmp/rjr*`, `.tmp/rjfix*`, `.tmp/rjfit*` und `.tmp/rjp1`
bleiben erhalten. Die ersten Läufe bestehen die Abnahme nicht: die graue
Variante fällt aus der Registrierung, zwei unabhängige Varianten verfehlen
die Konturgrenze. Eine zunächst durchgängig angewandte Kantenkorrektur
verändert auch bereits ausreichende Vektoren; die finale zusätzliche Suche
wird deshalb nur bei unzureichender Kontur gestartet. Die finale neutrale
CLI-Abnahme liegt unter `.tmp/rjr3`, die unabhängigen Läufe unter `.tmp/rjp3`
und `.tmp/rjp4`. Frühere Diagnosen zählen nicht als bestandene Abnahme.

## Bestandsschutz und nächste Rotation

Die Erfolgsübersicht enthält 320 Paare; alle 306 bisherigen Indexeinträge
bleiben unverändert. Die vollständige Standardsammlung besteht mit **3.117 bestandenen Tests, 30 bestehenden Skips und null Fehlern**.
Alle 3.147 gesammelten Testknoten sind genau einmal nachgewiesen.
Die erneute Archivkonvertierung besteht mit **320/320**; alle 306 bisherigen
Prüfdatensätze und die 22 bekannten älteren Kompatibilitätsabweichungen
bleiben unverändert. Die schweren AC08-/AC0100-Smoke-Tests bestehen mit **2/2**.
Abschlusszahlen und Artefakthashes stehen in
`artifacts/evaluation/right_gradient_junction_recheck_v1/validation_2026-10-16.json`.
Der Review enthält unverändert 1.000 Einträge und 993 renderbare Paare;
alle 48 bisherigen Bestenlisteneinträge bleiben unter der unveränderten Grenze.
Ausschließlich die 14 abgenommenen GE9032-Varianten sind zusätzlich
ausgeschlossen. Die nächste reguläre Rotation lautet `AC0414_2_L`,
`GE9033_6M`, `AC0424_2_M`, `AC0840_S`, `AC0840_M`.
Bestehende offene Aufgaben bleiben erhalten.

## Reproduktion

CLI-Abnahmen benötigen frische Ausgabeverzeichnisse. Kurze Pfade vermeiden
die bereits dokumentierten Windows-I/O-Probleme langer Archivpfade.

```powershell
$env:IMAGE_CONVERTER_ISOLATE_SVG_RENDER = '0'
.venv/Scripts/python.exe artifacts/evaluation/right_gradient_junction_recheck_v1/verify_evidence.py
.venv/Scripts/python.exe -m tools.run_gradient_junction_recheck artifacts/evaluation/right_gradient_junction_recheck_v1/manifest.json --output-dir .tmp/r-reproduce
.venv/Scripts/python.exe artifacts/evaluation/right_gradient_junction_recheck_v1/recheck_catalog_context.py --output-dir .tmp/r-catalog
.venv/Scripts/python.exe -m tools.run_plan_b_variations --svg artifacts/evaluation/right_gradient_junction_recheck_v1/independent.svg --description-file artifacts/evaluation/right_gradient_junction_recheck_v1/independent.txt --seed 20261016 --output-dir .tmp/r-plan-b --keep-debug-artifacts
.venv/Scripts/python.exe artifacts/evaluation/labeled_disk_recheck_v1/recheck_archive_families.py --output-dir .tmp/r-archive
.venv/Scripts/python.exe artifacts/evaluation/spiral_disk_recheck_v1/run_standard_profile.py --output-dir .tmp/r-standard
$env:RUN_HEAVY_CONVERSION_TESTS = '1'
.venv/Scripts/python.exe -m pytest -q tests/test_right_gradient_junction_family.py tests/test_gradient_junction_runtime.py tests/test_side_gradient_junction_runtime.py tests/test_conversion_regression_smoke.py --basetemp .tmp/r-focused
.venv/Scripts/python.exe -m compileall -q src tests tools
.venv/Scripts/python.exe -m src.imageCompositeConverter --help
.venv/Scripts/python.exe -m tools.check_no_new_image_id_hardcoding
git -c core.whitespace=cr-at-eol diff --check
```
