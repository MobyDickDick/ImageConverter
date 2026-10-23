# Nächstes Arbeitspaket – Varianten-Gate der Optimierungs-Telemetrie Run ABV (2026-08-02)

Run ABV setzt den in Run ABU dokumentierten nächsten Schritt um: Der
Baseline-Vergleich kann einen Batch anhand der Varianten-Deltas
maschinenlesbar als Regression markieren.

## 1) Opt-in-Vertrag

Das Gate wird nur gemeinsam mit einer expliziten Baseline aktiviert:

```bash
ICC_OPTIMIZATION_RENDER_TELEMETRY_BASELINE=/pfad/baseline.json \
ICC_OPTIMIZATION_RENDER_TELEMETRY_REGRESSION_GATE=1 \
python src/imageCompositeConverter.py ...
```

Als Aktivierungswerte akzeptiert der Runtime-Adapter `1`, `true`, `yes` und
`on` ohne Beachtung der Groß-/Kleinschreibung. Ohne Aktivierung bleibt das
bisherige Comparison-v1-Artefakt unverändert.

## 2) Maschinenlesbares Ergebnis

Bei aktivem Gate erhält
`optimization_render_telemetry_comparison.json` das Objekt
`regression_gate`. Ein positiver Delta-Wert für `render_timeouts` oder
`render_errors` markiert die betreffende Variante als Regression. Das Objekt
enthält den Status `passed` oder `regression`, die Anzahl betroffener Varianten
und eine alphabetisch stabile Liste mit Variante und den regressiven Zählern.
Verbesserungen, unveränderte Zähler und nur aus der Baseline verschwundene
Varianten lassen das Gate passieren.

## 3) Regressionstests und nächster Schritt

Die Helper-Tests sichern kombinierte Timeout-/Fehlerregressionen sowie den
Pass-Fall bei ausschließlich sinkenden Zählern. Als nächstes kann die
maschinenlesbare Gate-Entscheidung optional an den Prozess-Exit oder an einen
CI-Artefakt-Consumer angebunden werden; standardmäßig bleibt sie bewusst rein
berichtend und rückwärtskompatibel.
