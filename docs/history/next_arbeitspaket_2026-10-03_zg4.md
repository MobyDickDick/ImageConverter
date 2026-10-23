# Nächstes Arbeitspaket – ZG4 harte Dimensionstreue (2026-10-03)

Dieses Paket arbeitet nach ZG3 die nächste offene Leitaufgabe aus
`docs/open_tasks.md` ab: **ZG4 – Dimensionstreue als harte Regel erzwingen**.

## Umsetzung

Das Good-Solution-Gate kann mit `--image-dir` und `--svg-dir` die tatsächlichen
Abmessungen des JPEG- und SVG-Artefakts prüfen. Es ermittelt getrennte
Übereinstimmungswerte für Breite, Höhe und Seitenverhältnis. Der kleinste Wert
wird als `dimension_match` in die Gate-Entscheidung übernommen und ersetzt
bewusst einen möglicherweise veralteten Wert aus der Result-Map.

Die Rasterabmessungen werden direkt aus den standardisierten PNG-/JPEG-Headern
gelesen. Das Gate bleibt dadurch auch in der schlanken CI-Testumgebung ohne
optionale Pillow-Installation ausführbar.

Fehlt ein Artefakt oder lässt sich seine Dimension nicht lesen, bleibt die
Pflichtmetrik unbekannt und der Fall wird `not_reachable`. Liegt einer der drei
Werte unter der versionierten ZG3-Schwelle von `0.99`, ist das Ergebnis
mindestens `suboptimal` und kann nicht `good` werden.

```bash
python tools/evaluate_good_solution_gate.py \
  artifacts/converted_images/reports/conversion_result_map.json \
  --image-dir artifacts/images_to_convert \
  --svg-dir artifacts/converted_images/converted_svgs \
  --output /tmp/good_solution_gate_v1.json
```

## Absicherung

Der Regressionstest erzeugt ein Raster mit `40x20` Pixeln und ein absichtlich
falsches SVG mit `40x40` Pixeln. Obwohl die Eingabe-Result-Map fälschlich
`dimension_match=1.0` meldet, klassifiziert das Gate den Fall wegen Höhen- und
Seitenverhältnisabweichung als `suboptimal`. ZG4 ist damit abgeschlossen.
