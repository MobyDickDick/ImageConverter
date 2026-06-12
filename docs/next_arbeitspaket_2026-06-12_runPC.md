# Nächstes Arbeitspaket – Plan-B AC0732_1_L Run PC (2026-06-12)

## Ziel

Run PC arbeitet den in Run PB dokumentierten Kandidaten `AC0732_1_L.jpg`
vollständig ab. Das bisherige SVG lag mit `normalized_mse=0.06552955` oberhalb
der Review-Grenze und bildete die beschriebene, nach rechts gedrehte
Quadrat-Kelle mit horizontal bleibendem `P` nicht semantisch ab.

## Reale Re-Konvertierung

Der reale Non-Composite-Lauf verwendet den bereits allgemeingültigen,
schreibfehlertoleranten AC0732-Pfad `non_composite_description_geometry_ir`.
Er erzeugt ein dimensionstreues `45x25`-SVG ohne Rastereinbettung und registriert
ausschließlich größenrelative Geometrie am Eingabebild.

| Metrik | Vorher | Nachher |
| --- | ---: | ---: |
| `mean_delta2` | `12783.177734` | `6015.989258` |
| `normalized_mse` | `0.06552955` | `0.03083937` |
| Review-Grenze | `0.04594568` | `0.04594568` |

Die Verbesserung des `mean_delta2` beträgt rund `52.94 %`.

## Algorithmische Absicherung und Perception-Lerneffekt

Das vorhandene `RightFacingSquareKellePGlyph` wird unverändert auf die große
Variante angewendet. Anschluss, Quadratgrundkörper und horizontaler P-Glyph
bleiben getrennte SVG-Elemente; weder variantenspezifische Pixelkoordinaten noch
fertige Bilddaten wurden im Algorithmus ergänzt. Ein neuer Regressionstest
sichert Dimensionen, Qualität, Elementtrennung und Rasterbildfreiheit des
committeten Ergebnisses.

PF8 entfernt `AC0732_1_L` aus der aktiven Rotation und nimmt `AC0845_S` auf.
Dort wird der Kreis bereits als allgemeiner `CircleBackground`-Seed mit
Konfidenz `0.914` erkannt; die Entscheidung lautet deshalb `generalisiert`.
Die korrekte zentrierte `rH`-Glyph und das Ausbleiben einer fälschlichen
Außenleitung bleiben Aufgabe des nächsten Plan-B-Pakets.

## Rotation

Die aktiven Kandidaten sind nun `AC0254_2`, `AC0732_1_S`, `AC0701_1_S`,
`AC0722_1_S` und `AC0845_S`.

## 5-Zeilen-Log

- **Getestet:** Reale AC0732-1-L-Re-Konvertierung, Qualitätsreview, PF8-Linkage und Regressionstests.
- **Ergebnis:** `mean_delta2` um `52.94 %` auf `6015.989258` gesenkt; `normalized_mse=0.03083937` liegt unter der Grenze.
- **Blocker:** Kein technischer Blocker; bei `AC0845_S` fehlt im PF8-Vorlauf noch die Text-Glyph-Erkennung.
- **Nächster Schritt:** Die Plan-B-Rotation mit `AC0254_2.jpg` fortsetzen.
- **Startbefehl:** `PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/test_review_conversion_quality.py tests/test_plan_b_perception_linkage.py`.
