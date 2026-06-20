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
