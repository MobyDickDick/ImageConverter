# Nächstes Arbeitspaket – Plan-B AC0701_1_S Run PF (2026-06-12)

## Ziel

Run PF arbeitet den in Run PE dokumentierten Kandidaten `AC0701_1_S.jpg`
vollständig ab. Das bisherige SVG zeigte eine gedrehte Kompressorgeometrie und
lag mit `normalized_mse=0.05935915` oberhalb der Review-Grenze. Die
Bildbeschreibung verlangt stattdessen eine aufrechte Kelle mit Quadrat anstelle
des oberen Kreises.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf erkennt die Beschreibung
`Kelle, aber mit Quadrat anstelle von Kreis oben.` als
`UprightSquareKelleGlyph`. Ergebnis: Exit `0`, ein dimensionstreues `15x25`-SVG
mit getrenntem Quadratgrundkörper und unterem vertikalem Anschluss, ohne
Rastereinbettung.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `11579.485352` | `560.104004` |
| `normalized_mse` | `0.05935915` | `0.00287122` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `95.16 %`.

## Algorithmische Absicherung und Perception-Lerneffekt

Das neue `UprightSquareKelleGlyph` wird allein aus den allgemeinen Begriffen
`Kelle` und `Quadrat` beziehungsweise `Viereck` gewählt, sofern keine Drehung
oder Spiegelung beschrieben ist. Körper und Anschluss verwenden ausschließlich
größenrelative Koordinaten; es werden weder Sample-SVGs noch feste Bilddaten
hinterlegt. Regressionstests sichern Erkennung, Elementtrennung, Dimensionen,
Qualitätsgrenze und Rasterbildfreiheit.

PF8 entfernt `AC0701_1_S` aus der aktiven Rotation. Der vorgeschaltete
Perception-Detektor hatte die Kombination noch nicht als Seed erkannt; die reale
Rekonstruktion belegt nun aber die allgemeine beschreibungsgetriebene
Rechteck-/Linien-Topologie. Deshalb wird kein variantenspezifischer
Perception-Sonderfall ergänzt.

## Rotation

Die aktiven Kandidaten sind nun `AC0722_1_S` und `AC0845_S`. Der
reproduzierbare Review findet derzeit keine weiteren qualifizierten Diff-Fälle
oberhalb der Grenze.

## 5-Zeilen-Log

- **Getestet:** Reale AC0701-1-S-Re-Konvertierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `95.16 %` auf `560.104004` gesenkt; `normalized_mse=0.00287122` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; der qualifizierte Diff-Pool enthält aktuell nur zwei offene Fälle.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0722_1_S.jpg` fortsetzen.
- **Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
