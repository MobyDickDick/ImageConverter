# Nächstes Arbeitspaket – Plan-B AC0722_1_S Run PG (2026-06-12)

## Ziel

Run PG arbeitet den in Run PF dokumentierten Kandidaten `AC0722_1_S.jpg`
vollständig ab. Das bisherige SVG zeigte weiterhin einen gedrehten Kreis und
lag mit `normalized_mse=0.05681223` oberhalb der Review-Grenze. Die
Bildbeschreibung verlangt die kleine links gedrehte Quadrat-Kelle mit
horizontal bleibendem T-Glyph.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf nutzt das bereits für `AC0722_1_L` eingeführte
`LeftRotatedSquareKelleTGlyph`. Die allgemeine Rasterregistrierung transformiert
nun neben Anschluss und Text auch `body_bbox`-Rechtecke. Ergebnis: Exit `0`, ein
dimensionstreues `25x15`-SVG mit getrenntem Anschluss, Quadratgrundkörper und
T-Glyph ohne Rastereinbettung.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `11082.645508` | `2729.645264` |
| `normalized_mse` | `0.05681223` | `0.01399280` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `75.37 %`.

## Algorithmische Absicherung und Perception-Lerneffekt

Die Registrierung behandelt `body_bbox` nun wie das bereits unterstützte
allgemeine `bbox`: Ursprung, Breite und Höhe werden durch dieselbe globale,
strukturwahrende Transformation angepasst. Damit skaliert die gemeinsame
AC0722-Topologie auf kleine Raster, ohne variantenspezifische Koordinaten oder
Sample-SVGs einzuführen. Tests sichern die Transformation sowie Dimensionen,
Qualitätsgrenze, Elementtrennung und Rasterbildfreiheit der realen Variante.

PF8 entfernt `AC0722_1_S` aus der aktiven Rotation. Die erfolgreiche reale
Rekonstruktion bestätigt den generalisierten beschreibungsgetriebenen
Rechteck-/Linien-/Text-Pfad; ein variantenspezifischer Perception-Sonderfall ist
nicht erforderlich.

## Rotation

Der einzige aktive Kandidat ist nun `AC0845_S`. Der reproduzierbare Review
findet derzeit keinen weiteren qualifizierten Diff-Fall oberhalb der Grenze.

## 5-Zeilen-Log

- **Getestet:** Reale AC0722-1-S-Re-Konvertierung, allgemeine `body_bbox`-Registrierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `75.37 %` auf `2729.645264` gesenkt; `normalized_mse=0.01399280` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; der qualifizierte Diff-Pool enthält aktuell nur einen offenen Fall.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0845_S.jpg` fortsetzen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
