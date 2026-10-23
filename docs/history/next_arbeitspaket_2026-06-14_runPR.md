# Nächstes Arbeitspaket – T6.8 AC0812-Radiusvalidierung Run PR (2026-06-14)

## Ziel

Run PR prüft den nächsten dokumentierten Langläufer nach T6.7:
`test_validate_badge_can_expand_ac0812_tiny_circle_radius` muss die
Radius-Erweiterungslogik weiterhin real ausführen und isoliert in höchstens
75 Sekunden abschließen.

## Ausgangslage

Die Blocker-Inventur führte den Test mit einer historischen Laufzeit von
`101.94s`. Der Test startet die AC0812-S-Kreisgeometrie absichtlich mit dem zu
kleinen Radius `5.0`, führt zwei Elementvalidierungsrunden aus und verlangt
anschließend:

- einen Radius strikt größer als `5.0`,
- mindestens einen protokollierten `Radius-Bracketing r`-Schritt.

Vor einer weiteren Budgetreduktion wurde der unveränderte Test auf der
aktuellen vendorten Python-3.10-Toolchain erneut gemessen.

## Umsetzung

- Der fokussierte Heavy-Test wurde mit einem äußeren 75-Sekunden-Guard und dem
  gleich großen pytest-Einzeltest-Timeout ausgeführt.
- Beide bestehenden Validierungsrunden und beide fachlichen Assertions blieben
  unverändert.
- Da der aktuelle Lauf das Ziel deutlich unterschreitet, waren weder eine
  künstliche Verkürzung des Testpfads noch Änderungen am Produktionscode
  erforderlich.
- T6.8 ist in `docs/open_tasks.md` mit dem reproduzierbaren Messwert und dem
  Run-Log abgeschlossen.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 75 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTEST_PER_TEST_TIMEOUT_SECONDS=75 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius
```

| Kriterium | Gefordert | Run PR |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=75s` | `3.10s` |
| Wandzeit | `<=75s` | `4.184s` |
| Radius nach Validierung | strikt `>5.0` | grün |
| Radius-Bracketing-Log | vorhanden | grün |

Gegenüber der historischen Inventurlaufzeit von `101.94s` liegt die aktuelle
Pytest-Dauer rund `96.96 %` niedriger.

## 5-Zeilen-Log

- **Getestet:** Unveränderter isolierter AC0812-S-Radius-Bracketing-Test mit zwei Validierungsrunden.
- **Ergebnis:** Exit `0`, `1 passed in 3.10s`; Radius-Erweiterung und Bracketing-Log bleiben grün.
- **Blocker:** Kein T6.8-Blocker; das 75-Sekunden-Akzeptanzziel ist ohne Codeänderung erfüllt.
- **Nächster Schritt:** T6.9, den Adaptive-Unlock-Test, unter das 45-Sekunden-Ziel bringen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`.
