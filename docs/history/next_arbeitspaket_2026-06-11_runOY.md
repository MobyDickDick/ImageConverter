# Nächstes Arbeitspaket – Plan-B AC0733_1_M Run OY (2026-06-11)

## Ziel

Run OY arbeitet den dokumentierten Kandidaten `AC0733_1_M.jpg` vollständig ab.
Das bisherige SVG lag mit `normalized_mse=0.08842208` oberhalb der
Review-Grenze und zeigte nur eine unpassende Kreisfläche. Geprüft wird, ob das
in Run OX eingeführte Quadrat-Kellen-Geometry-IR ohne variantenspezifische
Logik auf die mittlere 20x35-Variante generalisiert.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf verwendet dieselbe XML-Beschreibung und denselben
`RightRotatedSquareKellePGlyph`-Pfad wie `AC0733_1_L`. Ergebnis: Exit `0`,
dimensionstreues `20x35`-SVG und Auswahl von
`non_composite_description_geometry_ir`.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `17248.937500` | `3555.331543` |
| `normalized_mse` | `0.08842208` | `0.01822546` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `79.39 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Es war keine neue Produktions-Sonderfalllogik erforderlich. Anschluss, roter
Quadratgrundkörper und P-Glyph bleiben getrennte SVG-Elemente; der Text wird
nicht rotiert. Die vorhandene Rasterregistrierung passt die größenrelativen
Familienparameter an die mittlere Variante an. Ein neuer Regressionstest hält
Dimensionen, Messwert, Elementtrennung und Rasterbildfreiheit des committed SVG
fest. Damit ist der beschreibungsgetriebene Familienpfad über zwei reale Größen
bestätigt.

PF8 bleibt davon getrennt: Die aktive Rotation entfernt `AC0733_1_M` und nimmt
`AC0254_2` auf. Dort wird bislang nur eine Linie, aber kein allgemeiner
Rechteck-/Rule-Seed gefunden; die Entscheidung lautet `nur Sonderfall`.

## Rotation

Die aktiven Kandidaten sind nun `AC0722_1_L`, `AC0723_1_S`, `AC0732_1_M`,
`AC0732_1_L` und `AC0254_2`.

## 5-Zeilen-Log

- **Getestet:** Reale AC0733-1-M-Re-Konvertierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `79.39 %` auf `3555.331543` gesenkt; `normalized_mse=0.01822546` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; PF8 benötigt weiterhin allgemeine Rechteck-/Text-Seeds für die AC0733-Familie.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0722_1_L.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
