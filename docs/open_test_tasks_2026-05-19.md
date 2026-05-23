# Offene Test-Aufgaben (Stand 2026-05-19)

Ziel: Einen stabilen, schnell laufenden Testblock grün halten und die aktuell bekannten Problemfälle separat nachverfolgen.

## Stabil laufender Testblock
Folgende Tests laufen aktuell grün (unter Python 3.10.20):

```bash
PYENV_VERSION=3.10.20 pytest -q \
  tests/detailtests/test_conversion_execution_helpers.py \
  tests/detailtests/test_iteration_setup_helpers.py \
  tests/detailtests/test_quality_config_helpers.py
```

Ergebnis: `17 passed, 3 xfailed`.

## Als Aufgaben extrahierte (xfail) Problemfälle

### TASK-1: Failed-SVG bei `semantic_mismatch` wird nicht geschrieben ✅ (2026-05-21 erledigt)
- Test: `test_convert_one_impl_semantic_mismatch_is_reported_as_failure`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` wird erzeugt und enthält das eingebettete Fallback-SVG.

### TASK-2: Failed-SVG bei unbekanntem/non-success Status wird nicht geschrieben ✅ (2026-05-21 erledigt)
- Test: `test_convert_one_impl_unknown_status_is_recorded_as_failure`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` wird erzeugt und enthält das eingebettete Fallback-SVG.

### TASK-3: Failed-SVG bei trivialem Placeholder wird nicht geschrieben ✅ (2026-05-21 erledigt)
- Test: `test_convert_one_impl_trivial_placeholder_svg_is_marked_failed`
- Datei: `tests/detailtests/test_conversion_execution_helpers.py`
- Erwartung: `Failed_<name>.svg` existiert nach Verarbeitung.


### TASK-4: Satisfactory-Baseline-Regressionstest scheitert ohne Testdaten-Setup ❌ (neu 2026-05-23)
- Test: `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`
- Beobachtung: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Erwartung: Test soll entweder reproduzierbar die benötigte Baseline vorbereiten oder bei fehlenden Artefakten sauber `skippen` statt als Hard-Fail zu enden.
- Repro:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
- Artefakt: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runID.log`.


### TASK-5: Global-Search-Kleingewinn-Repro ist flaky/unter Zielschwelle ❌ (neu 2026-05-23)
- Test: `tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_does_not_count_small_relevant_gain_as_no_improvement`
- Beobachtung: Assertion `float(params["arm_x1"]) >= 1.10` schlägt fehl (`1.052784303601394`).
- Erwartung: Optimierungslogik soll bei kleinem relevantem Gewinn konsistent über die Zielschwelle verbessern oder der Test muss auf stabile, deterministische Akzeptanzkriterien umgestellt werden.
- Repro:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. pyenv exec pytest -q --maxfail=1`
- Artefakt: `artifacts/converted_images/reports/pytest_full_maxfail1_2026-05-23_runID.log`.

## Empfohlener Abarbeitungsmodus
1. Produktionslogik für File-Emission in `convertOneImpl` vereinheitlichen (ein zentraler Write/Move-Pfad für Failed-SVG).
2. Jeden Task einzeln fixen und mit `-k` gezielt validieren.
3. Nach jedem Fix `xfail` entfernen und Test auf normal `pass` umstellen.
4. Danach wieder größeren Block laufen lassen.


## Neu: Blockierende Tests aus der Gesamtliste als Aufgaben (2026-05-23)

Die folgenden `blocking_conversion`-Tests werden **nicht** mehr als Teil einer allgemeinen Grün-Testliste behandelt, sondern als explizite Aufgaben geführt.

- [ ] BC-01: `tests/test_image_composite_converter.py::test_semantic_validation_accepts_circle_supported_by_local_mask`
- [ ] BC-02: `tests/test_image_composite_converter.py::test_detect_semantic_primitives_detects_vertical_connector_without_arm`
- [ ] BC-03: `tests/test_image_composite_converter.py::test_semantic_validation_accepts_text_supported_by_local_mask`
- [ ] BC-04: `tests/test_image_composite_converter.py::test_semantic_validation_ignores_structural_false_positives_for_plain_circle_badge`
- [ ] BC-05: `tests/test_image_composite_converter.py::test_make_badge_params_reanchors_ac0811_l_stem_after_template_center_lock`
- [ ] BC-06: `tests/test_image_composite_converter.py::test_run_iteration_pipeline_converts_non_composite_as_embedded_svg`
- [ ] BC-07: `tests/test_image_composite_converter.py::test_validate_semantic_description_alignment_rejects_non_semantic_cross_shape`
- [ ] BC-08: `tests/test_image_composite_converter.py::test_validate_semantic_description_alignment_accepts_ac0813_vertical_connector`
- [ ] BC-09: `tests/test_image_composite_converter.py::test_convert_range_writes_svgs_and_diffs_to_dedicated_subfolders`
- [ ] BC-10: `tests/test_image_composite_converter.py::test_circle_error_uses_stable_source_mask_for_radius_candidates`
- [ ] BC-11: `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0223_m_circle_in_lower_half`
- [ ] BC-12: `tests/test_image_composite_converter.py::test_validate_semantic_alignment_accepts_vertical_circle_when_raw_hough_misses`
- [ ] BC-13: `tests/test_image_composite_converter.py::test_validate_semantic_alignment_accepts_ac0838_large_top_connector_voc_variant`
- [ ] BC-14: `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`
- [ ] BC-15: `tests/test_image_composite_converter.py::test_validate_semantic_alignment_accepts_merged_co2_blob_for_ac0831_artifact`
- [ ] BC-16: `tests/test_image_composite_converter.py::test_convert_range_uses_existing_conversion_rows_as_template_donors`
- [ ] BC-17: `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`
- [ ] BC-18: `tests/test_image_composite_converter.py::test_parse_description_manual_review_clears_default_label_for_unclassified_sia_symbol`
- [ ] BC-19: `tests/test_satisfactory_regression_battery.py::test_satisfactory_baseline_reconversion_smoke`
- [ ] BC-20: `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`

Akzeptanz pro BC-Task: reproduzierbarer Einzel-Repro + stabiler `passed`-Status ohne `skip/xfail` im Profil `research` oder Rückführung in `core-green`.


## Session-Update 2026-05-23 (Run IJ: nächste Aufgabe + Volltest + Blocking-Inventory)

- A3-Repro erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
  - Ergebnis: `1 failed, 5 warnings`, Exit `1`.
  - Blocker unverändert: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Volltest erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q -rs`
  - Ergebnis: kein finales Summary im Zeitfenster; Fortschritt erneut bis `91%`.
  - Sichtbar im Lauf: mindestens 11 Skip-Marker (`s`).
- Blocker-Inventar (collect-only) aktualisiert:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. pyenv exec python -m pytest --collect-only -q -m blocking_conversion`
  - Ergebnis unverändert: 20 `blocking_conversion`-Tests.

### Neu in Aufgabenform überführt (Run IJ)
- [ ] **A1-FU3:** Skip-NodeIDs des Run-IJ-Volltests mit `-rs`/Teilbatch vollständig auflösen (nicht nur Marker zählen).
  - **Akzeptanz:** vollständige NodeID-Liste + je Test Entscheidung (Fixture bereitstellen vs optional markieren).
- [ ] **A3-FU3:** Satisfactory-Baseline-Setup automatisieren oder fehlende Baseline als expliziten `skip` statt Hard-Fail behandeln.
  - **Akzeptanz:** der A3-Zieltest läuft in 2 direkten Wiederholungen ohne `FileNotFoundError` und mit finalem Summary.
- [ ] **A6-FU3:** 300s-Vollsuite-Limitierer ab ~91% durch NodeID-Teilbatches isolieren.
  - **Akzeptanz:** reproduzierbarer Limitierer dokumentiert inkl. Laufzeitprofil **oder** Vollsuite endet unter 300s mit finalem Summary.
- [ ] **BC-Inventory-FU1:** 20 `blocking_conversion`-Tests aus dem aktuellen Collect-only-Lauf als laufend verifiziert markieren (kein Rückgang/Anstieg unbemerkt).
  - **Akzeptanz:** Anzahl und NodeID-Liste sind in jedem Folgelauf diffbar dokumentiert.

## Session-Update 2026-05-23 (Run IK: Re-Run nächste Aufgabe + Volltest)

- A3-Repro erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
  - Ergebnis: weiterhin `1 failed, 5 warnings`; Root cause unverändert (`FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`).
- Volltest erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q -rs`
  - Ergebnis: Exit `124`; kein finales Summary im Zeitfenster, Laufstand erneut im Bereich `~91%`.

### Neu in Aufgabenform überführt (Run IK)
- [ ] **A3-FU4:** `_prepare_mini_baseline` für fehlendes `BASE/images` hart machen (Verzeichnis anlegen/kopieren) oder den Test bei fehlender Quellbasis kontrolliert `skippen`.
  - **Akzeptanz:** Zwei direkte Re-Runs des A3-Tests ohne `FileNotFoundError`; Ergebnis ist `passed` oder explizit begründeter `skipped`.
- [ ] **A6-FU4:** Vollsuite-Timeout bei 300s weiterhin reproduziert; den Verursacherbereich nach `91%` via NodeID-Chunking (`--maxfail=1` + `-k`/Dateibatches) isolieren.
  - **Akzeptanz:** Mindestens ein konkreter limitierender Testfall oder ein klarer enger Kandidatenblock dokumentiert.
