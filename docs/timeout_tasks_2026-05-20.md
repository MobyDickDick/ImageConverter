# Timeout-/Aufgabenliste (auto, 2026-05-20)

Quelle: automatische Auswertung von xfail-Markierungen + 30s-Timeout-Policy.

## Kandidaten (Priorität hoch)
- [ ] `test_convert_one_impl_semantic_mismatch_is_reported_as_failure` in `tests/detailtests/test_conversion_execution_helpers.py` — TODO: extract and fix Failed_<name>.svg emission for semantic_mismatch path
- [ ] `test_convert_one_impl_unknown_status_is_recorded_as_failure` in `tests/detailtests/test_conversion_execution_helpers.py` — TODO: extract and fix Failed_<name>.svg emission for non-success statuses
- [ ] `test_convert_one_impl_trivial_placeholder_svg_is_marked_failed` in `tests/detailtests/test_conversion_execution_helpers.py` — TODO: extract and fix Failed_<name>.svg emission when placeholder detection fails
- [ ] `test_ac08_regression_smoke_run_creates_expected_outputs` in `tests/test_conversion_regression_smoke.py` — AUFGABE: stabilisiere AC0800 smoke output (expected SVG/metrics drift in current env)

## Kandidat aus Laufzeitgrenze (30s)
- [ ] `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` überschreitet 30s und wird als `AUFGABE` geführt.
