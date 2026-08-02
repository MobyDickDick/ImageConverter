# Nächstes Arbeitspaket – Varianten-Deltas der Optimierungs-Telemetrie Run ABU (2026-08-02)

Run ABU setzt den in Run ABT dokumentierten nächsten Schritt um: Der
Baseline-Vergleich weist Render-Timeouts und Renderfehler nicht nur für den
gesamten Batch, sondern auch je betroffener Variante aus.

## 1) Varianten-Vereinigungsmenge

Der Vergleich bildet die Vereinigungsmenge der `affected_variants` aus
Baseline und aktuellem Lauf. Damit bleiben sowohl neu betroffene als auch nur
in der Baseline vorhandene Varianten sichtbar. Variantennamen werden wie bei
der Summary normalisiert und die Ausgabe wird alphabetisch sortiert.

Falls mehrere Ergebniszeilen derselben Variante vorliegen, werden deren Zähler
vor dem Vergleich addiert. Fehlende Varianten erhalten für die betreffende
Seite den Wert null.

## 2) Maschinenlesbarer Vertrag

Das bestehende Artefakt
`optimization_render_telemetry_comparison.json` enthält nun zusätzlich
`variant_deltas`. Jeder Eintrag umfasst den Variantennamen sowie für
`render_timeouts` und `render_errors` jeweils Baseline, aktuellen Wert und die
vorzeichenbehaftete Differenz `current - baseline`.

Fehlerhafte Variantenlisten, leere Variantennamen sowie negative oder nicht
ganzzahlige Variantenzähler werden eindeutig abgelehnt. Ältere gültige
Summaries ohne `affected_variants` bleiben kompatibel und ergeben eine leere
Delta-Liste.

## 3) Regressionstests und nächster Schritt

Die Helper-Tests sichern die Vereinigungsmenge, normalisierte und
deterministische Reihenfolge, positive und negative Varianten-Deltas sowie die
Validierung einzelner Zähler ab.

Als nächstes kann ein optionales maschinenlesbares Gate auf den Varianten-Deltas
aufbauen und einen Lauf bei neu hinzugekommenen Render-Timeouts oder
Renderfehlern gezielt als Regression kennzeichnen.
