# Nächstes Arbeitspaket – Telemetrie-Alias-Verifikationsgate Run ACG (2026-08-03)

Run ACG macht den in Run ACF eingeführten Verifikationsbeleg als eigenständiges
CI-/Administrationsgate prüfbar. Ein vorhandener Beleg gilt nicht allein wegen
seiner Existenz als erfolgreiche Aktivierung.

## 1) Strikte Bindungs- und Erfolgsprüfung

`tools/check_optimization_telemetry_alias_verification.py` vergleicht den Beleg
mit dem zugehörigen `recommended-baseline-alias.json`. Geprüft werden die beiden
Schema-Versionen, Workflow und Dispatch-Eingaben, Baseline-Run, Artefaktname und
Source-SHA sowie eine positive Verifikations-Run-ID. Nur die konsistente
Kombination `gate_status=passed` und `verified=true` besteht das Gate.

Damit werden insbesondere Belege einer anderen Promotion, manipulierte
Provenienzfelder und fehlgeschlagene oder abgebrochene Workflow-Läufe mit
Exitcode `1` abgewiesen.

## 2) Reproduzierbarer Gate-Aufruf

```bash
python tools/check_optimization_telemetry_alias_verification.py \
  recommended-baseline-alias.json \
  telemetry-alias-verification.json
```

Der Befehl gibt ein kompaktes `PASS` oder `FAIL` aus. Im Fehlerfall folgen alle
gefundenen Abweichungen, damit die administrative Korrektur nicht nur an einem
generischen CI-Fehler endet.

## 3) Ergebnis

Promotion, Aktivierungsrezept, externe No-Override-Verifikation und deren
abschließendes Urteil bilden nun eine durchgehend maschinenlesbare Kette. Die
tatsächliche Aktivierung bleibt wie vorgesehen ein administrativer Vorgang.
