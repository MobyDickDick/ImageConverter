# Nächstes Arbeitspaket – CI-Beispiel für Optimierungs-Telemetrie Run ABX (2026-08-03)

Run ABX setzt den in Run ABW dokumentierten nächsten Schritt um: Ein isolierter,
manuell startbarer GitHub-Actions-Workflow stellt die Telemetrie-Baseline als
Artefakt bereit und erprobt den strikten Konverteraufruf in einem nachgelagerten
Job.

## 1) Isolierter Workflow

Der Workflow `Optimization render telemetry gate example` läuft ausschließlich
über `workflow_dispatch`. Damit bleibt das Beispiel von den regulären lokalen
Abschluss- und Katalogjobs getrennt und kann bewusst über die Actions-Oberfläche
gestartet werden.

Der Job `publish-baseline` erzeugt eine minimale Summary-v1-Baseline ohne
Timeouts oder Renderfehler und veröffentlicht sie für einen Tag unter dem
Artefaktnamen `optimization-render-telemetry-baseline`.

## 2) Strikter Konverteraufruf

`strict-converter-call` lädt das Baseline-Artefakt in einen eigenen Job und
übergibt dessen Pfad über `ICC_OPTIMIZATION_RENDER_TELEMETRY_BASELINE`. Der
Konverter wird mit `--fail-on-optimization-render-regression` auf einer leeren,
deterministischen Sentinel-Auswahl gestartet. Dadurch prüft der Workflow den
vollständigen CLI-, Finalisierungs-, Comparison- und Exitcode-Vertrag, ohne
einen teuren Katalog- oder Renderlauf auszulösen.

Nach dem Lauf wird zusätzlich geprüft, dass das erzeugte Comparison-Artefakt
`regression_gate.status=passed` enthält. Die Reports werden auch zur Diagnose
eines fehlgeschlagenen Laufs als eigenes Workflow-Artefakt hochgeladen.

## 3) Nächster Schritt

Das Beispiel hält die Baseline absichtlich synthetisch und reproduzierbar. Ein
späteres Arbeitspaket kann für einen produktiven Katalog-Shard die Baseline aus
einem freigegebenen Referenzlauf beziehen und dessen Report-Artefakt über einen
expliziten Promote-Schritt versionieren.
