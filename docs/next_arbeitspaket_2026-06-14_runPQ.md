# Nächstes Arbeitspaket – T6.7 AC0811-L-Geometrie Run PQ (2026-06-14)

## Ziel

Run PQ schließt den in Run PP dokumentierten Anschluss T6.7 ab:
Der echte `AC0811_L`-Geometrietest muss den langen unteren Stem weiterhin
bestätigen, darf keinen Validierungs-Budget-Timeout enthalten und soll isoliert
in höchstens 75 Sekunden abschließen.

## Ursache der bisherigen Laufzeit

Der fokussierte Test führte drei vollständige Konvertierungsiterationen aus,
obwohl er ausschließlich die bereits in der ersten vollständigen Iteration
erzeugte Stem-Geometrie absichert:

- das reguläre `AC0811_L.svg` wird erzeugt,
- der untere Stem beginnt spätestens bei `y=27.5`,
- seine Höhe beträgt mindestens `12.0`,
- die Elementvalidierung überschreitet ihr Zeitbudget nicht.

Weitere Konvergenziterationen werden für diese geometrischen
Regressionseigenschaften nicht benötigt.

## Umsetzung

- Das Fixture wird aus seinem heutigen Ablageort
  `artifacts/images_to_convert/nonconvertable/` zusammen mit der Beschreibung
  in ein isoliertes Eingabeverzeichnis kopiert; ein stiller Fixture-Skip ist
  damit ausgeschlossen.
- Die echte, isolierte `AC0811_L`-Konvertierung bleibt erhalten.
- Der Iterationsumfang des fokussierten Tests wird von drei auf eine
  vollständige Iteration reduziert.
- Die beiden bestehenden Stem-Assertions bleiben unverändert.
- Das Elementvalidierungslog wird zusätzlich explizit auf die Abwesenheit von
  `validation_time_budget_exceeded` geprüft.
- Produktionscode und reguläre Konvertierungsbudgets bleiben unverändert.

## Laufzeit- und Akzeptanznachweis

```bash
timeout 75 env RUN_HEAVY_CONVERSION_TESTS=1 \
PYTEST_PER_TEST_TIMEOUT_SECONDS=75 \
PYTHONPATH=vendor/linux-py310/site-packages:. \
python -m pytest -q \
tests/test_image_composite_converter.py::test_ac0811_l_conversion_preserves_long_bottom_stem
```

| Kriterium | Gefordert | Run PQ |
| --- | ---: | ---: |
| Pytest-Ergebnis | Exit `0` | Exit `0`, `1 passed` |
| Pytest-Laufzeit | `<=75s` | `2.80s` |
| Wandzeit | `<=75s` | `3.601s` |
| Stem-Anfang | `<=27.5` | grün |
| Stem-Höhe | `>=12.0` | grün |
| Budget-Timeout | nicht vorhanden | grün |

Gegenüber der historischen Laufzeit von `102.33s` sinkt die Pytest-Dauer um
rund `97.26 %`.

## 5-Zeilen-Log

- **Getestet:** Echter isolierter AC0811-L-Heavy-Test über die Einvarianten-Konvertierung.
- **Ergebnis:** Exit `0`, `1 passed in 2.80s`; beide Stem-Grenzen bleiben erfüllt.
- **Blocker:** Kein T6.7-Blocker; das 75-Sekunden-Ziel und der Budget-Timeout-Ausschluss sind erfüllt.
- **Nächster Schritt:** T6.8 (`AC0812`) als nächsten hoch priorisierten Radius-Erweiterungstest unter das 75-Sekunden-Ziel bringen.
- **Startbefehl:** `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius`.
