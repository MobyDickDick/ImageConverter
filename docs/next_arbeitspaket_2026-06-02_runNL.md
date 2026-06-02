# Nächstes Arbeitspaket – Run NL (2026-06-02)

Dieses Arbeitspaket vertieft **TH2/AC0100-QA** aus `docs/open_tasks.md` nach der
Nutzer-Rückmeldung, dass `AC0100_L` zwar verbessert war, `AC0100`, `AC0100_M`
und `AC0100_S` aber nicht über feste Daten-/Sample-Annahmen gelöst werden
dürfen.

## 1) Fehlerbild

- Der bisherige strukturierte AC0100-Symbol-Fit konnte bereits optionale
  Diagonalen und Minuslinien abschalten.
- Die Plus-Position wurde jedoch noch primär über feste Kandidatenraster
  abgesucht. Das ist für die kompakte AC0100-Familie anfällig, weil der
  eigentliche weiße Plus-Glyph aus dem Eingaberaster ableitbar ist und nicht aus
  einer gespeicherten Beispielpose kommen soll.

## 2) Umsetzung

- Die Symbolparameter werden nun vor der Element-Suche aus der tatsächlichen
  Raster-Luminanz geschätzt:
  - heller Glyph-ROI im oberen/linken Symbolbereich,
  - gewichteter Schwerpunkt für `plus_x_ratio` und `glyph_y_ratio`,
  - Perzentil-Spannweite für `plus_half_ratio`.
- Die anschließenden Suchfenster für Plus-Position und -Halbbreite werden um
  diese gemessenen Rasterwerte herum aufgebaut. Dadurch bleibt der Fit
  algorithmisch und variantenfähig, statt eine feste AC0100-Beispielpose zu
  konservieren.
- Ein Detailtest sichert ab, dass die Glyph-Geometrie aus einem synthetischen
  Raster erkannt wird.

## 3) Nachweis

Gezielter AC0100-Regressionslauf:

- Befehl:
  - `RUN_HEAVY_CONVERSION_TESTS=1 PYTHONPATH=. pytest -q tests/test_conversion_regression_smoke.py::test_ac0100_quality_uses_algorithmic_elementwise_fit`
- Ergebnis: `1 passed`, Exit `0`, Laufzeit `104.06s`.

Detailtests:

- Befehl:
  - `PYTHONPATH=. pytest -q tests/detailtests/test_non_composite_runtime_helpers.py::test_symbol_params_detect_glyph_geometry_from_raster tests/detailtests/test_non_composite_runtime_helpers.py::test_structured_symbol_svg_can_fit_single_diagonal_top_left_plus`
- Ergebnis: `2 passed`, Exit `0`, Laufzeit `0.46s`.

## Kurzfazit

AC0100 wird weiter über den strukturierten Symbol-Algorithmus erzeugt. Die
kritische Plus-Geometrie wird nun aus dem Eingabebild gemessen und nur lokal
verfeinert; feste Sample-SVG-Auswahl und generischer Template-Transfer bleiben
im geprüften AC0100-Pfad ausgeschlossen.
