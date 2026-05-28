# PR-R5 Abnahme – Ketten-Architektur (Run LQ, 2026-05-28)

## Ziel
PR-R5 macht die in PR-R2 bis PR-R4 eingeführte Ketten-Architektur messbar und sprachlich eindeutig:

1. **Geometry-Phase**: elementweise Geometry-IR statt unscharfer Fallback-Begriffe.
2. **Policy-Phase**: Referenz-/Guard-/Sample-Entscheidungen erst nach der Geometriekette.
3. **Emergency/Placeholder**: echte Platzhalter- oder Notfallpfade separat ausweisen.

## Umgesetzte Telemetrie

- Neues Helper-Modul: `src/iCCModules/imageCompositeConverterChainTelemetry.py`.
- Stabile Logging-Begriffe:
  - `geometry_chain.elementwise`
  - `geometry_chain.unavailable`
  - `emergency.one_shot_geometry`
  - `policy.geometry_selected`
  - `policy.reference_selected`
  - `policy.guard_blocked`
  - `policy.no_geometry_available`
  - `emergency.placeholder_svg`
- Pro Konvertierungsversuch werden flache R5-Metriken erzeugt:
  - `step_count`
  - `step_accepted_count`
  - `step_success_rate`
  - `override_applied`
  - `override_reason`
  - `placeholder_emergency_used`
- Aggregation über mehrere Zeilen liefert:
  - `conversion_count`
  - `mean_step_success_rate`
  - `override_frequency`
  - `placeholder_emergency_rate`

## Verdrahtung

`generateCompositeSvgImpl(...)` schreibt nach der zentralen Policy-Schlussphase zusätzlich:

- `params["chain_phase_telemetry"]`
- `params["chain_phase_telemetry_line"]`

Damit ist die Reihenfolge für produktive Renderer eindeutig:

1. Geometry-IR auswählen.
2. Policy-Schlussphase anwenden.
3. R5-Telemetrie protokollierbar machen.
4. Final rendern.

## Zusätzlicher Vergleichs-/Regressionsschutz

Der AC0130-Pfad wurde im Zuge der R5-Zieltests korrigiert: AC0030-artige, geometrisch vollständige Beschreibungen setzen nun keine verdeckte `top_source_ref="AC0030"`-Referenz mehr, sondern bleiben im Geometry-IR-/Composite-Pfad ohne Donor-Top-Source. Dadurch bleibt die Trennung zwischen Geometriekette und Referenz-/Policy-Fallback schärfer.

## Ausgeführte Checks

### R5-Detailtests

```bash
PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_chain_telemetry_helpers.py tests/detailtests/test_policy_phase_helpers.py tests/detailtests/test_geometry_ir_optimizer_helpers.py tests/detailtests/test_composite_svg_helpers.py tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py
```

Ergebnis: `19 passed in 0.30s`
Log: `artifacts/converted_images/reports/pr_r5_chain_telemetry_detailtests_2026-05-28_runLQ.log`

### Gezielte AC0120/AC0130/AC0030 Vergleichstests

```bash
PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py::test_build_geometry_ir_maps_ac0130_like_description_to_ordered_chain tests/detailtests/test_geometry_ir_helpers.py::test_build_geometry_ir_maps_ac0120_self_description_to_plus_minus_chain tests/detailtests/test_description_contract_helpers.py::test_description_parser_attaches_geometry_ir_for_ac0120_like_description tests/test_image_composite_converter.py::test_parse_description_does_not_misread_ac0130_text_as_top_source_ref tests/detailtests/test_conversion_execution_helpers.py::test_convert_one_impl_uses_implicit_sample_svg_for_non_composite_placeholder_status
```

Ergebnis: `5 passed, 5 warnings in 0.77s`
Log: `artifacts/converted_images/reports/ac0120_ac0130_ac0030_r5_targeted_tests_2026-05-28_runLQ.log`

### Vollsuite

```bash
PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs
```

Ergebnis: `560 passed, 5 warnings in 5.03s`
Log: `artifacts/converted_images/reports/pytest_full_2026-05-28_runLQ.log`

## Vorher/Nachher-Kennzahlen

| Kennzahl | Vor PR-R5 | Nach PR-R5 |
| --- | --- | --- |
| Detailtest-Abdeckung Ketten-Telemetrie | nicht vorhanden | `3` neue R5-Tests, `19` Detailtests im R5-Sicherungsset grün |
| Vollsuite | Run LP: `557 passed, 5 warnings` | Run LQ: `560 passed, 5 warnings` |
| Phasenbegriffe | verteilt (`fallback`, `sample`, `policy`, `geometry`) | harmonisierte Labels für Geometry-, Policy- und Emergency-Phase |
| Step-Erfolgsrate | nur Optimizer-Step-Log | `step_success_rate` + Aggregation |
| Override-Häufigkeit | implizit aus Policy-Feldern ableitbar | `override_frequency` aggregierbar |
| Placeholder-Notfallrate | nicht zentral | `placeholder_emergency_rate` aggregierbar |

## Offene Restpunkte

- Produktive Laufberichte können die neue `chain_phase_telemetry_line` künftig in Batch-/CSV-Reports übernehmen.
- Reale Sample-Vergleichsmetriken können später als zusätzliche Felder neben `initial_error`/`final_error` in die R5-Telemetrie geschrieben werden.

## Fazit

PR-R5 ist umgesetzt und durch Detailtests, gezielte AC0120/AC0130/AC0030-Vergleichstests sowie die Vollsuite abgesichert. Die Ketten-Architektur hat jetzt eine reproduzierbare, datenbasierte Abnahmespur.
