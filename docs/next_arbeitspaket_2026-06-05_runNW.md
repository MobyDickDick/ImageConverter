# Nächstes Arbeitspaket – FP-D12 Run NW (2026-06-05)

## Ziel

FP-D12 fährt das in FP-D11 vorbereitete Release-Kandidaten-Gate hart erneut und
wendet die Regel **„No silent regression“** strikt an. Zulässiges Ergebnis ist
entweder ein vollständiges `PASS` oder ein explizites `FAIL` mit konkretem
Recovery-Plan.

## Absicherung gegen stumme Regressionen

Der Gate-Runner verwirft vor dem AC08-Smoke das komplette konfigurierte
Output-Verzeichnis und legt es frisch an. Dadurch kann ein abgebrochener Smoke
keine alte, grüne `ac08_success_metrics.csv` an das nachgelagerte Qualitätsgate
weiterreichen.

Zusätzlich ist das AC08-Zeitbudget nun über
`RC_GATE_AC08_TIMEOUT_SECONDS` konfigurierbar und beträgt standardmäßig 900
Sekunden. Das Work-Package-Label kann über `RC_GATE_WORK_PACKAGE` gesetzt werden;
der Standard ist `FP-D12`.

Ein Regressionstest legt bewusst eine alte vollständig grüne Metrics-Datei an,
lässt danach den Smoke mit Exit `124` abbrechen und belegt:

- die alte Metrics-Datei wurde entfernt,
- `ac08-smoke` wird als `BLOCKER` klassifiziert,
- `quality-gate` wird wegen fehlender neuer Metrics ebenfalls als `BLOCKER`
  klassifiziert.

## Harter Gate-Lauf

Ausgeführt wurde:

```bash
RC_GATE_NAME=fp-d12-run-nw \
RC_GATE_OUTPUT_DIR=/tmp/ic-fpd12-ac08 \
RC_GATE_AC08_TIMEOUT_SECONDS=900 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
PYENV_VERSION=3.10.20 \
./tools/run_release_candidate_gate.sh
```

| Schritt | Exit | Klassifikation | Ergebnis |
| --- | ---: | --- | --- |
| Kernsuite | `0` | `PASS` | `703 passed in 51.17s` |
| AC08-Smoke | `124` | `BLOCKER` | Timeout nach 900s; sechs Varianten erzeugt, aber keine vollständige Report-/Metrics-Kette. |
| Qualitätsgate | `1` | `BLOCKER` | Neue `ac08_success_metrics.csv` fehlt; keine alte Datei wurde wiederverwendet. |

Der Teilstand enthält `AC0800_L/M/S`, `AC0812_M`, `AC0820_L` und `AC0834_S`.
Dieser Teilstand ist ausdrücklich **keine** Release-Freigabe.

## Entscheidung und Recovery-Plan

FP-D12 endet mit **FAIL/BLOCKER**. Es gibt keine akzeptierte Ausnahme.

Vor FP-D13 wird der feste AC08-Regression-Satz in deterministische
Einzelvarianten-Segmente zerlegt. Jedes Segment erhält einen eigenen Timeout,
Exit-Code und Evidence-Eintrag. Die Gesamtmetrik darf erst erzeugt bzw. als
gültig akzeptiert werden, wenn alle Segmente erfolgreich abgeschlossen sind.
Damit bleibt auch im segmentierten Recovery-Pfad „No silent regression“ erhalten.

## Aufgabenstand im 14-Tage-Finish-Playbook

- Fachliche Tagesaufgaben (`FP-D*`): **30 erledigt**, **13 offen**.
- Einschließlich der vier übergreifenden Regeln (`FP-R*`): **30 erledigt**, **17 offen**.
- FP-D12 selbst: **3 von 3 erledigt**, **0 offen**.

Die noch offenen `FP-D*`-Einträge sind die bislang nicht abgehakten Baseline-
Pakete FP-D1/FP-D2 (7 Einträge) sowie FP-D13/FP-D14 (6 Einträge).

## 5-Zeilen-Log

- **Getestet:** Gate-/Metrics-Detailtests und vollständiger dreistufiger FP-D12-Gate-Lauf.
- **Ergebnis:** Detailtests und Kernsuite grün; hartes Gate bleibt wegen AC08-Timeout rot.
- **Blocker:** Keine vollständige neue `ac08_success_metrics.csv` nach 900 Sekunden.
- **Nächster Schritt:** AC08-Smoke deterministisch segmentieren und erst danach FP-D13 starten.
- **Morgiger Startbefehl:** `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_local_completion_checks_tool.py`.
