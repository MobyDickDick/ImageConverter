# Nächstes Arbeitspaket – T6.14 AC0820-L-Langläufertrack Run PX (2026-06-16)

## Ziel

Run PX arbeitet den nächsten offenen T6-Langläufer aus `docs/open_tasks.md` ab:
`test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]`
soll als separater Track isoliert laufen, unter dem 120-Sekunden-Ziel bleiben
und dabei keinen `validation_time_budget_exceeded`-Hinweis im Element-Log erzeugen.

## Umsetzung

- Der bestehende parametrisierte Heavy-Regressionsfall wurde unverändert isoliert
  ausgeführt.
- Der Lauf nutzte einen äußeren `timeout 120`-Guard und
  `PYTEST_PER_TEST_TIMEOUT_SECONDS=120`, damit das Akzeptanzbudget auch im
  Einzeltestpfad reproduzierbar abgebildet ist.
- Produktions- und Testcode mussten nicht geändert werden, weil der aktuelle
  AC0820-L-Semantikpfad das Budget bereits deutlich unterschreitet.
- Das erzeugte Element-Log wurde auf `validation_time_budget_exceeded` geprüft;
  der Hinweis ist nicht vorhanden, und `status=semantic_ok` bleibt erhalten.

## Laufzeit- und Akzeptanznachweis

```bash
start=$(date +%s); set -o pipefail; timeout 120 env RUN_HEAVY_CONVERSION_TESTS=1 PYTEST_PER_TEST_TIMEOUT_SECONDS=120 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q 'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]' 2>&1 | tee artifacts/converted_images/reports/T6_14_ac0820L_isolation_2026-06-16_runPX.log; code=${PIPESTATUS[0]}; end=$(date +%s); echo "WALL_TIME_SECONDS=$((end-start))" | tee -a artifacts/converted_images/reports/T6_14_ac0820L_isolation_2026-06-16_runPX.log; exit $code
```

| Kriterium | Gefordert | Run PX |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=120s` | `61.45s` |
| Wandzeit | `<=120s` | `62s` |
| Semantikstatus | `semantic_ok` | `semantic_ok` |
| Element-Log | kein `validation_time_budget_exceeded` | kein Treffer |

## 5-Zeilen-Log

- **Getestet:** Unveränderter AC0820-L-Heavy-Regressionsfall als isolierter T6.14-Track.
- **Ergebnis:** Exit `0`, `1 passed in 61.45s`; Wandzeit `62s`.
- **Blocker:** Kein T6.14-Blocker; der Element-Log enthält keinen `validation_time_budget_exceeded`-Eintrag.
- **Dokumentation:** T6.14 ist in `docs/open_tasks.md` abgeschlossen und das Run-Log liegt unter `artifacts/converted_images/reports/`.
- **Nächster Schritt:** T6.15, den AC0835-S-Regressionsfall isolieren und unter das 90-Sekunden-Ziel bringen.
