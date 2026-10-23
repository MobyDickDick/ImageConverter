# Nächstes Arbeitspaket – T6.10 Extent-Bracketing Run PT (2026-06-15)

## Ziel

Run PT prüft den nächsten dokumentierten Langläufer nach T6.9:
`test_validate_badge_logs_extent_bracketing_for_line_elements` muss den realen
AC0812-S-Validierungspfad ausführen, das Extent-/Längen-Bracketing weiterhin
protokollieren und isoliert in höchstens 35 Sekunden abschließen.

## Ausgangslage

Die Blocker-Inventur führte den Test mit einer historischen Laufzeit von
`51.61s`. Ältere Isolationsläufe waren abhängig von der Python-/OpenCV-Umgebung
teilweise übersprungen worden; aktive Läufe am 16. und 17. Mai 2026 benötigten
noch `58.50s` beziehungsweise `59.78s`.

Der fokussierte Test lädt das reale Fixture `AC0812_S.jpg`, erzeugt die
familienbezogenen Badge-Parameter, führt eine vollständige Elementvalidierungs-
runde aus und prüft anschließend explizit die Logzeile
`arm: Längen-Bracketing`.

## Umsetzung

- Der fokussierte Heavy-Test wurde mit einem äußeren 35-Sekunden-Guard und
  dem gleich großen pytest-Einzeltest-Timeout ausgeführt.
- Fixture, reale Elementvalidierung, eine vollständige Validierungsrunde und
  die fachliche Log-Assertion blieben unverändert.
- Da der aktuelle Lauf das Ziel deutlich unterschreitet, waren weder eine
  künstliche Verkürzung des Testpfads noch Änderungen am Produktions- oder
  Testcode erforderlich.
- T6.10 ist in `docs/open_tasks.md` mit dem reproduzierbaren Messwert und dem
  Run-Log abgeschlossen.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 35 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTEST_PER_TEST_TIMEOUT_SECONDS=35 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements
```

| Kriterium | Gefordert | Run PT |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=35s` | `4.33s` |
| Wandzeit | `<=35s` | `6s` |
| Fixture-Pfad | realer AC0812-S-Pfad | ausgeführt, nicht übersprungen |
| Bracketing-Assertion | `arm: Längen-Bracketing` | vorhanden |

Gegenüber der historischen Inventurlaufzeit von `51.61s` liegt die aktuelle
Pytest-Dauer rund `91.61 %` niedriger.

## 5-Zeilen-Log

- **Getestet:** Unveränderter realer AC0812-S-Elementvalidierungspfad mit einer vollständigen Runde.
- **Ergebnis:** Exit `0`, `1 passed in 4.33s`; die Extent-Bracketing-Assertion bleibt aktiv.
- **Blocker:** Kein T6.10-Blocker; das 35-Sekunden-Akzeptanzziel ist ohne Codeänderung erfüllt.
- **Nächster Schritt:** T6.11, die wiederholbare Blocker-Inventur, automatisieren.
- **Startbefehl:** `python -m pytest --maxfail=1 -vv --durations=20`.
