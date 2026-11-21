# AC0701_L: Quadrat mit Griff nach unten

Der gemeldete GUI-Lauf brach mit
`DescriptionRejected: logical_object_count:square:1:0` ab. Die aktuelle
Beschreibung wurde bereits als ein Quadrat und eine Linie verstanden.
Der vorhandene spezialisierte Quadrat-/Griff-Fit berücksichtigte nach unten
gerichtete Griffe aber nur bei einer Innenmarkierung. Die allgemeine
Geometry-IR-Anpassung erzeugte stattdessen ein Rechteck; die verbindliche
Quadratprüfung verwarf das Ergebnis.

Der bestehende Quadrat-/Griff-Fit unterstützt jetzt auch unmarkierte vertikale
Varianten. Eine gemeinsame Seitenlänge hält das Quadrat exakt quadratisch;
der Griff bleibt am Mittelpunkt der betreffenden Seite. Die Orientierung wird
vor der Anpassung normalisiert und anschliessend zurücktransformiert. Es
werden keine zusätzlichen Formen erzeugt. Markierte Varianten behalten ihren
bisherigen Anpassungspfad.

Die reguläre Modellfreigabe prüft für diesen Fit zusätzlich die vollständige
Beschreibung, den Pixelvergleich und die Zeichenflächengrenzen. Nur ein tatsächlich
geprüftes Ergebnis erhält den Status `satisfactory`. Die Beschreibung und beide
XML-Tabellen wurden bei dieser Reparatur nicht geändert. Der Produktionscode
enthält keine Bild-ID oder Referenzgeometrie für diesen Fall.

## Ergebnis

Das gespeicherte SVG liegt unter
`artifacts/converted_images/converted_svgs/AC0701_L.svg` und enthält genau ein
Quadrat und eine Linie innerhalb der ursprünglichen 25 × 45 Pixel.

| Prüfung | Gespeichertes SVG | Frischer HTTP-Lauf |
| --- | ---: | ---: |
| Normalisierter Pixelfehler | 0.00020829 | 0.00023624 |
| Vordergrund-IoU | 1.0 | 1.0 |
| Kantenübereinstimmung | 1.0 | 1.0 |
| Qualitätsprüfung | bestanden | bestanden |

`http_summary.json` dokumentiert einen echten frischen Auftrag über den bereits
laufenden Server auf Port 8766, ohne Wiederverwendung des aktuellen SVGs.
`fresh_gui_summary.json` dokumentiert den frischen isolierten GUI-Worker.
`gui_summary.json` dokumentiert die anschliessende erfolgreiche Wiederverwendung
des gespeicherten SVGs. Die reguläre Ablage behält das geringfügig bessere,
bereits gespeicherte Ergebnis. `saved_quality.json` enthält dessen unabhängige
Nachprüfung. `comparison.png` zeigt links das Original, rechts das gespeicherte
SVG, achtfach vergrössert.

Für diese Reparatur war kein Serverneustart notwendig: Der bestehende Server
startet für einen neuen Auftrag einen neuen Konvertierungsprozess und liest
dabei den geänderten Fit ein.

## Prüfungen

**230 Tests bestanden:** 108 Prüfungen für Quadrat-/Griff-Varianten sowie
122 bestehende Prüfungen für Beschreibungssprache, verworfene Vorlagen,
Grundformen, Zeichenflächengrenzen und das Zweiwegventil. Neue Tests verwenden
zusätzlich unabhängige Geometrien, verschiedene Grautöne, Subpixelpositionen und
Auflösungen. Fehlende Griffe, zusätzliche Formen, Innenmarkierungen,
versetzte Griffe und rechteckige Grundkörper erhalten keine Qualitätsfreigabe.
Der echte GUI-Start wird sowohl ohne Vorlage als auch mit unpassender Vorlage
unter neutralem Dateinamen geprüft.

```powershell
$env:PYTHONPATH='.'
.venv/Scripts/python.exe artifacts/evaluation/ac0701_square_handle_2026-11-21/run_gui.py --fresh
.venv/Scripts/python.exe artifacts/evaluation/ac0701_square_handle_2026-11-21/run_gui.py
.venv/Scripts/python.exe artifacts/evaluation/ac0701_square_handle_2026-11-21/run_http.py
.venv/Scripts/python.exe -m pytest tests/test_plain_vertical_square_stem.py tests/test_right_stem_square_runtime.py tests/test_bottom_stem_marked_square_runtime.py tests/test_top_stem_marked_square_runtime.py tests/test_left_stem_marked_square_runtime.py tests/test_marked_square_runtime.py -q
.venv/Scripts/python.exe -m pytest tests/test_description_language.py tests/test_sample_start_regression.py tests/test_simple_form_representation.py tests/test_canvas_containment.py tests/test_two_way_valve_description.py -q
.venv/Scripts/python.exe tools/check_no_new_image_id_hardcoding.py
```

Die Nullprüfung für Bild-ID-Sonderfälle und die Whitespace-Prüfung der hier
geänderten Code- und README-Dateien bestehen. Die vollständige Arbeitskopie
enthält bereits andere Änderungen; ihre Whitespace-Meldungen in `AC0152_M.svg`
wurden nicht mit dieser Reparatur vermischt.
