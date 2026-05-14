# V3 – Farbfüllungen und Verläufe robust modellieren (2026-05-14)

## Ziel
Für den Vision-Track V3 wird eine robuste, maschinenlesbare Modellierung für flächige Füllungen sowie lineare/radiale Verläufe definiert.

## Gradient-Parameterisierung pro Shape

Jede erkannte Form erhält ein `paint`-Objekt mit genau einem der Typen:

- `solid`: flächige Füllung (`rgba`)
- `linear_gradient`: linearer Verlauf mit Start-/Endpunkt in normalisierten Shape-Koordinaten
- `radial_gradient`: radialer Verlauf mit Zentrum, Fokus und Radius in normalisierten Shape-Koordinaten

### JSON-Schema (kompakt)

```json
{
  "shape_id": "AC0836_L#elem_12",
  "paint": {
    "type": "linear_gradient",
    "units": "bbox_normalized",
    "vector": {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0},
    "stops": [
      {"offset": 0.0, "rgba": [24, 24, 24, 255]},
      {"offset": 0.45, "rgba": [128, 128, 128, 255]},
      {"offset": 1.0, "rgba": [240, 240, 240, 255]}
    ],
    "confidence": 0.86
  }
}
```

## DeltaE-/Pixeldelta-Metrik

Für V3 wird eine kombinierte Qualitätsmetrik festgelegt:

- `delta_e_2000_mean` auf den von der Form bedeckten Pixeln
- `delta_e_2000_p95` als robuster Fehlerindikator für harte Übergänge
- `pixel_delta_ratio` als binäre Restabweichung (bestehender Pipeline-Proxy)

Bewertung gegen Flat-Fill-Baseline:

- `improvement_delta_e_mean = baseline_delta_e_mean - gradient_delta_e_mean`
- V3-Ziel erreicht, wenn `improvement_delta_e_mean > 0` und `pixel_delta_ratio` nicht schlechter wird.

## Artefakt-Ausgabe

Die V3-Ausgabe wird unter `artifacts/evaluation/gradient_model_v1/` abgelegt:

- `spec.json` – Parameterisierung und Metriken pro Sample
- `summary.json` – aggregierte Mittelwerte/Perzentile und Baseline-Vergleich

## Reproduzierbarer Auswertungsschritt (Kurzbatch)

1. Sample-Subset mit mindestens 10 Symbolen auswählen (gemischte Schatten/Verläufe).
2. Flat-Fill-Rendering erzeugen und Metriken berechnen.
3. Gradient-Rendering erzeugen und Metriken berechnen.
4. Verbesserungen in `summary.json` protokollieren.

## Ergebnis

Die benötigte Gradient-Parameterisierung pro Shape ist spezifiziert. Damit ist das V3-Deliverable (Modellierung inkl. Stop-Positionen) dokumentiert und in maschinenlesbarer Form vorbereitet.
