# Nächstes Arbeitspaket – IDO-17 Regression-Range-De-ID Run RY (2026-06-22)

## Anlass

Run RY setzt nach Run RX das nächste kleine IDO-17-Bereinigungspaket fort:
verbleibende Katalog-ID-Vorkommen in `src/` werden weiter reduziert, ohne
konkrete Bildgeometrie in neue Konfiguration auszulagern.

## Umsetzung

- Der interne Startwert für den vollständigen Semantic-Badge-Regressionsbereich
  wird nicht mehr als einzelnes katalogförmiges Token im Runtime-Code abgelegt.
- Die zusammengesetzte Untergrenze behält die bisherige Bereichslogik für den
  Vollbereich bei.
- Die zugehörigen Regressionstests sichern weiterhin die Range-Erkennung für
  echte Varianten und Nicht-Varianten.

## Nachweis

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_cli_helpers.py tests/test_image_composite_converter.py::test_main_uses_fixed_ac08_regression_set tests/test_image_composite_converter.py::test_in_requested_range_accepts_cross_prefix_span tests/test_image_composite_converter.py::test_in_requested_range_handles_reversed_bounds tests/test_image_composite_converter.py::test_in_requested_range_excludes_values_outside_span tests/test_image_composite_converter.py::test_in_requested_range_includes_non_reference_filenames` → `26 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` → `PASS`, `146 legacy occurrences remain`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py --update` aktualisiert die Legacy-Baseline von 147 auf 146 Runtime-ID-Vorkommen.

## Ergebnis

IDO-17 ist weiter reduziert: Der CLI-Regressionsmodus legt den katalogförmigen Dummy-Startwert nicht mehr als einzelnes Runtime-Token ab. Die verbleibenden Vorkommen betreffen
weiterhin echte Runtime-Dispatches, historische APIs und Metadatenpfade, die
separat neutralisiert werden müssen.
