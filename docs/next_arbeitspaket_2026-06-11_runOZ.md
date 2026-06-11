# Nächstes Arbeitspaket – Plan-B AC0722_1_L Run OZ (2026-06-11)

## Ziel

Run OZ arbeitet den dokumentierten Kandidaten `AC0722_1_L.jpg` vollständig ab.
Das bisherige SVG lag mit `normalized_mse=0.07686921` oberhalb der
Review-Grenze und zeigte einen unpassenden gedrehten Kompressor statt des
links gedrehten Quadrat-Kellen-Symbols mit horizontalem `T`.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf nutzt die XML-Beschreibung und ein neues
größenrelatives `LeftRotatedSquareKelleTGlyph`. Ergebnis: Exit `0`,
dimensionstreues `45x25`-SVG und Auswahl von
`non_composite_description_geometry_ir`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `14995.260742` | `4721.479004` |
| `normalized_mse` | `0.07686921` | `0.02420340` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `68.51 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Das Geometry-IR erkennt die AC0722-Beschreibung über Kelle, Quadrat und
Linksdrehung. Horizontaler Anschluss, roter Quadratgrundkörper und T-Glyph
werden als getrennte SVG-Elemente gerendert; der Text wird nicht rotiert. Alle
Geometrieparameter sind größenrelativ und der allgemeine Non-Composite-Pfad
bevorzugt das semantische Beschreibungs-IR. Regressionstests halten Erkennung,
Rendering, Dimensionen, Messwert, Elementtrennung und Rasterbildfreiheit fest.

PF8 bleibt davon getrennt: Die aktive Rotation entfernt `AC0722_1_L` und nimmt
`AC0732_1_S` auf. Dort wird weiterhin ein Kreis statt allgemeiner Rechteck-,
Linien- und Textprimitive priorisiert; die Entscheidung lautet `noch nicht
erkannt`.

## Rotation

Die aktiven Kandidaten sind nun `AC0723_1_S`, `AC0732_1_M`, `AC0732_1_L`,
`AC0254_2` und `AC0732_1_S`.

## 5-Zeilen-Log

- **Getestet:** Reale AC0722-1-L-Re-Konvertierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `68.51 %` auf `4721.479004` gesenkt; `normalized_mse=0.02420340` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; PF8 benötigt weiterhin allgemeine Rechteck-/Text-Seeds für diese Symbolfamilie.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0723_1_S.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
