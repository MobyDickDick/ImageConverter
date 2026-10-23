# Nächstes Arbeitspaket – Plan-B AC0732_1_M Run PB (2026-06-12)

## Ziel

Run PB arbeitet den dokumentierten Kandidaten `AC0732_1_M.jpg` vollständig ab.
Das bisherige SVG lag mit `normalized_mse=0.06993533` oberhalb der
Review-Grenze und bildete die beschriebene, nach rechts gedrehte Quadrat-Kelle
mit horizontal bleibendem `P` nicht semantisch ab.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf erkennt auch den Schreibfehler `gredreht` in der
XML-Beschreibung und wählt `non_composite_description_geometry_ir`. Ergebnis:
Exit `0`, dimensionstreues `35x20`-SVG ohne Rastereinbettung.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `13642.634766` | `3317.628662` |
| `normalized_mse` | `0.06993533` | `0.01700694` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `75.68 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Das neue `RightFacingSquareKellePGlyph` modelliert linken horizontalen
Anschluss, roten Quadratgrundkörper und horizontalen P-Glyph als getrennte
SVG-Elemente. Die Erkennung basiert auf der AC072-Referenz, der Rechtsdrehung
und dem horizontalen P-Hinweis; sie toleriert sowohl `gedreht` als auch den im
Quelldatensatz vorhandenen Schreibfehler `gredreht`. Sämtliche Geometrie bleibt
größenrelativ. Regressionstests sichern Erkennung, Rendering, Dimensionen,
Qualitätsgrenze, Elementtrennung und Rasterbildfreiheit.

PF8 bleibt bewusst getrennt: Die aktive Rotation entfernt `AC0732_1_M` und
nimmt `AC0722_1_S` auf. Für die neue kleine T-Kellen-Variante werden noch keine
passenden allgemeinen Rechteck-, Linien- oder Text-Seeds gefunden; die
Entscheidung lautet `noch nicht erkannt`.

## Rotation

Die aktiven Kandidaten sind nun `AC0732_1_L`, `AC0254_2`, `AC0732_1_S`,
`AC0701_1_S` und `AC0722_1_S`.

## 5-Zeilen-Log

- **Getestet:** Reale AC0732-1-M-Re-Konvertierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `75.68 %` auf `3317.628662` gesenkt; `normalized_mse=0.01700694` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; PF8 benötigt weiterhin allgemeine Rechteck-/Linien-/Text-Seeds für diese Symbolfamilie.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0732_1_L.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
