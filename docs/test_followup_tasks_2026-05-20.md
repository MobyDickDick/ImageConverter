# Test-Follow-up-Aufgaben (nur echte Grün-Tests in der Kernliste)

Datum: 2026-05-20  
Basis: letzter vollständiger grüner Suite-Lauf mit Python 3.10 (`pytest -q`).

## Session-Update 2026-05-21 (nicht-grüner Lauf explizit nachgeführt)

- Reproduzierter Kontrolllauf: `timeout 300 python -m pytest -q`
- Ergebnis: Lauf erreichte in 300s kein finales `pytest`-Summary und endete mit Exit `124` (Timeout), bei sichtbarem Zwischenstand mit weiterhin vorhandenen `xfailed` (`x`) und `skipped` (`s`) Markern.
- Einordnung: Dieser Lauf zählt **nicht** als „wirklich grün“ und bleibt als Follow-up-Aufgabe offen.


## Session-Update 2026-05-21 (Teilabschluss A1/A2/A4, Collect-only-Inventar)

- Reproduzierbarer Inventarlauf für aktuell ausgeblendete `blocking_conversion`-Tests durchgeführt:
  - `python -m pytest --collect-only -q -m blocking_conversion`
  - Ergebnis: `20/867 tests collected (847 deselected)` in `5.98s`.
- Die aktuell 20 `blocking_conversion`-NodeIDs wurden vollständig namentlich erfasst (siehe Liste unten unter **A2**).
- Warnungsbild erneut verifiziert (unverändert 5 Deprecation-Warnungen zu `SwigPyPacked`, `SwigPyObject`, `swigvarlink`).


## Session-Update 2026-05-21 (A6-Teilfortschritt: 300s-Batching durchgeführt)

- Teilbatch ohne `tests/test_image_composite_converter.py` reproduzierbar grün innerhalb des 300s-Limits:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q tests/detailtests tests/test_image_composite_converter_element_decomposition.py tests/test_image_composite_converter_naming.py tests/test_weak_family_pipeline.py tests/test_shape_detection_vertical_lines.py tests/test_conversion_regression_smoke.py tests/test_shape_detection_classification.py tests/test_retry_failed_image_conversions.py tests/test_shape_detection_colors.py tests/test_generate_form_code_inventory.py tests/test_shape_detection_eval.py tests/test_satisfactory_regression_battery.py`
  - Ergebnis: `521 passed, 1 skipped, 5 warnings`, Exit `0`, Laufzeit `236s`.
- Isolierter Batch für `tests/test_image_composite_converter.py` weiterhin nicht innerhalb des 300s-Limits abschließbar:
  - `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q tests/test_image_composite_converter.py`
  - Ergebnis: Exit `124` (Timeout bei `300s`), kein finales Summary.
- Ableitung: Der aktuell langsamste/limitierende Block für A6 ist `tests/test_image_composite_converter.py`; weitere Repros sollten auf NodeID-/Marker-Ebene in genau dieser Datei aufgesplittet werden.


## Session-Update 2026-05-22 (A3-Stabilitäts-Repro)

- Repro-Lauf für den zuletzt temporär grünen A3-Kandidaten erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 python -m pytest -q tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`
  - Ergebnis: `1 xfailed, 5 warnings`, Exit `0`, Laufzeit `186.69s`.
- Log-Artefakt: `artifacts/converted_images/reports/TB_A3_xfail_probe_2026-05-22_runHY.log`.
- Einordnung: A3 bleibt offen; der Test ist aktuell nicht stabil reproduzierbar grün.

## Ziel

Nur **wirklich grüne** Tests sollen als stabile Kern-Testliste gelten.  
Alles andere (skip/deselect/xfail/warnings) wird hier als explizite Aufgabe geführt.

## Snapshot (Ist-Stand)

- `842 passed`
- `4 skipped`
- `18 deselected`
- `3 xfailed`
- `5 warnings`

## Aufgaben aus Nicht-Grün-Ergebnissen

### A1 – Skipped-Tests eliminieren oder eindeutig als optionale Fixture-Tests markieren
- [x] Alle 4 `skipped` Tests identifizieren und je Test entscheiden: (2026-05-21: Skip-Kandidatenquellen eingegrenzt auf AC0800-Smoke-Placeholder, optionale Baseline-Fixture-Pfade in `tests/test_satisfactory_regression_battery.py` und Import-/Fixture-abhängige Shape/AC08-Tests; Entscheidungsdokumentation gestartet).
  - [ ] Entweder Fixture/Umgebung in CI bereitstellen (damit Test wieder grün läuft),
  - [ ] oder Test dauerhaft in eine klar benannte optional-suite verschieben (`@pytest.mark.optional_fixture`).
- [x] Für jeden Skip-Grund eine reproduzierbare Anleitung in `docs/` ergänzen. (2026-05-21: Leitfaden unter `docs/skip_repro_guide_2026-05-21.md` ergänzt.)

### A2 – Deselected-Tests in explizite Testprofile überführen
- [x] Die 18 `deselected` Tests namentlich erfassen. (2026-05-21 aktualisiert: aktueller Collect-only-Stand zeigt 20 `blocking_conversion`-Tests; Liste unten ergänzt.)

- Erfasste `blocking_conversion`-NodeIDs (Stand 2026-05-21):
  1. `tests/test_image_composite_converter.py::test_semantic_validation_accepts_circle_supported_by_local_mask`
  2. `tests/test_image_composite_converter.py::test_detect_semantic_primitives_detects_vertical_connector_without_arm`
  3. `tests/test_image_composite_converter.py::test_semantic_validation_accepts_text_supported_by_local_mask`
  4. `tests/test_image_composite_converter.py::test_semantic_validation_ignores_structural_false_positives_for_plain_circle_badge`
  5. `tests/test_image_composite_converter.py::test_make_badge_params_reanchors_ac0811_l_stem_after_template_center_lock`
  6. `tests/test_image_composite_converter.py::test_run_iteration_pipeline_converts_non_composite_as_embedded_svg`
  7. `tests/test_image_composite_converter.py::test_validate_semantic_description_alignment_rejects_non_semantic_cross_shape`
  8. `tests/test_image_composite_converter.py::test_validate_semantic_description_alignment_accepts_ac0813_vertical_connector`
  9. `tests/test_image_composite_converter.py::test_convert_range_writes_svgs_and_diffs_to_dedicated_subfolders`
  10. `tests/test_image_composite_converter.py::test_circle_error_uses_stable_source_mask_for_radius_candidates`
  11. `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0223_m_circle_in_lower_half`
  12. `tests/test_image_composite_converter.py::test_validate_semantic_alignment_accepts_vertical_circle_when_raw_hough_misses`
  13. `tests/test_image_composite_converter.py::test_validate_semantic_alignment_accepts_ac0838_large_top_connector_voc_variant`
  14. `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`
  15. `tests/test_image_composite_converter.py::test_validate_semantic_alignment_accepts_merged_co2_blob_for_ac0831_artifact`
  16. `tests/test_image_composite_converter.py::test_convert_range_uses_existing_conversion_rows_as_template_donors`
  17. `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`
  18. `tests/test_image_composite_converter.py::test_parse_description_manual_review_clears_default_label_for_unclassified_sia_symbol`
  19. `tests/test_satisfactory_regression_battery.py::test_satisfactory_baseline_reconversion_smoke`
  20. `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality`

- [x] In `pytest.ini`/Runner-Skripten feste Profile definieren: (2026-05-21: Profil-Runner `tools/run_pytest_profile.py` ergänzt; Profile `core-green`, `extended`, `research` implementiert.)
  - [x] `core-green` (nur harte grüne Tests),
  - [x] `extended` (inkl. langsam/optional),
  - [x] `research` (experimentell).
- [x] Sicherstellen, dass `core-green` keine impliziten Deselections mehr enthält. (2026-05-21: globales `pytest.ini`-`addopts` entfernt; Markerfilter werden nur noch explizit über den Profil-Runner gesetzt.)

### A3 – XFail-Tests in echte Qualitäts-Tasks auflösen
- [ ] Alle 3 `xfailed` Tests inkl. Grund dokumentieren.
- [ ] Für jeden `xfail` ein Akzeptanzkriterium definieren, wann zurück auf normalen Assert.
- [ ] Ziel: `xfail` schrittweise auf `0` reduzieren.

### A4 – Warnings auf Null bringen (oder strikt erlaubte Liste pflegen)
- [x] Die 5 Warnungen (aktuell `SwigPyPacked/SwigPyObject/swigvarlink` Deprecations) technisch bewerten. (2026-05-21: Warnungsbild in `pytest --collect-only` und Zieltestlauf bestätigt; Quelle ist weiterhin `<frozen importlib._bootstrap>:241` über PyMuPDF/SWIG-Bindings.)
- [ ] Entweder:
  - [ ] Ursache beheben (Abhängigkeiten/Bindings aktualisieren), oder
  - [ ] temporär als bekannte, explizit erlaubte Warnungen dokumentieren.
- [ ] Mittelfristig CI-Profil mit `-W error` für `core-green` vorbereiten.


### A5 – Laufzeitüberschreitungen strikt als Follow-up-Aufgaben behandeln
- [x] Alle Testfälle mit Laufzeitüberschreitung (`_PerTestTimeout`) täglich aus dem `pytest`-Output extrahieren und in einer eigenen Liste erfassen (NodeID + Dauergrenze). (2026-05-21: Inventar unter `docs/per_test_timeout_inventory_2026-05-21.md` angelegt.)
- [x] Für jeden Timeout-Fall genau **eine** Folgeaufgabe mit Akzeptanzkriterium anlegen (z. B. „<30s in Python 3.10.20“). (2026-05-21: 1:1-Zuordnung + Akzeptanzkriterien in `docs/per_test_timeout_inventory_2026-05-21.md` dokumentiert.)
- [ ] Timeout-Fälle dürfen nicht als „nur Umgebung langsam“ verbucht werden; sie gelten bis zur Auflösung als offene Qualitätsaufgabe.
- [ ] Nach Stabilisierung: Timeout-Marker entfernen und Test zurück in `core-green` überführen.

### A6 – `pytest -q` in 300s wieder deterministisch zum Endsummary bringen
- [x] Timeout-Lauf vom 2026-05-21 (`timeout 300 python -m pytest -q`, Exit `124`) in Teilbatches aufspalten und den langsamsten Block identifizieren. (2026-05-21: Batch-Split durchgeführt; limitierender Block ist `tests/test_image_composite_converter.py`, Einzelbatch endet weiterhin mit Exit `124` bei 300s.)
- [ ] Für den langsamsten Block einen reproduzierbaren Einzel-Repro (NodeID oder Marker-Subset) dokumentieren.
- [ ] Akzeptanz: Ein erneuter Suite-Lauf mit identischem 300s-Limit endet mit finalem `pytest`-Summary statt Exit `124`.

## Definition „wirklich grün“

Ein Test zählt nur als **wirklich grün**, wenn er:
1. ausgeführt wurde,
2. `passed` ist,
3. nicht `skip`/`xfail`/`deselect` ist,
4. und keine Warnung erzeugt (für das Kernprofil).

## Session-Update 2026-05-23 (Run IF: nächste Aufgabe + Volltest)

- Repro-Lauf der nächsten dokumentierten Aufgabe erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
  - Ergebnis: `1 failed, 5 warnings`, Exit `1`.
  - Blocker: `FileNotFoundError` für `artifacts/regression_baseline/satisfactory/images`.
- Zusätzlicher Volltestlauf ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q`
  - Ergebnis: Exit `124` (Timeout), weiterhin kein finales Summary.

### Neu/konkretisierte Folgeaufgaben aus den blockierenden oder misslungenen Tests

- [ ] **A3-FU1 (Setup-Baseline deterministisch):** Vor dem A3-Zieltest die Baseline-Bilder reproduzierbar bereitstellen (`artifacts/regression_baseline/satisfactory/images` mit verwertbaren Testbildern statt leer/missing).
  - **Akzeptanzkriterium:** `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` läuft mindestens in zwei direkten Wiederholungen ohne `FileNotFoundError` und endet jeweils mit finalem `pytest`-Summary.
- [ ] **A6-FU1 (300s-Volltest entblocken):** Den Timeout-Limitierer im Volltestlauf (`timeout 300 ... pytest -q`) weiter per NodeID-/Marker-Batches eingrenzen und einen reproduzierbaren Teilrepro inkl. Laufzeitgrenze dokumentieren.
  - **Akzeptanzkriterium:** Ein Vollsuite-Lauf mit identischem 300s-Limit endet mit finalem Summary statt Exit `124`.


## Session-Update 2026-05-23 (Run IE: nächste Aufgabe + Vollsuite erneut)

- Nächste dokumentierte Aufgabe erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
  - Ergebnis: `1 failed, 5 warnings`, Exit `1` (statt `xfail`).
  - Primärer Blocker unverändert: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.
- Vollsuite erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q`
  - Ergebnis: kein finales Summary innerhalb 300s (nicht erfolgreich abgeschlossen), Fortschritt bis `91%`.
  - Im Protokoll sichtbar: mindestens `11` Skip-Marker (`s`).

### Neue/aktualisierte Aufgaben aus übersprungenen, fehlgeschlagenen und blockierenden Tests

- [ ] **A1-FU2 (Skips aus Vollsuite auflösen):** Die im Run-IE-Vollsuiteprotokoll sichtbaren Skip-Kandidaten (`>=11` Marker) per `pytest -rs` exakt als NodeIDs erfassen und je Test in „Fixture bereitstellen“ vs. „optional markieren“ überführen.
  - **Akzeptanzkriterium:** Für alle in Run IE sichtbaren Skip-NodeIDs liegt eine dokumentierte Entscheidung + Repro-Schritt vor.
- [ ] **A3-FU2 (Fehlschlag statt XFail stabilisieren):** Den A3-Test wieder auf reproduzierbare Vorbedingungen bringen (Baseline-Verzeichnis + Mindestinhalt), sodass der Test nicht mehr mit `FileNotFoundError` abbricht.
  - **Akzeptanzkriterium:** `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` läuft in 2 direkten Wiederholungen ohne Exception-Abbruch durch und liefert jeweils ein finales Pytest-Summary.
- [ ] **A6-FU2 (Blockierenden Langläufer isolieren):** Für den 300s-Timeout in der Vollsuite den bremsenden Restbereich ab ~`91%` mit NodeID-Teilbatches auflösen.
  - **Akzeptanzkriterium:** Reproduzierbarer Teilbatch inkl. Laufzeitprofil dokumentiert **oder** Vollsuite mit identischem 300s-Limit endet mit finalem Summary.

## Session-Update 2026-05-23 (Run IJ: nächste dokumentierte Aufgabe erneut)

- Nächste dokumentierte Aufgabe erneut ausgeführt:
  - `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`
  - Ergebnis: `1 failed, 5 warnings`, Exit `1`.
  - Primärer Blocker unverändert: `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`.

### Neue/konkretisierte Aufgaben aus misslungenen, übersprungenen oder blockierenden Tests

- [ ] **A3-FU3 (Baseline-Guard im Testpfad):** Vor dem Aufruf von `converter.main(...)` sicherstellen, dass der erwartete Eingabeordner `artifacts/regression_baseline/satisfactory/images` existiert und mindestens eine verwertbare Datei enthält; andernfalls deterministisch mit klarer Setup-Fehlermeldung abbrechen.
  - **Akzeptanzkriterium:** Der A3-Repro endet in 2 direkten Wiederholungen ohne `FileNotFoundError`; Ergebnis ist entweder valider Assert-Lauf oder klarer, reproduzierbarer Setup-Fehler mit finalem Pytest-Summary.
- [ ] **A4-FU1 (Warnungen im A3-Repro auflösen/klassifizieren):** Die weiterhin sichtbaren 5 SWIG-Deprecation-Warnungen im A3-Repro entweder technisch beheben oder explizit als erlaubte Übergangswarnungen dokumentieren.
  - **Akzeptanzkriterium:** A3-Repro liefert entweder `0 warnings` oder eine verlinkte Allowlist-Entscheidung inkl. Begründung pro Warnungstyp.
- [ ] **A1-FU3 (Skip-Pfad nach Baseline-Fix verifizieren):** Nach Bereitstellung der Baseline den Fall `No baseline variants found.` gezielt reproen und als expliziten Skip-Kandidaten (NodeID + Entscheidungsweg) dokumentieren.
  - **Akzeptanzkriterium:** Für den Skip-Text liegt ein reproduzierbarer NodeID-Lauf mit dokumentierter Einordnung „Fixture bereitstellen“ oder „optional markieren" vor.
