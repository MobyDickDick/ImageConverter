# Nächstes Arbeitspaket – Plan-B AC0723_1_S Run PA (2026-06-11)

## Ziel

Run PA arbeitet den dokumentierten Kandidaten `AC0723_1_S.jpg` vollständig ab.
Das bisherige SVG lag mit `normalized_mse=0.07402805` oberhalb der
Review-Grenze und zeigte einen unpassenden gedrehten Kompressor statt der
vertikal gespiegelten Quadrat-Kelle mit oberem Anschluss und horizontalem `T`.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf nutzt die XML-Beschreibung und ein neues
größenrelatives `VerticallyMirroredSquareKelleTGlyph`. Ergebnis: Exit `0`,
dimensionstreues `15x25`-SVG und Auswahl von
`non_composite_description_geometry_ir`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `14441.021484` | `2197.709229` |
| `normalized_mse` | `0.07402805` | `0.01126597` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `84.78 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Das Geometry-IR erkennt die AC0723-Beschreibung über Kelle, Quadrat und
vertikale Spiegelung. Oberer Anschluss, roter Quadratgrundkörper und T-Glyph
werden als getrennte SVG-Elemente gerendert; der Text wird nicht rotiert. Alle
Geometrieparameter sind größenrelativ und der allgemeine Non-Composite-Pfad
bevorzugt das semantische Beschreibungs-IR. Regressionstests halten Erkennung,
Rendering, Dimensionen, Messwert, Elementtrennung und Rasterbildfreiheit fest.

PF8 bleibt davon getrennt: Die aktive Rotation entfernt `AC0723_1_S` und nimmt
`AC0701_1_S` auf. Dort werden bislang keine passenden allgemeinen Rechteck-
oder Linienkandidaten erkannt; die Entscheidung lautet `noch nicht erkannt`.

## Rotation

Die aktiven Kandidaten sind nun `AC0732_1_M`, `AC0732_1_L`, `AC0254_2`,
`AC0732_1_S` und `AC0701_1_S`.

## 5-Zeilen-Log

- **Getestet:** Reale AC0723-1-S-Re-Konvertierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `84.78 %` auf `2197.709229` gesenkt; `normalized_mse=0.01126597` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; PF8 benötigt weiterhin allgemeine Rechteck-/Linien-Seeds für diese Symbolfamilie.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0732_1_M.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
