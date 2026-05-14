# V6 – Iterativer Nachzeichnungsalgorithmus auf Semantik umstellen (v1)

Datum: 2026-05-14

## Ziel

Der bestehende Iterationspfad wird von rein pixel-/geometriegetriebener Optimierung auf eine **mehrzielige semantische Optimierung** umgestellt:

1. Initiale Primitive-Schätzung
2. SVG-Render
3. Fehleranalyse im Pixelraum **und** im Semantikraum
4. Parameter-Update mit gewichteten Zielgrößen
5. Abbruch bei Konvergenz/Stagnation

## Mehrziel-Zielfunktion

Für Iteration `t`:

`L_t = w_geo * L_geo + w_color * L_color + w_sem * L_sem + w_reg * L_reg`

- `L_geo`: Geometriefehler (Masken-IoU, Konturabstand, Keypoint-Offset)
- `L_color`: Farbfehler (DeltaE + Pixel-L1 im Objektmaskenraum)
- `L_sem`: Semantikfehler (Relationsverletzungen, Constraint-Verstöße, fehlende Primitive)
- `L_reg`: Regularisierung (Parameterglättung, Plausibilitätsgrenzen)

Startgewichte (Heuristik v1):

- `w_geo=0.45`
- `w_color=0.20`
- `w_sem=0.30`
- `w_reg=0.05`

## Semantik-Konsistenzscore

`L_sem` wird als gewichtete Summe aus Teilstrafen gerechnet:

- Primitive-Vollständigkeit (fehlende erwartete Primitive)
- Relationstreue (`left_of`, `above`, `touches`, `continues_behind`)
- Occlusion-Konsistenz (Layer-Graph widerspruchsfrei)
- Text-/Label-Konsistenz (falls vorhanden)

Normalisierung auf `[0,1]`, wobei `0` semantisch konsistent bedeutet.

## Update-Strategie pro Iteration

1. **Kandidaten erzeugen**: Lokale Geometrie-, Farb- und Layer-Änderungen
2. **Batch-Evaluierung**: Für alle Kandidaten `L_t` berechnen
3. **Pareto-Filter**: Dominierte Kandidaten verwerfen
4. **Entscheidung**:
   - Primär niedrigstes `L_t`
   - Bei Gleichstand: niedrigeres `L_sem`
5. **Trust-Region**: Schrittweite begrenzen, um Oszillation zu vermeiden

## Konvergenz- und Abbruchkriterien

Abbruch bei einem der folgenden Punkte:

- `ΔL_t < 1e-3` über 3 Iterationen (stabile Konvergenz)
- Maximalrunden erreicht (`max_rounds`, standard 6)
- Stagnation erkannt (kein besserer Pareto-Kandidat in 2 Runden)

## Metriken für Akzeptanz (V6)

Für mindestens 3 Referenzfamilien (z. B. AC0811, AC0812, AC0836):

- Konvergenzplot `L_t` über Iterationen
- Zusätzlich Plot für `L_geo`, `L_color`, `L_sem`
- Reproduzierbare Verbesserung gegenüber Runde 1 in mindestens 2 der 3 Familien
- Keine Zunahme von Semantikverletzungen im Endzustand

## Artefaktstruktur (vorgeschlagen)

- `artifacts/evaluation/semantic_iteration_v1/<run_id>/metrics.json`
- `artifacts/evaluation/semantic_iteration_v1/<run_id>/convergence.csv`
- `artifacts/evaluation/semantic_iteration_v1/<run_id>/plots/*.png`
- `docs/semantic_iteration_v1_<date>_<run_id>_summary.md`

## Reproduzierbarkeit

Pflichtfelder je Run:

- Commit-SHA
- Python-Version
- Seeds
- Verwendete Gewichte (`w_*`)
- Referenzfamilienliste
- Timeout-/Ressourcengrenzen

## Ergebnis

Mit dieser Spezifikation ist V6 als dokumentierter Arbeitsrahmen definiert und direkt in kurze, reproduzierbare Experimentläufe überführbar.
