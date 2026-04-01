# Open Tasks

This checklist only tracks work that is actionable for the ImageConverter in the
current repository snapshot. Older unrelated language/compiler/runtime tasks were removed so the list stays
focused on the actual project scope.

## How to use this list

- Work from top to bottom unless a dependency requires a different order.
- When a task is completed, change its checkbox to `- [x]` and add a short note.
- If a task splits into multiple deliverables, keep the parent item and add nested
  subtasks below it.

## Current status

- The latest committed AC08 report snapshot now contains `10` evaluated AC08 validation logs, and all `10` are `semantic_ok` (`0` `semantic_mismatch`).
- The refresh run currently covers the most recently touched connector/circle families present in `artifacts/converted_images/reports` (`AC0811`, `AC0832`, `AC0835`, `AC0836`, `AC0870`, `AC0882`).
- Continue to add new work items here before implementation starts, then mark them in-place when they are done.

## Next tasks (added 2026-03-28)

- [ ] C1: `src/imageCompositeConverter.py` schrittweise in Module mit Blöcken von ca. 100 Zeilen aufteilen.
  - Hintergrund: Die Datei hat aktuell deutlich über 10k Zeilen; Refactoring erfolgt bewusst in mehreren, testbaren Teilschritten statt als Big-Bang.
  - Vorgehen: pro Teilbereich (z. B. Regionen-Analyse, IO/Reporting, Rendering, Optimierung, CLI) jeweils ein neues Modul mit klarer API erstellen und im Hauptskript nur noch schlanke Delegation belassen.
  - Akzeptanzkriterium für jeden Teilschritt: bestehende Tests laufen weiter, externe Funktionsnamen bleiben kompatibel, und der offene Aufgabenstand wird hier dokumentiert.
- [ ] C1.1: Erste Extraktion abgeschlossen: Regionen-Analyse/Annotierung aus dem Monolithen ausgelagert.
  - 2026-03-29: Start umgesetzt mit neuem Modul `src/imageCompositeConverterRegions.py`.
  - `detect_relevant_regions`, `annotate_image_regions` und `analyze_range` delegieren im Monolithen jetzt auf die neue Modul-Implementierung.
  - 2026-04-01: Optionale Dependency-/Import-Hilfen in neues Modul `src/imageCompositeConverterDependencies.py` ausgelagert; der Monolith enthält nur noch kompatible Delegations-Wrapper (`camelCase` + `snake_case`).
  - 2026-04-01: Bereichs-/Filter-Helfer (`_extractRefParts` bis `_inRequestedRange`) in `src/imageCompositeConverterRange.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantik-Parser-Helfer in neues Modul `src/imageCompositeConverterSemantic.py` ausgelagert; `Reflection.parseDescription` delegiert die Family-Regeln plus Layout-/Alias-Extraktion weiterhin kompatibel über Wrapper.
  - Nächster geplanter Schritt: semantische Prüf- und Optimierungsblöcke in denselben kleinen Schritten extrahieren.

- [x] B1: PyMuPDF-Ressourcen im Fallback-Diff-Pfad sauber schließen.
  - `_create_diff_image_without_cv2` nutzt jetzt Context-Manager für beide `fitz.open(...)` Dokumente, damit Batch-Läufe keine unnötig offenen MuPDF-Dokumente ansammeln.
  - Ziel: Stabilere AC08-Serienläufe ohne native MuPDF-Stackoverflow-Ausreißer durch Ressourcenaufbau über viele Dateien.
- [ ] B2: AC08-Batchlauf mit vollständigem Bereich `AC0800..AC0899` nach B1 erneut ausführen und Crash-Freiheit dokumentieren.
  - 2026-03-28: Vollbereichslauf erneut gestartet mit
    `python -u -m src.imageCompositeConverter ... --start AC0800 --end AC0899`
    und Log nach `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-03-28.log` geschrieben.
  - 2026-03-29 (Lauf A): Erneuter Vollbereichslauf mit identischem Befehl und Log nach
    `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-03-29.log` geschrieben.
  - 2026-03-29 (Lauf B, Verifikation): gleicher Befehl erneut ausgeführt, diesmal reproduzierbarer Abbruch mit
    `MuPDF error: exception stack overflow!` und Shell-Exit-Code `139` (Segmentation Fault).
  - Dokumentierte Reproduktion: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-03-29_repro.log`
    und Kurzprotokoll `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-03-29_repro_summary.md`.
  - 2026-03-29 (Lauf C, erneuter Retry): gleicher Vollbereichs-Befehl erneut ausgeführt, diesmal Exit-Code `0`.
    Der Lauf blieb aber semantisch nicht vollständig erfolgreich (`batch_failure_summary.csv`: `AC0838_S` als `semantic_mismatch`).
  - 2026-03-29 (Lauf E, erneute Verifikation mit Log-Mitschnitt): gleicher Vollbereichs-Befehl per `tee` erneut ausgeführt;
    reproduzierbarer Abbruch mit `MuPDF error: exception stack overflow!` und Exit-Code `139` (`Segmentation fault`).
  - Dokumentation für Lauf E: `docs/ac0800_ac0899_runE_2026-03-29_summary.md`
    (inkl. Kommando, Exit-Code und letzter sichtbarer Datei vor dem Crash).
  - 2026-03-29 (Lauf F, erneuter Vollbereichscheck): gleicher Vollbereichs-Befehl per `tee` erneut ausgeführt; diesmal Exit-Code `0` ohne MuPDF-Segfault, aber semantischer Stop bei `AC0838_M.jpg` (`semantic_mismatch`).
  - Dokumentation für Lauf F: `docs/ac0800_ac0899_runF_2026-03-29_summary.md`
    (inkl. Kommando, Exit-Code und Verweis auf `batch_failure_summary.csv`).
  - Qualitätsvergleich gegen den vorherigen Commit-Stand (`pixel_delta2_ranking.csv`, nur `AC08*`):
    `51` gemeinsame Varianten, davon `50` unverändert und `1` verbessert (`AC0800_S`: `4980.680176` -> `1429.839966`),
    **keine** verschlechterte Variante.
  - Status: Crash-Freiheit für den Vollbereich ist **nicht** nachgewiesen; B2 bleibt offen bis der Lauf stabil Exit-Code `0` liefert.
- [ ] B2.1: MuPDF-Stackoverflow/Segfault im Vollbereich `AC0800..AC0899` isolieren und robusten Guard ergänzen.
  - Die bisherigen B1-Fixes (Context-Manager im Fallback-Diff-Pfad) reichen für den Vollbereich noch nicht aus.
  - Die Rendering-Stabilisierung muss den nativen Crash im Haupt-Renderpfad (`render_svg_to_numpy`) verhindern.
  - 2026-03-29: Optionaler Subprozess-Guard für `render_svg_to_numpy` ergänzt (`--isolate-svg-render`), inklusive Fallback auf In-Process-Render wenn der isolierte Worker fehlschlägt.
  - Offener Nachweis: Vollbereich `AC0800..AC0899` mit aktiviertem Guard erneut laufen lassen und Crash-Freiheit dokumentieren.
- [ ] B3: Deterministischen Diagnosemodus für die Dateireihenfolge ergänzen (ohne `shuffle`), um schwer reproduzierbare Batchfehler schneller zu isolieren.



## Kelle-/Optimierungs-Backlog (neu aus dem Umsetzungscheck)

- [x] A1: Gemeinsamen Parametervektor für globale Optimierung einführen.
  - Added `GlobalParameterVector` as a central structure for geometry/text optimization fields (`cx`, `cy`, `r`, arm/stem, text position/scale), including param round-tripping.
  - Added central bounds/lock metadata via `_global_parameter_vector_bounds` and per-round debug logging with `_log_global_parameter_vector`.
  - Wrapped the existing circle adaptive/stochastic optimizers to read/write through the shared vector abstraction.
- [x] A2: Globalen Mehrparameter-Suchmodus ergänzen (nicht nur Kreis-Pose).
  - Added `Action._optimize_global_parameter_vector_sampling` as a reproducible baseline search that samples and shrinks multiple unlocked dimensions from `GlobalParameterVector` jointly (`cx`, `cy`, `r`, `stem_*`, `text_*`).
  - Added per-round progress logs for `best_err`, accepted candidates, and the active parameter subset, plus a final delta summary for changed dimensions.
  - Integrated the new mode into the existing optimization loop behind `enable_global_search_mode`, so the global pass can be activated without changing default conversion behavior.
- [x] A3: Near-Optimum-Plateau auf den globalen Parameterraum verallgemeinern.
  - Added a formal near-optimum definition in the global optimizer logs (`err <= best_err + epsilon`, with `epsilon=max(0.06, best_err*0.02)`).
  - Added per-round global plateau persistence and instrumentation in `_optimize_global_parameter_vector_sampling`, including point count, per-parameter spans, mean span, and a stability hint.
  - Added regression coverage that checks near-optimum plateau logging for multi-round global runs.
- [x] A4: Schwerpunkt/zentralen Repräsentanten des Plateau-Bereichs berechnen und auswählen.
  - Der globale Suchmodus berechnet jetzt pro Runde einen fehlergewichteten Plateau-Schwerpunkt und bewertet ihn gegen den Best-Sample-Kandidaten.
  - Der finale Rundensieger kann bewusst aus `schwerpunkt` oder `best_sample` stammen; die Entscheidung inkl. Begründung wird mit `global-search: plateau-repräsentant` geloggt.
  - Sicherheitslogik verwirft Schwerpunktkandidaten mit ungültiger Fehlerbewertung oder Constraint-Verletzung vor einer möglichen Übernahme.
- [x] A5: Regressionstests für globalen Suchmodus, Seeds und Constraint-Einhaltung ergänzen.
  - Added a deterministic seed regression test to ensure the global search RNG seed incorporates both `STOCHASTIC_RUN_SEED` and `STOCHASTIC_SEED_OFFSET`.
  - Added a lock/constraint regression test that verifies locked dimensions (`cx`, `text_x`, `text_y`) stay unchanged and optimized active dimensions remain within initial vector bounds.

Details und Akzeptanzkriterien stehen in `docs/kelle_umsetzungscheck.md` unter
„Abgeleitete Aufgaben (umsetzbare Roadmap)“.

## Next priority tasks

- [x] Fix the vertical-connector semantic false positives in the remaining AC08 families.
  - Target `AC0811_S`, `AC0813_L`, `AC0813_M`, `AC0831_M`, and `AC0836_L` first.
  - `AC0811_M` is now covered by the vertical-family circle-mask fallback; keep it in the next report refresh to confirm the committed artifacts match the fixed code path.
  - The current logs repeatedly report `Im Bild ist waagrechter Strich erkennbar, aber nicht in der Beschreibung enthalten`, although these families are expected to use vertical connectors or stems.
  - Primitive detection/reporting now records connector orientation classification (`vertical`/`horizontal`/`ambiguous`) plus candidate counts in semantic mismatch logs before validation fails.

- [x] Harden circle detection for small AC08 variants before the semantic gate runs.
  - `AC0811_L` is treated as a regression-safe good conversion anchor and should remain out of the weak-family backlog unless a future report explicitly regresses it.
  - The fixed AC08 regression set now loads its previously marked good variants from `artifacts/converted_images/reports/successful_conversions.txt` and reports whether any of them regressed or went missing.
  - Prioritize `AC0811_S`, `AC0814_S`, and `AC0870_S`, where the reports also contain `Beschreibung erwartet Kreis, im Bild aber nicht robust erkennbar` and/or `Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt`.
  - Reuse the local mask / foreground fallback path already proven for thin-ring cases and expose enough instrumentation to tell whether the accepted circle came from Hough, foreground mask, or family-specific fallback.
  - `_detect_semantic_primitives` now reports `circle_detection_source` (`hough`, `foreground_mask`, `family_fallback`, `none`) and semantic mismatch logs print this source together with connector classification.
  - Added a small-variant family fallback (`AC0811`/`AC0814`/`AC0870`) that validates expected template-circle ring support against the foreground mask when Hough + contour fallback both miss.
  - Added regression coverage for `AC0870_S` circle presence and for explicit `family_fallback` source reporting when Hough/foreground circle candidates are intentionally disabled.

- [x] Add a family-level semantic rule for the plain-ring family `AC0800`.
  - `AC0800` now derives `SEMANTIC: Kreis ohne Buchstabe` as an explicit semantic family instead of relying on text clues alone.
  - `AC0800_L`, `AC0800_M`, and `AC0800_S` are treated as currently optimal conversions and are locked into the AC08 regression suite so future adjustments must keep them `semantic_ok`.
  - `AC0800_S` now keeps the converted circle concentric with the template and may no longer shrink below the original template radius during circle-only validation, so the small plain-ring variant is no longer tracked as an open geometric follow-up.

- [x] Refresh the AC08 reports after the next semantic round.
  - Re-ran the affected AC08 semantic families and refreshed the committed `AC08*_element_validation.log` snapshot under `artifacts/converted_images/reports`.
  - The refreshed snapshot currently reports `10/10 semantic_ok` and no `semantic_mismatch` entries for the committed AC08 logs.
  - Updated `docs/ac08_artifact_analysis.md` so the backlog reflects the current post-fix distribution instead of the former 43/11 split.

- [x] Make the AC08 success gate actionable in the normal workflow.
  - The AC08 regression run now emits an explicit console gate status (`passed`/`failed`) including failed criterion names and `mean_validation_rounds_per_file`, so failures are visible immediately after the run.
  - The workflow/README now include a CI-/shell-friendly regression check that evaluates `ac08_success_metrics.csv` and exits non-zero when any gate criterion fails.
  - Fixed validation-round instrumentation in the AC08 success metrics (`Runde n` log parsing), and added a dedicated criterion `criterion_validation_rounds_recorded` so `mean_validation_rounds_per_file` can no longer silently stay at `0.000` in a passing gate.

## Image conversion pipeline

- [x] Publish the detailed roadmap checklist referenced from the README.
  - Added this file so roadmap tasks can now be tracked and marked complete in-repo.

- [x] Improve error positions and messages.
  - Added a structured `DescriptionMappingError` with optional `SourceSpan` metadata so malformed CSV/XML description files now report exact file/line/column locations.
  - The CLI now surfaces these diagnostics as stable `[ERROR]` messages instead of failing with ambiguous parser exceptions.
  - Added regression tests for malformed XML, malformed CSV rows, and the CLI-facing error output.

## Tooling and documentation

- [x] Improve CLI wrapper ergonomics and documentation.
  - Added a proper CLI reference in `docs/image_converter_cli.md` with canonical convert/annotate/regression/vendor commands.
  - Updated the parser help text with examples, a clearer descriptions-table flag (`--descriptions-path` alias), a named `--iterations` override, and a default input directory for non-conversion helper flows.
  - Added regression tests that lock the new help text and the documented parser behaviors.

- [x] Stabilize formatter, lints, and local documentation workflows.
  - Added `docs/image_converter_workflow.md` as the canonical local verification sequence for compile/test/CLI-help checks.
  - Added regression tests that keep the workflow document referenced from the README and lock key command anchors.
  - Re-validated the documented tooling commands against the current parser/help surface.

## AC08 follow-up work

- [x] Continue improving AC08 output quality.
  - Added the generated reports `ac08_weak_family_status.csv` and `ac08_weak_family_status.txt`, which summarize remaining AC08 weak families from `pixel_delta2_ranking.csv` together with the currently implemented mitigation status and observed log markers.
  - Revalidated the new weak-family status reporting with targeted regression tests so the documentation task now has reproducible output instead of manual notes only.
  - Kept `docs/ac08_improvement_plan.md` aligned with the new reporting artifacts and the existing mitigation heuristics.

- [x] Document that the canonical open-task list is currently empty and keep roadmap references aligned.
  - Added an explicit current-status section here and synchronized the README/documentation index wording so future work is added back to the same checklist before implementation starts.

- [x] Materialize the AC08 weak-family follow-up reports referenced by the improvement plan.
  - Regenerated `artifacts/converted_images/reports/ac08_weak_family_status.csv` and `.txt` from the current `pixel_delta2_ranking.csv` so the documented AC08 follow-up now exists as committed snapshot artifacts, not only as code/tests.
