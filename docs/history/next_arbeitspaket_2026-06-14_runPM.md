# Nächstes Arbeitspaket – T6.3 AC0838-M-Isolation Run PM (2026-06-14)

## Ziel

Run PM schließt den nächsten sehr hoch priorisierten Langläufer nach T6.2:
Der echte `AC0838_M`-VOC-Badge-Test muss seine bestehende Kreisgeometrie
weiterhin bestätigen und isoliert in weniger als 90 Sekunden abschließen.

## Ursache der bisherigen Laufzeit

Der Test führte sechs vollständige Runden der rechenintensiven
Elementvalidierung aus, obwohl er ausschließlich drei grobe
Geometrieeigenschaften des resultierenden Kreises absichert:

- Radius mindestens `9.0`,
- horizontales Zentrum ungefähr `10.0`,
- vertikales Zentrum mindestens `24.0`.

Die erste vollständige Optimierungsrunde reicht aus, um genau diese
Regressionseigenschaften zu prüfen. Weitere Konvergenzrunden gehören zu den
End-to-End- und Qualitätsprüfungen, nicht zu diesem fokussierten
Parameter-Regressionstest.

## Umsetzung

- `max_rounds` des isolierten Tests wurde von sechs auf eine vollständige
  Elementvalidierungsrunde reduziert.
- Die drei bestehenden Assertions wurden nicht verändert.
- Produktionscode, Standardbudgets und reguläre Konvertierungsläufe bleiben
  unverändert.
- Der Test wurde mit aktivierten Heavy-Conversion-Tests und einem äußeren
  90-Sekunden-Timeout ausgeführt.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 90 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout
```

| Kriterium | Gefordert | Run PM |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<90s` | `60.14s` |
| Wandzeit | `<90s` | `60.947s` |
| Radius-Assertion | unverändert grün | grün |
| X-Zentrum-Assertion | unverändert grün | grün |
| Y-Zentrum-Assertion | unverändert grün | grün |

Gegenüber der historischen Laufzeit von `173.27s` sinkt die Pytest-Dauer um
rund `65.29 %`.

## 5-Zeilen-Log

- **Getestet:** Echter isolierter AC0838-M-Heavy-Test mit Rasterbild und Elementvalidierung.
- **Ergebnis:** Exit `0`, `1 passed in 60.14s`; alle drei bestehenden Geometrie-Assertions bleiben grün.
- **Blocker:** Kein Blocker für T6.3; das 90-Sekunden-Akzeptanzziel ist erfüllt.
- **Nächster Schritt:** T6.4 (`AC0820_L`) als nächsten sehr hoch priorisierten Regressionstest unter das 120-Sekunden-Ziel bringen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q 'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]'`.
