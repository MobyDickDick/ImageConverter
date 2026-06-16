# Nächstes Arbeitspaket – T6.15 AC0835-S-Isolation Run PY (2026-06-16)

## Ziel

Run PY arbeitet den nächsten offenen T6-Langläufer aus `docs/open_tasks.md` ab:
`test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]`
soll isoliert laufen, unter dem 90-Sekunden-Ziel bleiben und weiterhin den
semantischen Status `semantic_ok` bestätigen.

## Umsetzung

- Der bestehende parametrisierte Heavy-Regressionsfall wurde unverändert isoliert
  ausgeführt.
- Der Lauf nutzte einen äußeren `timeout 90`-Guard und
  `PYTEST_PER_TEST_TIMEOUT_SECONDS=90`, damit das Akzeptanzbudget auch im
  Einzeltestpfad reproduzierbar abgebildet ist.
- Produktions- und Testcode mussten nicht geändert werden, weil der aktuelle
  AC0835-S-Semantikpfad das Budget bereits deutlich unterschreitet.
- Das erzeugte Element-Log bestätigt `status=semantic_ok`; ein
  `validation_time_budget_exceeded`-Hinweis wurde nicht gefunden.

## Laufzeit- und Akzeptanznachweis

```bash
start=$(date +%s); set -o pipefail; timeout 90 env RUN_HEAVY_CONVERSION_TESTS=1 PYTEST_PER_TEST_TIMEOUT_SECONDS=90 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q 'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]' 2>&1 | tee artifacts/converted_images/reports/T6_15_ac0835S_isolation_2026-06-16_runPY.log; code=${PIPESTATUS[0]}; end=$(date +%s); echo "WALL_TIME_SECONDS=$((end-start))" | tee -a artifacts/converted_images/reports/T6_15_ac0835S_isolation_2026-06-16_runPY.log; exit $code
```

| Kriterium | Gefordert | Run PY |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=90s` | `45.66s` |
| Wandzeit | `<=90s` | `49s` |
| Semantikstatus | `semantic_ok` | `semantic_ok` |
| Element-Log | kein `validation_time_budget_exceeded` | kein Treffer |

## 5-Zeilen-Log

- **Getestet:** Unveränderter AC0835-S-Heavy-Regressionsfall als isolierter T6.15-Track.
- **Ergebnis:** Exit `0`, `1 passed in 45.66s`; Wandzeit `49s`.
- **Blocker:** Kein T6.15-Blocker; der Element-Log bestätigt `status=semantic_ok` und enthält keinen `validation_time_budget_exceeded`-Eintrag.
- **Dokumentation:** T6.15 ist in `docs/open_tasks.md` abgeschlossen und das Run-Log liegt unter `artifacts/converted_images/reports/`.
- **Nächster Schritt:** Nach Abschluss der dokumentierten T6.11–T6.15-Langläuferrotation wieder zur allgemeinen Priorisierung in `docs/open_tasks.md` zurückkehren.
