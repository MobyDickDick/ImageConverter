# Nächstes Arbeitspaket – Plan-B AC0732_1_S Run PE (2026-06-12)

## Ziel

Run PE arbeitet den in Run PD dokumentierten Kandidaten `AC0732_1_S.jpg`
vollständig ab. Das bisherige SVG enthielt keine semantischen Elemente und lag
mit `normalized_mse=0.06000391` oberhalb der Review-Grenze. Zu prüfen war, ob
das bereits an L und M bestätigte AC0732-Geometry-IR auch auf der nur `25x15`
Pixel großen Variante verallgemeinert.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf erkennt die schreibfehlerhafte Beschreibung
`Wie AC072, aber nach rechts gredreht, Text immer noch horizontal "P"` und
verwendet `non_composite_description_geometry_ir`. Ergebnis: Exit `0`, ein
dimensionstreues `25x15`-SVG und drei getrennte Vektorelemente ohne
Rastereinbettung.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `11705.263672` | `3659.341309` |
| `normalized_mse` | `0.06000391` | `0.01875864` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `68.74 %`.

## Algorithmische Absicherung und Perception-Lerneffekt

Das vorhandene `RightFacingSquareKellePGlyph` wird unverändert auf die kleine
Variante angewendet. Linker Anschluss, roter Quadratgrundkörper und horizontaler
P-Glyph bleiben getrennt; sämtliche Koordinaten sind größenrelativ. Ein neuer
Regressionstest sichert Dimensionen, Qualität, Elementtrennung, horizontale
Textausrichtung und Rasterbildfreiheit des committeten Ergebnisses.

PF8 entfernt `AC0732_1_S` aus der aktiven Rotation. Die vorgelagerte
Perception-Pipeline liefert für die vollständige Rechteck-/Linien-/Textfrage
noch keine passenden Seeds, doch der reale beschreibungsgetriebene
Geometry-IR-Pfad ist nun für S, M und L belegt. Deshalb wird kein künstlicher
variantenspezifischer Perception-Sonderfall ergänzt.

## Rotation

Die aktiven Kandidaten sind nun `AC0701_1_S`, `AC0722_1_S` und `AC0845_S`.
Der reproduzierbare Review findet derzeit keine weiteren qualifizierten
Diff-Fälle oberhalb der Grenze.

## 5-Zeilen-Log

- **Getestet:** Reale AC0732-1-S-Re-Konvertierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `68.74 %` auf `3659.341309` gesenkt; `normalized_mse=0.01875864` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; der qualifizierte Diff-Pool enthält aktuell nur drei offene Fälle.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0701_1_S.jpg` fortsetzen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
