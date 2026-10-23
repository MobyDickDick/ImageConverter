# Nächstes Arbeitspaket – Run LQ (2026-05-28)

Dieses Arbeitspaket bearbeitet den in `docs/open_tasks.md` priorisierten PR-R5-Schritt der Ketten-Architektur und schließt die PR-Roadmap mit sichernden Tests ab.

## 1) PR-R5 Benennung, Telemetrie, Abnahme

- Eingeführtes Modul:
  - `src/iCCModules/imageCompositeConverterChainTelemetry.py`
- Harmonisierte Phasenbegriffe:
  - Geometry: `geometry_chain.elementwise`, `geometry_chain.unavailable`, `emergency.one_shot_geometry`
  - Policy: `policy.geometry_selected`, `policy.reference_selected`, `policy.guard_blocked`, `policy.no_geometry_available`
  - Emergency/Placeholder: `emergency.placeholder_svg`
- Erfasste R5-Metriken:
  - `step_count`
  - `step_accepted_count`
  - `step_success_rate`
  - `override_applied`
  - `override_reason`
  - `placeholder_emergency_used`
- Aggregierte Abnahmemetriken:
  - `conversion_count`
  - `mean_step_success_rate`
  - `override_frequency`
  - `placeholder_emergency_rate`

## 2) Verdrahtung

- `generateCompositeSvgImpl(...)` schreibt nach Geometry-IR-Auswahl und Policy-Schlussphase:
  - `params["chain_phase_telemetry"]`
  - `params["chain_phase_telemetry_line"]`
- Damit ist die R5-Abnahmespur direkt an die Reihenfolge Geometry → Policy → Finalrender gekoppelt.

## 3) Zusatzkorrektur

- AC0030-artige, geometrisch vollständige Beschreibungen setzen keine verdeckte `top_source_ref="AC0030"` mehr.
- AC0130 bleibt dadurch im Geometry-IR-/Composite-Pfad ohne Donor-Top-Source; Referenz-/Sample-Entscheidungen bleiben Policy-/Fallback-Sache.

## 4) Abnahmedokument

- Ergänzt:
  - `docs/chain_architecture_r5_acceptance_2026-05-28_runLQ.md`

## 5) Tests

- R5-Detailtests:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_chain_telemetry_helpers.py tests/detailtests/test_policy_phase_helpers.py tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/detailtests/test_composite_svg_helpers.py tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py`
  - Ergebnis: `19 passed in 0.30s`
  - Log: `artifacts/converted_images/reports/pr_r5_chain_telemetry_detailtests_2026-05-28_runLQ.log`
- Gezielte AC0120/AC0130/AC0030-Vergleichstests:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py::test_build_geometry_ir_maps_ac0130_like_description_to_ordered_chain tests/detailtests/test_geometry_ir_helpers.py::test_build_geometry_ir_maps_ac0120_self_description_to_plus_minus_chain tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_geometry_ir_for_ac0120_like_description tests/test_image_composite_converter.py::test_parse_description_does_not_misread_ac0130_text_as_top_source_ref tests/detailtests/test_conversion_execution_helpers.py::test_convert_one_impl_uses_implicit_sample_svg_for_non_composite_placeholder_status`
  - Ergebnis: `5 passed, 5 warnings in 0.77s`
  - Log: `artifacts/converted_images/reports/ac0120_ac0130_ac0030_r5_targeted_tests_2026-05-28_runLQ.log`
- Volltest:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`
  - Ergebnis: `560 passed, 5 warnings in 5.03s`
  - Log: `artifacts/converted_images/reports/pytest_full_2026-05-28_runLQ.log`

## Fazit

PR-R5 ist implementiert und getestet. Die Ketten-Architektur hat nun harmonisierte Logging-Begriffe, phasenbezogene Qualitätsmetriken und eine dokumentierte, reproduzierbare Abnahme.
