# ImageConverter CLI

Die primäre CLI wird als Python-Modul gestartet:

```bash
python -m src.imageCompositeConverter --help
```

## Häufige Aufrufe

### Katalogbereich konvertieren

```bash
python -m src.imageCompositeConverter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/converted_images \
  --start AC0000 \
  --end ZZ9999
```

### Einzelne Bereiche annotieren

```bash
python -m src.imageCompositeConverter \
  --mode annotate \
  --output-dir artifacts/annotated_images \
  --start AC0811 \
  --end AC0814
```

## Artefakt- und Log-Pfade

`artifacts/converted_images/` ist für erzeugte Bild-/SVG-/CSV- und Review-Artefakte reserviert. Neue Laufzeitlogs sollen nicht mehr unter `artifacts/converted_images/` abgelegt werden, damit synchronisierte Arbeitskopien wie `myCloud/imageConverter/artifacts/converted_image(s)` keine Logdateien enthalten. Für neue Nachweise bitte stattdessen `artifacts/test-evidence/*.log` verwenden und die zugehörige Zusammenfassung als Markdown daneben ablegen.

### Ein einzelnes Bild konvertieren und als Regression einfrieren

Für das schrittweise Abarbeiten einzelner Bilder gibt es einen dedizierten Wrapper,
der exakt eine Varianten-ID startet, deterministische Reihenfolge erzwingt und
Batch-Einzelfehler als Fehlercode zurückgibt:

```bash
python -m tools.convert_one_image AC0800_L \
  --input-dir artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --output-dir artifacts/one-image-conversions \
  --iterations 64
```

Wenn die Konvertierung visuell abgenommen ist, kann derselbe Lauf die erzeugte
SVG-Datei zusammen mit dem Quellbild in die geschützte Satisfactory-Baseline
kopieren:

```bash
python -m tools.convert_one_image AC0800_L --freeze-baseline
```

`--freeze-baseline` ergänzt `artifacts/regression_baseline/satisfactory/variants.txt`
im Append-Modus. Dadurch prüft `./tools/run_satisfactory_regression_battery.sh`
bei späteren Änderungen automatisch, dass die neu konvertierte Version für alle
bereits eingefrorenen Varianten die gespeicherte `mean_delta2`-Qualität nicht
verschlechtert.
