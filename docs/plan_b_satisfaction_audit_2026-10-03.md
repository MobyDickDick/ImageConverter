# Plan-B-Zufriedenheitsprüfung (2026-10-03)

## Klare Antwort

**Nein: Die aktuell ausgewählten Plan-B-Resultate sind nach den dokumentierten
Qualitätsgrenzen nicht zufriedenstellend.** Plan B liefert bei einzelnen
historischen Isolationsläufen teils große Verbesserungen, aber „verbessert“ ist
nicht gleich „zufriedenstellend“. Maßgeblich ist das heute aus den vorhandenen
JPEG-/SVG-Paaren reproduzierte Review, nicht ein früherer Zwischenbestwert.

## Reproduzierbarer Review

```bash
PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 \
  python -m tools.review_conversion_quality \
  --output-dir /tmp/plan-b-review-current --max-candidates 5
```

Der Lauf wertete `688` Paare aus und wählte folgende fünf höchsten kompakten
Fehlerfälle. Alle überschreiten sowohl die dokumentierte harte
`mean_delta2 <= 18000`-Grenze als auch die engere Review-Grenze:

| Rang | Variante | mean_delta2 | normalized_mse | Zufriedenstellend |
| ---: | --- | ---: | ---: | :---: |
| 1 | AC0554_2_L | 35769.074219 | 0.183361 | nein |
| 2 | AC0713_1_S | 24899.021484 | 0.127638 | nein |
| 3 | AC0724_1_S | 22276.960938 | 0.114197 | nein |
| 4 | AC0252_1 | 20853.748047 | 0.106901 | nein |
| 5 | AC0731_1_L | 18881.216797 | 0.096790 | nein |

Auch die Review-Grenze ist weiterhin scharf: `GE9021_2M` ist mit
`normalized_mse=0.045639` der letzte passende Fall; `AC0232_M` ist mit
`0.046010` der erste nicht mehr passende Fall.

## Konsequenz

Plan-B-Pakete dürfen künftig nur als **zufriedenstellend** bezeichnet werden,
wenn ein erneuter Review des tatsächlich akzeptierten SVGs das Qualitätsgate
erfüllt. Ein grüner Prozess-Exit, semantisch richtige Primitive oder eine
Verbesserung gegenüber dem Ausgangswert reichen allein nicht. Der nächste
Plan-B-Lauf beginnt mit `AC0554_2_L` und muss Vorher-/Nachher-Werte sowie den
Gate-Status gemeinsam dokumentieren.
