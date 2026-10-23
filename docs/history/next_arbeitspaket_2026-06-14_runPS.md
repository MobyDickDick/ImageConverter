# Nächstes Arbeitspaket – T6.9 Adaptive-Unlock-Stagnation Run PS (2026-06-14)

## Ziel

Run PS prüft den nächsten dokumentierten Langläufer nach T6.8:
`test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`
muss den Adaptive-Unlock-Stagnationspfad weiterhin real ausführen und
isoliert in höchstens 45 Sekunden abschließen.

## Ausgangslage

Die Blocker-Inventur führte den Test mit einer historischen Laufzeit von
`65.09s`. Der fokussierte Test erzeugt für die AC0831-Familie absichtlich
Stagnation, indem alle elementweisen Optimierer ohne Änderung zurückkehren.
Er führt vier Validierungsrunden aus und prüft anschließend, dass diese nicht
für Phase 2 freigeschaltete Familie keinen `adaptive_unlock_applied`-Marker
erhält.

Vor einer Änderung des fachlichen Testpfads wurde der unveränderte Test auf
der aktuellen vendorten Python-3.10-Toolchain erneut gemessen.

## Umsetzung

- Der fokussierte Heavy-Test wurde mit einem äußeren 45-Sekunden-Guard und
  dem gleich großen pytest-Einzeltest-Timeout ausgeführt.
- Die vier bestehenden Validierungsrunden und die fachliche Assertion blieben
  unverändert.
- Da der aktuelle Lauf das Ziel deutlich unterschreitet, waren weder eine
  künstliche Verkürzung des Testpfads noch Änderungen am Produktionscode
  erforderlich.
- T6.9 ist in `docs/open_tasks.md` mit dem reproduzierbaren Messwert und dem
  Run-Log abgeschlossen.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 45 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTEST_PER_TEST_TIMEOUT_SECONDS=45 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation
```

| Kriterium | Gefordert | Run PS |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=45s` | `4.27s` |
| Wandzeit | `<=45s` | `6s` |
| Validierungsrunden | unverändert `4` | unverändert |
| AC0831-Unlock-Marker | nicht vorhanden | nicht vorhanden |

Gegenüber der historischen Inventurlaufzeit von `65.09s` liegt die aktuelle
Pytest-Dauer rund `93.44 %` niedriger.

## 5-Zeilen-Log

- **Getestet:** Unveränderter isolierter AC0831-Stagnationstest mit vier Validierungsrunden.
- **Ergebnis:** Exit `0`, `1 passed in 4.27s`; die Adaptive-Unlock-Grenze bleibt testbar.
- **Blocker:** Kein T6.9-Blocker; das 45-Sekunden-Akzeptanzziel ist ohne Codeänderung erfüllt.
- **Nächster Schritt:** T6.10, den Extent-Bracketing-Test, unter das 35-Sekunden-Ziel bringen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements`.
