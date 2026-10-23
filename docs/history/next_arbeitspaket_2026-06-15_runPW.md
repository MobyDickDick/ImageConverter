# Nächstes Arbeitspaket – T6.13 AC0800-M-Isolation Run PW (2026-06-15)

## Ziel

Run PW bearbeitet den nächsten dokumentierten Langläufer nach T6.12:
Der echte parametrisierte `AC0800_M`-Regressionstest muss isoliert in
höchstens 120 Sekunden abschließen und weiterhin den semantischen Status
`semantic_ok` bestätigen.

## Befund

Der aktuelle Repository-Stand benötigt für diesen Test keine weitere
fachliche oder technische Verkürzung. Der unveränderte Regressionstest wurde
mit aktiviertem Heavy-Conversion-Pfad sowie einem äußeren und inneren
120-Sekunden-Limit ausgeführt. Er schließt bereits nach `3.03s` Pytest-Zeit
beziehungsweise `5s` auf ganze Sekunden gemessener Wandzeit erfolgreich ab.

Damit ist die historische Einordnung als Langläufer für den aktuellen Stand
überholt. Eine Reduktion der Validierungsrunden oder Änderung an
Produktionsbudgets wäre nicht durch den gemessenen Lauf gerechtfertigt.

## Umsetzung

- T6.13 wurde anhand des aktuellen isolierten Laufs abgeschlossen.
- Der bestehende Testpfad und seine Assertion auf `status=semantic_ok` bleiben
  unverändert.
- Produktionscode, Testcode und reguläre Konvertierungsbudgets bleiben
  unverändert.
- Das vollständige Laufprotokoll wurde als dauerhaftes Evidenzartefakt
  abgelegt.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 120 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTEST_PER_TEST_TIMEOUT_SECONDS=120 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
  'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0800_M-semantic_ok]'
```

| Kriterium | Gefordert | Run PW |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=120s` | `3.03s` |
| Wandzeit | `<=120s` | `5s` |
| Semantischer Status | `semantic_ok` | grün |
| Codeänderung erforderlich | nur bei messbarem Bedarf | nein |

## 5-Zeilen-Log

- **Getestet:** Echter isolierter AC0800-M-Heavy-Test über den bestehenden parametrisierten AC08-Regressionstest.
- **Ergebnis:** Exit `0`, `1 passed in 3.03s`; die Wandzeit beträgt auf ganze Sekunden gemessen `5s`.
- **Blocker:** Kein T6.13-Blocker; das 120-Sekunden-Akzeptanzziel wird deutlich unterschritten.
- **Nächster Schritt:** T6.14, den AC0820-L-Regressionsfall als separaten Langläufer-Track isolieren und unter dem 120-Sekunden-Ziel bestätigen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q 'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]'`.
