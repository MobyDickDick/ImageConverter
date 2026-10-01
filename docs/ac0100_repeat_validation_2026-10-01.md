# Wiederholungsprüfung AC0010/AC0100 (2026-10-01)

## Anlass

Die in `nextPrompt.txt` beschriebene Aufgabe wurde erneut auf dem aktuellen
Stand ausgeführt. Geprüft wurden das Basissymbol `AC0010` (in der Anfrage als
`AC010` bezeichnet) und die drei real vorhandenen Größenvarianten
`AC0100_L`, `AC0100_M` und `AC0100_S`.

## Ergebnis

Der gemeinsame schwere Regressionstest ist grün. Er konvertiert alle vier
Varianten neu aus Eingabebild und Bildbeschreibung und prüft danach sowohl die
Qualitätsgrenzen als auch den tatsächlich gewählten Erzeugungspfad.

Für jede Variante wurde
`non_composite_elementwise_symbol_fit` verwendet. Weder eine feste Sample-SVG
noch ein Template-Transfer war beteiligt. Damit ist die bereits implementierte
allgemeine Korrektur weiterhin wirksam; eine weitere bildnamenspezifische
Sonderbehandlung ist nicht erforderlich.

Zusätzlich sind die schnellen Renderer- und Non-Composite-Detailtests grün.
Sie sichern insbesondere ab, dass kontinuierliche SVG-Verläufe für die lokale
Qualitätsbewertung rendererkompatibel expandiert werden, ohne die gespeicherte
Konvertierungs-SVG in feste Pixelstreifen umzuwandeln.

## Ausgeführte Prüfungen

```text
PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q \
  tests/detailtests/test_rendering_gradient_compatibility.py \
  tests/detailtests/test_non_composite_runtime_helpers.py \
  -k 'gradient or structured or raster_fit'
# 14 passed, 65 deselected

RUN_HEAVY_CONVERSION_TESTS=1 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
timeout 600 python -m pytest -q \
  tests/test_conversion_regression_smoke.py::test_ac0100_quality_uses_algorithmic_elementwise_fit
# 1 passed
```

## Schlussfolgerung

Die gemeldete Regression ist auf dem aktuellen Stand nicht mehr
reproduzierbar. Der Algorithmus erzeugt die Familie variantenfähig aus Raster
und Beschreibung; die im Repository vorhandenen Samples und früheren
Konvertierungsartefakte dienen in diesem geprüften Pfad nicht als Quelldaten.
