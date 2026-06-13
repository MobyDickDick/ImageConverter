# Nächstes Arbeitspaket – Plan-B AC0845_S Run PH (2026-06-12)

## Ziel

Run PH arbeitet den in Run PG dokumentierten letzten Kandidaten `AC0845_S.jpg`
vollständig ab. Das bisherige SVG enthielt eine falsche Außenleitung, keinen
`rH`-Glyph und lag mit `normalized_mse=0.04927739` oberhalb der Review-Grenze.
Die Bildbeschreibung fordert einen grauen Kreisring mit zentriertem `rH` und
ausdrücklich keinen Anschluss außerhalb des Kreises.

## Reale Re-Konvertierung

Die Reflection leitet das ausreichend beschriebene AC08-Symbol in den
Non-Composite-Geometry-IR-Pfad. Das neue allgemeine Muster erzeugt einen
`CircleBackground` und einen referenzierten `TextGlyph`; die bestehende
Rasterregistrierung passt Kreis und Text gemeinsam an das `15x15`-Raster an.
Der reale Lauf endet mit Exit `0` und erzeugt ein dimensionstreues SVG ohne
Rastereinbettung oder Außenleitung.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `9612.787109` | `6536.853516` |
| `normalized_mse` | `0.04927739` | `0.03350944` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `32.00 %`.

## Algorithmische Absicherung und Perception-Lerneffekt

Die Erkennung basiert auf den semantischen Merkmalen Kreis/Kreisring, dem
expliziten `rH`-Text und dem Ausschluss einer äußeren Griff-/Leitungslinie. Sie
ist weder an den Dateinamen noch an feste Pixelkoordinaten gebunden. Tests
sichern IR-Aufbau, Rendering, Reflection-Routing, reale Qualitätsgrenze,
Elementtrennung und Rasterbildfreiheit.

PF8 hatte den allgemeinen Kreis bereits erkannt. Der Glyph wird aus der
Beschreibung als `TextGlyph` ergänzt; hierfür ist kein variantenspezifischer
Perception-Sonderfall und kein Sample-SVG nötig.

## Rotation

`AC0845_S` ist aus Triage und PF8-Linkage entfernt. Der reproduzierbare Review
findet aktuell keinen qualifizierten Diff-Fall oberhalb der Grenze; die Rotation
ist damit vorläufig vollständig abgearbeitet.

## 5-Zeilen-Log

- **Getestet:** Reale AC0845-S-Re-Konvertierung, Geometry-IR-Aufbau und -Rendering, Reflection-Routing, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `32.00 %` auf `6536.853516` gesenkt; `normalized_mse=0.03350944` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; aktuell ist kein weiterer Kandidat qualifiziert.
- **Nächster Schritt:** Rotation pausieren und bei einem neu qualifizierten Review-Fall fortsetzen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_image_composite_converter.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
