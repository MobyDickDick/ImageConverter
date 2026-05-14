# S1 – Shape-Detection API Spezifikation v1 (2026-05-14)

Diese Spezifikation definiert die erste versionierte API für eine allgemeine Formen-Erkennung
(`circle`, `triangle`, `arrow`, `rectangle`, `line`) inkl. Geometrie, Konfidenz und Farb-/Strichinfos.

## 1) Input

```json
{
  "image": {
    "path": "artifacts/images_to_convert/samples/AC0800.jpeg",
    "format": "jpeg"
  },
  "roi": {
    "x": 0,
    "y": 0,
    "width": 512,
    "height": 512
  },
  "scale": 1.0,
  "options": {
    "detect_colors": true,
    "detect_stroke_width": true,
    "min_confidence": 0.0
  }
}
```

## 2) Output (JSON-Schema, Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://imageconverter.local/schemas/shape-detection-result-v1.json",
  "title": "ShapeDetectionResultV1",
  "type": "object",
  "required": ["api_version", "image", "detections"],
  "properties": {
    "api_version": {"type": "string", "const": "shape-detection-v1"},
    "image": {
      "type": "object",
      "required": ["path", "width", "height"],
      "properties": {
        "path": {"type": "string"},
        "width": {"type": "integer", "minimum": 1},
        "height": {"type": "integer", "minimum": 1}
      },
      "additionalProperties": false
    },
    "detections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["primitive", "bbox", "confidence"],
        "properties": {
          "primitive": {"type": "string", "enum": ["circle", "triangle", "arrow", "rectangle", "line"]},
          "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
          "bbox": {
            "type": "object",
            "required": ["x", "y", "width", "height"],
            "properties": {
              "x": {"type": "number"},
              "y": {"type": "number"},
              "width": {"type": "number", "exclusiveMinimum": 0},
              "height": {"type": "number", "exclusiveMinimum": 0}
            },
            "additionalProperties": false
          },
          "polygon": {
            "type": "array",
            "items": {
              "type": "array",
              "prefixItems": [{"type": "number"}, {"type": "number"}],
              "minItems": 2,
              "maxItems": 2
            }
          },
          "params": {"type": "object"},
          "stroke_width_px": {"type": "number", "minimum": 0},
          "fill_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
          "stroke_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

## 3) Beispielausgaben (10 Referenzbilder)

1. `AC0800.jpeg` → `rectangle`, `line`
2. `AC0814_L.jpeg` → `circle`, `line`
3. `AC0814_M.jpeg` → `circle`, `line`
4. `AC0838_M.jpeg` → `circle`, `line`
5. `AC0VR2_M.jpeg` → `circle`, `triangle`
6. `AC0VR2_AB_M.jpeg` → `circle`, `arrow`
7. `AC0511_L.jpeg` → `rectangle`, `line`
8. `AR0030.jpeg` → `arrow`, `line`
9. `DLG0010.jpeg` → `triangle`, `rectangle`
10. `z_201.jpeg` → `line`

> Hinweis: Die obigen Zeilen sind API-Beispielfälle für die Versionierung und Testfallplanung;
> die konkreten Messwerte (`bbox`, Farben, Breite, Konfidenz) werden in S2–S5 durch Laufdaten belegt.

