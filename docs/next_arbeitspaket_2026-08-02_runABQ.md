# Nächstes Arbeitspaket – getrennte Renderfehler-Telemetrie Run ABQ (2026-08-02)

Run ABQ setzt den in Run ABP dokumentierten nächsten Schritt um: Ein
unendlicher Kandidatenfehler soll erkennen lassen, ob das knappe
Validierungsbudget den Render-Subprozess beendet hat oder ob der Renderer ein
regulär fehlerhaftes Ergebnis geliefert hat.

## 1) Statuskanal des isolierten Renderers

Der Subprozess-Renderer meldet über einen optionalen Callback `timeout` für
`TimeoutExpired` und `error` für Start-, Exitcode-, JSON- und Protokollfehler.
Render-Dispatch und Kompatibilitätswrapper reichen den Kanal gemeinsam mit dem
Per-Call-Timeout weiter. Der bestehende Rückgabevertrag (Bild oder `None`) bleibt
dadurch unverändert.

## 2) Optimierungstelemetrie

Globale Vektorsuche und Farb-Bracketing führen pro Optimierungslauf getrennte
Zähler `render_timeouts` und `render_fehler`. Nur fehlgeschlagene Render werden
gezählt; ein Timeout fällt nicht zusätzlich in den allgemeinen Fehlerzähler.
Die globale Evaluate-Telemetrie gibt beide Werte immer aus. Beim Abbruch des
Farb-Bracketings wegen nicht-finiten Kandidatenfehlern erscheinen sie direkt in
der Abbruchmeldung.

## 3) Regressionstests und nächster Schritt

Helper-Tests sichern die Statusmeldung des Subprozess-Renderers, die getrennte
Zuordnung in beiden Optimierungspfaden und die bisherige Timeout-Weitergabe ab.

Als nächstes kann ein strukturierter Optimierungsreport die beiden Zähler neben
den textuellen Logs in die Iterationsartefakte übernehmen. Damit wären
Budgetengpässe auch ohne Log-Parsing über mehrere Samples aggregierbar.
