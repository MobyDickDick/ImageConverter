# Nächstes Arbeitspaket – Plan-B AC0254_2 Run PD (2026-06-12)

## Ziel

Run PD arbeitet den in Run PC dokumentierten Kandidaten `AC0254_2.jpg`
vollständig ab. Das bisherige SVG bestand nur aus einer grünen Ellipse und lag
mit `normalized_mse=0.06059016` oberhalb der Review-Grenze. Die Sichtprüfung
korrigiert außerdem die bisherige Triage-Annahme einer rechteckigen Klappe: Das
Raster zeigt einen grünen Kreisgrundkörper mit einem nach links gerichteten,
hellen dreieckigen Schließblatt.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf erkennt die Beschreibung
`Wie AC0521, aber nach links gedreht` als
`LeftRotatedCircularDamperGlyph` und wählt
`non_composite_description_geometry_ir`. Ergebnis: Exit `0`, ein
dimensionstreues `31x31`-SVG und zwei getrennte Vektorprimitive ohne
Rastereinbettung.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `11819.625000` | `587.050964` |
| `normalized_mse` | `0.06059016` | `0.00300936` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `95.03 %`.

## Algorithmische Umsetzung und Perception-Lerneffekt

Das neue Geometry-IR modelliert Kreisgrundkörper und dreieckiges Schließblatt
als semantisch getrennte Elemente mit größenrelativen Koordinaten. Die
allgemeine Geometry-IR-Rasterregistrierung berücksichtigt nun auch
`blade_points`, sodass globale Translation und Skalierung die gesamte Topologie
gemeinsam transformieren. Es wurden weder feste Bilddaten noch eine
variantenspezifische SVG-Vorlage eingebettet.

PF8 hatte für die frühere Rechteck-/Linienfrage lediglich eine Hough-Linie
gefunden und `nur Sonderfall` entschieden. Die Sichtprüfung zeigt, dass diese
Frage von einer falschen Topologieannahme ausging. Run PD dokumentiert deshalb
den Lerneffekt, ohne einen unzutreffenden allgemeinen Rechteck-Seed zu
erzwingen, und entfernt den abgeschlossenen Fall aus dem aktiven Linkage.

## Rotation

Die aktiven Kandidaten sind nun `AC0732_1_S`, `AC0701_1_S`, `AC0722_1_S` und
`AC0845_S`. Der reproduzierbare Review findet derzeit keinen fünften
qualifizierten Diff-Fall oberhalb der Grenze.

## 5-Zeilen-Log

- **Getestet:** Reale AC0254-2-Re-Konvertierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `95.03 %` auf `587.050964` gesenkt; `normalized_mse=0.00300936` liegt deutlich unter der Grenze.
- **Blocker:** Kein technischer Blocker; der qualifizierte Diff-Pool enthält aktuell nur vier offene Fälle.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0732_1_S.jpg` fortsetzen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
