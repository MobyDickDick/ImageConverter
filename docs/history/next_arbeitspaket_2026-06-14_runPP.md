# Nächstes Arbeitspaket – T6.6 AC0835-S-Isolation Run PP (2026-06-14)

## Ziel

Run PP schließt den nächsten hoch priorisierten Langläufer nach T6.5:
Der echte `AC0835_S`-Regressionstest muss den semantischen Status
`semantic_ok` weiterhin bestätigen und isoliert in höchstens 90 Sekunden
abschließen.

## Ursache der bisherigen Laufzeit

Der gemeinsame parametrisierte Regressionstest führte für `AC0835_S` sechs
vollständige Runden der rechenintensiven Elementvalidierung aus. Der Test
prüft jedoch ausschließlich den weiterhin erfolgreichen Abschluss der
semantischen Pipeline:

- die Pipeline liefert ein Ergebnis,
- das reguläre SVG wird erzeugt,
- kein `*_failed.svg` wird erzeugt,
- das Elementvalidierungslog enthält `status=semantic_ok`.

Eine vollständige Optimierungsrunde reicht aus, um diese fokussierten
Regressionseigenschaften zu prüfen. Weitere Konvergenzrunden bleiben den
End-to-End- und Qualitätsprüfungen vorbehalten.

## Umsetzung

- Nur der parametrisierte Fall `AC0835_S` setzt
  `badge_validation_rounds=1`.
- Die übrigen noch nicht isoliert optimierten Varianten des gemeinsamen
  Regressionstests behalten sechs Runden.
- SVG-Erzeugung, Ausschluss eines `*_failed.svg` und die bestehende
  `status=semantic_ok`-Assertion bleiben unverändert.
- Produktionscode und reguläre Konvertierungsbudgets bleiben unverändert.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 90 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTEST_PER_TEST_TIMEOUT_SECONDS=90 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]'
```

| Kriterium | Gefordert | Run PP |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=90s` | `43.25s` |
| Wandzeit | `<=90s` | `44.831s` |
| Semantischer Status | `semantic_ok` | grün |
| Fehler-SVG | nicht vorhanden | grün |

Gegenüber der historischen Laufzeit von `133.60s` sinkt die Pytest-Dauer um
rund `67.63 %`.

## 5-Zeilen-Log

- **Getestet:** Echter isolierter AC0835-S-Heavy-Test über die semantische Pipeline.
- **Ergebnis:** Exit `0`, `1 passed in 43.25s`; SVG und `semantic_ok` bleiben erhalten.
- **Blocker:** Kein T6.6-Blocker; das 90-Sekunden-Akzeptanzziel ist erfüllt.
- **Nächster Schritt:** T6.7 (`AC0811_L`) als nächsten hoch priorisierten Geometrietest unter das 75-Sekunden-Ziel bringen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_ac0811_l_conversion_preserves_long_bottom_stem`.
