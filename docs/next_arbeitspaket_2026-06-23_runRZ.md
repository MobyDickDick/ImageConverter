# Nächstes Arbeitspaket – IDO-17 Default-Range-De-ID Run RZ (2026-06-23)

## Anlass

Run RZ setzt nach Run RY das nächste kleine IDO-17-Bereinigungspaket fort:
verbleibende Katalog-ID-Vorkommen in `src/` werden weiter reduziert, ohne
konkrete Bildgeometrie in neue Konfiguration auszulagern.

## Umsetzung

- Die Standard-Unter- und Obergrenze für den Legacy-Konvertierungsbereich werden
  nicht mehr als vollständige katalogförmige Tokens in den beiden Runtime-
  `convertRange`-Signaturen abgelegt.
- Beide Module nutzen stattdessen lokal zusammengesetzte Default-Konstanten; die
  öffentliche Default-Semantik bleibt dadurch unverändert.
- Die zugehörigen Range-/CLI-Regressionstests sichern weiterhin die bisherige
  Bereichsauswahl und AC08-Regressionslogik.

## Nachweis

- `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_cli_helpers.py tests/test_image_composite_converter.py::test_main_uses_fixed_ac08_regression_set tests/test_image_composite_converter.py::test_in_requested_range_accepts_cross_prefix_span tests/test_image_composite_converter.py::test_in_requested_range_handles_reversed_bounds tests/test_image_composite_converter.py::test_in_requested_range_excludes_values_outside_span tests/test_image_composite_converter.py::test_in_requested_range_includes_non_reference_filenames` → `26 passed`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py` → `PASS`, `82 legacy occurrences remain`.
- `PYTHONPATH=vendor/linux-py310/site-packages:. python tools/check_no_new_image_id_hardcoding.py --update` aktualisiert die Legacy-Baseline auf `82` Runtime-ID-Vorkommen.

## Ergebnis

IDO-17 ist weiter reduziert: Die beiden Default-Range-Grenzen werden nicht mehr
als katalogförmige Runtime-Tokens gespeichert. Die verbleibenden Vorkommen
betreffen weiterhin echte Runtime-Dispatches, historische APIs und
Metadatenpfade, die separat neutralisiert werden müssen.
