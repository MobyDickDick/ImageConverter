# Nächstes Arbeitspaket – CI-Exit für Optimierungs-Telemetrie Run ABW (2026-08-02)

Run ABW setzt den in Run ABV dokumentierten nächsten Schritt um: Die bislang
rein berichtende Gate-Entscheidung kann einen Konverterlauf nun optional mit
einem für CI-Systeme auswertbaren Exitcode beenden.

## 1) Opt-in-CLI-Vertrag

Der strikte Modus wird explizit über die CLI aktiviert und benötigt weiterhin
eine bewusst ausgewählte Baseline:

```bash
ICC_OPTIMIZATION_RENDER_TELEMETRY_BASELINE=/pfad/baseline.json \
python src/imageCompositeConverter.py ... \
  --fail-on-optimization-render-regression
```

Die Option aktiviert intern das in Run ABV eingeführte maschinenlesbare Gate.
Ohne Baseline beendet sich die CLI vor der Konvertierung mit Exitcode 2 und
einer verständlichen Contract-Meldung.

## 2) Exit-Verhalten

Nach einem abgeschlossenen Konvertierungsbatch liest die CLI das erzeugte
`reports/optimization_render_telemetry_comparison.json`. Meldet dessen
`regression_gate.status` den Wert `regression`, endet der Lauf mit Exitcode 1.
Ein bestandener, fehlender oder nicht aktivierter Gate-Eintrag verändert das
bisherige Exit-Verhalten nicht. `--fail-on-batch-failures` bleibt davon
unabhängig.

## 3) Regressionstests und nächster Schritt

Helper-Tests sichern die neue CLI-Option, das Auslesen des Gate-Artefakts und
den Exitcode 1 im Regressionsfall. Als nächstes kann ein CI-Beispielworkflow
die Baseline als Artefakt bereitstellen und den strikten Aufruf in einer
isolierten Pipeline erproben.
