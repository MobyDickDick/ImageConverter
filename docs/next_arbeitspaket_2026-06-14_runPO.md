# Nächstes Arbeitspaket – T6.5 AC0820-L-Kreisgeometrie Run PO (2026-06-14)

## Ziel

Run PO schließt den nächsten hoch priorisierten Langläufer nach T6.4:
Der echte `AC0820_L`-Kreisgeometrietest muss weiterhin belegen, dass der
Kreisdurchmesser strikt größer als die halbe Bildbreite ist, und isoliert in
höchstens 100 Sekunden abschließen.

## Ursache der bisherigen Laufzeit

Der fokussierte Test führte standardmäßig sechs vollständige Runden der
Elementvalidierung aus, obwohl er ausschließlich die Geometrie des
resultierenden Kreises prüft:

- Quellbreite und Quellhöhe bleiben jeweils `30`,
- im erzeugten SVG muss ein Kreis vorhanden sein,
- der doppelte Radius muss strikt größer als `15` sein.

Eine vollständige Optimierungsrunde reicht aus, um diese
Regressionseigenschaft an der realen semantischen Pipeline zu prüfen.

## Umsetzung

- Nur der fokussierte Kreisgeometrietest setzt
  `badge_validation_rounds=1`.
- Quelldatei, Beschreibungsdatei, Iterationszahl und Produktionspipeline
  bleiben unverändert.
- Die bestehende strikte Kreisdiameter-Assertion wurde nicht verändert.
- Produktionscode und reguläre Konvertierungsbudgets bleiben unverändert.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 100 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTEST_PER_TEST_TIMEOUT_SECONDS=100 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
tests/test_image_composite_converter.py::test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width
```

| Kriterium | Gefordert | Run PO |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=100s` | `59.17s` |
| Wandzeit | `<=100s` | `60.759s` |
| Quelldimension | `30x30` | grün |
| Kreisdiameter | strikt `>15` | grün |

Gegenüber der historischen Laufzeit von `165.26s` sinkt die Pytest-Dauer um
rund `64.20 %`.

## 5-Zeilen-Log

- **Getestet:** Echter isolierter AC0820-L-Heavy-Test über die semantische Pipeline.
- **Ergebnis:** Exit `0`, `1 passed in 59.17s`; die bestehende Kreisdiameter-Assertion bleibt grün.
- **Blocker:** Kein T6.5-Blocker; das 100-Sekunden-Akzeptanzziel ist erfüllt.
- **Nächster Schritt:** T6.6 (`AC0835_S`) als nächsten hoch priorisierten Regressionstest unter das 90-Sekunden-Ziel bringen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q 'tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]'`.
