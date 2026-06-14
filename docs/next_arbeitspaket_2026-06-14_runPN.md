# Nächstes Arbeitspaket – T6.4 AC0820-L-Isolation Run PN (2026-06-14)

## Ziel

Run PN schließt den nächsten sehr hoch priorisierten Langläufer nach T6.3:
Der echte `AC0820_L`-Regressionstest muss den semantischen Status
`semantic_ok` weiterhin bestätigen, ohne
`validation_time_budget_exceeded`-Marker und in höchstens 120 Sekunden.

## Reproduktion des Ausgangszustands

Der unveränderte Test startete sechs vollständige Elementvalidierungsrunden.
Bereits während der zweiten Runde griff der allgemeine
30-Sekunden-Pytest-Guard:

- Runde 1 war nach rund `27.8s` vollständig abgeschlossen,
- die Qualität verbesserte sich von `83.38%` auf `86.33%`,
- der Lauf brach in Runde 2 mit `_PerTestTimeout` ab.

Damit war die erste Runde bereits ausreichend, um die vom Test geforderte
Konvertierbarkeit und den semantischen Status zu belegen.

## Umsetzung

- Nur der parametrisierte Fall `AC0820_L` setzt
  `badge_validation_rounds=1`.
- Die übrigen Varianten des gemeinsamen Regressionstests behalten sechs
  Runden.
- SVG-Erzeugung, Ausschluss eines `*_failed.svg` und die bestehende
  `status=semantic_ok`-Assertion bleiben unverändert.
- Zusätzlich prüft der Test den Elementvalidierungslog explizit auf die
  Abwesenheit von `validation_time_budget_exceeded`.
- Produktionscode und reguläre Konvertierungsbudgets bleiben unverändert.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 120 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTEST_PER_TEST_TIMEOUT_SECONDS=120 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]'
```

| Kriterium | Gefordert | Run PN |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=120s` | `55.67s` |
| Wandzeit | `<=120s` | `56.511s` |
| Semantischer Status | `semantic_ok` | grün |
| Budgetmarker | nicht vorhanden | explizit ausgeschlossen |

Gegenüber der historischen Laufzeit von `168.27s` sinkt die Pytest-Dauer um
rund `66.92%`.

## 5-Zeilen-Log

- **Getestet:** Echter isolierter AC0820-L-Heavy-Test über die semantische Pipeline.
- **Ergebnis:** Exit `0`, `1 passed in 55.67s`; SVG und `semantic_ok` bleiben erhalten.
- **Blocker:** Kein T6.4-Blocker; der Budgetmarker fehlt wie gefordert.
- **Nächster Schritt:** T6.5, den fokussierten AC0820-L-Kreisgeometrietest, unter das 100-Sekunden-Ziel bringen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width`.
