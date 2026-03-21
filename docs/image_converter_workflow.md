# ImageConverter workflow

Diese Kurzanleitung bündelt die aktuell empfohlenen lokalen Befehle für den
ImageConverter.

## 1. Syntax- und Test-Checks

```bash
python -m compileall src tests
python -m pytest
python -m src.image_composite_converter --help
```

## 2. Interaktive Konvertierung

```bash
python -m src.image_composite_converter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --interactive-range
```

## 3. Regression-Set für AC08

```bash
python -m src.image_composite_converter \
  artifacts/images_to_convert \
  --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml \
  --ac08-regression-set \
  --output-dir artifacts/converted_images
```

## 4. Linux-Vendor-Kommando ausgeben

```bash
python -m src.image_composite_converter --print-linux-vendor-command --vendor-dir vendor
```

## 5. VS Code Debugging unter Windows

- Nutze nach Möglichkeit die Workspace-Launch-Konfiguration
  `ImageConverter: convert interactive range`.
- Falls `debugpy` in der geloggten `Command line` nur den Ordner
  `.venv\\Scripts` startet, ist der Interpreter falsch gewählt. In diesem Fall
  in VS Code explizit `.venv\\Scripts\\python.exe` auswählen.
