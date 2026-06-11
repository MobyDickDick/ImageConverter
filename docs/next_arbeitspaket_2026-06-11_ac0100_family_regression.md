# Nächstes Arbeitspaket – AC0010/AC0100-Familienregression (2026-06-11)

Dieses Arbeitspaket schließt die Rückmeldung aus `nextPrompt.txt` zur
AC0010/AC0100-Familie vollständig ab.

## Fehleranalyse

Die produktiven Konvertierungspfade waren inzwischen allgemeingültig
algorithmisch:

- `AC0010` wird aus der Beschreibung als normalisierte Geometry-IR aus
  Verlauf, Rechteckrahmen, Diagonale sowie Plus-/Minus-Glyph aufgebaut und am
  tatsächlichen Raster registriert.
- `AC0100_L`, `AC0100_M` und `AC0100_S` verwenden den rasterabgeleiteten,
  elementweisen Symbol-Fit. Farben, Glyph-Positionen, Linienbreiten und
  Verlauf werden aus dem jeweiligen Eingabebild bestimmt.

Die noch bestehende Lücke lag im automatisierten Nachweis: Der schwere
Regressions-Smoke prüfte ausschließlich L/M/S. Das in der Rückmeldung separat
genannte Basisbild `AC0010.jpg` konnte deshalb unbemerkt auf einen Sample- oder
Template-Pfad zurückfallen.

## Umsetzung

Der bestehende AC0100-Regressions-Smoke konvertiert nun in einem gemeinsamen
Lauf alle vier real vorhandenen Familienmitglieder:

- `AC0010`
- `AC0100_L`
- `AC0100_M`
- `AC0100_S`

Für jede Variante werden der erwartete algorithmische Status, eine explizite
Qualitätsgrenze und das Ausbleiben von Sample-SVG-Auswahl beziehungsweise
Template-Transfer geprüft. Damit werden keine Bildkoordinaten oder fertigen
SVG-Daten gespeichert; der Test sichert ausschließlich den allgemeinen
Algorithmus und dessen Ergebnisqualität ab.

## Qualitätsgrenzen

- `AC0010`: `best_error < 25`, `mean_delta2 < 3000`
- `AC0100_L`: `best_error < 18`, `mean_delta2 < 1800`
- `AC0100_M/S`: `best_error < 18`, `mean_delta2 < 1600`

Die getrennten Grenzen berücksichtigen, dass das unskalierte Basisbild über
die beschreibungsgetriebene Geometry-IR läuft, während die drei
Größenvarianten den elementweisen Raster-Fit verwenden.

## Nachweis

Der erweiterte Heavy-Smoke wurde lokal vollständig ausgeführt:

- `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=. pytest -q tests/test_conversion_regression_smoke.py::test_ac0100_quality_uses_algorithmic_elementwise_fit`
- Ergebnis: `1 passed` in `517.03s`.
