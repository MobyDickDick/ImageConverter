# V2 – Bezierkurven-Erkennung ergänzen (2026-05-14)

## Ziel
Für konturbasierte Formen sollen quadratische und kubische Beziersegmente robust aus Rasterkonturen geschätzt werden, damit die Rekonstruktion weniger Polylinien-Artefakte zeigt.

## Fitting-Strategie

1. **Konturextraktion**
   - Binärmaske je zusammenhängender Form ableiten.
   - Konturen mit Subpixel-Glättung samplen.
2. **Segmentierung in monotone Teilstücke**
   - Krümmungssignatur pro Punkt bestimmen.
   - Segmentgrenzen an Krümmungsnulldurchgängen und starken Richtungswechseln setzen.
3. **Modellwahl (quad vs. cubic)**
   - Start mit quadratischem Fit.
   - Falls Fehlergrenzen überschritten werden, auf kubisch eskalieren.
4. **Least-Squares-Fit im Kurvenraum**
   - Kontrollpunkte über gewichtete kleinste Quadrate schätzen.
   - Endpunkte hart fixieren; Tangenten weich regularisieren.
5. **Adaptive Rekursion**
   - Bei verbleibendem Fehler Segment halbieren und pro Teilsegment erneut fitten.

## Fehlerschranke

Es werden zwei Grenzwerte parallel geführt:

- **Pixelraum-Fehler** (`max_pixel_error`, `mean_pixel_error`)
  - Distanz jedes Konturpunkts zur gerenderten Bezier.
  - Akzeptanzgrenze (Startwert):
    - `max_pixel_error <= 1.50 px`
    - `mean_pixel_error <= 0.45 px`
- **Kurvenraum-Fehler** (`hausdorff_curve_error`)
  - Symmetrische Hausdorff-Distanz zwischen Konturpolyline und Bezier-Sampling.
  - Akzeptanzgrenze (Startwert):
    - `hausdorff_curve_error <= 1.20 px`

Ein Segment gilt als „fit_ok“, wenn **alle** drei Grenzwerte eingehalten sind.

## Ausgabeformat (V2-Erweiterung)

Pro erkanntem Kurvensegment wird folgendes JSON-Objekt erwartet:

```json
{
  "type": "bezier",
  "order": 2,
  "p0": [12.4, 8.1],
  "p1": [16.9, 9.7],
  "p2": [21.2, 14.4],
  "confidence": 0.91,
  "fit_error": {
    "max_pixel_error": 1.03,
    "mean_pixel_error": 0.31,
    "hausdorff_curve_error": 0.88
  }
}
```

`order=2` steht für quadratisch, `order=3` für kubisch.

## Evaluationsprotokoll (für nächste Läufe)

- Testfamilien mit hoher Kurvenlast zuerst: `AC08`, `GE90xx`.
- Vergleich gegen Flat-Polyline-Baseline:
  - Restabweichung (Delta2)
  - Anzahl Segmente pro Kontur
  - Anteil „fit_ok“-Segmente

## Abnahmekriterium V2

V2 gilt als erfüllt, wenn für die kurvenlastigen Referenzen:

1. die mittlere Restabweichung gegenüber der Polyline-Baseline sinkt,
2. mindestens 80% der Beziersegmente `fit_ok` sind,
3. und die rekonstruierten SVGs visuell weniger Zackenartefakte zeigen.
