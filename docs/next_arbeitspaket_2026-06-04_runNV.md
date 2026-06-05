# Nächstes Arbeitspaket – FP-D11 Run NV (2026-06-04)

## Ziel

FP-D11 bereitet das Release-Kandidaten-Gate vor. Der Probelauf soll nicht still
„grün“ wirken, sondern Kernsuite, AC08-Smoke und Qualitätsvergleich reproduzierbar
als feste Checkliste ausführen und jede Abweichung als **Blocker** oder bewusst
akzeptierte Ausnahme klassifizieren.

## Gegenmaßnahme / Prüfmechanik

Neu ist ein kleiner Gate-Runner:

```bash
./tools/run_release_candidate_gate.sh
```

Der Runner schreibt für jeden Gate-Schritt ein Evidence-Log unter
`artifacts/test-evidence/<gate-name>/` und eine maschinenlesbare
`gate_status.csv` mit den Spalten `step`, `exit`, `classification` und `log`.
Standardmäßig sind keine Ausnahmen akzeptiert; nur explizit über
`RC_GATE_ACCEPTED_EXCEPTIONS` benannte Schritte werden als `ACCEPTED_EXCEPTION`
statt `BLOCKER` klassifiziert.

Die feste Checkliste ist:

1. **Kernsuite:** `python -m pytest -q -rs`
2. **AC08-Smoke:** deterministischer AC08-Regression-Set-Lauf in ein separates
   Output-Verzeichnis.
3. **Qualitätsvergleich:** `tools/check_ac08_success_metrics_gate.py` prüft die
   finalen `ac08_success_metrics.csv`-Kriterien inklusive
   `criterion_regression_set_improved`, `criterion_stable_families_not_worse`
   und `overall_success`.

## Datenbasierte Entscheidung

| Check | Befehl | Exit | Ergebnis |
| --- | --- | ---: | --- |
| Gate-/Metrics-Detailtests | `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_local_completion_checks_tool.py` | `0` | `8 passed in 18.57s`; Runner klassifiziert akzeptierte Ausnahmen vs. Blocker, Metrics-Gate meldet grün/rot stabil. |
| Kernsuite | `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs` | `0` | `701 passed in 34.74s`. |
| AC08-Smoke | `rm -rf /tmp/ic-fpd11-ac08 && timeout 300 env PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-fpd11-ac08 --ac08-regression-set --deterministic-order` | `124` | **Blocker:** Timeout nach 300s; bis dahin wurden nur Teilartefakte bis `AC0812_M` erzeugt. |
| Qualitätsgate | `python tools/check_ac08_success_metrics_gate.py /tmp/ic-fpd11-ac08/reports/ac08_success_metrics.csv` | `1` | **Folge-Blocker:** finale Metrics-Datei fehlt wegen AC08-Smoke-Timeout. |

## Ergebnis

- FP-D11-1 ist erfüllt: Die Gate-Checkliste ist als reproduzierbarer Runner
  vorhanden und ein Probelauf wurde gestartet.
- FP-D11-2 ist erfüllt: Die Abweichung ist als **Blocker** markiert, nicht als
  akzeptierte Ausnahme.
- FP-D11-EXIT ist erfüllt: Der Probelauf hat einen eindeutigen Status:
  **FAIL/BLOCKER** wegen AC08-Smoke-Timeout und fehlender finaler
  Qualitätsmetrik.

## 5-Zeilen-Log

- **Getestet:** Gate-Runner/Metric-Checker, Kernsuite, AC08-Smoke, Qualitätsgate.
- **Ergebnis:** Kernsuite und Detailtests grün; AC08-Smoke überschreitet 300s.
- **Blocker:** Kein `ac08_success_metrics.csv`, daher kein freigabefähiger
  Qualitätsvergleich.
- **Nächster Schritt:** FP-D12 fährt dasselbe Gate hart mit höherem Budget oder
  segmentiertem AC08-Smoke und wendet „No silent regression“ strikt an.
- **Morgiger Startbefehl:** `RC_GATE_OUTPUT_DIR=/tmp/ic-fpd12-ac08 PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 ./tools/run_release_candidate_gate.sh`.
