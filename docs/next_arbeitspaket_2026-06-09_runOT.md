# Nächstes Arbeitspaket – Plan-B AC0403_1_M Run OT (2026-06-09)

## Ziel

Run OT arbeitet den dokumentierten Kandidaten `AC0403_1_M.jpg` vollständig
ab. Das bisherige SVG lag mit `normalized_mse=0.11117438` oberhalb der
Review-Grenze und bildete die beschriebene Kreis-/Dreieck-Geometrie nicht
passend ab.

## Reale Re-Konvertierung

Der isolierte Ein-Datei-Lauf nutzt die XML-Beschreibung und den regulären
Non-Composite-Pfad. Ergebnis: Exit `0`, dimensionstreues `30x30`-SVG und
Auswahl von `non_composite_description_geometry_ir`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `21687.341797` | `4297.878906` |
| `normalized_mse` | `0.11117438` | `0.02203193` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung beträgt rund `80.18 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Referenzierende AC0251-/AC0401-Familienbeschreibungen werden allgemein als
Pumpensymbol interpretiert. Das Geometry-IR modelliert einen
`CircleBackground` und ein `PumpTriangleGlyph`; die deklarierte
180-Grad-Drehung bestimmt die Dreiecksausrichtung. Die bestehende
Rasterregistrierung passt die normalisierten Primitive an das Bild an. Es
wurden keine AC0403-spezifischen Pixelkoordinaten oder Kandidaten-SVGs im
Algorithmus hinterlegt.

## Rotation

`AC0403_1_M` wurde aus Triage und PF8-Zielen entfernt. Der reproduzierbare
Review füllt mit `AC0733_1_M` auf. Die aktiven Kandidaten sind nun
`AC0150_2`, `AC0253_1`, `AC0551_2_M`, `AC0733_1_L` und `AC0733_1_M`.

## 5-Zeilen-Log

- **Getestet:** Geometry-IR-Tests, isolierter AC0403-1-M-Reallauf, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `80.18 %` auf `4297.878906` gesenkt; `normalized_mse=0.02203193` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; Textprimitive der neu rotierten AC0733-Varianten besitzen noch keinen allgemeinen Seed.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0150_2.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
