# Nächstes Arbeitspaket – Telemetrie-Alias-Verifikationsbeleg Run ACF (2026-08-03)

Run ACF setzt den optionalen Folgepunkt aus Run ACE um: Die extern gestartete
No-Override-Verifikation kann nun mit Workflow-Run-ID und Gate-Status dauerhaft
als maschinenlesbarer Beleg protokolliert werden.

## 1) Versionierter Verifikationsbeleg

`tools/record_optimization_telemetry_alias_verification.py` liest das bei der
Promotion erzeugte `recommended-baseline-alias.json`, validiert eine positive
Workflow-Run-ID und einen terminalen Gate-Status und schreibt den Vertrag
`optimization_render_telemetry_alias_verification_v1`. Der Beleg bindet die
Verifikation an Workflow, Dispatch-Eingaben, Baseline-Run, Artefakt und
Source-SHA. `verified` ist ausschließlich für `gate_status=passed` wahr;
Fehlschläge und Abbrüche bleiben damit sichtbar statt fälschlich als Aktivierung
zu gelten.

## 2) Reproduzierbarer Aufruf

Nach der in Run ACE dokumentierten Verifikation wird der Beleg beispielsweise
so erzeugt:

```bash
python tools/record_optimization_telemetry_alias_verification.py \
  recommended-baseline-alias.json \
  telemetry-alias-verification.json \
  --workflow-run-id 123456789 \
  --gate-status passed
```

Zulässige terminale Statuswerte sind `passed`, `failed`, `cancelled` und
`timed_out`. Dadurch kann derselbe Vertrag auch negative Gate-Ausgänge für die
spätere Diagnose festhalten.

## 3) Ergebnis und nächster Schritt

Alias-Aktivierung, No-Override-Dispatch und dessen externes Ergebnis besitzen
jetzt jeweils einen maschinenlesbaren Vertrag. Ein weiterer Repository-Schritt
ist nicht erforderlich; die tatsächliche Aktivierung und Workflow-Ausführung
bleiben bewusst administrative Vorgänge.
