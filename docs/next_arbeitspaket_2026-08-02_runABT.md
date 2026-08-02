# Nächstes Arbeitspaket – Optimierungs-Telemetrie Baseline-Vergleich Run ABT (2026-08-02)

Run ABT setzt den in Run ABS dokumentierten nächsten Schritt um: Die
maschinenlesbare Optimierungs-Telemetrie eines aktuellen Laufs kann mit einer
explizit ausgewählten Batch-Summary verglichen werden.

## 1) Explizite Baseline

Die Umgebungsvariable `ICC_OPTIMIZATION_RENDER_TELEMETRY_BASELINE` wählt die
Baseline-Datei. Ohne diese Variable bleibt der bisherige Abschlusslauf
unverändert und erzeugt keinen Vergleich. Der Konversionsalgorithmus speichert
damit weiterhin keinen laufübergreifenden Zustand.

Ist die Variable gesetzt, liest die Post-Conversion-Finalisierung nach dem
Schreiben der aktuellen `optimization_render_telemetry_summary.json` beide
versionierten Summaries ein. Unbekannte Schemas sowie ungültige negative oder
nicht ganzzahlige Zähler brechen den Vergleich eindeutig ab, statt irreführende
Differenzen zu erzeugen.

## 2) Vergleichsvertrag

Das neue Artefakt `optimization_render_telemetry_comparison.json` verwendet das
Schema `optimization_render_telemetry_comparison_v1`. Für `render_timeouts` und
`render_errors` enthält es jeweils Baseline, aktuellen Wert und die vorzeichenbehaftete
Differenz `current - baseline`. Zusätzlich hält es die explizit gewählte
Baseline- und aktuelle Summary-Datei fest.

Beispiel:

```bash
ICC_OPTIMIZATION_RENDER_TELEMETRY_BASELINE=/path/to/baseline/optimization_render_telemetry_summary.json \
  python -m src.imageCompositeConverter
```

## 3) Regressionstests und nächster Schritt

Helper-Tests sichern positive und negative Differenzen, Pfadmetadaten und die
Ablehnung fremder Schemaversionen. Der Finalisierungstest stellt sicher, dass
der optionale Vergleich unmittelbar nach der aktuellen Summary ausgeführt wird.

Als nächstes kann der Vergleich optional Varianten-Deltas für die Vereinigungsmenge
der in Baseline und aktuellem Lauf betroffenen Varianten ausweisen. So bleibt
neben der Batch-Tendenz auch die Ursache einer Zähleränderung direkt sichtbar.
