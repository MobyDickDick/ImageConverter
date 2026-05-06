# N6 Variation Suite – Run 02 (2026-05-06)

## Anlass

Automatisierbaren Vergleichslauf für die bereits erzeugte N6-Variationssuite ergänzen,
inklusive Qualitätsmetriken pro Szenario.

## Ausgeführter Befehl

```bash
python -m tools.generate_svg_variation_suite \
  --out-dir artifacts/images_to_convert/n6_variations \
  --catalog-csv artifacts/converted_images/reports/n6_variation_catalog.csv \
&& python -m tools.validate_sample_pairs artifacts/images_to_convert/n6_variations \
  --render-missing-jpeg \
  --reference-dir artifacts/images_to_convert/n6_variations \
  --report-csv artifacts/converted_images/reports/n6_variation_metrics_2026-05-06_run02.csv
```

## Ergebnis

- Exit-Code: `0`
- Generierte SVG-Varianten: `6`
- Pair-Validation: `ok`
- Metrik-Report geschrieben: `artifacts/converted_images/reports/n6_variation_metrics_2026-05-06_run02.csv`

## Kurzfazit

Die N6-Szenarien liegen als reproduzierbarer Katalog vor und können nun per
Batch gegen Referenz-JPEGs mit per-Szenario-Metriken (`mean_delta2`) geprüft
werden.
