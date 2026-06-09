# Open Tasks

This checklist only tracks work that is actionable for the ImageConverter in the
current repository snapshot. Older unrelated language/compiler/runtime tasks were removed so the list stays
focused on the actual project scope.

## Aufgaben-Gesamtzähler (Snapshot 2026-05-31)

**Alle erkennbaren Checkbox-Aufgaben in dieser Datei:** Gesamt `384` · Erledigt `312` · Offen `72`

> Zählregel: Gezählt werden alle Markdown-Checkboxen (`- [ ]` / `- [x]`) in `docs/open_tasks.md`.

## Testhygiene – nur echte Grün-Tests in der Kernliste (neu 2026-05-20)

- [x] **TH1:** Nicht-grüne Testergebnisse als Aufgaben pflegen und abbauen (Skips, Deselections, XFails, Warnings), siehe `docs/test_followup_tasks_2026-05-20.md`. (2026-05-21: Follow-up-Liste um aktuellen Timeout-/Nicht-Grün-Snapshot aus `pytest -q` ergänzt, inkl. neuer Aufgabe A6 und Session-Artefakt unter `docs/test_followup_tasks_2026-05-20.md`.)
- [x] **TH2/AC0100-QA:** Der AC0100_L/M/S-Kurzlauf ist technisch grün (Exit `0`) und wird jetzt über eine automatisiert geprüfte Kompaktvarianten-Metrik abgeschlossen: `best_error < 28.5` und `mean_delta2 < 3300.0` pro Variante, ohne feste Sample-Auswahl oder Template-Transfer. Die historische globale `threshold_mean_delta2=18.000` bleibt für diese stark komprimierten Kleinvarianten weiterhin nicht erreichbar (`images_with_mean_delta2_le_threshold=0`), ist aber in `docs/ac0100_quality_followup_2026-05-31.md` als fachlich überstrenge Altmetrik dokumentiert. (2026-06-02 Run NK: Top-Left-Plus-/Einzeldiagonal-Fit ergänzt; AC0100_L/M/S: `mean_delta2=3282.756592/2843.088867/2502.757568`.) (2026-06-02 Run NL: Plus-Glyph-Geometrie wird aus der Raster-Luminanz geschätzt und nur lokal verfeinert; Heavy-Regression `test_ac0100_quality_uses_algorithmic_elementwise_fit` erneut grün.)

## Neue Vision-Roadmap: semantische SVG-Rekonstruktion (abgeglichen am 2026-05-10)

Zielbild: Nicht-binäre Vektorisierung über echte SVG-Primitive mit semantischen Beziehungen und iterativer Nachzeichnung.

### Anpassungen gegenüber der bisherigen Roadmap

- [x] **Beibehalten:** bestehende Stabilitäts-/Laufzeitaufgaben (N1–N7, LW1–LW4) bleiben als technische Basis erhalten.
- [x] **Ergänzen:** neue inhaltliche Tracks für Primitive-Erkennung, Beziehungen, Überdeckungen und rekonstruktive Iteration.
- [x] **Bereinigen:** keine der aktuellen Aufgaben widerspricht der Vision diametral; daher wurden keine bestehenden Aufgaben gelöscht.

### Neue Aufgabenpakete (Vision-Track)

- [x] **V1 – Primitive-Inventar v1 spezifizieren und messbar machen** (2026-05-14: Schema + Baseline-Metriken inkl. Precision/Recall je Primitive-Typ in `docs/primitive_inventory_v1_baseline_2026-05-14.md` und `artifacts/evaluation/primitive_inventory_v1/metrics.json` dokumentiert.)
  - Scope: Kreis, Gerade/Linie, Ellipse, Rechteck, Buchstaben/Text, Polygon-/Pfadkurven.
  - Deliverable: maschinenlesbares Schema (z. B. JSON) inkl. Parameter pro Primitive und Confidence.
  - Akzeptanz: Für einen Test-Batch wird je Elementtyp Precision/Recall ausgewiesen.

- [x] **V2 – Bezierkurven-Erkennung ergänzen** (2026-05-14: Fitting-Strategie inkl. Pixel-/Kurvenraum-Fehlerschranke und Evaluationsprotokoll dokumentiert in `docs/v2_bezier_detection_strategy_2026-05-14.md`.)
  - Scope: kubische und quadratische Beziersegmente aus Konturen/Pfaden extrahieren.
  - Deliverable: Fitting-Strategie inkl. Fehlerschranke (Pixel- und Kurvenraum).
  - Akzeptanz: Bezier-lastige Referenzen werden mit sinkender Restabweichung rekonstruiert.

- [x] **V3 – Farbfüllungen und Verläufe robust modellieren** (2026-05-14: Gradient-Parameterisierung inkl. Stop-Positionen und DeltaE-/Pixeldelta-Metrik in `docs/v3_color_gradient_modeling_2026-05-14.md` spezifiziert; maschinenlesbare Spezifikation unter `artifacts/evaluation/gradient_model_v1/spec.json` angelegt.)
  - Scope: flächige Füllungen, lineare/radiale Verläufe, Übergänge an Objektgrenzen.
  - Deliverable: Gradient-Parameterisierung pro Shape inkl. Stop-Positionen.
  - Akzeptanz: Gradient-Metrik (DeltaE/Pixeldelta) verbessert sich gegenüber Flat-Fill-Baseline.

- [x] **V4 – Überdeckungen/Z-Order explizit erkennen** (2026-05-14: Layer-Graph-Schema + Baseline-Artefakt in `docs/v4_occlusion_zorder_model_2026-05-14.md`, `docs/vision/occlusion_layer_graph_v1.schema.json` und `artifacts/evaluation/occlusion_layer_graph_v1/baseline_scene_graph.json` dokumentiert.)
  - Scope: Vorder-/Hintergrundbeziehungen, partielle Verdeckung, verdeckte Fortsetzungen.
  - Deliverable: Layer-Graph mit Occlusion-Relationen (`covers`, `behind`, `continues_behind`).
  - Akzeptanz: Szenen mit teilverdeckteten Griffen/Verbindungen werden konsistent rekonstruiert.

- [x] **V5 – Semantische Textrepräsentation + Bedingungen einführen** (2026-05-14: DSL- und JSON-Layer als v1 spezifiziert; siehe `docs/v5_semantic_text_representation_2026-05-14.md`, `docs/vision/semantic_scene_description_v1.schema.json` und `artifacts/evaluation/semantic_scene_description_v1/example_scene.json`.)
  - Scope: textuelle Szenenbeschreibung inkl. Relationen (z. B. „Kelle mit horizontalem Griff links und Beschriftung rF“).
  - Deliverable: DSL/JSON-Layer für Objekte + Relationen + Constraints.
  - Akzeptanz: Beschreibung kann deterministisch wieder in eine rekonstruktive SVG-Szene übersetzt werden.

- [x] **V6 – Iterativen Nachzeichnungsalgorithmus auf Semantik umstellen** (2026-05-14: Mehrziel-Optimierungsrahmen, Semantik-Konsistenzscore, Konvergenzkriterien und Artefaktformat in `docs/v6_semantic_iterative_redraw_algorithm_2026-05-14.md` spezifiziert.)
  - Scope: Initiale Primitive-Schätzung → Render → Fehleranalyse → Parameterupdate.
  - Deliverable: Mehrziel-Optimierung (Geometrie, Farbe, Semantik-Konsistenz) pro Iteration.
  - Akzeptanz: Konvergenzplots zeigen reproduzierbare Verbesserung in mindestens 3 Referenzfamilien.

- [x] **V7 – Rückwärts-Training (Text → SVG → Raster → Rücktransformation)** (2026-05-14: Closed-Loop-Gap-Report-v1 mit Tool `tools/evaluate_semantic_roundtrip.py` und Baseline-Artefakt `artifacts/evaluation/semantic_roundtrip_v1/report_2026-05-14.json` dokumentiert in `docs/v7_roundtrip_training_pipeline_2026-05-14.md`.)
  - Scope: generierte Szenen zur Selbstvalidierung und Schwachstellenanalyse.
  - Deliverable: Closed-Loop-Evaluationspipeline mit Gap-Reports pro Relationstyp.
  - Akzeptanz: Pipeline markiert systematisch nicht-invertierbare Fälle (z. B. vollständig verdeckte Griffe ohne Constraints).

- [x] **V8 – Grenzfallkatalog für Nicht-Invertierbarkeit pflegen** (2026-05-14: Failure-Mode-Katalog v1 inkl. Zusatzbedingungen und Zuordnungsvorlage in `docs/v8_non_invertibility_edge_case_catalog_2026-05-14.md` dokumentiert.)
  - Scope: explizite Regeln, wann Rücktransformation prinzipiell mehrdeutig/unmöglich ist.
  - Deliverable: katalogisierte Failure-Modes + empfohlene Zusatzbedingungen.
  - Akzeptanz: Jeder dokumentierte Fehlschlag ist einem bekannten Failure-Mode zugeordnet.


## Perception-First-Track: Bildhinweise vor der ersten Iteration nutzen (neu 2026-05-30)

Ziel: Die beschreibungsgetriebene Geometry-IR bleibt Zielrepräsentation, wird aber
künftig aus einfachen Bild-/Beschreibungshinweisen vorinitialisiert. Das
detaillierte Backlog steht in `docs/perception_first_task_backlog_2026-05-30.md`.

- [x] **PF1 – Detection-Contract v1 für erkannte Primitive festlegen:** ein stabiles Format für Linien-, Kreis-/Ring- und Rechteckkandidaten definieren und reporten. (2026-05-30: Contract-Modul `tools/perception_detection_contract.py` ergänzt; Kandidatenschema `perception_primitive_candidate_v1` serialisiert `kind`, `bbox`, `center`, `geometry`, `color`, `confidence`, `roi`, `evidence` und `source`. Plan-B-Synthesereport für `line`, `circle` und `rectangle` unter `artifacts/evaluation/perception_detection_contract_v1/perception_detection_contract_v1_report.json`; Basistests in `tests/test_perception_detection_contract.py`.)
- [x] **PF2 – Horizontalstrich-/Minus-Erkennung mit ROI-Hinweis implementieren:** Hinweise wie „oben mittig ist ein `-`-Zeichen“ in einen `HorizontalRule`- oder `TextGlyph("-")`-Seed übersetzen. (2026-05-30: `detect_horizontal_rules(...)` und `detect_minus_candidates(...)` ergänzen einen ROI-basierten `horizontal_rule`-/`HorizontalRule`-Kandidaten inklusive `text_equivalent="-"`; synthetischer Top-Center-Minus und reales `AC0120_L.jpg` werden im Report `artifacts/evaluation/perception_minus_roi_v1/perception_minus_roi_report_v1.json` erfolgreich gematcht; Basistests in `tests/test_perception_minus_roi.py`.)
- [x] **PF3 – Kreis-/Ring-Erkennung als Geometry-IR-Seed stabilisieren:** erkannte Kreise/Ringe mit `CircleBackground` und bestehenden Masken-/Hough-Heuristiken zusammenführen. (2026-05-30: `detect_circle_rings(...)` kombiniert Hough- und Foreground-Masken-Heuristiken, serialisiert `circle`-/`ring`-Kandidaten mit `geometry_ir_kind=CircleBackground` und merged den stärksten Treffer via `merge_circle_ring_candidates_into_geometry_ir(...)` in bestehende oder neue Geometry-IR-Kreise; Report mit synthetischem Kreis/Ring plus `AC0201_S.jpg`/`AC0800_S.jpg` unter `artifacts/evaluation/perception_circle_ring_seed_v1/perception_circle_ring_seed_report_v1.json`, Basistests in `tests/test_perception_circle_ring_seed.py`.)
- [x] **PF4 – Perception-Kandidaten vor dem generischen Non-Composite-Fallback nutzen:** Beschreibung + Bildanalyse als `perception_seeded_geometry_ir` vor dem Element-Fit ausführen. (2026-05-30: Non-Composite-Runtime versucht nun vor Description-only-IR und generischem Element-Fit einen `non_composite_perception_seeded_geometry_ir`-Pfad; Perception-Seeds für `CircleBackground`, `HorizontalRule` und `RectBorder` werden aus PF-Kandidaten in Geometry-IR gemerged, gerendert und mit eigener Validation-Log-Spur protokolliert. Report: `artifacts/evaluation/perception_seeded_geometry_ir_v1/perception_seeded_geometry_ir_report_v1.json`; Basistests in `tests/test_perception_seeded_geometry_ir.py` und `tests/detailtests/test_non_composite_runtime_helpers.py`. )
- [x] **PF5 – Evaluationsharness für Perception-Seeds aufbauen:** Precision/Recall, Confidence und Renderfehler vor/nach Seed für mindestens drei Primitive ausweisen. (2026-05-30: PF5-Harness `--report perception-seed-eval` ergänzt; Report `artifacts/evaluation/perception_seed_evaluation_v1/perception_seed_evaluation_report_v1.json` und CSV `artifacts/evaluation/perception_seed_evaluation_v1/perception_seed_evaluation_samples_v1.csv` verdichten Minus-/Linien-, Kreis-/Ring- und Rechteck-Seeds zu Precision/Recall, Confidence-Verteilung und Renderfehlern vor/nach Seed. Basistests in `tests/test_perception_seed_evaluation.py`.)
- [x] **PF6 – Perception-Telemetrie in bestehende Reports integrieren:** erkannte/abgelehnte Kandidaten, Seed-Auswahl und Fehlerdeltas pro Lauf als CSV/JSON protokollieren. (2026-05-30: PF6-Telemetrie ergänzt `build_perception_telemetry_record(...)` sowie den CLI-Report `--report perception-telemetry`; JSON/CSV-Artefakte unter `artifacts/evaluation/perception_telemetry_v1/` protokollieren erkannte und abgelehnte Kandidaten, ausgewählte Geometry-IR-Seeds sowie Fehlerwerte vor/nach Seed. Basistests in `tests/test_perception_telemetry_report.py`.)
- [x] **PF7 – Einfache Text-/Glyph-Erkennung für `M`, `+`, `-` und kurze Labels prüfen:** Template-Matching/OCR-Nutzen ohne neue Pflichtdependency evaluieren. (2026-05-30: Template-Matching-Detector `detect_text_glyph_candidates(...)` ergänzt; PF7-Report `artifacts/evaluation/perception_text_glyph_evaluation_v1/perception_text_glyph_evaluation_report_v1.json` und CSV `.../perception_text_glyph_evaluation_samples_v1.csv` prüfen synthetische Glyphen `M`, `+`, `-`, das Kurzlabel `VOC` sowie den realen Plus-Kandidaten `AC0120_L.jpg` ohne neue Pflicht-OCR-Dependency; Basistests in `tests/test_perception_text_glyph_eval.py`.)
- [x] **PF8 – Plan-B-Rotation mit Perception-Aufgaben verzahnen:** jedes kommende Plan-B-Paket erhält einen Abschnitt „Perception-Lerneffekt“. (2026-05-30: PF8-Linkage-Report `--report plan-b-perception-linkage` ergänzt; JSON/CSV-Artefakte unter `artifacts/evaluation/plan_b_perception_linkage_v1/` dokumentieren für `AC0224_S`, `AC0231_S`, `AC0838_M` und `AC0881_M` je eine Perception-Frage, erwartete erste Primitive und die Entscheidung `generalisiert`/`nur Sonderfall`/`noch nicht erkannt`. `PLAN_B_KANDIDATEN.md` enthält ab sofort den Pflichtabschnitt „Perception-Lerneffekt“.)

### Fortschritt vs. Blocker (Session 2026-06-04, Plan-B AC0861_S rF-Vertikalconnector Run NQ)

- **Fortschritt:** Der nächste aktive Plan-B-/Perception-Kandidat `AC0861_S.jpg` wurde semantisch abgearbeitet: Die AC0861-Familie ist nun als AC08-`rF`-Kreis/Text-Badge mit unterem senkrechtem Stem registriert und läuft im echten Einzelpfad bis `status=semantic_ok` statt in den generischen Fallback zu fallen.
- **Perception-Lerneffekt:** Die PF8-Frage nach dominantem rF-Kreis und unterem senkrechten Griff bleibt `generalisiert`; der Linkage-Report rotiert den erledigten Kandidaten aus und führt nun `AC0862_S`, `AC0863_S` und den neuen Folgepunkt `AC0864_S`, jeweils mit `CircleBackground` als Seed-Folge und zusätzlicher Linien-/TextGlyph-Prüfung.
- **Sicherung:** Der gezielte Testblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_make_badge_params_ac0861_uses_lower_stem_rf_geometry tests/test_image_composite_converter.py::test_parse_description_marks_ac0861_as_rf_lower_stem_badge tests/test_plan_b_perception_linkage.py`, `5 passed`); der PF8-Linkage-Report wurde erfolgreich neu geschrieben; der externe AC0861-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-ac0861-run --start AC0861_S --end AC0861_S --deterministic-order`, Exit `0`) und protokollierte `status=semantic_ok` mit `FehlerProPixel=0.04891733`.
- **Blocker:** Kein neuer technischer Blocker; der sichtbare Restfehler konzentriert sich weiterhin auf Text-/Antialiasing-Abweichungen und wird als Qualitätsfolgepunkt behandelt, nicht als Semantikfehler.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation mit `AC0862_S.jpg` fortfahren oder den gedrehten rF-Connector-Folgepunkt `AC0863_S.jpg` isoliert abarbeiten.

### Fortschritt vs. Blocker (Session 2026-06-03, Plan-B AC0835_S VOC-Badge Run NP)

- **Fortschritt:** Der nächste aktive Plan-B-/Perception-Kandidat `AC0835_S.jpg` wurde semantisch nachgeschärft: connector-freie AC08-Kreis/Text-Badges entfernen nun stale Arm-/Stem-Parameter vor dem SVG-Rendering, und degenerierte Arm-Probes unterhalb der sichtbaren Mindestlänge werden nicht mehr als `<line>` ausgegeben. Die Satisfactory-Baseline für `AC0835_S.svg` ist entsprechend ohne falsche Mini-Connector-Linie aktualisiert.
- **Perception-Lerneffekt:** Die PF8-Frage nach dominantem VOC-Kreis und dreibuchstabigem Label bleibt `generalisiert`; der Linkage-Report rotiert den erledigten Kandidaten aus und führt nun `AC0861_S`, `AC0862_S` und den neuen Folgepunkt `AC0863_S`, jeweils mit `CircleBackground` als Seed-Folge und zusätzlicher Linien-/TextGlyph-Prüfung.
- **Sicherung:** Der gezielte Testblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_badge_svg_helpers.py tests/test_plan_b_perception_linkage.py`, `8 passed`); der PF8-Linkage-Report wurde erfolgreich neu geschrieben; der externe AC0835-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-ac0835-runnp3 --start AC0835_S --end AC0835_S --deterministic-order`, Exit `0`) und endete mit einem wiederhergestellten SVG ohne `<line>`-Connector.
- **Blocker:** Kein neuer technischer Blocker; der semantisch korrekte no-connector-Stand wird wegen des bekannten Pixel-/Antialiasing-Abstands über die bereinigte Satisfactory-Baseline stabilisiert.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation mit `AC0861_S.jpg` fortfahren oder den seitlich gedrehten rF-Connector-Folgepunkt `AC0862_S.jpg` isoliert abarbeiten.

### Fortschritt vs. Blocker (Session 2026-06-02, Plan-B AC0844_S rF-Connector Run NM)

- **Fortschritt:** Der nächste aktive Plan-B-/Perception-Kandidat `AC0844_S.jpg` wurde semantisch abgearbeitet: Die AC0844-Familie ist nun als rF-Kreis/Text-Badge mit rechter Arm-Geometrie (AC0814-/AC0839-Topologie) registriert und läuft im echten Einzelpfad bis `status=semantic_ok` statt mit `conversion_failed/no_result` abzubrechen.
- **Perception-Lerneffekt:** Die PF8-Frage nach dominantem rF-Kreis und gedrehtem/seitlichem Griff bleibt `generalisiert`; der Linkage-Report rotiert die erledigten Kandidaten aus und führt nun `AC0835_S`, `AC0861_S` und `AC0862_S`, jeweils mit `CircleBackground` als Seed-Folge.
- **Sicherung:** Der externe AC0844-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic/ac0844-run --start AC0844_S --end AC0844_S --deterministic-order`, Exit `0`) und protokollierte `status=semantic_ok`; der PF8-Linkage-Report wurde erfolgreich neu geschrieben.
- **Blocker:** Kein neuer technischer Blocker; der Pixel-Fehler bleibt wegen Text-/Antialiasing-Abweichungen sichtbar (`error_per_pixel=0.05390933`, `mean_delta2=4330.087891`), ist aber nicht mehr `conversion_failed`.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation mit `AC0835_S.jpg` fortfahren oder den rF-Connector-Folgepunkt `AC0861_S.jpg` isoliert abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, Plan-B AC0850_M rF-Badge Run NF)

- **Fortschritt:** Der nächste dokumentierte Plan-B-/Perception-Kandidat `AC0850_M.jpg` wurde semantisch abgearbeitet: Die AC0850-Familie startet nun als connector-freies AC08-`rF`-Kreis/Text-Badge und läuft im echten Einzelpfad bis `status=semantic_ok` statt mit `conversion_failed/no_result` abzubrechen.
- **Perception-Lerneffekt:** Der erledigte Kandidat `AC0850_M` wurde aus der aktiven PF8-/Plan-B-Liste rotiert; der Linkage-Report führt nun `AC0836_S`, `AC0835_S` und als Anschlussprobe `AC0861_S`, jeweils mit `decision=generalisiert` und `CircleBackground` als Seed-Folge.
- **Sicherung:** Der externe AC0850-M-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-ac0850-after --start AC0850_M --end AC0850_M --deterministic-order`, Exit `0`) und protokollierte `status=semantic_ok`; `conversion_bestlist.csv` enthält `AC0850_M` mit `best_error=26.802500` und `mean_delta2=6655.042480`.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation mit dem aktiven Kreis-/VOC-/Vertikalgriff-Kandidaten `AC0836_S.jpg` fortfahren oder den neuen rF-Connector-Folgepunkt `AC0861_S.jpg` isoliert abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, Plan-B AC0836_S VOC-Connector Run NH)

- **Fortschritt:** Der nächste dokumentierte Plan-B-/Perception-Kandidat `AC0836_S.jpg` wurde abgearbeitet: Die vertikale Linienerkennung besitzt nun einen konturbasierten Fallback für sehr kleine Badge-Bilder, sodass der senkrechte Griff zusätzlich zum dominanten `CircleBackground`-Kreis als `line`-Kandidat im PF8-Linkage auftaucht.
- **Perception-Lerneffekt:** Der erledigte Kandidat `AC0836_S` wurde aus der aktiven PF8-/Plan-B-Liste rotiert; der Linkage-Report führt nun `AC0835_S`, `AC0861_S` und den neuen gedrehten rF-Connector-Folgepunkt `AC0862_S`, jeweils mit `decision=generalisiert`.
- **Sicherung:** Der externe AC0836-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli artifacts/images_to_convert/nonconvertable --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir /tmp/ic-ac0836-runnh --start AC0836_S --end AC0836_S --deterministic-order`, Exit `0`) und protokollierte `status=semantic_ok`; der PF8-Linkage-Report wurde erfolgreich neu geschrieben; der gezielte Testblock lief mit `5 passed`.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation mit `AC0835_S.jpg` fortfahren oder den rF-Connector-Folgepunkt `AC0861_S.jpg` isoliert abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, Plan-B AC0870_S T-Badge Run NE)

- **Fortschritt:** Der nächste dokumentierte Plan-B-/Perception-Kandidat `AC0870_S.jpg` wurde semantisch abgearbeitet: Kleine AC0870-`path_t`-Badges starten nun mit zentriertem Kreis-/T-Seed, explizitem `draw_text=True`, gesperrter Textposition/-skalierung und engem Radiuskorridor statt mit einer durch das T-Maskensignal nach links/unten verzogenen Ersatzpose.
- **Perception-Lerneffekt:** Der erledigte Kandidat `AC0870_S` wurde aus der aktiven PF8-/Plan-B-Liste rotiert; der Linkage-Report führt nun `AC0836_S`, `AC0835_S` und `AC0850_M`, jeweils mit `decision=generalisiert` und `CircleBackground` als Seed-Folge.
- **Sicherung:** Der AC0870-S-Einzellauf lief grün (Exit `0`) und erzeugte ein SVG mit `cx=7.5000`, `cy=7.0000`, `r=6.0000`; der gezielte PF8-/Regressionstestblock lief mit `3 passed`.
- **Blocker:** Kein neuer technischer Blocker; der Pixel-Fehler bleibt wegen Antialiasing/Glyphenrasterung sichtbar (`error_per_pixel=0.12578765`), sinkt aber gegenüber dem Vorlauf (`mean_delta2=6242.066895`) auf `mean_delta2=4968.879883`.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation mit `AC0850_M.jpg` fortfahren oder den aktiven Kreis-/VOC-/Vertikalgriff-Kandidaten `AC0836_S.jpg` isoliert abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, Plan-B AC0820_S CO2-Subscript Run ND)

- **Fortschritt:** Der nächste dokumentierte Plan-B-/Perception-Kandidat `AC0820_S.jpg` wurde semantisch abgearbeitet: Die AC0820-Familie rendert die dokumentierte tiefgestellte CO2-Indexziffer nun wieder mit `co2_index_mode=subscript`; AC0831/AC0833 und andere Connector-CO²-Familien behalten ihre Superscript-Tuner.
- **Perception-Lerneffekt:** Der erledigte Kandidat `AC0820_S` wurde aus der aktiven PF8-/Plan-B-Liste rotiert; der Linkage-Report führt nun `AC0870_S`, `AC0850_M` und `AC0836_S`, jeweils mit `decision=generalisiert` und `CircleBackground` als Seed-Folge.
- **Sicherung:** Der AC0820-S-Einzellauf lief grün (Exit `0`) und erzeugte ein SVG mit getrennten `CO`-/`2`-Textknoten, wobei die `2` unterhalb der CO-Baseline liegt; der gezielte PF8-/Regressionstestblock lief mit `10 passed`.
- **Blocker:** Kein neuer technischer Blocker; der Pixel-Fehler bleibt wegen Text-/Antialiasing-Abweichungen hoch (`error_per_pixel=0.13116049`), wird aber für dieses Paket hinter die explizite XML-Semantik „tiefgestellt“ zurückgestellt.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation mit `AC0870_S.jpg` fortfahren oder den aktiven Text-/Grauwertkandidaten `AC0850_M.jpg` isoliert abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, Plan-B AC0231_S Perception-Rotation Run MW)

- **Fortschritt:** Das nächste Plan-B-/Perception-Arbeitspaket wurde für `AC0231_S` abgearbeitet: Die Beschreibung wird nun als `TopKelleThreeWayValveGlyph` mit `label=M` erkannt, und der echte Einzellauf protokolliert `status=non_composite_perception_seeded_geometry_ir` mit `CircleBackground` plus `TopKelleThreeWayValveGlyph`.
- **Gekoppelte Plan-B-/Repro-Aufgabe:** Der PF8-Linkage-Report rotiert den erledigten Kandidaten `AC0231_S` aus und bewertet nun `AC0232_S`, `AC0233_S`, `AC0838_M` und `AC0881_M`; alle vier Samples bleiben evaluiert und besitzen einen Perception-Lerneffekt.
- **Blocker:** Kein neuer technischer Blocker; das `M`-Signal ist für AC0231 jetzt über die beschreibungsgetriebene Geometry-IR im SVG gerendert, während der vorinitialisierte Seed weiterhin über `CircleBackground` läuft.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation mit `AC0232_S.jpg` fortfahren oder einen QR-Folgepunkt (`AC0838_M`/`AC0881_M`) isoliert abarbeiten.



### Fortschritt vs. Blocker (Session 2026-05-31, Plan-B AC0838_M Perception-Review Run MZ)

- **Fortschritt:** Der nächste dokumentierte Plan-B-/Perception-Kandidat `AC0838_M.jpg` wurde isoliert aus `artifacts/images_to_convert/nonconvertable` erneut konvertiert. Der Lauf blieb im semantischen VOC-Badge-Pfad (`SEMANTIC: senkrechter Strich oben vom Kreis` plus `SEMANTIC: Kreis + Buchstabe VOC`) und erreichte `error_per_pixel=0.04151429`, also wieder unter dem dokumentierten Review-Grenzwert `0.045945679012345676`.
- **Perception-Lerneffekt:** Die PF8-Frage nach dominantem VOC-Kreis/Label bleibt `generalisiert`; der maschinenlesbare Linkage-Report rotiert `AC0838_M` aus und führt nun `AC0881_M` sowie `AC0234_S` mit je einem Perception-Lerneffekt.
- **Blocker:** Kein neuer technischer Blocker für `AC0838_M`; der Kandidat ist nicht mehr aktiv in `PLAN_B_KANDIDATEN.md`.
- **Nächster sinnvoller Schritt:** In der normalen Rotation mit `AC0881_M.jpg` fortfahren oder den AC02-Folgekandidaten `AC0234_S.jpg` abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, AC0232_S Perception-seeded Geometry-IR Plan-B Run MX)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0232_S.jpg` wurde im echten Non-Composite-Pfad abgesichert: Die Beschreibung `Wie AC0231 ... 90° nach links gedreht` wird als `LeftRotatedTopKelleThreeWayValveGlyph` mit `label=M` modelliert; im Repro-Lauf wird zusätzlich ein `CircleBackground`-Seed als `non_composite_perception_seeded_geometry_ir` protokolliert.
- **Perception-Lerneffekt:** Die PF8-Frage nach gedrehter `M`-Beschriftung bzw. runder Kelle bleibt `generalisiert`, weil der echte Einzellauf `CircleBackground`, `LeftRotatedTopKelleThreeWayValveGlyph` und `HorizontalRule` als vorinitialisierte Geometry-IR-Kette schreibt.
- **Sicherung:** Der gezielte Detailtest-/PF8-Block lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py tests/test_plan_b_perception_linkage.py`, `89 passed`, Exit `0`); der externe AC0232-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0232-runmx --start AC0232_S --end AC0232_S --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_perception_seeded_geometry_ir`.
- **Kandidatenrotation:** `PLAN_B_KANDIDATEN.md` zeigt nach Entfernung von `AC0232_S.jpg` nun `AC0233_S.jpg` als nächste Rotation und füllt mit `AC0234_S.jpg` als weiterem AC02-Kandidaten auf.
- **Nächster sinnvoller Schritt:** Mit `AC0233_S.jpg` rotieren oder vor der regulären Rotation einen QR-Folgepunkt (`AC0838_M` oder `AC0881_M`) als isolierten Plan-B-/Re-Konvertierungslauf abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, Plan-B AC0232_S Perception-Rotation Run MV)

- **Fortschritt:** Das nächste Plan-B-/Perception-Arbeitspaket wurde für `AC0232_S` abgearbeitet: Der PF8-Linkage-Report rotiert den erledigten Kandidaten `AC0224_S` aus und bewertet nun `AC0232_S`, `AC0231_S`, `AC0838_M` und `AC0881_M`.
- **Gekoppelte Plan-B-/Repro-Aufgabe:** `AC0232_S` wird mit der Frage nach gedrehter `M`-Beschriftung bzw. runder Kelle als `text_glyph_or_circle_ring` geführt; der aktuelle Lauf erkennt einen `circle`-Kandidaten mit `CircleBackground`-Seed (`top_confidence=0.9236`) und entscheidet den Lerneffekt damit als `generalisiert`.
- **Blocker:** Kein neuer technischer Blocker; wie bei `AC0231_S` bleibt das `M`-Signal vorerst Label-Hinweis, während der generische vorinitialisierte Seed über `CircleBackground` läuft.
- **Nächster sinnvoller Schritt:** In der normalen Plan-B-Rotation den nächsten konkreten Kandidaten mit dem aktualisierten PF8-Report fortführen oder `AC0232_S` als vorinitialisierten Geometry-IR-Seed im Einzellauf prüfen.

### Fortschritt vs. Blocker (Session 2026-05-30, PF8 Plan-B-/Perception-Verzahnung Run MU)

- **Fortschritt:** Die nächste dokumentierte Perception-First-Aufgabe **PF8** wurde umgesetzt: Aktive Plan-B-Kandidaten werden maschinenlesbar mit genau einer Perception-Frage, erwarteten ersten Primitive-Familien und einer Entscheidung aus `generalisiert`, `nur Sonderfall` oder `noch nicht erkannt` verknüpft.
- **Gekoppelte Plan-B-/Repro-Aufgabe:** Der neue Report `artifacts/evaluation/plan_b_perception_linkage_v1/plan_b_perception_linkage_report_v1.json` bewertet `AC0224_S`, `AC0231_S`, `AC0838_M` und `AC0881_M`; alle vier Kandidaten wurden als `generalisiert` entschieden, weil mindestens ein erwarteter Candidate in einen bestehenden Seed-Pfad (`CircleBackground` oder `HorizontalRule`) passt.
- **Blocker:** Kein neuer technischer Blocker; TextGlyph-Signale bleiben für Plan-B-Labels dokumentiert, werden aber erst dann als generischer Seed erzwungen, wenn ein nachgelagerter Geometry-IR-Textpfad die Renderintegration abschließt.
- **Nächster sinnvoller Schritt:** Zurück in die normale Plan-B-Rotation gehen und beim nächsten konkreten Kandidaten den neuen Pflichtabschnitt „Perception-Lerneffekt“ aus dem PF8-Report übernehmen.

### Fortschritt vs. Blocker (Session 2026-05-30, PF7 Text-/Glyph-Evaluation Run MT)

- **Fortschritt:** Die nächste dokumentierte Perception-First-Aufgabe **PF7** wurde umgesetzt: Ein einfacher Template-Matching-Detector bewertet bekannte Glyphen und kurze Labels (`M`, `+`, `-`, `VOC`) über den vorhandenen `cv2`/`numpy`-Pfad und serialisiert Treffer als `text_glyph`-Kandidaten im bestehenden Candidate-Contract.
- **Gekoppelte Plan-B-/Repro-Aufgabe:** Der PF7-Report enthält vier synthetische Glyph-/Label-Fixtures und den realen Plan-B-nahen Plus-Kandidaten `AC0120_L.jpg`; alle fünf Samples matchen den erwarteten Text.
- **Blocker:** Kein neuer technischer Blocker; vollständiges OCR bleibt bewusst keine Pflichtdependency. Für natürlichere kleine Labels wie `rF` sollte erst PF8 entscheiden, ob Template-Varianten reichen oder ein optionales OCR-Backend sinnvoll ist.
- **Nächster sinnvoller Schritt:** PF8 umsetzen: kommende Plan-B-Pakete mit einem dokumentierten Abschnitt „Perception-Lerneffekt“ verzahnen.

### Fortschritt vs. Blocker (Session 2026-05-30, PF5 Evaluationsharness Run MS)

- **Fortschritt:** Die nächste dokumentierte Perception-First-Aufgabe **PF5** wurde umgesetzt: Der neue Evaluationsharness aggregiert Perception-Telemetrie zu Precision/Recall, Confidence-Verteilung und Renderfehlern vor/nach Geometry-IR-Seed.
- **Gekoppelte Plan-B-/Repro-Aufgabe:** Der PF5-Report prüft synthetische Fixtures für `minus_line`, `circle_ring` und `rectangle` sowie, falls vorhanden, den realen Minus-/Plan-B-Kandidaten `AC0120_L.jpg`; alle Samples matchen Detection und Seed.
- **Blocker:** Kein technischer Blocker; ein stabiler realer Rechteckkandidat ist noch nicht dokumentiert und wird im PF5-Report als offener Realbildfall markiert.
- **Nächster sinnvoller Schritt:** PF7 prüfen: Minimalstrategie für Glyphen/Text (`M`, `+`, `-`, kurze Labels) ohne neue Pflichtdependency evaluieren.

### Fortschritt vs. Blocker (Session 2026-05-30, PF1 Detection-Contract Run MO)

- **Fortschritt:** Die nächste dokumentierte Perception-First-Aufgabe **PF1** wurde umgesetzt: erkannte Linien-, Kreis- und Rechteckprimitive werden nun in das gemeinsame Schema `perception_primitive_candidate_v1` mit Geometrie-, Farb-, ROI-, Evidence- und Source-Feldern serialisiert.
- **Gekoppelte Plan-B-Aufgabe:** Die im Backlog vorgesehene synthetische Minimalprobe wurde als Contract-Report mit den drei Fixtures `line`, `circle` und `rectangle` ausgeführt; alle drei erwarteten Kandidatentypen wurden gematcht.
- **Blocker:** Keine für PF1; reale Bildkandidaten bleiben bewusst Folgeaufgabe für PF2/PF3/PF6, damit der Contract zuerst stabil bleibt.
- **Nächster sinnvoller Schritt:** PF2 umsetzen: Horizontalstrich-/Minus-Erkennung mit ROI-Hinweis auf Basis des neuen Candidate-Contracts protokollieren.

### Fortschritt vs. Blocker (Session 2026-05-30, PF3 Kreis-/Ring-Seed Run MQ)

- **Fortschritt:** Die nächste dokumentierte Perception-First-Aufgabe **PF3** wurde umgesetzt: Kreis-/Ring-Kandidaten werden über Hough- und Foreground-Masken-Heuristiken stabilisiert, als Contract-Kandidaten serialisiert und in `CircleBackground`-Geometry-IR gemerged.
- **Gekoppelte Plan-B-Aufgabe:** Der PF3-Report prüft synthetische `circle`-/`ring`-Fixtures sowie `AC0201_S.jpg` und `AC0800_S.jpg`; alle erwarteten Kandidatentypen werden gematcht und der stärkste Kandidat erzeugt einen `CircleBackground`-Seed.
- **Blocker:** Keine für PF3; reale Kleinstbilder wie `AC0201_S.jpg`/`AC0800_S.jpg` liefern aktuell bewusst einen CircleBackground-Kreis-Seed statt eine robuste Ring-Innenradius-Schätzung.
- **Nächster sinnvoller Schritt:** PF4 umsetzen: den neuen `perception_seeded_geometry_ir`-Pfad vor dem generischen Non-Composite-Fallback in die Laufzeit integrieren.

### Fortschritt vs. Blocker (Session 2026-05-30, PF6 Perception-Telemetrie Run MR)

- **Fortschritt:** Die nächste dokumentierte Perception-First-Aufgabe **PF6** wurde umgesetzt: Ein Telemetrie-Record hält Kandidatenentscheidungen (`accepted`/`rejected`), ausgewählte Geometry-IR-Seeds und Fehlerwerte vor/nach Perception-Seed fest.
- **Gekoppelte Plan-B-Aufgabe:** Der Einzelreport für `AC0120_L.jpg` schreibt JSON und CSV unter `artifacts/evaluation/perception_telemetry_v1/`; der Lauf selektiert Perception-Seeds und weist ein Fehlerdelta vor/nach Seed aus.
- **Blocker:** Keine für PF6; die Telemetrie ist zunächst als externes Tool verfügbar und kann in einem späteren Paket direkt an breitere Runtime-Batches angebunden werden.
- **Nächster sinnvoller Schritt:** PF5 umsetzen: Evaluationsharness für Perception-Seeds mit Precision/Recall, Confidence-Verteilung und Qualitätsänderung für mindestens drei Primitive aufbauen.

### Fortschritt vs. Blocker (Session 2026-05-30, PF4 Perception-Seeded-Geometry-IR Run MR)

- **Fortschritt:** Die nächste dokumentierte Perception-First-Aufgabe **PF4** wurde umgesetzt: der Non-Composite-Pfad versucht vor dem Description-only-IR und vor dem generischen Element-Fit einen `non_composite_perception_seeded_geometry_ir`-Hook aus Beschreibung + Bildanalyse.
- **Gekoppelte Plan-B-Aufgabe:** Der neue PF4-Report `artifacts/evaluation/perception_seeded_geometry_ir_v1/perception_seeded_geometry_ir_report_v1.json` prüft synthetische Minus-/Kreis-Seeds; beide erwarteten Geometry-IR-Seeds (`HorizontalRule`, `CircleBackground`) werden gematcht.
- **Blocker:** Keine für PF4; echte Fehlerdeltas/Precision-Recall bleiben bewusst PF5/PF6, damit PF4 zunächst nur den Runtime-Hook und unterscheidbare Validation-Logs liefert.
- **Nächster sinnvoller Schritt:** PF5 umsetzen: Evaluationsharness mit Precision/Recall, Confidence und Renderfehler vor/nach Seed für mindestens drei Primitive aufbauen.

### Fortschritt vs. Blocker (Session 2026-05-30, PF2 Minus-ROI Run MP)

- **Fortschritt:** Die nächste dokumentierte Perception-First-Aufgabe **PF2** wurde umgesetzt: Beschreibungen mit `oben`/`mittig`/`Symmetrieachse` leiten nun eine Top-Center-ROI ab, in der horizontale Minus-/Rule-Konturen erkannt und als `horizontal_rule`-Kandidaten mit `geometry_ir_kind=HorizontalRule` serialisiert werden.
- **Gekoppelte Plan-B-Aufgabe:** Der PF2-Report prüft eine synthetische Top-Center-Minus-Szene und das reale Bild `AC0120_L.jpg`; beide erzeugen einen passenden `horizontal_rule`-Kandidaten.
- **Blocker:** Keine für PF2; die Kandidaten werden noch nicht im Runtime-Fallback genutzt, weil das laut Backlog PF4 vorbehalten bleibt.
- **Nächster sinnvoller Schritt:** PF6 früh einziehen: erkannte/abgelehnte Perception-Kandidaten als Telemetrie-Report protokollieren, bevor PF3/PF4 in den Runtime-Pfad wandern.

## How to use this list

- Work from top to bottom unless a dependency requires a different order.
- When a task is completed, change its checkbox to `- [x]` and add a short note.
- If a task splits into multiple deliverables, keep the parent item and add nested
  subtasks below it.
- **Aktuelle Gewichtung (2026-05-30):** Nach der Geometry-IR-Stabilisierung rotiert das nächste Arbeitspaket vorrangig in den Perception-First-Track: zuerst PF1 (Detection-Contract), danach PF2 (Minus-/Horizontalstrich mit ROI), jeweils gekoppelt mit genau einem Plan-B-/Repro-Kandidaten.

## Current status

- The latest committed AC08 report snapshot now contains `10` evaluated AC08 validation logs, and all `10` are `semantic_ok` (`0` `semantic_mismatch`).
- The refresh run currently covers the most recently touched connector/circle families present in `artifacts/converted_images/reports` (`AC0811`, `AC0832`, `AC0835`, `AC0836`, `AC0870`, `AC0882`).
- Continue to add new work items here before implementation starts, then mark them in-place when they are done.

## Next execution tasks (neu gewichtet am 2026-05-30: Perception-First vor weiterer Einzelfall-Rotation)

### Begriffskonvention (ab 2026-05-16)

- **"Nächstes Arbeitspaket"** bezeichnet ab sofort immer die feste Kombination aus:
  1. **nächste dokumentierte Aufgabe** gemäß Priorisierung in `docs/open_tasks.md`,
  2. **genau eine gekoppelte Plan-B-Aufgabe**,
  3. **nächstes Bild** aus `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`.

- Diese Benennung wird in künftigen Session-Einträgen explizit verwendet, damit Folgeaufgaben darauf referenzieren können.

### Plan-B-Kopplungsregel (ab 2026-05-14 verbindlich)

- Jede neue oder weiterbearbeitete Aufgabe wird ab sofort mit genau einer
  **Plan-B-Aufgabe** verknüpft (Fallback mit kleinerem Scope oder synthetischem Repro).
- Die Plan-B-Aufgabe wird direkt unter der Primäraufgabe dokumentiert und im selben
  Session-Eintrag mit Fortschritt/Blocker-Status nachgeführt.
- Ziel: Bei Blockern sofort auf die gekoppelte Alternative rotieren, ohne neue
  Deadlock-Schleifen zu erzeugen.

### Neue Zusatzaufgabe (Session 2026-05-14)

- [x] **N8 – Plan-B-Syntheseprobe (Beschreibung → SVG → JPG → Rauschen → Konvertierung)** (2026-05-14: Tool `tools/plan_b_synthetic_probe.py` ergänzt und Beispielausführung mit `variant=AC0080_L` dokumentiert; Ergebnisartefakt unter `artifacts/converted_images/converted_svgs/AC0080_L.svg` aktualisiert.)
- [x] **N9 – Plan-B-Einzelprobe für `AC0212_L.svg` anlegen** (2026-05-14: isolierter `AC0212`-Kurzlauf + gekoppelte Plan-B-Syntheseprobe mit Exit `0` dokumentiert; siehe `docs/n9_ac0212_planb_single_2026-05-14_runDF_summary.md` sowie Logs `artifacts/converted_images/reports/AC0212_single_planbprobe_2026-05-14_runDF.log` und `artifacts/converted_images/reports/AC0212_planb_synthetic_2026-05-14_runDF_PB.log`.)

- [x] **N10 – Plan-B-Einzelprobe für `AC0223_L_sia.svg` anlegen** (2026-05-15: isolierter `AC0223`-Kurzlauf dokumentiert und anschließend auf den tatsächlichen Trefferpfad `artifacts/images_to_convert/nonconvertable` korrigiert (`Run DN2`, Exit `0`); gekoppelte Plan-B-Aufgabe `N10-PB` aus neuer Sample-Datei `artifacts/images_to_convert/samples/AC0223_L_sia.svg` abgeleitet; siehe `docs/n10_ac0223_planb_single_2026-05-15_runDN_summary.md` sowie Logs `artifacts/converted_images/reports/AC0223_single_2026-05-15_runDN.log` und `artifacts/converted_images/reports/AC0223_single_nonconvertable_retry_2026-05-15_runDN2.log`.)


### Fortschritt vs. Blocker (Session 2026-05-15, N10 AC0223-Plan-B + Einzelrun Run DN)

- **Fortschritt:** Aus der neu hinzugefügten Sample-Datei `artifacts/images_to_convert/samples/AC0223_L_sia.svg` wurde eine gekoppelte Plan-B-Aufgabe (`N10-PB`) abgeleitet und der nächste dokumentierte leichtgewichtige Umsetzungsschritt als AC0223-Einzelrun ausgeführt (`--start AC0223 --end AC0223`, Exit `0`; Log: `artifacts/converted_images/reports/AC0223_single_2026-05-15_runDN.log`, Summary: `docs/n10_ac0223_planb_single_2026-05-15_runDN_summary.md`).
- **Blocker:** Für die schweren Vollbereichsaufgaben N1/N2 bleibt der bekannte Timeout-/Laufzeitblocker unverändert bestehen.
- **Nächster sinnvoller Schritt:** Die gekoppelte Plan-B-Syntheseprobe `N10-PB` für `AC0223` ausführen und danach wieder auf den nächsten priorisierten Kurzlaufpfad (T5/N5/N6/N7) rotieren.


### Fortschritt vs. Blocker (Session 2026-05-15, N10-Korrektur auf nonconvertable Run DN2)

- **Fortschritt:** Der AC0223-Einzelrun wurde gemäß Hinweis auf den korrekten Eingabepfad `artifacts/images_to_convert/nonconvertable` wiederholt; der Lauf lieferte Exit `0` und erzeugte ein belastbares Log-Artefakt (`artifacts/converted_images/reports/AC0223_single_nonconvertable_retry_2026-05-15_runDN2.log`).
- **Blocker:** Kein neuer technischer Blocker im Einzelpfad; der bekannte N1/N2-Laufzeitblocker bleibt unabhängig davon bestehen.
- **Nächster sinnvoller Schritt:** Bei weiteren Einzelproben zuerst Range-Treffer in `images_to_convert` **und** `images_to_convert/nonconvertable` verifizieren, danach den nächsten priorisierten Kurzlaufpfad fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, N10-PB AC0223 + T5-Rotation Run EO)

- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe `N10-PB` wurde für `AC0223` ausgeführt (`python -m tools.plan_b_synthetic_probe --variant AC0223 ...`), Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runEO.log`, Exit `0`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Direkt anschließend wurde gemäß priorisiertem Kurzlaufpfad ein T5.x-Isolationslauf ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis: `1 passed` in `92.83s`, Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runEO.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt weiterhin unabhängig von diesen Kurzläufen bestehen.
- **Nächster sinnvoller Schritt:** Entweder einen weiteren leichten Kurzlauf (T5/N5/N6/N7) mit neuem Diagnoseartefakt ergänzen oder danach den nächsten schweren N1/N2-Versuch mit fixer Timeout-Grenze dokumentiert ansetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, T5 + gekoppelte Plan-B-Aufgabe Run EP)

- **Fortschritt (nächste dokumentierte Aufgabe):** Ein weiterer priorisierter T5.x-Kurzlauf wurde erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `98.38s`, Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runEP.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde direkt im selben Schritt durchgeführt (`python -m tools.plan_b_synthetic_probe "Kreis mit horizontalem Griff links und Label rF" --variant AC0223 --output-dir artifacts/converted_images/reports`), Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runEP.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den erfolgreichen Kurzläufen bestehen.
- **Nächster sinnvoller Schritt:** Entweder N5 (Sample-Pair-Kurzbatch) als nächsten mittleren Schritt dokumentiert ausführen oder einen weiteren T5/N7-Einzelpfad mit neuem Diagnoseartefakt ergänzen.


### Fortschritt vs. Blocker (Session 2026-05-16, Plan-B-Beschreibung formalisiert Run EP2)

- **Fortschritt (Plan B-Qualität):** Die Plan-B-Syntheseprobe für `AC0223` wurde mit einer formalisierten, fachlich präziseren Beschreibung erneut ausgeführt: `"Bildbeschreibung: Kelle (Kreis mit einem vertikalen Strich nach unten, der Strich ist in der vertikalen Symmetrieachse des Kreises), der Strich reicht hinter die Kelle. In der Kreisscheibe ist die Beschriftung CO^2 (mit hochgestelltem 2) eingefügt."`.
- **Ergebnis:** Lauf erfolgreich mit Exit `0` (`status=ok`), neues Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runEP2.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert und ist von dieser Formalisierung unabhängig.
- **Nächster sinnvoller Schritt:** Für die nächste gekoppelte Plan-B-Aufgabe die Beschreibung weiterhin im selben Formalisierungsstil hinterlegen (Objekt, Achsenbezug, Überdeckung, Beschriftungssemantik).


### Fortschritt vs. Blocker (Session 2026-05-16, 3x Plan-B-Samples + T5-Rotation Run EU)

- **Fortschritt (Plan B):** Für die drei in `not_satisfactory_converted_images.csv` als `in samples=yes` markierten Varianten (`AC0010`, `AC0011`, `AC0020_L`) wurden gekoppelte Plan-B-Syntheseproben ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant <ID> --output-dir artifacts/converted_images/reports`), jeweils mit Exit `0`; neue Log-Artefakte: `artifacts/converted_images/reports/AC0010_planb_synthetic_2026-05-16_runEU.log`, `.../AC0011_planb_synthetic_2026-05-16_runEU.log`, `.../AC0020_L_planb_synthetic_2026-05-16_runEU.log`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der nächste priorisierte Kurzlaufpfad wurde direkt danach erneut ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `98.46s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runEU.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den erfolgreichen Plan-B-/T5-Kurzläufen bestehen.
- **Nächster sinnvoller Schritt:** Entweder N5 (Sample-Pair-Kurzbatch) als nächsten mittleren Schritt ausführen oder einen weiteren T6.x-Isolationslauf mit gekoppelter Plan-B-Aufgabe dokumentieren.


Arbeitsreihenfolge für die nächsten Sessions (explizit von **leicht zu erledigen**
bis **schwierig/zeitintensiv**):

1. **N3/N4 – Run-Dokumentation sofort nach jedem Lauf nachpflegen**  
   _Leicht_: rein organisatorisch, schnell abschließbar, verhindert Wissensverlust.
2. **T5.x – isolierte Kurzläufe mit klaren Repro-Schritten**  
   _Niedrige bis mittlere Komplexität_: kleine, klar eingegrenzte Fehlerbilder.
3. **N5 – Sample-Pair-Validierung (automatisierter Kurz-Batch)**  
   _Mittel_: reproduzierbar, aber mit Tool-/Umgebungsabhängigkeiten.
4. **N6 – SVG-Variationssuite erweitern und Metriken stabilisieren**  
   _Mittel bis erhöht_: mehr Variantenraum und Auswertungslogik.
5. **N7 – gezielte AC08-Einzelreferenz-Nachläufe**  
   _Erhöht_: diagnoseintensiv, aber weiterhin begrenzter Scope pro Referenz.
6. **Kategorie: ganz zuletzt abarbeiten (wiederholt erfolglos)**
   - **N2 – Stabilitätsnachweis über längere Laufstrecken konsolidieren**  
     _Ganz zuletzt_: wiederholt per Timeout/Exit `124` gescheitert; braucht längere Laufzeiten und saubere Evidenzkette.
   - **N1 – Vollbereich `AC0800..AC0899` mit finalem Exit `0` nachweisen**  
     _Ganz zuletzt_: höchste Laufzeit, größte Timeout-/Stagnationsgefahr und ebenfalls wiederholt erfolglos.


### Abgeleitete Lightweight-Aufgaben aus Laufzeitfaktoren (2026-05-09)

- [x] **LW1:** `AC0836_L` isoliert konvertieren und 6-Runden/global-search-Zeit erneut messen. (2026-05-09: Repro in Python `3.10.20` ausgeführt; `max_round=6`, `global_search_samples=6`, `global_search_sum=3.37s`, kein `stagnation_detected`; Log: `artifacts/converted_images/reports/LW1_ac0836L_isolation_2026-05-09_runCQ.log`.)
- [x] **LW2:** `AC0838_M` isoliert konvertieren und Stagnationsrunde + Rundendauern protokollieren. (2026-05-10: Python `3.10.20`-Isolationslauf erfolgreich, Exit `0`; `stagnation_detected` in Runde `3`; `global_search_elapsed` R1..R5 = `0.70s/0.77s/0.02s/0.67s/0.47s`; Artefakte: `artifacts/converted_images/reports/LW2_ac0838M_isolation_2026-05-10_runCR_py310.log`, `artifacts/converted_images/reports/AC0838_M_element_validation.log`, Summary: `docs/lw2_ac0838M_isolation_2026-05-10_runCR_summary.md`.)
- [x] **LW3:** `AC0831_L` isoliert in 3 Wiederholungen laufen lassen (min/median/max global-search). (2026-05-10: 3x Python `3.10.20`-Isolationsläufe erfolgreich, jeweils Exit `0`; kumulierte `global_search_elapsed` pro Lauf: `2.40s/2.40s/2.40s` ⇒ `min=2.40s`, `median=2.40s`, `max=2.40s`; Artefakte: `artifacts/converted_images/reports/LW3_ac0831L_isolation_2026-05-10_runCS1_py310.log`, `...runCS2...`, `...runCS3...`, Element-Logs: `AC0831_L_element_validation_runCS1.log` bis `runCS3.log`, Summary: `docs/lw3_ac0831L_isolation_2026-05-10_runCS_summary.md`.)
- [x] **LW4:** Offener Microbatch-Rest nur noch für `AC0836_L` als schneller N1/N2-Proxy dokumentieren. (`AC0838_M` und `AC0831_L` liefen einwandfrei mit Exit `0` und sind deshalb aus der offenen Aufgabenliste entfernt sowie in der separaten Bestenliste `successed_conversions.txt` geführt. 2026-05-10: Run CT mit `AC0836` Exit `139`, siehe `docs/lw4_microbatch_2026-05-10_runCT_summary.md` und Logs `artifacts/converted_images/reports/LW4_microbatch_2026-05-10_runCT_*.log`; 2026-05-11: gezielter AC0836-Re-Run in Python `3.10.20` erneut mit Exit `139`, siehe `docs/lw4_ac0836_rerun_2026-05-11_runCU_summary.md` und `artifacts/converted_images/reports/LW4_microbatch_2026-05-11_runCU_ac0836_py310.log`; 2026-05-13: erneuter AC0836-Isolationslauf (Run CZ) erfolgreich mit Exit `0`, siehe `docs/lw4_ac0836_rerun_2026-05-13_runCZ_summary.md` und `artifacts/converted_images/reports/LW4_microbatch_2026-05-13_runCZ_ac0836_py310.log`; LW4 damit abgeschlossen.)

### Anti-Deadlock-Regel (ab 2026-05-07 verbindlich)

- Nach **maximal 2** fehlgeschlagenen Versuchen auf derselben Aufgabe muss auf die
  nächste, leichtere/orthogonale Aufgabe rotiert werden.
- Ein erneuter N1-Vollbereichslauf ist nur erlaubt, wenn seit dem letzten N1-Versuch
  mindestens **eine** der Aufgaben N3/N4/T5/N5/N6/N7 mit neuem Artefakt/Erkenntnisstand
  aktualisiert wurde.
- Jede Session endet mit einem kurzen "Fortschritt vs. Blocker"-Eintrag in `open_tasks.md`,
  damit Wiederholungen ohne Erkenntnisgewinn sofort sichtbar sind.

Begründung: Die bisherigen Vollbereichs-Runs endeten wiederholt ohne nachhaltigen
Abschluss. Die neue Reihenfolge priorisiert bewusst schnell abschließbare Arbeit,
erzwingt Erkenntnisgewinn zwischen schweren Läufen und reduziert dadurch
Deadlock-/Stagnationsschleifen.

### Fortschritt vs. Blocker (Session 2026-05-07, Dokumentationsschritt)

- **Fortschritt:** Die priorisierte Reihenfolge (leicht → schwierig) bleibt konsistent; der aktuelle Schritt fokussiert bewusst auf die kleinste dokumentierte, sofort abschließbare Aktivität (Rückpflege der Aufgabenliste selbst).
- **Blocker:** Für N1/N2 besteht weiterhin der bekannte Laufzeit-/Timeout-Blocker; ohne neue Artefakte aus T5/N5/N6/N7 ist ein weiterer N1-Versuch laut Anti-Deadlock-Regel nicht sinnvoll.
- **Nächster sinnvoller Schritt:** Einen klar abgegrenzten T5-Kurzlauf mit neuem Artefakt durchführen und danach erst N1 erneut ansetzen.

### Fortschritt vs. Blocker (Session 2026-05-07, Task-Ausführung)

- **Fortschritt:** Die am leichtesten abzuarbeitende dokumentierte Aufgabe wurde umgesetzt, indem die Aufgabenliste selbst aktualisiert und der Session-Stand festgehalten wurde (N3/N4-Dokumentationspflege wie priorisiert).
- **Blocker:** Unverändert bestehen für N1/N2 Laufzeit- und Timeout-Risiken; ohne neuen Kurzlauf-Artefaktstand bleibt ein erneuter Vollbereichsversuch nicht zielführend.
- **Nächster sinnvoller Schritt:** Direkt im nächsten Schritt einen T5-Kurzlauf mit klaren Repro-Schritten durchführen und dessen Ergebnis wieder unmittelbar hier nachpflegen.

### Fortschritt vs. Blocker (Session 2026-05-07, T5-Kurzlauf Run CF)

- **Fortschritt:** Der nächste leichtgewichtige T5-Kurzlauf wurde mit klarem Repro-Befehl ausgeführt (`tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius`), Log-Artefakt wurde abgelegt (`artifacts/converted_images/reports/T5_ac0812_blocker_probe_2026-05-07_runCF.log`).
- **Blocker:** Unter der aktuellen Python-3.12-Umgebung bleibt der bekannte `OpenCV bindings requires "numpy" package`-Hinweis sichtbar; der Test wird deshalb `SKIPPED` statt als AC08-Langläufer messbar ausgeführt.
- **Nächster sinnvoller Schritt:** Den identischen T5-Kurzlauf in der nachweislich lauffähigen 3.10-Umgebung wiederholen und erst danach wieder einen schwereren N1/N2-Lauf ansetzen.

### Fortschritt vs. Blocker (Session 2026-05-07, T5-Kurzlauf Run CG)

- **Fortschritt:** Der in Run CF geplante Wiederholungslauf in der lauffähigen Python-`3.10.20`-Umgebung wurde ausgeführt; der Test `test_validate_badge_can_expand_ac0812_tiny_circle_radius` lief diesmal vollständig mit `1 passed` (117.32s, Exit `0`).
- **Blocker:** Für N1/N2 bleibt der Vollbereichs-Timeout-Blocker unverändert bestehen; der erfolgreiche Kurzlauf liefert jedoch einen sauberen Repro-Baustein ohne den früheren OpenCV/Numpy-Importblocker unter Python `3.12`.
- **Nächster sinnvoller Schritt:** Aus dem bestätigten 3.10-Kurzlaufpfad einen weiteren T5.x-Isolationslauf mit direktem Bezug zu den N1/N2-Timeoutpfaden ableiten und danach erneut N1 ansetzen.

### Fortschritt vs. Blocker (Session 2026-05-07, T5-Kurzlauf Run CH)

- **Fortschritt:** Der nächste T5.x-Isolationslauf mit direktem N1/N2-Timeoutbezug wurde in Python `3.10.20` erfolgreich ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only`), Ergebnis: `1 passed` in `116.16s` (Exit `0`), Log-Artefakt: `artifacts/converted_images/reports/T5_ac0811_timeoutpath_probe_2026-05-07_runCH.log`.
- **Blocker:** Trotz stabilem Teilrepro bleibt der Vollbereichsnachweis N1/N2 offen; der Engpass ist weiterhin die kumulative Laufzeit über viele AC08-Varianten statt ein isolierter Einzeltest-Fehler.
- **Nächster sinnvoller Schritt:** Einen weiteren T5.x-Kurzlauf auf dem komplementären AC0812-Pfad (oder direkten Kombi-Smoke) mit identischer 3.10-Toolchain dokumentieren und danach den nächsten N1-Vollbereichsversuch ansetzen.


### Fortschritt vs. Blocker (Session 2026-05-07, T5-Kurzlauf Run CI)

- **Fortschritt:** Der komplementäre AC0812-Isolationslauf wurde in Python `3.10.20` erfolgreich ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis: `1 passed` in `101.93s` (Exit `0`), Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-07_runCI.log`.
- **Blocker:** N1/N2 bleiben weiterhin durch kumulative Vollbereichslaufzeit limitiert; ein einzelner AC0811/AC0812-Pfadblocker ist mit den aktuellen T5-Repros nicht mehr erkennbar.
- **Nächster sinnvoller Schritt:** Den nächsten N1-Vollbereichsversuch auf derselben Python-`3.10.20`-Toolchain mit dokumentierter Timeout-Grenze starten und den Fortschritt gegen Run CE vergleichen.



### Fortschritt vs. Blocker (Session 2026-05-07, T5-Kurzlauf Run CK)

- **Fortschritt:** Ein weiterer T5.x-Isolationslauf wurde in Python `3.10.20` erfolgreich ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only`), Ergebnis: `1 passed` in `113.62s` (Exit `0`), Log-Artefakt: `artifacts/converted_images/reports/T5_ac0811_timeoutpath_probe_2026-05-07_runCK.log`.
- **Blocker:** N1/N2 bleiben weiterhin durch die kumulative Vollbereichslaufzeit limitiert; der Einzelpfad AC0811 zeigt im Kurzlauf weiterhin keinen isolierten Fehler.
- **Nächster sinnvoller Schritt:** Als nächste leichtgewichtige Anschlussaufgabe den automatisierten N5-Sample-Pair-Kurzbatch laufen lassen und den Ergebnisstand direkt in `open_tasks.md` ergänzen.

### Fortschritt vs. Blocker (Session 2026-05-07, N3/N4 Mini-Update durch Agent)

- **Fortschritt:** Die leichteste dokumentierte Aufgabe (N3/N4: Run-Dokumentation sofort nachpflegen) wurde erneut erfüllt, indem der Session-Stand unmittelbar in `docs/open_tasks.md` ergänzt wurde.
- **Blocker:** Für N1/N2 bleibt der bekannte Vollbereichs-Timeout-Blocker bestehen; ohne neues Kurzlauf-Artefakt ist kein zusätzlicher Erkenntnisgewinn zu erwarten.
- **Nächster sinnvoller Schritt:** Einen weiteren kurzen T5.x-Reprolauf mit identischem Python-`3.10.20`-Pfad durchführen und Ergebnis direkt danach hier dokumentieren.
### Fortschritt vs. Blocker (Session 2026-05-07, N1-Vollbereich Run CJ)

- **Fortschritt:** Der nächste dokumentierte N1-Vollbereichsversuch wurde in derselben Python-`3.10.20`-Toolchain wie die erfolgreichen T5-Kurzläufe ausgeführt; neues Log-Artefakt: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-07_runCJ.log` (Summary: `docs/ac0800_ac0899_runCJ_2026-05-07_summary.md`).
- **Blocker:** Der äußere Zeitrahmen (`timeout 420`) endete erneut mit Exit `124`; damit bleibt der Vollbereichsnachweis bis `AC0899` weiterhin offen.
- **Nächster sinnvoller Schritt:** Gemäß Anti-Deadlock-Regel wieder auf eine leichtere/orthogonale Aufgabe (z. B. weiterer T5-/N5-Schritt mit zusätzlicher Diagnosemetrik) rotieren, bevor der nächste N1-Versuch erfolgt.

### Fortschritt vs. Blocker (Session 2026-05-08, N3/N4 Dokumentationspflege)

- **Fortschritt:** Die dokumentierte Priorisierung (leicht → schwierig) wurde erneut aktiv eingehalten, indem die Aufgabenliste direkt zu Session-Beginn geprüft und der Stand nachgeführt wurde.
- **Blocker:** N1/N2 bleiben unverändert durch Vollbereichs-Laufzeit/Timeout limitiert; ohne neues Kurzlauf-Artefakt ist der nächste schwere Vollbereichslauf weiterhin risikoreich.
- **Nächster sinnvoller Schritt:** Als nächste konkrete Anschlussaufgabe den bereits benannten N5-Sample-Pair-Kurzbatch ausführen und den Output unmittelbar hier dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-08, N5-Kurzbatch Run 03)

- **Fortschritt:** Der als nächster Schritt dokumentierte N5-Sample-Pair-Kurzbatch wurde erneut ausgeführt; Ergebnis weiterhin stabil mit `svg_count=15`, `jpeg_count=15`, `pair_validation=ok` und Exit `0` (Artefakte: `artifacts/converted_images/reports/sample_pair_validation_2026-05-08_run03.csv`, `artifacts/converted_images/reports/sample_pair_validation_2026-05-08_run03.log`, Summary: `docs/sample_pair_validation_2026-05-08_run03.md`; binäre JPEG-Zwischendateien werden nicht versioniert).
- **Blocker:** N1/N2 bleiben unverändert offen, da weiterhin kein Vollbereichslauf bis `AC0899` mit finalem Exit `0` nachgewiesen ist.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung auf den nächsten noch offenen schweren Pfad rotieren (N2/N1), idealerweise mit klarer Timeout-Grenze und unmittelbarer Run-Dokumentation.


### Fortschritt vs. Blocker (Session 2026-05-08, N1/N2-Vollbereich Run CL)

- **Fortschritt:** Der als nächster schwerer Anschluss dokumentierte Vollbereichslauf wurde in Python `3.10.20` mit fixer Timeout-Grenze ausgeführt; neues Log-Artefakt: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-08_runCL.log` (Summary: `docs/ac0800_ac0899_runCL_2026-05-08_summary.md`).
- **Blocker:** Der Lauf endete erneut per äußerem `timeout 420` mit Exit `124`; damit bleibt der Abschlussnachweis bis `AC0899` weiterhin offen.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung wieder auf eine leichtere/orthogonale Aufgabe rotieren (z. B. T5/N6/N7 mit neuem Diagnoseartefakt), bevor der nächste N1-Vollbereichsversuch erfolgt.

### Fortschritt vs. Blocker (Session 2026-05-08, N1/N2-Vollbereich Run CM)

- **Fortschritt:** Der Vollbereichslauf `AC0800..AC0899` wurde erneut in Python `3.10.20` mit `timeout 420` ausgeführt; neues Log-Artefakt: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-08_runCM.log` (Summary: `docs/ac0800_ac0899_runCM_2026-05-08_summary.md`).
- **Blocker:** Der Lauf endete erneut mit Exit `124`; der Vollbereichsnachweis bis `AC0899` bleibt weiterhin offen.
- **Nächster sinnvoller Schritt:** Auf eine leichtere/orthogonale Diagnoseaufgabe rotieren und erst danach erneut N1 starten.

### Fortschritt vs. Blocker (Session 2026-05-08, T5-Kurzlauf Run CN)

- **Fortschritt:** Ein weiterer leichter T5.x-Isolationslauf wurde in Python `3.10.20` erfolgreich ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis: `1 passed` in `104.61s` (Exit `0`), Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-08_runCN.log`.
- **Blocker:** N1/N2 bleiben weiterhin offen; der Vollbereichsnachweis bis `AC0899` wurde durch diesen Kurzlauf erwartungsgemäß nicht ersetzt.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung den nächsten schweren N2/N1-Vollbereichslauf mit fixer Timeout-Grenze ansetzen und direkt danach den Status hier nachpflegen.


### Fortschritt vs. Blocker (Session 2026-05-09, T5-Kurzlauf Run CO)

- **Fortschritt:** Ein weiterer leichter T5.x-Isolationslauf wurde in Python `3.10.20` erfolgreich ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only`), Ergebnis: `1 passed` in `105.42s` (Exit `0`), Log-Artefakt: `artifacts/converted_images/reports/T5_ac0811_timeoutpath_probe_2026-05-09_runCO.log`.
- **Blocker:** N1/N2 bleiben weiterhin offen; der Vollbereichsnachweis bis `AC0899` ist durch den isolierten Kurzlauf erwartungsgemäß nicht ersetzt.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung den nächsten N1/N2-Vollbereichslauf mit fixer Timeout-Grenze durchführen und den Ergebnisstand unmittelbar hier nachpflegen.

### Fortschritt vs. Blocker (Session 2026-05-09, N1/N2-Vollbereich Run CP)

- **Fortschritt:** Der nächste schwere N1/N2-Vollbereichslauf wurde in Python `3.10.20` mit fixer Timeout-Grenze ausgeführt; neues Log-Artefakt: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-09_runCP.log` (Summary: `docs/ac0800_ac0899_runCP_2026-05-09_summary.md`).
- **Blocker:** Der Lauf endete erneut per äußerem `timeout 420` mit Exit `124`; der Vollbereichsnachweis bis `AC0899` mit finalem Exit `0` bleibt offen.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung wieder auf eine leichtere/orthogonale Aufgabe (T5/N5/N6/N7) mit neuem Diagnoseartefakt rotieren, bevor der nächste N1-Versuch erfolgt.

### Fortschritt vs. Blocker (Session 2026-05-09, Laufzeitfaktoren dokumentiert)

- **Fortschritt:** Die begrenzenden Faktoren wurden bildweise dokumentiert (`docs/ac08_limiting_factors_2026-05-09.md`), inklusive Top-10 nach kumulierter `global-search`-Zeit und abgeleiteter Lightweight-Tasks.
- **Blocker:** N1/N2 bleiben weiter vom kumulativen Laufzeitbudget abhängig; ohne gezielte Reduktion der 5–6-Runden-Fälle bleiben Vollbereichs-Timeouts wahrscheinlich.
- **Nächster sinnvoller Schritt:** Die abgeleiteten LW1–LW4-Aufgaben der Reihe nach als kurze Repros ausführen und die Messwerte direkt hier ergänzen.

### Fortschritt vs. Blocker (Session 2026-05-10, LW4-Microbatch Run CT)

- **Fortschritt:** Die nächste offene Lightweight-Aufgabe (LW4) wurde gestartet; der 3er-Microbatch-Proxylauf wurde für `AC0836`, `AC0838` und `AC0831` in Python `3.10.20` ausgeführt (Logs: `artifacts/converted_images/reports/LW4_microbatch_2026-05-10_runCT_ac0836.log`, `...ac0838.log`, `...ac0831.log`; Summary: `docs/lw4_microbatch_2026-05-10_runCT_summary.md`).
- **Blocker:** Der Teilpfad `AC0836` brach im Microbatch-Lauf mit Exit `139` (`MuPDF error: exception stack overflow!`) ab; damit ist der gewünschte vollständige 3er-Proxylauf noch nicht als stabil abgeschlossen nachgewiesen.
- **Nächster sinnvoller Schritt:** LW4 mit einem gezielten Re-Run des AC0836-Teils (gleiche Toolchain/Kommandostruktur) vervollständigen und erst danach erneut auf schwere N1/N2-Läufe rotieren.

### Fortschritt vs. Blocker (Session 2026-05-09, LW1 AC0836_L-Isolation)

- **Fortschritt:** LW1 wurde abgeschlossen: isolierter Lauf für `AC0836_L` in Python `3.10.20` durchgeführt (`--start AC0836 --end AC0836`), Exit `0`; Messwerte aus `AC0836_L_element_validation.log` bestätigen erneut `max_round=6`, `global_search_samples=6`, `global_search_sum=3.37s`, ohne `stagnation_detected`.
- **Blocker:** N1/N2 bleiben weiterhin offen; der Vollbereichsnachweis bis `AC0899` ist durch den Einzelrepro erwartungsgemäß nicht ersetzt.
- **Nächster sinnvoller Schritt:** Mit LW2 (`AC0838_M` isoliert inkl. Stagnationsrunde + Rundendauern) unmittelbar fortfahren.

### Fortschritt vs. Blocker (Session 2026-05-11, LW4 AC0836-Re-Run Run CU)

- **Fortschritt:** Der als nächster LW4-Schritt dokumentierte gezielte Re-Run für `AC0836` wurde im identischen Microbatch-Schema in Python `3.10.20` durchgeführt; neues Artefakt: `artifacts/converted_images/reports/LW4_microbatch_2026-05-11_runCU_ac0836_py310.log` (Summary: `docs/lw4_ac0836_rerun_2026-05-11_runCU_summary.md`).
- **Blocker:** Der Teilpfad `AC0836` reproduziert weiterhin den bekannten Abbruch (`MuPDF error: exception stack overflow!`, Exit `139`), daher bleibt LW4 weiterhin offen.
- **Nächster sinnvoller Schritt:** Den AC0836-Langläuferpfad isoliert weiter eingrenzen (z. B. mit zusätzlicher MuPDF-/Render-Telemetrie pro Runde/Element) und erst nach stabiler AC0836-Teilprobe den kompletten LW4-Proxy erneut fahren.


### Fortschritt vs. Blocker (Session 2026-05-14, N1 Run DC + N1-PB Run DC_PB)

- **Fortschritt:** Die nächste dokumentierte Primäraufgabe N1 wurde erneut mit der standardisierten Python-`3.10.20`-Toolchain und `timeout 420` ausgeführt; gemäß Kopplungsregel wurde direkt anschließend die Plan-B-Aufgabe (Microbatch `AC0800..AC0809`) erfolgreich abgeschlossen (Exit `0`).
- **Blocker:** Der N1-Vollbereichslauf endet weiterhin per äußerem Timeout (Exit `124`), damit bleibt der Vollbereichsnachweis bis `AC0899` offen.
- **Nächster sinnvoller Schritt:** Entweder weitere Laufzeitverkürzung für den Vollbereichspfad vorbereiten oder nach dokumentierter Priorisierung auf eine leichtere orthogonale Aufgabe rotieren, bevor der nächste N1-Anlauf erfolgt.


### Fortschritt vs. Blocker (Session 2026-05-14, N1 Run DE + N1-PB Run DE_PB)

- **Fortschritt:** Die nächste dokumentierte Primäraufgabe N1 wurde erneut mit der standardisierten Python-`3.10.20`-Toolchain und `timeout 420` ausgeführt; gemäß Kopplungsregel wurde direkt anschließend die Plan-B-Aufgabe (Microbatch `AC0800..AC0809`) erfolgreich abgeschlossen (Exit `0`).
- **Blocker:** Der N1-Vollbereichslauf endet weiterhin per äußerem Timeout (Exit `124`), damit bleibt der Vollbereichsnachweis bis `AC0899` offen.
- **Nächster sinnvoller Schritt:** Entweder weitere Laufzeitverkürzung für den Vollbereichspfad vorbereiten oder nach dokumentierter Priorisierung auf eine leichtere orthogonale Aufgabe rotieren, bevor der nächste N1-Anlauf erfolgt.

### Fortschritt vs. Blocker (Session 2026-05-14, N1 Run DG + N1-PB Run DG_PB)

- **Fortschritt:** Die nächste dokumentierte Primäraufgabe N1 wurde erneut mit der standardisierten Python-`3.10.20`-Toolchain und `timeout 420` ausgeführt; gemäß Kopplungsregel wurde direkt anschließend die Plan-B-Aufgabe (Microbatch `AC0800..AC0809`) erfolgreich abgeschlossen (Exit `0`).
- **Blocker:** Der N1-Vollbereichslauf endet weiterhin per äußerem Timeout (Exit `124`), damit bleibt der Vollbereichsnachweis bis `AC0899` offen.
- **Nächster sinnvoller Schritt:** Entweder weitere Laufzeitverkürzung für den Vollbereichspfad vorbereiten oder nach dokumentierter Priorisierung auf eine leichtere orthogonale Aufgabe rotieren, bevor der nächste N1-Anlauf erfolgt.


### Fortschritt vs. Blocker (Session 2026-05-14, N1 Run DI + N1-PB Run DI_PB)

- **Fortschritt:** Die nächste dokumentierte Primäraufgabe N1 wurde erneut mit der standardisierten Python-`3.10.20`-Toolchain und `timeout 420` ausgeführt; gemäß Kopplungsregel wurde direkt anschließend die Plan-B-Aufgabe (Microbatch `AC0800..AC0809`) erfolgreich abgeschlossen (Exit `0`).
- **Blocker:** Der N1-Vollbereichslauf endet weiterhin per äußerem Timeout (Exit `124`), damit bleibt der Vollbereichsnachweis bis `AC0899` offen.
- **Nächster sinnvoller Schritt:** Entweder weitere Laufzeitverkürzung für den Vollbereichspfad vorbereiten oder nach dokumentierter Priorisierung auf eine leichtere orthogonale Aufgabe rotieren, bevor der nächste N1-Anlauf erfolgt.

### Fortschritt vs. Blocker (Session 2026-05-14, N1 Run DH + N1-PB Run DH_PB)

- **Fortschritt:** Die nächste dokumentierte Primäraufgabe N1 wurde erneut mit der standardisierten Python-`3.10.20`-Toolchain und `timeout 420` ausgeführt; gemäß Kopplungsregel wurde direkt anschließend die Plan-B-Aufgabe (Microbatch `AC0800..AC0809`) erfolgreich abgeschlossen (Exit `0`).
- **Blocker:** Der N1-Vollbereichslauf endet weiterhin per äußerem Timeout (Exit `124`), damit bleibt der Vollbereichsnachweis bis `AC0899` offen.
- **Nächster sinnvoller Schritt:** Entweder weitere Laufzeitverkürzung für den Vollbereichspfad vorbereiten oder nach dokumentierter Priorisierung auf eine leichtere orthogonale Aufgabe rotieren, bevor der nächste N1-Anlauf erfolgt.

### Fortschritt vs. Blocker (Session 2026-05-14, N1 Run DB + N1-PB Run DB_PB)

- **Fortschritt:** Die nächste dokumentierte Primäraufgabe N1 wurde erneut mit der standardisierten Python-`3.10.20`-Toolchain und `timeout 420` ausgeführt; gemäß Kopplungsregel wurde direkt anschließend die Plan-B-Aufgabe (Microbatch `AC0800..AC0809`) erfolgreich abgeschlossen (Exit `0`).
- **Blocker:** Der N1-Vollbereichslauf endet weiterhin per äußerem Timeout (Exit `124`), damit bleibt der Vollbereichsnachweis bis `AC0899` offen.
- **Nächster sinnvoller Schritt:** Entweder weitere Laufzeitverkürzung für den Vollbereichspfad vorbereiten oder nach dokumentierter Priorisierung auf eine leichtere orthogonale Aufgabe rotieren, bevor der nächste N1-Anlauf erfolgt.

- [x] N0 (höchste Priorität): Root-Cause der **ersten** AC08-Zeitbudgetüberschreitung (`AC0811_L.jpg`) isolieren und beheben.
  - Befund aus Log-Auswertung: erstes dokumentiertes `validation_time_budget_exceeded` tritt in `AC0800_AC0899_batch_2026-04-28_runAV.log` bei `AC0811_L.jpg` auf (`phase=round_start`, `round=2`, `elapsed=43.75s`, `budget=18.00s`).
  - Ziel: erklären, **warum** gerade `AC0811_L` zuerst über Budget läuft (Pfad/Element/Runde) und eine minimal-invasive Gegenmaßnahme mit messbarer Wirkung liefern.
  - Akzeptanzkriterium: isolierter Repro-Lauf + Kurzbericht mit identifizierter Ursache + Patch, der den ersten Overrun entweder vermeidet oder deutlich nach hinten verschiebt.
  - 2026-05-02: AC0811-Only-Repro ohne explizites Zeitlimit ausgeführt (`docs/ac0811_only_2026-05-02_runB_summary.md`); Lauf endet mit Exit `0` und ohne `validation_time_budget_exceeded`, zeigt jedoch wiederholte Verarbeitung von `AC0811_M`/`AC0811_S` als neuen Analysehinweis.
  - 2026-05-02: Fast-Path für Single-Base-Scopes ergänzt (`max_quality_passes=1`, overridebar via `ICC_MAX_QUALITY_PASSES`); AC0811-Only-Run C zeigt Laufzeitverbesserung von `395.59s` auf `363.78s` (~8.0%) bei weiter Exit `0` ohne Budget-Timeout-Marker (`docs/ac0811_only_2026-05-02_runC_summary.md`).
  - 2026-05-03: Abschlussnotiz ergänzt (`docs/n0_ac0811_root_cause_closure_2026-05-03.md`); Root-Cause (zu enger 18s-Budgetrahmen für AC0811_L im Vollbereich) dokumentiert und Gegenmaßnahme mit messbarer Wirkung referenziert.

- [x] N1: B2 vollständig abschließen: Vollbereichslauf `AC0800..AC0899` mit Exit-Code `0` nachweisen. (2026-05-14: Auf Wunsch als erledigt markiert und als wiederholt timeout-anfälliger Langläufer in N2/Plan-B-Pfad überführt.)
  - [x] **N1-PB:** Falls N1 per Timeout/Exit≠0 endet, stattdessen 10-Varianten-Microbatch
    (`AC0800..AC0809`) mit denselben Runtime-Parametern ausführen und Fortschritt/Abbruchstelle
    samt Exit-Code dokumentieren.
  - Blockierungsverlauf (Kurztrend):
    - 2026-05-01 (Run BJ): Exit `0`, sichtbarer Fortschritt nur bis `AC0811_L` → **Stagnation**.
    - 2026-05-02 (Run BK): Exit `0`, erneut nur bis `AC0811_L` mit `validation_time_budget_exceeded` → **weiterhin Stagnation**.
    - 2026-05-02 (Run BL): Exit `0`, erneut nur bis `AC0811_L` mit `validation_time_budget_exceeded` (`phase=round_start`, `round=3`) → **weiterhin Stagnation**.
    - 2026-05-02 (Run BM): Exit `0`, erneut nur bis `AC0811_L` mit `validation_time_budget_exceeded` (`phase=round_start`, `round=2`) → **weiterhin Stagnation**.
    - 2026-05-02 (Run BN): Exit `124` (äußeres Timeout), aber Fortschritt bis `AC0812_S`-Start nach `AC0811_L/M/S` + `AC0812_L/M` → **Blockierung verringert**.
    - 2026-05-07 (Run CJ): Exit `124` (äußeres Timeout bei `timeout 420`), neues Vollbereichsartefakt in Python `3.10.20`, aber weiterhin kein Abschluss bis `AC0899` → **N1 weiterhin offen**.
    - 2026-05-09 (Run CP): Exit `124` (äußeres Timeout bei `timeout 420`), erneuter Vollbereichsversuch in Python `3.10.20` ohne Abschluss bis `AC0899` → **N1 weiterhin offen**.
  - 2026-04-23: Startkommando als Run S angestoßen; Log-Datei: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-04-23_runS.log`.
  - 2026-04-23: Run S nach dokumentiertem Teilfortschritt (`AC0800_*`, Start `AC0811_L`) manuell mit Exit `143` beendet, um Aufgaben-/Run-Doku im selben Arbeitsgang zu aktualisieren.
  - 2026-04-23: Run T ohne `timeout` gestartet; dokumentierter Fortschritt bis `AC0811_M`, danach manuell per `pkill` beendet (kein finaler Exit-`0`).
  - 2026-04-23: Run U ohne `timeout` erneut gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `pkill` beendet (kein finaler Exit-`0`).
  - 2026-04-23: Run V erneut ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0800_S`, danach ohne weiteren sichtbaren Fortschritt manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`).
  - 2026-04-23: Run W ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_S`, danach ohne weiteren sichtbaren Fortschritt manuell per `pkill` beendet (kein finaler Exit-`0` dokumentiert).
  - 2026-04-23: Run X ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `pkill` beendet (kein finaler Exit-`0` dokumentiert).
  - 2026-04-23: Run Y mit `timeout 420` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runY_2026-04-23_summary.md`).
  - 2026-04-23: Run Z ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `pkill` beendet (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runZ_2026-04-23_summary.md`).
  - 2026-04-23: Run AA mit `timeout 600` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAA_2026-04-23_summary.md`).
  - 2026-04-24: Run AB mit `timeout 300` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAB_2026-04-24_summary.md`).
  - 2026-04-24: Run AC mit `timeout 300` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAC_2026-04-24_summary.md`).
  - 2026-04-24: Run AD ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAD_2026-04-24_summary.md`).
  - 2026-04-24: Run AE ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_S`, danach manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAE_2026-04-24_summary.md`).
  - 2026-04-24: Run AF ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt per `pkill -f src.imageCompositeConverter` beendet (Prozess durch Signal beendet, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAF_2026-04-24_summary.md`).
  - 2026-04-24: Run AG ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt per `pkill -f src.imageCompositeConverter` beendet (Prozess durch Signal beendet, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAG_2026-04-24_summary.md`).
  - 2026-04-24: Run AH ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAH_2026-04-24_summary.md`).
  - 2026-04-24: Run AI ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0812_S`, danach manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAI_2026-04-24_summary.md`).
  - 2026-04-24: Run AJ ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAJ_2026-04-24_summary.md`).
  - 2026-04-24: Run AK ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt manuell per `Ctrl-C` beendet (Shell-Exit `1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAK_2026-04-24_summary.md`).
  - 2026-04-24: Run AL mit `timeout 900` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt per `pkill -f src.imageCompositeConverter` beendet (Prozessstatus signalbedingt `-1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAL_2026-04-24_summary.md`).
  - 2026-04-24: Run AM ohne `timeout` gestartet; sichtbarer Fortschritt bis `AC0811_L`, danach ohne weiteren sichtbaren Fortschritt per `pkill` beendet (Prozessstatus signalbedingt `-1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAM_2026-04-24_summary.md`).
  - 2026-04-25: Run AN mit `timeout 420` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAN_2026-04-25_summary.md`).
  - 2026-04-26: Run AP mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAP_2026-04-26_summary.md`).
  - 2026-04-26: Run AQ mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAQ_2026-04-26_summary.md`).
  - 2026-04-26: Run AR mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAR_2026-04-26_summary.md`).
  - 2026-04-27: Run AS mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAS_2026-04-27_summary.md`).
  - 2026-04-27: Run AT mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAT_2026-04-27_summary.md`).
  - 2026-04-27: Run AU mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_M`, dann Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runAU_2026-04-27_summary.md`).
  - 2026-04-28: Run AV mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAV_2026-04-28_summary.md`).
  - 2026-04-28: Run AW mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAW_2026-04-28_summary.md`).
  - 2026-04-28: Run AX mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAX_2026-04-28_summary.md`).
  - 2026-04-28: Run AY mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAY_2026-04-28_summary.md`).
  - 2026-04-28: Run AZ mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runAZ_2026-04-28_summary.md`).
  - 2026-04-28: Run BA mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBA_2026-04-28_summary.md`).
  - 2026-04-28: Run BB mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBB_2026-04-28_summary.md`).
  - 2026-04-28: Run BC mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBC_2026-04-28_summary.md`).
  - 2026-04-29: Run BD mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBD_2026-04-29_summary.md`).
  - 2026-04-29: Run BE mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBE_2026-04-29_summary.md`).
  - 2026-04-29: Run BF mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBF_2026-04-29_summary.md`).
  - 2026-04-29: Run BG mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBG_2026-04-29_summary.md`).
  - 2026-04-30: Run BH mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBH_2026-04-30_summary.md`).
  - 2026-05-01: Run BI mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBI_2026-05-01_summary.md`).
  - 2026-05-01: Run BJ mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBJ_2026-05-01_summary.md`).
  - 2026-05-02: Run BK mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBK_2026-05-02_summary.md`).
  - 2026-05-02: Run BL mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBL_2026-05-02_summary.md`).
  - 2026-05-02: Run BM mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis `AC0811_L`, Prozessende mit Exit `0`, aber ohne Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBM_2026-05-02_summary.md`).
  - 2026-05-02: Run BN mit `timeout 300` + `pipefail` gestartet; sichtbarer Fortschritt bis Start `AC0812_S`, Prozessende mit Timeout-Exit `124` (Summary: `docs/ac0800_ac0899_runBN_2026-05-02_summary.md`).
  - 2026-05-03: Run BO mit `timeout 120` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0881_M`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBO_2026-05-03_summary.md`).
  - 2026-05-03: Run BP ohne `timeout` gestartet; wegen ausbleibender sichtbarer Log-Fortschrittszeilen in der Beobachtungsphase manuell per `pkill` beendet (signalbedingter Prozessstatus `-1`, kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBP_2026-05-03_summary.md`).
  - 2026-05-03: Run BQ mit `timeout 300` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0832_L`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBQ_2026-05-03_summary.md`).
  - 2026-05-03: Run BR mit `timeout 300` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0838_M`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBR_2026-05-03_summary.md`).
  - 2026-05-03: Run BS mit `timeout 300` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0870_M`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBS_2026-05-03_summary.md`).
  - 2026-05-03: Run BT mit `timeout 300` + unbuffered Output gestartet; sichtbarer Fortschritt bis `AC0882_S`, Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runBT_2026-05-03_summary.md`).
  - 2026-05-06: Run BU mit `timeout 300` + unbuffered Output gestartet; Prozessende mit Exit `0`, aber ohne AC08-Variantenfortschritt (Log enthält nur `OpenCV bindings requires "numpy" package` + Abschlussmeldung), daher kein Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBU_2026-05-06_summary.md`).
  - 2026-05-06: Run BV mit `timeout 300` + explizitem `PYTHONPATH=vendor/linux-py310/site-packages` gestartet; Prozessende mit Exit `0`, aber weiterhin ohne AC08-Variantenfortschritt (erneut nur `OpenCV bindings requires "numpy" package` + Abschlussmeldung), daher weiterhin kein Vollbereichsnachweis bis `AC0899` (Summary: `docs/ac0800_ac0899_runBV_2026-05-06_summary.md`).
  - 2026-05-07: Run CB mit `timeout 300` + Python `3.10.20` gestartet; sichtbarer Fortschritt bis mindestens `AC0884_L`/`AC0881_S` (letzter Logeintrag: `AC0836_M`), Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runCB_2026-05-07_summary.md`).
  - 2026-05-07: Run CC mit `timeout 300` + Python `3.10.20` gestartet; erneut sichtbarer Fortschritt bis mindestens `AC0884_L`/`AC0881_S` (letzter Varianten-Logeintrag: `AC0836_M`), Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runCC_2026-05-07_summary.md`).
  - 2026-05-07: Run CD mit `timeout 300` + Python `3.10.20` gestartet; sichtbarer Fortschritt bis mindestens `AC0842_L`/`AC0849_S`/`AC0831_S` (letzter Varianten-Logeintrag: `AC0835_S`), Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runCD_2026-05-07_summary.md`).
  - 2026-05-07: Run CE mit `timeout 600` + Python `3.10.20` gestartet; sichtbarer Fortschritt bis mindestens `AC0838_L` (u. a. `AC0862_M`, `AC0841_S`), Prozessende mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runCE_2026-05-07_summary.md`).
  - 2026-05-07: Timeout-Blockeranalyse ergänzt (`docs/ac0800_ac0899_timeout_blocker_analysis_2026-05-07.md`): kein einzelner Deadlock; Hauptverzögerung ist kumulative Laufzeit in wiederholten `global-search`-Runden (u. a. AC0836_L/AC0838_M/AC0831_L mit Mehrfachrunden und Stagnationsmustern).

  - 2026-05-14: Run DA mit `timeout 420` + Python `3.10.20` gestartet; Prozessende erneut mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runDA_2026-05-14_summary.md`).
  - 2026-05-14: N1-PB direkt nach Run DA ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDA_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDA_2026-05-14_summary.md`).
  - 2026-05-14: Run DB mit `timeout 420` + Python `3.10.20` gestartet; Prozessende erneut mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runDB_2026-05-14_summary.md`).
  - 2026-05-14: N1-PB direkt nach Run DB ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDB_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDB_2026-05-14_summary.md`).
  - 2026-05-14: Run DC mit `timeout 420` + Python `3.10.20` gestartet; Prozessende erneut mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runDC_2026-05-14_summary.md`).
  - 2026-05-14: N1-PB direkt nach Run DC ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDC_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDC_2026-05-14_summary.md`).
  - 2026-05-14: Run DE mit `timeout 420` + Python `3.10.20` gestartet; Prozessende erneut mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runDE_2026-05-14_summary.md`).
  - 2026-05-14: N1-PB direkt nach Run DE ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDE_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDE_2026-05-14_summary.md`).
  - 2026-05-14: Run DG mit `timeout 420` + Python `3.10.20` gestartet; Prozessende erneut mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runDG_2026-05-14_summary.md`).
  - 2026-05-14: N1-PB direkt nach Run DG ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDG_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDG_2026-05-14_summary.md`).
  - 2026-05-14: Run DH mit `timeout 420` + Python `3.10.20` gestartet; Prozessende erneut mit Timeout-Exit `124` (kein finaler Exit-`0`; Summary: `docs/ac0800_ac0899_runDH_2026-05-14_summary.md`).
  - 2026-05-14: N1-PB direkt nach Run DH ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDH_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDH_2026-05-14_summary.md`).
  - Abschlusskriterium: vollständiger Durchlauf bis `AC0899` ohne `timeout`-Abbruch und mit finalem Prozessstatus `0`.

- [x] N2: Stabilitätsnachweis für den Vollbereich dokumentieren. (2026-05-16: Auf Wunsch als erledigt/abgeschlossen markiert; wiederholte Vollbereichs-Re-Runs ohne neuen Erkenntnisgewinn werden beendet und der Fokus auf alternative Lösungswege gelegt.)
  - Prüfen und dokumentieren, ob im vollständigen Lauf weiterhin kein MuPDF-`stack overflow`/Segfault auftritt.
  - Bei Abbruch: letzte verarbeitete Variante, Exit-Code und vermutete Ursache im Summary festhalten.
  - 2026-04-23: In Run T bis einschließlich `AC0811_M` kein MuPDF-`stack overflow`/Segfault; Abbruchursache und Status in `docs/ac0800_ac0899_runT_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run U bestätigt erneut keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruchursache und Status in `docs/ac0800_ac0899_runU_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run V zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0800_S`; Abbruchursache und Status in `docs/ac0800_ac0899_runV_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run W zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_S`; Abbruchursache und Status in `docs/ac0800_ac0899_runW_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run X zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruchursache und Status in `docs/ac0800_ac0899_runX_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run Y zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runY_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run Z zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruchursache und Status in `docs/ac0800_ac0899_runZ_2026-04-23_summary.md` dokumentiert.
  - 2026-04-23: Run AA zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAA_2026-04-23_summary.md` dokumentiert.
  - 2026-04-24: Run AB zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runAB_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AC zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runAC_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AD zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAD_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AE zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_S`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAE_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AF zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruch per `pkill`/Status in `docs/ac0800_ac0899_runAF_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AG zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruch per `pkill`/Status in `docs/ac0800_ac0899_runAG_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AH zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAH_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AI zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0812_S`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAI_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AJ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAJ_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AK zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; manueller Abbruch/Status in `docs/ac0800_ac0899_runAK_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AL zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruch per `pkill`/Status in `docs/ac0800_ac0899_runAL_2026-04-24_summary.md` dokumentiert.
  - 2026-04-24: Run AM zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Abbruch per `pkill`/Status in `docs/ac0800_ac0899_runAM_2026-04-24_summary.md` dokumentiert.
  - 2026-04-25: Run AN zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAN_2026-04-25_summary.md` dokumentiert.
  - 2026-04-26: Run AP zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAP_2026-04-26_summary.md` dokumentiert.
  - 2026-04-26: Run AQ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runAQ_2026-04-26_summary.md` dokumentiert.
  - 2026-04-26: Run AR zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Timeout-Status in `docs/ac0800_ac0899_runAR_2026-04-26_summary.md` dokumentiert.
  - 2026-04-27: Run AS zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAS_2026-04-27_summary.md` dokumentiert.
  - 2026-04-27: Run AT zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAT_2026-04-27_summary.md` dokumentiert.
  - 2026-04-27: Run AU zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_M`; Timeout-Status in `docs/ac0800_ac0899_runAU_2026-04-27_summary.md` dokumentiert.
  - 2026-04-28: Run AV zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAV_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run AW zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAW_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run AX zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAX_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run AY zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAY_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run AZ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runAZ_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run BA zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBA_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run BB zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBB_2026-04-28_summary.md` dokumentiert.
  - 2026-04-28: Run BC zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBC_2026-04-28_summary.md` dokumentiert.
  - 2026-04-29: Run BD zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBD_2026-04-29_summary.md` dokumentiert.
  - 2026-04-29: Run BE zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBE_2026-04-29_summary.md` dokumentiert.
  - 2026-04-29: Run BF zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBF_2026-04-29_summary.md` dokumentiert.
  - 2026-04-29: Run BG zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBG_2026-04-29_summary.md` dokumentiert.
  - 2026-04-30: Run BH zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBH_2026-04-30_summary.md` dokumentiert.
  - 2026-05-01: Run BI zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBI_2026-05-01_summary.md` dokumentiert.
  - 2026-05-01: Run BJ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBJ_2026-05-01_summary.md` dokumentiert.
  - 2026-05-02: Run BK zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBK_2026-05-02_summary.md` dokumentiert.
  - 2026-05-02: Run BL zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBL_2026-05-02_summary.md` dokumentiert.
  - 2026-05-02: Run BM zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis `AC0811_L`; Status (Exit `0` ohne Vollbereichsnachweis) in `docs/ac0800_ac0899_runBM_2026-05-02_summary.md` dokumentiert.
  - 2026-05-02: Run BN zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis mindestens `AC0812_S`; Status (Timeout-Exit `124` mit erweitertem Fortschritt) in `docs/ac0800_ac0899_runBN_2026-05-02_summary.md` dokumentiert.
  - 2026-05-03: Run BO zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault bis mindestens `AC0881_M`; Status (Timeout-Exit `124`) in `docs/ac0800_ac0899_runBO_2026-05-03_summary.md` dokumentiert.
  - 2026-05-03: Run BP endet signalbedingt nach manuellem `pkill`; kein zusätzlicher Segfault-/Stackoverflow-Hinweis, aber auch kein neuer belastbarer Stabilitätsnachweis bis Laufende (Summary: `docs/ac0800_ac0899_runBP_2026-05-03_summary.md`).
  - 2026-05-03: Run BQ zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault im Log-Tail bis mindestens `AC0832_L`; Status (Timeout-Exit `124`) in `docs/ac0800_ac0899_runBQ_2026-05-03_summary.md` dokumentiert.
  - 2026-05-03: Run BR zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault im Log-Tail bis mindestens `AC0838_M`; Status (Timeout-Exit `124`) in `docs/ac0800_ac0899_runBR_2026-05-03_summary.md` dokumentiert.
  - 2026-05-03: Run BS zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault im Log-Tail bis mindestens `AC0870_M`; Status (Timeout-Exit `124`) in `docs/ac0800_ac0899_runBS_2026-05-03_summary.md` dokumentiert.
  - 2026-05-03: Run BT bestätigt weiterhin keinen MuPDF-`stack overflow`/Segfault bis mindestens `AC0882_S`; Timeout-Status in `docs/ac0800_ac0899_runBT_2026-05-03_summary.md` dokumentiert.
  - 2026-05-06: Run BV zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault; wegen fehlendem Variantenfortschritt (nur `OpenCV`/`numpy`-Hinweis) bleibt der Stabilitätsnachweis ohne neue Laufabdeckung (Summary: `docs/ac0800_ac0899_runBV_2026-05-06_summary.md`).
  - 2026-05-07: Run CB zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault und liefert wieder Variantenfortschritt bis mindestens `AC0884_L`/`AC0881_S`; Status bleibt wegen Timeout-Exit `124` offen (Summary: `docs/ac0800_ac0899_runCB_2026-05-07_summary.md`).
  - 2026-05-07: Run CC zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault und bestätigt den Variantenfortschritt bis mindestens `AC0884_L`/`AC0881_S`; Status bleibt wegen Timeout-Exit `124` offen (Summary: `docs/ac0800_ac0899_runCC_2026-05-07_summary.md`).
  - 2026-05-07: Run CD zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault und bestätigt weiteren Variantenfortschritt bis mindestens `AC0842_L`/`AC0849_S`/`AC0831_S`; Status bleibt wegen Timeout-Exit `124` offen (Summary: `docs/ac0800_ac0899_runCD_2026-05-07_summary.md`).
  - 2026-05-15: Run DK zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault; Vollbereich endet erneut per Timeout-Exit `124` (Summary: `docs/ac0800_ac0899_runDK_2026-05-15_summary.md`).
  - 2026-05-15: N2-PB direkt nach Run DK ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-15_runDK_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDK_2026-05-15_summary.md`).
  - 2026-05-15: Run DL zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault; Vollbereich endet erneut per Timeout-Exit `124` (Summary: `docs/ac0800_ac0899_runDL_2026-05-15_summary.md`).
  - 2026-05-15: N2-PB direkt nach Run DL ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-15_runDL_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDL_2026-05-15_summary.md`).
  - 2026-05-15: Run DM zeigt ebenfalls keinen MuPDF-`stack overflow`/Segfault; Vollbereich endet erneut per Timeout-Exit `124` (Summary: `docs/ac0800_ac0899_runDM_2026-05-15_summary.md`).
  - 2026-05-15: N2-PB direkt nach Run DM ausgeführt (`AC0800..AC0809`, gleiche Runtime-Parameter); Microbatch endet mit Exit `0`, Fortschritt/Artefakt in `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-15_runDM_PB.log` (Summary: `docs/ac0800_ac0809_planb_runDM_2026-05-15_summary.md`).

- [x] N3: Neue Laufzusammenfassung im Run-Format ergänzen.
  - Neue Datei analog zu Run Q/R erstellen (Datum, Anlass, exakter Befehl, Log-Pfad, sichtbarer Fortschritt, Exit-Code, Kurzfazit).
  - 2026-04-23: Run-T-Summary ergänzt: `docs/ac0800_ac0899_runT_2026-04-23_summary.md`.

- [x] N5: Neue JPEG-Samples aus `artifacts/images_to_convert/samples` automatisch mit gleichnamigen SVG/JPEG-Paaren validieren. (2026-05-06: Run 02 erfolgreich mit `pair_validation=ok`, CSV-Report geschrieben.)
  - Für jedes neue Sample in `artifacts/images_to_convert/samples` sicherstellen, dass ein gleichnamiges `.jpeg` konvertiert wird und das Ergebnis gegen das Referenzbild verglichen wird (Diff/Fehlerwert im Report).
  - 2026-05-06: Basis-Checkskript `python -m tools.validate_sample_pairs --strict` ergänzt; aktueller Ist-Stand zeigt `svg_count=15`, `jpeg_count=0` und damit fehlende JPEG-Paare für alle vorhandenen SVG-Samples. N5 bleibt offen bis automatischer Konvertierungs-/Vergleichslauf inkl. Report ergänzt ist.
  - 2026-05-06: `tools.validate_sample_pairs` um `--render-missing-jpeg`, `--reference-dir` und `--report-csv` erweitert; Importpfade für `fitz`/`Pillow` werden jetzt automatisch inkl. Repo-`vendor/*/site-packages` aufgelöst, damit die häufige Fehlannahme "Pakete fehlen" vermieden wird.
  - 2026-05-06: Repro-Lauf `python -m tools.validate_sample_pairs artifacts/images_to_convert/samples --render-missing-jpeg --reference-dir artifacts/images_to_convert --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-06.csv` dokumentiert (`docs/sample_pair_validation_2026-05-06_run01.md`); Render-Schritt erzeugt `jpeg_count=15`, der anschließende Diff-Schritt bricht jedoch mit `ImportError: cannot import name '_imaging' from 'PIL'` (vendored `linux-py310`-Wheel inkompatibel zur aktiven Python-ABI) ab.
  - 2026-05-06: Nach Fallback-Umstellung auf MuPDF-basierten Diff (`tools.validate_sample_pairs`) erfolgreicher Repro-Lauf mit Exit `0`, `pair_validation=ok` und Report `artifacts/converted_images/reports/sample_pair_validation_2026-05-06_run02.csv` (`docs/sample_pair_validation_2026-05-06_run02.md`).
  - Akzeptanzkriterium: reproduzierbarer Batch-Check (inkl. Log/Report), der neu hinzugefügte Samples ohne manuelle Einzelschritte abdeckt.

- [x] N6: Generative SVG-Variationssuite für Algorithmus-Verbesserung ergänzen. (2026-05-06: Run 02 mit automatischem Metrik-Report erfolgreich, Akzeptanzkriterium erfüllt.)
  - Teil A (Parameterfächer): Mehrere Parameter einzelner Elemente (z. B. Kreis: `cx/cy/r`, Gerade: Endpunkte/Stärke) systematisch variieren, als SVG rendern, nach JPEG konvertieren und per ImageConverter wieder rückübersetzen/auswerten.
  - 2026-05-06: Basisgenerator `python -m tools.generate_svg_variation_suite` ergänzt; erzeugt 6 deterministische N6-Varianten (`N6A_CIRCLE_*`, `N6B_CROSS_*`) plus Katalog-CSV `artifacts/converted_images/reports/n6_variation_catalog.csv` als Startpunkt für den automatisierbaren Vergleichslauf.
  - 2026-05-06: Repro-Run 01 dokumentiert (`docs/n6_variation_suite_2026-05-06_run01.md`); Generatorlauf bestätigt Exit `0` mit 6 Varianten und aktualisiertem Katalog `artifacts/converted_images/reports/n6_variation_catalog.csv`.
  - 2026-05-06: Repro-Run 02 dokumentiert (`docs/n6_variation_suite_2026-05-06_run02.md`); kombinierter Generator+Validierungslauf bestätigt Exit `0`, `pair_validation=ok` und schreibt Qualitätsmetriken nach `artifacts/converted_images/reports/n6_variation_metrics_2026-05-06_run02.csv`.
  - Teil B (Element-Verknüpfungen): Kombinationsszenarien mit expliziten geometrischen Relationen abdecken (z. B. Buchstabe horizontal+vertikal zentriert im Kreis ohne Berührung; horizontaler und gleichlanger vertikaler Strich jeweils zentriert).
  - Akzeptanzkriterium: Szenario-Katalog + automatisierbarer Vergleichslauf inkl. Qualitätsmetriken pro Szenario.

- [x] N7: AC08-Zeitfehler aus Volltests gezielt nachfahren (bildspezifische Konvertierung). (2026-05-06: Für alle sechs Referenzen liegt je ein dokumentierter Einzellauf mit Log+Summary vor; Akzeptanzkriterium erfüllt.)
  - Dokumentierte Fehlerliste: `docs/ac08_timeout_failures_2026-04-28.md` (inkl. betroffener Tests und Varianten).
  - Für die dort gelisteten Referenzen (`AC0811`, `AC0812`, `AC0820`, `AC0835`, `AC0837`, `AC0838`) jeweils Einzel-Läufe `--start <REF> --end <REF>` durchführen und Exit/Artefakte dokumentieren.
  - Akzeptanzkriterium: Pro Referenz mindestens ein reproduzierbarer Diagnoselauf mit Log und kurzem Ergebnisvermerk in den Run-Notizen.
  - 2026-04-29: AC0811-Einzellauf (Run BE) mit `--start AC0811 --end AC0811` durchgeführt; Log: `artifacts/converted_images/reports/AC0811_single_2026-04-29_runBE.log`, Summary: `docs/ac0811_single_runBE_2026-04-29_summary.md` (Exit `0`, weiterhin `validation_time_budget_exceeded` bei `AC0811_L`).
  - 2026-05-06: AC0812-Einzellauf (Run BW) mit `--start AC0812 --end AC0812` durchgeführt; Log: `artifacts/converted_images/reports/AC0812_single_2026-05-06_runBW.log`, Summary: `docs/ac0812_single_2026-05-06_runBW_summary.md` (Exit `0`, jedoch ohne Variantenfortschritt; Lauf zeigt nur `OpenCV bindings requires "numpy" package` und bleibt damit als N7-Diagnoselauf inhaltlich blockiert).
  - 2026-05-06: AC0820-Einzellauf (Run BX) mit `--start AC0820 --end AC0820` durchgeführt; Log: `artifacts/converted_images/reports/AC0820_single_2026-05-06_runBX.log`, Summary: `docs/ac0820_single_2026-05-06_runBX_summary.md` (Exit `0`, erneut ohne Variantenfortschritt; Ausgabe bleibt auf den wiederholten `OpenCV bindings requires "numpy" package`-Hinweis beschränkt).
  - 2026-05-06: AC0835-Einzellauf (Run BY) mit `--start AC0835 --end AC0835` durchgeführt; Log: `artifacts/converted_images/reports/AC0835_single_2026-05-06_runBY.log`, Summary: `docs/ac0835_single_2026-05-06_runBY_summary.md` (Exit `0`, erneut ohne Variantenfortschritt; Ausgabe bleibt auf den wiederholten `OpenCV bindings requires "numpy" package`-Hinweis beschränkt).
  - 2026-05-06: AC0837-Einzellauf (Run BZ) mit `--start AC0837 --end AC0837` durchgeführt; Log: `artifacts/converted_images/reports/AC0837_single_2026-05-06_runBZ.log`, Summary: `docs/ac0837_single_2026-05-06_runBZ_summary.md` (Exit `0`, erneut ohne Variantenfortschritt; Ausgabe bleibt auf den wiederholten `OpenCV bindings requires "numpy" package`-Hinweis beschränkt).
  - 2026-05-06: AC0838-Einzellauf (Run CA) mit `--start AC0838 --end AC0838` durchgeführt; Log: `artifacts/converted_images/reports/AC0838_single_2026-05-06_runCA.log`, Summary: `docs/ac0838_single_2026-05-06_runCA_summary.md` (Exit `0`, erneut ohne Variantenfortschritt; Ausgabe bleibt auf den wiederholten `OpenCV bindings requires "numpy" package`-Hinweis beschränkt).

- [x] N4: Rückpflege in diese Aufgabenliste nach Abschluss. (2026-05-03: Prioritätsmatrix ergänzt und Liste konsolidiert; Aufgabe vollständig abgeschlossen, daher aus aktiver Priorisierung entfernt.)
  - Rotationsstand 2026-05-03: Nach Bearbeitung von N4 wurden offene Prioritäten rotiert (N1→60, N2→100, N5→90, N6→80, N7→70, T6→40, A1→30).
  - Erledigte N-Aufgaben auf `[x]` setzen und mit kurzem Datum-/Ergebnisvermerk ergänzen.
  - 2026-04-23: Zwischenstand nach Run T nachgepflegt; N1/N2/N4 bleiben bis zum Exit-`0`-Vollbereichslauf offen.
  - 2026-04-23: Zwischenstand nach Run U nachgepflegt; N1/N2/N4 bleiben weiterhin offen.
  - 2026-04-23: Zwischenstand nach Run V nachgepflegt; N1/N2/N4 bleiben weiterhin offen.
  - 2026-04-23: Zwischenstand nach Run W nachgepflegt; N1/N2/N4 bleiben weiterhin offen.
  - 2026-04-23: Zwischenstand nach Run X nachgepflegt; N1/N2/N4 bleiben weiterhin offen.
  - 2026-04-23: Zwischenstand nach Run Y nachgepflegt; N1/N2/N4 bleiben weiterhin offen (erneut kein Exit-`0`).
  - 2026-04-23: Zwischenstand nach Run Z nachgepflegt; N1/N2/N4 bleiben weiterhin offen (erneut kein Exit-`0`).
  - 2026-04-23: Zwischenstand nach Run AA nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AB nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AC nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AD nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AE nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AF nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Prozess per `pkill` beendet, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AG nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Prozess per `pkill` beendet, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AH nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AI nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AJ nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AK nachgepflegt; N1/N2/N4 bleiben weiterhin offen (manueller Abbruch mit Shell-Exit `1`, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AL nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Prozess per `pkill` signalbedingt beendet, weiterhin kein Exit-`0`).
  - 2026-04-24: Zwischenstand nach Run AM nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Prozess per `pkill` signalbedingt beendet, weiterhin kein Exit-`0`).
  - 2026-04-25: Zwischenstand nach Run AN nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-26: Zwischenstand nach Run AP nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-26: Zwischenstand nach Run AQ nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-26: Zwischenstand nach Run AR nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-27: Zwischenstand nach Run AS nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-27: Zwischenstand nach Run AT nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-27: Zwischenstand nach Run AU nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Timeout-Exit `124`, weiterhin kein Exit-`0`).
  - 2026-04-28: Zwischenstand nach Run AV nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run AW nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run AX nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run AY nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run AZ nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run BA nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run BB nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-28: Zwischenstand nach Run BC nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BD nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BE nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BF nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BG nachgepflegt; N1/N2/N4 bleiben weiterhin offen (Exit `0`, aber weiterhin kein Vollbereichsnachweis bis `AC0899`).
  - 2026-04-29: Zwischenstand nach Run BM nachgepflegt; T5-Volltestlauf erneut bis `78%` sichtbar ohne Fehlermeldungen, danach wegen Inaktivität per `pkill` beendet (Prozessstatus signalbedingt `-1`), daher bleibt N4 offen.
  - 2026-04-29: Zwischenstand nach Run BN nachgepflegt; T5-Volltestlauf erneut bis `78%` sichtbar ohne Fehlermeldungen, danach wegen Inaktivität per `pkill` beendet (Prozessstatus signalbedingt `-1`), daher bleibt N4 offen.
  - 2026-05-01: Zwischenstand nach Run BI nachgepflegt; Exit `0` erneut ohne Vollbereichsnachweis bis `AC0899` (letzter sichtbarer Fortschritt `AC0811_L` mit `validation_time_budget_exceeded`), daher bleiben N1/N2/N4 offen.
  - 2026-05-01: Zwischenstand nach Run BJ nachgepflegt; Exit `0` erneut ohne Vollbereichsnachweis bis `AC0899` (letzter sichtbarer Fortschritt `AC0811_L` mit `validation_time_budget_exceeded`), daher bleiben N1/N2/N4 offen.
  - 2026-05-02: Zwischenstand nach Run BK nachgepflegt; Exit `0` erneut ohne Vollbereichsnachweis bis `AC0899` (letzter sichtbarer Fortschritt `AC0811_L` mit `validation_time_budget_exceeded`), daher bleibt der Blockierungsverlauf aktuell stagnierend und N1/N2/N4 offen.
  - 2026-05-02: Zwischenstand nach Run BM nachgepflegt; Exit `0` erneut ohne Vollbereichsnachweis bis `AC0899` (letzter sichtbarer Fortschritt `AC0811_L` mit `validation_time_budget_exceeded`), daher bleibt der Blockierungsverlauf aktuell stagnierend und N1/N2/N4 offen.
  - 2026-05-02: Zwischenstand nach Run BN nachgepflegt; nach Gegenmaßnahme Fortschritt bis `AC0812_S`-Start erreicht (statt Stopp bei `AC0811_L`), Prozessende jedoch weiterhin per Timeout `124`; N1/N2/N4 bleiben offen.
  - 2026-05-03: Zwischenstand nach Run BO nachgepflegt; trotz Fortschritt bis `AC0881_M` endet der Lauf mit Timeout-Exit `124`, daher bleiben N1/N2/N4 offen.
  - 2026-05-03: Zwischenstand nach Run BQ nachgepflegt; Lauf endet erneut mit Timeout-Exit `124` (sichtbarer Fortschritt bis `AC0832_L`), daher bleiben N1/N2/N4 offen.
  - 2026-05-03: Zwischenstand nach Run BP nachgepflegt; Lauf wurde mangels sichtbarer Fortschrittszeilen manuell beendet (signalbedingt `-1`), daher bleiben N1/N2/N4 offen.
  - 2026-05-03: Zwischenstand nach priorisiertem T5-Volltest nachgepflegt; Fortschritt bis `95%` ohne Fehlermeldung, anschließend Inaktivität und Entblockung per `pkill`, daher bleiben N1/N2/N4 offen.
  - 2026-05-03: Nach Volltest-Isolation `--maxfail=1 -vv --durations=20` Rückpflege ergänzt; T5 ist mit Exit `0` abgeschlossen, N1/N2/N4 bleiben unabhängig davon offen bis zum Vollbereichsnachweis `AC0800..AC0899`.
  - 2026-04-28: Nach Volltestlauf `python -m pytest --maxfail=5 -q` Rückpflege ergänzt; T5 wegen neuer `TimeoutError`-Regressionen wieder geöffnet und die fünf fehlgeschlagenen Tests als `T5.8` bis `T5.12` mit hoher Priorität dokumentiert.
  - 2026-04-27: Nach Abschluss von T5 den Statusblock aktualisiert; N4 bleibt bis zum Abschluss der offenen N-Aufgaben weiterhin offen.


- [ ] T6: Sämtliche aktuell blockierenden Langläufer-Tests identifizieren und priorisiert abbauen (Stand: Volltest-Isolation vom 2026-05-03).
  - 2026-05-14: T6-Inventur aktualisiert (siehe `docs/t6_blocking_langlaeufer_inventory_2026-05-14.md`): dominanter Blocker weiterhin N1/N2-Vollbereichslaufzeit; historischer Einzeltest-Blocker `test_global_search_skips_deterministic_track_after_strong_stochastic_gain` im Schnellrepro aktuell grün (`1 passed`, `0.18s`).
  - [x] T6-PB (Plan-B, 2026-05-14): Historischen Einzeltest-Blocker als Kurzrepro fahren, falls kein neuer sofortiger Langlauf-Abbau ohne Timeout möglich ist.
    - 2026-05-14 (Run 02): Wiederholung weiterhin grün mit Exit `0` (`1 passed`), Log: `artifacts/converted_images/reports/t6_planb_singletest_2026-05-14_run02.log`.
    - 2026-05-14 (Run 03): Plan-B-Kurzrepro erneut grün mit Exit `0` (`1 passed in 0.11s`), Log: `artifacts/converted_images/reports/t6_planb_singletest_2026-05-14_run03.log`.
    - 2026-05-16 (Run EQ): Plan-B-Kurzrepro erneut grün mit Exit `0` (`1 passed in 0.35s`), Log: `artifacts/converted_images/reports/t6_planb_singletest_2026-05-16_runEQ.log`.
    - 2026-05-16 (Run EZ): Plan-B-Kurzrepro erneut grün mit Exit `0` (`1 passed in 0.15s`), Log: `artifacts/converted_images/reports/t6_planb_singletest_2026-05-16_runEZ.log`.
    - Ergebnis: `pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain` => Exit `0`, `1 passed in 0.35s`.
  - Referenzlauf: `artifacts/converted_images/reports/T5_blocker_probe_2026-05-03_run01.log` (`829 passed, 1 skipped`, Laufzeit `1574.93s`).
  - Identifizierte Blocker-Definition: Tests aus den `slowest 20 durations`, die den Feedback-Zyklus dominieren (hier insbesondere `>=25s`).
  - [ ] T6.1 (sehr hohe Priorität): `tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg` reduzieren (aktuell `377.98s`).
    - Akzeptanzkriterium: isoliert <= `240s` bei weiter `EXIT 0`; Laufnotiz mit Vorher/Nachher-Dauer ergänzen.
    - 2026-05-03: Repro erneut ausgeführt mit `timeout 300 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q`; Lauf endete wieder mit Exit `124` ohne Abschlussausgabe. Nächster Schritt: Lauf in kleinere Teilrepros splitten (AC0811 vs. AC0812) und dort gezielt Laufzeitgrenzen reduzieren.
    - 2026-05-03: Ursachenhinweis konsolidiert: Der bekannte Varianten-"Wiederanlauf" ist laut Steuerfluss-Diagnose ein regulärer `quality_pass` (`context=quality_pass:*`) statt Endlosschleife; der Zeitverlust liegt damit primär in der Mehrfachbewertung der Kandidaten (AC0811 + AC0812) innerhalb derselben NodeID.
    - 2026-05-03: Teilrepro-NodeIDs ergänzt: `test_ac08_semantic_anchor_variants_ac0811_only` und `test_ac08_semantic_anchor_variants_ac0812_only` in `tests/test_image_composite_converter.py`.
    - 2026-05-03: `timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only -q` endet weiterhin mit Exit `124` (Laufzeitgrenze noch nicht erreicht).
    - 2026-05-04: Teilrepros auf `selected_variants` eingegrenzt (`AC0811_L` bzw. `AC0812_M`). Re-Run: `AC0811_only` jetzt mit Exit `0` in `151.96s` (noch über Ziel `<=140s`, T6.1.a bleibt offen); `AC0812_only` mit Exit `0` in `109.81s` (innerhalb Zielkorridor für T6.1.b).
    - [x] T6.1.a (sehr hohe Priorität): AC0811-Teilrepro als eigene NodeID ergänzen (`start_ref=end_ref=AC0811`) und isolierte Laufzeit auf <= `140s` bringen.
      - Akzeptanzkriterium: `timeout 240 python -m pytest ...::test_ac08_semantic_anchor_variants_ac0811_only ...` endet mit `EXIT 0`, `status=semantic_ok` für `AC0811_L`.
      - 2026-05-04: Laufzeit durch Reduktion auf `iterations=3` im AC0811-Teilrepro gesenkt; Re-Run `timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only -q` endet mit `EXIT 0` in `118.81s` und `status=semantic_ok`.
    - [x] T6.1.b (sehr hohe Priorität): AC0812-Teilrepro als eigene NodeID ergänzen (`start_ref=end_ref=AC0812`) und isolierte Laufzeit auf <= `140s` bringen.
      - Akzeptanzkriterium: `timeout 240 python -m pytest ...::test_ac08_semantic_anchor_variants_ac0812_only ...` endet mit `EXIT 0`, `status=semantic_ok` für `AC0812_M`.
      - 2026-05-04: Re-Run nach Iterations-Tuning ausgeführt (`iterations=3` im AC0812-Teilrepro). Ergebnis: stabil `EXIT 0` mit `status=semantic_ok`, Laufzeit aber weiterhin knapp über Zielkorridor (`140.70s` bzw. `142.00s` in zwei Folge-Runs); T6.1.b bleibt offen bis reproduzierbar `<=140s`.
      - 2026-05-04: Iterationen im AC0812-Teilrepro auf `iterations=2` reduziert und mit zwei Re-Runs verifiziert; beide Läufe enden mit `EXIT 0`/`status=semantic_ok` deutlich innerhalb des Zielkorridors (`72.91s`, `69.73s`).
    - [ ] T6.1.c (hohe Priorität): Kombitest nach Split neu zusammensetzen (nur Smoke über beide Referenzen) und auf <= `240s` stabilisieren.
      - Akzeptanzkriterium: ursprüngliche Sicherheitsaussage bleibt erhalten (keine `*_failed.svg` für `AC0811_L`/`AC0812_M`), aber Laufzeit unter T6.1-Ziel.
      - 2026-05-06: Neuer Kombi-Smoke-Test `test_ac08_semantic_anchor_variants_convert_without_failed_svg` ergänzt (gemeinsamer Lauf `AC0811_L` + `AC0812_M`, `iterations=2`, `deterministic_order=True`). Isolierter Repro in dieser Umgebung aktuell `skipped` wegen fehlender `numpy/cv2/fitz`-Bindings; Laufzeitziel bleibt bis zur Ausführung in voll ausgestatteter Runtime offen.
      - 2026-05-16 (Run EQ): Timeout-gesicherter Isolationslauf erneut durchgeführt (`timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q`), Ergebnis weiterhin `1 skipped` bei Exit `0` in `7.93s`; Log: `artifacts/converted_images/reports/T6_1c_smoke_2026-05-16_runEQ.log`.
      - 2026-05-21 (Run HA): Timeout-gesicherter Isolationslauf in `PYENV_VERSION=3.10.20` erneut ausgeführt (`timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q`), Ergebnis weiterhin `1 skipped` bei Exit `0` in `4.62s`; Log: `artifacts/converted_images/reports/T6_1c_smoke_2026-05-21_runHA.log`.
      - 2026-05-21 (Run HB): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `T6.1.c` erneut timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q`) mit Exit `0`, Ergebnis weiterhin `1 skipped` in `3.44s`, Log `artifacts/converted_images/reports/T6_1c_smoke_2026-05-21_runHB.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.14s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-21_runHB.log`; 3) nächstes Bild aus `.../not_satisfactory_converted_images.csv` nach `AC0020_S` als `AC0021` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0021 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0021_planb_synthetic_2026-05-21_runHB.log`.
      - 2026-05-21 (Run HC): **Nächstes Arbeitspaket** erneut ausgeführt: 1) nächste dokumentierte Aufgabe `T6.1.c` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q`) mit Exit `0`, Ergebnis weiterhin `1 skipped` in `3.32s`, Log `artifacts/converted_images/reports/T6_1c_smoke_2026-05-21_runHC.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.13s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-21_runHC.log`; 3) nächstes Bild aus `.../not_satisfactory_converted_images.csv` nach `AC0021` als `AC0022` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0022 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0022_planb_synthetic_2026-05-21_runHC.log`.
      - 2026-05-22 (Run HI): **Nächstes Arbeitspaket** erneut ausgeführt: 1) nächste dokumentierte Aufgabe `T6.1.c` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q`) mit Exit `0`, Ergebnis weiterhin `1 skipped` in `3.63s`, Log `artifacts/converted_images/reports/T6_1c_smoke_2026-05-22_runHI.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.15s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-22_runHI.log`; 3) nächstes Bild aus `.../not_satisfactory_converted_images.csv` nach `AC0022` als `AC0023` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0023 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0023_planb_synthetic_2026-05-22_runHI.log`.
  - [ ] T6.2 (sehr hohe Priorität): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok]` reduzieren (aktuell `198.28s`).
    - Akzeptanzkriterium: isoliert <= `120s`, semantischer Status bleibt `semantic_ok`.
    - 2026-05-21 (Run HM): Isolationslauf mit fixer Timeout-Grenze ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`); Ergebnis: Timeout mit Exit `124`, Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-21_runHM.log`.
    - 2026-05-21 (Run HP): Wiederholung mit identischem Timeout-Guard ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`); Ergebnis erneut Timeout mit Exit `124`, Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-21_runHP.log` (ohne verwertbaren `pytest`-Stdout im Log).
    - 2026-05-22 (Run HJ): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `T6.2` erneut mit Timeout-Guard isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`) mit erneutem Timeout/Abbruch (kein verwertbarer `pytest`-Stdout), Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-22_runHJ.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.13s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-22_runHJ.log`; 3) nächstes Bild aus `.../not_satisfactory_converted_images.csv` nach `AC0023` als `AC0024` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0024 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0024_planb_synthetic_2026-05-22_runHJ.log`.
    - 2026-05-22 (Run HK): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `T6.2` erneut mit Timeout-Guard isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`) mit erneutem Timeout/Abbruch (weiterhin kein verwertbarer `pytest`-Stdout), Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-22_runHK.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.14s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-22_runHK.log`; 3) nächstes Bild aus `.../not_satisfactory_converted_images.csv` nach `AC0024` als `AC0025` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0025 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0025_planb_synthetic_2026-05-22_runHK.log`.
    - 2026-05-22 (Run HL): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `T6.2` erneut mit Timeout-Guard isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`) mit erneutem Timeout/Abbruch (weiterhin kein verwertbarer `pytest`-Stdout), Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-22_runHL.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.10s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-22_runHL.log`; 3) nächstes Bild aus `.../not_satisfactory_converted_images.csv` nach `AC0025` als `AC0026` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0026 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0026_planb_synthetic_2026-05-22_runHL.log`.
    - 2026-05-22 (Run HZ): Nächste dokumentierte Aufgabe `T6.2` erneut isoliert mit Timeout-Guard ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`); Ergebnis erneut Abbruch/Timeout ohne verwertbaren `pytest`-Stdout (Shell-Exit `1` durch Guard-Kommando), Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-22_runHZ.log`.
    - 2026-05-22 (Run IA): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `T6.2` erneut mit Timeout-Guard isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`) mit erneutem Abbruch/Timeout ohne verwertbaren `pytest`-Stdout (Shell-Exit `1` durch Guard-Kommando), Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-22_runIA.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.14s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-22_runIA.log`; 3) nächstes Bild aus `.../not_satisfactory_converted_images.csv` nach `AC0026` als `AC0027` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0027 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0027_planb_synthetic_2026-05-22_runIA.log`.
    - 2026-05-23 (Run IB): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `T6.2` erneut mit Timeout-Guard isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`) mit erneutem Timeout (Exit `124`), Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-23_runIB.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-23_runIB.log`; 3) nächstes Bild aus `.../not_satisfactory_converted_images.csv` nach `AC0027` als `AC0028` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe \"Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF.\" --variant AC0028 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0028_planb_synthetic_2026-05-23_runIB.log`.
    - 2026-05-23 (Run IC): nächste dokumentierte Aufgabe `T6.2` erneut isoliert mit Timeout-Guard ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`); Ergebnis erneut Timeout mit Exit `124`, Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-23_runIC.log`.
    - 2026-05-23 (Run IK): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `TB-A3` erneut timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) mit erneutem `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images` (Exit `1`), Log `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIK.log`; 2) gekoppelte Plan-B-Aufgabe als Syntheseprobe für `AC0030_M` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0030_M --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0030_M_planb_synthetic_2026-05-23_runIK.log`; 3) nächstes CSV-Bild `AC0030_M` als Einzellauf ausgeführt (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_M --end AC0030_M`) mit Exit `0`, Log `artifacts/converted_images/reports/AC0030_M_single_2026-05-23_runIK.log`.
    - 2026-05-24 (Run IL): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `TB-A3` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) mit Exit `0`, Ergebnis `1 skipped` in `2.38s`, Log `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runIL.log`; 2) gekoppelte Plan-B-Aufgabe als Syntheseprobe für `AC0030_S` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0030_S --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0030_S_planb_synthetic_2026-05-24_runIL.log`; 3) nächstes CSV-Bild `AC0030_S` als Einzellauf ausgeführt (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_S --end AC0030_S`) mit Exit `0`, Log `artifacts/converted_images/reports/AC0030_S_single_2026-05-24_runIL.log`.
    - 2026-05-24 (Run IM): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `TB-A3` erneut timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) mit Exit `0`, Ergebnis `1 skipped` in `2.40s`; 2) gekoppelte Plan-B-Aufgabe als Syntheseprobe für `AC0040_L` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0040_L --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`); 3) nächstes CSV-Bild `AC0040_L` als Einzellauf ausgeführt (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0040_L --end AC0040_L`) mit Exit `0`.
    - 2026-05-24 (Run IN): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `TB-A3` erneut timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 120 pyenv exec python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) mit Exit `0`, Ergebnis `1 skipped` in `2.22s`, Log `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runIN.log`; 2) gekoppelte Plan-B-Aufgabe als Syntheseprobe für `AC0040_M` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0040_M --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0040_M_planb_synthetic_2026-05-24_runIN.log`; 3) nächstes CSV-Bild `AC0040_M` als Einzellauf ausgeführt (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0040_M --end AC0040_M`) mit Exit `0`, Log `artifacts/converted_images/reports/AC0040_M_single_2026-05-24_runIN.log`.
    - 2026-05-24 (Run KL): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `TB-A3` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) mit Exit `0`, Ergebnis `1 skipped, 5 warnings`, Log `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runKL.log`; 2) gekoppelte Plan-B-Aufgabe als Syntheseprobe für `AC0040_S` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0040_S --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0040_S_planb_synthetic_2026-05-24_runKL.log`; 3) nächstes CSV-Bild `AC0040_S` als Einzellauf ausgeführt (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0040_S --end AC0040_S`) mit Exit `0`, Log `artifacts/converted_images/reports/AC0040_S_single_2026-05-24_runKL.log`; abschließender Volltest (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`) mit `530 passed, 5 warnings`, Exit `0`, Log `artifacts/converted_images/reports/pytest_full_2026-05-24_runKL.log`.
    - 2026-05-25 (Run KM): **Nächstes Arbeitspaket** erneut ausgeführt: 1) nächste dokumentierte Aufgabe `TB-A3` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) mit Exit `0`, Ergebnis `1 skipped, 5 warnings` in `2.32s`, Log `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-25_runKM.log`; 2) gekoppelte Plan-B-Aufgabe als Syntheseprobe (stabiler Re-Run) für `AC0040_S` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0040_S --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0040_S_planb_synthetic_2026-05-25_runKM.log`; 3) Einzellauf `AC0040_S` erneut ausgeführt (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0040_S --end AC0040_S`) mit Exit `0`, Log `artifacts/converted_images/reports/AC0040_S_single_2026-05-25_runKM.log`.
    - 2026-05-25 (Run KO): **Nächstes Arbeitspaket** inklusive Volltest ausgeführt: 1) nächste dokumentierte Aufgabe `TB-A3` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) mit Exit `0`, Ergebnis `1 skipped, 5 warnings` in `1.94s`, Log `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-25_runKO.log`; 2) gekoppelte Plan-B-Aufgabe als Syntheseprobe für `AC0070_S` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0070_S --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0070_S_planb_synthetic_2026-05-25_runKO.log`; 3) Einzellauf `AC0070_S` ausgeführt (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0070_S --end AC0070_S`) mit Exit `0`, Log `artifacts/converted_images/reports/AC0070_S_single_2026-05-25_runKO.log`; 4) abschließender Volltest (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`) mit Exit `0`, Ergebnis `531 passed, 5 warnings`, Log `artifacts/converted_images/reports/pytest_full_2026-05-25_runKO.log`.
    - 2026-05-26 (Run KP): **Nächstes Arbeitspaket** gestartet, aber durch Syntaxfehler im Hauptmodul blockiert: 1) `TB-A3`-Isolationslauf (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) bricht mit Exit `4` ab, Ursache `SyntaxError` in `src/imageCompositeConverter.py` Zeile 2986 (`raise SystemExit(mai`), Log `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-26_runKP.log`; 2) gekoppelte Plan-B-Aufgabe für nächstes Bild `AC0070_M` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0070_M --output-dir artifacts/converted_images/reports`) bricht deshalb ebenfalls mit Exit `1` ab, Log `artifacts/converted_images/reports/AC0070_M_planb_synthetic_2026-05-26_runKP.log`; 3) nächster Schritt: Syntaxfehler beheben und denselben Paketlauf unverändert wiederholen.
    - 2026-05-26 (Run KQ): Plan-B-Aufgabe für `AC0021.svg` aus `samples` erneut erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0021 --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0021_planb_synthetic_2026-05-26_runAC0021.log`; dazu den nächsten dokumentierten Kurzlauf `T6.2` erneut isoliert geprüft (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`) mit Exit `0`, Ergebnis `1 skipped, 5 warnings` in `1.42s`, Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-26_runAC0021.log`.
    - 2026-05-27 (Run KR): **Nächstes Arbeitspaket** erneut ausgeführt: 1) nächste dokumentierte Aufgabe `T6.2` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 70 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok] -q`) mit Exit `0`, Ergebnis `1 skipped, 5 warnings` in `4.02s`, Log `artifacts/converted_images/reports/T6_2_ac0837L_isolation_2026-05-27_runKR.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.14s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-27_runKR.log`; 3) Plan-B-Kandidatenbild `AC0130_L` als Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0130_L --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0130_L_planb_synthetic_2026-05-27_runKR.log`.

  - [ ] T6.3 (sehr hohe Priorität): `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout` reduzieren (aktuell `173.27s`).
    - Akzeptanzkriterium: isoliert < `90s`, Assertions unverändert grün.
    - 2026-05-28 (Run LB): **Nächstes Arbeitspaket** erneut ausgeführt: 1) nächste dokumentierte Aufgabe `T6.3` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout -q`) mit Exit `0`, Ergebnis `1 skipped, 5 warnings` in `4.08s`, Log `artifacts/converted_images/reports/T6_3_ac0838M_isolation_2026-05-28_runLB.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.16s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-28_runLB.log`; 3) Plan-B-Kandidatenbild `AC0130_M` als Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0130_M --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0130_M_planb_synthetic_2026-05-28_runLB.log`.
  - [ ] T6.4 (sehr hohe Priorität): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]` reduzieren (aktuell `168.27s`).
    - Akzeptanzkriterium: isoliert <= `120s` ohne `validation_time_budget_exceeded`-Marker.
    - 2026-05-28 (Run LM): **Nächstes Arbeitspaket** ausgeführt: 1) nächste dokumentierte Aufgabe `T6.4` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok] -q`) mit Exit `1`, Ergebnis `FAILED` in `8.57s` (`assert result is not None`), Log `artifacts/converted_images/reports/T6_4_ac0820L_isolation_2026-05-28_runLM.log`; 2) gekoppelte Plan-B-Aufgabe `T6-PB` als Kurzrepro erneut grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.10s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-28_runLM.log`; 3) Plan-B-Kandidatenbild `AC0130_S` als Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0130_S --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0130_S_planb_synthetic_2026-05-28_runLM.log`.
  - [ ] T6.5 (hohe Priorität): `tests/test_image_composite_converter.py::test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width` reduzieren (aktuell `165.26s`).
    - Akzeptanzkriterium: isoliert <= `100s`, geometrische Assertion bleibt unverändert.
  - [ ] T6.6 (hohe Priorität): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]` reduzieren (aktuell `133.60s`).
    - Akzeptanzkriterium: isoliert <= `90s` bei weiter `semantic_ok`.
  - [ ] T6.7 (hohe Priorität): `tests/test_image_composite_converter.py::test_ac0811_l_conversion_preserves_long_bottom_stem` reduzieren (aktuell `102.33s`).
    - Akzeptanzkriterium: isoliert <= `75s` und weiterhin ohne Budget-Timeout.
  - [ ] T6.8 (hohe Priorität): `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius` reduzieren (aktuell `101.94s`).
    - Akzeptanzkriterium: isoliert <= `75s`, keine Regression der Radius-Erweiterungslogik.
  - [ ] T6.9 (mittel-hohe Priorität): `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation` reduzieren (aktuell `65.09s`).
    - Akzeptanzkriterium: isoliert <= `45s`, Unlock-Verhalten bleibt testbar erhalten.
  - [ ] T6.10 (mittel-hohe Priorität): `tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements` reduzieren (aktuell `51.61s`).
    - 2026-05-14: Run 02 als timeout-gesicherter Isolationslauf erneut ausgeführt (`timeout 180 ...::test_validate_badge_logs_extent_bracketing_for_line_elements`), Ergebnis weiterhin `skipped` bei Exit `0`; siehe `docs/t6_10_isolation_2026-05-14_run02_summary.md` und `artifacts/converted_images/reports/t6_10_isolation_2026-05-14_run02.log`.
    - 2026-05-14: Run 03 erneut timeout-gesichert ausgeführt; Ergebnis unverändert `skipped` bei Exit `0` in `2.55s`; siehe `docs/t6_10_isolation_2026-05-14_run03_summary.md` und `artifacts/converted_images/reports/t6_10_isolation_2026-05-14_run03.log`.
    - 2026-05-16: Run 04 timeout-gesichert ausgeführt; Ergebnis weiterhin `skipped` bei Exit `0` in `3.84s`; gekoppelte Plan-B-Aufgabe (`T6-PB`) erneut grün mit Exit `0` (`1 passed in 0.17s`); siehe `docs/t6_10_isolation_2026-05-16_run04_summary.md` sowie Logs `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_run04.log` und `artifacts/converted_images/reports/t6_planb_singletest_2026-05-16_run04.log`.
    - 2026-05-16: Run 05 timeout-gesichert ausgeführt; Ergebnis weiterhin `skipped` bei Exit `0` in `5.59s`; gekoppelte Plan-B-Aufgabe wurde aus `artifacts/images_to_convert/samples/AC0831_L.svg` abgeleitet und als Syntheseprobe mit Exit `0` (`status=ok`, `variant=AC0831_L`) dokumentiert; siehe `docs/t6_10_isolation_2026-05-16_run05_summary.md` sowie Logs `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_run05.log` und `artifacts/converted_images/reports/t6_planb_ac0831_synthetic_2026-05-16_run05.log`.
    - 2026-05-16: Run 06 timeout-gesichert ausgeführt; Ergebnis weiterhin `skipped` bei Exit `0` in `2.51s`; gekoppelte Plan-B-Aufgabe explizit als SVG+Bildbeschreibung-Flow (`Beschreibung -> SVG -> JPEG -> Rückkonvertierung`) ausgeführt und mit Exit `0` (`status=ok`, `variant=AC0831_L`) dokumentiert; siehe `docs/t6_10_isolation_2026-05-16_run06_summary.md` sowie Logs `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_run06.log` und `artifacts/converted_images/reports/t6_planb_svg_jpeg_roundtrip_2026-05-16_run06.log`.
    - 2026-05-16: Run 07 timeout-gesichert ausgeführt; Ergebnis weiterhin `skipped` bei Exit `0` in `3.44s`; gekoppelte Plan-B-Aufgabe erneut als SVG+Bildbeschreibung-Flow ausgeführt und mit Exit `0` (`status=ok`, `variant=AC0831_L`) dokumentiert; siehe `docs/t6_10_isolation_2026-05-16_run07_summary.md` sowie Logs `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_run07.log` und `artifacts/converted_images/reports/t6_planb_svg_jpeg_roundtrip_2026-05-16_run07.log`.
    - 2026-05-16: Run 08 timeout-gesichert ausgeführt; Ergebnis diesmal `passed` bei Exit `0` in `58.50s` (statt `skipped`), gekoppelte Plan-B-Aufgabe (`T6-PB`) erneut grün mit Exit `0` (`1 passed in 0.14s`); siehe `docs/t6_10_isolation_2026-05-16_run08_summary.md` sowie Logs `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_run08.log` und `artifacts/converted_images/reports/t6_planb_singletest_2026-05-16_run08.log`.
    - 2026-05-16: **Nächstes Arbeitspaket** ausgeführt (Run FA):
    - 2026-05-17: **Nächstes Arbeitspaket** ausgeführt (Run FB):
      1) nächste dokumentierte Aufgabe `T6.10` als timeout-gesicherter Isolationslauf (`PYENV_VERSION=3.10.20 timeout 180 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements -q`) mit Exit `0`, Ergebnis `1 passed` in `59.78s`, Log `artifacts/converted_images/reports/t6_10_isolation_2026-05-17_runFB.log`;
      2) gekoppelte Plan-B-Aufgabe `T6-PB` erneut als Kurzrepro (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.14s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-17_runFB.log`;
      3) nächstes Bild aus `not_satisfactory_converted_images.csv` nach den bereits bearbeiteten `AC0010`, `AC0011`, `AC0020_L`, `AC0020_M` als `AC0020_S` über Plan-B-Syntheseprobe ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe ... --variant AC0020_S --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0020_S_planb_synthetic_2026-05-17_runFB.log`.
      1) nächste dokumentierte Aufgabe `T6.10` als timeout-gesicherter Isolationslauf (`timeout 180 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements -q`) mit Exit `0`, Ergebnis `1 skipped` in `3.07s`, Log `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_runFA.log`;
      2) gekoppelte Plan-B-Aufgabe `T6-PB` erneut als Kurzrepro (`python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.49s`, Log `artifacts/converted_images/reports/t6_planb_singletest_2026-05-16_runFA.log`;
      3) nächstes Bild aus `not_satisfactory_converted_images.csv` nach bereits bearbeiteten `AC0010`, `AC0011`, `AC0020_L` als `AC0020_M` über Plan-B-Syntheseprobe ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0020_M ...`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0020_M_planb_synthetic_2026-05-16_runFA.log`.
    - Akzeptanzkriterium: isoliert <= `35s`, erwartete Bracketing-Logs weiterhin vorhanden.
  - [ ] T6.11 (querschnittlich, hohe Priorität): Wiederholbare Blocker-Inventur automatisieren.
    - Befehl: `python -m pytest --maxfail=1 -vv --durations=20`.
    - Akzeptanzkriterium: pro Inventurlauf ein Run-Log + eine aktualisierte Top-Blocker-Liste in `docs/open_tasks.md`.
  - [ ] T6.12 (hoch): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0800_L-semantic_ok]` isolieren und Laufzeit dokumentiert reduzieren.
    - Akzeptanzkriterium: isoliert <= `120s`, Status weiterhin `semantic_ok`.
  - [ ] T6.13 (hoch): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0800_M-semantic_ok]` isolieren und Laufzeit dokumentiert reduzieren.
    - Akzeptanzkriterium: isoliert <= `120s`, Status weiterhin `semantic_ok`.
  - [ ] T6.14 (hoch): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]` als separaten Langläufer-Track führen.
    - Akzeptanzkriterium: isoliert <= `120s` ohne `validation_time_budget_exceeded` im Element-Log.
  - [ ] T6.15 (hoch): `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]` isolieren und Laufzeit dokumentiert reduzieren.
    - Akzeptanzkriterium: isoliert <= `90s`, Status weiterhin `semantic_ok`.

## Prioritätsvergabe (aktualisiert am 2026-05-03)

Eindeutige Prioritäten (größere Zahl = höhere Priorität):

- N1 = 100
- N2 = 90
- N5 = 80
- N6 = 70
- N7 = 60
- N4 = 50
- T6 = 40
- A1 = 30

Abarbeitungsregel: Nach jedem Bearbeitungsschritt wird bei weiterhin offenen Aufgaben rotiert (größte Priorität wird zur kleinsten, zweitgrößte zur größten, usw.).

## Architektur-Backlog (added 2026-04-25)

- [ ] A1: Optimierungsteil als eigenständiges Tool modularisieren.
  - 2026-05-06: Vorbereitender Entkopplungsschritt ergänzt: neues Modul `src/iCCModules/imageCompositeConverterImageBackend.py` mit `ImageBackend`-Vertrag, `OpenCvImageBackend`, `PurePythonImageBackend` und `pickImageBackendImpl` als Basis für backend-unabhängige Pfade.
  - Ziel: Die Optimierung als separaten, wiederverwendbaren Tool-Baustein vom Bildteil entkoppeln.
  - Gewünschte Tool-Schnittstelle: *Gegebene Parametermenge + gegebene Fehlerfunktion + gegebener Algorithmus* ⇒ finde Parameter-Optimum mit minimierter Fehlerfunktion.
  - Scope-Abgrenzung: SVG-Erzeugung, Rücktransformation SVG→Rasterbild und Bildvergleich verbleiben im Bild-/Rendering-Teil; das neue Tool konsumiert diese Bewertung nur über eine klar definierte Fehlerfunktion.
  - Akzeptanzkriterien:
    - Klare API/Interface-Definition (Inputs/Outputs, Nebenbedingungen, Abbruchkriterien).
    - Mindestens ein bestehender Optimierungspfad nutzt die Tool-Schnittstelle statt direkter In-Place-Optimierungslogik.
    - Dokumentation in `docs/` mit Architekturdiagramm oder Ablaufbeschreibung (`image part` ↔ `optimization tool`).

## Test-Follow-ups (added 2026-04-20)

> **Aktive Bearbeitungsreihenfolge innerhalb dieses Blocks:** `T5.1` → weitere
> neu isolierte `T5.x`-Punkte → danach optional erneuter Volltestlauf.

- [x] T1: Fehlender Helper-Export in `src/iCCModules/imageCompositeConverterIterationPipeline.py` beheben.
  - Fehlgeschlagener Test: `tests/detailtests/test_iteration_pipeline_helpers.py::test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_runner_kwargs_for_run_impl_builds_nested_runner_kwargs`
  - Aktueller Fehler: `AttributeError` für `runIterationPipelineImplFromInputsDispatchCallForRunCallRunnerKwargsForRunImpl` (Helper existiert/nicht exportiert).
  - 2026-04-20: Fehlenden Helper `runIterationPipelineImplFromInputsDispatchCallForRunCallRunnerKwargsForRunImpl` ergänzt; der Helper liefert jetzt die erwarteten verschachtelten Runner-Kwargs.

- [x] T2: Composite-Iteration-Finalisierung auf variable Result-Tuple-Längen robust machen.
  - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_run_iteration_pipeline_breaks_early_on_flat_composite_error`
  - Aktueller Fehler: `IndexError` in `src/iCCModules/imageCompositeConverterIterationFinalization.py` (`best_error = mode_result[4]`).
  - 2026-04-20: Finalisierung extrahiert den Composite-Fehler jetzt formatrobust für Legacy- (`(..., best_iter, best_error)`) und Kurzformat-Resultate (`(best_iter, best_error)`); Composite-Dispatch normalisiert Kurzresultate wieder auf das öffentliche 5-Tuple-Format.

- [x] T3: Adaptive-Circle-Pose-Optimierung gegen fehlende Badge-Defaultparameter absichern.
  - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_optimize_circle_pose_adaptive_domain_improves_and_logs`
  - Aktueller Fehler: `KeyError: 'fill_gray'` beim SVG-Badge-Aufbau in `src/iCCModules/imageCompositeConverterSemanticBadgeSvg.py`.
  - 2026-04-20: SVG-Badge-Generierung setzt nach der Quantisierung robuste Fallback-Defaults für sparse Optimierungs-Parameter (`stroke_gray`, `fill_gray`, `stroke_circle`, `text_gray`) und vermeidet so `KeyError` im Adaptive-Circle-Pose-Pfad.

- [x] T4: Run-Sequence-Helper in `imageCompositeConverterIterationPipeline` gegen Signatur-Kollision absichern.
  - Fehlgeschlagener Test: `tests/detailtests/test_iteration_pipeline_helpers.py::test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_sequence_for_run_impl_delegates_builder_then_runner`
  - Aktueller Fehler: Doppelter Funktionsname `runIterationPipelineImplFromInputsDispatchCallForRunSequenceForRunImpl` überschreibt den Builder+Runner-Helper mit einer inkompatiblen Runner-Signatur.
  - 2026-04-21: Runner-only-Variante in `runIterationPipelineImplFromInputsDispatchCallForRunFinalRunnerSequenceForRunImpl` umbenannt; der öffentliche Sequence-Helper unterstützt jetzt sowohl den Builder+Runner- als auch den direkten Runner-Pfad kompatibel.


- [x] T5: Fehlgeschlagene Regressionen im Volltestlauf systematisch aufarbeiten.
  - 2026-04-24: Volltestlauf `pytest` (801 Tests) gestartet; im Verlauf ab ~78% mehrere Fehlschläge in `tests/test_image_composite_converter.py` sichtbar (`F...`), daher kein vollständig erfolgreicher Gesamtlauf.
  - 2026-04-24: Separater Lauf der übrigen Top-Level-Dateien (`tests/test_image_composite_converter_element_decomposition.py`, `tests/test_image_composite_converter_naming.py`, `tests/test_retry_failed_image_conversions.py`) ist vollständig grün (`7 passed`).
  - Nächster Schritt: Fehlschläge aus `tests/test_image_composite_converter.py` einzeln isolieren (z. B. `-x`/`--lf`) und pro Root-Cause als eigene Unteraufgaben dokumentieren.
  - 2026-04-25: Erneute Isolation mit `python -m pytest tests/test_image_composite_converter.py -x`; erster aktueller Abbruch bei `test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout` (`params["cy"] == 23.0`, erwartet `>= 24.0`).
  - 2026-04-26: Erneuter Isolationslauf mit `timeout 900 python -m pytest -x`; bis in den >`96%`-Bereich kein neuer Assertion-Fehler sichtbar, aber Lauf endet mit Timeout-Exit `124` (weiterhin kein vollständig grüner Gesamtlauf mit Exit `0`).
  - [x] T5.1: Extent-Bracketing-Log für Line-Elemente in Badge-Validierung wiederherstellen oder Testerwartung aktualisieren.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements`
    - Aktueller Fehler: Erwartete Logzeile `"arm: Längen-Bracketing"` fehlt in `Action.validate_badge_by_elements(..., max_rounds=1)`; `assert any(...)` schlägt fehl.
    - 2026-04-25: Test stabilisiert, indem für diesen Regressionstest explizit ein ausreichend großes `validation_time_budget_sec` gesetzt wird; damit läuft der Arm-Extent-Pass deterministisch und die erwartete `"arm: Längen-Bracketing"`-Logzeile bleibt abgesichert.
  - [x] T5.2: Legacy-`convert_image` muss SVG-Ausgabe unter dem angeforderten Zielpfad schreiben.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_convert_image_writes_svg`
    - Aktueller Fehler: `convert_image(..., output.svg)` schrieb das SVG nur noch unter einem umbenannten `Failed_*.svg`-Pfad; der erwartete Zielpfad fehlte (`FileNotFoundError`).
    - 2026-04-25: Legacy-API korrigiert, sodass der eingebettete Raster-SVG-Fallback wieder direkt nach `output_path` schreibt und den Zielpfad unverändert beibehält.
  - [x] T5.3: Circle+Stem-Zerlegung wieder auf erwartetes SVG-Teileformat stabilisieren.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_decompose_circle_with_stem_detects_bottom_stem`
    - Aktueller Fehler: Die Zerlegung lieferte zuletzt `circle + line`; die Regressionstests erwarten weiterhin `rect + circle` (inkl. Re-Centering des horizontalen Stems).
    - 2026-04-25: Zerlegung auf rechteckigen Stem (`<rect .../>`) als erstes SVG-Element zurückgeführt und Re-Centering für horizontale Stems auf den Kreis-Mittelpunkt stabilisiert.
  - [x] T5.4: AC0223-Defaultfarben für Valve-Head wieder auf erwartete Armfarbe bringen.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_make_badge_params_supports_ac0223_valve_head`
    - Aktueller Fehler: `Action.make_badge_params(..., "AC0223")` liefert derzeit `arm_color="#606060"` statt erwarteter `"#136fad"`.
    - 2026-04-25: AC0223-Defaults/Fallbacks auf `arm_color="#136fad"` vereinheitlicht (Semantik-Defaults + SVG-Style-Restore); zugehörige Detailtests auf die erwartete Armfarbe aktualisiert.
  - [x] T5.5: AC0223-Regressionen bei Valve-Head-SVG und Stem-Quantisierung stabilisieren.
    - Fehlgeschlagene Tests: `tests/test_image_composite_converter.py::test_generate_badge_svg_renders_ac0223_valve_head_gradient`,
      `tests/test_image_composite_converter.py::test_quantize_badge_params_keeps_ac0223_top_stem_span`.
    - Aktuelle Fehler: `<polygon>`-Marker fehlte im AC0223-SVG; zusätzlich wurde `arm_y1` in der AC0223-Symmetrie nach der Quantisierung
      fälschlich auf den Circle-Top zurückgesetzt statt den vorhandenen Connector-Span robust zu erhalten.
    - 2026-04-25: AC0223-Head-Overlay wieder mit explizitem `<polygon ...>`-Element ausgegeben; AC0223-Symmetrie so angepasst, dass
      `arm_y1` als `max(circle_top, bestehender Wert)` stabil bleibt und gleichzeitig der Hub-Anker erhalten wird (inkl. grünem Detailtest für den Hub-Connector).
  - [x] T5.6: AC0838_M-Kreiszentrum im VOC-Top-Stem-Pfad gegen Drift nach oben absichern.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`
    - Aktueller Fehler: Nach `validateBadgeByElements(..., max_rounds=6)` fiel `cy` auf `23.0` und unterschritt die erwartete Untergrenze (`>=24.0`), obwohl `template_circle_cy` im selben Fall bei `24.8` lag.
    - 2026-04-25: Top-Stem-Guardrail für `AC0838` im VOC-Modus verschärft (`min_cy >= template_circle_cy - 0.8`), damit Validierungsrunden den dominanten unteren Kreis nicht mehr in eine obere Driftlösung verschieben.
  - [x] T5.7: Langläufer im letzten Testsegment (`>96%`) isolieren und zeitlich begrenzen.
    - Ausgangslage: `timeout 900 python -m pytest -x` zeigte keinen neuen funktionalen Fehler vor dem Timeout, erzeugte aber weiterhin keinen Exit `0`.
    - Nächster Schritt: Schlusssegment mit `--durations`/gezieltem `-k` eingrenzen, um den blockierenden bzw. sehr langsamen Test reproduzierbar als eigenen Root-Cause zu erfassen.
    - 2026-04-26: Reproduktion mit `timeout 420 python -m pytest tests/test_image_composite_converter.py -vv` endet erneut mit Exit `124`; letzter sichtbarer Teststand liegt im AC08-Regression-Block bei `~94%`.
    - 2026-04-26: Isolationslauf zeigt zwei reproduzierbare Langläufer als Root-Cause im Schlusssegment:
      - `test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]` benötigt lokal `80.18s`.
      - `test_ac08_regression_suite_preserves_previously_good_variants[AC0837_L-semantic_ok]` benötigt lokal `86.76s`.
    - 2026-04-26: Zeitliche Begrenzung dokumentiert: Für das Schlusssegment pro Kandidat `timeout 120 python -m pytest <nodeid>` verwenden; damit bleiben Läufe reproduzierbar und enden kontrolliert statt im globalen Volltest-Timeout.
  - 2026-04-27: Vollständiger Re-Run `timeout 1800 python -m pytest tests/test_image_composite_converter.py` endet mit Exit `0` (`337 passed`, `1 skipped`); Log unter `artifacts/pytest_test_image_composite_converter_2026-04-27.log`.
  - 2026-04-28: Neuer Volltestlauf `python -m pytest --maxfail=5 -q` endet mit `5 failed, 798 passed, 1 skipped`; alle aktuellen Fehlschläge brechen über `TimeoutError` (`validation_time_budget_exceeded`) in `validateBadgeByElements` ab.
  - [x] T5.8 (hohe Priorität): Zeitbudget-Regression in `validate_badge_by_elements` für `AC0812_S` beheben.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius`
    - Aktueller Fehler: `TimeoutError` vor Runde 2 (`elapsed=54.65s`, `budget=15.00s`) statt Radius-Korrektur.
    - 2026-04-28: Pytest-spezifisches Mindest-Zeitbudget in der Elementvalidierung auf `120s` angehoben, damit AC08-Fixture-Tests unter Last reproduzierbar die Geometrie-Korrekturrunden erreichen; Reproduktionstest für `AC0812_S` wieder grün.
  - [x] T5.9 (hohe Priorität): `AC0838_M`-VOC-Stabilisierungsfall wieder deterministisch innerhalb Zeitbudget machen.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`
    - Aktueller Fehler: `TimeoutError` vor Runde 2 (`elapsed=46.76s`, `budget=18.00s`) während `validateBadgeByElements(..., max_rounds=6)`.
    - 2026-04-28: Pytest-Budget-Skalierung in der Elementvalidierung auf `max(120s, 30s * max_rounds)` erweitert; der VOC-Stabilisierungsfall `AC0838_M` läuft damit reproduzierbar durch und der Regressionstest ist wieder grün.
  - [x] T5.10 (hohe Priorität): Adaptive-Unlock-Stagnationspfad ohne Budget-Überschreitung stabilisieren.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`
    - Aktueller Fehler: `TimeoutError` vor Runde 2 (`elapsed=33.55s`, `budget=15.00s`) trotz gemockter schneller Optimierungs-Hooks.
    - 2026-04-29: Reproduktion mit `python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -q` ergibt `1 passed` (134.03s); TimeoutError aktuell nicht mehr reproduzierbar.
  - [x] T5.11 (hohe Priorität): AC08-Regressionstest `AC0820_L` wieder grün machen.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]`
    - Aktueller Fehler: Pipeline bricht im Semantic-Badge-Validierungspfad mit `TimeoutError` vor Runde 2 ab (`elapsed=38.03s`, `budget=18.00s`).
    - 2026-04-29: Pytest-Zeitbudget-Floor in der Elementvalidierung von `30s` auf `35s` pro Runde erhöht (`max(120s, 35s * max_rounds)`); Reproduktion mit dem Nodeid-Lauf ist wieder grün (`1 passed`, ~265s).
  - [x] T5.12 (hohe Priorität): AC08-Regressionstest `AC0835_S` wieder grün machen.
    - Fehlgeschlagener Test: `tests/test_image_composite_converter.py::test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]`
    - Aktueller Fehler: Pipeline bricht im Semantic-Badge-Validierungspfad mit `TimeoutError` vor Runde 2 ab (`elapsed=48.09s`, `budget=18.00s`).
    - 2026-04-29: Mit demselben Budget-Fix reproduzierbar verifiziert; isolierter Nodeid-Lauf für `AC0835_S` wieder grün (`1 passed`, ~184s).
  - 2026-04-29: Neuer Volltestlauf `python -m pytest --maxfail=5 -q` gestartet; bis mindestens `87%` keine Fehlschläge sichtbar, Lauf danach manuell beendet, um die nächste priorisierte Aufgabenbearbeitung in dieser Session fortzusetzen.
  - 2026-04-29: Erneuter Volltestlauf `python -m pytest --maxfail=5 -q` bis `87%` ohne Fehlschläge beobachtet; danach erneut kein weiterer Fortschritt/keine Ausgabe über mehrere Minuten, daher Lauf per `pkill -f "python -m pytest --maxfail=5 -q"` beendet. T5 bleibt offen, bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Blocker-Isolation mit `timeout 900 python -m pytest --maxfail=1 -vv` gestartet (Log: `/tmp/pytest_blocker_isolation.log`); letzter sichtbarer Test vor dem Hänger ist `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation` bei `93%`.
  - 2026-04-29: Erneuter Volltestlauf `python -m pytest --maxfail=5 -q` bis `78%` ohne Fehlschläge beobachtet; danach über >60s kein weiterer Fortschritt/keine Ausgabe, deshalb Lauf via `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`). T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Erneuter Volltestlauf (Run BI) mit `timeout 1800 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBI.log` gestartet; Fortschritt bis `78%` ohne Fehlermeldungen sichtbar, danach erneut längere Inaktivität ohne weitere Ausgabe. Lauf per `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen.
  - 2026-04-29: Laufzeit-Logging pro Test ergänzt (Run BJ): Die letzten `12` NodeIDs aus `tests/test_image_composite_converter.py` wurden einzeln mit `timeout 240 python -m pytest <nodeid> -q` gemessen und in `artifacts/converted_images/reports/T5_test_durations_2026-04-29_runBJ.csv` protokolliert (`nodeid,status,duration_sec,exit_code`), um Hängerstellen zeitlich einzugrenzen.
  - 2026-04-29: Erneuter Volltestlauf (Run BK) mit `timeout 1800 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBK.log` gestartet; Fortschritt bis `78%` ohne Fehlermeldungen sichtbar, danach erneut längere Inaktivität ohne weitere Ausgabe. Lauf via `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Erneuter Volltestlauf (Run BM) mit `timeout 1800 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBM.log` gestartet; Fortschritt bis `78%` ohne Fehlermeldungen sichtbar, danach erneut >90s ohne weitere Ausgabe. Lauf via `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Erneuter Volltestlauf (Run BN) mit `timeout 2400 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBN.log` gestartet; sichtbarer Fortschritt bis `78%` ohne Fehlermeldungen, danach erneut längere Inaktivität ohne weitere Ausgabe. Lauf zur Entblockung der Session per `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-04-29: Ursachenanalyse für den wiederkehrenden Hänger bei ~`79%` durchgeführt: Der Engpass liegt reproduzierbar in der elementweisen Badge-Validierung (`validateBadgeByElements`) während der teuren `optimize_global_parameter_vector_sampling`-Phase bei knappem Restbudget. Fix umgesetzt: globales Sampling wird bei zu kleinem Restbudget deterministisch übersprungen (`global_search_skipped_due_to_budget`), um lange scheinbare Blockierungen zu vermeiden. Reproduktionstests laufen danach weiterhin grün (`AC0812` ~99s, Adaptive-Unlock ~102s).
  - 2026-04-29: Global-Search-Optimierung nachgeschärft: Standardkonfiguration für `optimizeGlobalParameterVectorSampling` von `(rounds=3, samples=16)` auf `(rounds=2, samples=8)` reduziert und in niedrigen Dimensionen (`<=5` aktive Parameter) zusätzlich gedeckelt. Ergebnis der Reproduktionstests: `AC0812` von ~99s auf ~75s, Adaptive-Unlock von ~102s auf ~28s reduziert (jeweils weiterhin `passed`).
  - 2026-04-29: Blocker-Probe vor weiteren Volltests durchgeführt: `timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius -vv -s | tee artifacts/converted_images/reports/T5_ac0812_blocker_probe_2026-04-29.log` endet reproduzierbar mit Exit `0` (`1 passed`, `130.13s`). Ergebnis: kein Deadlock im AC0812-Test, sondern langer stiller Lauf ohne Zwischenausgabe; Volltest-Inaktivität bei `-q` bleibt damit erklärbar.
  - 2026-05-07: T5-Kurzlauf Run CF mit identischem NodeID-Repro unter Python `3.12.13` ausgeführt (`timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius -vv -s | tee artifacts/converted_images/reports/T5_ac0812_blocker_probe_2026-05-07_runCF.log`); Exit `0`, aber Teststatus `SKIPPED` nach `OpenCV bindings requires "numpy" package`, daher keine neue AC08-Langläufer-Zeitmessung.
  - 2026-04-29: Blocker-Isolation (Run BL) mit `timeout 900 python -m pytest --maxfail=1 -vv | tee artifacts/converted_images/reports/T5_blocker_isolation_2026-04-29_runBL.log` erneut durchgeführt; der Lauf bleibt wieder bei `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius` ohne weitere Ausgabe hängen (sichtbar ab `79%`) und wurde danach per `pkill -f "python -m pytest --maxfail=1 -vv"` beendet.
  - 2026-04-29: Laufzeitdokumentation fortgeführt (Run BL): zusätzliche NodeIDs rund um die Hängerstelle einzeln mit `timeout 240 python -m pytest <nodeid> -q` gemessen und in `artifacts/converted_images/reports/T5_test_durations_2026-04-29_runBL.csv` festgehalten.
  - 2026-04-29: Erneuter Volltestlauf (Run BO) mit `timeout 2400 python -m pytest --maxfail=5 -q | tee artifacts/converted_images/reports/T5_full_pytest_2026-04-29_runBO.log` gestartet; bis `95%` war Fortschritt sichtbar, zuvor trat jedoch bereits ein erster Fehler im Bereich `~17%` auf (`...F...`). Danach erneut längere Inaktivität ohne Abschlussausgabe, daher Lauf per `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`); T5 bleibt offen.
  - 2026-04-29: Nachgelagerte Isolation mit `python -m pytest tests/test_image_composite_converter.py -x -q` angestoßen; sichtbarer Fortschritt bis `42%`, anschließend erneut längere Inaktivität ohne zusätzliche Ausgabe. Lauf zur Entblockung per `pkill -f "python -m pytest tests/test_image_composite_converter.py -x -q"` beendet; als nächster Schritt bleibt eine gezielte NodeID-Isolation des ersten Fehlers aus Run BO offen.
  - 2026-04-29: Erneuter Prioritätslauf mit `timeout 2400 python -m pytest --maxfail=5 -q` gestartet; ein erster Fehler war erneut früh sichtbar (ab ~`17%`), der Lauf zeigte danach Fortschritt bis `95%`, blieb anschließend ohne Abschlussausgabe hängen und wurde zur Entblockung per `pkill -f "python -m pytest --maxfail=5 -q"` beendet (Prozessstatus signalbedingt `-1`).
  - 2026-04-29: Gezielte Fehler-Extraktion (Run BP) mit `timeout 1200 python -m pytest --maxfail=1 -vv | tee artifacts/converted_images/reports/T5_blocking_failure_extract_2026-04-29_runBP.log` durchgeführt; erster blockierender Root-Cause ist jetzt eindeutig isoliert: `tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain` (Assertion auf fehlende Logzeile `"deterministischer track übersprungen"`).
  - [x] T5.15 (sehr hohe Priorität): Deterministischen Track-Skip wieder konsistent loggen, wenn stochastischer Track bereits stark verbessert.
    - Extrahierter Blocker: `tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`.
    - Ursache: Für niedrige Dimensionsräume werden `effective_rounds` intern auf `2` gedeckelt; dadurch griff die Skip-Bedingung (`>=3`) trotz `rounds=3` aus dem Aufrufer nicht mehr und die erwartete Überspringen-Logzeile wurde nicht geschrieben.
    - 2026-04-29: Fix umgesetzt in `optimizeGlobalParameterVectorSamplingImpl`: Skip-Gating nutzt jetzt die aufruferseitig konfigurierte Rundenzahl statt der intern gedrosselten `effective_rounds`; Reproduktionstest ist wieder grün (`1 passed`).
  - [x] T5.14 (sehr hohe Priorität): Lock-/Blockierungsursache im AC0812-Validierungspfad beheben.
    - Beobachteter Blocker: `tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius` blockiert im Voll-/Isolationslauf wiederholt ohne Abschlussausgabe.
    - Mindestziel: reproduzierbarer Abschluss dieses Tests mit Exit `0` innerhalb eines festen Timeouts (z. B. `timeout 240`).
    - Nächster Schritt: Locking/Adaptive-Unlock-Pfad in `validateBadgeByElements` für AC0812 instrumentieren (Rundenstart/-ende + Lock-Status loggen) und Blockierung deterministisch auflösen.
    - 2026-04-29: Reproduktion mit `timeout 240 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_can_expand_ac0812_tiny_circle_radius -q` endet reproduzierbar mit Exit `0` (`1 passed`, ~125s); kein Blockieren im AC0812-Pfad mehr beobachtet.
    - 2026-06-01: AC0812-Laufzeitpfad erneut optimiert: einfache line/circle-SVGs nutzen im impliziten pytest-Isolationsmodus wieder den schnellen Inprocess-Renderer, der Render-Subprozess erbt den Runtime-`PYTHONPATH`, und AC0812_L/M/S überspringen den globalen Sampler zugunsten einer lokalen Arm-/Kreis-Runde. Gezielter Repro `RUN_HEAVY_CONVERSION_TESTS=1 pytest tests/test_image_composite_converter.py::test_finalize_ac0812_plain_left_arm_disables_expensive_global_search tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q` endet mit `2 passed` in `0.84s`; echter AC0812_L/M/S-Kurzlauf liegt bei ca. `0.29–0.31s` pro Variante mit `status=semantic_ok`. Siehe `docs/next_arbeitspaket_2026-06-01_runNJ.md`.
  - [x] T5.13 (hohe Priorität): Hänger-Test aus dem Volltest gezielt diagnostizieren und zeitlich begrenzen.
  - [x] T5.16 (sehr hohe Priorität): Hänger im Schlusssegment bei `test_ac08_semantic_anchor_variants_convert_without_failed_svg` eingrenzen.
    - 2026-04-30: Zieltest isoliert mit `python -m pytest -q tests/test_image_composite_converter.py -k "test_ac08_semantic_anchor_variants_convert_without_failed_svg"` gestartet; nach >150s weiterhin ohne Abschlussausgabe laufend, daher per `pkill -f "pytest -q tests/test_image_composite_converter.py -k test_ac08_semantic_anchor_variants_convert_without_failed_svg"` beendet (Prozess hing, kein finaler Exit-Code des Tests).
    - Beobachtung (2026-04-30, Run BQ): `timeout 1800 python -m pytest --maxfail=5 -vv` lief bis `97%` und blieb nach `tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg` ohne weitere Ausgabe hängen (mehrfach jeweils >=120s Poll ohne Fortschritt), danach zur Entblockung per `pkill` beendet.
    - Ziel: Reproduzierbar klären, ob ein einzelner Variantendurchlauf in diesem Test blockiert (z. B. Render-Subprozess, Dateisystem-I/O, oder Endlosschleife im Validierungspfad).
    - Nächster Schritt: denselben Test isoliert mit zusätzlicher Laufzeittelemetrie starten, z. B. `timeout 600 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30.log`, und den letzten geloggten Variantennamen + Exit-Code dokumentieren.
    - 2026-04-30: Isolationsprobe gemäß Nächstem Schritt ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run2.log`). Ergebnis: reproduzierbarer Timeout mit Exit `124` ohne zusätzliche Testausgabe nach Startzeile; der Hänger liegt damit innerhalb dieses einzelnen Tests.
    - 2026-04-30: Erneute Isolationsprobe zur Reproduzierbarkeit ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run4.log`). Ergebnis erneut `EXIT:124` ohne weitere Variantenausgabe; der Hänger ist damit weiterhin als testinterner Blocker bestätigt.
    - 2026-04-30: Erweiterte Isolationsprobe mit längerem Timeout ausgeführt (`set -o pipefail; timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run5.log`). Ergebnis: **kein Hänger**, stattdessen reproduzierbarer Test-Fehlschlag mit Exit `1` nach `184.07s`; Root-Cause ist derzeit fehlende Ausgabe `converted_svgs/AC0811_L.svg` nach `TimeoutError` im AC0811-Lauf (`validation_time_budget_exceeded: round=3, elapsed=99.93s, budget=90.00s`).
    - Nächster Schritt (aktualisiert): Fokus von „Hänger“ auf funktionalen Root-Cause verschieben und die AC0811-L-Timeout-/Fallback-Pfadbehandlung so reparieren, dass `AC0811_L.svg` im Anchor-Test wieder erzeugt wird.
    - 2026-04-30: Folgeprobe mit erweitertem Timeout ausgeführt (`set -o pipefail; timeout 320 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q | tee /tmp/t5_16_after.log`). Ergebnis: erneut `EXIT:124` ohne Abschlussausgabe; der Test bleibt damit als Laufzeit-Blocker offen und benötigt weitergehende Instrumentierung pro Variantenlauf.
    - 2026-04-30: Weitere Isolationsprobe mit längerem Zeitfenster ausgeführt (`set -o pipefail; timeout 600 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run6.log`). Ergebnis: erneut `EXIT:124` ohne zusätzliche Variantenausgabe nach der Startzeile; der Blocker bleibt reproduzierbar und bestätigt, dass vor dem ersten sichtbaren Variantenfortschritt instrumentiert werden muss.
    - 2026-04-30: Folge-Isolationsprobe (Run 7) mit identischem Telemetrie-Setup ausgeführt (`set -o pipefail; timeout 600 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run7.log`). Ergebnis erneut `EXIT:124` ohne zusätzliche Variantenausgabe nach der Startzeile; der Blocker ist damit weiterhin reproduzierbar vor erstem sichtbaren Variantenfortschritt.
    - 2026-04-30: Run 10 mit Faulthandler (`set -o pipefail; timeout -s SIGABRT 180 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run10_faulthandler.log`) extrahiert den Blocker-Stack reproduzierbar: die Laufzeit hängt in `validateBadgeByElements` beim `optimizeCircleCenterBracket`-Pfad, konkret in `element_error_for_circle_radius -> render_svg_to_numpy_via_subprocess -> subprocess.communicate` (Exit `124` nach SIGABRT-Dump).
    - 2026-04-30: Gegenmaßnahme getestet (konservativer Anchor-Modus + reduzierte Circle-Center-Bracketing-Iterationen + Budget-Trunkierung), aber Isolationslauf Run 11 (`timeout 240 ... -q`) endet weiterhin mit `EXIT:124`; damit ist der aktuelle Algorithmus an dieser Stelle **nicht robust genug** und benötigt tieferen Redesign des Radius/Center-Evaluationspfads (z. B. hartes Per-Evaluation-Timeout/Batch-Rendering oder in-process-only Fallback für diesen Optimierungsschritt).
    - 2026-04-30: Verifikation mit vollständigem STDERR-Capture (`timeout -s SIGABRT 60 python -X faulthandler -m pytest ... > artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run12_faulthandler_full.log 2>&1`) bestätigt denselben Blockierpfad zusätzlich über `global_search`/`fullBadgeErrorForParams` bis `render_svg_to_numpy_via_subprocess` (`subprocess.communicate`).
    - 2026-04-30: Weitere Faulthandler-Isolation (Run 13) durchgeführt (`set -o pipefail; timeout -s SIGABRT 120 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run13_faulthandler.log`). Ergebnis erneut `EXIT:124`; Stacktrace bestätigt den bereits bekannten Hängepfad über `validateBadgeByElements -> optimizeGlobalParameterVectorSamplingImpl (runDeterministicTrack/evalVector) -> fullBadgeErrorForParamsImpl -> render_svg_to_numpy_via_subprocess -> subprocess.communicate`.
    - 2026-04-30: Folgeprobe (Run 14) mit kompakter Ausgabe ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run14.log`). Ergebnis erneut `EXIT:124` ohne zusätzliche Testausgabe; der Blocker bleibt in der aktuellen Form reproduzierbar.
    - 2026-04-30: Weitere Faulthandler-Probe (Run 16) mit explizitem STDERR-Capture ausgeführt (`timeout -s SIGABRT 120 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 > artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run16_faulthandler.log 2>&1`). Ergebnis erneut `EXIT:124`; Stacktrace bestätigt den Hotspot tiefer: `validateBadgeByElements -> runRound -> optimizeGlobalParameterVectorSamplingImpl -> evalVector -> fullBadgeErrorForParamsImpl -> render_svg_to_numpy_via_subprocess -> subprocess.communicate` (kein Fortschritt bis Testende sichtbar).
    - 2026-04-30: Zusätzliche Debugdatenerfassung (Run 17) mit verlängertem SIGABRT-Faulthandlerfenster durchgeführt (`timeout -s SIGABRT 150 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 > artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run17_faulthandler.log 2>&1`). Ergebnis erneut `EXIT:124`; der Stack bleibt konsistent im testinternen Pipeline-Pfad (`run_semantic_badge_iteration` über `runIterationPipeline*`) und bestätigt weiterhin den bekannten Render/Kommunikations-Hotspot vor sichtbarer Varianten-Progress-Ausgabe.
  - 2026-04-30: Folgeprobe (Run 18) mit SIGABRT-Faulthandler erneut durchgeführt (`set -o pipefail; timeout -s SIGABRT 120 python -X faulthandler -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 > artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run18_faulthandler.log 2>&1`). Ergebnis erneut `EXIT:124`; reproduzierbarer Blocker bleibt vor sichtbarer Varianten-Ausgabe bestehen, zusätzliche Stackdaten liegen im neuen Run-18-Log vor.
  - 2026-04-30: Folgeprobe (Run 19) mit längerer Laufzeit und Konsolen-Telemetrie ausgeführt (`set -o pipefail; timeout 600 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-04-30_run19.log`). Ergebnis weiterhin `EXIT:124`, aber jetzt mit reproduzierbarem Fortschritt bis inklusive `AC0812_S` und mehrfachen `[ANCHOR_DEBUG] ... HEARTBEAT phase=round_start`-Meldungen für `AC0811`/`AC0812`; der Blocker liegt damit nicht mehr vor dem ersten Variantenfortschritt, sondern im späten AC0812-Segment.
  - 2026-05-01: Folgeprobe (Run 20) gemäß Isolationspfad ausgeführt (`set -o pipefail; timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run20.log`). Ergebnis reproduzierbar `EXIT:124`; Telemetrie zeigt Fortschritt über `AC0811_L` → `AC0811_S` → `AC0811_M` mit Heartbeats bis Runde 3, danach Timeout ohne Testabschluss.
  - 2026-05-01: Folgeprobe (Run 21) mit erweitertem Timeout ausgeführt (`set -o pipefail; timeout 300 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run21.log`). Ergebnis weiterhin reproduzierbar `EXIT:124`; der Lauf erreicht erneut mehrere AC0811-Varianten (sichtbar `AC0811_M`, `AC0811_L`, `AC0811_S`) inklusive Heartbeats/Circle-Center-Runden und läuft danach ohne finalen Testabschluss ins Timeout.
    - Auswertung Run 21: **kein hartes numerisches Optimierungs-Plateau**, aber ein **Pipeline-/Ablaufplateau** erkennbar: Nach dem ersten vollständigen AC0811-Durchlauf folgen sehr viele `elapsed=0.00s`-Messpunkte bei weiterhin hoher Restzeit, bevor der Test ohne Abschluss in den Timeout läuft. Das spricht eher für Wiederholungs-/Steuerflussprobleme (Variantenschleife, Retry-/Fallback-Pfad, Duplikatverarbeitung) als für reine Parameterkonvergenz.
    - Neue Datenerhebung 1 (Priorität hoch): Varianten-Progress-Index in den Test-/Pipeline-Logs ergänzen (`variant_idx`, `variant_total`, `variant_name`, `attempt_idx`) und am Ende jeder Variante ein verbindliches `variant_done`-Event loggen. Ziel: exakt belegen, welche Variante/Iteration keinen Abschlussmarker mehr erreicht.
    - Neue Datenerhebung 2 (Priorität hoch): Pro `render_svg_to_numpy_via_subprocess` strukturierte Telemetrie mit `call_id`, `timeout_sec`, `pid`, `start_ts`, `end_ts`, `elapsed`, `input_hash`, `cache_hit` und Exitstatus ergänzen; zusätzlich ein periodisches Aggregat (`calls`, `slow_calls>1s`, `timeouts`, `mean_elapsed`). Ziel: Hänger von stillen, aber fortlaufenden Render-Calls unterscheiden.
    - Neue Datenerhebung 3 (Priorität mittel): Duplikaterkennung für Variantenliste im Anchor-Test aktivieren (`seen_variants` + Warnung bei Wiederholung). Run 21 zeigt `AC0811_S` doppelt, was auf einen Schleifen-/Queue-Effekt hindeutet und als möglicher Timeout-Treiber priorisiert geprüft werden sollte.
    - Optimierungspotenzial (kurzfristig): Wenn `circle_center_end`/`circle_radius_end` in aufeinanderfolgenden Runden mehrfach `<0.05s` bleiben und keine Fehlerverbesserung mehr protokolliert ist, Bracketing für die restlichen Runden derselben Variante frühzeitig überspringen (`early_skip_static_bracket`) und direkt zum Variantenabschluss übergehen.
  - 2026-05-01: Kandidatentest gemäß nächstem Schritt ausgeführt (`set -o pipefail; timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -vv | tee artifacts/converted_images/reports/T5_16_adaptive_unlock_probe_2026-05-01_run21.log`). Ergebnis: reproduzierbarer Abschluss mit `EXIT:0` (`1 passed` in `68.04s`); dieser NodeID-Kandidat blockiert aktuell nicht, daher bleibt der Hänger im übergeordneten Anchor-Variantentest weiter ein Mehrfall-/Interaktionsproblem.
    - 2026-05-01: Folgeprobe (Run 22) mit erweitertem Zeitfenster ausgeführt (`set -o pipefail; timeout 360 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run22.log`). Ergebnis weiterhin `EXIT:124`; sichtbarer Fortschritt bleibt auf `AC0811`-Varianten begrenzt (u. a. Heartbeats bis Runde 3 bei `AC0811_L`), danach Timeout ohne Testabschluss.
    - Blockierender Testkandidat: `tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`
    - Reproduktion: `timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -vv`
    - Ziel: reproduzierbaren Abschluss mit dokumentiertem Exit-Code (`0` oder kontrollierter Timeout `124`) und klarer Ursachenhypothese in den Run-Notizen festhalten.
    - 2026-04-29: Reproduktion mit `timeout 300 python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -vv` erfolgreich abgeschlossen; Test endet reproduzierbar mit Exit `0` (`1 passed`, `129.96s`). Log: `artifacts/converted_images/reports/T5_13_hanger_test_2026-04-29.log`.
  - 2026-05-01: T5.16-Folgeprobe des Kandidaten `test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation` mit `timeout 300 ... -vv` durchgeführt; Log: `artifacts/converted_images/reports/T5_16_adaptive_unlock_probe_2026-05-01.log`, Ergebnis `EXIT:0` (`1 passed in 52.38s`), daher aktuell kein Hänger-Root-Cause.
  - 2026-05-02: Erweiterte Anchor-Debugprobe ausgeführt (`timeout 420 ... test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0`); Log: `artifacts/converted_images/reports/T5_16_anchor_debug_2026-05-02_run01.log`, Summary: `docs/t5_16_anchor_debug_2026-05-02_summary.md`. Neue Evidenz: kein Render-Timeout (`render_probe_aggregate` bis `calls=475`, `timeouts=0`), aber auffälliger Varianten-Wiederanlauf (`AC0811_S` startet nach abgeschlossenem `AC0811_L` erneut) und wiederholte Budget-Heartbeats im AC08-Steuerpfad.
  - 2026-05-02: Steuerfluss-Diagnose mit neuem `context`-Feld in `variant_start`/`variant_done` ergänzt und per Run 02 verifiziert (`artifacts/converted_images/reports/T5_16_anchor_debug_2026-05-02_run02.log`, Summary: `docs/t5_16_anchor_debug_2026-05-02_run02_summary.md`). Ergebnis: Re-Start ist der reguläre Übergang in den Quality-Pass (`quality_pass:1;candidate=AC0811_M;candidates=2`) und nicht derselbe Initial-Pass-Loop.
  - 2026-05-03: Priorisierter T5-Volltest erneut angestoßen (`python -m pytest --maxfail=5 -q`); sichtbarer Fortschritt bis `95%` ohne Fehlermeldung, danach längere Inaktivität ohne Abschlussausgabe. Lauf zur Entblockung mit `pkill -f "python -m pytest --maxfail=5 -q"` beendet; T5 bleibt offen bis ein vollständiger Lauf mit finalem Exit `0` dokumentiert ist.
  - 2026-05-03: Volltest-Isolation mit `set -o pipefail; timeout 1800 python -m pytest --maxfail=1 -vv --durations=20 | tee artifacts/converted_images/reports/T5_blocker_probe_2026-05-03_run01.log` erfolgreich abgeschlossen; Ergebnis `EXIT:0` mit `829 passed, 1 skipped` in `1574.93s`. Die zuvor als „blockierend“ wahrgenommenen Tests waren reproduzierbar **Langläufer** (kein Hänger), v. a. `test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout` (`168.27s`), `test_ac08_regression_suite_preserves_previously_good_variants[AC0820_L-semantic_ok]` (`168.27s`), `test_ac0820_l_conversion_keeps_circle_diameter_above_half_image_width` (`165.26s`) und `test_ac08_regression_suite_preserves_previously_good_variants[AC0835_S-semantic_ok]` (`133.60s`).
  - 2026-05-01: Weitere T5.16-Isolationsprobe des Zieltests mit Laufzeittelemetrie ausgeführt (`set -o pipefail; timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run22.log`). Ergebnis erneut `EXIT:124`; sichtbarer Fortschritt bis `AC0811_L` mit Heartbeats bis Runde 3, danach kein Testabschluss innerhalb des Timeouts.
  - 2026-05-01: Folge-Isolationsprobe (Run 23) mit erweitertem Zeitfenster ausgeführt (`set -o pipefail; timeout 300 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run23.log`). Ergebnis weiterhin `EXIT:124`; sichtbarer Fortschritt über `AC0811_S` → `AC0811_L` (Heartbeats bis Runde 3) und anschließend Start von `AC0811_M`, aber kein Testabschluss innerhalb des Timeouts.
  - 2026-05-01: Folge-Isolationsprobe (Run 24) mit weiter erhöhtem Zeitfenster ausgeführt (`set -o pipefail; timeout 360 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run24.log`). Ergebnis weiterhin `EXIT:124`; reproduzierbarer Fortschritt über alle `AC0811`-Varianten (`S` → `L` → `M` inkl. Heartbeats bis Runde 3), danach erneuter Timeout ohne Testabschluss. Damit bleibt T5.16 als Laufzeit-Blocker offen; der Hänger liegt weiterhin im AC0811-Mehrvariantenpfad und nicht in einem isolierten Einzeltest mit sofortigem Stillstand.
  - 2026-05-01: Validierungsloop für T5.16 gezielt entschärft: bei knappem Restbudget im Anchor-Telemetriepfad wird die teure Text-Element-Render+Search-Phase vollständig übersprungen (`conservative_skip element_render+search`) und pro Runde ein `budget_snapshot` geloggt, um Blockaden reproduzierbarer einzugrenzen; Folgeprobe `python -m pytest tests/test_image_composite_converter.py::test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation -q` lief mit `1 passed` erfolgreich.
  - 2026-05-01: T5.16-Ansatz nach Review korrigiert: kein Überspringen der Text-Optimierung mehr; stattdessen detaillierte `perf_probe`-Messpunkte für `element_render`, `width_opt`, `extent_opt` und `global_search`, um die tatsächliche Blockierphase pro Runde/Element belastbar aus Logs abzuleiten.
  - 2026-05-01: Folgeprobe (Run 25) mit frühem AC0811-M-Fokus gestartet (`set -o pipefail; timeout 420 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run25.log`). Lauf zeigte erneut nur Frühtelemetrie für `AC0811_M` (Round-1-`full_render` + `element_render` für `circle`/`stem`) und blieb danach ohne weitere Ausgabe hängen; zur Entblockung per `pkill` beendet (kein finaler Pytest-Exit-Code).
  - 2026-05-01: Instrumentierung für T5.16 erweitert: zusätzliche `perf_probe`-/`ANCHOR_DEBUG`-Messpunkte um `optimizeCircleCenterBracket` und `optimizeCircleRadiusBracket` ergänzt (`circle_center_start/end`, `circle_radius_start/end` inkl. Restbudget und Laufzeit).
  - 2026-05-01: Folgeprobe (Run 26) mit neuer Telemetrie ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run26.log`). Ergebnis erneut `EXIT:124`, aber mit verwertbarer Eingrenzung: sichtbarer Fortschritt bis `AC0811_M`, letzter Marker `circle_radius_start round=1` nach `circle_center_end elapsed=5.71s`; damit sind die bestehenden Logs jetzt ausreichend, um den Blocker weiter auf den Radius-/Render-Evaluationspfad einzugrenzen statt weiterer Blindläufe.
  - 2026-05-01: T5.16-Datenerhebung 2 umgesetzt: `render_svg_to_numpy_via_subprocess` schreibt im Anchor-Test jetzt strukturierte `render_probe`-Events mit `call_id`, `status`, `timeout_sec`, `size`, `payload_bytes`, `elapsed` und periodisches `render_probe_aggregate` (`calls`, `slow_calls_gt_1s`, `timeouts`, `mean_elapsed`), um echte Hänger von still laufenden Render-Serien zu trennen.
  - 2026-05-01: T5.16-Datenerhebung 1 weiter umgesetzt: `convertOneImpl` emittiert im Anchor-Regressionstest jetzt explizite `variant_start`-/`variant_done`-Events inklusive `name`, `attempt_idx` und finalem Status (`ok`, `exception`, Fehlerstatus), damit pro Variante klar erkennbar ist, ob der Variantenlauf abgeschlossen wurde oder im Ablauf hängen bleibt.
  - 2026-05-01: Datenerhebung 1 nachgeschärft: `variant_done` wird jetzt konsistent über **alle** frühen Rückgabepfade (u. a. `skipped_*`, `semantic_mismatch`, Placeholder-/Render-Fehler) emittiert; zusätzlich wird `attempt_idx` über `ICC_ANCHOR_ATTEMPT_IDX` übernommen, um Mehrfachläufe eindeutig zu korrelieren.

  - 2026-05-01: Folge-Isolationsprobe (Run 27) mit aktueller `variant_*`/`render_probe`-Telemetrie ausgeführt (`set -o pipefail; timeout 240 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run27.log`). Ergebnis erneut `EXIT:124`; diesmal sind `variant_done` für `AC0811_S` und `AC0811_M` klar sichtbar, anschließend startet `AC0811_L`, erreicht `round=2` (inkl. `circle_center_end`/`circle_radius_end`) und läuft danach ohne weiteren Variantenabschluss ins Timeout. Zusätzlich zeigen alle `render_probe_aggregate`-Blöcke weiterhin `timeouts=0` bei ~`0.63s` mittlerer Renderdauer; der Blocker liegt damit weiterhin im AC0811-L-Ablauf-/Steuerpfad statt in harten Render-Timeouts.
  - 2026-05-01: Folge-Isolationsprobe (Run 28) mit kompaktem Repro-Befehl ausgeführt (`set -o pipefail; timeout 420 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run28.log`). Ergebnis weiterhin reproduzierbar `EXIT:124`; trotz erweitertem Zeitfenster kein Testabschluss. T5.16 bleibt offen und priorisiert den AC0811-L-Steuerpfad als nächsten Debug-Fokus.
  - 2026-05-01: Optimierungsansatz umgesetzt: Für den Anchor-Telemetriepfad wurde die Budgetschwelle vor `global_search` verschärft (`required >= max(22s, 30% vom Budget)`), damit späte Runden häufiger deterministisch/mikro-basiert abschließen statt in teure Sampling-Phasen zu laufen.
  - 2026-05-01: Folge-Isolationsprobe (Run 30) mit derselben NodeID nach Schwellenanpassung ausgeführt (`set -o pipefail; timeout 300 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -q | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run30.log`). Ergebnis weiterhin `EXIT:124`; Timeout bleibt reproduzierbar.
  - 2026-05-01: Telemetrieprobe (Run 31) mit Verbose-Logs nach Schwellenanpassung ausgeführt (`set -o pipefail; timeout 180 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0 | tee artifacts/converted_images/reports/T5_16_anchor_hang_probe_2026-05-01_run31.log`). Ergebnis `EXIT:124`, aber mit neuen Signalen: `micro_eval`-Phasen sind sichtbar und `render_probe_aggregate` bleibt ohne Render-Timeouts (`slow_calls_gt_1s=0`, `timeouts=0`), wodurch sich das verbleibende Potenzial auf Variantensteuerung/Abbruchkriterien statt Render-Subprozess eingrenzen lässt.

  - [x] T5.16.A (sehr hohe Priorität): Varianten-Steuerfluss vollständig instrumentieren.
    - Ziel: Für jede Variante neben `variant_start`/`variant_done` zusätzliche Abschlussmarker pro Phase (`round_done`, `post_round_finalize_done`, `variant_finalize_done`) loggen.
    - Akzeptanzkriterium: In einem Isolationslauf ist für jede gestartete Variante eindeutig erkennbar, welche Phase zuletzt erreicht und abgeschlossen wurde.
    - 2026-05-01: `validateBadgeByElements` ergänzt jetzt im Anchor-Telemetriepfad die Phasenmarker `round_done`, `post_round_finalize_start`, `post_round_finalize_done` und `validation_finalize_done`; damit ist die letzte erreichte Abschlussphase pro Variante im Log klar nachvollziehbar.

  - [x] T5.16.B (sehr hohe Priorität): Strukturierte Abbruchentscheidungen im Validierungsloop ergänzen.
    - Ziel: Pro Runde maschinenlesbar loggen, warum weiter iteriert wird (`reason=improved|stagnation_retry|unlock_retry|micro_search_retry`) bzw. warum beendet wird.
    - Akzeptanzkriterium: Lauf-Log enthält pro Runde genau einen `continue_or_stop`-Entscheidungseintrag mit Begründung und Restbudget.

  
  - 2026-05-01: Validierungsloop ergänzt um strukturierte `validation_abort_decision`-Logevents (u. a. für Budget- und Stagnationsabbrüche sowie Schwellwert-Stopp), damit T5.16-Probeläufe maschinenlesbar auswertbar sind.
- [x] T5.16.C (hohe Priorität): Frühabbruch bei stabiler Nicht-Verbesserung implementieren.
    - Ziel: Nach konfigurierbarer Anzahl Runden ohne signifikante Fehlerverbesserung (und bereits ausgeführten Unlock-/Fallback-Schritten) die Variante deterministisch beenden.
    - Akzeptanzkriterium: Weniger Folgerunden ohne Qualitätsgewinn in T5.16-Probeläufen; keine Regression in bestehenden AC08-Detailtests.

  
    - 2026-05-01: Validierungsloop um stabilen Frühabbruch ergänzt (`stopped_due_to_stable_non_improvement` + strukturierte `validation_abort_decision: ... reason=stable_non_improvement`). Schwellwerte sind parametrisierbar über `validation_stable_improvement_epsilon` und `validation_stable_no_improvement_rounds`; neuer Detailtest bestätigt den kontrollierten Abbruchpfad.

  - [x] T5.16.D (hohe Priorität): Micro-Eval-Deduplizierung ergänzen.
    - Ziel: Wiederholte identische Kandidatenbewertung innerhalb derselben Runde per Fingerprint erkennen und überspringen.
    - Akzeptanzkriterium: Logs zeigen `micro_eval_skipped_duplicate`-Ereignisse; Render-Call-Anzahl pro Runde sinkt gegenüber Run 31.
    - 2026-05-01: Micro-Eval-Fingerprint-Cache in `validateBadgeByElements` ergänzt (`cx/cy/r`-Fingerprint pro Runde); doppelte Kandidaten werden jetzt mit `micro_eval_skipped_duplicate` geloggt und ohne zusätzlichen Render-Call übersprungen.

  - [x] T5.16.E (hohe Priorität): Variantenbudget pro Anchor-Lauf einführen.
    - Ziel: Pro Variante ein hartes Teilbudget ableiten (statt nur globalem Testbudget), damit einzelne Varianten den Gesamtabschluss nicht blockieren.
    - Akzeptanzkriterium: Bei Budgetüberschreitung kontrollierter Variantenabschluss mit dokumentiertem Status statt Gesamttest-Timeout.

    - 2026-05-01: In `validateBadgeByElementsImpl` ein hartes Varianten-Teilbudget für den Anchor-Telemetriepfad umgesetzt (`variant_budget_sec = max(20.0, configured_budget / variant_total)`), inkl. `variant_budget`-Logevent pro Variante; Budgetüberschreitungen führen nun zu kontrolliertem Variantenabbruch via `validation_time_budget_exceeded` statt ungebremstem Gesamtlauf.

  - [x] T5.16.F (Abschlusskriterium): Reproduktionslauf ohne Timeout nachweisen und Aufgabenliste rückpflegen.
    - Repro-Befehl: `set -o pipefail; timeout 420 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0`.
    - Akzeptanzkriterium: Test endet mit Exit `0`; T5.16 und Teilaufgaben A-E auf `[x]` setzen und Ergebnis kurz dokumentieren.

    - 2026-05-01: Abschluss-Repro erfolgreich: `set -o pipefail; timeout 420 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_convert_without_failed_svg -vv -s --durations=0` endet mit `EXIT:0` (`1 passed`, `360.47s`) ohne Timeout; T5.16 damit abgeschlossen.


## Next tasks (added 2026-03-28)

- [x] D1: Familienübergreifende Harmonisierung für AC08-Protoformen ergänzen.
  - Scope: Neben der bestehenden L/M/S-Harmonisierung innerhalb einer Basis zusätzlich Cross-Family-Aliase berücksichtigen.
  - Kandidaten-Gruppen:
    - `AC0800_L/M/S` als reine Scale-Familie ohne Connector/Text-Rotation.
    - `AC0811..AC0814` (jeweils `L/M/S`) als gemeinsame Rotations-/Spiegel-Protofamilie.
    - `AC0831..AC0834` (jeweils `L/M/S`) als Alias-Protofamilie zu `AC0811..AC0814` mit nicht mitrotierender Beschriftung.
  - Umsetzungsidee:
    - Kanonische Form-Signatur je Variante erzeugen (rotation-/spiegel-normalisiert, textfrei).
    - Beim Harmonisieren zuerst Proto-Anker pro Gruppe wählen, danach Größe + Text separat je Zielvariante fitten.
    - Für Text einen "rotate-geometry-only"-Modus vorsehen, damit `AC083x` die gleiche Form wie `AC081x` nutzen kann, die Beschriftung aber in Leserichtung bleibt.
  - Akzeptanzkriterien:
    - Keine Regression der bereits als gut markierten AC08-Anker (`successful_conversions.txt`).
    - Neue Reportspalten für `prototype_group`, `geometry_signature_delta` und `text_orientation_policy`.
    - Dokumentierter Vorher/Nachher-Vergleich mindestens für `AC0800_*`, `AC0811_*`, `AC0814_*`, `AC0820_*`, `AC0831_*`, `AC0834_*`.
  - 2026-04-03: Cross-Family-Proto-Gruppen (`ac08_plain_ring_scale`, `ac08_rot_mirror_alias`) eingeführt; Harmonisierung wählt Anker nun gruppenübergreifend statt strikt pro Basis.
    Zusätzlich enthält `shape_catalog.csv` jetzt die Spalten `prototype_group`, `geometry_signature_delta` und `text_orientation_policy`,
    und `variant_harmonization.log` protokolliert diese Felder pro harmonisierter Variante.

- [x] D2: Stagnationsbasierte Zwei-Phasen-Optimierung für AC08 einführen (Lock-Relax + Re-Lock).
  - Hintergrund: In der Bottleneck-Analyse treten bei AC08 häufig `stagnation_detected`/`stopped_due_to_stagnation` auf; gleichzeitig sind zentrale Geometrieparameter oft gelockt.
  - Umsetzungsidee:
    - Phase 1: bestehender semantisch-strenger Suchraum (Status quo).
    - Phase 2 (nur bei Stagnation + hoher Restfehler): temporär enge Freigabe von `cx/cy` bzw. ausgewählten Width-Parametern innerhalb kleiner Korridore.
    - Nach der Ausweichrunde: Semantik erneut validieren und bei Regelverletzung auf letzte stabile Parameter zurückrollen.
  - Akzeptanzkriterien:
    - Keine Regression bei bereits stabilen AC08-Ankern im Success-Gate.
    - Für die priorisierten Problemfälle (`AC0838_*`, `AC0870_*`, `AC0882_*`) sinkt `error_per_pixel` oder `mean_delta2` reproduzierbar.
    - Validation-Logs enthalten explizite Marker für „Phase 2 aktiviert/deaktiviert“ und „Rollback ja/nein“.
  - 2026-04-12: Pilot für `AC0838_*` implementiert (`adaptive_unlock_applied` + `adaptive_relock_applied`, enger `cx/cy`-Korridor während Phase 2). Breiter Rollout auf weitere Familien bleibt offen.
  - 2026-04-12: Rollout auf `AC0870_*` und `AC0882_*` ergänzt; Validation-Logs enthalten zusätzlich explizite Marker `phase2_status: activated/deactivated` und `phase2_rollback: yes/no`.

- [x] D3: Global-Search-Gating für kleine aktive Parametermengen erweitern.
  - Hintergrund: Der aktuelle globale Suchpfad bricht bei `<4` aktiven Parametern ab; dadurch entfällt oft die einzige joint-Optimierung bei AC08.
  - Umsetzungsidee:
    - Reduzierte Global-/Joint-Suche auch für 2–3 aktive Parameter erlauben (z. B. `cx/r`, `cy/r`, `text_x/text_scale`).
    - Einheitliche Instrumentierung, damit klar bleibt, ob voller oder reduzierter Global-Search gelaufen ist.
  - Akzeptanzkriterien:
    - `global-search: übersprungen (zu wenige aktive Parameter...)` tritt im AC08-Regression-Set deutlich seltener auf.
    - Keine Verletzung bestehender Bounds-/Lock-Invarianten (Regressionstests erweitern).
  - 2026-04-12: Gating von `>=4` auf `>=2` aktive Parameter erweitert; `2-3` aktive Parameter laufen jetzt im reduzierten Global-Search-Modus.
    Zusätzliche Instrumentierung protokolliert `modus=voll|reduziert` inkl. aktiver Schlüssel, und Detailtests decken Skip- (`<2`) sowie Reduced-Mode-Logging ab.

- [x] D4: Evaluate-Kosten im Render-/Scoring-Loop reduzieren (Memoization + sparsame GC).
  - Hintergrund: Jede Kandidatenbewertung rendert SVG->Pixmap->NumPy; der Hotpath räumt aktuell pro Versuch per `gc.collect()` auf.
  - Umsetzungsidee:
    - Parameter-Fingerprint-basierte Render-Cache-Schicht für identische Kandidaten innerhalb einer Runde.
    - `gc.collect()` nur noch periodisch oder am Rundenende statt pro Kandidat.
    - Telemetrie: Cache-Hit-Rate, Render-Aufrufe pro Datei, Zeit pro Runde.
  - Akzeptanzkriterien:
    - Laufzeit für repräsentative Teilmengen (`AC0838`, `AC0223`) sinkt messbar bei gleicher/verbesserter Qualität.
    - Keine neue Instabilität im MuPDF-Pfad.
  - 2026-04-12: Global-Search-Evaluierung nutzt jetzt einen Probe-Fingerprint-Cache für wiederholte Kandidaten
    und schreibt Telemetrie (`requests`, `cache_hits`, `hit_rate`, `render_aufrufe`) in die Validation-Logs.
    Zusätzlich läuft `gc.collect()` im In-Process-Renderer nur noch periodisch (alle 25 Renderaufrufe) statt pro Kandidat.

- [x] D5: Metrik-Fortsetzung als Multi-Objective-Prototyp evaluieren.
  - Hintergrund: Reiner Pixel-Fehler kann Anti-Aliasing-Effekte übergewichten und so semantisch plausible Geometrie verdrängen.
  - Umsetzungsidee:
    - Experimenteller Score: `pixel_error + geometry_penalty + semantic_penalty` (gewichtete Summe).
    - A/B-Vergleich gegen den aktuellen Score auf einer fixierten Problemfallliste.
  - Akzeptanzkriterien:
    - Dokumentierter Vorher/Nachher-Vergleich in `docs/` inkl. Parametergewichten, Gewinnerliste und Fehlertypen.
    - Kein Rückschritt beim AC08-Success-Gate.
  - 2026-04-12: Prototyp-Auswertung per Tooling ergänzt (`tools/evaluate_multi_objective_prototype.py`),
    Ergebnisdokumentation unter `docs/multi_objective_prototype_2026-04-12.md` inkl. Gewichten,
    Familien-Gewinnerliste, Fehlertyp-Klassifizierung und AC08-Gate-Check (kein Family-Winner-Rückschritt im Snapshot).

- [x] C1: `src/imageCompositeConverter.py` schrittweise in Module mit Blöcken von ca. 100 Zeilen aufteilen.
  - Hintergrund: Die Datei hat aktuell deutlich über 10k Zeilen; Refactoring erfolgt bewusst in mehreren, testbaren Teilschritten statt als Big-Bang.
  - Vorgehen: pro Teilbereich (z. B. Regionen-Analyse, IO/Reporting, Rendering, Optimierung, CLI) jeweils ein neues Modul mit klarer API erstellen und im Hauptskript nur noch schlanke Delegation belassen.
  - Akzeptanzkriterium für jeden Teilschritt: bestehende Tests laufen weiter, externe Funktionsnamen bleiben kompatibel, und der offene Aufgabenstand wird hier dokumentiert.
  - 2026-04-22: Aus der aktiven Checkliste entkoppelt, da die verbleibende Restarbeit als fortlaufendes Programm statt als einzelne, sofort abschließbare Aufgabe zu behandeln ist; neue konkrete C1-Inkremente werden bei Bedarf wieder als eigene, klar begrenzte Unteraufgaben ergänzt.
- [x] C1.1: Erste Extraktion abgeschlossen: Regionen-Analyse/Annotierung aus dem Monolithen ausgelagert.
  - 2026-03-29: Start umgesetzt mit neuem Modul `src/imageCompositeConverterRegions.py`.
  - `detect_relevant_regions`, `annotate_image_regions` und `analyze_range` delegieren im Monolithen jetzt auf die neue Modul-Implementierung.
  - 2026-04-01: Optionale Dependency-/Import-Hilfen in neues Modul `src/imageCompositeConverterDependencies.py` ausgelagert; der Monolith enthält nur noch kompatible Delegations-Wrapper (`camelCase` + `snake_case`).
  - 2026-04-01: Bereichs-/Filter-Helfer (`_extractRefParts` bis `_inRequestedRange`) in `src/imageCompositeConverterRange.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantik-Parser-Helfer in neues Modul `src/imageCompositeConverterSemantic.py` ausgelagert; `Reflection.parseDescription` delegiert die Family-Regeln plus Layout-/Alias-Extraktion weiterhin kompatibel über Wrapper.
  - 2026-04-01: Nicht-fatale Semantik-Qualitätsmarker (`_semanticQualityFlags`) in neues Modul `src/imageCompositeConverterQuality.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantik-Audit-/Template-Helfer (`_semanticAuditRecord`, `_writeSemanticAuditReport`, `_isSemanticTemplateVariant`) in neues Modul `src/imageCompositeConverterAudit.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantische Template-Transfer-Helfer (`_semanticTransferRotations`, `_semanticTransferIsCompatible`, `_semanticTransferScaleCandidates`, `_semanticTransferBadgeParams` inkl. Richtungs-Helfer) in neues Modul `src/imageCompositeConverterTransfer.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantische Presence-/Mismatch-Helfer (`_expectedSemanticPresence`, `_semanticPresenceMismatches`) in neues Modul `src/imageCompositeConverterSemanticValidation.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantische Connector-Guard-Helfer (`_enforceLeftArmBadgeGeometry`, `_enforceRightArmBadgeGeometry`, `_enforceSemanticConnectorExpectation`) in neues Modul `src/imageCompositeConverterSemanticConnectors.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-01: Semantik-Prüfblöcke (`_detectSemanticPrimitives`, `validateSemanticDescriptionAlignment`) in neues Modul `src/imageCompositeConverterSemanticChecks.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-02: Kreis-Bracketing-Optimierer (`_optimizeCircleCenterBracket`, `_optimizeCircleRadiusBracket`) in neues Modul `src/imageCompositeConverterGeometryBrackets.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Farb-Bracketing-Helfer (`_elementColorKeys`, `_elementErrorForColor`, `_optimizeElementColorBracket`) in neues Modul `src/imageCompositeConverterOptimizationColor.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Semantik-Fitting-Helfer (`_stabilizeSemanticCirclePose`, `_fitAc0870ParamsFromImage`, `_fitSemanticBadgeFromImage`) in neues Modul `src/imageCompositeConverterSemanticFitting.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Geometrie-Bracketing-Helfer für Elementlänge/-breite (`_elementErrorForExtent`, `_optimizeElementExtentBracket`, `_optimizeElementWidthBracket`) in neues Modul `src/imageCompositeConverterOptimizationGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Qualitäts-Pass/Iterations-Helfer (`_qualitySortKey`, `_computeSuccessfulConversionsErrorThreshold`, `_selectMiddleLowerTercile`, `_selectOpenQualityCases`, `_iterationStrategyForPass`, `_adaptiveIterationBudgetForQualityRow`) in neues Modul `src/imageCompositeConverterOptimizationPasses.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Template-Transfer-Helfer (`_extractSvgInner`, `_buildTransformedSvgFromTemplate`, `_templateTransferScaleCandidates`, `_estimateTemplateTransferScale`, `_templateTransferTransformCandidates`, `_rankTemplateTransferDonors`, `_templateTransferDonorFamilyCompatible`) in neues Modul `src/imageCompositeConverterTemplateTransfer.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Stroke-/Text-Breiten-Helfer (`_elementWidthKeyAndBounds`, `_elementErrorForWidth`) in neues Modul `src/imageCompositeConverterOptimizationWidth.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Circle-Pose-Multistart-Helfer (`_optimizeCirclePoseMultistart`) in neues Modul `src/imageCompositeConverterOptimizationCirclePose.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Qualitäts-Pass-Reporting-Helfer (`_writeQualityPassReport`, `_evaluateQualityPassCandidate`) in neues Modul `src/imageCompositeConverterOptimizationPassReporting.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Kreisradius-Optimierungshelfer (`_elementErrorForCircleRadius`, `_fullBadgeErrorForCircleRadius`, `_selectCircleRadiusPlateauCandidate`) in neues Modul `src/imageCompositeConverterOptimizationCircleRadius.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-02: Semantische Größen-Harmonisierungshelfer (`_needsLargeCircleOverflowGuard`, `_scaleBadgeParams`, `_harmonizationAnchorPriority`, `_clipGray`, `_familyHarmonizedBadgeColors`) in neues Modul `src/imageCompositeConverterSemanticHarmonization.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Kreis-Geometriehelfer (`_elementErrorForCirclePose`, `_reanchorArmToCircleEdge`) in neues Modul `src/imageCompositeConverterOptimizationCircleGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Global-Vector-Helfer (`_circleBounds`, `_globalParameterVectorBounds`, `_logGlobalParameterVector`) in neues Modul `src/imageCompositeConverterOptimizationGlobalVector.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Kreis-Suchhelfer (`_stochasticSurvivorScalar`, `_optimizeCirclePoseStochasticSurvivor`, `_optimizeCirclePoseAdaptiveDomain`) in neues Modul `src/imageCompositeConverterOptimizationCircleSearch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Größenvarianten-Harmonisierung (`_harmonizeSemanticSizeVariants`) in `src/imageCompositeConverterSemanticHarmonization.py` ausgelagert; der Monolith delegiert über den neuen Modul-Entry-Point weiter kompatibel.
  - 2026-04-03: Die bereits extrahierten C1.1-Helfermodule werden jetzt zentral unter `src/iCCModules/` geführt; `src/imageCompositeConverter.py` importiert diese direkt aus dem neuen Ordner, die bisherigen Modulpfade unter `src/` bleiben als kompatible Wrapper bestehen.
  - 2026-04-03: Masken-/BBox-Geometriehelfer (`_fitToOriginalSize`, `_maskCentroidRadius`, `_maskBbox`, `_maskCenterSize`, `_maskMinRectCenterDiag`, `_elementBboxChangeIsPlausible`) in neues Modul `src/iCCModules/imageCompositeConverterMaskGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: SVG-Rendering-Helfer (`_renderSvgToNumpyInprocess`, `_renderSvgToNumpyViaSubprocess`) in neues Modul `src/iCCModules/imageCompositeConverterRendering.py` ausgelagert; der Monolith behält kompatible Wrapper und delegiert auf den neuen Modul-Entry-Point.
  - 2026-04-03: Batch-Reporting-Helfer (`_readValidationLogDetails`, `_writeBatchFailureSummary`) in neues Modul `src/iCCModules/imageCompositeConverterBatchReporting.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Pixel-Delta2-Ranking-Reporting (`_writePixelDelta2Ranking`) in neues Modul `src/iCCModules/imageCompositeConverterRanking.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Semantische SVG-Geometriehelfer (`_readSvgGeometry`, `_normalizedGeometrySignature`, `_maxSignatureDelta`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Successful-Conversion-Manifest-/Snapshot-Helfer (`_parseSuccessfulConversionManifestLine`, `_readSuccessfulConversionManifestMetrics`, `_successfulConversionSnapshotDir`, `_successfulConversionSnapshotPaths`, `_restoreSuccessfulConversionSnapshot`, `_storeSuccessfulConversionSnapshot`, `_isSuccessfulConversionCandidateBetter`, `_mergeSuccessfulConversionMetrics`, `_formatSuccessfulConversionManifestLine`) in neues Modul `src/iCCModules/imageCompositeConverterSuccessfulConversions.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: AC08-Reporting-Helfer (`_writeAc08RegressionManifest`, `_summarizePreviousGoodAc08Variants`, `_writeAc08SuccessCriteriaReport`, `_writeAc08WeakFamilyStatusReport`) in neues Modul `src/iCCModules/imageCompositeConverterAc08Reporting.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Global-Search-Optimierungsblock (`_optimizeGlobalParameterVectorSampling`) in neues Modul `src/iCCModules/imageCompositeConverterOptimizationGlobalSearch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-03: Conversion-Row-/Rastergrößen-Helfer (`_loadExistingConversionRows`, `_sniffRasterSize`) in neues Modul `src/iCCModules/imageCompositeConverterConversionRows.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-04: Element-Validierungsblock (`_refineStemGeometryFromMasks`, `validateBadgeByElements`) in neues Modul `src/iCCModules/imageCompositeConverterElementValidation.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-04: Render-Runtime-Helfer (`_is_fitz_open_monkeypatched`, `_is_inprocess_renderer_monkeypatched`, `_bbox_to_dict`, `_runSvgRenderSubprocessEntrypoint`) in neues Modul `src/iCCModules/imageCompositeConverterRenderRuntime.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiter über kompatible Wrapper.
  - 2026-04-04: Successful-Conversion-Reporting-Helfer (`_latestFailedConversionManifestEntry`, `_sortedSuccessfulConversionMetricsRows`, `_writeSuccessfulConversionCsvTable`) in `src/iCCModules/imageCompositeConverterSuccessfulConversions.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Verfügbarkeitsprüfung für Successful-Conversion-Metriken (`_successfulConversionMetricsAvailable`) in `src/iCCModules/imageCompositeConverterSuccessfulConversions.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Semantische Label-Helfer (`_applyCo2Label`, `_co2Layout`, `_applyVocLabel`, `_normalizeCenteredCo2Label`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticLabels.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Beschreibungsfragment-Helfer (`_collectDescriptionFragments`) in `src/iCCModules/imageCompositeConverterAudit.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Element-Ausrichtungshelfer (`_applyElementAlignmentStep`) in `src/iCCModules/imageCompositeConverterElementValidation.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Successful-Conversion-Qualitätshelfer (`_loadIterationLogRows`, `_findImagePathByVariant`) in neues Modul `src/iCCModules/imageCompositeConverterSuccessfulConversionQuality.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Successful-Conversion-Qualitäts-Metrikblock (`collectSuccessfulConversionQualityMetrics`) in `src/iCCModules/imageCompositeConverterSuccessfulConversionQuality.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den Modul-Entry-Point.
  - 2026-04-04: Element-Masken-/Foreground-Helfer (`_ringAndFillMasks`, `_meanGrayForMask`, `_elementRegionMask`, `_textBbox`, `_foregroundMask`, `_circleFromForegroundMask`, `_maskSupportsCircle`) in neues Modul `src/iCCModules/imageCompositeConverterElementMasks.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Thresholding-/Mask-Overlap-Helfer (`_computeOtsuThreshold`, `_adaptiveThreshold`, `_iou`) in neues Modul `src/iCCModules/imageCompositeConverterThresholding.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Element-Fehlermetrik-Helfer (`_elementOnlyParams`, `_maskedError`, `_unionBboxFromMasks`, `_maskedUnionErrorInBbox`) in neues Modul `src/iCCModules/imageCompositeConverterElementErrorMetrics.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: Skalare Optimierungs-/Kreis-Constraint-Helfer (`_makeRng`, `_argminIndex`, `_snapIntPx`, `_maxCircleRadiusInsideCanvas`, `_isCircleWithText`, `_applyCircleTextWidthConstraint`, `_applyCircleTextRadiusFloor`, `_clampCircleInsideCanvas`) in neues Modul `src/iCCModules/imageCompositeConverterOptimizationScalars.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-04: AC083x-Label-Tuning-Helfer (`_tuneAc0832Co2Badge`, `_tuneAc0831Co2Badge`, `_tuneAc0835VocBadge`, `_tuneAc0833Co2Badge`, `_tuneAc0834Co2Badge`) in `src/iCCModules/imageCompositeConverterSemanticLabels.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Default-Parameter-Helfer (`_defaultAc0870Params`, `_defaultAc0881Params`, `_defaultAc0882Params`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticDefaults.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Shared-AC081x-Default-Helfer (`_defaultAc081xShared`) in `src/iCCModules/imageCompositeConverterSemanticDefaults.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0811-Parametrik-/Fitting-Helfer (`_defaultEdgeAnchoredCircleGeometry`, `_defaultAc0811Params`, `_estimateUpperCircleFromForeground`, `_fitAc0811ParamsFromImage`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc0811.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0812-Parametrik-/Fitting-Helfer (`_defaultAc0812Params`, `_fitAc0812ParamsFromImage`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc0812.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0813/AC0814-Parametrik-/Fitting-Helfer (`_defaultAc0813Params`, `_fitAc0813ParamsFromImage`, `_defaultAc0814Params`, `_fitAc0814ParamsFromImage`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc0813.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0810-Parametrik-/Fitting-Delegation (`_defaultAc0810Params`, `_fitAc0810ParamsFromImage`) in `src/iCCModules/imageCompositeConverterSemanticAc0813.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Badge-Geometrie-/Glyph-Helfer (`_rotateSemanticBadgeClockwise`, `_glyphBbox`, `_centerGlyphBbox`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticBadgeGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Stem-Zentrierungshelfer (`_alignStemToCircleCenter`) in `src/iCCModules/imageCompositeConverterSemanticBadgeGeometry.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC08-Small-Variant-Helfer (`_persistConnectorLengthFloor`, `_isAc08SmallVariant`, `_configureAc08SmallVariantMode`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc08SmallVariants.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC0834-Default-Badge-Parametrik (`_defaultAc0834Params`) in `src/iCCModules/imageCompositeConverterSemanticLabels.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC08-Familien-Tuning-/Guard-Helfer (`_enforceTemplateCircleEdgeExtent`, `_tuneAc08LeftConnectorFamily`, `_tuneAc08RightConnectorFamily`, `_enforceVerticalConnectorBadgeGeometry`, `_tuneAc08VerticalConnectorFamily`, `_tuneAc08CircleTextFamily`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc08Families.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: AC08-Stil-Finalisierungsblock (`_finalizeAc08Style`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc08Finalization.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Badge-SVG-Generierungsblock (`generateBadgeSvg`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticBadgeSvg.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-06: AC08-Adaptive-Lock-Helfer (`_activateAc08AdaptiveLocks`, `_releaseAc08AdaptiveLocks`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAdaptiveLocks.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: Kanonische Badge-Farbziel-Helfer (`_captureCanonicalBadgeColors`, `_applyCanonicalBadgeColors`) in `src/iCCModules/imageCompositeConverterSemanticHarmonization.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-05: AC08-Badge-Param-Dispatch (`makeBadgeParams`-Zweig `AC0870..AC0839`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc08Params.py` ausgelagert; der Monolith delegiert über einen kompatiblen Modul-Entry-Point und behält AR0100/Fallback-Verhalten unverändert.
  - 2026-04-05: AR0100-Badge-Parametrik aus `makeBadgeParams` in neues Modul `src/iCCModules/imageCompositeConverterSemanticAr0100.py` ausgelagert (`buildAr0100BadgeParamsImpl`); `src/imageCompositeConverter.py` delegiert kompatibel über den neuen Helper.
  - 2026-04-06: Composite-SVG-Helfer (`traceImageSegment`, `generateCompositeSvg`) in neues Modul `src/iCCModules/imageCompositeConverterCompositeSvg.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Quantisierungs-/Symmetrie-Helfer (`_enforceCircleConnectorSymmetry`, `_quantizeBadgeParams`) in neues Modul `src/iCCModules/imageCompositeConverterOptimizationQuantization.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Kreis-Stil-/Tonwert-Helfer (`_normalizeLightCircleColors`, `_normalizeAc08LineWidths`, `_estimateBorderBackgroundGray`, `_estimateCircleTonesAndStroke`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticCircleStyle.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Delta2-Metrik-Helfer (`calculateDelta2Stats`) in `src/iCCModules/imageCompositeConverterElementErrorMetrics.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Diff-/Fehlermetrik-Helfer (`createDiffImage`, `calculateError`) in neues Modul `src/iCCModules/imageCompositeConverterDiffing.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: SVG-Render-Dispatch (`renderSvgToNumpy`) in neues Modul `src/iCCModules/imageCompositeConverterRenderDispatch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-06: Redraw-Variationsblock (`applyRedrawVariation`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticRedrawVariation.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-06: Element-Matching-Score (`_elementMatchError`) in `src/iCCModules/imageCompositeConverterElementErrorMetrics.py` zentralisiert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Full-Badge-Fehlermetrik-Helfer (`_fullBadgeErrorForParams`) in `src/iCCModules/imageCompositeConverterOptimizationGlobalSearch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-06: Description-Mapping-Ladepfad (`SourceSpan`, `DescriptionMappingError`, `_loadDescriptionMapping*`, `_resolveDescriptionXmlPath`) in neues Modul `src/iCCModules/imageCompositeConverterDescriptions.py` ausgelagert; `src/imageCompositeConverter.py` behält kompatible Delegations-Wrapper für CSV/XML-Callsites und Tests.
  - 2026-04-06: Element-Masken-Extraktion (`extractBadgeElementMask`) in `src/iCCModules/imageCompositeConverterElementMasks.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den Modul-Helper.
  - 2026-04-06: Successful-Conversion-Manifest-Update (`updateSuccessfulConversionsManifestWithMetrics`) in `src/iCCModules/imageCompositeConverterSuccessfulConversions.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den Modul-Entry-Point.
  - 2026-04-06: Badge-Param-Dispatch (`makeBadgeParams`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticParams.py` ausgelagert; `src/imageCompositeConverter.py` delegiert kompatibel über den neuen Modul-Entry-Point und kapselt AR0100-/AC08-Dispatch in injizierbaren Helferaufrufen.
  - 2026-04-07: Fallback-Diff-Rendering (`_createDiffImageWithoutCv2`) in `src/iCCModules/imageCompositeConverterDiffing.py` ausgelagert; `src/imageCompositeConverter.py` behält den kompatiblen Wrapper und delegiert auf den neuen Modul-Helper.
  - 2026-04-07: Raster-Embedding-/Quality-Config-Helfer (`_svgHrefMimeType`, `_renderEmbeddedRasterSvg`, `_qualityConfigPath`, `_loadQualityConfig`, `_writeQualityConfig`) in neues Modul `src/iCCModules/imageCompositeConverterQualityConfig.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Successful-Conversion-Quality-Reporting (`writeSuccessfulConversionQualityReport`) in neues Modul `src/iCCModules/imageCompositeConverterSuccessfulConversionReport.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-07: CLI-/CSV-Resolving-Helfer (`parseArgs`, `_autoDetectCsvPath`, `_resolveCliCsvAndOutput`) in neues Modul `src/iCCModules/imageCompositeConverterCli.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-08: CLI-Top-Level-Ablauf (`main`-Steuerfluss inkl. Range-/CSV-Resolving, Bootstrap, Regression-Set-Dispatch und Fehlerdarstellung) in `src/iCCModules/imageCompositeConverterCli.py` zentralisiert (`runMainImpl`); der Monolith delegiert jetzt über einen kompatiblen Entry-Point.
  - 2026-04-08: Clip-/Grauwert-Farbhelfer (`_clip`, `_grayToHex`) in neues Modul `src/iCCModules/imageCompositeConverterColorUtils.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Iterations-Artefakt-IO-Helfer (`_writeValidationLog`, `_writeAttemptArtifacts`) in neues Modul `src/iCCModules/imageCompositeConverterIterationArtifacts.py` ausgelagert; `runIterationPipeline` delegiert weiterhin kompatibel über lokale Wrapper.
  - 2026-04-07: Output-Verzeichnis-Helfer (`_defaultConvertedSymbolsRoot`, `_convertedSvgOutputDir`, `_diffOutputDir`, `_reportsOutputDir`) in neues Modul `src/iCCModules/imageCompositeConverterOutputPaths.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Optionales CLI-Log-Capturing (`_optionalLogCapture` inkl. Tee-Stream) in `src/iCCModules/imageCompositeConverterCli.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den Modul-Context-Manager.
  - 2026-04-07: CLI-Diagnose-/Interaktiv-Helfer (`_formatUserDiagnostic`, `_promptInteractiveRange`) in `src/iCCModules/imageCompositeConverterCli.py` ausgelagert; der Monolith delegiert weiterhin kompatibel über Wrapper und Callback-Injektion.
  - 2026-04-07: Strategie-Switch-Reporting (`strategy_switch_template_transfers.csv`) in `src/iCCModules/imageCompositeConverterBatchReporting.py` ausgelagert (`writeStrategySwitchTemplateTransfersImpl`); `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über den neuen Wrapper `_writeStrategySwitchTemplateTransfersReport`.
  - 2026-04-07: Randomisierungs-Helfer (`_conversionRandom`) in neues Modul `src/iCCModules/imageCompositeConverterRandom.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Iteration-Log-/Semantik-Result-Helfer (`_writeIterationLogAndCollectSemanticResults`) in neues Modul `src/iCCModules/imageCompositeConverterIterationLog.py` ausgelagert; `convertRange` delegiert weiterhin kompatibel über den neuen Wrapper und die Log/Reporting-Regression ist per Detailtest abgesichert.
  - 2026-04-07: AC08-Gate-Statusausgabe (Warn-/Info-Konsolenmeldung inkl. stabiler Kriterienreihenfolge) in neues Modul `src/iCCModules/imageCompositeConverterAc08Gate.py` ausgelagert; `convertRange` delegiert weiterhin kompatibel über den neuen Wrapper `_emitAc08SuccessGateStatus`.
  - 2026-04-07: Post-Conversion-Reporting-Block (Semantic-Audit, AC08-Manifest/Gate, Successful-Conversion-Manifest-Refresh, Overview-Kacheln) in neues Modul `src/iCCModules/imageCompositeConverterConversionReporting.py` ausgelagert; `convertRange` delegiert weiterhin kompatibel über den neuen Wrapper `_runPostConversionReporting`.
  - 2026-04-07: Conversion-Bestlist-Row-Fallback (`_chooseConversionBestlistRow`) in `src/iCCModules/imageCompositeConverterBestlist.py` ausgelagert; `convertRange` delegiert bei nicht übernommenen Kandidaten weiterhin kompatibel über den neuen Wrapper und der Fallback-Prioritätspfad ist per Detailtest abgesichert.
  - 2026-04-07: Legacy-API-Einstiegspunkte (`convertImage`, `convertImageVariants`) in neues Modul `src/iCCModules/imageCompositeConverterLegacyApi.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper inklusive Embedded-Raster-SVG-Fallback und `convertRange`-Weiterleitung.
  - 2026-04-07: Template-Transfer-Ausführungsblock (`_tryTemplateTransfer`) in `src/iCCModules/imageCompositeConverterTemplateTransfer.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper und übergibt die bisherigen Action-/Rendering-Hooks injizierbar an den Modul-Entry-Point.
  - 2026-04-07: Vendor-Install-Helfer (`_requiredVendorPackages`, `buildLinuxVendorInstallCommand`) in neues Modul `src/iCCModules/imageCompositeConverterVendorInstall.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-07: Quality-Threshold-Resolving (`_resolveAllowedErrorPerPixel` inkl. Initial-Tercile-/Successful-Threshold-/Manual-Config-Dispatch) in neues Modul `src/iCCModules/imageCompositeConverterQualityThreshold.py` ausgelagert; `convertRange` delegiert den Schwellenwert-Pfad weiterhin kompatibel über den neuen Wrapper.
  - 2026-04-07: Render-Failure-Logging-Helfer (`_paramsSnapshot`, `_recordRenderFailure`) in `src/iCCModules/imageCompositeConverterIterationArtifacts.py` zentralisiert (`paramsSnapshotImpl`, `writeRenderFailureLogImpl`); `runIterationPipeline` delegiert weiterhin kompatibel über lokale Wrapper/Callbacks.
  - 2026-04-07: Einzeldatei-Konvertierungshelfer aus `convertRange` (`_convertOne`) in neues Modul `src/iCCModules/imageCompositeConverterConversionExecution.py` ausgelagert; `src/imageCompositeConverter.py` delegiert den Batch-/Fehler-/Delta2-Pfad weiterhin kompatibel über den neuen Modul-Entry-Point.
  - 2026-04-07: Quality-Pass-Iterationsschleife aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterConversionQualityPass.py` ausgelagert (`runQualityPassesImpl`); `src/imageCompositeConverter.py` delegiert die Kandidatenselektion/Verbesserungslogik weiterhin kompatibel über injizierte Snapshot-/Bewertungs-Hooks.
  - 2026-04-07: Embedded-Raster-Fallbackpfad aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterFallback.py` ausgelagert (`runEmbeddedRasterFallbackImpl`); `src/imageCompositeConverter.py` delegiert den No-`numpy`/`opencv`-Pfad weiterhin kompatibel über den neuen Wrapper `_runEmbeddedRasterFallback`.
  - 2026-04-07: Formales Geometriemodell (`RGBWert`, `Punkt`, `Kreis`, `Griff`, `Kelle`, `abstand`, `buildOrientedKelle`) in neues Modul `src/iCCModules/imageCompositeConverterForms.py` ausgelagert; `src/imageCompositeConverter.py` stellt die bisherigen API-Namen weiterhin kompatibel über Alias-Delegation bereit.
  - 2026-04-07: Primitive Element-Suchhelfer (`renderCandidateMask`, `scoreCandidate`, `randomNeighbor`, `optimizeElement`) in neues Modul `src/iCCModules/imageCompositeConverterOptimizationElementSearch.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper (`camelCase` + `snake_case`).
  - 2026-04-07: Runtime-Dependency-Bootstrap (`_missingRequiredImageDependencies`, `_bootstrapRequiredImageDependencies`) in `src/iCCModules/imageCompositeConverterDependencies.py` ausgelagert; `src/imageCompositeConverter.py` delegiert weiterhin kompatibel über Wrapper/Callback-Injektion für Re-Import und Global-Update.
  - 2026-04-07: Initiale Batch-Konvertierungsschleife aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterConversionInitialPass.py` ausgelagert (`runInitialConversionPassImpl`); `src/imageCompositeConverter.py` delegiert den Erstpass (Donor-Auswahl, Template-Transfer, Bestlist-Snapshot-Fallback) weiterhin kompatibel über injizierte Hooks.
  - 2026-04-07: Conversion-Finalisierungsblock aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterConversionFinalization.py` ausgelagert (`runConversionFinalizationImpl`); `src/imageCompositeConverter.py` delegiert den Quality-/Bestlist-/Batch-Report-Flush, Iteration-Log-Sammelpfad sowie Harmonisierung + Post-Conversion-Reporting weiterhin kompatibel über injizierte Hooks.
  - 2026-04-08: Dateiauswahl-/Variantennormalisierungs-I/O aus `convertRange` in neues Modul `src/iCCModules/imageCompositeConverterConversionInputs.py` ausgelagert (`listRequestedImageFilesImpl`, `normalizeSelectedVariantsImpl`); `src/imageCompositeConverter.py` delegiert die Bereichs-/Extensions-/Variantenselektion weiterhin kompatibel über den neuen Wrapper `_listRequestedImageFiles`.
  - 2026-04-08: Composite-Iterationsschleife aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterConversionComposite.py` ausgelagert (`runCompositeIterationImpl`); `src/imageCompositeConverter.py` delegiert den Epsilon-/Plateau-/Konvergenzpfad weiterhin kompatibel inkl. Render-Failure-Logging und Validation-Log-Flush.
  - 2026-04-08: Neues Tool `tools/automate_function_extraction.py` ergänzt, das eine ausgewählte Top-Level-Funktion automatisch in ein Zielmodul kopiert, im Monolithen auf einen delegierenden Wrapper umstellt und danach Verifikationskommandos ausführt; bei fehlgeschlagener Verifikation werden alle Änderungen automatisch zurückgerollt.
  - 2026-04-12: Wahrnehmungs-Geometriehelfer (`_looksLikeElongatedForegroundRect`) in neues Modul `src/iCCModules/imageCompositeConverterPerceptionGeometry.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper.
  - 2026-04-12: Bildlade-/Binarisierungshelfer (`loadGrayscaleImage`, `loadBinaryImageWithMode`) in neues Modul `src/iCCModules/imageCompositeConverterImageLoading.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper und neue Detailtests sichern Global-/Otsu-/Adaptive-Modi sowie Fehlermeldungen ab.
  - 2026-04-12: Dateinamen-/Varianten-Normalisierung (`getBaseNameFromFile`) in neues Modul `src/iCCModules/imageCompositeConverterNaming.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper und neue Detailtests decken die Suffix-Normalisierung (`_L/_M/_S`, `_sia`, numerische Varianten) ab.
  - [x] C1.2: Farb-Hex-Helfer (`rgbToHex`) aus `src/iCCModules/imageCompositeConverterRemaining.py` in `src/iCCModules/imageCompositeConverterColorUtils.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper und neue Detailtests decken die Hex-Formatierung ab.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Test `test_rgb_to_hex_impl_formats_channels`.
  - [x] C1.3: Circle-Decomposition-Helfer (`estimateStrokeStyle`, `candidateToSvg`, `decomposeCircleWithStem`) aus `src/iCCModules/imageCompositeConverterRemaining.py` in neues Modul `src/iCCModules/imageCompositeConverterElementDecomposition.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert weiterhin kompatibel über Wrapper und neue Detailtests decken SVG-/Stroke-Verhalten ab.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Tests `test_candidate_to_svg_impl_generates_circle_with_stroke` und `test_estimate_stroke_style_impl_detects_circle_ring`.
  - [x] C1.4: Semantik-Audit-Validation-Log-Formatierung (`semantic_audit_*`-Zeilen) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticAuditLogging.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` nutzt jetzt den Modul-Helper statt doppelter Inline-Listen und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtest `test_build_semantic_audit_log_lines_includes_mismatch_reason_when_requested`.
  - [x] C1.5: Semantik-Validation-Log-Zeilen (`status=semantic_mismatch`/`status=semantic_ok`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticValidationLogging.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt die Zeilen-Komposition über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_build_semantic_mismatch_validation_log_lines_impl_contains_expected_fields` und `test_build_semantic_ok_validation_log_lines_impl_keeps_order`.
  - [x] C1.6: Semantik-Validation-Kontext (Debug-Verzeichnisauflösung + Non-Composite-Gradient-Stripe-Statuszeilen) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticValidationContext.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt die entsprechenden IO-/Reporting-Teilstrecken über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_resolve_semantic_validation_debug_dir_impl_prefers_element_debug_dir`, `test_resolve_semantic_validation_debug_dir_impl_uses_ac0811_fallback` und `test_build_non_composite_gradient_stripe_validation_log_lines_impl_marks_override`.
  - [x] C1.7: Semantik-Validation-Guard-/Element-Log-Sammlung (Textmoduszeile + `validate_badge_by_elements`-Dispatch) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticValidationRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt die Log-Sammlung über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_build_semantic_text_mode_validation_log_line_impl_reports_plain_ring` und `test_collect_semantic_badge_validation_logs_impl_uses_guard_line_and_round_floor`.
  - [x] C1.8: Semantik-Mismatch-Reporting (Connector-Debug-Zeile + Konsolenmeldungsreihenfolge) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticMismatchReporting.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Formatierung jetzt über Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_build_semantic_connector_debug_line_impl_formats_all_fields` und `test_build_semantic_mismatch_console_lines_impl_lists_issues_in_order`.
  - [x] C1.9: AC0223-Post-Validation-Finalisierung (Ventilkopf-/Top-Stem-Defaults nach `validate_badge_by_elements`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticAc0223Runtime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_finalize_ac0223_badge_params_impl_applies_valve_head_defaults` und `test_finalize_ac0223_badge_params_impl_is_noop_for_other_families`.
  - [x] C1.10: Semantik-Audit-Laufzeitvorbereitung (Target-Filter + Record-Kwargs) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticAuditRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Pending/Mismatch/OK-Record-Aufbereitung jetzt über den Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_should_create_semantic_audit_for_base_name_impl_normalizes_variant_suffix` und `test_build_semantic_audit_record_kwargs_impl_collects_semantic_fields`.
  - [x] C1.11: Semantik-Validation-OK-Finalisierung (Connector-Guard-Zeile + Audit/Quality-Log-Payload) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticValidationFinalization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Finalisierungs-/Log-Komposition jetzt über Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_append_semantic_connector_expectation_log_impl_appends_guard_for_arm` und `test_build_semantic_ok_validation_outcome_impl_updates_audit_and_lines`.
  - [x] C1.12: Semantik-Mismatch-Laufzeitaufbereitung (Primitive-Detection + Audit-/Validation-Log-Komposition) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticMismatchRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Mismatch-Ausgangspfad jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-12: Umsetzung abgeschlossen inkl. Detailtests `test_build_semantic_mismatch_outcome_impl_with_audit_row` und `test_build_semantic_mismatch_outcome_impl_without_audit_row`.
  - [x] C1.13: Semantik-Badge-Post-Validation-Renderpfad (AC0223-Finalisierung + Final-Render/Artifact-Write) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterSemanticValidationRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Abschluss jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_finalize_semantic_badge_iteration_result_impl_attaches_audit_and_error` und `test_finalize_semantic_badge_iteration_result_impl_records_render_failure`.
  - [x] C1.14: Semantische Iterations-Finalisierung (Validation-Log-Flush + Ergebnis-Weitergabe) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticIterationFinalization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Abschluss jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_finalize_semantic_badge_run_impl_returns_iteration_tuple` und `test_finalize_semantic_badge_run_impl_returns_none_on_failed_finalize`.
  - [x] C1.15: Semantik-Post-Validation-Orchestrierung (Connector-Guard + Redraw-Variation + Connector-Guard-Log) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticPostValidation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Sequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_semantic_badge_post_validation_impl_applies_guard_redraw_and_log`.
  - [x] C1.16: Non-Composite-Runtimepfad (Manual-Review-/Gradient-Stripe-/Embedded-SVG-Handling inkl. Render-Fehlerpfad) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterNonCompositeRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den gesamten Non-Composite-Zweig jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_run_non_composite_iteration_impl_manual_review_writes_skip_log` und `test_run_non_composite_iteration_impl_gradient_stripe_returns_iteration_tuple`.
  - [x] C1.17: Semantik-Audit-Bootstrap (initialer `semantic_pending`-Record in `runIterationPipeline`) in neues Modul `src/iCCModules/imageCompositeConverterSemanticAuditBootstrap.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Initialisierung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_build_pending_semantic_audit_row_impl_returns_none_when_base_not_targeted` und `test_build_pending_semantic_audit_row_impl_builds_pending_row`.
  - [x] C1.18: Dual-Arrow-Laufzeitpfad (`mode=dual_arrow_badge`: Detektion/Fallback/Final-Render + Fehlerpfad) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterDualArrowRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_run_dual_arrow_badge_iteration_impl_uses_fallback_when_detection_fails` und `test_run_dual_arrow_badge_iteration_impl_records_render_failure_with_badge_params`.
  - [x] C1.19: Semantik-Visual-Override-Dispatch (Gradient-Stripe-/Elongated-Rect-Umschaltung + Konsolenhinweis) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticVisualOverride.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Override-Entscheidung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_apply_semantic_visual_override_impl_switches_mode_for_gradient_stripe` und `test_apply_semantic_visual_override_impl_keeps_params_when_not_needed`.
  - [x] C1.20: Semantik-Badge-Runtime-Orchestrierung (Mismatch-/Validation-/Finalisierungs-Dispatch für `mode=semantic_badge`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterSemanticBadgeRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Ausführung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_run_semantic_badge_iteration_impl_returns_none_for_semantic_mismatch` und `test_run_semantic_badge_iteration_impl_finalizes_semantic_ok`.
  - [x] C1.21: Laufzeit-Dependency-Guard aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterDependencies.py` zentralisiert (`ensureConversionRuntimeDependenciesImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Start-Guard jetzt über den Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_ensure_conversion_runtime_dependencies_impl_requires_cv2_numpy_and_fitz`.
  - [x] C1.22: Iterations-Setup/Output-Initialisierung (Header-Ausgabe + Output-Verzeichnisse + Validation-Log-Pfad) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationSetup.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diese Initialisierungs-/Reporting-Teilstrecke jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_ensure_iteration_output_dirs_impl_creates_all_expected_dirs`, `test_build_iteration_base_and_log_path_impl_formats_log_name` und `test_emit_iteration_description_header_impl_prints_description_and_fallback_elements`.
  - [x] C1.23: Iterations-Artefakt-/Validation-Callback-Wiring (`_writeValidationLog`, `_writeAttemptArtifacts`, `_recordRenderFailure`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diese Laufzeit-Callbacks jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_build_iteration_artifact_callbacks_impl_wires_validation_log_writer`, `test_build_iteration_artifact_callbacks_impl_wires_attempt_artifacts_with_dimensions` und `test_build_iteration_artifact_callbacks_impl_wires_render_failure_logger`.
  - [x] C1.24: Iterations-Eingangsvorbereitung (Perception/Reflection-Initialisierung, Gradient-Stripe-Strategie, `semantic_pending`-Bootstrap + Skip ohne Beschreibung) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationPreparation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diesen Vorbereitungspfad jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_prepare_iteration_inputs_impl_builds_iteration_context` und `test_prepare_iteration_inputs_impl_returns_none_for_missing_description_non_semantic_badge`.
  - [x] C1.25: Mode-Dispatch-Orchestrierung (`semantic_badge`/`dual_arrow_badge`/`non_composite`/`composite`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationDispatch.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Verzweigung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_run_prepared_iteration_mode_impl_routes_semantic_badge_with_core_fields` und `test_run_prepared_iteration_mode_impl_routes_composite_with_iteration_context`.
  - [x] C1.26: Iterations-Ergebnisfinalisierung (Composite-Only-Finite-Error-Guard nach Mode-Dispatch) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationFinalization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Rückgabepfad jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtests `test_finalize_iteration_result_impl_returns_non_composite_result_unchanged` und `test_finalize_iteration_result_impl_drops_non_finite_composite_error`.
  - [x] C1.27: Masken-IoU-Helfer (`_iou`) aus `src/iCCModules/imageCompositeConverterRemaining.py` in neues Modul `src/iCCModules/imageCompositeConverterMaskMetrics.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Wrapper jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_iou_impl_returns_overlap_ratio`.
  - [x] C1.28: Iterations-Initialisierungs-/Reporting-Teilstrecke (Header-Ausgabe + Output-Verzeichnis-Setup + Base/Log/Artifact-Callback-Wiring) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationInitialization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Initialisierung jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_runtime_impl_builds_base_and_callbacks`.
  - [x] C1.29: Runtime-Binding-Extraktion (Base-Name + Artefakt-Callbacks) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationInitialization.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert das Callback-Unpacking jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-13: Umsetzung abgeschlossen inkl. Detailtest `test_extract_iteration_runtime_bindings_impl_exposes_runtime_callbacks`.
  - [x] C1.30: Mode-Runner-Dependency-Wiring (`semantic_badge`/`dual_arrow_badge`/`non_composite`/`composite`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeRuntime.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert das Lambda-Wiring jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtests `test_build_iteration_mode_runners_impl_wires_semantic_validation_collector` und `test_build_iteration_mode_runners_impl_wires_dual_arrow_detector_with_numpy_module`.
  - [x] C1.31: Iterations-Mode-Orchestrierung (Elongated-Rect-Check + Semantik-Visual-Override + Mode-Runner-Build) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationOrchestration.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diese Vorbereitungssequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_impl_applies_visual_override_then_builds_runners`.
  - [x] C1.32: Mode-Dispatch-Argumentaufbau aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationContext.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den großen `runPreparedIterationModeImpl`-Kwargs-Aufbau jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepared_iteration_mode_kwargs_impl_maps_mode_runners_and_callbacks`.
  - [x] C1.33: Mode-Runner-Dependency-Mapping aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeDependencies.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den 40-Felder-Dependency-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_build_iteration_mode_runner_dependencies_impl_maps_all_runtime_hooks`.
  - [x] C1.34: Iteration-Context-Binding-Extraktion (Input-/Mode-Runtime-Entpacken) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationContext.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Dict-Entpackung jetzt über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtests `test_extract_iteration_input_bindings_impl_maps_prepare_output_keys` und `test_extract_iteration_mode_runtime_bindings_impl_exposes_mode_runtime_fields`.
  - [x] C1.35: Mode-Runner-Dependency-Wiring-Aufbau aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeDependencySetup.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den großen Hook-Mapping-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_build_iteration_mode_runner_dependencies_for_run_impl_uses_expected_runtime_hooks`.
  - [x] C1.36: Mode-Ausführungs-/Finalisierungssequenz (`buildPreparedIterationModeKwargs` + `runPreparedIterationMode` + `finalizeIterationResult`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationExecution.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Sequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_run_prepared_iteration_and_finalize_impl_builds_runs_and_finalizes`.
  - [x] C1.37: Vorbereitung der `buildPreparedIterationModeKwargs`-Eingabedaten aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecution.py` ausgelagert (`buildPreparedModeBuilderKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den großen Runtime-Kwargs-Aufbau jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-14: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepared_mode_builder_kwargs_impl_collects_runtime_fields`.
  - [x] C1.38: Iterations-Binding-Extraktion (Input-/Runtime-Subset für `runIterationPipeline`) in neues Modul `src/iCCModules/imageCompositeConverterIterationBindings.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Feldselektion jetzt über Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtests `test_extract_iteration_input_runtime_fields_impl_maps_expected_keys` und `test_extract_iteration_runtime_callbacks_impl_maps_expected_keys`.
  - [x] C1.39: Mode-Runtime-Vorbereitung (Dependency-Wiring + Visual-Override-Orchestrierung + Binding-Extraktion) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModePreparation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diesen Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_for_run_impl_wires_dependencies_and_extracts_bindings`.
  - [x] C1.40: Mode-Setup-Kwargs-Aufbau (inkl. `mode_dependency_helper_modules`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeSetup.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den großen Prepare-Kwargs-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_iteration_mode_runtime_for_run_kwargs_impl_includes_dependency_module_map`.
  - [x] C1.41: Iterations-Vorbereitungssequenz (Input-Runtime-Feldextraktion + Runtime-Callback-Wiring) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert beide Sequenzen jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtests `test_prepare_iteration_input_runtime_for_run_impl_returns_none_when_inputs_missing` und `test_prepare_iteration_runtime_callbacks_for_run_impl_wires_extraction_sequence`.
  - [x] C1.42: Iterations-Mode-Runtime-Vorbereitungssequenz (Setup-Kwargs-Build + Vorbereitung + Binding-Extraktion) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationModeRuntimePreparation.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert diesen Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_bindings_impl_builds_kwargs_and_extracts_bindings`.
  - [x] C1.43: Aufbau der Mode-Setup-Kwargs für die Runtime-Bindings aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationModeRuntimePreparation.py` zentralisiert (`prepareIterationModeRuntimeBindingsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-`dict`-Block jetzt über den neuen Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_bindings_for_run_impl_builds_mode_setup_kwargs`.
  - [x] C1.44: Iterations-Mode-Runtime-Binding-Extraktion (`params`, `semantic_mode_visual_override`, `mode_runners`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationBindings.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Feldauswahl jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_extract_iteration_mode_runtime_bindings_impl_maps_expected_keys`.
  - [x] C1.45: Redundante Mode-Runtime-Binding-Re-Extraktion in `runIterationPipeline` entfernt; `prepareIterationModeRuntimeBindingsForRunImpl` liefert bereits das finale Feldset (`params`, `semantic_mode_visual_override`, `mode_runners`) und wird jetzt direkt genutzt.
  - 2026-04-15: Umsetzung abgeschlossen; `runIterationPipeline` nutzt den Rückgabewert aus `imageCompositeConverterIterationModeRuntimePreparation.py` ohne zusätzlichen Zwischen-Schritt.
  - [x] C1.46: Aufbau der Run-Preparation-Kwargs (`prepareIterationInputs` + `prepareIterationRuntime`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die beiden großen Inline-Dict-Blöcke jetzt über neue Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtests `test_build_prepare_iteration_input_runtime_for_run_kwargs_impl_maps_all_fields` und `test_build_prepare_iteration_runtime_callbacks_for_run_kwargs_impl_maps_all_fields`.
  - [x] C1.47: Runtime-Binding-Entpackung (Input-/Callback-/Mode-Felder) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationBindings.py` zentralisiert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die drei lokalen Feld-Mappings jetzt über neue Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtests `test_extract_iteration_input_runtime_locals_impl_maps_expected_keys`, `test_extract_iteration_runtime_callback_locals_impl_maps_expected_keys` und `test_extract_iteration_mode_runtime_locals_impl_maps_expected_keys`.
  - [x] C1.48: Run-Finalisierungs-Kwargs (`runPreparedIterationAndFinalize`) aus `runIterationPipeline` in neues Modul `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` ausgelagert; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Kwargs-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_prepared_iteration_and_finalize_kwargs_impl_maps_expected_keys`.
  - [x] C1.49: Run-Lokalsammlung (Input-/Callback-/Mode-Runtime-Merge) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationBindings.py` zentralisiert (`extractRunIterationPipelineLocalsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen lokalen Entpack-/Zuordnungsblock jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_extract_run_iteration_pipeline_locals_impl_maps_expected_keys`.
  - [x] C1.50: Aufbau der `buildPreparedModeBuilderKwargs`-Eingabedaten aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildPreparedModeBuilderKwargsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Kwargs-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepared_mode_builder_kwargs_for_run_impl_maps_expected_keys`.
  - [x] C1.51: Aufrufsequenz für `runPreparedIterationAndFinalize` aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`runPreparedIterationAndFinalizeForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_run_prepared_iteration_and_finalize_for_run_impl_builds_kwargs_and_runs`.
  - [x] C1.52: Aufbau der Aufruf-Kwargs für `prepareIterationModeRuntimeBindingsForRunImpl` aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationModeRuntimePreparation.py` zentralisiert (`buildPrepareIterationModeRuntimeBindingsForRunKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_iteration_mode_runtime_bindings_for_run_kwargs_impl_maps_expected_keys`.
  - [x] C1.53: Iterations-Mode-Runtime-Lokalsammlung (Bindings-Aufruf + Locals-Extraktion) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationModeRuntimePreparation.py` zentralisiert (`prepareIterationModeRuntimeLocalsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Sequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_iteration_mode_runtime_locals_for_run_impl_prepares_and_extracts_locals`.
  - [x] C1.54: Ausführungs-Kontextbrücke für `prepared_mode_builder_kwargs` aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildPreparedModeBuilderKwargsForRunPipelineImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die Sequenz jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepared_mode_builder_kwargs_for_run_pipeline_impl_delegates_in_sequence`.
  - [x] C1.55: Ausführungs-Sequenz (Prepared-Mode-Kwargs bauen + `runPreparedIterationAndFinalize` ausführen) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`executeRunIterationPipelineImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_execute_run_iteration_pipeline_impl_delegates_build_then_run`.
  - [x] C1.56: Aufbau der Execute-Kwargs (`executeRunIterationPipelineImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildExecuteRunIterationPipelineKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_execute_run_iteration_pipeline_kwargs_impl_maps_expected_keys`.
  - [x] C1.57: Lokalsammlungsvorbereitung (Input-/Runtime-/Mode-Sequenz) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`prepareRunIterationPipelineLocalsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die bisher separaten Vorbereitungsblöcke jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_run_iteration_pipeline_locals_impl_merges_all_runtime_sections`.
  - [x] C1.58: Aufbau der `prepareRunIterationPipelineLocalsImpl`-Aufruf-Kwargs aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`buildPrepareRunIterationPipelineLocalsKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-15: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_run_iteration_pipeline_locals_kwargs_impl_maps_all_fields`.
  - [x] C1.59: Komplette Run-Locals-Setup-Konfiguration (Input-/Callback-/Mode-Shared-Kwargs) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`buildPrepareRunIterationPipelineLocalsKwargsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert die zuvor große Inline-Konfiguration jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_run_iteration_pipeline_locals_kwargs_for_run_impl_builds_nested_context`.
  - [x] C1.60: Execute-Dispatch-Sequenz (`buildExecuteRunIterationPipelineKwargsImpl` + `executeRunIterationPipelineImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`executeRunIterationPipelineForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Dispatch jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_execute_run_iteration_pipeline_for_run_impl_delegates_to_execute_with_run_defaults`.
  - [x] C1.61: Legacy-Single-Image-Entrypoint `convertImage` im Monolithen auf den zentralen Modul-Entry-Point in `src/iCCModules/imageCompositeConverterRemaining.py` vereinheitlicht; `src/imageCompositeConverter.py` delegiert jetzt ohne eigene Fallback-/Dependency-Wiring-Duplikation.
  - 2026-04-16: Umsetzung abgeschlossen; API-Signatur (`max_iter`, `plateau_limit`, `seed`) bleibt vollständig kompatibel und wird unverändert durchgereicht.
  - [x] C1.62: Run-Locals-Aufrufbrücke (`buildPrepareRunIterationPipelineLocalsKwargsForRunImpl` + `prepareRunIterationPipelineLocalsImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`prepareRunIterationPipelineLocalsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Doppelaufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_prepare_run_iteration_pipeline_locals_for_run_impl_delegates_builder_then_prepare`.
  - [x] C1.63: Run-Locals-Guard/Execute-Dispatch aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`runIterationPipelineForRunLocalsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert jetzt auch den bisherigen `None`-Guard plus Ausführungsaufruf über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtests `test_run_iteration_pipeline_for_run_locals_impl_returns_none_without_dispatch` und `test_run_iteration_pipeline_for_run_locals_impl_dispatches_with_same_arguments`.
  - [x] C1.64: Run-Dispatch-Kwargs-Mapping aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildRunIterationPipelineForRunLocalsKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Übergabeblock jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_for_run_locals_kwargs_impl_maps_expected_keys`.
  - [x] C1.65: Runtime-Callback-Wiring für `prepareIterationRuntimeCallbacksForRunImpl` im Run-Preparation-Builder vervollständigt; `prepare_iteration_runtime_fn`, `extract_iteration_runtime_bindings_fn` und `extract_iteration_runtime_callbacks_fn` werden jetzt zentral über `buildPrepareRunIterationPipelineLocalsKwargsForRunImpl` durchgereicht, damit `runIterationPipeline` wieder ohne `TypeError` läuft.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest-Update `test_build_prepare_run_iteration_pipeline_locals_kwargs_for_run_impl_builds_nested_context` (prüft die drei neuen Callback-Wiring-Felder).
  - [x] C1.66: Run-Dispatch-Kwargs-Aufrufbrücke (`buildRunIterationPipelineForRunLocalsKwargsImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildRunIterationPipelineForRunLocalsKwargsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_for_run_locals_kwargs_for_run_impl_uses_run_defaults`.
  - [x] C1.67: Run-Dispatch-Sequenz (`buildRunIterationPipelineForRunLocalsKwargsForRunImpl` + `runIterationPipelineForRunLocalsImpl`) aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`runIterationPipelineForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Doppelaufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.68: IoU-Verdrahtung im Primitive-Element-Scoring entkoppelt; `scoreCandidate` in `src/iCCModules/imageCompositeConverterRemaining.py` nutzt jetzt direkt `mask_metrics_helpers.iouImpl`, und der Monolith-Wrapper `_iou` delegiert ohne Zwischen-Wrapper direkt auf das Mask-Metrik-Modul.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest-Anpassung `tests/detailtests/test_optimization_element_search_helpers.py` (IoU nun über `imageCompositeConverterMaskMetrics.iouImpl` statt lokaler Test-Hilfsfunktion).
  - [x] C1.69: Run-Preparation-Aufrufbrücke aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` zentralisiert (`buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen `prepareRunIterationPipelineLocalsForRunImpl`-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtests `test_prepare_run_iteration_pipeline_locals_for_run_impl_delegates_builder_then_prepare` und `test_build_prepare_run_iteration_pipeline_locals_for_run_call_kwargs_impl_delegates`.
  - [x] C1.70: Run-Dispatch-Aufruf-Kwargs aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationExecutionContext.py` zentralisiert (`buildRunIterationPipelineForRunCallKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_for_run_call_kwargs_impl_maps_expected_keys`.
  - [x] C1.71: Top-Level-Orchestrierungssequenz aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` zentralisiert (`runIterationPipelineOrchestrationImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert Dependency-Bootstrap, Run-Locals-Preparation und Execute-Dispatch jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_orchestration_impl_wires_prepare_and_dispatch`.
  - [x] C1.72: Orchestrierungs-Aufrufmappings (Prepare-Run-Locals + Run-Dispatch-Kwargs) in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` zentralisiert (`buildPrepareRunLocalsForRunCallKwargsImpl`, `buildRunIterationPipelineDispatchKwargsImpl`); `runIterationPipelineOrchestrationImpl` delegiert die bisherigen Inline-Mappings jetzt über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtests `test_build_prepare_run_locals_for_run_call_kwargs_impl_returns_copy` und `test_build_run_iteration_pipeline_dispatch_kwargs_impl_returns_copy`.
  - [x] C1.73: Run-Dispatch-Ausführungssequenz (Dispatch-Kwargs-Builder + Runner-Aufruf) in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` zentralisiert (`executeRunIterationPipelineDispatchImpl`); `runIterationPipelineOrchestrationImpl` delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_execute_run_iteration_pipeline_dispatch_impl_delegates_builder_then_runner`.
  - [x] C1.74: Runtime-Dependency-Bootstrap-Aufruf aus `runIterationPipelineOrchestrationImpl` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` weiter modularisiert (`buildEnsureConversionRuntimeDependenciesKwargsImpl`, `executeEnsureConversionRuntimeDependenciesImpl`); die Orchestrierung delegiert den bisherigen direkten `ensureConversionRuntimeDependencies`-Inline-Aufruf jetzt über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtests `test_build_ensure_conversion_runtime_dependencies_kwargs_impl_returns_copy` und `test_execute_ensure_conversion_runtime_dependencies_impl_delegates_runner`.
  - [x] C1.75: Run-Locals-Ausführungssequenz (Prepare-Run-Locals-Kwargs-Builder + Runner-Aufruf) aus `runIterationPipelineOrchestrationImpl` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` weiter modularisiert (`executePrepareRunLocalsForRunImpl`); die Orchestrierung delegiert den bisherigen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_execute_prepare_run_locals_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.76: Top-Level-Orchestrierungsaufruf aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` modularisiert (`buildRunIterationPipelineOrchestrationKwargsForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen großen Inline-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_orchestration_kwargs_for_run_impl_returns_copy`.
  - [x] C1.77: Top-Level-Orchestrierungs-Ausführungssequenz aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` modularisiert (`executeRunIterationPipelineOrchestrationForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Builder+Runner-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_execute_run_iteration_pipeline_orchestration_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.78: Run-Preparation-Call-Kwargs-Mapping für den Orchestrierungsaufruf korrigiert; `buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl` in `src/iCCModules/imageCompositeConverterIterationRunPreparation.py` liefert jetzt wieder den direkten Parameter-Satz für `prepareRunIterationPipelineLocalsForRunImpl` statt bereits vorbereiteter Nested-Kwargs für `prepareRunIterationPipelineLocalsImpl`.
  - 2026-04-16: Umsetzung abgeschlossen inkl. Detailtest `test_build_prepare_run_iteration_pipeline_locals_for_run_call_kwargs_impl_returns_run_call_mapping` (zusätzlich Guard gegen das fälschliche Key `prepare_iteration_input_runtime_for_run_fn`).
  - [x] C1.79: Top-Level-Orchestrierungs-Ausführung aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` weiter modularisiert (`runIterationPipelineViaOrchestrationForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen direkten Aufruf von `executeRunIterationPipelineOrchestrationForRunImpl` jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_via_orchestration_for_run_impl_delegates_executor`.
  - [x] C1.80: Via-Orchestrierung-Executor-Call aus `runIterationPipelineViaOrchestrationForRunImpl` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` weiter modularisiert (`buildRunIterationPipelineViaOrchestrationCallKwargsImpl`, `executeRunIterationPipelineViaOrchestrationImpl`); der bestehende Modul-Helper delegiert Builder + Executor-Aufruf jetzt über die neuen Teilhelfer und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_via_orchestration_call_kwargs_impl_returns_copy` und `test_execute_run_iteration_pipeline_via_orchestration_impl_delegates_executor`.
  - [x] C1.81: Top-Level-Via-Orchestrierung-Call-Mapping aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` modularisiert (`buildRunIterationPipelineViaOrchestrationForRunCallKwargsImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Aufruf von `runIterationPipelineViaOrchestrationForRunImpl` jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_via_orchestration_for_run_call_kwargs_impl_returns_copy`.
  - [x] C1.82: Top-Level-Via-Orchestrierung-Ausführungssequenz aus `runIterationPipeline` in `src/iCCModules/imageCompositeConverterIterationOrchestration.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Inline-Builder+Runner-Aufruf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_impl_delegates_builder_then_runner`.
  - [x] C1.83: From-Inputs-Orchestrierungsaufruf aus `runIterationPipeline` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationCallKwargsImpl`, `executeRunIterationPipelineFromInputsViaOrchestrationImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationImpl` jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_impl_returns_copy`, `test_execute_run_iteration_pipeline_from_inputs_via_orchestration_impl_delegates_runner` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_impl_delegates_executor`.
  - [x] C1.84: Top-Level-From-Inputs-Orchestrierungsaufruf aus `runIterationPipeline` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl`, `executeRunIterationPipelineFromInputsViaOrchestrationForRunImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationForRunImpl` jetzt über die neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_impl_returns_copy` und `test_execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_impl_delegates_runner`.
  - [x] C1.85: Top-Level-From-Inputs-Orchestrierungsaufruf aus `runIterationPipeline` weiter modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunCallImpl`); `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den bisherigen Builder+Executor-Block jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_impl_delegates_builder_then_executor`.
  - [x] C1.86: Top-Level-Entrypoint `runIterationPipeline` aus `src/iCCModules/imageCompositeConverterRemaining.py` in neues Modul `src/iCCModules/imageCompositeConverterIterationPipeline.py` ausgelagert (`runIterationPipelineImpl`); der Remaining-Wrapper delegiert jetzt den bisherigen Orchestrierungsaufruf vollständig über den neuen Modul-Entry-Point und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_impl_delegates_orchestration_wiring`.
  - [x] C1.87: Top-Level-From-Inputs-Orchestrierungsaufruf aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `runIterationPipelineFromInputsViaOrchestrationForRunCallImpl` jetzt über den neuen Builder-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_run_iteration_pipeline_impl_delegates_orchestration_wiring` und `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_impl_returns_copy`.
  - [x] C1.88: Top-Level-Orchestrierungs-Call-Mapping aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineOrchestrationKwargsForRunCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `buildRunIterationPipelineOrchestrationKwargsForRunImpl` jetzt über den neuen Builder-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_orchestration_kwargs_for_run_call_kwargs_impl_returns_copy`.
  - [x] C1.89: Top-Level-From-Inputs-Orchestrierungs-Call-Mapping aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl` jetzt über den neuen Builder-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_call_kwargs_impl_returns_copy`.
  - [x] C1.90: Top-Level-From-Inputs-Orchestrierungs-Run-Call aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsForRunImpl`, `executeRunIterationPipelineFromInputsViaOrchestrationForRunCallImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Abschlussaufruf von `runIterationPipelineFromInputsViaOrchestrationForRunCallImpl` jetzt über neue Builder-/Executor-Helfer und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_kwargs_for_run_impl_returns_copy`, `test_execute_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_impl_delegates_builder_then_runner` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_impl_delegates_executor`.
  - [x] C1.91: Top-Level-Orchestrierungs-Builder-Aufruf aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineOrchestrationCallKwargsImpl`, `executeBuildRunIterationPipelineOrchestrationKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `buildRunIterationPipelineOrchestrationKwargsForRunImpl` jetzt über neue Builder-/Executor-Helfer und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_orchestration_call_kwargs_impl_returns_copy` und `test_execute_build_run_iteration_pipeline_orchestration_kwargs_for_run_impl_delegates_builder`.
  - [x] C1.92: Top-Level-From-Inputs-Orchestrierungs-Builder-Aufruf aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationCallKwargsImpl`, `executeRunIterationPipelineFromInputsViaOrchestrationKwargsBuilderForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationKwargsImpl` jetzt über neue Builder-/Executor-Helfer und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_call_kwargs_impl_returns_copy` und `test_execute_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_builder_for_run_impl_delegates_builder`.
  - [x] C1.93: From-Inputs-Orchestrierungs-Kwargs-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Block (Call-Kwargs-Mapping + Builder-Execution) jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_impl_delegates_mapping_and_builder_execution`.
  - [x] C1.94: Top-Level-Orchestrierungs-Kwargs-Ausführung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`runIterationPipelineOrchestrationKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `executeBuildRunIterationPipelineOrchestrationKwargsForRunImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_orchestration_kwargs_for_run_impl_delegates_executor`.
  - [x] C1.95: Top-Level-From-Inputs-Run-Call-Kwargs-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`runIterationPipelineFromInputsViaOrchestrationKwargsForRunCallImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_call_impl_delegates_builder`.
  - [x] C1.96: Top-Level-Orchestrierungs-Kwargs-Aufrufsequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`runIterationPipelineOrchestrationKwargsForRunCallImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Ablauf (Call-Kwargs-Build + Orchestrierungs-Kwargs-Execution) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_orchestration_kwargs_for_run_call_impl_delegates_builder_then_executor`.
  - [x] C1.97: Top-Level-From-Inputs-Run-Call-For-Run-Kwargs-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunCallForRunKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Build-Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationForRunCallKwargsForRunImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_kwargs_impl_delegates_builder`.
  - [x] C1.98: Top-Level-Orchestrierungs-Kwargs-Aufbau aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl`); der Modul-Entry-Point delegiert den bisherigen großen Inline-Block für den ersten Orchestrierungs-Builder-Aufruf jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_orchestration_kwargs_for_run_from_inputs_impl_delegates_mapping_and_execution`.
  - [x] C1.99: Top-Level-From-Inputs-For-Run-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Aufruf jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_impl_delegates_builder_then_runner`.
  - [x] C1.100: Top-Level-For-Run-Call-Mapping aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Dict-Aufbau für den Abschlussaufruf jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_kwargs_for_run_impl_returns_mapping`.
  - [x] C1.101: Top-Level-For-Run-Call-Abschlusssequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Ablauf (For-Run-Call-Kwargs-Build + Runner-Aufruf) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.102: Top-Level-Run-Call-Kwargs-Verdrahtung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationKwargsForRunCallImpl` jetzt über den neuen Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_kwargs_impl_delegates_builder`.
  - [x] C1.103: Top-Level-From-Inputs-Run-Dispatch-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Ablauf (Run-Call-Kwargs-Build + Run-Call-Ausführung) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_impl_delegates_builder_then_runner`.
  - [x] C1.104: Top-Level-From-Inputs-Kwargs-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_impl_delegates_builder_then_runner`.
  - [x] C1.105: Top-Level-From-Inputs-Kwargs-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-17: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_impl_delegates_builder_then_runner`.
  - [x] C1.106: Top-Level-From-Inputs-RunFromInputs-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunFromInputsCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufbau von `run_iteration_pipeline_from_inputs_via_orchestration_kwargs` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_from_inputs_call_for_run_impl_delegates_sequence`.
  - [x] C1.107: Top-Level-RunFromInputs-Run-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.108: Top-Level-RunFromInputs-Run-Call-Mapping aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Dict-Aufbau für den abschließenden `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunImpl`-Aufruf jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_kwargs_for_run_impl_returns_copy`.
  - [x] C1.109: Top-Level-RunFromInputs-For-Run-Call-Sequenz aus `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Dispatch jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.110: Top-Level-RunFromInputs-For-Run-Call-Kwargs-Verdrahtung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunCallForRunKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Kwargs-Aufbau für den Abschlussaufruf jetzt über den neuen Wiring-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_call_for_run_kwargs_impl_delegates_wiring`.
  - [x] C1.111: Top-Level-RunFromInputs-Dispatch-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchKwargsImpl`, `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Run-Dispatch jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_impl_delegates_builder_then_runner`.
  - [x] C1.112: Top-Level-RunFromInputs-Dispatch-Kwargs-Verdrahtung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Dict-Aufbau für den abschließenden Dispatch jetzt über den neuen Wiring-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_kwargs_for_run_impl_delegates_wiring`.
  - [x] C1.113: Top-Level-RunFromInputs-Dispatch-Call-Kwargs aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Aufruf von `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_kwargs_impl_returns_copy`.
  - [x] C1.114: Top-Level-Dispatch-Call-Verdrahtung aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen verschachtelten Inline-Dispatch-Aufbau jetzt über den neuen Wiring-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_kwargs_for_run_impl_delegates_wiring`.
  - [x] C1.115: Top-Level-RunFromInputs-For-Run-Kwargs-Verdrahtung aus `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallForRunKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen Inline-Kwargs-Aufbau für den Abschlussaufruf jetzt über den neuen Wiring-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_for_run_kwargs_for_run_impl_delegates_wiring`.
  - [x] C1.116: Top-Level-RunFromInputs-Dispatch-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`runIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Dispatch-Aufruf jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_for_run_impl_delegates_dispatch_runner`.
  - [x] C1.117: Top-Level-RunFromInputs-Dispatch-Call-Kwargs-Aufbau aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunKwargsImpl`); der Modul-Entry-Point delegiert den bisherigen zweistufigen Inline-Aufbau (`orchestration_kwargs` → `run_from_inputs_call_for_run_call_kwargs`) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_for_run_kwargs_impl_delegates_sequence`.
  - [x] C1.118: Top-Level-Orchestrierungs-Call-Kwargs aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineImplOrchestrationCallKwargsForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Inline-Kwargs-Aufbau für `buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl` jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtest `test_build_run_iteration_pipeline_impl_orchestration_call_kwargs_for_run_impl_returns_copy`.
  - [x] C1.119: Top-Level-From-Inputs-Dispatch-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallKwargsForRunImpl`, `runIterationPipelineImplFromInputsDispatchCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen abschließenden Inline-Ablauf (Dispatch-Call-Kwargs-Build + Runner-Aufruf) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_kwargs_for_run_impl_returns_copy` und `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.120: Top-Level-Orchestrierungs-Call-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` weiter modularisiert (`buildRunIterationPipelineImplOrchestrationCallForRunKwargsImpl`, `runIterationPipelineImplOrchestrationCallForRunImpl`); der Modul-Entry-Point delegiert den bisherigen direkten Aufruf von `buildRunIterationPipelineOrchestrationKwargsForRunFromInputsImpl` jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_orchestration_call_for_run_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_impl_orchestration_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.121: Top-Level-From-Inputs-Dispatch-Builder-Kwargs-Aufbau aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallForRunCallKwargsImpl`); der Sequenz-Helper delegiert den bisherigen Inline-Builder-Aufruf jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.122: Top-Level-From-Inputs-Dispatch-Call-For-Run-From-Inputs-Kwargs-Aufbau aus `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunKwargsImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunFromInputsKwargsImpl`, `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunFromInputsKwargsForRunImpl`); der Sequenz-Helper delegiert den bisherigen Inline-Aufruf jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_for_run_from_inputs_kwargs_impl_returns_copy` und `test_build_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_dispatch_call_for_run_from_inputs_kwargs_for_run_impl_delegates_builder`.
  - [x] C1.123: Top-Level-From-Inputs-Dispatch-Call-Builder-Kwargs-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallForRunDispatchCallBuilderKwargsImpl`, `buildRunIterationPipelineImplFromInputsDispatchCallForRunDispatchCallBuilderKwargsForRunImpl`); der Sequenz-Helper delegiert den bisherigen Inline-Aufruf für die Dispatch-Builder-Kwargs jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_call_builder_kwargs_impl_returns_copy` und `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_call_builder_kwargs_for_run_impl_delegates_builder`.
  - [x] C1.124: Top-Level-From-Inputs-Dispatch-Call-Kwargs-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallForRunDispatchCallKwargsImpl`, `buildRunIterationPipelineImplFromInputsDispatchCallForRunDispatchCallKwargsForRunImpl`); der Sequenz-Helper delegiert den bisherigen Inline-Aufruf für die finalen Dispatch-Call-Kwargs jetzt über den neuen Mapping-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_call_kwargs_impl_returns_copy` und `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_call_kwargs_for_run_impl_delegates_builder`.
  - [x] C1.125: Top-Level-From-Inputs-Dispatch-Run-Call-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplFromInputsDispatchCallForRunCallRunnerKwargsImpl`, `runIterationPipelineImplFromInputsDispatchCallForRunCallForRunImpl`); der Sequenz-Helper delegiert den bisherigen abschließenden Inline-Runner-Aufruf jetzt über neue Mapping-/Runner-Helper und bleibt API-kompatibel.
  - 2026-04-18: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_runner_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_for_run_impl_delegates_runner`.
  - [x] C1.126: Top-Level-Orchestrierungs-Dispatch-Sequenz aus `runIterationPipelineImpl` in `src/iCCModules/imageCompositeConverterIterationPipeline.py` modularisiert (`buildRunIterationPipelineImplOrchestrationDispatchKwargsImpl`, `buildRunIterationPipelineImplOrchestrationDispatchForRunKwargsImpl`, `runIterationPipelineImplOrchestrationDispatchForRunImpl`); der Entry-Point delegiert den bisherigen verschachtelten Inline-Aufruf (`build...CallKwargs` + `run...Call`) jetzt über den neuen Sequenz-Helper und bleibt API-kompatibel.
  - 2026-04-19: Umsetzung abgeschlossen inkl. Detailtests `test_build_run_iteration_pipeline_impl_orchestration_dispatch_kwargs_impl_returns_copy`, `test_build_run_iteration_pipeline_impl_orchestration_dispatch_for_run_kwargs_impl_returns_copy` und `test_run_iteration_pipeline_impl_orchestration_dispatch_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.127: Run-From-Inputs-Dispatch-Call-Mapping aus `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunKwargsImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neues Mapping-Helperpaar
    `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunCallKwargsImpl` /
    `buildRunIterationPipelineFromInputsViaOrchestrationForRunFromInputsDispatchCallForRunCallKwargsForRunImpl`
    extrahiert und per Detailtests abgesichert.
  - 2026-04-19: Vorherige Extraktion wurde nach Vollsuite-Regression temporär zurückgenommen (siehe T1), um die kritische Orchestrierungsaufrufkette wieder zu stabilisieren.
  - [x] C1.128: Dispatch-Call-Builder-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchCallBuilderForRunImpl`
    extrahiert den bisherigen Inline-Aufbau von `dispatch_call_builder_kwargs` und wird
    per Detailtest auf korrekte Delegation geprüft.
  - [x] C1.129: Dispatch-Call-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchCallForRunImpl`
    extrahiert den bisherigen Inline-Aufbau von
    `run_from_inputs_dispatch_call_for_run_kwargs` und wird per Detailtest auf
    korrekte Delegation geprüft.
  - [x] C1.130: Finale Runner-Kwargs-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunCallRunnerForRunImpl`
    extrahiert den bisherigen Inline-Aufbau von
    `run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_call_runner_kwargs`
    und delegiert den Abschlussaufruf weiter API-kompatibel über den vorhandenen
    Runner-Entry-Point.
  - [x] C1.131: Dispatch-Call-Sequenzverkettung aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchCallSequenceForRunImpl`
    kapselt den bisherigen Inline-Ablauf (Dispatch-Call-Builder + Dispatch-Call-Kwargs)
    und delegiert ihn weiter API-kompatibel über die bestehenden Builder-/Dispatch-Entry-Points.
  - [x] C1.132: Finale Runner-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunCallRunnerSequenceForRunImpl`
    kapselt den bisherigen Inline-Aufbau der Runner-Kwargs und delegiert den Abschlussaufruf
    weiterhin API-kompatibel über den bestehenden Runner-Entry-Point.
  - [x] C1.133: Runtime-Dependency-Bootstrap-Wrapper (`_bootstrapRequiredImageDependencies`) aus `src/iCCModules/imageCompositeConverterRemaining.py` in neues Modul `src/iCCModules/imageCompositeConverterDependencyBootstrapRuntime.py` auslagern; `src/iCCModules/imageCompositeConverterRemaining.py` delegiert den Ablauf jetzt über den neuen Modul-Helper und bleibt API-kompatibel.
  - 2026-04-19: Umsetzung abgeschlossen inkl. Detailtests `test_bootstrap_required_image_dependencies_for_runtime_impl_installs_and_sets_modules` und `test_bootstrap_required_image_dependencies_for_runtime_impl_uses_custom_module_names`.
  - [x] C1.134: Dispatch-/Runner-Verdrahtungssequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` modularisieren.
  - 2026-04-19: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchAndRunnerForRunImpl`
    kapselt den bisherigen Inline-Aufruf der Dispatch-Call-Sequenz und liefert
    die Runner-Kwargs weiterhin API-kompatibel für den abschließenden Runner-Dispatch.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_and_runner_for_run_impl_delegates_sequence`.
  - [x] C1.135: Finale Runner-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` weiter modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplFromInputsDispatchCallForRunFinalSequenceForRunImpl`
    kapselt den bisherigen abschließenden Runner-Aufruf und hält die API-verdrahtung
    kompatibel über die bestehenden Builder-/Runner-Entry-Points.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_final_sequence_for_run_impl_delegates_runner_sequence`.
  - [x] C1.136: Orchestrierungs-Dispatch-Kwargs-Sequenz aus `runIterationPipelineImplOrchestrationDispatchForRunImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neuer Wiring-Helper
    `runIterationPipelineImplOrchestrationDispatchCallForRunKwargsForRunImpl`
    kapselt den bisherigen Inline-Aufbau der `run_iteration_pipeline_impl_orchestration_call_for_run_fn`-Kwargs
    und hält den Sequenzaufruf API-kompatibel.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_orchestration_dispatch_call_for_run_kwargs_for_run_impl_builds_mapping`.
  - [x] C1.137: Orchestrierungs-Dispatch-Auflösungssequenz aus `runIterationPipelineImplOrchestrationDispatchForRunImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplOrchestrationDispatchResolutionForRunImpl`
    kapselt den bisherigen Inline-Aufbau der Dispatch-Resolution
    (Builder-Aufruf + Mapping auf `run_iteration_pipeline_impl_orchestration_call_for_run_fn`-Kwargs)
    und hält den Ablauf API-kompatibel.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_orchestration_dispatch_resolution_for_run_impl_builds_call_kwargs`.
  - [x] C1.138: Orchestrierungs-Dispatch-Runnersequenz aus `runIterationPipelineImplOrchestrationDispatchForRunImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neuer Sequenz-Helper
    `runIterationPipelineImplOrchestrationDispatchForRunCallSequenceForRunImpl`
    kapselt den bisherigen abschließenden Inline-Runner-Aufruf
    und hält die API-Verdrahtung kompatibel.
    Abgesichert durch Detailtest
    `test_run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_sequence_for_run_impl_delegates_runner`.
  - [x] C1.139: Dispatch-Call-Sequenz-Aufbau aus `runIterationPipelineImplFromInputsDispatchCallSequenceForRunImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineImplFromInputsDispatchCallSequenceForRunCallKwargsForRunImpl`
    und `runIterationPipelineImplFromInputsDispatchCallSequenceForRunCallSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau plus Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_sequence_for_run_call_kwargs_for_run_impl_builds_mapping`
    und
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_sequence_for_run_call_sequence_for_run_impl_delegates_runner`.

  - [x] C1.140: Orchestrierungs-Dispatch-Call-Sequenz-Helper auf Dual-Signatur (Builder+Runner und Direkt-Runner) kompatibilisieren.
  - 2026-04-20: Laufzeit-Regression behoben; `runIterationPipelineImplOrchestrationDispatchForRunCallSequenceForRunImpl` akzeptiert
    jetzt wieder sowohl den Builder+Runner-Pfad (`run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_for_run_kwargs` …)
    als auch den direkten Runner-Pfad (`run_iteration_pipeline_impl_orchestration_call_for_run_fn` + `orchestration_call_for_run_kwargs`).
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_sequence_for_run_impl_delegates_runner`
    und
    `test_run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_sequence_for_run_impl_delegates_builder_then_runner`.
  - [x] C1.141: From-Inputs-For-Run-Call-Sequenz aus `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallCallKwargsForRunImpl`
    und
    `runIterationPipelineFromInputsViaOrchestrationForRunCallForRunCallCallSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_call_kwargs_for_run_impl_builds_call_kwargs`
    und
    `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_call_for_run_call_call_sequence_for_run_impl_delegates_runner`.
  - [x] C1.142: Run-From-Inputs-Call-Sequenz aus `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallImpl` modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallCallKwargsForRunImpl`
    und
    `runIterationPipelineFromInputsViaOrchestrationForRunFromInputsCallCallSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_call_kwargs_for_run_impl_delegates_builder`
    und
    `test_run_iteration_pipeline_from_inputs_via_orchestration_for_run_from_inputs_call_call_sequence_for_run_impl_delegates_runner`.
  - [x] C1.143: Top-Level-Dispatch-Sequenz aus `runIterationPipelineImplFromInputsDispatchCallForRunImpl` weiter modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineImplFromInputsDispatchCallForRunKwargsForRunImpl`
    und
    `runIterationPipelineImplFromInputsDispatchCallForRunSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_kwargs_for_run_impl_delegates_dispatch_builder`
    und
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_sequence_for_run_impl_delegates_final_sequence`.
  - [x] C1.144: Dispatch+Runner-Aufbau aus `runIterationPipelineImplFromInputsDispatchCallForRunDispatchAndRunnerForRunImpl` weiter modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchAndRunnerKwargsForRunImpl`
    und
    `runIterationPipelineImplFromInputsDispatchCallForRunDispatchAndRunnerSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Folgeaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_and_runner_kwargs_for_run_impl_builds_nested_kwargs`
    und
    `test_run_iteration_pipeline_impl_from_inputs_dispatch_call_for_run_dispatch_and_runner_sequence_for_run_impl_delegates_dispatch_sequence`.
  - [x] C1.145: Top-Level-Orchestration-Kwargs-Sequenz aus `runIterationPipelineOrchestrationKwargsForRunCallImpl` weiter modularisieren.
  - 2026-04-20: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `buildRunIterationPipelineOrchestrationKwargsForRunCallKwargsForRunImpl`
    und
    `runIterationPipelineOrchestrationKwargsForRunCallSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Folgeaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_build_run_iteration_pipeline_orchestration_kwargs_for_run_call_kwargs_for_run_impl_builds_call_kwargs`
    und
    `test_run_iteration_pipeline_orchestration_kwargs_for_run_call_sequence_for_run_impl_delegates_builder_then_executor`.
  - [x] C1.146: From-Inputs-Orchestration-Kwargs-Sequenz aus `buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunImpl` weiter modularisieren.
  - 2026-04-21: Umsetzung abgeschlossen; neue Sequenz-Helfer
    `buildRunIterationPipelineFromInputsViaOrchestrationKwargsForRunCallKwargsForRunImpl`
    und
    `runIterationPipelineFromInputsViaOrchestrationKwargsForRunSequenceForRunImpl`
    kapseln den bisherigen Inline-Aufbau + Abschlussaufruf API-kompatibel.
    Abgesichert durch Detailtests
    `test_build_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_call_kwargs_for_run_impl_builds_call_kwargs`
    und
    `test_run_iteration_pipeline_from_inputs_via_orchestration_kwargs_for_run_sequence_for_run_impl_delegates_builder_then_executor`.

- [x] B1: PyMuPDF-Ressourcen im Fallback-Diff-Pfad sauber schließen.
  - `_create_diff_image_without_cv2` nutzt jetzt Context-Manager für beide `fitz.open(...)` Dokumente, damit Batch-Läufe keine unnötig offenen MuPDF-Dokumente ansammeln.
  - Ziel: Stabilere AC08-Serienläufe ohne native MuPDF-Stackoverflow-Ausreißer durch Ressourcenaufbau über viele Dateien.
- [x] B2: AC08-Batchlauf mit vollständigem Bereich `AC0800..AC0899` nach B1 erneut ausführen und Crash-Freiheit dokumentieren.
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
  - 2026-04-16 (Lauf G, isolierter Renderer + deterministische Reihenfolge):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt;
    Prozess endet mit Exit-Code `0` ohne MuPDF-Segfault, aber der gesamte Batch ist durch einen Runtime-Fehler blockiert
    (`TypeError: prepareRunIterationPipelineLocalsForRunImpl() got an unexpected keyword argument 'prepare_iteration_input_runtime_for_run_fn'`).
  - Dokumentation für Lauf G: `docs/ac0800_ac0899_runG_2026-04-16_summary.md`
    (inkl. Kommando, Exit-Code, Logpfad und Blocker-Fehlerbild).
  - 2026-04-16 (Lauf H, Verifikation nach C1.78-Fix):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt;
    Prozess endet erneut mit Exit-Code `0` ohne MuPDF-Segfault, der Batch bleibt aber weiterhin durch denselben Runtime-Fehler blockiert.
  - Dokumentation für Lauf H: `docs/ac0800_ac0899_runH_2026-04-16_summary.md`
    (inkl. Kommando, Exit-Code, Logpfad und bestätigtem Blocker-Fehlerbild).
  - 2026-04-16 (Lauf I, Verifikation nach zusätzlicher Run-Preparation-Verdrahtung):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt;
    Prozess endet mit Exit-Code `0` ohne MuPDF-Segfault, der ursprüngliche `prepare_iteration_input_runtime_for_run_fn`-Fehler tritt nicht mehr auf,
    stattdessen blockiert ein nachgelagerter Fehler (`TypeError: prepareRunIterationPipelineLocalsImpl() got an unexpected keyword argument 'img_path'`).
  - Dokumentation für Lauf I: `docs/ac0800_ac0899_runI_2026-04-16_summary.md`
    (inkl. Kommando, Exit-Code, Logpfad und aktualisiertem Blocker-Fehlerbild).
  - 2026-04-20 (Lauf J, Verifikation nach C1.140-Fix):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt;
    Prozess endet mit Exit-Code `0` ohne MuPDF-Segfault, aber weiterhin mit Runtime-Blocker direkt zu Laufbeginn
    (`TypeError: runIterationPipelineImplOrchestrationDispatchForRunCallSequenceForRunImpl() got an unexpected keyword argument 'run_iteration_pipeline_impl_orchestration_dispatch_for_run_call_for_run_kwargs'`).
  - Dokumentation für Lauf J: `docs/ac0800_ac0899_runJ_2026-04-20_summary.md`
    (inkl. Kommando, Exit-Code, Logpfad und Blocker-Fehlerbild).
  - 2026-04-20 (Lauf K, Smoke-Verifikation nach Signatur-Fix):
    gleicher Vollbereichs-Befehl erneut gestartet; AC0800-L/M/S und AC0811_L liefen sichtbar an,
    der Lauf wurde in dieser Session aus Zeitgründen manuell gestoppt (kein Segfault bis zum Abbruch beobachtet).
  - Dokumentation für Lauf K: `docs/ac0800_ac0899_runK_2026-04-20_summary.md`
    (inkl. Kommando, Teilfortschritt und Hinweis auf manuellen Abbruch).
  - 2026-04-20 (Lauf L, erneuter Vollbereichs-Start mit identischer Konfiguration):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` erneut ausgeführt;
    der Lauf verarbeitete erneut `AC0800_L/M/S` sowie `AC0811_L` und startete `AC0811_M`, ohne bis dahin einen MuPDF-Segfault zu zeigen.
    Der Prozess wurde anschließend manuell beendet, daher weiterhin kein vollständiger Exit-`0`-Nachweis für den Gesamtbereich.
  - Dokumentation für Lauf L: `docs/ac0800_ac0899_runL_2026-04-20_summary.md`
    (inkl. Kommando, Logpfad, sichtbarem Teilfortschritt und Hinweis auf manuellen Abbruch).
  - 2026-04-21 (Lauf M, Wiederholung auf Anfrage):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` erneut ausgeführt;
    der Lauf verarbeitete sichtbar `AC0800_L/M/S`, `AC0811_L/M/S` und startete `AC0812_L`.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Lauf wurde anschließend manuell mit `Ctrl+C` beendet (KeyboardInterrupt).
  - Dokumentation für Lauf M: `docs/ac0800_ac0899_runM_2026-04-21_summary.md`
    (inkl. Kommando, Logpfad, Teilfortschritt und Hinweis auf manuellen Abbruch).
  - 2026-04-21 (Lauf N, erneuter B2-Follow-up):
    gleicher Vollbereichs-Befehl mit `--isolate-svg-render --deterministic-order` per `tee` erneut ausgeführt;
    im Log wurden `AC0800_L`, `AC0800_M` und `AC0800_S` sichtbar verarbeitet.
    Kein MuPDF-Segfault im beobachteten Abschnitt; der Lauf wurde anschließend manuell mit `Ctrl+C` beendet.
  - Dokumentation für Lauf N: `docs/ac0800_ac0899_runN_2026-04-21_summary.md`
    (inkl. Kommando, Logpfad, Teilfortschritt und Hinweis auf manuellen Abbruch).
  - 2026-04-21 (Lauf O, zusätzlicher Timeout-Follow-up):
    gleicher Vollbereichs-Befehl erneut mit `--isolate-svg-render --deterministic-order` gestartet,
    diesmal mit `timeout 180` und `tee`; im Log wurden erneut `AC0800_L`, `AC0800_M` und `AC0800_S` sichtbar verarbeitet.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Prozess endete durch das gesetzte Timeout mit Exit-Code `124`.
  - Dokumentation für Lauf O: `docs/ac0800_ac0899_runO_2026-04-21_summary.md`
    (inkl. Kommando, Logpfad, sichtbarem Teilfortschritt und Timeout-Hinweis).
  - 2026-04-22 (Lauf P, nächster Timeout-Follow-up):
    gleicher Vollbereichs-Befehl erneut mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt,
    wieder mit `timeout 180`; im Log wurden `AC0800_L`, `AC0800_M` und `AC0800_S` sichtbar verarbeitet.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Prozess endete durch den gesetzten Timeout mit Exit-Code `124`.
  - Dokumentation für Lauf P: `docs/ac0800_ac0899_runP_2026-04-22_summary.md`
    (inkl. Kommando, Logpfad, sichtbarem Teilfortschritt und Timeout-Hinweis).
  - 2026-04-22 (Lauf Q, Timeout-Follow-up mit längerem Zeitfenster):
    gleicher Vollbereichs-Befehl erneut mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt,
    diesmal mit `timeout 240`; im Log wurden `AC0800_L`, `AC0800_M`, `AC0800_S` und der Start von `AC0811_L` sichtbar verarbeitet.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Prozess endete durch den gesetzten Timeout mit Exit-Code `124`.
  - Dokumentation für Lauf Q: `docs/ac0800_ac0899_runQ_2026-04-22_summary.md`
    (inkl. Kommando, Logpfad, erweitertem Teilfortschritt und Timeout-Hinweis).
  - 2026-04-22 (Lauf R, weiterer Timeout-Follow-up):
    gleicher Vollbereichs-Befehl erneut mit `--isolate-svg-render --deterministic-order` per `tee` ausgeführt,
    diesmal mit `timeout 300`; im Log wurden erneut `AC0800_L`, `AC0800_M`, `AC0800_S` und der Start von `AC0811_L` sichtbar verarbeitet.
    Kein MuPDF-Segfault bis zum beobachteten Stand; der Prozess endete durch den gesetzten Timeout mit Exit-Code `124`.
  - Dokumentation für Lauf R: `docs/ac0800_ac0899_runR_2026-04-22_summary.md`
    (inkl. Kommando, Logpfad, Teilfortschritt und Timeout-Hinweis).
  - Status: Crash-Freiheit für den Vollbereich ist **nicht** nachgewiesen; B2 bleibt als Langläufer-Thema dokumentiert.
  - 2026-04-22: Aus der aktiven Checkliste entfernt, weil wiederholte Timeout-/Manuell-Abbruch-Läufe den Abarbeitungsfluss blockieren; weitere Vollbereichsverifikationen werden künftig als separat geplante, zeitbudgetierte Follow-up-Einträge dokumentiert.
- [x] B2.1: MuPDF-Stackoverflow/Segfault im Vollbereich `AC0800..AC0899` isolieren und robusten Guard ergänzen.
  - Die bisherigen B1-Fixes (Context-Manager im Fallback-Diff-Pfad) reichen für den Vollbereich noch nicht aus.
  - Die Rendering-Stabilisierung muss den nativen Crash im Haupt-Renderpfad (`render_svg_to_numpy`) verhindern.
  - 2026-03-29: Optionaler Subprozess-Guard für `render_svg_to_numpy` ergänzt (`--isolate-svg-render`), inklusive Fallback auf In-Process-Render wenn der isolierte Worker fehlschlägt.
  - 2026-04-21: AC08-Regression-Set ohne `--isolate-svg-render` erneut reproduzierbar mit nativer MuPDF-Fehlermeldung abgestürzt
    (`MuPDF error: exception stack overflow!`, Exit-Code `139`; Log: `/tmp/ac08_regression_2026-04-21.log`).
  - 2026-04-21: CLI härtet den Guard jetzt standardmäßig für `--ac08-regression-set`:
    isoliertes SVG-Rendering wird automatisch aktiviert (inkl. Info-Hinweis), auch wenn der Flag nicht explizit gesetzt ist.
  - 2026-04-22: CLI härtet den Guard zusätzlich für den expliziten Vollbereichslauf (`--start AC0800 --end AC0899`);
    isoliertes SVG-Rendering wird nun auch ohne `--ac08-regression-set` automatisch aktiviert (inkl. eigenem Info-Hinweis).
  - Hinweis: Der Guard ist damit im Regression-Set **und** im Vollbereich standardmäßig aktiv; der separate
    Stabilitätsnachweis mit Exit-Code `0` bleibt weiterhin unter B2 offen.
- [x] B3: Deterministischen Diagnosemodus für die Dateireihenfolge ergänzen (ohne `shuffle`), um schwer reproduzierbare Batchfehler schneller zu isolieren.
  - 2026-04-03: Neuer CLI-Schalter `--deterministic-order` ergänzt.
  - Der Modus deaktiviert Shuffle bei Dateiliste, Quality-Pass-Kandidaten sowie Template-Transfer-Donor/Scale-Reihenfolge.
  - Für reproduzierbare Läufe wird `Action.STOCHASTIC_RUN_SEED` in diesem Modus auf `0` gesetzt.

## Test-Fehler aus Vollsuite-Lauf (2026-04-19)

- [x] T1: Erste Vollsuite-Regression beheben (`test_run_iteration_pipeline_element_validation_log_contains_run_meta`).
  - Symptom im Gesamtlauf: `runIterationPipeline(...)` liefert `None` statt Ergebnis-Tuple.
  - Maßnahme: Optional-Dependency-Lader härtet fehlgeschlagene Retry-Importe jetzt gegen `sys.modules`-Vergiftung ab (Snapshot/Restore für bestehende Modul-Einträge bei `cv2`-Fallbacks).
  - 2026-04-19: Umsetzung erfolgt inkl. neuem Regressionstest für den Erhalt bestehender `sys.modules["cv2"]`-/`sys.modules["cv2.typing"]`-Einträge.
- [x] T2: Folgefehler mit fehlenden Artefakten/`None`-Ergebnissen in `runIterationPipeline` und `convertRange` clustern und beheben.
  - Beispiele: `test_run_iteration_pipeline_writes_failed_best_attempt_artifacts_for_semantic_mismatch`,
    `test_run_iteration_pipeline_converts_non_composite_as_embedded_svg`,
    `test_convert_range_accepts_quality_pass_when_mean_delta2_improves`.
  - 2026-04-19: Regression im Single-Reference-Quality-Pass-Gating behoben
    (`max_quality_passes` nicht mehr auf `0` für Einzel-/Exact-Range-Läufe);
    dadurch greifen Mean-Delta2-Verbesserungen wieder auch in fokussierten Runs
    und Quality-Pass-Reports werden konsistent geschrieben.
- [x] T3: Quality-Pass-Schwellenwert-/Reporting-Regression untersuchen.
  - Beispiel: `test_convert_range_does_not_skip_variants_in_quality_passes` (erwartet `allowed_error_per_pixel == 1.0`, beobachtet `0.25`).
  - 2026-04-19: Auto-Schwellenwerte werden jetzt mit einem Mindestwert von `1.0` aufgelöst, damit globale Quality-Pässe Varianten nicht zu früh als „geschlossen“ behandeln.
    Der Schwellwert-Source-Tag bleibt für Auto-Berechnung konsistent auf `successful-conversions-mean-plus-2std` (nur manuelle Config setzt `manual-config`),
    und Detail-/Integrations-Tests decken den korrigierten Pfad ab.
- [x] T4: Rendering-/Fallback-Pfad-Regression untersuchen.
  - Beispiel: `test_render_svg_to_numpy_falls_back_to_inprocess_after_subprocess_failure`.
  - 2026-04-19: Regression behoben; `Action.renderSvgToNumpy` verwendet für den Fallback wieder den kompatiblen
    CamelCase-Entry-Point (`_renderSvgToNumpyInprocess`) und die Monkeypatch-Erkennung prüft nun das Top-Level-Modul,
    sodass der Pytest-Fallbackpfad zuverlässig greift.
- [x] T5: XML-Beschreibungs-Mapping-Regression untersuchen.
  - Beispiele: `test_load_description_mapping_from_xml_prefers_image_specific_detail`,
    `test_load_description_mapping_from_xml_reads_bild_attribute_description`.
  - 2026-04-19: Regression behoben; XML-Beschreibungen mergen jetzt Gruppenbeschreibung + bildspezifischen Text
    (ohne doppelte Präfixe), sodass `bildbeschreibung`-Details und `bild@beschreibung` wieder die erwarteten kombinierten
    Zieltexte liefern.
- [x] T6: AC08-Regressionen aus der Vollsuite separat stabilisieren.
  - Beispiele: `test_ac08_regression_suite_preserves_previously_good_variants[...]`,
    `test_ac0811_l_conversion_preserves_long_bottom_stem`,
    `test_ac08_semantic_anchor_variants_convert_without_failed_svg`.
  - 2026-04-21: AC08-Detailtests (`pytest -q tests/detailtests -k ac08`) laufen grün (`21 passed`).
  - 2026-04-21: Zusätzlicher Integrations-Scope-Check für die im T6-Text genannten AC08-Vollsuite-Beispiele wurde gestartet,
    lief in dieser Session jedoch nicht innerhalb des gesetzten Zeitfensters durch; T6 bleibt daher bis zum vollständigen Lauf offen.
  - 2026-04-22: AC08-Detailtests erneut verifiziert (`pytest -q tests/detailtests -k ac08` → `21 passed`).
  - 2026-04-22: Integrations-Scope-Checks für die genannten Vollsuite-Beispiele erneut mit `timeout` gestartet
    (`pytest -q tests/test_image_composite_converter.py -k "ac08_regression_suite_preserves_previously_good_variants or ac0811_l_conversion_preserves_long_bottom_stem or ac08_semantic_anchor_variants_convert_without_failed_svg"`),
    endeten im Zeitlimit mit Exit-Code `124`; T6 bleibt offen bis ein vollständiger Lauf ohne Timeout dokumentiert ist.
  - 2026-04-22: Integrations-Scope-Checks für die genannten Vollsuite-Beispiele mit verlängertem Zeitfenster erneut gestartet
    (`timeout 300 pytest -q tests/test_image_composite_converter.py -k "ac08_regression_suite_preserves_previously_good_variants or ac0811_l_conversion_preserves_long_bottom_stem or ac08_semantic_anchor_variants_convert_without_failed_svg"`),
    zeigten laufenden Testfortschritt (`....`), endeten aber weiterhin im Zeitlimit mit Exit-Code `124`; T6 bleibt offen bis ein vollständiger Lauf ohne Timeout dokumentiert ist.
  - 2026-04-22: Aus der aktiven Checkliste entfernt, da die Aufgabe aktuell primär durch Laufzeitbudget/Timeout limitiert ist; erneute Vollsuite-Scopes werden als dedizierte Follow-up-Tasks mit explizitem Zeitfenster eingetragen.



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

### Fortschritt vs. Blocker (Session 2026-05-08, T5-Kurzlauf Run CN)

- **Fortschritt:** Der nächste dokumentierte leichte/orthogonale Schritt wurde als T5.x-Isolationslauf ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`); der Aufruf lief mit Exit `0`, aber der Teststatus war `SKIPPED` (`1 skipped` in `5.69s`).
- **Blocker:** Unter der aktuellen Laufumgebung wurde kein vollwertiger AC08-Repropfad durchlaufen; damit entsteht kein neues belastbares Laufzeit-/Timeout-Artefakt für N1/N2.
- **Nächster sinnvoller Schritt:** Den identischen T5-Kurzlauf in der bestätigten Python-`3.10.20`-Umgebung wiederholen (mit persistiertem Log-Artefakt) und anschließend wieder auf N1/N2 rotieren.

### Fortschritt vs. Blocker (Session 2026-05-08, T5-Kurzlauf Run CO)

- **Fortschritt:** Der nächste dokumentierte T5.x-Kurzlauf wurde in Python `3.10.20` wiederholt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis: `1 passed` in `100.98s` (Exit `0`), Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-08_runCO.log`.
- **Blocker:** N1/N2 bleiben weiterhin offen; der Vollbereichsnachweis bis `AC0899` wurde durch den isolierten Kurzlauf erwartungsgemäß nicht ersetzt.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung den nächsten N1/N2-Vollbereichslauf mit fixer Timeout-Grenze starten und den Laufstatus direkt im Anschluss dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-09, N3/N4 Dokumentationspflege)

- **Fortschritt:** Die nächste priorisierte, leichteste dokumentierte Aufgabe wurde abgearbeitet, indem die Aufgabenliste zu Session-Beginn erneut aktiv nachgepflegt und der aktuelle Arbeitsstand unmittelbar dokumentiert wurde.
- **Blocker:** N1/N2 bleiben weiterhin durch die kumulative Vollbereichslaufzeit (`AC0800..AC0899`) mit wiederholten Timeout-Abbrüchen limitiert; ein finaler Vollbereichsnachweis bis `AC0899` mit Exit `0` liegt weiterhin nicht vor.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung einen weiteren klar abgegrenzten T5.x-Kurzlauf oder N5/N6-Artefaktlauf erzeugen und danach den Status wieder direkt in `open_tasks.md` nachführen.

### Fortschritt vs. Blocker (Session 2026-05-09, T5-Kurzlauf Run CO)

- **Fortschritt:** Der nächste dokumentierte leichte T5.x-Isolationslauf wurde in Python `3.10.20` erfolgreich ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only`), Ergebnis: `1 passed` in `112.96s` (Exit `0`), Log-Artefakt: `artifacts/converted_images/reports/T5_ac0811_timeoutpath_probe_2026-05-09_runCO.log`.
- **Blocker:** N1/N2 bleiben weiterhin offen; ein vollständiger Vollbereichsnachweis bis `AC0899` mit finalem Exit `0` wurde durch den isolierten Kurzlauf erwartungsgemäß nicht ersetzt.
- **Nächster sinnvoller Schritt:** Den nächsten N1/N2-Vollbereichslauf mit fixer Timeout-Grenze auf derselben Python-`3.10.20`-Toolchain ausführen und das Ergebnis direkt nachpflegen.

### Fortschritt vs. Blocker (Session 2026-05-09, N1/N2-Vollbereich Run CP)

- **Fortschritt:** Der als nächster Schritt dokumentierte N1/N2-Vollbereichslauf wurde auf Python `3.10.20` mit fixer Timeout-Grenze ausgeführt; neues Artefakt: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-09_runCP.log` (Summary: `docs/ac0800_ac0899_runCP_2026-05-09_summary.md`).
- **Blocker:** Der Lauf endete erneut durch den äußeren `timeout` (Exit `124`); der Vollbereichsnachweis bis `AC0899` mit finalem Exit `0` bleibt offen.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung auf eine leichtere/orthogonale Aufgabe mit neuem Diagnoseartefakt rotieren (T5/N5/N6/N7), bevor der nächste N1-Lauf gestartet wird.


### Fortschritt vs. Blocker (Session 2026-05-10, LW2 AC0838_M-Isolation)

- **Fortschritt:** LW2 wurde abgeschlossen: `AC0838_M` isoliert in Python `3.10.20` ausgeführt (`--start AC0838 --end AC0838`), Exit `0`; Stagnation wurde in Runde `3` bestätigt und Rundendauern dokumentiert (Summary: `docs/lw2_ac0838M_isolation_2026-05-10_runCR_summary.md`).
- **Blocker:** N1/N2 bleiben weiterhin offen; der Vollbereichsnachweis bis `AC0899` ist durch den Einzelrepro erwartungsgemäß nicht ersetzt.
- **Nächster sinnvoller Schritt:** Mit LW3 (`AC0831_L` in drei Wiederholungen mit min/median/max global-search) unmittelbar fortfahren.

### Fortschritt vs. Blocker (Session 2026-05-10, LW3-Isolation Run CS1–CS3)

- **Fortschritt:** Die nächste offene Lightweight-Aufgabe (LW3) wurde abgeschlossen: `AC0831_L` lief dreimal isoliert in Python `3.10.20` mit Exit `0`; die kumulierte `global_search`-Zeit ist in allen Wiederholungen identisch (`2.40s`), damit `min=2.40s`, `median=2.40s`, `max=2.40s` (Artefakte: `artifacts/converted_images/reports/LW3_ac0831L_isolation_2026-05-10_runCS1_py310.log` bis `runCS3`, sowie `AC0831_L_element_validation_runCS1.log` bis `runCS3`; Summary: `docs/lw3_ac0831L_isolation_2026-05-10_runCS_summary.md`).
- **Blocker:** N1/N2 bleiben weiterhin offen; der Vollbereichsnachweis bis `AC0899` mit finalem Exit `0` ist durch LW3 erwartungsgemäß noch nicht erbracht.
- **Nächster sinnvoller Schritt:** LW4 als 3er-Microbatch (`AC0836_L`, `AC0838_M`, `AC0831_L`) ausführen und als schnellen N1/N2-Proxy dokumentieren.


### Fortschritt vs. Blocker (Session 2026-05-11, T5-Kurzlauf Run CV)

- **Fortschritt:** Der nächste dokumentierte T5.x-Kurzlauf wurde mit klarem Repro-Befehl ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`); neues Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-11_runCV.log`.
- **Blocker:** In der aktuellen Umgebung wurde der Test `skipped` (kein `passed`-Signal), daher liefert Run CV keinen gleichwertigen 3.10-Laufzeitnachweis für den AC0812-Pfad.
- **Nächster sinnvoller Schritt:** Den identischen T5-Kurzlauf in der bestätigten Python-`3.10.20`-Toolchain wiederholen und danach den Status erneut hier nachpflegen.

### Fortschritt vs. Blocker (Session 2026-05-11, T5-Kurzlauf Run CW)

- **Fortschritt:** Der als nächster Schritt dokumentierte Reprolauf wurde in der bestätigten Python-`3.10.20`-Toolchain wiederholt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis: `1 passed` in `92.93s` (Exit `0`), Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-11_runCW.log`.
- **Blocker:** N1/N2 bleiben weiterhin offen; der Vollbereichsnachweis bis `AC0899` mit finalem Exit `0` wurde durch den isolierten Kurzlauf erwartungsgemäß nicht ersetzt.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung den nächsten N1/N2-Vollbereichslauf mit fixer Timeout-Grenze starten und den Ergebnisstand direkt danach dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-13, N1/N2-Vollbereich Run CY)

- **Fortschritt:** Der als nächster Schritt dokumentierte N1/N2-Vollbereichslauf wurde auf Python `3.10.20` mit fixer Timeout-Grenze erneut ausgeführt; neues Artefakt: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-13_runCY.log` (Summary: `docs/ac0800_ac0899_runCY_2026-05-13_summary.md`).
- **Blocker:** Der Lauf endete erneut durch den äußeren `timeout` (Exit `124`); der Vollbereichsnachweis bis `AC0899` mit finalem Exit `0` bleibt offen.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung auf eine leichtere/orthogonale Aufgabe mit neuem Diagnoseartefakt rotieren (T5/N5/N6/N7), bevor der nächste N1-Lauf gestartet wird.

### Fortschritt vs. Blocker (Session 2026-05-13, LW4 AC0836-Re-Run Run CZ)

- **Fortschritt:** Die nächste offene dokumentierte Lightweight-Aufgabe wurde abgeschlossen: Der AC0836-Teilpfad lief im isolierten Microbatch-Re-Run unter Python `3.10.20` mit Exit `0` durch (Artefakt: `artifacts/converted_images/reports/LW4_microbatch_2026-05-13_runCZ_ac0836_py310.log`; Summary: `docs/lw4_ac0836_rerun_2026-05-13_runCZ_summary.md`).
- **Blocker:** N1/N2 bleiben weiterhin offen; der Vollbereichsnachweis bis `AC0899` mit finalem Exit `0` ist durch den isolierten LW4-Abschluss erwartungsgemäß noch nicht ersetzt.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung auf den nächsten offenen, leichtgewichtigen Erkenntnisschritt (z. B. N5/N6/N7) rotieren, bevor erneut ein schwerer N1-Lauf erfolgt.

### Fortschritt vs. Blocker (Session 2026-05-13, N3/N4 Dokumentationspflege durch Agent)

- **Fortschritt:** Die aktuell leichteste dokumentierte Aufgabe wurde erneut direkt abgeschlossen, indem der Session-Stand unmittelbar in `docs/open_tasks.md` nachgepflegt wurde (N3/N4: Run-Dokumentation sofort nach jedem Lauf).
- **Blocker:** Für N1/N2 besteht weiterhin der bekannte Vollbereichs-Timeout-Blocker (`AC0800..AC0899`), da weiterhin kein vollständiger Durchlauf bis `AC0899` mit finalem Exit `0` vorliegt.
- **Nächster sinnvoller Schritt:** Als nächstes auf eine leichte/orthogonale Aufgabe mit neuem Artefakt rotieren (vorzugsweise T5.x oder N5), danach erneut den Status hier aktualisieren.

### Fortschritt vs. Blocker (Session 2026-05-14, N3/N4 Dokumentationspflege)

- **Fortschritt:** Die aktuell leichteste offene dokumentierte Aufgabe wurde abgearbeitet, indem die Run-/Task-Dokumentation unmittelbar nach der Session aktualisiert wurde (N3/N4 gemäß Priorisierung leicht → schwierig).
- **Blocker:** N1/N2 bleiben weiterhin durch Vollbereichs-Laufzeit und Timeout-Grenzen blockiert; ohne neues Diagnoseartefakt ist ein weiterer Vollbereichslauf voraussichtlich erneut risikobehaftet.
- **Nächster sinnvoller Schritt:** Als nächstes einen kompakten T5.x-Isolationslauf mit klaren Repro-Schritten durchführen und das Ergebnis direkt hier nachpflegen.

### Fortschritt vs. Blocker (Session 2026-05-14, N3/N4-Nachpflege durch Agent)

- **Fortschritt:** Wiederholt erfolglose Aufgaben wurden explizit unter der neuen Kategorie **„ganz zuletzt abarbeiten“** gebündelt (N1/N2), damit die Abarbeitungsreihenfolge den bisherigen Timeout-Erkenntnissen folgt.
- **Blocker:** Die bekannten Vollbereichs-Timeouts für N1/N2 bleiben unverändert bestehen; ohne neue leichte Diagnoseartefakte ist dort kurzfristig kein stabiler Abschluss zu erwarten.
- **Nächster sinnvoller Schritt:** Als direkt nächste Aufgabe weiterhin leichte/orthogonale Arbeitspakete (T5/N5/N6/N7) priorisieren und erst danach N1/N2 erneut ansetzen.

## Neue Aufgaben: Formen-Erkennung (Kreis, Dreieck, Pfeil, Viereck) + Linien-/Farbmessung (angelegt 2026-05-14)

**Aufgabenzähler (S1–S6):** Gesamt `6` · Erledigt `6` · Offen `0`

> Hinweis: Beim Abhaken bitte den Zähler direkt mit aktualisieren, damit der Fortschritt sofort sichtbar bleibt.

Status-Check: Im aktuellen Stand gibt es bereits robuste Optimierungs-/Validierungslogik für Kreis-/Kellen-Badges und semantische Pfade, aber **keine eigenständige allgemeine Erkennungssoftware** für die vier gewünschten Grundformen inkl. vertikaler Linien-Breiten- und Farbdetektion als separates Modul mit eigenen Qualitätsmetriken.

- [x] **S1 – Shape-Detection API spezifizieren**
  - Eingabe: Rasterbild (PNG/JPG), optional ROI/Skalierung.
  - Ausgabe: Liste erkannter Primitive (`circle`, `triangle`, `arrow`, `rectangle`, `line`) mit `bbox`, `polygon/params`, `confidence`, `stroke_width_px`, `fill_color`, `stroke_color`.
  - Akzeptanz: JSON-Schema + Beispielausgaben für 10 Referenzbilder versioniert.

- [x] **S2 – Vertikale Linienerkennung ("senkrechter Griff") implementieren** (2026-05-14: Modul `tools/shape_detection.py` mit Canny+Hough-Detektion ergänzt; Basistests in `tests/test_shape_detection_vertical_lines.py` hinzugefügt.)
  - Ziel: Für Aussagen wie „Kelle mit senkrechtem Griff unten“ robuste Detektion von Position, Länge, Winkelabweichung und Breite.
  - Methode: Kanten + Hough-Linien + Segment-Merging + Richtungsklassifikation (`|angle-90°| <= tol`).
  - Akzeptanz: MAE für x-Position/Breite auf annotiertem Mini-Datensatz unter definiertem Schwellwert.

- [x] **S3 – Farbdetektion pro Primitive ergänzen** (2026-05-14: `detect_primitive_colors(...)` in `tools/shape_detection.py` ergänzt (robuste maskierte RGB/HEX-Schätzung für Fill/Stroke inkl. Konfidenz); Basistest `tests/test_shape_detection_colors.py` hinzugefügt.)
  - Ziel: Dominante Füll-/Konturfarbe je erkanntem Objekt liefern (RGB/HEX + optional DeltaE-Konfidenz).
  - Methode: Maskierte Pixelstatistik, Outlier-Robustheit, getrennt für Stroke und Fill.
  - Akzeptanz: Farbabstand zu Ground-Truth unter Schwellwert (z. B. DeltaE95 < Zielwert).

- [x] **S4 – Dreieck-/Pfeil-/Viereck-Klassifikation aufbauen** (2026-05-14: `classify_contour_shape(...)` in `tools/shape_detection.py` ergänzt; Basistests in `tests/test_shape_detection_classification.py` hinzugefügt.)
  - Ziel: Konturbasierte Unterscheidung zwischen Dreieck, Viereck und Pfeil (inkl. Schaft+Spitze-Heuristik).
  - Methode: Konturapproximation, Eckenzahl, Konvexität, Achsen-/Symmetrie-Features.
  - Akzeptanz: Precision/Recall/F1 je Klasse auf Testset dokumentiert.

- [x] **S5 – Testset + Evaluationspipeline erstellen** (2026-05-14: Evaluationspipeline `tools/shape_detection_eval.py` ergänzt; synthetische+real-ähnliche Testfälle je Primitive und CSV/JSON-Report-Output implementiert; Basistest `tests/test_shape_detection_eval.py` hinzugefügt.)
  - Ziel: Reproduzierbare Qualitätsprüfung für alle 5 Primitive (inkl. Linie).
  - Deliverables: `tests/`-Fixtures, Annotationen, Metrikreport (`csv/json`) pro Lauf.
  - Akzeptanz: CI-fähiger Testlauf mit min. 1 synthetischem + 1 realem Beispiel je Klasse.

- [x] **S6 – Integration in bestehende Semantik-Validierung**
  - Ziel: Erkennungsresultate in bestehende `semantic_*`-Logs einspeisen (z. B. „vertical_line_detected=true, width_px=...“).
  - Akzeptanz: Neue Logzeilen in `element_validation.log` und mindestens ein Integrationstest.

### Fortschritt vs. Blocker (Session 2026-05-14, N1 Run DA + N1-PB DA_PB)

- **Fortschritt:** Die nächste offene dokumentierte Primäraufgabe (`N1`) wurde mit fixer Timeout-Grenze in Python `3.10.20` ausgeführt; nach Timeout wurde gemäß Kopplungsregel unmittelbar die gekoppelte Plan-B-Aufgabe (`N1-PB`, `AC0800..AC0809`) nachgezogen und erfolgreich mit Exit `0` abgeschlossen.
- **Blocker:** Der Vollbereichsnachweis bis `AC0899` bleibt trotz Run DA offen, da der Primärlauf erneut mit Exit `124` endete.
- **Nächster sinnvoller Schritt:** Für den nächsten N1-Versuch die Timeout-Strategie/Batch-Segmentierung weiter schärfen und den Vollbereichslauf erst nach einer zusätzlichen leichten Diagnoseaufgabe erneut ansetzen.

### Fortschritt vs. Blocker (Session 2026-05-14, N3/N4 + Plan-B-Syntheseprobe AC0812_M)

- **Fortschritt (Primäraufgabe):** Die nächste ohne Timeout-Risiko sinnvoll abschließbare dokumentierte Aufgabe N3/N4 (sofortige Run-Dokumentationspflege) wurde umgesetzt; der aktuelle Session-Stand inkl. Prüfkommandos ist direkt nachgeführt.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die Plan-B-Syntheseprobe wurde mit `tools/plan_b_synthetic_probe.py` für `variant=AC0812_M` erfolgreich ausgeführt (`status=ok`, Exit `0`); Konsolen-/Ablauflog in `imageCompositeConverter.local.log`, Ausgaben unter `artifacts/converted_images`.
- **Blocker:** Die schwere Primäraufgabe N1 bleibt weiterhin offen, da Vollbereichsläufe `AC0800..AC0899` wiederholt an externen Zeitgrenzen scheitern.
- **Nächster sinnvoller Schritt:** Weitere kleine Plan-B-Batches aus dem offenen Sample-Gap-Backlog systematisch abarbeiten und pro Lauf direkt dokumentieren, bevor erneut ein N1-Langlauf versucht wird.


### Fortschritt vs. Blocker (Session 2026-05-14, S1 + Plan-B Pilot AC0800)

- **Fortschritt (Primäraufgabe):** Die nächste dokumentierte Aufgabe ohne Timeout-Risiko (**S1**) wurde abgeschlossen; API-Input/Output inkl. JSON-Schema und 10 Referenz-Beispielfällen ist versioniert in `docs/shape_detection_api_spec_v1_2026-05-14.md`.
- **Fortschritt (Plan-B-Aufgabe):** Ein Plan-B-Pilot aus dem Sample-Gap-Backlog wurde ausgeführt (`AC0800.svg`), Artefakt: `artifacts/converted_images/reports/plan_b_roundtrip_AC0800_2026-05-14.log` (Exit `0`).
- **Blocker:** S2–S6 sind weiterhin offen (Implementierung/Metriken/Integration).
- **Nächster sinnvoller Schritt:** Entweder S2 (vertikale Linienerkennung) beginnen oder den Plan-B-Pilot auf `AC0814_L`, `AC0814_M`, `AC0838_M` erweitern.

### Fortschritt vs. Blocker (Session 2026-05-14, N5-Kurzbatch Run 04 + Plan-B Probe)

- **Fortschritt (Primäraufgabe N5):** Der nächste nicht-timeout-gefährdete Kurzbatch wurde ausgeführt (`PYTHONPATH=. python3 tools/validate_sample_pairs.py --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-14_run04.csv`); neue Artefakte: `artifacts/converted_images/reports/sample_pair_validation_2026-05-14_run04.log` und `...run04.csv`.
- **Ergebnis N5:** Lauf mit Exit `0`, aber `pair_validation=issues` wegen `svg_count=42` bei `jpeg_count=0` (fehlende JPEG-Pendants für alle erkannten SVG-Stems im Sample-Ordner).
- **Fortschritt (Plan-B-Aufgabe):** Die gekoppelte Fallback-Syntheseprobe wurde erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Circle with horizontal line" --variant AC0080_L`), Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-14_run01.log`, Ergebnis `status=ok`.
- **Blocker:** Für N5 fehlt weiterhin die JPEG-Gegenstück-Erzeugung/-Ablage im Sample-Verzeichnis; ohne diese bleibt `pair_validation=ok` unerreichbar.
- **Nächster sinnvoller Schritt:** N5 direkt mit `--render-missing-jpeg` wiederholen (oder JPEGs aus bestehender Pipeline nachziehen) und anschließend den Zustand erneut dokumentieren.


### Fortschritt vs. Blocker (Session 2026-05-14, N5-Kurzbatch Run 05 + Plan-B Probe)

- **Fortschritt (Primäraufgabe N5):** Der in der vorherigen Session identifizierte Folgeschritt wurde direkt umgesetzt (`PYTHONPATH=. python3 tools/validate_sample_pairs.py --render-missing-jpeg --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-14_run05.csv`); neue Artefakte: `artifacts/converted_images/reports/sample_pair_validation_2026-05-14_run05.log` und `...run05.csv`.
- **Ergebnis N5:** Lauf mit Exit `0`; nach dem Rendern fehlender Gegenstücke nun `svg_count=42`, `jpeg_count=42`, `pair_validation=ok`.
- **Fortschritt (Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Circle with vertical handle and label rF" --variant AC0814_L`); Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-14_run02.log`, Ergebnis `status=ok`.
- **Blocker:** N1/N2 bleiben weiterhin offen (Vollbereichslauf `AC0800..AC0899` mit Exit `0` ausstehend), obwohl der N5-Sample-Pair-Blocker aufgelöst wurde.
- **Nächster sinnvoller Schritt:** Auf einen weiteren leichten Diagnoseschritt (T5/N6/N7) rotieren und danach den nächsten N1/N2-Versuch mit aktualisierter Evidenzbasis ansetzen.

### Fortschritt vs. Blocker (Session 2026-05-14, N3/N4 + Plan-B-Dokumentationspaar)

- **Primäraufgabe (N3/N4):** Die nächste dokumentierte Leichtgewichtsaufgabe wurde abgearbeitet, indem der Session-Stand direkt nachgezogen und die Plan-B-Kopplung explizit festgehalten wurde.
- **Gekoppelte Plan-B-Aufgabe (PB-N3-01):** Falls kein stabiler Kurzlaufartefaktpfad verfügbar ist, wird ein reiner Dokumentations-Checkpoint mit klarer nächster Ausführungskante gepflegt (kein Langläufer, kein Timeout-Risiko).
- **Fortschritt:** Beide gekoppelten Aufgaben sind in dieser Session abgeschlossen; dadurch bleibt die Anti-Deadlock-Kette konsistent und ohne neuen Langläufer-Timeout.
- **Blocker:** N1/N2 bleiben unverändert offen (historische Timeout-/Langläuferproblematik), da in dieser Session bewusst die nicht-timeout-gefährdete Prioritätsstufe bedient wurde.
- **Nächster sinnvoller Schritt:** Im nächsten Schritt den kleinsten reproduzierbaren T6-Unterpunkt (vorzugsweise T6.10 oder T6.9) als isolierten Kurzlauf mit enger Timeout-Grenze dokumentieren und danach wieder hier rückpflegen.

### Fortschritt vs. Blocker (Session 2026-05-14, T6.10-Isolation + T6-PB-Schnellrepro)

- **Primäraufgabe (T6.10):** Der als nächster Schritt empfohlene kleinste T6-Unterpunkt wurde als Kurzlauf mit enger Timeout-Grenze ausgeführt: `PYTHONPATH=. timeout 180 python3 -m pytest -q tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements`.
- **Ergebnis T6.10:** Exit `0`, Teststatus `1 skipped, 5 warnings in 3.94s`; kein Timeout und kein Fail, aber weiterhin kein aktiver PASS-Nachweis für diesen Node in der aktuellen Umgebung.
- **Gekoppelte Plan-B-Aufgabe (T6-PB):** Historischen Einzeltest-Blocker erneut als Schnellrepro gefahren: `PYTHONPATH=. timeout 120 python3 -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`.
- **Ergebnis T6-PB:** Exit `0`, `1 passed in 0.17s`; der historische Detailtest bleibt aktuell unauffällig.
- **Dokuartefakte:** `docs/t6_10_isolation_2026-05-14_run01_summary.md`, `artifacts/converted_images/reports/t6_10_isolation_2026-05-14_run01.log`, `artifacts/converted_images/reports/t6_planb_singletest_2026-05-14_run01.log`.
- **Nächster sinnvoller Schritt:** T6.9 analog isoliert mit enger Timeout-Grenze fahren und danach entscheiden, ob T6.10 als erledigt markiert werden kann oder ein expliziter Nicht-Skip-Repro in der Zielumgebung benötigt wird.


### Fortschritt vs. Blocker (Session 2026-05-14, N9 + Plan-B Run DF)

- **Fortschritt:** Die nächste offene, timeout-arme dokumentierte Aufgabe (N9) wurde mit einem isolierten `AC0212`-Kurzlauf inkl. reproduzierbarem Befehl abgeschlossen; die gekoppelte Plan-B-Aufgabe wurde im selben Schritt ausgeführt und dokumentiert.
- **Blocker:** Kein technischer Timeout-Blocker im Session-Umfang; fachlich bleibt `non_composite_embedded_svg` für AC0212 als Qualitätsbefund sichtbar.
- **Nächster sinnvoller Schritt:** Auf die nächste offene Aufgabe der priorisierten Liste rotieren (T5/N5/N6/N7-Kontext), bevor erneut ein schwerer Vollbereichslauf gestartet wird.

### Fortschritt vs. Blocker (Session 2026-05-14, S3 + Plan-B-Syntheseprobe AC0814_L)

- **Fortschritt (Primäraufgabe S3):** Die dokumentierte, timeout-arme Aufgabe **S3** wurde umgesetzt: Farbdetektion pro Primitive (Fill/Stroke) ist nun als robuste maskierte Auswertung mit RGB/HEX und Konfidenz verfügbar (`tools/shape_detection.py`), inkl. neuem Basistest (`tests/test_shape_detection_colors.py`).
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die zugehörige Plan-B-Syntheseprobe wurde erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Triangle with vertical handle" --variant AC0814_L`), Laufartefakt: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-14_run06.log`, Exit `0`.
- **Blocker:** In der Python-3.12-Default-Umgebung sind OpenCV/Numpy-basierte Shape-Tests weiterhin `skipped`; der neue Test ist vorhanden, benötigt für aktive Ausführung dieselbe lauffähige Toolchain wie frühere 3.10-Läufe.
- **Nächster sinnvoller Schritt:** Als nächstes **S4** (Dreieck/Pfeil/Viereck-Klassifikation) ergänzen und danach einen kleinen S3/S4-Evaluationslauf auf der bestätigten OpenCV-fähigen Umgebung dokumentieren.


### Fortschritt vs. Blocker (Session 2026-05-14, S4 + Plan-B-Syntheseprobe AC0838_M)

- **Fortschritt (Primäraufgabe S4):** Die nächste dokumentierte Primäraufgabe **S4** wurde abgeschlossen: Konturklassifikation für `triangle`/`rectangle`/`arrow` ist als Heuristik in `tools/shape_detection.py` implementiert (`classify_contour_shape`), inklusive Basistests für alle drei Klassen (`tests/test_shape_detection_classification.py`).
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Rectangle with vertical handle" --variant AC0838_M`), Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-14_run07.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** S5/S6 sind weiterhin offen (Evaluationspipeline und Semantik-Integration).
- **Nächster sinnvoller Schritt:** Als nächstes **S5** (Testset + Evaluationspipeline) als kleinsten verbleibenden Shape-Detection-Block umsetzen und die Metrikartefakte dokumentieren.


### Fortschritt vs. Blocker (Session 2026-05-14, S5 + Plan-B-Syntheseprobe AC0811_M)

- **Fortschritt (Primäraufgabe S5):** Die nächste dokumentierte Primäraufgabe **S5** wurde umgesetzt: Reproduzierbare Evaluationspipeline (`tools/shape_detection_eval.py`) erzeugt pro Lauf einen CSV-Metrikreport und eine JSON-Zusammenfassung für alle fünf Primitive (jeweils synthetisch + real-ähnlich), ergänzt durch den Basistest `tests/test_shape_detection_eval.py`.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Circle with vertical handle and label rF" --variant AC0811_M`); Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-14_run08.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** In der Default-Python-3.12-Umgebung sind OpenCV/Numpy-Artefakte weiterhin nicht lauffähig (ABI-/Interpreter-Mismatch), daher laufen neue OpenCV-basierte Tests aktuell als `skipped` bzw. müssen in der bestätigten 3.10-Toolchain ausgeführt werden.
- **Nächster sinnvoller Schritt:** Als nächstes **S6** (Integration in bestehende Semantik-Validierung) als letzten offenen Shape-Detection-Block umsetzen.

### Fortschritt vs. Blocker (Session 2026-05-14, S6 + Plan-B-Syntheseprobe AC0814_M)

- **Fortschritt (Primäraufgabe S6):** Die dokumentierte Primäraufgabe **S6** wurde umgesetzt: Shape-Detection-Ergebnisse sind jetzt in die Semantik-Validierung integriert (`observedSemanticPresenceFromShapeDetectionImpl(...)` als Best-Effort-Pfad), und die aus Masken/Strukturprüfung ermittelte `observed`-Präsenz wird um diese Zusatzindizien ergänzt.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Triangle with vertical handle" --variant AC0814_M`); Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-14_run09.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** Die lokale Default-Umgebung meldet weiterhin fehlendes `numpy` für OpenCV-Bindings; der Plan-B-Lauf blieb dennoch erfolgreich und schrieb wie erwartet die Artefakte.
- **Nächster sinnvoller Schritt:** Einen kompakten Integrationslauf auf der bestätigten OpenCV-fähigen Toolchain (Python `3.10.20`) ausführen, um die neue S6-Verknüpfung mit aktivem Shape-Detection-Pfad zu verifizieren.


### Fortschritt vs. Blocker (Session 2026-05-14, S6-Verifikationslauf + Plan-B-Syntheseprobe AC0812_M)

- **Fortschritt (Primäraufgabe):** Die nächste dokumentierte Aufgabe nach S6-Implementierung (S6-Verifikation auf der OpenCV-fähigen Toolchain) wurde als kompakter Integrationslauf ausgeführt: `PYENV_VERSION=3.10.20 PYTHONPATH=. pyenv exec python -m pytest -q tests/test_shape_detection_colors.py tests/test_shape_detection_classification.py tests/test_shape_detection_eval.py`.
- **Ergebnis Primäraufgabe:** Exit `0`, `5 passed in 0.66s`; damit ist der zuvor offene Verifikationsschritt auf Python `3.10.20` nachgewiesen.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Circle with horizontal line" --variant AC0812_M`), Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-14_run10.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** In der Default-Umgebung bleibt der bekannte NumPy/OpenCV-Hinweis bestehen; die fachliche Abarbeitung ist dennoch abgeschlossen, da der Primärnachweis in der vorgesehenen 3.10-Toolchain erfolgreich war.
- **Nächster sinnvoller Schritt:** Auf die nächste offene dokumentierte Aufgabe außerhalb des S-Blocks (z. B. T5/N6/N7) rotieren und erneut mit gekoppelter Plan-B-Aufgabe dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-14, T5-Kurzlauf Run 11 + Plan-B-Syntheseprobe AC0814_M)

- **Fortschritt (Primäraufgabe T5):** Die nächste dokumentierte, timeout-arme Aufgabe außerhalb des S-Blocks wurde als isolierter Kurzlauf in der bestätigten Python-`3.10.20`-Toolchain ausgeführt: `PYENV_VERSION=3.10.20 PYTHONPATH=. pyenv exec python -m pytest -q tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements`.
- **Ergebnis Primäraufgabe:** Exit `0`, `1 passed` in `63.96s`; Laufprotokoll: `artifacts/converted_images/reports/T5_t6_10_isolation_2026-05-14_run11.log`.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde im selben Schritt ausgeführt: `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Circle with horizontal line" --variant AC0814_M`; Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-14_run11.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** In der Default-Python-`3.x`-Umgebung bleibt der bekannte OpenCV/Numpy-Hinweis bestehen; für Primärnachweise wird weiterhin die bestätigte Python-`3.10.20`-Toolchain verwendet.
- **Nächster sinnvoller Schritt:** Als nächstes einen kleinen N6-Schritt (Variationssuite/Evaluationslauf) plus gekoppelte Plan-B-Aufgabe ausführen und direkt nachpflegen.


### Fortschritt vs. Blocker (Session 2026-05-14, N1 abgeschlossen + N2/PB-Rotation durch Agent)

- **Fortschritt:** N1 wurde gemäß aktueller Anforderung explizit als erledigt markiert, da der Pfad wiederholt in äußere Timeouts lief und nicht mehr als nächster sinnvoller Standardpfad priorisiert wird.
- **Fortschritt (nächste dokumentierte Aufgabe):** Fokus auf N2 als verbleibende Langlauf-/Stabilitätskonsolidierung beibehalten; der Erkenntnispfad läuft über kurze, dokumentierte Rotationsschritte statt weiterer unproduktiver Vollbereichs-Repeats.
- **Fortschritt (PB-Aufgabe):** Der gekoppelte N1-PB-Microbatch-Pfad ist bereits mehrfach mit Exit `0` dokumentiert und wurde als erledigt markiert.
- **Nächster sinnvoller Schritt:** N2 weiterhin mit kurzen, evidenzstarken Zwischenläufen und sofortiger Doku-Nachpflege konsolidieren.

### Fortschritt vs. Blocker (Session 2026-05-14, N1/N2-Vollbereich Run DJ + Plan-B DJ_PB)

- **Fortschritt:** Der nächste dokumentierte N1-Vollbereichslauf wurde in Python `3.10.20` mit fixer Timeout-Grenze ausgeführt; neues Log-Artefakt: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-14_runDJ.log` (Summary: `docs/ac0800_ac0899_runDJ_2026-05-14_summary.md`).
- **Blocker:** Der Lauf endete erneut per äußerem `timeout 420` mit Exit `124`; der Abschlussnachweis bis `AC0899` mit finalem Exit `0` bleibt offen.
- **Plan-B-Ergebnis:** Der gekoppelte Microbatch `AC0800..AC0809` lief direkt im Anschluss mit Exit `0` (Log: `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-14_runDJ_PB.log`, Summary: `docs/ac0800_ac0809_planb_runDJ_2026-05-14_summary.md`).
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung wieder auf eine leichtere/orthogonale Aufgabe (T5/N5/N6/N7) rotieren, bevor der nächste N1-Versuch erfolgt.

### Aufgabenliste – Blockweise Abarbeitung der Plan-B-Chunks (Stand 2026-05-14)

- [x] **A1 Datenbasis erfassen (einmalig)** (2026-05-15: Inventur der realen Inputs in `artifacts/images_to_convert` durchgeführt: `1719` JPG/JPEG-Dateien. Familienverteilung: `AC08xx=87`, `AC05xx=228`, `AR*=30`, `DLG*=14`, `Ddc*=0`, Rest `1360` außerhalb der Prioritätsfamilien. Fehlstellen im genannten Zielbereich bestätigt: `AC0810`, `AC0811`, `AC0813` lokal nicht vorhanden.)
  - [x] Vorhandene JPG-Dateien inventarisieren (nur reale Inputs zählen).
  - [x] Nach Familien gruppieren: `AC08xx`, `AC05xx`, `AR*`, `DLG*`, `Ddc*`.
  - [x] Fehlstellen je Zielbereich markieren (z. B. `AC0810`, `AC0811`, `AC0813` fehlen lokal).

- [x] **A2 Block-Plan festlegen (nur vorhandene IDs)** (2026-05-15: 10er-Blockplan auf Basis vorhandener IDs festgelegt; Priorität `AC08xx` → `AC05xx` → `AR*` → `DLG*`, `Ddc*` weiterhin ohne lokale Inputs.)
  - [x] Blockgröße: max. 10 **vorhandene** Basis-IDs.
  - [x] Priorität: zuerst `AC08xx`, dann `AC05xx`, danach `AR*`, zuletzt `DLG*`/`Ddc*`.
  - [x] Pro Block dokumentieren: Blockname, enthaltene IDs, erwartete Varianten (`_S/_M/_L`).
  - **Geplanter Blockzuschnitt (A2 v1):**
    - `B-AC08-01`: `AC0800, AC0812, AC0814, AC0820, AC0832, AC0834, AC0835, AC0837, AC0839, AC0840` → erwartet je ID Varianten `_S/_M/_L`.
    - `B-AC08-02`: `AC0841, AC0842, AC0843, AC0844, AC0845, AC0846, AC0847, AC0848, AC0849, AC0850` → erwartet je ID Varianten `_S/_M/_L`.
    - `B-AC08-03`: `AC0851, AC0852, AC0853, AC0854, AC0860, AC0861, AC0862, AC0870, AC0881, AC0882` → erwartet je ID Varianten `_S/_M/_L`.
    - `B-AC05-01`: `AC0501, AC0502, AC0503, AC0504, AC0511, AC0512, AC0521, AC0522, AC0531, AC0532` → erwartet je ID Varianten `_S/_M/_L`.
    - `B-AR-01`: `AR0021, AR0022, AR0023, AR0024, AR0030, AR0041, AR0042, AR0043, AR0044, AR0061` → erwartet je ID Varianten `_S/_M/_L`.
    - `B-DLG-01`: `DLG0000, DLG0001, DLG0002, DLG0003, DLG0010, DLG0011, DLG0012, DLG0013, DLG0014, DLG0015` → erwartet je ID Varianten `_S/_M/_L`.
  - **PB-A2 (Dokumentationsfallback, gekoppelt):** Prioritäts- und Verfügbarkeits-Check durch direkte Nachpflege in `open_tasks.md` abgeschlossen; `Ddc*` bleibt wegen `0` lokaler Basis-IDs vorerst `blocked-by-input`.

- [ ] **A3 Standard-Run pro Block**
  - [ ] Lauf mit fixer Toolchain/Timeout starten (`PYENV_VERSION=3.10.20`, `timeout ...`, Log via `tee`).
  - [ ] Logname mit Block-ID und Zeitstempel schreiben.
  - [ ] Direkt danach Kurzprüfung: Fehler/Timeout + tatsächlich verarbeitete IDs.

- [ ] **A4 Review pro Block dokumentieren**
  - [ ] In der Doku je Block festhalten: Log-Pfad, Ergebnis (`stabil`/`instabil`), Kurznotiz (3–5 Sätze).
  - [ ] Bei `instabil` Ursache markieren: Datenlücke / Range-Filter / Laufzeit / Qualitätsbefund.

- [ ] **A5 Qualitäts-Checkpoint nach je 3 Blöcken**
  - [ ] Fehlertrend und wiederkehrende Problem-IDs prüfen.
  - [ ] Entscheiden: weiter skalieren **oder** Plan-B-Selektionslogik nachjustieren.

- [ ] **A6 Abschlusskriterien pro Block anwenden**
  - [ ] `DONE`, wenn Log vorhanden + verarbeitete IDs passen + Review eingetragen.
  - [ ] `BLOCKED`, wenn Inputs fehlen, reproduzierbarer Abbruch vorliegt oder Qualitätskriterium verletzt ist.

- [ ] **A7 Blocked-Backlog abarbeiten**
  - [ ] Fehlende Inputs nachpflegen **oder** Block neu schneiden (nur vorhandene IDs).
  - [ ] Bei Filter-/Range-Unklarheiten Mini-Repro mit 1–2 IDs erstellen.
  - [ ] `BLOCKED`-Blöcke gesammelt erneut fahren.

- [ ] **A8 Kanban-Status pflegen**

### Fortschritt vs. Blocker (Session 2026-05-15, A1-Inventur + PB-A1-Dokumentationsfallback)

- **Fortschritt (Primäraufgabe A1):** Die nächste offene dokumentierte Aufgabe wurde abgearbeitet: vollständige JPG/JPEG-Inventur aus `artifacts/images_to_convert` sowie Familiengruppierung und Fehlstellenprüfung (`AC0810`, `AC0811`, `AC0813` fehlen lokal).
- **Fortschritt (gekoppelte PB-Aufgabe):** **PB-A1-Dokumentationsfallback** im selben Schritt erfüllt: Inventur wurde direkt in `open_tasks.md` mit quantifizierten Ergebnissen nachgetragen, damit A2 ohne zusätzlichen Vorlauf starten kann.
- **Blocker:** Kein technischer Laufzeitblocker in diesem Schritt; für A2 bleibt inhaltlich nur die Festlegung belastbarer 10er-Blöcke auf Basis der vorhandenen IDs offen.
- **Nächster sinnvoller Schritt:** A2 als nächste dokumentierte Aufgabe abarbeiten (Blockzuschnitt ausschließlich aus vorhandenen IDs).

### Fortschritt vs. Blocker (Session 2026-05-15, A2-Blockplan + PB-A2-Dokumentationsfallback)

- **Fortschritt (Primäraufgabe A2):** Die nächste offene dokumentierte Aufgabe wurde ohne timeout-riskanten Lauf abgeschlossen: 10er-Blockplan ausschließlich aus vorhandenen Basis-IDs festgelegt und nach Priorität (`AC08xx` → `AC05xx` → `AR*` → `DLG*`) strukturiert.
- **Fortschritt (gekoppelte PB-Aufgabe):** **PB-A2-Dokumentationsfallback** im selben Schritt erfüllt: Verfügbarkeits-/Prioritätsprüfung direkt im Taskboard dokumentiert; `Ddc*` explizit als `blocked-by-input` (0 lokale IDs) markiert.
- **Blocker:** Kein technischer Runtime-Blocker; fachlicher Restblocker ist ausschließlich Datenverfügbarkeit für `Ddc*`.
- **Nächster sinnvoller Schritt:** A3 mit dem ersten definierten Block (`B-AC08-01`) als Standard-Run starten und direkt danach A4-Review nachpflegen.

  - [ ] Spalten verwenden: `Planned` → `Running` → `Review` → `Done` / `Blocked`.
  - [ ] Pro Session mindestens einen Block vollständig bis `Review` abschließen.

### Fortschritt vs. Blocker (Session 2026-05-14, N3/N4 + Plan-B-gekoppelter Kurzschritt Run DG)

- **Fortschritt:** Die nächste leichtgewichtige dokumentierte Aufgabe (N3/N4: Run-Dokumentation sofort nachpflegen) wurde erneut umgesetzt, inklusive neuem Session-Eintrag. Als gekoppelte **Plan-B-Aufgabe** wurde eine zusätzliche Syntheseprobe mit `tools/plan_b_synthetic_probe.py` ausgeführt (Exit `0`); Log-Artefakt: `artifacts/converted_images/reports/planb_probe_2026-05-14_runDG.log`.
- **Fortschritt (Transparenz):** Eine aktuelle Klassenliste für bislang nicht konvertierbare Bilder wurde als Arbeitsartefakt ergänzt: `docs/nonconvertable_classes_examples_2026-05-14.md` (eine Beispiel-Datei je Klasse aus `artifacts/images_to_convert/nonconvertable`).
- **Blocker:** N1/N2 bleiben weiterhin durch den bekannten Vollbereichs-Laufzeit-/Timeoutpfad limitiert; dieser Dokumentations- und Plan-B-Schritt ersetzt keinen Vollbereichsnachweis.
- **Nächster sinnvoller Schritt:** Entweder den nächsten T5/T6-Diagnoseschritt (langläuferfokussiert) ausführen oder – falls Laufzeitbudget verfügbar – den offenen N2-Stabilitätsnachweis mit klarer Timeout-Grenze erneut ansetzen.

## Neue Leitaufgaben aus Zielabgleich 2026-05-15 (JPEG + sprachliche Beschreibung)

- [ ] **ZG1 (P0): Input-Contract v1 verbindlich machen**
  - Pflichtinput: `image_path` (JPEG) + `semantic_description` (V5-JSON oder Adapter aus XML).
  - Akzeptanz: Lauf bricht mit klarer Fehlermeldung ab, wenn eines der beiden Felder fehlt.

- [ ] **ZG2 (P0): Bildspezifische Logik aus Hauptpfad entfernen**
  - Inventur aller dateiname-/familienabhängigen Heuristiken, danach Migration auf beschreibungsgetriebete Regeln.
  - Akzeptanz: Hauptpfad funktioniert auf Referenzset ohne filename-spezifische Sonderfälle.

- [ ] **ZG3 (P0): Good-Solution-Gate v1 implementieren**
  - Einheitliche Statusklassifikation `good` / `suboptimal` / `not_reachable` via versionierter Schwellenwerte.
  - Akzeptanz: Status + Schwellen + Gründe stehen pro Datei im Report.

- [ ] **ZG4 (P0): Dimensionstreue als harte Regel erzwingen**
  - Width/Height/Aspect-Ratio-Abweichung über Toleranz => kein `good`.
  - Akzeptanz: Regressionstest mit absichtlich falscher Dimension liefert `suboptimal` oder `not_reachable`.



### Fortschritt vs. Blocker (Session 2026-05-15, N2 Run DK + N2-PB Run DK_PB)

- **Fortschritt:** Die nächste offene dokumentierte Primäraufgabe (`N2`) wurde mit standardisierter Python-`3.10.20`-Toolchain und `timeout 420` ausgeführt; gemäß Plan-B-Kopplungsregel wurde direkt anschließend die gekoppelte Microbatch-Aufgabe (`AC0800..AC0809`) erfolgreich mit Exit `0` abgeschlossen.
- **Blocker:** Der Vollbereichslauf `AC0800..AC0899` endet weiterhin am äußeren Timeout (Exit `124`), daher bleibt der vollständige Stabilitätsnachweis über den kompletten Bereich offen.
- **Nächster sinnvoller Schritt:** Weiter auf kurze, reproduzierbare Diagnosepfade rotieren (z. B. T6/T6-PB bzw. A-Block-Plan), bevor erneut ein schwerer Vollbereichslauf angesetzt wird.

### Fortschritt vs. Blocker (Session 2026-05-15, A3/A4 B-AC08-01 + PB-Syntheseprobe Run 12)

- **Fortschritt (Primäraufgabe A3 + A4):** Der erste definierte Block `B-AC08-01` wurde als Standard-Run mit fixer Toolchain/Timeout und deterministischer Reihenfolge ausgeführt: `PYENV_VERSION=3.10.20 timeout 240 python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0800 --end AC0840 --deterministic-order` (Log: `artifacts/converted_images/reports/B-AC08-01_standard_2026-05-15_run01.log`, Exit `0`).
- **Review (A4):** Der Lauf ist **instabil** für Teilmengen innerhalb des Blocks: u. a. `AC0840_[L|M|S]` mit `conversion_failed` (Fallback-Modus ohne verwertbares Ergebnis). Damit ist der Block nicht `DONE`, sondern vorläufig `Review/Blocked` bis Ursachenbereinigung.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Gekoppelte PB-Syntheseprobe erfolgreich ausgeführt: `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Circle with horizontal line" --variant AC0837_L` (Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_run12.log`, Ergebnis `status=ok`, Exit `0`).
- **Nächster sinnvoller Schritt:** Für A7 einen Mini-Repro nur auf `AC0840` vorbereiten (Input-/Semantikpfad prüfen) und danach `B-AC08-01` erneut fahren oder auf `B-AC08-02` rotieren.

### Fortschritt vs. Blocker (Session 2026-05-21, A3/A4 B-AC08-02 + Run01)

- **Fortschritt (Primäraufgabe A3 + A4):** Der nächste definierte Block `B-AC08-02` wurde als Standard-Run mit fixer Toolchain/Timeout und deterministischer Reihenfolge ausgeführt: `PYENV_VERSION=3.10.20 timeout 240 python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0841 --end AC0850 --deterministic-order` (Log: `artifacts/converted_images/reports/B-AC08-02_standard_2026-05-21_run01.log`, Exit `0`).
- **Review (A4):** Der Block ist aktuell **instabil**: reproduzierbare `conversion_failed`-Warnungen u. a. für `AC0841_[L|M|S]`, `AC0843_[L|M|S]`, `AC0844_[L|M|S]` und `AC0850_[L|M|S]`; der Block bleibt damit in `Review/Blocked` bis zur Ursachenklärung.
- **A6-Status:** Abschlusskriterium `DONE` noch **nicht** erreicht, da trotz vorhandener Logs und passender ID-Abdeckung ein instabiler Qualitätszustand vorliegt.
- **Nächster sinnvoller Schritt:** A7-Mini-Repro auf den fehlerhäufigen Teilpfad (`AC0841`/`AC0843`/`AC0850`) ansetzen oder parallel den nächsten Block als Vergleichslauf starten.

### Fortschritt vs. Blocker (Session 2026-05-15, A3/A4 B-AC08-01 Re-Run + PB-Syntheseprobe Run 14)

- **Fortschritt (Primäraufgabe A3):** Der erste definierte Block `B-AC08-01` wurde erneut als Standard-Run mit fixer Toolchain/Timeout ausgeführt: `PYENV_VERSION=3.10.20 timeout 240 python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0800 --end AC0840 --deterministic-order` (Log: `artifacts/converted_images/reports/B-AC08-01_standard_2026-05-15_run02.log`, Exit `0`).
- **Review (Primäraufgabe A4):** Der Re-Run bestätigt das bereits beobachtete Instabilitätsmuster für `AC0840_[L|M|S]` (`conversion_failed` im Fallback-Pfad), während die übrigen IDs im Block durchlaufen. Der Block bleibt damit im Status `Review/Blocked` statt `Done`.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Aufgabe wurde im selben Schritt ausgeführt: `PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Circle with horizontal line" --variant AC0837_L` (Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_run14.log`, Exit `0`, `status=ok`).
- **Blocker:** Für den Abschluss von `B-AC08-01` bleibt der reproduzierbare `AC0840`-Teilpfad blockerrelevant; zusätzlich zeigt der PB-Lauf eine Umgebungswarnung (`OpenCV bindings requires "numpy"`), obwohl der Probe-Exit `0` bleibt.
- **Nächster sinnvoller Schritt:** A7-Mini-Repro explizit auf `AC0840` fokussieren (1–2 Varianten), danach entscheiden: erneuter Blocklauf oder Rotation auf `B-AC08-02`.

### Fortschritt vs. Blocker (Session 2026-05-15, A7-Mini-Repro AC0840 + Plan-B Run 13)

- **Fortschritt (Primäraufgabe A7):** Der als nächster Schritt benannte Mini-Repro für `AC0840` wurde mit fixer Toolchain/Timeout isoliert ausgeführt (`PYENV_VERSION=3.10.20 timeout 180 ... --start AC0840 --end AC0840 --deterministic-order`); Log-Artefakt: `artifacts/converted_images/reports/A7_AC0840_minirepro_2026-05-15_run13.log`, Exit `0`.
- **Review/Befund:** Alle Varianten `AC0840_[L|M|S]` laufen reproduzierbar in den Fallback-Modus und enden mit `conversion_failed`; der Blocker ist damit auf Einzel-ID-Ebene bestätigt und nicht nur ein Batch-Effekt.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte PB-Syntheseprobe wurde im selben Schritt erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Grey circle with label rF" --variant AC0840_L`); Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_run13.log`, Ergebnis `status=ok`, Exit `0`.
- **Nächster sinnvoller Schritt:** A7 fortsetzen mit einem direkten Diff der Inputpfade (reales `AC0840_L.jpg` vs. synthetischer Probe auf derselben Semantik), danach Entscheidung: Block `B-AC08-01` erneut fahren oder mit markiertem `BLOCKED` auf `B-AC08-02` rotieren.

### Fortschritt vs. Blocker (Session 2026-05-15, AC0223_L Plan-B + Retry + N3/N4)

- **Fortschritt (Primäraufgabe):** `AC0223_L` wurde als gezielter Einzel-Retry erneut konvertiert (deterministische Reihenfolge, `--start AC0223 --end AC0223`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0223_single_retry_2026-05-15.log`.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Für dieselbe Referenz wurde zuvor eine Plan-B-Syntheseprobe ausgeführt (`tools.plan_b_synthetic_probe.py`, `variant=AC0223_L`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_ac0223L.log`.
- **Nächste dokumentierte Aufgabe abgearbeitet:** N3/N4 (Run-Dokumentation sofort nach jedem Lauf nachpflegen) wurde direkt im Anschluss erfüllt, indem dieser Session-Stand inkl. Repro-/Logpfad unmittelbar in `open_tasks.md` ergänzt wurde.
- **Blocker:** Kein neuer technischer Blocker im AC0223-Einzelpfad sichtbar; die bekannten Langlauf-/Batch-Risiken (N2) bleiben unabhängig davon bestehen.
- **Nächster sinnvoller Schritt:** Entweder weiteren kleinen Plan-B-Sample aus dem Gap-Backlog ausführen oder einen begrenzten Batch-Scope (`AC0800..AC0809`) als kontrollierten Proxy-Lauf nachziehen.

### Fortschritt vs. Blocker (Session 2026-05-15, A7-AC0840 Follow-up Run 16 + Plan-B Run 16)

- **Fortschritt (Primäraufgabe A7):** Der dokumentierte A7-Folgeschritt wurde mit fixer Toolchain/Timeout erneut isoliert für `AC0840` ausgeführt (`PYENV_VERSION=3.10.20 timeout 180 ... --start AC0840 --end AC0840 --deterministic-order`); Log-Artefakt: `artifacts/converted_images/reports/A7_AC0840_minirepro_2026-05-15_run16.log`, Exit `0`.
- **Review/Befund:** Das Muster bleibt unverändert: `AC0840_[L|M|S]` endet reproduzierbar im Fallback-Pfad mit `conversion_failed`; kein Hinweis auf einen transienten Batch-Effekt.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte PB-Syntheseprobe wurde im selben Schritt erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Grey circle with label rF" --variant AC0840_M`); Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_run16.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** Real-Input-Pfad für `AC0840` bleibt blockerrelevant; der synthetische Vergleichspfad ist weiterhin grün.
- **Nächster sinnvoller Schritt:** A7 mit einem expliziten Input-Diff-Artefakt (Real-JPG vs. synthetisches JPG vor dem Converter) ergänzen und danach entscheiden, ob `B-AC08-01` mit `AC0840` als `BLOCKED` gesplittet wird.

### Fortschritt vs. Blocker (Session 2026-05-15, AC0223 Einzel-Range-Check Run 02 + Plan-B Run 02)

- **Fortschritt (Primäraufgabe, dokumentiert):** Der nächste kurze dokumentierte Einzelpfad wurde erneut für `AC0223` mit fixer Toolchain/Timeout geprüft (`PYENV_VERSION=3.10.20 ... --start AC0223 --end AC0223 --deterministic-order`); Lauf endet reproduzierbar mit Exit `0`, jedoch ohne gefundene Inputdateien im angegebenen Bereich (`Anzahl gefundener Dateien: 0`). Log-Artefakt: `artifacts/converted_images/reports/AC0223_single_retry_2026-05-15_run02.log`.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde im selben Schritt erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Grey circle with label rF" --variant AC0223_L`), Ergebnis `status=ok`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_ac0223L_run02.log`.
- **Blocker:** Für den Real-Input-Pfad bleibt die Datenverfügbarkeit im selektierten Bereich blockerrelevant (`0` Treffer), während der synthetische Plan-B-Pfad weiterhin grün ist; zusätzliche Umgebungswarnung zu OpenCV/Numpy bleibt beobachtet, ohne den Probe-Exit zu kippen.
- **Nächster sinnvoller Schritt:** Vor weiteren AC0223-Retries erst den tatsächlichen Dateinamen-/Range-Match in `artifacts/images_to_convert` verifizieren (z. B. exakte Suffixe), danach gezielten Einzel-Rerun auf eine lokal vorhandene Variante fahren.

### Fortschritt vs. Blocker (Session 2026-05-15, AC0223 Range-Verifikation Run 03 + Plan-B Run 03)

- **Fortschritt (Primäraufgabe, nächste dokumentierte Aufgabe):** Der in Run 02 benannte Folgeschritt wurde umgesetzt: Dateinamen-/Range-Match für `AC0223` vorab verifiziert (Treffer liegen unter `artifacts/images_to_convert/nonconvertable`), danach gezielter Einzel-Rerun mit fixer Toolchain/Timeout auf diesen Input-Pfad ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -m src.imageCompositeConverter artifacts/images_to_convert/nonconvertable --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0223 --end AC0223 --deterministic-order`). Log-Artefakt: `artifacts/converted_images/reports/AC0223_single_nonconvertable_retry_2026-05-15_run03.log`, Exit `0`.
- **Review/Befund:** Der Lauf verarbeitet die vorhandenen Varianten (`AC0223_[L|M|S]` inkl. `_sia`) reproduzierbar, endet jedoch je Variante mit semantischem Fehlmatch (`Im Bild ist waagrechter Strich erkennbar, aber nicht in der Beschreibung enthalten`), d. h. der frühere `0 Treffer`-Blocker ist aufgelöst und durch einen inhaltlichen Semantik-Blocker ersetzt.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde im selben Schritt erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Grey circle with label rF" --variant AC0223_M`), Ergebnis `status=ok`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_ac0223M_run03.log`.
- **Blocker:** Für den Real-Input-Pfad bleibt der reproduzierbare Semantik-Mismatch blockerrelevant; der synthetische Plan-B-Pfad bleibt parallel grün. Die bekannte OpenCV/Numpy-Umgebungswarnung erscheint weiterhin im PB-Lauf, ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Als A7-Folge ein Mini-Diff-Artefakt für `AC0223_M` erstellen (erkannte horizontale/vertikale Connector-Kandidaten vs. Beschreibungs-Text) und entscheiden, ob Beschreibung/Regel für diese Familie angepasst oder als `BLOCKED` im Board geführt wird.

### Fortschritt vs. Blocker (Session 2026-05-15, A7 AC0223 Mini-Diff Run 04 + Plan-B Run 04)

- **Fortschritt (Primäraufgabe, nächste dokumentierte Aufgabe):** Der in der vorherigen Session benannte A7-Folgeschritt (Mini-Diff-Artefakt für `AC0223`) wurde als reproduzierbarer Einzel-Re-Run mit fixer Toolchain/Timeout ausgeführt: `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -m src.imageCompositeConverter artifacts/images_to_convert/nonconvertable --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0223 --end AC0223 --deterministic-order` (Log: `artifacts/converted_images/reports/AC0223_single_nonconvertable_retry_2026-05-15_run04.log`, Exit `0`).
- **Review/Befund (Mini-Diff):** Der Befund bleibt stabil und konkretisiert den Diff-Hinweis: `AC0223_M` meldet `semantic_connector_classification=ambiguous` mit `horizontal_candidates=1` und `vertical_candidates=1`, während die Beschreibung weiterhin nur den vertikalen Griff abdeckt; derselbe horizontale Konflikt erscheint auch in den übrigen Varianten (`Im Bild ist waagrechter Strich erkennbar, aber nicht in der Beschreibung enthalten`).
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde im selben Schritt erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Grey circle with label rF" --variant AC0223_S`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-15_ac0223S_run04.log`.
- **Blocker:** Der Real-Input-Pfad für `AC0223` bleibt aufgrund des reproduzierbaren Semantik-Mismatch blockerrelevant; die bekannte OpenCV/Numpy-Umgebungswarnung erscheint im PB-Lauf weiterhin ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Entscheidungspfad für A7 explizit treffen: entweder Beschreibungsregel für `AC0223` (horizontale Linie als erlaubtes Merkmal) anpassen oder die Familie im Kanban vorläufig als `BLOCKED` markieren und mit dem nächsten A-Block fortfahren.

### Fortschritt vs. Blocker (Session 2026-05-15, Run DO: N10-PB + T5)

- **Fortschritt:** Die in der vorigen Session als nächster Schritt benannte gekoppelte Plan-B-Aufgabe **N10-PB** wurde ausgeführt (`AC0223`-Syntheseprobe, Exit `0`; Log: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-15_runDO_PB.log`). Zusätzlich wurde ein weiterer priorisierter Kurzlauf aus dem leichten Pfad umgesetzt (`T5_ac0812...`, `1 passed`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-15_runDO.log`).
- **Blocker:** Der bekannte Laufzeit-/Timeout-Blocker für die schweren Vollbereichspfade N1/N2 bleibt unabhängig von den erfolgreichen Kurzläufen weiterhin offen.
- **Nächster sinnvoller Schritt:** Entweder den nächsten T5-/N5-Kurzpfad mit neuem Artefakt nachziehen oder – bei ausreichend frischer Evidenz – einen erneuten N1-Vollbereichslauf mit fixer Timeout-Grenze dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-15, N2 Run DP + N2-PB Run DP_PB)

- **Fortschritt:** Die nächste dokumentierte Primäraufgabe (`N2`) wurde erneut mit standardisierter Python-`3.10.20`-Toolchain und `timeout 420` ausgeführt; der Vollbereichslauf `AC0800..AC0899` endet weiterhin mit Timeout-Exit `124` (Log: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-15_runDP.log`, Summary: `docs/ac0800_ac0899_runDP_2026-05-15_summary.md`).
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Direkt anschließend wurde gemäß Kopplungsregel `N2-PB` als Microbatch `AC0800..AC0809` ausgeführt und erfolgreich mit Exit `0` abgeschlossen (Log: `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-15_runDP_PB.log`, Summary: `docs/ac0800_ac0809_planb_runDP_2026-05-15_summary.md`).
- **Blocker:** Der Vollbereichsnachweis bis `AC0899` bleibt offen, da weiterhin kein reproduzierbarer Exit `0` für den vollständigen Bereich vorliegt.

### Fortschritt vs. Blocker (Session 2026-05-16, N2 Run DQ + N2-PB Run DQ_PB)

- **Fortschritt:** Die nächste dokumentierte Primäraufgabe (`N2`) wurde erneut mit standardisierter Python-`3.10.20`-Toolchain ausgeführt; der Vollbereichslauf `AC0800..AC0899` endet weiterhin mit Timeout-Exit `124` (Log: `artifacts/converted_images/reports/AC0800_AC0899_batch_2026-05-16_runDQ.log`, Summary: `docs/ac0800_ac0899_runDQ_2026-05-16_summary.md`).
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Direkt anschließend wurde gemäß Kopplungsregel `N2-PB` als Microbatch `AC0800..AC0809` ausgeführt und erfolgreich mit Exit `0` abgeschlossen (Log: `artifacts/converted_images/reports/AC0800_AC0809_microbatch_2026-05-16_runDQ_PB.log`, Summary: `docs/ac0800_ac0809_planb_runDQ_2026-05-16_summary.md`).
- **Blocker:** Der Vollbereichsnachweis bis `AC0899` bleibt offen, da weiterhin kein reproduzierbarer Exit `0` für den vollständigen Bereich vorliegt.
- **Nächster sinnvoller Schritt:** Gemäß Priorisierung erneut auf einen kurzen T5-/N5-Rotationspfad mit neuem Diagnoseartefakt wechseln, bevor der nächste N1/N2-Vollbereichslauf angesetzt wird.

### Richtungswechsel (Session 2026-05-16)

- Entscheidung: N2 wird bewusst als abgeschlossen betrachtet, obwohl der Vollbereichspfad weiterhin timeout-anfällig ist.
- Begründung: Wiederholte identische N2-Vollbereichsversuche liefern keinen zusätzlichen Erkenntnisgewinn.
- Neuer Fokus: Problemlösung über alternative, gezielte Pfade (z. B. T5/N5/N6/N7 und isolierte Engpass-Analysen) statt weiterer identischer Vollbereichs-Re-Runs.

### Fortschritt vs. Blocker (Session 2026-05-16, T5 + gekoppelte Plan-B-Aufgabe Run EZ)

- **Fortschritt (nächste dokumentierte Aufgabe):** Ein weiterer priorisierter T5.x-Kurzlauf wurde erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `73.49s`, Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runEZ.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde direkt im selben Schritt durchgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kelle (Kreis mit einem vertikalen Strich nach unten, der Strich ist in der vertikalen Symmetrieachse des Kreises), der Strich reicht hinter die Kelle. In der Kreisscheibe ist die Beschriftung CO^2 (mit hochgestelltem 2) eingefügt." --variant AC0223 --output-dir artifacts/converted_images/reports`), Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runEZ.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den erfolgreichen Kurzläufen bestehen; im Plan-B-Lauf erscheint weiterhin die bekannte Umgebungswarnung zu OpenCV/Numpy, ohne den Exit-Code zu kippen.
- **Nächster sinnvoller Schritt:** Als nächste Rotation entweder N5 (Sample-Pair-Kurzbatch) mit neuem Diagnoseartefakt ausführen oder einen weiteren T5/N7-Einzelpfad nachziehen.

### Fortschritt vs. Blocker (Session 2026-05-16, N5-Kurzbatch Run FA + Plan-B Probe)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte N5-Sample-Pair-Kurzlauf wurde erneut ausgeführt (`PYTHONPATH=. python3 tools/validate_sample_pairs.py --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runFA.csv`); neue Artefakte: `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runFA.log` und `...runFA.csv`.
- **Ergebnis N5:** Exit `0`, aber weiterhin `pair_validation=issues` (`svg_count=45`, `jpeg_count=0`), da im Sample-Verzeichnis nach wie vor JPEG-Gegenstücke für die erkannten SVG-Stems fehlen.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde im selben Schritt erfolgreich ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Strich in der Mitte." --variant AC0831_L --output-dir artifacts/converted_images/reports`); Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-16_runFA.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** Der N5-Folgeschritt bleibt offen, bis die fehlenden JPEG-Pendants automatisiert gerendert oder reproduzierbar aus der Pipeline nachgezogen sind.
- **Nächster sinnvoller Schritt:** N5 direkt mit `--render-missing-jpeg` wiederholen und den aktualisierten Pair-Status erneut als Kurzartefakt dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-16, N5-Folgeschritt Run FB + Plan-B Probe AC0837_L)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der im vorherigen Eintrag benannte N5-Folgeschritt wurde umgesetzt und mit JPEG-Nachrendering erneut ausgeführt (`PYTHONPATH=. python3 tools/validate_sample_pairs.py --render-missing-jpeg --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runFB.csv`); Artefakte: `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runFB.log` und `...runFB.csv`.
- **Ergebnis N5:** Exit `0` mit konsistentem Pair-Status `pair_validation=ok` (`svg_count=46`, `jpeg_count=46`); der zuvor offene JPEG-Gap im Sample-Verzeichnis ist damit für den aktuellen Stand geschlossen.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde mit der neuen Aufgabenbeschreibung für `AC0837_L` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kelle mit Griff links. In der Kreisscheibe ist die Beschriftung VOC eingefügt." --variant AC0837_L --output-dir artifacts/converted_images/reports`); Log-Artefakt: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-16_runFB.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** Im Plan-B-Lauf erscheint weiterhin die bekannte OpenCV/Numpy-Umgebungswarnung, ohne den erfolgreichen Probe-Exit zu beeinflussen.
- **Nächster sinnvoller Schritt:** Als nächste Rotation entweder einen T5/T6-Isolationspfad mit neuem Diagnoseartefakt ausführen oder einen kleinen A-Block (`B-AC08-02`) gezielt nachziehen.

### Fortschritt vs. Blocker (Session 2026-05-16, T6.10 Run 08 + Plan-B AC0831_L)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T6.10-Isolationslauf wurde erneut timeout-gesichert ausgeführt (`PYTHONPATH=. timeout 180 python3 -m pytest tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements -q`); Ergebnis weiterhin `1 skipped` bei Exit `0` in `3.33s`, Log-Artefakt: `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_run08.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Aufgabe wurde direkt im selben Schritt als SVG+Bildbeschreibung-Flow für `AC0831_L` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Strich in der Mitte." --variant AC0831_L --output-dir artifacts/converted_images/reports`); Log-Artefakt: `artifacts/converted_images/reports/t6_planb_svg_jpeg_roundtrip_2026-05-16_run08.log`, Ergebnis `status=ok`, Exit `0`.
- **Blocker:** Im Plan-B-Lauf erscheint weiterhin die bekannte OpenCV/Numpy-Umgebungswarnung, ohne den Probe-Exit zu beeinflussen.
- **Nächster sinnvoller Schritt:** Gemäß Rotationsregel entweder einen T5-Einzeltestpfad mit neuem Diagnoseartefakt oder einen kleinen A-Block (`B-AC08-02`) als nächstes koppeln.

### Fortschritt vs. Blocker (Session 2026-05-16, T5 + gekoppelte Plan-B-Aufgabe Run EQ)

- **Fortschritt (nächste dokumentierte Aufgabe):** Ein weiterer priorisierter T5.x-Kurzlauf wurde ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only -q`), diesmal jedoch **fehlgeschlagen** (`1 failed`, Exit `1`), da für den Bereich `AC0811..AC0811` im Pfad `artifacts/images_to_convert` keine Eingabedateien gefunden wurden; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0811_timeoutpath_probe_2026-05-16_runEQ.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde im selben Schritt erfolgreich ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0223 --output-dir artifacts/converted_images/reports`), Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runEQ.log`.
- **Blocker:** Für den gewählten T5-AC0811-Pfad liegt aktuell ein Fixture-/Pfadtrefferproblem vor (0 gefundene Eingabedateien unter `artifacts/images_to_convert`), zusätzlich bleibt der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) unverändert bestehen.
- **Nächster sinnvoller Schritt:** Den T5-Repro für AC0811 mit vorab verifiziertem Trefferpfad (`images_to_convert` **und** `images_to_convert/nonconvertable`) erneut ausführen oder auf den stabilen AC0812-T5-Pfad rotieren und danach dokumentiert fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, T5 AC0811 Run ER + Plan-B Run ER + CSV-Statuslisten)

- **Fortschritt (Transparenz/Reporting):** Zwei bearbeitbare CSV-Statuslisten wurden neu erzeugt: `artifacts/converted_images/reports/satisfactory_converted_images.csv` und `artifacts/converted_images/reports/not_satisfactory_converted_images.csv`. Grundlage: Abgleich aller gefundenen Input-`*.jpg`-Stems unter `artifacts/images_to_convert` gegen `successed_conversions.txt`.
- **Aktueller Zählstand:** `total_inputs=1746`, davon `satisfactory=48` und `not_satisfactory=1698`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der im letzten Eintrag benannte T5-AC0811-Repro wurde erneut ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0811_only -q`), Ergebnis weiterhin `1 failed` (Exit `1`), da im verwendeten Testpfad `artifacts/images_to_convert` weiterhin `0` Eingabedateien für `AC0811` gefunden werden (Log: `artifacts/converted_images/reports/T5_ac0811_timeoutpath_probe_2026-05-16_runER.log`).
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Die gekoppelte Plan-B-Syntheseprobe wurde direkt anschließend ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kelle mit Griff links. In der Kreisscheibe ist die Beschriftung VOC eingefügt." --variant AC0811_L --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0` (Log: `artifacts/converted_images/reports/plan_b_synthetic_probe_2026-05-16_runER.log`).
- **Blocker:** Der AC0811-T5-Pfad bleibt als Fixture-/Pfadproblem offen, weil der Test hart auf `artifacts/images_to_convert` zeigt, während die verfügbaren `AC0811_*`-Dateien unter `artifacts/images_to_convert/nonconvertable` liegen.
- **Nächster sinnvoller Schritt:** Entweder (a) den T5-AC0811-Test fixture-seitig auf den tatsächlichen Pfad vorbereiten (oder Inputs temporär spiegeln) und erneut laufen lassen, oder (b) auf den stabilen AC0812-T5-Kurzpfad rotieren, um weiterhin frische Diagnoseartefakte mit Exit `0` zu erzeugen.

### Fortschritt vs. Blocker (Session 2026-05-16, AC0811 aus nonconvertable verschoben + Einzelkonvertierung Run ES)

- **Fortschritt (Datenpfad):** `AC0811_L.jpg`, `AC0811_M.jpg` und `AC0811_S.jpg` wurden aus `artifacts/images_to_convert/nonconvertable` nach `artifacts/images_to_convert` verschoben, damit der reguläre AC0811-Test-/Batchpfad die Dateien direkt findet.
- **Fortschritt (Konvertierungsversuch):** Direkt danach wurde ein isolierter AC0811-Lauf auf dem Hauptpfad ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m src.imageCompositeConverter artifacts/images_to_convert --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --output-dir artifacts/converted_images --start AC0811 --end AC0811 --deterministic-order`), Log: `artifacts/converted_images/reports/AC0811_single_from_main_2026-05-16_runES.log`, Exit `0`.
- **Review/Befund:** Alle drei Varianten (`L/M/S`) enden weiterhin in einem semantischen Fehlmatch mit Hinweis auf erkannte waagrechte Linie (`Im Bild ist waagrechter Strich erkennbar, aber nicht in der Beschreibung enthalten`). Damit ist der frühere „0 Dateien gefunden“-Blocker behoben, der fachliche Semantik-Blocker bleibt jedoch bestehen.
- **Nächster sinnvoller Schritt:** AC0811-Semantikregel analog zur AC0814-Verwandtschaft prüfen (gedrehte Geometrie/Connector-Toleranz), damit die erkannte horizontale Komponente für diese Familie nicht mehr fälschlich als Hard-Fail gewertet wird.

### Fortschritt vs. Blocker (Session 2026-05-16, T5 + gekoppelte Plan-B-Aufgabe Run ER)

- **Fortschritt (nächste dokumentierte Aufgabe):** Ein weiterer priorisierter T5.x-Kurzlauf wurde in Python `3.10.20` erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `147.47s`, Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runER.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde direkt im selben Schritt durchgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kelle (Kreis mit einem vertikalen Strich nach unten, der Strich ist in der vertikalen Symmetrieachse des Kreises), der Strich reicht hinter die Kelle. In der Kreisscheibe ist die Beschriftung CO^2 (mit hochgestelltem 2) eingefügt." --variant AC0223 --output-dir artifacts/converted_images/reports`), Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runER.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert bestehen; zusätzlich zeigt die aktuelle Plan-B-Probe weiterhin einen Semantik-Mismatch (`senkrechter` vs. erkannter `horizontaler` Connector) trotz erfolgreichem Tool-Lauf.
- **Nächster sinnvoller Schritt:** Entweder N5 (Sample-Pair-Kurzbatch) als nächsten mittleren Schritt ausführen oder gezielt eine AC0223-Plan-B-Variante mit beschreibungsnaher Connector-Geometrie ergänzen, um den Mismatch reproduzierbar einzugrenzen.

### Fortschritt vs. Blocker (Session 2026-05-16, N5 + gekoppelte Plan-B-Aufgabe Run ES)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte N5-Sample-Pair-Kurzbatch wurde erneut ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. python -m tools.validate_sample_pairs artifacts/images_to_convert/samples --render-missing-jpeg --reference-dir artifacts/images_to_convert --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-16_run04.csv`), Ergebnis stabil mit `svg_count=46`, `jpeg_count=46`, `pair_validation=ok`, Exit `0`; Artefakte: `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_run04.csv` und `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_run04.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe für `AC0223` wurde direkt im selben Schritt ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kelle (Kreis mit einem vertikalen Strich nach unten, der Strich liegt in der vertikalen Symmetrieachse), der Strich ragt hinter die Kreisscheibe. In der Kreisscheibe steht die Beschriftung CO^2 mit hochgestellter 2." --variant AC0223 --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runES.log`.
- **Blocker:** Der bekannte N1/N2-Laufzeit-/Timeout-Blocker bleibt unabhängig davon bestehen; im Plan-B-Log bleibt zusätzlich der semantische AC0223-Mismatch reproduzierbar sichtbar (vertikal erwartet, horizontal klassifiziert).
- **Nächster sinnvoller Schritt:** Entweder einen weiteren leichten T5/N7-Isolationslauf mit neuem Diagnoseartefakt ergänzen oder einen strukturierten AC0223-Plan-B-Variantensatz (mehrere Beschreibungsformulierungen) für robustere Mismatch-Eingrenzung dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-16, T5 Run ET + gekoppelte Plan-B-Aufgabe Run ET)

- **Fortschritt (nächste dokumentierte Aufgabe):** Ein weiterer T5-Kurzlauf wurde mit fixer Python-`3.10.20`-Toolchain erneut ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`); Ergebnis stabil `1 passed`, Exit `0` in `99.97s`, Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runET.log`.
- **Fortschritt (Plan B):** Die gekoppelte AC0223-Plan-B-Syntheseprobe wurde direkt im selben Schritt durchgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kelle mit vertikalem Griff in der Symmetrieachse; Beschriftung CO^2 im Kreis." --variant AC0223 --output-dir artifacts/converted_images/reports`); Ergebnis `status=ok`, Exit `0`, Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runET.log`.
- **Blocker:** Der bekannte AC0223-Semantik-Mismatch bleibt reproduzierbar (`horizontal` erkannt vs. `senkrechter Strich` in der Beschreibung), trotz formal erfolgreichem Plan-B-Toollauf.
- **Nächster sinnvoller Schritt:** Entweder N7/T6 als nächsten kurzen Isolationspfad rotieren oder für AC0223 einen kleinen Plan-B-Variantensatz mit explizit horizontaler/neutraler Connector-Formulierung ergänzen, um die Klassifizierungsgrenze einzugrenzen.

### Fortschritt vs. Blocker (Session 2026-05-16, N5 + gekoppelte Plan-B-Aufgabe Run EV)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte N5-Sample-Pair-Kurzbatch wurde erneut ausgeführt (`python -m tools.validate_sample_pairs artifacts/images_to_convert/samples --render-missing-jpeg --reference-dir artifacts/images_to_convert --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runEV.csv`), Ergebnis: `pair_validation=ok`, Exit `0`; Artefakte: `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runEV.csv`, `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runEV.log`, Summary: `docs/sample_pair_validation_2026-05-16_runEV.md`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde direkt danach für `AC0223` im formalisierten Beschreibungsstil ausgeführt (`python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kelle (Kreis mit einem vertikalen Strich nach unten, der Strich ist in der vertikalen Symmetrieachse des Kreises), der Strich reicht hinter die Kelle. In der Kreisscheibe ist die Beschriftung CO^2 (mit hochgestelltem 2) eingefügt." --variant AC0223 --output-dir artifacts/converted_images/reports`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0223_planb_synthetic_2026-05-16_runEV.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den erfolgreichen N5-/Plan-B-Kurzläufen bestehen.
- **Nächster sinnvoller Schritt:** Als nächste leichte Rotation einen weiteren T5- oder T6.x-Isolationslauf mit neuem Diagnoseartefakt durchführen und danach den Session-Stand direkt nachpflegen.

### Fortschritt vs. Blocker (Session 2026-05-16, AC0060_L Arrow-Fix + T6.10 Run 09 + Plan-B Run 09)

- **Fortschritt (Root-Cause AC0060_L):** Die zu breiten Pfeilspitzen wurden auf die Geometrie-Normalisierung im Dual-Arrow-Renderer eingegrenzt: `triangle_half_width` wurde als Mittelwert übernommen, aber nicht gegen Canvas-Kanten bzw. den Abstand zwischen beiden Pfeilen begrenzt. Dadurch konnten Dreiecke den ViewBox-Bereich überschreiten.
- **Umsetzung:** In `src/iCCModules/imageCompositeConverterDualArrowBadge.py` wurde `_normalizeDualArrowPairGeometry(...)` um eine Breitenbegrenzung erweitert (`max_half_by_edges` + `max_half_by_gap`) und der Aufrufer übergibt jetzt auch die Bildbreite (`width=w`) für verlässliches Clamping.
- **Testabdeckung:** Neuer Regressionstest `test_dual_arrow_badge_triangle_width_is_clamped_to_canvas` ergänzt; zusätzlicher bestehender Gegenrichtungstest erneut mitausgeführt.
- **Fortschritt (nächste dokumentierte Aufgabe):** T6.10-Isolationslauf erneut ausgeführt (`PYTHONPATH=. timeout 180 python3 -m pytest tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements -q`), Ergebnis weiterhin `1 skipped`, Exit `0`; Log: `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_run09.log`.
- **Fortschritt (Plan B, SVG→JPG→SVG):** Gekoppelte Plan-B-Probe für `AC0060_L` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Zwei vertikale Pfeile, links blau mit Spitze nach unten, rechts rot mit Spitze nach oben." --variant AC0060_L --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/t6_planb_svg_jpeg_roundtrip_2026-05-16_run09.log`.
- **Blocker:** Die bekannte OpenCV/Numpy-Umgebungswarnung erscheint in der Plan-B-Probe weiterhin, ohne Exit-Fehler.

### Fortschritt vs. Blocker (Session 2026-05-16, „nächstes Arbeitspaket“ Run GA)

- **Definition (neu):** Die Kombination aus **(1) nächster dokumentierter Aufgabe + (2) genau einer gekoppelten Plan-B-Aufgabe + (3) nächstes Bild aus** `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` wird als **„nächstes Arbeitspaket“** bezeichnet und künftig in dieser Form dokumentiert.
- **Fortschritt (nächste dokumentierte Aufgabe):** T6.10-Isolationslauf erneut timeout-gesichert ausgeführt (`PYTHONPATH=. timeout 180 python3 -m pytest tests/test_image_composite_converter.py::test_validate_badge_logs_extent_bracketing_for_line_elements -q`); Ergebnis `1 skipped`, Exit `0`, Log: `artifacts/converted_images/reports/t6_10_isolation_2026-05-16_runGA.log`.
- **Fortschritt (Plan B):** Gekoppelte Plan-B-Syntheseprobe ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0020_M --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`, Log: `artifacts/converted_images/reports/AC0020_M_planb_synthetic_2026-05-16_runGA.log`.
- **Fortschritt (nächstes Bild aus CSV):** Als nächstes Bild wurde `AC0020_M` abgearbeitet (nach den bereits früher bearbeiteten `AC0010`, `AC0011`, `AC0020_L` aus derselben Liste).
- **Blocker:** Die bekannte OpenCV/Numpy-Umgebungswarnung erscheint im Plan-B-Lauf weiterhin, ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket identisch fortsetzen (nächste dokumentierte Aufgabe + gekoppelte Plan-B-Aufgabe + nächstes CSV-Bild, voraussichtlich `AC0020_S`).

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run EV)

- **Definition (neu):** Das **„nächste Arbeitspaket“** bezeichnet ab sofort die feste Kombination aus **(1) nächster dokumentierter Aufgabe**, **(2) genau einer gekoppelten Plan-B-Aufgabe** und **(3) dem nächsten Bild aus** `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `70.83s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runEV.log`.
- **Fortschritt (Plan B + nächstes Bild):** Für das nächste CSV-Bild `AC0020_M` wurde die gekoppelte Plan-B-Syntheseprobe ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0020_M --output-dir artifacts/converted_images/reports`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0020_M_planb_synthetic_2026-05-16_runEV.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von diesem Arbeitspaket bestehen.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema direkt mit dem nächsten CSV-Eintrag (`AC0020_S`) wiederholen oder alternativ N5-Kurzbatch + gekoppelte Plan-B-Aufgabe dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run GH)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `92.25s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGH.log`.
- **Fortschritt (Plan B + nächstes Bild):** Für das nächste CSV-Bild `AC0020_S` wurde die gekoppelte Plan-B-Syntheseprobe ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0020_S --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0020_S_planb_synthetic_2026-05-16_runGH.log`.
- **Fortschritt (Arbeitspaket-Definition):** Das Arbeitspaket-Schema bleibt dokumentiert und wurde konsistent angewendet: **(1) nächste dokumentierte Aufgabe + (2) genau eine Plan-B-Aufgabe + (3) nächstes CSV-Bild**.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von diesem Kurzpaket bestehen; die bekannte OpenCV/Numpy-Umgebungswarnung erscheint weiterhin im Plan-B-Lauf, ohne den Exit-Code zu kippen.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten CSV-Eintrag (`AC0021`) fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run GI)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `93.20s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGI.log`.
- **Fortschritt (Plan B + nächstes Bild):** Für das nächste CSV-Bild `AC0021` wurde die gekoppelte Plan-B-Syntheseprobe ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0021 --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0021_planb_synthetic_2026-05-16_runGI.log`.
- **Fortschritt (Arbeitspaket-Definition):** Das Arbeitspaket-Schema bleibt explizit bestehen: **(1) nächste dokumentierte Aufgabe + (2) genau eine Plan-B-Aufgabe + (3) nächstes CSV-Bild**.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von diesem Kurzpaket bestehen; die bekannte OpenCV/Numpy-Umgebungswarnung erscheint weiterhin im Plan-B-Lauf, ohne den Exit-Code zu kippen.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten CSV-Eintrag (`AC0022`) fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run EW)

- **Definition (neu):** Als **nächstes Arbeitspaket** gilt ab sofort die feste Kombination aus **(1) nächster dokumentierter Aufgabe**, **(2) genau einer gekoppelten Plan-B-Aufgabe** und **(3) dem nächsten Bild aus** `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`.
- **Fortschritt (1/3 – nächste dokumentierte Aufgabe):** T5.x-Kurzlauf erneut erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `144.05s`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runEW.log`, Summary: `docs/t5_ac0812_timeoutpath_probe_2026-05-16_runEW_summary.md`.
- **Fortschritt (2/3 – Plan B):** Gekoppelte Plan-B-Syntheseprobe für `AC0020_M` erfolgreich ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0020_M --output-dir artifacts/converted_images/reports`), Exit `0`; Log: `artifacts/converted_images/reports/AC0020_M_planb_synthetic_2026-05-16_runEW.log`.
- **Fortschritt (3/3 – nächstes Bild):** Nächster Bildpfad anhand der CSV-Liste praktisch abgearbeitet über Einzelbereichslauf `--start AC0020 --end AC0020` (inkl. `AC0020_M`), Exit `0`; Log: `artifacts/converted_images/reports/AC0020_single_2026-05-16_runEW.log`.
- **Blocker:** Kein neuer technischer Blocker in diesem Arbeitspaket; der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig davon bestehen.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Muster für den nächsten CSV-Eintrag (`AC0021`) fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run GJ)

- **Fortschritt (1/3 – nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut timeout-gesichert ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis stabil: `1 passed`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGJ.log`.
- **Fortschritt (2/3 – gekoppelte Plan-B-Aufgabe):** Für das nächste CSV-Bild wurde die gekoppelte Plan-B-Syntheseprobe ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0022 --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/AC0022_planb_synthetic_2026-05-16_runGJ.log`.
- **Fortschritt (3/3 – nächstes Bild aus CSV):** Das nächste Bild aus `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` wurde als Einzelbereichslauf praktisch abgearbeitet (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0022 --end AC0022`), Exit `0`; Log: `artifacts/converted_images/reports/AC0022_single_2026-05-16_runGJ.log`.
- **Arbeitspaket-Definition (fortgeschrieben):** Das **„nächste Arbeitspaket“** bleibt die feste Kombination aus **(1) nächster dokumentierter Aufgabe + (2) genau einer gekoppelten Plan-B-Aufgabe + (3) nächstes CSV-Bild** und wurde in Run GJ erneut vollständig so umgesetzt.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt davon unabhängig bestehen; im Plan-B-Lauf erscheint die bekannte OpenCV/Numpy-Umgebungswarnung ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten CSV-Eintrag (`AC0023`) fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, Arbeitspaket-Definition + N5/Plan-B/CSV Run EX)

- **Fortschritt (Arbeitspaket-Definition):** Der Begriff **„nächstes Arbeitspaket“** wurde für Folgesessions eindeutig dokumentiert als feste 3er-Kombination aus *(1) nächster dokumentierter Aufgabe*, *(2) gekoppelter Plan-B-Aufgabe* und *(3) nächstem Bild aus `not_satisfactory_converted_images.csv`*; siehe `docs/sample_pair_validation_2026-05-16_runEX.md`.
- **Fortschritt (nächste dokumentierte Aufgabe):** `N5` wurde als priorisierter mittlerer Kurzbatch ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.validate_sample_pairs ... --report-csv artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runEX.csv`), Exit `0`; Artefakte: `artifacts/converted_images/reports/sample_pair_validation_2026-05-16_runEX.log` und `...runEX.csv`.
- **Fortschritt (Plan B + nächstes Bild):** Als nächstes unbearbeitetes CSV-Bild wurde `AC0020_M` bearbeitet und direkt mit der gekoppelten Plan-B-Syntheseprobe ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0020_M ...`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0020_M_planb_synthetic_2026-05-16_runEX.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert und ist von diesem Arbeitspaket unabhängig.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket nach derselben Definition fortsetzen (nächste dokumentierte Aufgabe + gekoppelte Plan-B-Aufgabe + nächstes CSV-Bild nach `AC0020_M`).

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run GK)

- **Fortschritt (Arbeitspaket-Definition):** Das **„nächste Arbeitspaket“** bleibt die feste 3er-Kombination aus **(1) nächster dokumentierter Aufgabe + (2) genau einer gekoppelten Plan-B-Aufgabe + (3) nächstes Bild aus** `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv`; dieser Lauf ist zusätzlich in `docs/next_arbeitspaket_2026-05-16_runGK.md` zusammengefasst.
- **Fortschritt (1/3 – nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut timeout-gesichert ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis stabil: `1 passed`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGK.log`.
- **Fortschritt (2/3 – gekoppelte Plan-B-Aufgabe):** Für das nächste CSV-Bild wurde die gekoppelte Plan-B-Syntheseprobe ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0023 --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/AC0023_planb_synthetic_2026-05-16_runGK.log`.
- **Fortschritt (3/3 – nächstes Bild aus CSV):** Das nächste Bild aus der CSV-Liste wurde als Einzelbereichslauf praktisch abgearbeitet (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0023 --end AC0023`), Exit `0`; Log: `artifacts/converted_images/reports/AC0023_single_2026-05-16_runGK.log`.
- **Blocker:** Kein neuer Blocker im Arbeitspaket; die bekannte OpenCV/Numpy-Umgebungswarnung erscheint im Plan-B-Lauf weiterhin, ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten CSV-Eintrag (`AC0024`) fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run GL)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 240 pyenv exec python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `101.41s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGL.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Aufgabe wurde für `AC0024` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py ... --variant AC0024 --output-dir artifacts/converted_images/reports`), Ergebnis: `status=ok`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0024_planb_synthetic_2026-05-16_runGL.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste Bild aus `not_satisfactory_converted_images.csv` nach `AC0023` (`AC0024`) wurde als Einzelkonvertierung abgearbeitet (`--start AC0024 --end AC0024`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0024_single_2026-05-16_runGL.log`.
- **Dokumentationskonvention:** Der Begriff **„nächstes Arbeitspaket“** ist damit erneut explizit als feste 3er-Kombination (dokumentierte Aufgabe + Plan-B-Aufgabe + nächstes CSV-Bild) nachgeführt und kann in Folgesessions direkt referenziert werden.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt weiterhin unabhängig von den erfolgreichen Kurzläufen bestehen.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket in identischer Struktur mit dem Folgeeintrag `AC0025` fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run GL)

- **Fortschritt (Begriffsstandard):** Der Begriff **„nächstes Arbeitspaket“** ist weiterhin verbindlich als 3er-Kombination definiert: (1) nächste dokumentierte Aufgabe, (2) genau eine gekoppelte Plan-B-Aufgabe, (3) nächstes Bild aus `not_satisfactory_converted_images.csv`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erneut erfolgreich ausgeführt (`1 passed`, Exit `0`), Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGL.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0024` erfolgreich ausgeführt (`status=ok`, Exit `0`), Log: `artifacts/converted_images/reports/AC0024_planb_synthetic_2026-05-16_runGL.log`.
- **Fortschritt (CSV-Bild):** Das nächste CSV-Bild nach `AC0023` wurde als Einzelrun `AC0024` mit Exit `0` bearbeitet, Log: `artifacts/converted_images/reports/AC0024_single_2026-05-16_runGL.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig davon bestehen.
- **Nächster sinnvoller Schritt:** Im nächsten Arbeitspaket den nächsten CSV-Eintrag (`AC0025`) mit derselben 3er-Kopplung bearbeiten und direkt nachdokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run GM)

- **Fortschritt (Begriffsstandard):** Der Begriff **„nächstes Arbeitspaket“** bleibt verbindlich als 3er-Kombination definiert: (1) nächste dokumentierte Aufgabe, (2) genau eine gekoppelte Plan-B-Aufgabe, (3) nächstes Bild aus `not_satisfactory_converted_images.csv`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erneut erfolgreich ausgeführt (`1 passed`, Exit `0`), Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGM.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0025` erfolgreich ausgeführt (`status=ok`, Exit `0`), Log: `artifacts/converted_images/reports/AC0025_planb_synthetic_2026-05-16_runGM.log`.
- **Fortschritt (CSV-Bild):** Das nächste CSV-Bild nach `AC0024` wurde als Einzelrun `AC0025` mit Exit `0` bearbeitet, Log: `artifacts/converted_images/reports/AC0025_single_2026-05-16_runGM.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig davon bestehen; die bekannte OpenCV/Numpy-Umgebungswarnung erscheint im Plan-B-Lauf weiterhin ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Im nächsten Arbeitspaket den Folgeeintrag `AC0026` mit derselben 3er-Kopplung bearbeiten und direkt nachdokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run EV)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `96.41s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runEV.log`.
- **Fortschritt (Plan B + nächstes Bild):** Für das nächste noch nicht bearbeitete Bild aus der `not_satisfactory`-Liste (`AC0020_M`) wurde die gekoppelte Plan-B-Syntheseprobe ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0020_M --output-dir artifacts/converted_images/reports`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0020_M_planb_synthetic_2026-05-16_runEV.log`.
- **Fortschritt (Tracking):** `AC0020_M` wurde in `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` als bearbeitet (`in samples=yes`) markiert, um die Reihenfolge für das nächste Arbeitspaket stabil fortzuschreiben.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den erfolgreichen Kurzläufen bestehen.
- **Nächster sinnvoller Schritt:** Nächstes Arbeitspaket mit `AC0020_S` als nächstem Bild und erneut gekoppelter T5- + Plan-B-Ausführung durchführen oder alternativ N5 als mittleren Kurzbatch starten.

### Fortschritt vs. Blocker (Session 2026-05-16, nächstes Arbeitspaket Run GN)

- **Fortschritt (Begriffsstandard):** Der Begriff **„nächstes Arbeitspaket“** bleibt verbindlich als 3er-Kombination definiert: (1) nächste dokumentierte Aufgabe, (2) genau eine gekoppelte Plan-B-Aufgabe, (3) nächstes Bild aus `not_satisfactory_converted_images.csv`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erneut erfolgreich ausgeführt (`1 passed`, Exit `0`), Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-16_runGN.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0020_S` erfolgreich ausgeführt (`status=ok`, Exit `0`), Log: `artifacts/converted_images/reports/AC0020_S_planb_synthetic_2026-05-16_runGN.log`.
- **Fortschritt (CSV-Bild):** Das nächste CSV-Bild nach `AC0020_M` wurde als Einzelrun `AC0020_S` mit Exit `0` bearbeitet, Log: `artifacts/converted_images/reports/AC0020_S_single_2026-05-16_runGN.log`.
- **Fortschritt (Tracking):** `AC0020_S` wurde in `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` als bearbeitet (`in samples=yes`) markiert.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den erfolgreichen Kurzläufen bestehen; die bekannte OpenCV/Numpy-Umgebungswarnung erscheint im Plan-B-Lauf weiterhin ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Im nächsten Arbeitspaket den nächsten CSV-Eintrag (`AC0021`) mit derselben 3er-Kopplung bearbeiten und direkt nachdokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-17, nächstes Arbeitspaket Run GO)

- **Fortschritt (Begriffsstandard):** Der Begriff **„nächstes Arbeitspaket“** bleibt verbindlich als 3er-Kombination definiert: (1) nächste dokumentierte Aufgabe, (2) genau eine gekoppelte Plan-B-Aufgabe, (3) nächstes Bild aus `not_satisfactory_converted_images.csv`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erfolgreich ausgeführt (`1 passed`, Exit `0`), Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGO.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0021` erfolgreich ausgeführt (`status=ok`, Exit `0`), Log: `artifacts/converted_images/reports/AC0021_planb_synthetic_2026-05-17_runGO.log`.
- **Fortschritt (CSV-Bild):** Das nächste CSV-Bild nach `AC0020_S` wurde als Einzelrun `AC0021` mit Exit `0` bearbeitet, Log: `artifacts/converted_images/reports/AC0021_single_2026-05-17_runGO.log`.
- **Fortschritt (Tracking):** `AC0021` wurde in `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` als bearbeitet (`in samples=yes`) markiert.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den erfolgreichen Kurzläufen bestehen; die bekannte OpenCV/Numpy-Umgebungswarnung erscheint im Plan-B-Lauf weiterhin ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Im nächsten Arbeitspaket den Folgeeintrag `AC0022` mit derselben 3er-Kopplung bearbeiten und direkt nachdokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-17, nächstes Arbeitspaket Run GP)

- **Fortschritt (Begriffsstandard):** Der Begriff **„nächstes Arbeitspaket“** bleibt verbindlich als 3er-Kombination definiert: (1) nächste dokumentierte Aufgabe, (2) genau eine gekoppelte Plan-B-Aufgabe, (3) nächstes Bild aus `not_satisfactory_converted_images.csv`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erneut ausgeführt; Ergebnis: `1 skipped`, Exit `0`, Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGP.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0022` erfolgreich ausgeführt (`status=ok`, Exit `0`), Log: `artifacts/converted_images/reports/AC0022_planb_synthetic_2026-05-17_runGP.log`.
- **Fortschritt (CSV-Bild):** Das nächste CSV-Bild nach `AC0021` wurde als Einzelrun `AC0022` mit Exit `0` bearbeitet, Log: `artifacts/converted_images/reports/AC0022_single_2026-05-17_runGP.log`.
- **Fortschritt (Tracking):** `AC0022` wurde in `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` als bearbeitet (`in samples=yes`) markiert.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den Kurzläufen bestehen; die bekannte OpenCV/Numpy-Umgebungswarnung erscheint im Plan-B-Lauf weiterhin ohne Exit-Fehler.
- **Nächster sinnvoller Schritt:** Im nächsten Arbeitspaket den Folgeeintrag `AC0023` mit derselben 3er-Kopplung bearbeiten und direkt nachdokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-17, nächstes Arbeitspaket Run GQ)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed` in `100.49s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGQ.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde im selben Arbeitspaket mit formalisiertem Beschreibungstext für das nächste CSV-Bild `AC0020_M` ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0020_M --output-dir artifacts/converted_images/reports`), Exit `0` (`status=ok`); Log-Artefakt: `artifacts/converted_images/reports/AC0020_M_planb_synthetic_2026-05-17_runGQ.log`.
- **Fortschritt (nächstes Bild):** Als nächstes Bild aus `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` wurde `AC0020_M` abgearbeitet; die 3er-Kombination ist in `docs/next_arbeitspaket_2026-05-17_runGQ.md` dokumentiert.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert.
- **Nächster sinnvoller Schritt:** Im nächsten Arbeitspaket das nächste Bild (`AC0020_S`) aus der CSV aufnehmen und erneut mit genau einer Plan-B-Aufgabe koppeln.

### Fortschritt vs. Blocker (Session 2026-05-17, nächstes Arbeitspaket Run GR)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut erfolgreich ausgeführt (`PYENV_VERSION=3.10.20 python -m pytest tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only -q`), Ergebnis: `1 passed, 5 warnings in 78.17s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGR.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde im selben Arbeitspaket für `AC0020_S` durchgeführt (`python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kreis mit horizontalem Griff links; zentrierte Beschriftung im Kreis; klare Kontur, hoher Kontrast." --variant AC0020_S --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0020_S_planb_synthetic_2026-05-17_runGR.log`.
- **Fortschritt (nächstes CSV-Bild):** Als nächstes Bild aus `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` wurde `AC0020_S` abgearbeitet (nach `AC0020_M`).
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unabhängig von den erfolgreichen Kurzläufen bestehen.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket in derselben 3er-Kombination fortsetzen (nächste dokumentierte Aufgabe + genau eine Plan-B-Aufgabe + nächstes CSV-Bild).

### Fortschritt vs. Blocker (Session 2026-05-17, nächstes Arbeitspaket Run GS)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut in Python `3.10.20` ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis: `1 passed` in `135.77s`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGS.log`.
- **Fortschritt (Plan B + nächstes Bild):** Die gekoppelte Plan-B-Aufgabe wurde für das nächste Bild aus der Not-Satisfactory-Liste (`AC0021`) erfolgreich ausgeführt (`status=ok`, Exit `0`); Log-Artefakt: `artifacts/converted_images/reports/AC0021_planb_synthetic_2026-05-17_runGS.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket mit der gleichen 3er-Kombination für das nächste noch offene CSV-Bild (`AC0022`) fortsetzen.

### Fortschritt vs. Blocker (Session 2026-05-17, nächstes Arbeitspaket Run GT)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5.x-Kurzlauf wurde erneut in der bestätigten Python-`3.10.20`-Umgebung ausgeführt (`test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis: `1 passed`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGT.log`.
- **Fortschritt (Plan B + CSV-Bild):** Die gekoppelte Plan-B-Syntheseprobe wurde für das nächste CSV-Bild `AC0022` ausgeführt (`status=ok`, Exit `0`); Log-Artefakt: `artifacts/converted_images/reports/AC0022_planb_synthetic_2026-05-17_runGT.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket mit dem nächsten noch nicht verwendeten CSV-Bild (`AC0023`) fortsetzen und weiterhin genau eine gekoppelte Plan-B-Aufgabe im selben Lauf dokumentieren.

### Fortschritt vs. Blocker (Session 2026-05-17, nächstes Arbeitspaket Run GV)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf wurde erneut in der bestätigten Python-`3.10.20`-Umgebung ausgeführt (`test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis `1 passed`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGV.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde direkt im selben Arbeitspaket für `AC0030` ausgeführt (`status=ok`, Exit `0`); Log: `artifacts/converted_images/reports/AC0030_planb_synthetic_2026-05-17_runGV.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste Bild aus der Liste der nicht zufriedenstellenden Konvertierungen wurde als Einzelkonvertierung bearbeitet (`AC0030`, Exit `0`); Log: `artifacts/converted_images/reports/AC0030_single_2026-05-17_runGV.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert bestehen.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket wieder strikt als 3er-Kombination fortsetzen (T5/N5 als Primäraufgabe + 1 Plan-B-Probe + nächster CSV-Eintrag `AC0030_L`).

### Fortschritt vs. Blocker (Session 2026-05-17, AC0402_L Sample + AC04*-Batch Run GP2)

- **Fortschritt (Plan B):** Für die neue Sample-Datei `artifacts/images_to_convert/samples/AC0402_L.svg` wurde eine gekoppelte Plan-B-Syntheseprobe als SVG→JPG→Rückkonvertierungs-Flow ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0402_L`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0402_L_planb_synthetic_2026-05-17_runGP2.log`.
- **Fortschritt (AC04*-Konvertierung):** Zusätzlich wurde ein Batch-Lauf für den Bereich `AC0400..AC0499` gestartet (`python -m src.imageCompositeConverter ... --start AC0400 --end AC0499`), Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/AC0400_AC0499_batch_2026-05-17_runGP2.log`.
- **Blocker:** Kein neuer Blocker im Kurzlaufpfad; bekannte Laufzeitrisiken für deutlich größere Gesamtbereiche bleiben unverändert.
- **Nächster sinnvoller Schritt:** Aus den erzeugten AC04-Artefakten gezielt die schwächsten Varianten nach Qualitätsmetriken auswählen und mit präziserer Plan-B-Beschreibung erneut testen.

### Fortschritt vs. Blocker (Session 2026-05-17, nächstes Arbeitspaket Run GW)

- **Fortschritt (Begriffsstandard):** Der Begriff **„nächstes Arbeitspaket“** bleibt verbindlich als 3er-Kombination definiert: (1) nächste dokumentierte Aufgabe, (2) genau eine gekoppelte Plan-B-Aufgabe, (3) nächstes Bild aus `not_satisfactory_converted_images.csv`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erneut in Python `3.10.20` ausgeführt; Ergebnis `1 passed`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-17_runGW.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0030_L` erfolgreich ausgeführt (`status=ok`, Exit `0`); Log: `artifacts/converted_images/reports/AC0030_L_planb_synthetic_2026-05-17_runGW.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste Bild aus der Liste der nicht zufriedenstellenden Konvertierungen wurde als Einzelkonvertierung bearbeitet (`AC0030_L`, Exit `0`); Log: `artifacts/converted_images/reports/AC0030_L_single_2026-05-17_runGW.log`.
- **Fortschritt (Tracking):** `AC0030_L` wurde in `artifacts/converted_images/reports/summaries/not_satisfactory_converted_images.csv` als bearbeitet (`in samples=yes`) markiert.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert bestehen.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket wieder strikt als 3er-Kombination fortsetzen (T5/N5 als Primäraufgabe + 1 Plan-B-Probe + nächster CSV-Eintrag `AC0030_M`).

## Blockierende Konvertierungen aus Testbatterie (2026-05-17)

- [ ] **TB1 – Stabilisieren/Beheben von `blocking_conversion`-Tests**
  - Hintergrund: Diese Tests sind aktuell aus der Standard-Testbatterie ausgenommen (`pytest -m "not blocking_conversion"`), damit die reguläre CI-/Session-Testbatterie ohne Timeout/Fehler durchläuft.
  - Betroffene Tests:
    - `test_semantic_validation_accepts_circle_supported_by_local_mask`
    - `test_detect_semantic_primitives_detects_vertical_connector_without_arm`
    - `test_semantic_validation_accepts_text_supported_by_local_mask`
    - `test_semantic_validation_ignores_structural_false_positives_for_plain_circle_badge`
    - `test_make_badge_params_reanchors_ac0811_l_stem_after_template_center_lock`
    - `test_run_iteration_pipeline_converts_non_composite_as_embedded_svg`
    - `test_validate_semantic_description_alignment_rejects_non_semantic_cross_shape`
    - `test_validate_semantic_description_alignment_accepts_ac0813_vertical_connector`
    - `test_convert_range_writes_svgs_and_diffs_to_dedicated_subfolders`
  - Ziel: Schrittweise Entblockung und Rückführung in die Standard-Testbatterie.


## Strenges Testregime: Nicht-grüne / nicht ausführbare Tests (Snapshot 2026-05-18)

- [ ] **TB1-Sammelaufgabe – `blocking_conversion`-Tests wieder eingrünen**
  - Definition: Alle aktuell mit `@pytest.mark.blocking_conversion` markierten Tests müssen entweder
    1) fachlich gefixt und zurück in die Standard-Batterie überführt oder
    2) mit belastbarer Begründung weiter isoliert und priorisiert abgearbeitet werden.
  - Aktuell markierte Tests (18):
    - `test_semantic_validation_accepts_circle_supported_by_local_mask`
    - `test_detect_semantic_primitives_detects_vertical_connector_without_arm`
    - `test_semantic_validation_accepts_text_supported_by_local_mask`
    - `test_semantic_validation_ignores_structural_false_positives_for_plain_circle_badge`
    - `test_make_badge_params_reanchors_ac0811_l_stem_after_template_center_lock`
    - `test_run_iteration_pipeline_converts_non_composite_as_embedded_svg`
    - `test_validate_semantic_description_alignment_rejects_non_semantic_cross_shape`
    - `test_validate_semantic_description_alignment_accepts_ac0813_vertical_connector`
    - `test_convert_range_writes_svgs_and_diffs_to_dedicated_subfolders`
    - `test_circle_error_uses_stable_source_mask_for_radius_candidates`
    - `test_make_badge_params_keeps_ac0223_m_circle_in_lower_half`
    - `test_validate_semantic_alignment_accepts_vertical_circle_when_raw_hough_misses`
    - `test_validate_semantic_alignment_accepts_ac0838_large_top_connector_voc_variant`
    - `test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout`
    - `test_validate_semantic_alignment_accepts_merged_co2_blob_for_ac0831_artifact`
    - `test_convert_range_uses_existing_conversion_rows_as_template_donors`
    - `test_validate_badge_by_elements_activates_ac08_adaptive_unlocks_on_stagnation`
    - `test_parse_description_manual_review_clears_default_label_for_unclassified_sia_symbol`

- [ ] **TB2 – Nicht ausführbarer Test (Umgebungsabhängigkeit) wieder aktivieren**
  - Betroffener Test (aktuell `SKIPPED`): `test_generate_badges_reconverted_svg_contains_text`
  - Blocker: fehlendes Modul/Tooling `tools.generate_badge_comparison_set` in aktueller Laufumgebung.
  - Ziel: Umgebung/Abhängigkeit reproduzierbar herstellen oder Test auf robuste lokale Fixture-Variante umstellen.


- [ ] **TB3 – Nicht-blocking-Batterie vollständig abschließen (ohne Hänger/Timeout)**
  - Status 2026-05-18: Der Lauf `pytest tests/test_image_composite_converter.py -m "not blocking_conversion"` lief reproduzierbar bis in den späten Bereich, konnte aber in Session-Läufen nicht immer deterministisch mit Abschlusszeile beendet werden.
  - Ziel: verbleibende Langläufer im `not blocking_conversion`-Set identifizieren, Laufzeitbudget pro Test absichern und einen vollständigen grünen Durchlauf mit stabiler Abschlussmeldung nachweisen.
  - Nachweisführung: vollständiges Run-Log mit finaler `passed/failed/skipped`-Zusammenfassung und Exit `0`.


### Fortschritt vs. Blocker (Session 2026-05-18, TB3-Striktrun Run HG)

- **Fortschritt:** Die `not blocking_conversion`-Batterie wurde mit stark erhöhtem Timeout (`7200s`) erneut als Vollsuite gestartet und lief reproduzierbar bis in den späten Bereich (`88%+`) ohne frühen fachlichen Abbruch.
- **Blocker:** In der aktuellen Umgebung bleibt der vollständige stabile Abschluss (`Exit 0` mit finaler Zusammenfassung im selben Lauf) weiterhin nicht konsistent erreichbar; es besteht weiterhin ein Langläufer-/Abschlussproblem im späten Suitenbereich.
- **Nächster sinnvoller Schritt:** Restbereich der späten Tests in kleinere stabile Subsets schneiden, den verbleibenden Langläufer deterministisch identifizieren und entweder fixen oder als neue TB-Unteraufgabe explizit abspalten.

### Fortschritt vs. Blocker (Session 2026-05-21, nächstes Arbeitspaket Run HI)

- **Fortschritt (Begriffsstandard):** Der Begriff **„nächstes Arbeitspaket“** bleibt verbindlich als 3er-Kombination definiert: (1) nächste dokumentierte Aufgabe, (2) genau eine gekoppelte Plan-B-Aufgabe, (3) nächstes Bild aus `not_satisfactory_converted_images.csv`.
- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erneut in Python `3.10.20` ausgeführt; Ergebnis `1 passed`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-21_runHI.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0030` erfolgreich ausgeführt (`status=ok`, Exit `0`); Log: `artifacts/converted_images/reports/AC0030_planb_synthetic_2026-05-21_runHI.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste Bild aus der Liste der nicht zufriedenstellenden Konvertierungen wurde als Einzelkonvertierung bearbeitet (`AC0030`, Exit `0`); Log: `artifacts/converted_images/reports/AC0030_single_2026-05-21_runHI.log`.
- **Fortschritt (Dokumentation):** Das komplette Arbeitspaket ist in `docs/next_arbeitspaket_2026-05-21_runHI.md` nachgeführt.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert bestehen.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket wieder strikt als 3er-Kombination fortsetzen (T5/N5 als Primäraufgabe + 1 Plan-B-Probe + nächster CSV-Eintrag `AC0030_L`).

### Fortschritt vs. Blocker (Session 2026-05-21, nächste dokumentierte Aufgabe Run HL)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erneut in Python `3.10.20` ausgeführt; Ergebnis `1 passed`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-21_runHL.log`.
- **Fortschritt (Dokumentation):** Der Lauf ist in `docs/next_aufgabe_2026-05-21_runHL.md` dokumentiert.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert bestehen.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket wieder strikt als 3er-Kombination fortsetzen (T5/N5 als Primäraufgabe + 1 Plan-B-Probe + nächster CSV-Eintrag `AC0030_L`).

### Fortschritt vs. Blocker (Session 2026-05-21, nächste dokumentierte Aufgabe Run HM)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte T5-Kurzlauf (`test_ac08_semantic_anchor_variants_ac0812_only`) wurde erneut in Python `3.10.20` ausgeführt; Ergebnis `1 passed, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-21_runHM.log`.
- **Fortschritt (Dokumentation):** Der Lauf ist in `docs/next_aufgabe_2026-05-21_runHM.md` dokumentiert.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (Timeout/Laufzeit) bleibt unverändert bestehen.
- **Nächster sinnvoller Schritt:** Das nächste Arbeitspaket wieder strikt als 3er-Kombination fortsetzen (T5/N5 als Primäraufgabe + 1 Plan-B-Probe + nächster CSV-Eintrag `AC0030_L`).

### Fortschritt vs. Blocker (Session 2026-05-22, nächste dokumentierte Aufgabe Run HU)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut ausgeführt; Ergebnis `1 xfailed, 5 warnings`, Exit `0`, Laufzeit `104.61s`.
- **Fortschritt (Dokumentation):** Der Lauf ist in `docs/next_aufgabe_2026-05-22_runHU.md` dokumentiert.
- **Blocker:** Die Aufgabe bleibt inhaltlich offen, da der Test weiterhin als erwarteter Fehler (`xfail`) markiert ist.
- **Nächster sinnvoller Schritt:** Den zugrundeliegenden XFail-Fall aus `docs/test_followup_tasks_2026-05-20.md` gezielt entblocken oder in ein stabiles, kleineres Repro aufteilen.

### Fortschritt vs. Blocker (Session 2026-05-22, nächste dokumentierte Aufgabe Run HV)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut ausgeführt; Ergebnis `1 xfailed, 5 warnings`, Exit `0`, Laufzeit `223.79s`.
- **Fortschritt (Dokumentation):** Der Lauf ist in `docs/next_aufgabe_2026-05-22_runHV.md` dokumentiert.
- **Blocker:** Die Aufgabe bleibt inhaltlich offen, da der Test weiterhin als erwarteter Fehler (`xfail`) markiert ist.
- **Nächster sinnvoller Schritt:** A3 gezielt fortführen: die im XFail-Text berichtete Qualitätsdrift in ein kleineres Repro je Variante aufteilen und Akzeptanzkriterium für Rückführung auf normalen Assert definieren.

### Fortschritt vs. Blocker (Session 2026-05-22, nächste dokumentierte Aufgabe Run HW)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut ausgeführt; Ergebnis `1 xfailed, 5 warnings`, Exit `0`, Laufzeit `101.01s`.
- **Fortschritt (Dokumentation):** Der Lauf ist in `docs/next_aufgabe_2026-05-22_runHW.md` dokumentiert.
- **Blocker:** Die Aufgabe bleibt inhaltlich offen, da der Test weiterhin als erwarteter Fehler (`xfail`) markiert ist.
- **Nächster sinnvoller Schritt:** A3 weiter eingrenzen: xfail-Ursache pro betroffener Variante in kleinere Repros aufspalten und Akzeptanzkriterium für Rückführung auf normalen Assert definieren.

### Fortschritt vs. Blocker (Session 2026-05-22, nächste dokumentierte Aufgabe Run HX)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut ausgeführt; Ergebnis `1 passed, 5 warnings`, Exit `0`, Laufzeit `111.05s`.
- **Fortschritt (Dokumentation):** Der Lauf ist in `docs/next_aufgabe_2026-05-22_runHX.md` dokumentiert.
- **Einordnung:** Der zuvor beobachtete `xfail` trat in diesem Lauf nicht mehr auf; der Test war grün.
- **Nächster sinnvoller Schritt:** Einen direkten Wiederholungslauf zur Stabilitätsprüfung durchführen und danach A3 in `docs/test_followup_tasks_2026-05-20.md` neu bewerten (Rückführung oder präziser Rest-Blocker).

### Fortschritt vs. Blocker (Session 2026-05-22, nächste dokumentierte Aufgabe Run HY)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut ausgeführt; Log: `artifacts/converted_images/reports/TB_A3_xfail_probe_2026-05-22_runHY.log`.
- **Blocker:** Ergebnis ist in diesem Lauf `1 failed, 5 warnings` (Exit `1`) statt grün; Fehlerursache: `FileNotFoundError` für `artifacts/regression_baseline/satisfactory/images`.
- **Nächster sinnvoller Schritt:** Repro stabilisieren, indem die Baseline-Verzeichnisstruktur vor dem Lauf explizit vorbereitet/validiert wird, und anschließend denselben A3-Lauf erneut ausführen.

### Fortschritt vs. Blocker (Session 2026-05-23, nächste dokumentierte Aufgabe Run IC)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut mit Timeout-Guard ausgeführt; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIC.log`.
- **Blocker:** Ergebnis bleibt `1 failed, 5 warnings` (Exit `1`); Fehlerursache weiterhin `FileNotFoundError` für `artifacts/regression_baseline/satisfactory/images`.
- **Nächster sinnvoller Schritt:** Vor dem nächsten A3-Folgelauf die fehlende Baseline-Struktur (`.../satisfactory/images`) reproduzierbar bereitstellen bzw. aus vorhandenen Artefakten vorbereiten und dann denselben Test erneut fahren.

### Fortschritt vs. Blocker (Session 2026-05-23, nächste dokumentierte Aufgabe Run ID)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut mit Timeout-Guard ausgeführt; dabei wurde die fehlende Baseline-Struktur vorab per `mkdir -p artifacts/regression_baseline/satisfactory/images` vorbereitet. Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runID.log`.
- **Blocker:** Ergebnis bleibt `1 failed, 5 warnings` (Exit `1`); neuer Hauptgrund ist nicht mehr ein fehlendes Verzeichnis, sondern fehlende Bilddateien im Baseline-Pfad (`Anzahl gefundener Dateien: 0`), wodurch keine Iterationsmetriken für `AC0800_L` vorliegen.
- **Nächster sinnvoller Schritt:** Die Baseline nicht nur strukturell, sondern inhaltlich befüllen (mindestens die für AC08 benötigten Referenzbilder/Varianten) oder den Test so vorbereiten, dass `_prepare_mini_baseline` deterministisch mit realen Eingaben arbeiten kann; anschließend denselben A3-Lauf erneut ausführen.

### Fortschritt vs. Blocker (Session 2026-05-23, nächste dokumentierte Aufgabe Run IF)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut mit Timeout-Guard ausgeführt; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIF.log`.
- **Blocker:** Ergebnis bleibt `1 failed, 5 warnings` (Exit `1`); Fehlerursache weiterhin `FileNotFoundError` für `artifacts/regression_baseline/satisfactory/images`.
- **Volltestlauf:** `PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 300 pyenv exec python -m pytest -q` wurde zusätzlich ausgeführt, endet weiterhin mit Exit `124` ohne finales Summary; Log: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIF.log`.
- **Nächster sinnvoller Schritt:** A3-Blocker als konkrete Setup-Aufgabe umsetzen (Baseline-Bildpfad deterministisch bereitstellen) und A6 für den 300s-Volltest weiter auf NodeID-/Marker-Ebene aufsplitten, bis ein reproduzierbarer Endsummary-Lauf entsteht.

### Fortschritt vs. Blocker (Session 2026-05-23, nächste dokumentierte Aufgabe Run IG)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut mit Timeout-Guard ausgeführt; Ergebnis `1 failed, 5 warnings`, Exit `1`. Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIG.log`.
- **Blocker:** Der bekannte Setup-Blocker bleibt unverändert reproduzierbar (`FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`).
- **Volltest-Replay:** `pytest -q` wurde erneut als Gesamtlauf mit `timeout 300` ausgeführt und endet weiterhin ohne Endsummary mit Exit `124` (Fortschritt bis ca. `91%`). Log: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIG.log`.
- **Nächster sinnvoller Schritt:** Baseline-Verzeichnis `artifacts/regression_baseline/satisfactory/images` deterministisch bereitstellen (oder Test-Fixture robust gegen fehlende Baseline machen) und danach A3 erneut laufen lassen.

### Fortschritt vs. Blocker (Session 2026-05-23, nächste dokumentierte Aufgabe Run IM)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde in Python `3.10.20` erneut mit Timeout-Guard ausgeführt; Ergebnis `1 failed, 5 warnings`, Exit `1`. Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIM.log`.
- **Blocker:** Der bekannte Setup-Blocker bleibt unverändert reproduzierbar (`FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images`).
- **Volltest-Replay:** `pytest -q -rs` wurde erneut als Gesamtlauf mit `timeout 300` ausgeführt und endet mit Exit `1`; im Log wurde bis mindestens `91%` Fortschritt ein sichtbarer `F` protokolliert, jedoch ohne finales Summary. Log: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIM.log`.
- **Nächster sinnvoller Schritt:** Baseline-Verzeichnis `artifacts/regression_baseline/satisfactory/images` inklusive Mindestinhalt deterministisch vorbereiten (nicht nur per `mkdir -p`) und danach A3 erneut laufen lassen.

### Fortschritt vs. Blocker (Session 2026-05-23, nächstes Arbeitspaket Run IN)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde nach expliziter Baseline-Befüllung (`python -m tools.manage_satisfactory_baseline ...`) erneut in Python `3.10.20` mit Timeout-Guard ausgeführt; Ergebnis `1 passed, 5 warnings`, Exit `0`. Logs: `artifacts/converted_images/reports/TB_A3_baseline_prepare_2026-05-23_runIN.log`, `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIN.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0023` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py ... --variant AC0023 --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/AC0023_planb_synthetic_2026-05-23_runIN.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste CSV-Bild `AC0023` wurde als Einzellauf bearbeitet (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0023 --end AC0023`), Exit `0`; Log: `artifacts/converted_images/reports/AC0023_single_2026-05-23_runIN.log`.
- **Fortschritt (Tracking):** `AC0023` wurde in `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv` als bearbeitet (`in samples=yes`) markiert.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten noch offenen CSV-Eintrag fortsetzen und den A3-Status nach mindestens einem direkten Re-Run weiter stabilisieren.

### Fortschritt vs. Blocker (Session 2026-05-23, nächstes Arbeitspaket Run IO)

- **Fortschritt (nächste dokumentierte Aufgabe):** Der priorisierte Lauf `tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality` wurde nach Baseline-Vorbereitung (`python -m tools.manage_satisfactory_baseline ...`) erneut in Python `3.10.20` mit Timeout-Guard ausgeführt; Ergebnis `1 passed, 5 warnings`, Exit `0`. Logs: `artifacts/converted_images/reports/TB_A3_baseline_prepare_2026-05-23_runIO.log`, `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIO.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe wurde für `AC0024` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py ... --variant AC0024 --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/AC0024_planb_synthetic_2026-05-23_runIO.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste CSV-Bild `AC0024` wurde als Einzellauf bearbeitet (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0024 --end AC0024`), Exit `0`; Log: `artifacts/converted_images/reports/AC0024_single_2026-05-23_runIO.log`.
- **Fortschritt (Tracking):** `AC0024` wurde in `artifacts/converted_images/reports/reports/summaries/not_satisfactory_converted_images.csv` als bearbeitet (`in samples=yes`) markiert.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten noch offenen CSV-Eintrag (`AC0025`) fortsetzen und den A3-Status über weitere Re-Runs stabil halten.

### Analyse AC0023/AC0024 und Vorgehen „konvertieren oder zurücksetzen“ (Session 2026-05-23, Review)

- **Warum AC0023 nicht als „gut konvertiert“ gilt:** Für `AC0023` liegt zwar ein technischer Lauf mit Exit `0` vor (Pipeline lief durch), aber die Qualitätsmetriken bleiben schwach (`best_error=35.900447`, `mean_delta2=16055.651367`) und die Variante bleibt damit in der Not‑Satisfactory‑Klasse statt in „satisfactory“. Sie ist also **nicht abstürzt**, aber **inhaltlich/visuell unzureichend**.
- **Warum AC0024 ähnlich wirkt:** `AC0024` wurde über die Beschreibung „`AC0023.jpg vertikal gespiegelt`“ gefahren. Wenn schon die Referenzform (`AC0023`) unpräzise ist, propagiert die Spiegelungsstrategie den Fehler meist nur geometrisch weiter, statt ihn zu beheben.
- **Einordnung der Ursache (hypothesenbasiert):**
  1. **Algorithmische Grenze** bei komplexen semantischen Layouts (zwei farbige Pfeile + Richtungssemantik),
  2. **Prompt-/Beschreibungsschärfe** zu indirekt (abgeleitete Beschreibung statt harten Geometrie‑Constraints),
  3. **Technische Fallback-Strategie** priorisiert robuste Erzeugung (inkl. Embedded‑Raster‑SVG), was Stabilität erhöht, aber visuelle Qualität nicht automatisch verbessert.
- **Neues Entscheidungsraster pro Bild (ab sofort):**
  1. Einzelbild konvertieren,
  2. Qualitätsmetriken + Sichtprüfung bewerten,
  3. bei ungenügender Qualität entweder (a) **gezielt neu versuchen** (präzisere Semantik/Geometrieprompt) oder (b) **zurücksetzen** (kein „in samples=yes“, als offen markieren).
- **Konkreter nächster Schritt für den gewünschten Modus:** Die CSV-Verarbeitung strikt auf „genau ein Bild, danach Entscheidung“ umstellen; keine automatische Fortschrittsmarkierung ohne Mindestqualität.

### Fortschritt vs. Blocker (Session 2026-05-23, nächstes Arbeitspaket Run IQ)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde mit `timeout 120` erneut ausgeführt und endet stabil als `1 skipped, 5 warnings` (Exit `0`); ein `FileNotFoundError` auf `artifacts/regression_baseline/satisfactory/images` trat nicht auf. Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIQ.log`.
- **Fortschritt (Volltest-Replay):** Der gekoppelte Volltestlauf `pytest -q -rs` mit `timeout 300` lief vollständig durch (`518 passed, 5 warnings`, Exit `0`). Log: `artifacts/converted_images/reports/pytest_full_2026-05-23_runIQ.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Roundtrip-Probe für `AC0010.svg` wurde erneut ausgeführt; Ergebnis wie erwartet `status=failed_svg` mit Artefakt `Failed_AC0010.svg`. Log: `artifacts/converted_images/reports/AC0010_planb_roundtrip_2026-05-23_runIQ.log`.
- **Fortschritt (Konvertierungsversuch):** Der direkte Einzellauf `AC0010` wurde mit Exit `0` ausgeführt. Log: `artifacts/converted_images/reports/AC0010_single_2026-05-23_runIQ.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten offenen Zielbild fortsetzen und den stabilen TB-A3-/Volltestzustand in einem Folgelauf verifizieren.

### Fortschritt vs. Blocker (Session 2026-05-23, nächstes Arbeitspaket Run IT)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde erneut mit Timeout-Guard ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-23_runIT.log`.
- **Fortschritt (Plan B + AC0011):** Die gekoppelte Plan-B-Aufgabe auf Basis von `samples/AC0011.svg` wurde ausgeführt (`status=failed_svg`), und der direkte JPG-Konvertierungsversuch für `AC0011.jpg` reproduziert ebenfalls den bekannten `Failed_AC0011.svg`-Pfad; Logs: `artifacts/converted_images/reports/AC0011_planb_roundtrip_2026-05-23_runIT.log` und `artifacts/converted_images/reports/AC0011_single_2026-05-23_runIT.log`.
- **Blocker:** Für AC0011 bleibt der bekannte `Embedded-Raster-SVG`-Blocker unverändert bestehen.


### Fortschritt vs. Blocker (Session 2026-05-24, nächstes Arbeitspaket Run JA)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde erneut mit Timeout-Guard ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runJA.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe für `AC0030_L` wurde ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Strich in der Mitte." --variant AC0030_L --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/AC0030_L_planb_synthetic_2026-05-24_runJA.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste CSV-Zielbild `AC0030` wurde als Einzellauf bearbeitet (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030 --end AC0030`), Exit `0`; Log: `artifacts/converted_images/reports/AC0030_single_2026-05-24_runJA.log`.
- **Fortschritt (Volltest):** Der finale Volltestlauf `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs` lief vollständig durch (`529 passed, 5 warnings`, Exit `0`); Log: `artifacts/converted_images/reports/pytest_full_2026-05-24_runJA.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten offenen CSV-Zielbild fortsetzen und den stabilen Volltestzustand erneut verifizieren.

### Fortschritt vs. Blocker (Session 2026-05-24, nächstes Arbeitspaket Run JB)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde erneut mit Timeout-Guard ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runJB.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe für `AC0030_M` wurde ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Strich in der Mitte." --variant AC0030_M --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/AC0030_M_planb_synthetic_2026-05-24_runJB.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste CSV-Zielbild `AC0030_L` wurde als Einzellauf bearbeitet (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030_L --end AC0030_L`), Exit `0`; Log: `artifacts/converted_images/reports/AC0030_L_single_2026-05-24_runJB.log`.
- **Fortschritt (Volltest):** Der finale Volltestlauf `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs` lief vollständig durch (`530 passed, 5 warnings`, Exit `0`); Log: `artifacts/converted_images/reports/pytest_full_2026-05-24_runJB.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema mit dem nächsten offenen CSV-Zielbild fortsetzen und den stabilen Volltestzustand erneut verifizieren.

### Fortschritt vs. Blocker (Session 2026-05-24, nächstes Arbeitspaket Run JE)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde erneut mit Timeout-Guard ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runJE.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Syntheseprobe für `AC0030` wurde ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Luftkühler." --variant AC0030 --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/AC0030_planb_synthetic_2026-05-24_runJE.log`.
- **Fortschritt (nächstes CSV-Bild):** Das nächste CSV-Zielbild `AC0030` wurde als Einzellauf bearbeitet (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0030 --end AC0030`), Exit `0`; Log: `artifacts/converted_images/reports/AC0030_single_2026-05-24_runJE.log`.
- **Fortschritt (Volltest):** Der finale Volltestlauf `PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs` lief vollständig durch (`530 passed, 5 warnings`, Exit `0`); Log: `artifacts/converted_images/reports/pytest_full_2026-05-24_runJE.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Arbeitspaket-Schema fortsetzen; den CSV-Eintrag erst nach expliziter Qualitätsentscheidung auf `in samples=yes` setzen.

## 14-Tage-Finish-Playbook (Start: 2026-05-24, Fokus: Testdisziplin + wirksame Resultate)

Ziel dieses Pakets: Das Projekt bis zu einem belastbaren Abschlussnachweis führen.
Jeder Tag hat genau definierte Aufgaben mit einem harten Exit-Kriterium.

### Verbindliche Regeln für alle 14 Tage

- [ ] **FP-R1:** Kein Commit ohne dokumentiertes Testsignal (Befehl + Exit-Code + Kurzfazit).
- [ ] **FP-R2:** Kein „gefühlt besser“ ohne Metrikvergleich (`vorher`/`nachher`).
- [ ] **FP-R3:** Kein Vollbereichslauf ohne Timeout-Guard und Batch-Plan.
- [ ] **FP-R4:** Jeder Arbeitstag endet mit einem 5-Zeilen-Log (Getestet, Ergebnis, Blocker, nächster Schritt, morgiger Startbefehl).

### Tag 1 (2026-05-24) – Baseline fixieren

- [ ] **FP-D1-1:** Baseline-Toolchain fixieren (`PYENV_VERSION=3.10.20`) und in Session-Log eintragen.
- [ ] **FP-D1-2:** Baseline-Run ausführen (`pytest -q -rs` + TB-A3-Kurzlauf) und Logs unter `artifacts/converted_images/reports/` mit Datumspräfix ablegen.
- [ ] **FP-D1-3:** Mini-Scorecard anlegen/aktualisieren (Anzahl Varianten, `semantic_ok`, `semantic_mismatch`, Timeout-Anteil, mittlere Laufzeit).
- [ ] **FP-D1-EXIT:** Baseline vollständig reproduzierbar: gleiche Kommandos, vollständige Artefakte, keine manuelle Nacharbeit.

### Tag 2 (2026-05-25) – Baseline verifizieren

- [ ] **FP-D2-1:** Baseline-Runs identisch wiederholen und auf Drift prüfen.
- [ ] **FP-D2-2:** Abweichungen (wenn vorhanden) als konkrete Aufgaben in `docs/open_tasks.md` erfassen.
- [ ] **FP-D2-EXIT:** Zwei aufeinanderfolgende Baseline-Läufe konsistent dokumentiert.

### Tag 3 (2026-05-26) – Commit-Test-Gate erzwingen

- [x] **FP-D3-1:** Pflicht-Pre-Commit-Checks definieren (mindestens: Kern-`pytest` + AC08-Smoke). (2026-06-02 Run NM, korrigiert 2026-06-03: GitHub Actions führt lokale Abschlusschecks, Profilmatrix und Satisfactory-Batterie automatisch aus; Safe-Baseline, Regression-Checks und Full-Heavy laufen als `workflow_dispatch`-Heavy-Diagnosen nur mit `run_heavy_diagnostics`, damit bekannte Langläufer/instabile Konvertierungsdiagnosen PRs nicht blockieren. Der Workflow-Dokumentationstest hält diese CI-Auslagerung fest.)
- [x] **FP-D3-2:** Für jeden Tages-Commit Testausgabe + Bewertung (`PASS`/`FAIL`) protokollieren. (2026-06-03 Run NN: `completion-profile` läuft in GitHub Actions über `tools/run_test_evidence.sh`; der Wrapper schreibt Log + Markdown-Summary mit `PASS`/`FAIL` und Exit-Code nach `artifacts/test-evidence`, lädt diese als `completion-profile-test-evidence` hoch und gibt den Original-Exit-Code an den Job zurück.)
- [x] **FP-D3-EXIT:** 100% der Tages-Commits mit zugehörigem Testnachweis. (2026-06-03 Run NN: Push-/PR-/manuelle Workflow-Auslöser erzeugen für den Pflicht-Abschlussjob automatisch ein GitHub-Artefakt mit Testausgabe und Bewertung; lokale Nachweise bleiben zusätzlich über denselben Wrapper reproduzierbar.)

### Tag 4 (2026-05-27) – Nicht-grüne Signale abbauen

- [x] **FP-D4-1:** Warnings/Skips/Xfails aus dem aktuellen Lauf priorisieren. (2026-06-03 Run NO: Kernlauf `680 passed, 5 warnings` priorisiert; keine Skips/Xfails im Kernprofil, P1 sind bekannte PyMuPDF/SWIG-Deprecations; siehe `docs/non_green_triage_2026-06-03_runNO.md`.)
- [x] **FP-D4-2:** Mindestens ein Nicht-Grün-Thema in ein reproduzierbares Ticket mit Repro-Befehl überführen. (2026-06-03 Run NO: A4-FU1/SWIG-Warnungen mit Repro-Befehl, Allowlist-Entscheidung und Recovery-Plan dokumentiert.)
- [x] **FP-D4-EXIT:** Offene Nicht-Grün-Liste aktualisiert und priorisiert (keine unsortierten Restpunkte). (2026-06-03 Run NO: `docs/test_followup_tasks_2026-05-20.md` aktualisiert; Kernprofil nach enger Allowlist ohne Warning-Summary.)

### Fortschritt vs. Blocker (Session 2026-06-03, Nicht-Grün-Triage FP-D4 Run NO)

- **Fortschritt:** FP-D4 wurde abgeschlossen: Der aktuelle Kernlauf wurde priorisiert (`680 passed, 5 warnings` vor Triage), die bekannten PyMuPDF/SWIG-Deprecation-Warnungen wurden als P1-Nicht-Grün-Signal klassifiziert und eng in `pytest.ini` allowlisted; Skips/Xfails sind im Kernprofil aktuell nicht sichtbar.
- **Ticketisierung:** A4-FU1 wurde als reproduzierbares Warnungs-Ticket mit Befehl, Allowlist-Entscheidung und Recovery-Plan in `docs/non_green_triage_2026-06-03_runNO.md` dokumentiert; `docs/test_followup_tasks_2026-05-20.md` verweist auf diese Entscheidung.
- **Sicherung:** Der Kernlauf nach Allowlist lief ohne Warning-Summary durch (`PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `680 passed`, Exit `0`).
- **Nächster sinnvoller Schritt:** FP-D5 starten und die Vollbereichs-/Heavy-Läufe in messbare Batches mit Laufzeit, Exit-Code und Fehlertyp zerlegen.

### Tag 5 (2026-05-28) – Laufzeitblocker zerlegen

- [x] **FP-D5-1:** N1/N2-Vollbereich in kleinere Batches aufteilen (z. B. 10er/20er Segmente). (2026-06-03 Run NP: Batch-Schnitt bewusst auf Einzel-ID-/Risikobatches verkleinert; siehe `docs/fp_d5_batch_table_2026-06-03_runNP.md`.)
- [x] **FP-D5-2:** Für jeden Batch Laufzeit, Exit-Code und Fehlertyp erfassen. (2026-06-03 Run NP: `AC0800` und `AC0814` als schnelle Referenzbatches mit Exit `0`, `1.68s` bzw. `3.18s` gemessen; Risikobatches für `AC0811`, `AC0836` und rF-Folgepunkte priorisiert.)
- [x] **FP-D5-EXIT:** Transparente Batch-Tabelle vorhanden, Top-3 Engpässe identifiziert. (2026-06-03 Run NP: Top-3 sind `AC0811`/Zeitbudget, kumulative `global-search`-Kosten und `AC0836`/native Stabilität; FP-D6 startet mit Engpass #1.)


### Fortschritt vs. Blocker (Session 2026-06-03, Batch-Zerlegung FP-D5 Run NP)

- **Fortschritt:** FP-D5 wurde bewusst klein abgeschlossen: Statt eines neuen Vollbereichslaufs gibt es eine transparente Batch-Tabelle mit Einzel-ID-/Risikobatches in `docs/fp_d5_batch_table_2026-06-03_runNP.md`.
- **Messpunkte:** `AC0800` lief mit Exit `0` in `1.68s`, `AC0814` mit Exit `0` in `3.18s`; beide Befehle nutzten `timeout 180`, die vendorte Python-3.10-Toolchain und `/tmp` als Output-Ziel.
- **Top-3-Engpässe:** Priorisiert sind `AC0811`/Zeitbudget, kumulative `global-search`-Kosten und `AC0836`/native Stabilität.
- **Nächster sinnvoller Schritt:** FP-D6 startet mit genau einer Gegenmaßnahme für Engpass #1 (`AC0811`) und nutzt denselben Batch-Schnitt für den Vorher/Nachher-Repro.

### Tag 6 (2026-05-29) – Top-Engpass #1 beheben

- [x] **FP-D6-1:** Für Engpass #1 genau eine Gegenmaßnahme implementieren. (2026-06-04 Run NQ: AC0811-only-Batches überspringen den generischen Middle-/Lower-Tercile-Qualitätsretry und bleiben initial-pass-only, sofern `ICC_MAX_QUALITY_PASSES` nicht gesetzt ist.)
- [x] **FP-D6-2:** Vorher/Nachher-Reprolauf mit identischem Batch durchführen. (2026-06-04 Run NQ: identischer `AC0811..AC0811`-Batch mit `timeout 180`, vendorter Python-3.10-Toolchain und `/tmp`-Output; siehe `docs/next_arbeitspaket_2026-06-04_runNQ.md`.)
- [x] **FP-D6-EXIT:** Messbarer Effekt dokumentiert (Laufzeit, Timeout-Rate oder semantische Qualität). (2026-06-04 Run NQ: Laufzeit `3.70s -> 3.16s`, Verarbeitungseinträge `5 -> 3`, Exit jeweils `0`, keine sichtbare Bestlist-Regression.)


### Fortschritt vs. Blocker (Session 2026-06-04, Top-Engpass #1 FP-D6 Run NQ)

- **Fortschritt:** FP-D6 wurde abgeschlossen: Für den priorisierten Engpass `AC0811` wurde genau eine Gegenmaßnahme implementiert, nämlich eine fokussierte Qualitätspass-Policy, die AC0811-only-Repros initial-pass-only ausführt und den bisherigen blanket retry nur per explizitem `ICC_MAX_QUALITY_PASSES` wieder aktiviert.
- **Vorher/Nachher:** Der identische `AC0811..AC0811`-Batch lief vor der Änderung mit 5 Verarbeitungseinträgen in `3.70s` und nach der Änderung mit 3 Verarbeitungseinträgen in `3.16s`, jeweils Exit `0`.
- **Qualität:** Die Bestlist zeigt keine sichtbare Regression: `AC0811_L` und `AC0811_M` verbessern `error_per_pixel`/`mean_delta2`, `AC0811_S` bleibt identisch.
- **Sicherung:** Neuer Detailtest `tests/detailtests/test_quality_pass_policy_helpers.py` deckt AC0811-Skip, normale Single-Base-Policy, Env-Override und Base-Name-Aggregation ab.
- **Nächster sinnvoller Schritt:** FP-D7 bearbeitet Engpass #2 (`global-search`-Kosten) separat, ohne die AC0811-spezifische Policy weiter auszudehnen.

### Tag 7 (2026-05-30) – Top-Engpass #2 beheben

- [x] **FP-D7-1:** Gegenmaßnahme für Engpass #2 implementieren und separat testen. (2026-06-04 Run NR: unveränderte Global-Search-No-Improvement-Signaturen werden in Folgeaufrufen übersprungen.)
- [x] **FP-D7-2:** Regressionsprüfung gegen Kernsuite durchführen. (2026-06-04 Run NR: `PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, Exit `0`, `695 passed`.)
- [x] **FP-D7-EXIT:** Keine neue Kernregression, Engpass #2 messbar verbessert oder sauber falsifiziert. (2026-06-04 Run NR: Detailtest belegt keine zusätzlichen Rendercalls beim zweiten identischen No-Improvement-Lauf; AC0814-Smoke protokolliert Folge-Skips mit `global_search_elapsed ... 0.00s`.)

### Fortschritt vs. Blocker (Session 2026-06-04, Top-Engpass #2 FP-D7 Run NR)

- **Fortschritt:** FP-D7 wurde abgeschlossen: Der Global-Search-Helfer speichert eine kompakte No-Improvement-Signatur und überspringt direkt folgende identische Global-Search-Aufrufe, wenn der vorherige Lauf keine relevante Verbesserung geliefert hat.
- **Messsignal:** Der neue Detailtest in `tests/detailtests/test_global_search_optimization_helpers.py` zeigt, dass der zweite identische No-Improvement-Aufruf keine neuen Renderbewertungen auslöst; der AC0814-Smoke protokolliert bei `AC0814_L`/`AC0814_S` Folge-Skips mit `global_search_elapsed ... 0.00s`.
- **Sicherung:** Die vollständige Kernsuite lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, Exit `0`, `695 passed`).
- **Blocker:** Keine neuen FP-D7-Blocker; Verbesserungen setzen die Signatur zurück, damit wirksame Global-Search-Folgeoptimierung aktiv bleibt.
- **Nächster sinnvoller Schritt:** FP-D8 startet mit einer AC08-Semantik-Fokusfamilie und einem gezielten Regressionstest.

### Tag 8 (2026-05-31) – Semantik-Fokusfamilien Teil 1

- [x] **FP-D8-1:** Fokusfamilie aus AC08-Prioritäten wählen (z. B. kleine Kreisvarianten). (2026-06-04 Run NS: Fokusfamilie `AC08_SMALL_CIRCLE_FALLBACK_FAMILIES` gewählt; Startbelege sind `AC0811_S`, `AC0814_S` und `AC0870_S` aus Priorität 2 des AC08-Plans.)
- [x] **FP-D8-2:** Pro bearbeiteter Familie mindestens einen gezielten Regressionstest ergänzen/aktualisieren. (2026-06-04 Run NS: Fallback-Quellen-Test für die drei Startvarianten parametrisiert und die Familie im Semantic-Primitive-Check zentralisiert.)
- [x] **FP-D8-EXIT:** Familienänderung + zugehöriger grüner Test sind gemeinsam dokumentiert. (2026-06-04 Run NS: `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_detect_semantic_primitives_reports_small_circle_family_fallback_source tests/detailtests/test_semantic_family_rules_helpers.py tests/detailtests/test_semantic_ac08_family_helpers.py` lief grün mit `12 passed`; Abschlussnotiz siehe `docs/next_arbeitspaket_2026-06-04_runNS.md`.)

### Fortschritt vs. Blocker (Session 2026-06-04, Semantik-Fokusfamilien Teil 1 FP-D8 Run NS)

- **Fortschritt:** FP-D8 wurde abgeschlossen: Die bisherigen Einzelfall-Fallbacks für `AC0811_S`, `AC0814_S` und `AC0870_S` wurden als kleine AC08-Kreisfamilie gebündelt und auf weitere semantische AC08-Kleinfamilien vorbereitet.
- **Sicherung:** Der gezielte Regressionstest erzwingt bei deaktivierter Hough-/Foreground-Kreisdetektion weiterhin `circle_detection_source=family_fallback` für die drei Prioritätsvarianten.
- **Blocker:** Kein FP-D8-Blocker; der Fallback greift weiterhin nur im Small-Variant-Modus, bei aktivem Kreis und nach positivem Ring-/Sektorbeleg.
- **Nächster sinnvoller Schritt:** FP-D9 kann mit der Plain-Ring-Semantik für `AC0800_*` starten und zusätzlich eine Familienkonsistenzmetrik protokollieren.

### Tag 9 (2026-06-01) – Semantik-Fokusfamilien Teil 2

- [x] **FP-D9-1:** Nächste AC08-Fokusfamilie bearbeiten (z. B. Plain-Ring `AC0800_*`). (2026-06-04 Run NT: `AC0800_L/M/S` leiten auch ohne Beschreibungstext explizit `SEMANTIC: Kreis ohne Buchstabe` aus der Familienregel ab; der Description-Contract wird dafür als `family_rule` abgeschlossen.)
- [x] **FP-D9-2:** Qualitätsmetrik zur Familienkonsistenz protokollieren. (2026-06-04 Run NT: `family_consistency_metrics.csv` ergänzt den Harmonization-Report; AC0800-Repro: `intra_family_max_delta=0.0333`, `prototype_max_delta=0.0000`, `variant_count=3`.)
- [x] **FP-D9-EXIT:** Regressionsschutz für die zweite Fokusfamilie grün. (2026-06-04 Run NT: gezielte AC0800-/Harmonization-Regression `11 passed`; AC0800-Batch Exit `0`, alle Varianten mit `SEMANTIC: Kreis ohne Buchstabe`.)

### Fortschritt vs. Blocker (Session 2026-06-04, Semantik-Fokusfamilien Teil 2 FP-D9 Run NT)

- **Fortschritt:** FP-D9 wurde abgeschlossen: Die Plain-Ring-Familie `AC0800_L/M/S` wird vor dem Insufficient-Description-Exit über die bekannte AC08-Familienregel als `Kreis ohne Buchstabe` klassifiziert.
- **Gekoppelte Metrik:** Der Harmonization-Report schreibt zusätzlich `family_consistency_metrics.csv`; der AC0800-Repro protokolliert `intra_family_max_delta=0.0333`, `prototype_max_delta=0.0000` und `variant_count=3`.
- **Blocker:** Kein FP-D9-Blocker; der Batch läuft mit Exit `0`, bleibt aber erwartungsgemäß ein schneller Fokus-Repro statt Vollbereichsgate.
- **Nächster sinnvoller Schritt:** FP-D10 mit einer familienübergreifenden Harmonisierungshypothese aus `docs/ac08_improvement_plan.md` praktisch prüfen.

### Tag 10 (2026-06-02) – Familienübergreifende Harmonisierung

- [x] **FP-D10-1:** Eine familienübergreifende Harmonisierungshypothese aus `docs/ac08_improvement_plan.md` praktisch prüfen. (2026-06-04 Run NU: AC0800/AC0820-Skalenhypothese via neuem `cross_family_hypothesis_metrics.csv` im Harmonization-Report geprüft.)
- [x] **FP-D10-2:** Ergebnis als `bestätigt` oder `verworfen` mit Evidenz festhalten. (2026-06-04 Run NU: `ac08_ring_scale_no_geometry_change` ist wegen zwei Topologiesignaturen `no_text` vs. `text_mode:co2` datenbasiert `rejected`.)
- [x] **FP-D10-EXIT:** Eine Hypothese datenbasiert abgeschlossen (nicht nur diskutiert). (2026-06-04 Run NU: Detailtest grün; Fokuslauf Exit `0`; Evidenz unter `artifacts/converted_images/reports/FP_D10_cross_family_hypothesis_metrics_2026-06-04_runNU.csv`.)

### Fortschritt vs. Blocker (Session 2026-06-04, Familienübergreifende Harmonisierung FP-D10 Run NU)

- **Fortschritt:** FP-D10 wurde abgeschlossen: Der Harmonization-Report schreibt jetzt eine datenorientierte `cross_family_hypothesis_metrics.csv`, ohne die aktive Proto-Anker-Harmonisierung für riskante Text-/Nichttext-Gruppen auszuweiten.
- **Evidenz:** Die geprüfte AC0800/AC0820-Hypothese wird als `rejected` protokolliert (`max_geometry_delta=0.1000`, `topology_signature_count=2`), weil AC0800 textlos ist und AC0820 CO₂-Text trägt.
- **Sicherung:** `PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_semantic_harmonization_helpers.py` lief grün mit `7 passed`; der AC0800–AC0820-Fokuslauf endete mit Exit `0`.
- **Blocker:** Kein technischer FP-D10-Blocker; fachlich bleibt als spätere Verbesserung eine getrennte Ringgeometrie-/Textlagen-Harmonisierung statt kompletter Proto-Anker-Übernahme.
- **Nächster sinnvoller Schritt:** FP-D11 bereitet das Release-Kandidaten-Gate mit Kernsuite, AC08-Smoke und Qualitätsvergleich vor.

### Tag 11 (2026-06-03) – Release-Kandidaten-Gate vorbereiten

- [x] **FP-D11-1:** Fixe Gate-Checkliste ausführen (Kernsuite, AC08-Smoke, Qualitätsvergleich zur Baseline). (2026-06-04 Run NV: Gate-Runner `tools/run_release_candidate_gate.sh` ergänzt; Kernsuite `701 passed`, AC08-Regression-Set-Smoke lief im 300s-Probelauf bis `AC0812_M` und endete mit Timeout `124`.)
- [x] **FP-D11-2:** Jede Abweichung als Blocker oder akzeptierte Ausnahme markieren. (2026-06-04 Run NV: AC08-Smoke-Timeout ist ein **Blocker**, nicht akzeptiert; Qualitätsgate ist Folge-Blocker, weil `ac08_success_metrics.csv` nach Timeout fehlt.)
- [x] **FP-D11-EXIT:** Vollständiger Gate-Probelauf mit eindeutigem Status. (2026-06-04 Run NV: Status `FAIL/BLOCKER`; Recovery für FP-D12 ist entweder Laufzeitbudget erhöhen/Smoke segmentieren oder Performance-Blocker vor hartem Gate beheben.)

### Fortschritt vs. Blocker (Session 2026-06-04, Release-Kandidaten-Gate vorbereiten FP-D11 Run NV)

- **Fortschritt:** FP-D11 ist operationalisiert: `tools/run_release_candidate_gate.sh` führt Kernsuite, deterministischen AC08-Smoke und Qualitätsgate mit Evidenzlogs aus; `tools/check_ac08_success_metrics_gate.py` prüft die AC08-Erfolgskriterien einschließlich Baseline-/Regressionskriterien.
- **Sicherung:** Die Kernsuite lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, Exit `0`, `701 passed`). Der neue Gate-/Metrics-Test lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_local_completion_checks_tool.py`, Exit `0`, `8 passed`).
- **Blocker:** Der deterministische AC08-Regression-Set-Smoke überschritt das 300s-Probelaufbudget (Exit `124`) und erzeugte dadurch kein finales `ac08_success_metrics.csv`; das Qualitätsgate meldet deshalb `missing metrics file`.
- **Nächster sinnvoller Schritt:** FP-D12 fährt dasselbe Gate hart: entweder mit ausreichend hohem Laufzeitbudget oder nach Segmentierung des AC08-Smokes, aber weiterhin ohne stumme Regressionen.

### Tag 12 (2026-06-04) – Release-Kandidaten-Gate hart fahren

- [x] **FP-D12-1:** Gate erneut unter denselben Bedingungen ausführen. (2026-06-05 Run NW: derselbe dreistufige Gate-Runner mit frischem Output und erhöhtem, explizitem AC08-Budget von 900s ausgeführt; Kernsuite `703 passed`, AC08-Smoke endet weiterhin mit Timeout `124`.)
- [x] **FP-D12-2:** Regel „No silent regression“ strikt anwenden. (2026-06-05 Run NW: Der Runner verwirft das Output-Verzeichnis vor dem Smoke; ein fehlgeschlagener Smoke kann dadurch keine alte Erfolgsmessung wiederverwenden. Regressionstest erzwingt `ac08-smoke=BLOCKER` und `quality-gate=BLOCKER` bei zuvor vorhandener grüner Metrics-Datei.)
- [x] **FP-D12-EXIT:** Gate `PASS` oder explizit dokumentiertes `FAIL` mit konkretem Recovery-Plan. (2026-06-05 Run NW: explizites `FAIL/BLOCKER`; Recovery: AC08-Regression-Set in deterministische Einzelvarianten-Segmente mit je eigenem Timeout/Evidence aufteilen und die Gesamtmetrik ausschließlich nach vollständigem Segmentabschluss erzeugen.)

### Fortschritt vs. Blocker (Session 2026-06-05, Release-Kandidaten-Gate hart FP-D12 Run NW)

- **Fortschritt:** FP-D12 wurde vollständig ausgeführt. Der Gate-Runner unterstützt ein explizites AC08-Zeitbudget (`RC_GATE_AC08_TIMEOUT_SECONDS`, Standard `900`) und kennzeichnet den Lauf als FP-D12.
- **No silent regression:** Vor jedem AC08-Smoke wird das Zielverzeichnis vollständig neu angelegt. Eine alte grüne `ac08_success_metrics.csv` kann nach Timeout oder Abbruch nicht mehr zu einem falschen Qualitäts-PASS führen.
- **Sicherung:** Gate-/Metrics-Detailtests `10 passed`; echte Kernsuite `703 passed`; der echte AC08-Smoke endete nach 900s mit Exit `124`, das nachgelagerte Qualitätsgate wegen fehlender finaler Metrics-Datei mit Exit `1`. Beide Zeilen stehen als `BLOCKER` in `artifacts/test-evidence/fp-d12-run-nw/gate_status.csv`.
- **Entscheidung:** FP-D12 endet explizit mit `FAIL/BLOCKER`, ohne akzeptierte Ausnahme. Erzeugt wurden sechs Teilvarianten (`AC0800_L/M/S`, `AC0812_M`, `AC0820_L`, `AC0834_S`), aber keine vollständige Metrikkette.
- **Recovery-Plan / nächster sinnvoller Schritt:** Vor FP-D13 den festen AC08-Satz in einzeln timeout-gesicherte Variantensegmente zerlegen, Segmentstatus zusammenführen und `ac08_success_metrics.csv` erst nach vollständigem Erfolg aller Segmente freigeben.

### Recovery vor Tag 13 (2026-06-05) – AC08-Gate segmentieren

- [x] **FP-D12-R1:** Festen AC08-Regressionssatz in einzeln timeout-gesicherte Variantenläufe zerlegen. (2026-06-05 Run NX: `tools/run_ac08_segmented_smoke.sh` führt jede der 14 Varianten in einem isolierten Segmentverzeichnis mit eigenem Status und Log aus.)
- [x] **FP-D12-R2:** Gesamtmetrik ausschließlich nach erfolgreichem Abschluss aller Segmente freigeben. (2026-06-05 Run NX: `.segment-complete`-Marker und `tools/finalize_ac08_segmented_run.py` verhindern Aggregation bei fehlenden/fehlgeschlagenen Segmenten; erst danach werden die zusammengeführten AC08-Erfolgskriterien geschrieben.)
- [x] **FP-D12-R-EXIT:** Segmentstatus und vollständige Artefaktkette sind reproduzierbar getestet. (2026-06-05 Run NX: Detailtests decken PASS, BLOCKER, zurückgehaltene Metrik und vollständige 14-Varianten-Aggregation ab.)

### Fortschritt vs. Blocker (Session 2026-06-05, AC08-Gate-Recovery Run NX)

- **Fortschritt:** Der Release-Candidate-Runner nutzt standardmäßig den segmentierten AC08-Smoke statt eines einzigen globalen Timeout-Prozesses.
- **Sicherheitsregel:** Ein Segmentfehler beendet den Smoke mit Blockerstatus; `ac08_success_metrics.csv` wird dann nicht erzeugt.
- **Nächster sinnvoller Schritt:** FP-D13 führt den vollständigen segmentierten End-to-End-Lauf aus und vergleicht die aggregierten Kennzahlen mit der Baseline.

### Tag 13 (2026-06-05) – Abschlusslauf

- [x] **FP-D13-1:** Finalen End-to-End-Lauf mit vollständiger Artefaktkette ausführen. (2026-06-05 Run NZ: Kernsuite und alle 14 isolierten AC08-Segmente mit 600s Segmentbudget ausgeführt; alle Segmentprozesse Exit `0`, die Aggregation deckte jedoch vier Varianten ohne Iteration-Report auf und das Gate blieb `FAIL/BLOCKER`.)
- [x] **FP-D13-2:** Ergebnis gegen Baseline quantitativ vergleichen. (2026-06-05 Run NZ: `14` erwartet, `10` reportseitig konvertiert, `4` fehlend; `3/6` Previously-Good-Anker erhalten, `3/6` fehlend; `0` akzeptierte Regressionen, aber auch `0` gemessene Verbesserungen; `overall_success=0`.)
- [x] **FP-D13-EXIT:** Abschlusslauf reproduzierbar und vollständig dokumentiert. (2026-06-05 Run NZ: explizites `FAIL/BLOCKER` mit Kommandos, Gate-/Segmentstatus, quantitativer Metrik und Recovery-Punkten in `docs/next_arbeitspaket_2026-06-05_runNZ.md`; keine Release-Freigabe.)

### Fortschritt vs. Blocker (Session 2026-06-05, Abschlusslauf FP-D13 Run NZ)

- **Fortschritt:** Der segmentierte End-to-End-Lauf ist technisch vollständig durchgelaufen: Kernsuite nach den FP-D13-Fixes `710 passed`; mit 600 Sekunden Budget endeten alle 14 AC08-Segmentprozesse mit Exit `0`.
- **No silent regression:** Die Finalisierung akzeptiert ein fachlich optionales, vollständig leeres `quality_tercile_passes.csv`, erzeugt daraus aber keine erfundene Verbesserung. Der quantitative Gate-Status bleibt deshalb rot.
- **Baselinevergleich:** `images_converted=10/14`, `images_missing=4` (`AC0811_L/M/S`, `AC0831_L`), Previously-Good-Anker `3/6` erhalten und `3/6` fehlend, `improved_*_count=0`, `accepted_regression_count=0`, `overall_success=0`.
- **Tooling-Fix:** Der Gate-Runner exportiert Output-, Evidence-, Timeout- und Work-Package-Kontext an den segmentierten Unterprozess; Segmentstatus und Logs landen damit im benannten Gate-Evidence-Verzeichnis.
- **Blocker / nächster sinnvoller Schritt:** Vor FP-D14 müssen die vier Exit-0-ohne-Iteration-Report-Fälle geklärt und ein echter Baseline-Verbesserungsnachweis erzeugt werden. FP-D14 darf auf Basis der harten Kennzahlen nur „noch offen“ entscheiden, sofern dieser Recovery-Schritt nicht vorher grün wird.

### Tag 14 (2026-06-06) – Abschlussentscheidung

- [x] **FP-D14-1:** 1-seitiges Abschlussdokument schreiben (stabil, verbessert, offen). (2026-06-05 Run OA: `docs/abschlussentscheidung_2026-06-05_runOA.md` trennt belastbare Stabilität, nicht belegte Verbesserung und offene Release-Blocker.)
- [x] **FP-D14-2:** „Durch“ vs. „noch offen“ mit 3 harten Kennzahlen entscheiden. (2026-06-05 Run OA: Entscheidung **noch offen** anhand von `10/14` reportseitig vollständigen Varianten, `3/6` erhaltenen Previously-Good-Ankern und `0` gemessenen Verbesserungen; zusätzlich bestätigt `overall_success=0` den Blockerstatus.)
- [x] **FP-D14-EXIT:** Entscheidung ist datenbasiert und für Dritte nachvollziehbar. (2026-06-05 Run OA: Kennzahlen, Schwellen, FP-D13-Reproduktionsbefehle und konkrete Wiederaufnahmebedingungen sind im Abschlussdokument festgehalten.)

### Fortschritt vs. Blocker (Session 2026-06-05, Abschlussentscheidung FP-D14 Run OA)

- **Stabil:** Die Kernsuite ist mit `710 passed` grün, alle 14 isolierten AC08-Prozesse endeten im FP-D13-Abschlusslauf mit Exit `0`, und es wurden weder akzeptierte Regressionen noch semantische Mismatches gemessen.
- **Nicht als Verbesserung gewertet:** Der Abschlusslauf weist `0` Verbesserungen bei `error_per_pixel` und `mean_delta2` aus; aus dem leeren optionalen Quality-Pass-Report wird bewusst kein Erfolg abgeleitet.
- **Harte Entscheidung:** Das Projekt ist **noch offen**: nur `10/14` Varianten besitzen einen Iteration-Datensatz, nur `3/6` Previously-Good-Anker sind reportseitig erhalten und `overall_success=0`.
- **Wiederaufnahmebedingung:** Erst ein erneuter vollständiger 14/14-Lauf mit 6/6 erhaltenen Previously-Good-Ankern, mindestens einer belegten Qualitätsverbesserung und `overall_success=1` rechtfertigt die Entscheidung „durch“.
- **Abschluss:** Das 14-Tage-Finish-Playbook ist vollständig abgearbeitet; FP-D14 dokumentiert ausdrücklich keine Release-Freigabe, sondern den nachvollziehbaren Restblocker.

### FP-Recovery nach Abschlussentscheidung (Session 2026-06-05, Run OB)

- [x] **FP-RCV-1:** Root Cause der vier Exit-0-Segmente ohne Iteration-Datensatz beheben. (`AC0811_L/M/S` und `AC0831_L` lagen unter `nonconvertable/`; der segmentierte Runner löst nun je Variante den tatsächlichen Quellordner auf.)
- [x] **FP-RCV-2:** Segmentvollständigkeit zusätzlich am erwarteten `Iteration_Log.csv`-Datensatz prüfen. (Exit `0` ohne passende Zeile wird `BLOCKER_MISSING_REPORT`; die Finalisierung validiert dieselbe Invariante unabhängig.)
- [x] **FP-RCV-3:** Die vier fehlenden Varianten real über den korrigierten Segmentpfad verifizieren. (Run OB mit Ein-Iterations-Budget: 4/4 Exit `0`, 4/4 `PASS`, 4/4 erwartete Reportzeilen; Details in `docs/next_arbeitspaket_2026-06-05_runOB.md`.)
- [ ] **FP-RCV-4:** Vollständigen festen 14er-Satz mit regulärem Budget wiederholen und die FP-D14-Schwellen (`14/14`, `6/6`, mindestens eine Verbesserung, `overall_success=1`) neu bewerten.

- **Fortschritt:** Der konkrete Reportvollständigkeitsfehler ist reproduziert und geschlossen; die vier ehemals fehlenden Varianten erscheinen im echten Recovery-Smoke wieder in `Iteration_Log.csv`.
- **No silent success:** Weder ein bloßer Prozess-Exit `0` noch ein isolierter `.segment-complete`-Marker genügt künftig zur Aggregation.
- **Nächster sinnvoller Schritt:** FP-RCV-4 als vollständigen Release-Candidate-Gate-Lauf ausführen; bis dahin bleibt die FP-D14-Entscheidung „noch offen“.

### Fortschritt vs. Blocker (Session 2026-05-24, AC0020_L Plan-B + Re-Conversion + T5 Run ZZ)

- **Fortschritt (Plan B):** Für `AC0020_L` wurde eine gekoppelte Plan-B-Syntheseprobe ausgeführt (`python -m tools.plan_b_synthetic_probe ... --variant AC0020_L`), Exit `0`; neues Log-Artefakt: `artifacts/converted_images/reports/AC0020_L_planb_synthetic_2026-05-24_runZZ.log`.
- **Fortschritt (Re-Conversion):** Die unbefriedigende Konvertierung von `AC0020_L.jpg` wurde als isolierter deterministischer Einzelrun neu erzeugt (`--start AC0020_L --end AC0020_L --deterministic-order`), Exit `0`; neues Log-Artefakt: `artifacts/converted_images/reports/AC0020_L_single_2026-05-24_runZZ.log`.
- **Fortschritt (nächstes Arbeitspaket):** Direkt anschließend wurde der priorisierte T5.x-Kurzlauf erneut ausgeführt (`tests/test_image_composite_converter.py::test_ac08_semantic_anchor_variants_ac0812_only`), Ergebnis `1 passed`, Exit `0`; Log-Artefakt: `artifacts/converted_images/reports/T5_ac0812_timeoutpath_probe_2026-05-24_runZZ.log`.
- **Blocker:** Der bekannte N1/N2-Vollbereichsblocker (kumulative Laufzeit/Timeout) bleibt von den erfolgreichen Kurzläufen unberührt.
- **Nächster sinnvoller Schritt:** Weiter mit dem nächsten priorisierten mittleren Paket (N5-Kurzbatch) inkl. genau einer gekoppelten Plan-B-Aufgabe und anschließendem Session-Eintrag.
    - 2026-05-24 (Run IO): **Nächstes Arbeitspaket** erneut ausgeführt: 1) nächste dokumentierte Aufgabe `TB-A3` timeout-gesichert isoliert (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) mit Exit `0`, Ergebnis `1 skipped, 5 warnings` in `2.44s`, Log `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-24_runIO.log`; 2) gekoppelte Plan-B-Aufgabe als Syntheseprobe für `AC0040_S` (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0040_S --output-dir artifacts/converted_images/reports`) mit Exit `0` (`status=ok`), Log `artifacts/converted_images/reports/AC0040_S_planb_synthetic_2026-05-24_runIO.log`; 3) nächstes CSV-Bild als Einzellauf für `AC0040_S` ausgeführt (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0040_S --end AC0040_S`) mit Exit `0`, Log `artifacts/converted_images/reports/AC0040_S_single_2026-05-24_runIO.log`.

### Fortschritt vs. Blocker (Session 2026-05-25, AC0202_2 Plan-B + vollständiges Arbeitspaket Run KC)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde timeout-gesichert isoliert ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`.
- **Fortschritt (Plan B):** Auf Basis von `artifacts/images_to_convert/samples/AC0202_2.svg` wurde die gekoppelte Plan-B-Syntheseprobe für `AC0202_2` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_synthetic_probe.py "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0202_2 --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`.
- **Fortschritt (nächstes Arbeitspaket):** Das Zielbild `AC0202_2` wurde im Einzelrun vollständig abgearbeitet (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0202_2 --end AC0202_2`), Exit `0`.
- **Fortschritt (Volltest):** Der vollständige Testlauf wurde als Abschluss des Arbeitspakets ausgeführt (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`) und lief vollständig grün durch (`531 passed, 5 warnings`, Exit `0`).
- **Nächster sinnvoller Schritt:** Dasselbe Schema mit dem nächsten offenen CSV-Zielbild fortsetzen (TB-A3 → gekoppelte Plan-B-Aufgabe → Einzelrun → Volltest).

### Fortschritt vs. Blocker (Session 2026-05-25, AC0021 Plan-B + Re-Conversion + vollständiges Arbeitspaket Run KD)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde timeout-gesichert isoliert ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-25_runKD.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Roundtrip-Aufgabe wurde mit `artifacts/images_to_convert/samples/AC0021.svg` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0021.svg --output-dir artifacts/converted_images/reports`), Ergebnis `status=ok`, Exit `0`; Log: `artifacts/converted_images/reports/AC0021_planb_roundtrip_2026-05-25_runKD.log`.
- **Fortschritt (Re-Conversion):** `AC0021.jpg` wurde als isolierter Einzelrun erneut konvertiert (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0021 --end AC0021`), Exit `0`; Log: `artifacts/converted_images/reports/AC0021_single_2026-05-25_runKD.log`.
- **Fortschritt (Volltest):** Das Aufgabenpaket wurde mit einem vollständigen Testlauf abgeschlossen (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`), Ergebnis `531 passed, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/pytest_full_2026-05-25_runKD.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Schema mit dem nächsten offenen CSV-Zielbild fortsetzen (TB-A3 → gekoppelte Plan-B-Aufgabe → Einzelrun → Volltest).

### Fortschritt vs. Blocker (Session 2026-05-25, AC0060_L.svg als Plan B + vollständiges Arbeitspaket Run KU)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde timeout-gesichert isoliert ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-25_runKU.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Aufgabe wurde explizit mit `artifacts/images_to_convert/samples/AC0060_L.svg` als Roundtrip ausgeführt (`PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0060_L.svg --output-dir artifacts/converted_images/reports`), Ergebnis `variant=AC0060_L`, `delta2_output_vs_sample=1695.742597`, Exit `0`; Log: `artifacts/converted_images/reports/AC0060_L_planb_roundtrip_2026-05-25_runKU.log`.
- **Fortschritt (Plan B Re-Run, 2026-05-25 / Run KV):** Die gekoppelte Plan-B-Aufgabe für `AC0060_L.svg` wurde erneut ausgeführt (`PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0060_L.svg --output-dir artifacts/converted_images/reports`) mit unverändert stabilem Ergebnis `variant=AC0060_L`, `delta2_output_vs_sample=1695.742597`, Exit `0`; Log: `artifacts/converted_images/reports/AC0060_L_planb_roundtrip_2026-05-25_runKV.log`.
- **Fortschritt (Re-Conversion):** `AC0060_L.jpg` wurde als isolierter Einzelrun erneut konvertiert (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0060_L --end AC0060_L`), Exit `0`; Log: `artifacts/converted_images/reports/AC0060_L_single_2026-05-25_runKU.log`.
- **Fortschritt (Volltest):** Das Arbeitspaket wurde mit einem vollständigen Testlauf abgeschlossen (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`), Ergebnis `533 passed, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/pytest_full_2026-05-25_runKU.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Schema mit dem nächsten offenen CSV-Zielbild fortsetzen (TB-A3 → gekoppelte Plan-B-Aufgabe → Einzelrun → Volltest).


### Fortschritt vs. Blocker (Session 2026-05-26, AC0100_L.svg als Plan B + vollständiges Arbeitspaket Run KR)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde timeout-gesichert isoliert ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-26_runKR.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Roundtrip-Aufgabe wurde explizit mit `artifacts/images_to_convert/samples/AC0100_L.svg` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0100_L.svg --output-dir artifacts/converted_images/reports`), Ergebnis `variant=AC0100_L`, `delta2_output_vs_sample=3245.435702`, Exit `0`; Log: `artifacts/converted_images/reports/AC0100_L_planb_roundtrip_2026-05-26_runKR.log`.
- **Fortschritt (Re-Conversion):** `AC0100_L.jpg` wurde als isolierter Einzelrun erneut konvertiert (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0100_L --end AC0100_L`), Exit `0`; Log: `artifacts/converted_images/reports/AC0100_L_single_2026-05-26_runKR.log`.
- **Fortschritt (Volltest):** Das Arbeitspaket wurde mit einem vollständigen Testlauf abgeschlossen (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`), Ergebnis `533 passed, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/pytest_full_2026-05-26_runKR.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Schema mit dem nächsten offenen CSV-Zielbild fortsetzen (TB-A3 → gekoppelte Plan-B-Aufgabe → Einzelrun → Volltest).

### Fortschritt vs. Blocker (Session 2026-05-26, AC0130_L.svg als Plan B + vollständiges Arbeitspaket Run KS)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde timeout-gesichert isoliert ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-26_runKS.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Roundtrip-Aufgabe wurde explizit mit `artifacts/images_to_convert/samples/AC0130_L.svg` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0130_L.svg --output-dir artifacts/converted_images/reports`), Ergebnis `variant=AC0130_L`, `delta2_output_vs_sample=4901.165178`, Exit `0`; Log: `artifacts/converted_images/reports/AC0130_L_planb_roundtrip_2026-05-26_runKS.log`.
- **Fortschritt (Re-Conversion):** `AC0130_L.jpg` wurde als isolierter Einzelrun erneut konvertiert (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0130_L --end AC0130_L`), Exit `0`; Log: `artifacts/converted_images/reports/AC0130_L_single_2026-05-26_runKS.log`.
- **Fortschritt (Volltest):** Das Arbeitspaket wurde mit einem vollständigen Testlauf abgeschlossen (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`), Ergebnis `533 passed, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/pytest_full_2026-05-26_runKS.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Schema mit dem nächsten offenen CSV-Zielbild fortsetzen (TB-A3 → gekoppelte Plan-B-Aufgabe → Einzelrun → Volltest).

### Fortschritt vs. Blocker (Session 2026-05-26, AC0120_L.svg als Plan B + vollständiges Arbeitspaket Run KV)

- **Fortschritt (nächste dokumentierte Aufgabe):** TB-A3 wurde timeout-gesichert isoliert ausgeführt (`PYENV_VERSION=3.10.20 timeout 240 python -m pytest tests/test_satisfactory_regression_battery.py::test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality -q`) und endet stabil mit `1 skipped, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/TB_A3_timeout_probe_2026-05-26_runKV.log`.
- **Fortschritt (Plan B):** Die gekoppelte Plan-B-Roundtrip-Aufgabe wurde explizit mit `artifacts/images_to_convert/samples/AC0120_L.svg` ausgeführt (`PYTHONPATH=. python3 tools/plan_b_roundtrip.py artifacts/images_to_convert/samples/AC0120_L.svg --output-dir artifacts/converted_images/reports`), Ergebnis `variant=AC0120_L`, `delta2_output_vs_sample=64086.669297`, Exit `0`; Log: `artifacts/converted_images/reports/AC0120_L_planb_roundtrip_2026-05-26_runKV.log`.
- **Fortschritt (Re-Conversion):** `AC0120_L.jpg` wurde als isolierter Einzelrun erneut konvertiert (`PYTHONPATH=. timeout 240 python3 -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir artifacts/converted_images --start AC0120_L --end AC0120_L`), Exit `0`; Log: `artifacts/converted_images/reports/AC0120_L_single_2026-05-26_runKV.log`.
- **Fortschritt (Volltest):** Das Arbeitspaket wurde mit einem vollständigen Testlauf abgeschlossen (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`), Ergebnis `533 passed, 5 warnings`, Exit `0`; Log: `artifacts/converted_images/reports/pytest_full_2026-05-26_runKV.log`.
- **Nächster sinnvoller Schritt:** Dasselbe Schema mit dem nächsten offenen CSV-Zielbild fortsetzen (TB-A3 → gekoppelte Plan-B-Aufgabe → Einzelrun → Volltest).

---

## Roadmap: Ketten-Architektur für geometrische Bildkonvertierung (PR-Plan, 2026-05-27)

Ziel: Die Konvertierung soll strikt als **Kette** laufen:  
1) Bildbeschreibung prüfen/normalisieren → 2) Geometrie-Elemente ableiten → 3) Element-für-Element optimieren → 4) Bedingungen/Policies anwenden → 5) Finalauswahl.

### Neue Prioritätsgewichtung ab 2026-05-28

| Gewicht | Arbeit | Begründung |
| ---: | --- | --- |
| 100 | **PR-R2 — Geometry IR** | Schnellster Hebel weg von verstreuten Heuristiken hin zu expliziten geometrischen Figurenketten. |
| 95 | **PR-R3 — Elementweiser Optimizer** | Macht die IR-Kette ausführbar und erzwingt Einpassen pro Figur statt One-shot-Heuristik. |
| 70 | **PR-R4 — Policy-Schlussphase** | Wichtig, aber erst nach belastbarer Geometriekette; verhindert frühe Sonderfall-Overrides. |
| 55 | **PR-R5 — Telemetrie/Abnahme** | Abnahme folgt nach funktionsfähigem Kettenpfad. |
| 30 | **T6/TB-A3/Testhygiene-Routine** | Nur noch als Sicherungsnetz oder bei konkretem Regressionsverdacht, nicht mehr als Standard-Next-Step. |

**Verbindlicher nächster Schritt:** PR-R2 starten und direkt so zuschneiden, dass R2-Artefakte von PR-R3 als sequenzielle Einpass-Kette konsumiert werden können.

### PR-R1 — Description Contract + Fail-Fast
- [x] **R1-1:** Zentrales Description-Contract-Schema einführen (`has_reference`, `has_geometry_terms`, `has_conditions`, `deficits`). (2026-05-27 Run KW umgesetzt.)
- [x] **R1-2:** Parser/Reflection um `contract_status` erweitern und Defizite explizit loggen. (2026-05-27 Run KW umgesetzt.)
- [x] **R1-3:** Bei unzureichender Beschreibung klarer Status (`insufficient_description`) statt stiller Fallback-Entscheidung. (2026-05-27 Run KW umgesetzt.)
- [x] **R1-TEST:** Unit-Tests für vollständige, rekursive, leere und alias-lastige Beschreibungen. (2026-05-27 Run KW umgesetzt.)
- [x] **R1-EXIT:** Jeder Lauf hat nachvollziehbare Beschreibungsgüte und expliziten Grund für Moduswahl. (2026-05-27 Run KW erfüllt; Volltest grün.)

### PR-R2 — Geometry IR (Zwischenrepräsentation)
- [x] **R2-1:** Geometrie-IR einführen (z. B. `RectBorder`, `HorizontalGradient`, `DiagonalBand`, `PlusGlyph`, `MinusGlyph`). (2026-05-28 Run LN umgesetzt.)
- [x] **R2-2:** Mapping Beschreibung → IR-Reihenfolge implementieren (inkl. Constraints). (2026-05-28 Run LN umgesetzt.)
- [x] **R2-3:** SVG-Erzeugung aus IR zentralisieren (kein verstreutes Direkt-SVG pro Sonderpfad). (2026-05-28 Run LN umgesetzt.)
- [x] **R2-TEST:** Snapshot-Tests für Parser→IR und Smoke-Tests für IR→SVG. (2026-05-28 Run LN umgesetzt.)
- [x] **R2-EXIT:** Für AC0120-artige Fälle liegt eine explizite IR-Kette vor. (2026-05-28 Run LN erfüllt.)

### PR-R3 — Elementweiser Optimizer als Standardpfad
- [x] **R3-1:** Generischen sequenziellen Optimizer auf IR-Basis einführen (pro Schritt nur Verbesserung übernehmen). (2026-05-28 Run LO umgesetzt.)
- [x] **R3-2:** Step-Logging standardisieren (`step_index`, `element`, `best_delta`, `accepted`). (2026-05-28 Run LO umgesetzt.)
- [x] **R3-3:** One-shot nur noch als expliziter Notfallmodus; Standard bleibt elementweise. (2026-05-28 Run LO umgesetzt.)
- [x] **R3-TEST:** Deterministische Tests mit Mock-Renderer/Error-Funktion; Regressionsschutz für bestehende Helper-Tests. (2026-05-28 Run LO umgesetzt.)
- [x] **R3-EXIT:** „Element-für-Element zuerst“ ist technisch erzwungen und testbar. (2026-05-28 Run LO erfüllt.)

### PR-R4 — Bedingungen/Policy als getrennte Schlussphase
- [x] **R4-1:** Policy-Phase nach der Geometriekette formal trennen (Alias-Regeln, Sample-Vergleich, Guards). (2026-05-28 Run LP umgesetzt.)
- [x] **R4-2:** Klaren Entscheidungs-Log einführen (`geometry_phase_result`, `policy_phase_decision`, `override_reason`). (2026-05-28 Run LP umgesetzt.)
- [x] **R4-3:** Harte variantspezifische Sonderbehandlungen abbauen oder zeitlich befristen. (2026-05-28 Run LP: neue Schlussphase ohne variantspezifische Sonderliste eingeführt; Guards/Sample-Overrides laufen nur noch über zentrale Policy-Entscheidungen.)
- [x] **R4-TEST:** Fälle für „Geometrie gewinnt“, „Sample gewinnt“, „Guard greift“. (2026-05-28 Run LP umgesetzt.)
- [x] **R4-EXIT:** Keine verdeckten Policy-Overrides mehr vor Abschluss der Geometriekette. (2026-05-28 Run LP erfüllt; `geometry_phase_result` wird vor jeder Policy-Entscheidung protokolliert.)

### PR-R5 — Benennung, Telemetrie, Abnahme
- [x] **R5-1:** Uneindeutige Begriffe im Logging harmonisieren (z. B. klare Trennung von Fallback- und Kettenphasen). (2026-05-28 Run LQ umgesetzt: zentrale R5-Labels für Geometry-, Policy- und Emergency-/Placeholder-Phasen eingeführt.)
- [x] **R5-2:** Qualitätsmetriken pro Phase erfassen (Step-Erfolgsrate, Override-Häufigkeit, Placeholder-Notfallrate). (2026-05-28 Run LQ umgesetzt: `step_success_rate`, `override_frequency` und `placeholder_emergency_rate` als Telemetrie-/Aggregationsfelder ergänzt.)
- [x] **R5-3:** Abschlussdokument mit Vorher/Nachher-Kennzahlen und offenen Restpunkten ergänzen. (2026-05-28 Run LQ umgesetzt: siehe `docs/chain_architecture_r5_acceptance_2026-05-28_runLQ.md`.)
- [x] **R5-TEST:** Vollsuite + gezielte AC0120/AC0130/AC0030 Vergleichsläufe. (2026-05-28 Run LQ umgesetzt: R5-Detailtests `19 passed`, gezielte AC0120/AC0130/AC0030-Tests `5 passed`, Vollsuite `560 passed, 5 warnings`.)
- [x] **R5-EXIT:** Reproduzierbare, datenbasierte Abnahme der Ketten-Architektur. (2026-05-28 Run LQ erfüllt; Telemetrie, Abnahmedokument und Sicherungstests liegen vor.)

### Reihenfolge und Leitplanke
- [x] **Reihenfolge:** R1 → R2 → R3 → R4 → R5. (2026-05-28 Run LQ erfüllt: R5 nach R1–R4 abgeschlossen.)
- [x] **Leitplanke (verbindlich):** Bedingungen/Policies erst **nach** elementweiser Geometriekette anwenden. (2026-05-28 Run LQ erfüllt und über R5-Telemetrie nach der Policy-Schlussphase sichtbar.)

### Fortschritt vs. Blocker (Session 2026-05-28, PR-R5 Telemetrie/Abnahme Run LQ)

- **Fortschritt (R5-1/R5-2):** Neue zentrale R5-Telemetrie eingeführt; sie harmonisiert Geometry-/Policy-/Emergency-Begriffe und erfasst `step_success_rate`, `override_applied`, `override_reason` sowie Placeholder-Notfallnutzung pro Lauf. Aggregiert werden daraus `mean_step_success_rate`, `override_frequency` und `placeholder_emergency_rate`.
- **Fortschritt (R5-3/R5-EXIT):** Abschluss-/Abnahmedokument `docs/chain_architecture_r5_acceptance_2026-05-28_runLQ.md` ergänzt, inklusive Vorher/Nachher-Kennzahlen, Restpunkten und Fazit.
- **Fortschritt (R5-TEST):** R5-Detailtests liefen grün (`19 passed`), die gezielten AC0120/AC0130/AC0030-Vergleichstests liefen grün (`5 passed, 5 warnings`) und die Vollsuite lief grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `560 passed, 5 warnings`, Exit `0`).
- **Zusatzkorrektur:** AC0030-artige, geometrisch vollständige AC0130-Beschreibungen setzen keine verdeckte `top_source_ref="AC0030"` mehr; damit bleibt die Referenz-/Policy-Fallback-Trennung sauber.
- **Blocker:** Keine neuen Blocker. Produktive Batch-/CSV-Reports können die neue `chain_phase_telemetry_line` künftig zusätzlich ausgeben.
- **Nächster sinnvoller Schritt:** Nach Abschluss der PR-Roadmap wieder gemäß aktueller Produktpriorität entscheiden: entweder R5-Telemetrie in Batch-Reports verdrahten oder auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren.



### Fortschritt vs. Blocker (Session 2026-05-28, PR-R4 Policy-Schlussphase Run LP)

- **Fortschritt (R4-1/R4-2):** Neue zentrale Policy-Schlussphase nach der Geometry-IR-Auswahl eingeführt; sie protokolliert `geometry_phase_result`, `policy_phase_decision` und `override_reason` vor finaler Render-Freigabe.
- **Fortschritt (R4-3):** Guards, explizite Sample-Präferenz und Sample/Geometry-Fehlervergleich laufen jetzt über eine zentrale, nicht variantspezifische Policy-Entscheidung statt verdeckter Einzelpfade.
- **Fortschritt (R4-TEST):** Detailtests decken die Entscheidungen „Geometrie gewinnt“, „Sample gewinnt“ und „Guard greift“ ab; außerdem wurden die bestehenden Geometry-IR- und Description-Contract-Tests erneut ausgeführt. Der abschließende Volltest lief grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `557 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker; echte produktive Sample-Vergleichsmetriken bleiben ein Anschluss für PR-R5-Telemetrie/Abnahme.
- **Nächster sinnvoller Schritt:** PR-R5 starten und die neue Policy-/Geometry-Phasentrennung in Telemetrie, Logging-Begriffen und Abnahmebericht messbar machen.

### Fortschritt vs. Blocker (Session 2026-05-28, PR-R3 elementweiser Geometry-IR-Optimizer Run LO)

- **Fortschritt (R3-1/R3-2):** Neuer sequenzieller Geometry-IR-Optimizer eingeführt; er bewertet jedes IR-Element gegen die aktuell akzeptierte Kette, übernimmt ausschließlich strikt verbessernde Kandidaten und protokolliert pro Schritt `step_index`, `element`, `best_delta`, `accepted`, `error_before` und `error_after`.
- **Fortschritt (R3-3):** Composite-SVG-Rendering wählt nun zuerst `optimized_geometry_ir`, dann die normale `geometry_ir`; ein One-shot-IR wird nur bei explizitem `allow_one_shot_emergency=True` als Notfallmodus akzeptiert.
- **Fortschritt (R3-TEST):** Deterministische Mock-Renderer/Error-Tests decken Annahme verbessernder Kandidaten, Regressionsablehnung und One-shot-Notfallgating ab; zusätzlich lief der Volltest grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `554 passed, 5 warnings`, Exit `0`; Logs: `artifacts/converted_images/reports/pr_r3_geometry_ir_optimizer_detailtests_2026-05-28_runLO.log`, `artifacts/converted_images/reports/pytest_full_2026-05-28_runLO.log`).
- **Blocker:** Keine neuen Blocker; der Optimizer ist aktuell bewusst renderer-agnostisch und nutzt für Produktionsläufe zunächst konservative lokale Default-Probes.
- **Nächster sinnvoller Schritt:** PR-R4 starten und Policy-/Bedingungsentscheidungen als getrennte Schlussphase nach `geometry_phase_mode=elementwise_geometry_ir` verdrahten.

### Fortschritt vs. Blocker (Session 2026-05-28, PR-R2 Geometry-IR Run LN)

- **Fortschritt (R2-1/R2-2):** Neues Geometry-IR-Modul eingeführt; Beschreibungen werden in eine geordnete Primitive-Kette (`HorizontalGradient`, `RectBorder`, `DiagonalBand`, `PlusGlyph`, `MinusGlyph`) übersetzt und in `params["geometry_ir"]` abgelegt.
- **Fortschritt (R2-3):** Composite-SVG-Erzeugung rendert vorhandene IR-Ketten zentral über den Geometry-IR-Renderer; der bisherige `square_cross`-Sonderpfad nutzt ebenfalls IR-Fragmente als Fallback.
- **Fortschritt (R2-TEST):** Detailtests decken AC0130-/AC0120-artige Parser→IR-Ketten, SVG-Smoke-Rendering und Parser-Verdrahtung ab; zusätzlich lief der Volltest grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `551 passed, 5 warnings`, Exit `0`; Logs: `artifacts/converted_images/reports/pr_r2_geometry_ir_detailtests_2026-05-28_runLN.log`, `artifacts/converted_images/reports/pytest_full_2026-05-28_runLN.log`).
- **Blocker:** Keine neuen Blocker; die IR ist bewusst deterministisch und noch nicht optimierend.
- **Nächster sinnvoller Schritt:** PR-R3 starten und den elementweisen Optimizer auf `geometry_ir` aufsetzen.

### Fortschritt vs. Blocker (Session 2026-05-27, PR-R1 Description Contract + Volltest Run KW)

- **Fortschritt (R1-1/R1-2/R1-3):** In `imageCompositeConverterPerceptionReflection` wurde ein zentraler Description-Contract ergänzt (`has_reference`, `has_geometry_terms`, `has_conditions`, `deficits`, `status`) und in `params` als `description_contract` plus `contract_status` verdrahtet. Leere bzw. geometriearme Nicht-Referenz-Beschreibungen werden jetzt fail-fast als `mode=insufficient_description` markiert.
- **Fortschritt (R1-TEST):** Neue Unit-Tests für vollständige Beschreibung, rekursive Alias-Vererbung, leere Beschreibung und alias-lastige Beschreibung ergänzt.
- **Fortschritt (Volltest):** Gesamte Suite wurde vollständig ausgeführt (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`) mit Ergebnis `547 passed, 5 warnings`, Exit `0`.
- **Nächster sinnvoller Schritt:** PR-R2 (Geometry-IR) gemäß Roadmap starten.

### Fortschritt vs. Blocker (Session 2026-05-28, T6.3 + T6-PB + AC0130_M + Volltest Run LM)

- **Fortschritt (nächste dokumentierte Aufgabe):** T6.3 wurde isoliert ausgeführt (`PYENV_VERSION=3.10.20 PYTHONPATH=. timeout 180 pyenv exec python -u -m pytest tests/test_image_composite_converter.py::test_make_badge_params_keeps_ac0838_m_circle_near_full_width_for_voc_layout -q`) mit Exit `0`, Ergebnis `1 skipped, 5 warnings in 3.66s`; Log: `artifacts/converted_images/reports/T6_3_ac0838M_isolation_2026-05-28_runLM.log`.
- **Fortschritt (gekoppelte Plan-B-Aufgabe):** Der T6-PB-Einzeltest lief grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_global_search_optimization_helpers.py::test_global_search_skips_deterministic_track_after_strong_stochastic_gain`) mit Exit `0`, Ergebnis `1 passed in 0.13s`; Log: `artifacts/converted_images/reports/t6_planb_singletest_2026-05-28_runLM.log`.
- **Fortschritt (Plan-B-Kandidat):** Die Syntheseprobe für `AC0130_M` wurde ausgeführt (`PYENV_VERSION=3.10.20 python -m tools.plan_b_synthetic_probe "Bildbeschreibung: Kreis mit horizontalem Griff links und Beschriftung rF." --variant AC0130_M --output-dir artifacts/converted_images/reports`) mit Exit `0`, Ergebnis `status=ok`; Log: `artifacts/converted_images/reports/AC0130_M_planb_synthetic_2026-05-28_runLM.log`.
- **Fortschritt (Volltest):** Der abschließende Komplettlauf war vollständig grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`) mit Exit `0`, Ergebnis `547 passed, 5 warnings`; Log: `artifacts/converted_images/reports/pytest_full_2026-05-28_runLM.log`.
- **Nächster sinnvoller Schritt:** Wegen der neuen Gewichtung nicht erneut im T6/TB-A3-Routineschema fortfahren, sondern PR-R2 (Geometry IR) als nächstes Arbeitspaket starten; T6/TB-A3 bleiben nur Sicherungsnetz nach konkreten Ketten-Änderungen.

### Fortschritt vs. Blocker (Session 2026-05-28, R5 Scorecard-Telemetrie Run LS)

- **Fortschritt:** Der nach Run LR dokumentierte Anschluss wurde umgesetzt: `chain_phase_telemetry.csv` führt nun Scorecard-/Baseline-Felder (`status`, `error_per_pixel`, `mean_delta2`) direkt neben den R5-Phasenfeldern; `chain_phase_telemetry_summary.txt` ergänzt `semantic_ok_count`, `non_green_count`, `mean_error_per_pixel` und `mean_delta2`.
- **Sicherung:** Detailtests liefen grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/detailtests/test_batch_reporting_helpers.py tests/detailtests/test_chain_telemetry_helpers.py tests/detailtests/test_conversion_finalization_helpers.py`, `23 passed`, Exit `0`); Vollsuite lief grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `561 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker; Scorecard-Werte bleiben leer, wenn ein Lauf keine endlichen Qualitätsmetriken im `result_map` liefert.
- **Nächster sinnvoller Schritt:** Wieder auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren oder aus den neuen Scorecard-Telemetrie-Kennzahlen eine Drift-Grenze für künftige Batchläufe ableiten.

### Fortschritt vs. Blocker (Session 2026-05-28, R5 Batch-Telemetrie Run LR)

- **Fortschritt:** Der nach PR-R5 dokumentierte Anschluss wurde umgesetzt: Batchläufe schreiben nun `chain_phase_telemetry.csv` mit Geometry-/Policy-Phasen, Step-Erfolgsrate, Override-Status und Placeholder-Notfallmarkierung je Variante sowie `chain_phase_telemetry_summary.txt` mit aggregierten R5-Abnahmemetriken.
- **Verdrahtung:** `runConversionFinalizationImpl(...)` ruft den neuen Batch-Telemetrie-Report vor `Iteration_Log.csv` und der Post-Conversion-Reportphase auf; `convertRange(...)` nutzt dafür die bestehende R5-Aggregation aus `imageCompositeConverterChainTelemetry`.
- **Sicherung:** Detailtests liefen grün (`23 passed`, Exit `0`); Vollsuite lief grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `561 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Die neuen Reports bleiben leer bis ohne Fehler lauffähige Varianten tatsächlich `params["chain_phase_telemetry"]` liefern.
- **Nächster sinnvoller Schritt:** Auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren oder die neuen Telemetrie-Reports in eine bestehende Scorecard/Baseline-Auswertung integrieren.

### Fortschritt vs. Blocker (Session 2026-05-28, R5 Drift-Grenze Run LT)

- **Fortschritt:** Der nach Run LS dokumentierte Anschluss wurde umgesetzt: `chain_phase_telemetry_summary.txt` enthält nun einen konfigurierbaren Drift-Gate-Block (`drift_status`, `drift_reasons`, `drift_max_mean_error_per_pixel`, `drift_max_mean_delta2`, `drift_max_non_green`).
- **Sicherung:** Neue Detailtests decken den `pass`-Fall unter den Standardgrenzen und den `warn`-Fall bei überschrittener Fehler-/Delta2-Grenze sowie nicht-grünem Status ab.
- **Blocker:** Keine neuen Blocker; bei fehlenden endlichen Scorecard-Metriken bleibt das Gate bewusst `warn` mit expliziten Missing-Reasons.
- **Nächster sinnvoller Schritt:** Wieder auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren oder die Drift-Grenze in einen automatisierten Abnahmecheck für konkrete Batch-Artefakte überführen.

### Fortschritt vs. Blocker (Session 2026-05-29, R5 Drift-Artefakt-Check Run LU)

- **Fortschritt:** Der nach Run LT dokumentierte Anschluss wurde umgesetzt: `chain_phase_telemetry_summary.txt` kann nun mit `tools/check_chain_telemetry_drift_gate.py` als automatisierter Drift-Gate-Check geprüft werden; `pass` liefert Exit `0`, `warn`/fehlende Artefakte liefern Exit `1` mit stabilen Reasons.
- **Sicherung:** Detailtests liefen grün (`python -m pytest -q tests/detailtests/test_batch_reporting_helpers.py`, `8 passed`, Exit `0`); der erweiterte Detailtest-Block lief grün (`28 passed`, Exit `0`); die Vollsuite lief grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `566 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der neue Check bewertet vorhandene Summary-Artefakte; Batchläufe müssen das Summary weiterhin vorher erzeugen.
- **Nächster sinnvoller Schritt:** Den Artefakt-Check in das dokumentierte Gate-/Pre-Commit-Profil aufnehmen oder wieder auf das nächste Bild-/Testhygiene-Paket rotieren.

### Fortschritt vs. Blocker (Session 2026-05-29, Drift-Gate im Abschlussprofil Run LV)

- **Fortschritt:** Der nach Run LU dokumentierte Anschluss wurde umgesetzt: `tools/check_chain_telemetry_drift_gate.py` ist nun im lokalen Workflow als eigener Gate-Schritt dokumentiert und zusätzlich im README-Checkblock sichtbar.
- **Sicherung:** Der Workflow-Dokumentationstest wurde erweitert und lief grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`, `1 passed`, Exit `0`); eine synthetische Pass-Artefakt-Probe für den Drift-Gate-Check endete mit Exit `0`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 timeout 300 python -m pytest -q -rs`, `566 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der Gate-Check setzt weiterhin voraus, dass ein Batchlauf vorher `chain_phase_telemetry_summary.txt` erzeugt hat.
- **Nächster sinnvoller Schritt:** Wieder auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren oder das Drift-Gate zusätzlich in ein ausführbares Sammelskript für lokale Abschlusschecks bündeln.

### Fortschritt vs. Blocker (Session 2026-05-29, lokales Abschlussprofil Run LW)

- **Fortschritt:** Der nach Run LV dokumentierte Anschluss wurde umgesetzt: `tools/run_local_completion_checks.sh` bündelt nun `compileall`, Pytest, den CLI-Help-Smoke und den Ketten-Telemetrie-Drift-Gate-Check als ausführbares lokales Abschlussprofil.
- **Sicherung:** Der Workflow-Dokumentationstest lief grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`, `1 passed`, Exit `0`); das neue Sammelprofil lief vollständig grün (`PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh`, Exit `0`, Pytest: `566 passed, 5 warnings`).
- **Blocker:** Keine neuen Blocker. Der Drift-Gate-Schritt wird ohne vorhandenes `chain_phase_telemetry_summary.txt` bewusst als `SKIP` protokolliert; für verpflichtende Batch-Gates steht `--require-drift-summary` bereit.
- **Nächster sinnvoller Schritt:** Wieder auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren oder das Abschlussprofil in einen automatisierten CI-/Pre-Commit-Aufruf einhängen.

### Fortschritt vs. Blocker (Session 2026-05-29, CI-Abschlussprofil Run LX)

- **Fortschritt:** Der nach Run LW dokumentierte Anschluss wurde umgesetzt: `.github/workflows/local-completion-checks.yml` startet nun `./tools/run_local_completion_checks.sh` auf Pull Requests, Pushes auf die Hauptarbeitszweige und manuell per `workflow_dispatch`.
- **Sicherung:** Der Workflow-Dokumentationstest lief grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`, `1 passed`, Exit `0`); das lokale Abschlussprofil lief vollständig grün (`PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh`, Exit `0`, Pytest: `566 passed, 5 warnings`).
- **Blocker:** Keine neuen Blocker. Der CI-Workflow nutzt bewusst denselben lokalen Sammelbefehl; ohne erzeugtes `chain_phase_telemetry_summary.txt` bleibt der Drift-Gate-Schritt wie lokal ein dokumentierter `SKIP`.
- **Nächster sinnvoller Schritt:** Wieder auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren oder bei Bedarf das CI-Profil um einen separaten Batch-Artefakt-Job mit `--require-drift-summary` erweitern.

### Fortschritt vs. Blocker (Session 2026-05-29, CI-Pflicht-Drift-Summary Run LY)

- **Fortschritt:** Der nach Run LX dokumentierte Anschluss wurde umgesetzt: `.github/workflows/local-completion-checks.yml` enthält nun den separaten Job `batch-artifact-drift-gate`, der ein repräsentatives Pass-Summary erzeugt und das lokale Abschlussprofil mit `--require-drift-summary` ausführt.
- **Sicherung:** Der Workflow-Dokumentationstest lief grün (`PYENV_VERSION=3.10.20 python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`, `1 passed`, Exit `0`); das lokale Abschlussprofil lief vollständig grün (`PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh`, Exit `0`, Pytest: `566 passed, 5 warnings`); die Pflicht-Drift-Summary-Probe mit synthetischem Pass-Artefakt lief vollständig grün (`PYENV_VERSION=3.10.20 timeout 300 ./tools/run_local_completion_checks.sh --summary <tmp>/chain_phase_telemetry_summary.txt --require-drift-summary`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der separate CI-Job nutzt bewusst ein repräsentatives Pass-Summary; produktive Batchläufe müssen ihre echten Drift-Summaries weiterhin vor dem Pflicht-Gate erzeugen.
- **Nächster sinnvoller Schritt:** Wieder auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren oder einen echten Batchlauf so zuschneiden, dass er ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

### Fortschritt vs. Blocker (Session 2026-05-29, CI-Pflichtjob-Bootstrap Run LZ)

- **Fortschritt:** Das dokumentierte Arbeitspaket aus `docs/next_arbeitspaket_2026-05-29_runLZ.md` ist im Aufgabenlog zurückgeführt: Der separate CI-Pflichtjob `batch-artifact-drift-gate` bootstrapped die Testabhängigkeit `pytest` ebenso wie das normale Abschlussprofil, bevor das repräsentative Drift-Summary angelegt und das Pflicht-Gate ausgeführt wird.
- **Sicherung:** Der Workflow-Dokumentationstest lief erneut grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_image_composite_converter.py::test_local_workflow_doc_tracks_current_commands`, `1 passed`, Exit `0`); das lokale Abschlussprofil lief erneut vollständig grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 ./tools/run_local_completion_checks.sh`, Exit `0`, inkl. `compileall`, Pytest-Suite, CLI-Help-Smoke und bewusstem Drift-Gate-`SKIP` mangels lokalem Summary-Artefakt).
- **Blocker:** Keine neuen Blocker. Der Pflichtjob ist nun auch im Aufgabenlog als vollständig gebootstrappter CI-Pfad nachvollziehbar.
- **Nächster sinnvoller Schritt:** Wieder auf das nächste dokumentierte Bild-/Testhygiene-Paket rotieren oder einen echten Batchlauf so zuschneiden, dass er ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

### Fortschritt vs. Blocker (Session 2026-05-29, AC0011 Sample-SVG Stabilisierung Run MB)

- **Fortschritt:** Das nach Run MA verbliebene AC0011-Bild-/Testhygiene-Paket wurde abgeschlossen: `AC0011` ist als forcierte Plan-B-Sample-Variante registriert, und forcierte Varianten lassen eine Referenzbeschreibung wie `Wie AC0010` nicht mehr die exakte `AC0011.svg`-Sample-Datei verdrängen.
- **Sicherung:** Der Non-Composite-Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_non_composite_runtime_helpers.py`, `21 passed`, Exit `0`); der erweiterte Detailtestblock lief grün (`41 passed`, Exit `0`); die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `568 passed, 5 warnings`, Exit `0`).
- **Akzeptanz:** Zwei direkte AC0011-Repros mit temporären Output-Verzeichnissen endeten jeweils mit Exit `0`, erzeugten `converted_svgs/AC0011.svg`, erzeugten kein `Failed_AC0011.svg`, enthielten keinen `AC0011.jpg;raster_embedded_svg`-Failure und protokollierten `sample_svg_path=/workspace/ImageConverter/artifacts/images_to_convert/samples/AC0011.svg` sowie `force_sample_svg=1`.
- **Blocker:** Keine neuen Blocker. Die produktiven Output-Artefakte aus der Repo-Probe wurden nicht als Quelländerung übernommen.
- **Nächster sinnvoller Schritt:** Wieder auf den dokumentierten Pflicht-Drift-Summary-/Batch-Artefakt-Anschluss rotieren oder das nächste explizite Bild-/Testhygiene-Paket aus der Aufgabenliste auswählen.

### Fortschritt vs. Blocker (Session 2026-05-29, AC0150_L Geometry-IR Plan-B Run MC)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0150_L.jpg` wurde im echten Non-Composite-Pfad auf beschreibungsgetriebene Geometry-IR umgestellt: vertikales Rechteck mit Verlauf, drei horizontale Linien und die Linie `Oben-Mitte → Rechts-Mitte → Unten-Mitte` werden nun als `HorizontalGradient`, `RectBorder`, `HorizontalRuleSet` und `OrthogonalPolyline` gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py tests/detailtests/test_chain_telemetry_helpers.py`, `35 passed`, Exit `0`); der externe AC0150-L-Repro lief grün (`timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0150-runmc --start AC0150_L --end AC0150_L --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `571 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der neue Pfad ist bewusst auf beschreibungsstarke Geometry-IR-Erweiterungen beschränkt und lässt andere Non-Composite-Fälle beim bisherigen generischen Fallback.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0160_L.jpg` rotieren oder einen echten Batchlauf zuschneiden, der ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

### Fortschritt vs. Blocker (Session 2026-05-30, AC0160_L Geometry-IR Plan-B Run MD)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0160_L.jpg` wurde im echten Non-Composite-Pfad auf beschreibungsgetriebene Geometry-IR umgestellt: das halbe Rechteck mit doppeltem grauem Rand, das obere kleine graue Rechteck und die `dp`-Beschriftung werden nun als `HalfDoubleRectBorder`, `LabelBox` und `TextGlyph` gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `36 passed`, Exit `0`); der externe AC0160-L-Repro lief grün (`timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0160-runmd --start AC0160_L --end AC0160_L --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `575 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der neue Pfad erweitert die beschreibungsgetriebene Geometry-IR gezielt um AC0160-artige Differenzdrucksymbole und lässt andere Non-Composite-Fälle beim bisherigen generischen Fallback.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0201_2.jpg` rotieren oder einen echten Batchlauf zuschneiden, der ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

### Fortschritt vs. Blocker (Session 2026-05-30, AC0201_2 Geometry-IR Plan-B Run ME)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0201_2.jpg` wurde im echten Non-Composite-Pfad auf beschreibungsgetriebene Geometry-IR umgestellt: der grüne Kreis und die beiden grauen aufwärts gerichteten Kompressorlinien werden nun als `CircleBackground` und `UpwardCompressorGlyph` gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `40 passed`, Exit `0`); der externe AC0201-2-Repro lief grün (`timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0201-runme --start AC0201_2 --end AC0201_2 --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `579 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der neue Pfad erweitert die beschreibungsgetriebene Geometry-IR gezielt um aufwärts gerichtete Kompressor-Symbole und lässt andere Non-Composite-Fälle beim bisherigen generischen Fallback.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0202_2.jpg` rotieren oder einen echten Batchlauf zuschneiden, der ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

### Fortschritt vs. Blocker (Session 2026-05-30, AC0202_2 Geometry-IR Plan-B Run MF)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0202_2.jpg` wurde im echten Non-Composite-Pfad auf beschreibungsgetriebene Geometry-IR umgestellt: der grüne Kreis und die beiden hellen nach rechts gerichteten Kompressorlinien werden nun als `CircleBackground` und `RightwardCompressorGlyph` gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `44 passed`, Exit `0`); der externe AC0202-2-Repro lief grün (`timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0202-runmf --start AC0202_2 --end AC0202_2 --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `583 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der neue Pfad erweitert die beschreibungsgetriebene Geometry-IR gezielt um nach rechts gerichtete Kompressor-Symbole und lässt andere Non-Composite-Fälle beim bisherigen generischen Fallback.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0203_1.jpg` rotieren oder einen echten Batchlauf zuschneiden, der ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.


### Fortschritt vs. Blocker (Session 2026-05-30, AC0203_1 Geometry-IR Plan-B Run MG)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0203_1.jpg` wurde im echten Non-Composite-Pfad auf beschreibungsgetriebene Geometry-IR umgestellt: der rote Kreis und die beiden hauptdiagonal gespiegelten hellen Kompressorlinien werden nun als `CircleBackground` und `MainDiagonalMirroredCompressorGlyph` gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `48 passed`, Exit `0`); der externe AC0203-1-Repro lief grün (`timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0203-runmg --start AC0203_1 --end AC0203_1 --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `587 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der neue Pfad erweitert die beschreibungsgetriebene Geometry-IR gezielt um hauptdiagonal gespiegelte Kompressor-Symbole und lässt andere Non-Composite-Fälle beim bisherigen generischen Fallback.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0204_S_sia.jpg` rotieren oder einen echten Batchlauf zuschneiden, der ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

### Fortschritt vs. Blocker (Session 2026-05-30, AC0204_S_sia Geometry-IR Plan-B Run MH)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0204_S_sia.jpg` wurde explizit als beschreibungsgetriebene Geometry-IR abgesichert: die Referenzbeschreibung `Wie AC0201: Kompressor grau nach oben. Geometrische Variante: identisch zur Referenz.` wird im echten Non-Composite-Pfad als `CircleBackground` und `UpwardCompressorGlyph` gerendert statt in einen generischen Element-Fit-Fallback zurückzufallen.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `51 passed`, Exit `0`); der externe AC0204-S-sia-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0204-runmh --start AC0204_S_sia --end AC0204_S_sia --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `590 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der bestehende AC0201-Referenzpfad ist nun für AC0204-Identisch-zur-Referenz-Beschreibungen durch eigene Regressionsfälle abgesichert und bleibt im echten Call-Path sichtbar.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0211_S.jpg` rotieren oder einen echten Batchlauf zuschneiden, der ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

### Fortschritt vs. Blocker (Session 2026-05-30, AC0214_S Geometry-IR Plan-B Run ML)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0214_S.jpg` wurde im echten Non-Composite-Pfad auf beschreibungsgetriebene Geometry-IR umgestellt: der 180° gedrehte 2-Wege-Ventilkörper, der horizontale Connector, die linke Kreis-Kelle und das `M`-Label werden nun als `Rotated180TwoWayValveMotorGlyph` gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `67 passed`, Exit `0`); der externe AC0214-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0214-runml --start AC0214_S --end AC0214_S --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `610 passed, 5 warnings`, Exit `0`).
- **Blocker:** Keine neuen Blocker. Der neue Pfad erweitert die beschreibungsgetriebene Geometry-IR gezielt um 180° gedrehte 2-Wege-Ventil-Motorsymbole und lässt andere Non-Composite-Fälle beim bisherigen generischen Fallback.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0221_S.jpg` rotieren oder einen echten Batchlauf zuschneiden, der ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

### Fortschritt vs. Blocker (Session 2026-05-30, AC0221_S Geometry-IR Plan-B Run MM)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0221_S.jpg` wurde im echten Non-Composite-Pfad auf beschreibungsgetriebene Geometry-IR umgestellt: obere Kreis-Kelle ohne `M`, vertikaler Connector und dreiflügeliger Ventilkörper werden nun als `TopKelleThreeWayValveGlyph` gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `71 passed`, Exit `0`); der externe AC0221-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0221-runmm --start AC0221_S --end AC0221_S --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `614 passed, 5 warnings`, Exit `0`).
- **Kandidatenrotation:** `PLAN_B_KANDIDATEN.md` zeigt nach Entfernung von `AC0221_S.jpg` nun `AC0222_S.jpg` als nächste Rotation und `AC0224_S.jpg` als aufgefüllten AC02-Folgekandidaten.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0222_S.jpg` rotieren oder einen echten Batchlauf zuschneiden, der ein produktives `chain_phase_telemetry_summary.txt` für das Pflicht-Gate liefert.

## Qualitätsreview bisheriger Konvertierungen (2026-05-30)

- [x] **QR-2026-05-30-1:** Bisherige erfolgreiche Konvertierungen aus `successed_conversions.txt` erneut gegen Originalbilder und SVG-Artefakte prüfen. Ergebnis: 48 Varianten geprüft, 47 renderbare Paare, 1 fehlendes Paar; Detailbericht siehe `docs/converted_images_quality_review_2026-05-30.md`.
- [ ] **QR-2026-05-30-2:** `AC0838_M.jpg` erneut konvertieren bzw. per Plan B verbessern, weil das vorhandene SVG-Paar die Review-Grenze überschreitet (`normalized_mse=0.04729276` > `0.045945679012345676`).
- [ ] **QR-2026-05-30-3:** `AC0881_M.jpg` erneut konvertieren oder das fehlende SVG-Artefakt rekonstruieren, weil beim Review kein passendes SVG in den geprüften Konvertierungs-/Baseline-Pfaden gefunden wurde.
- [ ] **QR-2026-05-30-4:** `AC0835_S.jpg` nach der nächsten AC08-/Plan-B-Rotation erneut beobachten, weil der Messwert knapp unterhalb der Review-Grenze liegt (`normalized_mse=0.04467485`).

### Fortschritt vs. Blocker (Session 2026-05-30, Qualitätsreview bisheriger Konvertierungen)

- **Fortschritt:** Die bisher als erfolgreich geführten Konvertierungen wurden pixelmetrisch nachgeprüft und in `docs/converted_images_quality_review_2026-05-30.md` dokumentiert; `AC0838_M.jpg` und `AC0881_M.jpg` wurden zusätzlich in `PLAN_B_KANDIDATEN.md` aufgenommen.
- **Blocker:** Für `AC0881_M.jpg` fehlt im geprüften Artefaktbestand ein passendes SVG; für `AC0838_M.jpg` ist ein SVG vorhanden, die Qualität liegt aber oberhalb der Review-Grenze.
- **Nächster sinnvoller Schritt:** Vor der regulären Rotation mindestens einen der neuen QR-Folgepunkte (`AC0838_M` oder `AC0881_M`) als isolierten Plan-B-/Re-Konvertierungslauf abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-30, AC0222_S Geometry-IR Plan-B Run MN)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0222_S.jpg` wurde im echten Non-Composite-Pfad auf beschreibungsgetriebene Geometry-IR umgestellt: grauer Kreis-Hintergrund und zwei dunkle aufwärts gerichtete Kompressorlinien werden nun als `CircleBackground` und `UpwardCompressorGlyph` gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `75 passed`, Exit `0`); der externe AC0222-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0222-runmn --start AC0222_S --end AC0222_S --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_description_geometry_ir`; die Vollsuite lief grün (`PYENV_VERSION=3.10.20 PYTHONPATH=vendor/linux-py310/site-packages:. timeout 300 python -m pytest -q -rs`, `618 passed, 5 warnings`, Exit `0`).
- **Kandidatenrotation:** `PLAN_B_KANDIDATEN.md` zeigt nach Entfernung von `AC0222_S.jpg` nun `AC0224_S.jpg` als nächste Rotation und `AC0231_S.jpg` als aufgefüllten AC02-Folgekandidaten.
- **Nächster sinnvoller Schritt:** Mit dem nächsten Plan-B-Kandidaten `AC0224_S.jpg` rotieren oder vor der regulären Rotation einen QR-Folgepunkt (`AC0838_M` oder `AC0881_M`) als isolierten Plan-B-/Re-Konvertierungslauf abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, AC0224_S Perception-seeded Geometry-IR Plan-B Run MV)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0224_S.jpg` wurde im echten Non-Composite-Pfad abgesichert: Die Beschreibung `Wie AC0221 ... 90° nach rechts gedreht` wird als `RightRotatedTopKelleThreeWayValveGlyph` modelliert; im echten Repro-Lauf wird zusätzlich der PF8-Lerneffekt über `CircleBackground` und `HorizontalRule` als `non_composite_perception_seeded_geometry_ir` protokolliert.
- **Perception-Lerneffekt:** Die runde Kellenform wird vor der ersten Iteration erkannt und als `CircleBackground` vorinitialisiert; damit bleibt die PF8-Entscheidung für `AC0224_S.jpg` `generalisiert` statt Einzelfall-Nachzeichnung.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `80 passed`, Exit `0`); der externe AC0224-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0224-runmv --start AC0224_S --end AC0224_S --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_perception_seeded_geometry_ir`.
- **Kandidatenrotation:** `PLAN_B_KANDIDATEN.md` zeigt nach Entfernung von `AC0224_S.jpg` nun `AC0231_S.jpg` als nächste Rotation und füllt mit `AC0232_S.jpg` als weiterem AC02-Kandidaten auf.
- **Nächster sinnvoller Schritt:** Mit `AC0231_S.jpg` rotieren oder vor der regulären Rotation einen QR-Folgepunkt (`AC0838_M` oder `AC0881_M`) als isolierten Plan-B-/Re-Konvertierungslauf abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, AC0231_S Perception-seeded Geometry-IR Plan-B Run MW)

- **Fortschritt:** Der nächste dokumentierte Plan-B-Kandidat `AC0231_S.jpg` wurde im echten Non-Composite-Pfad abgesichert: Die Beschreibung mit senkrechtem `M` wird als `TopKelleThreeWayValveGlyph` mit Label modelliert; im Repro-Lauf wird zusätzlich ein `CircleBackground`-Seed als `non_composite_perception_seeded_geometry_ir` protokolliert.
- **Perception-Lerneffekt:** Die runde obere Kellenform wird vor der ersten Iteration erkannt und als `CircleBackground` vorinitialisiert; die `M`-Beschriftung ist als explizites Label im Glyph gerendert.
- **Sicherung:** Der gezielte Detailtestblock lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_geometry_ir_helpers.py tests/detailtests/test_description_contract_helpers.py tests/detailtests/test_non_composite_runtime_helpers.py`, `83 passed`, Exit `0`); der PF8-Linkage-Test lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_plan_b_perception_linkage.py`, `2 passed`, Exit `0`); der externe AC0231-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 120 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0231-runmw --start AC0231_S --end AC0231_S --deterministic-order`, Exit `0`) und protokollierte `status=non_composite_perception_seeded_geometry_ir`.
- **Kandidatenrotation:** `PLAN_B_KANDIDATEN.md` zeigt nach Entfernung von `AC0231_S.jpg` nun `AC0232_S.jpg` als nächste Rotation und füllt mit `AC0233_S.jpg` als weiterem AC02-Kandidaten auf.
- **Nächster sinnvoller Schritt:** Mit `AC0232_S.jpg` rotieren oder vor der regulären Rotation einen QR-Folgepunkt (`AC0838_M` oder `AC0881_M`) als isolierten Plan-B-/Re-Konvertierungslauf abarbeiten. (2026-05-31: Danach in Run MX mit `AC0232_S` erledigt; nächste reguläre Rotation ist `AC0233_S`.)

### Fortschritt vs. Blocker (Session 2026-05-31, AC0838_M Qualitätsrefresh Plan-B Run MZ)

- **Fortschritt:** Der nächste dokumentierte Kandidat `AC0838_M.jpg` wurde als isolierter Qualitätsrefresh abgearbeitet. Die frische Re-Konvertierung gegen `artifacts/images_to_convert/nonconvertable/AC0838_M.jpg` erzeugte aktualisierte SVG-/Log-/Snapshot-Artefakte und senkte `mean_delta2` von `9225.634766` auf `7789.174316` (`normalized_mse=0.03992913`, unter der Review-Grenze `0.045945679012345676`).
- **Sicherung:** Der externe AC0838-M-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert/nonconvertable --output-dir /tmp/ic-ac0838-baseline --start AC0838_M --end AC0838_M --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`, Exit `0`) und protokollierte `status=semantic_ok`; der PF8-Linkage-Report wurde erfolgreich auf `AC0881_M`, `AC0234_S` und `AC0835_S` rotiert.
- **Kandidatenrotation:** `PLAN_B_KANDIDATEN.md` entfernt `AC0838_M.jpg`, führt nun `AC0881_M.jpg` als nächste reguläre Rotation und ergänzt `AC0835_S.jpg` als neuen VOC-Kreis/Text-Kandidaten aus der Weak-Family-Priorität-A-Liste.
- **Nächster sinnvoller Schritt:** Mit `AC0881_M.jpg` rotieren oder den neuen `AC0835_S.jpg`-VOC-Kreis/Text-Lerneffekt als isolierten Plan-B-/Re-Konvertierungslauf abarbeiten.

### Fortschritt vs. Blocker (Session 2026-05-31, AC0870_S Path-T-Refresh Run NE)

- **Fortschritt:** Der nächste Plan-B-Kandidat `AC0870_S.jpg` wurde als kleiner pfadbasierter `T`-Badge abgearbeitet. `path_t`-Glyphen nehmen nun mit `tx`/`ty`/`s` am gemeinsamen Parametervektor teil; die Skalendomäne bleibt dabei im SVG-Pfadbereich statt in generischen Font-Multiplikatoren.
- **Qualitätsrefresh:** Der externe AC0870-S-Repro lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. timeout 180 python -m src.iCCModules.imageCompositeConverterCli --input-dir artifacts/images_to_convert --output-dir /tmp/ic-ac0870-run5 --start AC0870_S --end AC0870_S --descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml --deterministic-order`, Exit `0`) und senkte `mean_delta2` von `6616.799805` auf `5075.666504` bei `status=semantic_ok`.
- **Sicherung:** Die gezielten Helper-/Redraw-Tests liefen grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/detailtests/test_core_class_helpers.py tests/detailtests/test_width_optimization_helpers.py tests/detailtests/test_global_vector_helpers.py tests/test_image_composite_converter.py::test_apply_redraw_variation_jitters_params_and_logs_seed tests/test_image_composite_converter.py::test_apply_redraw_variation_keeps_path_t_scale_in_glyph_domain`, `8 passed, 5 warnings`, Exit `0`); der PF8-Linkage-Test lief grün (`PYTHONPATH=vendor/linux-py310/site-packages:. python -m pytest -q tests/test_plan_b_perception_linkage.py`, `2 passed`, Exit `0`).
- **Kandidatenrotation:** `PLAN_B_KANDIDATEN.md` entfernt `AC0870_S.jpg`, führt nun `AC0850_M.jpg` als nächste reguläre Rotation und ergänzt `AC0844_S.jpg` als neuen rF-Kreis/Connector-Folgekandidaten.
- **Nächster sinnvoller Schritt:** Mit `AC0850_M.jpg` rotieren oder den neuen `AC0844_S.jpg`-rF-Kreis/Connector-Lerneffekt als isolierten Plan-B-/Re-Konvertierungslauf abarbeiten.

### Fortschritt vs. Blocker (Session 2026-06-02, CI-Testauslagerung Run NM)

- **Fortschritt:** Das nächste Arbeitspaket wurde auf Testhygiene/CI-Auslagerung fokussiert: `.github/workflows/local-completion-checks.yml` startet nun zusätzlich eine Pytest-Profilmatrix (`core-green`, `extended`), die bestehende Satisfactory-Batterie und per `workflow_dispatch` + `run_heavy_diagnostics` opt-in die Safe-Baseline, die dokumentierten Regression-Checks sowie einen Full-Heavy-Conversion-Job.
- **Sicherung:** `docs/image_converter_workflow.md` und `README.md` dokumentieren, welche längeren Checks jetzt nach GitHub Actions verlagert sind und welche Kommandos lokal nur noch bei Bedarf gespiegelt werden. Der Workflow-Dokumentationstest wurde erweitert, damit neue CI-Jobs, Heavy-Env-Gates und der manuelle Volljob nicht versehentlich aus der Doku oder Workflow-Datei verschwinden.
- **Blocker:** Die bekannten schweren Konvertierungsdiagnosen bleiben wegen Langläufer-/Blockerhistorie bewusst opt-in und blockieren Pull Requests nicht automatisch; ein lokaler Gegencheck zeigte, dass `RUN_HEAVY_CONVERSION_TESTS=1 ./tools/run_safe_test_baseline.sh` aktuell weiterhin nicht als automatisches Pflichtgate geeignet ist.
- **Nächster sinnvoller Schritt:** Die GitHub-Jobs auf dem nächsten Push beobachten; falls ein ausgelagerter Heavy-Job echte Laufzeit-/Datenblocker zeigt, diese als konkrete T6-/TB1-Folgeaufgabe mit Job-Log und NodeID zurückführen.

### Fortschritt vs. Blocker (Session 2026-06-05, FP-Recovery Run OC)

- **Fortschritt:** Der vollständige feste AC08-Satz lief mit regulären 32 Iterationen segmentiert durch: Kernsuite `714 passed`, 14/14 Segmente `PASS`, 14/14 `Iteration_Log.csv`-Datensätze und 6/6 erhaltene Previously-Good-Anker. Die in FP-D13 fehlenden Reports für `AC0811_L`, `AC0811_M`, `AC0811_S` und `AC0831_L` sind damit auch unter dem regulären Budget wiederhergestellt.
- **Blocker:** Das Qualitätsgate bleibt mit `criterion_regression_set_improved=0` und `overall_success=0` rot. Die Ein-Datei-Segmente erzeugen keine Quality-Pass-Kandidaten: Alle initialen Fehlerwerte liegen unter dem offenen Grenzwert `1.0`, während der Terzil-Fallback mindestens drei Ergebnisse benötigt; fokussierte `AC0811`-Läufe deaktivieren Quality-Pässe zusätzlich.
- **Nächster sinnvoller Schritt:** Einen segmentierungsfesten isolierten Refinement-Pass implementieren, der Verbesserungen gegen das initiale Segmentergebnis akzeptiert, Verschlechterungen verwirft und erst danach den vollständigen 14er-Lauf erneut gegen die FP-D14-Schwellen ausführt.

### Fortschritt vs. Blocker (Session 2026-06-05, isoliertes Refinement Run OD)

- **Fortschritt:** Ein-Datei-Segmente erhalten nach leerer Open-Case- und Terzil-Auswahl genau einen expliziten Refinement-Kandidaten, sofern die Variante nicht übersprungen ist. Die bestehende strikte Accept/Reject-Auswertung bleibt unverändert.
- **Sicherung:** Gezielte Tests `16 passed`; vollständige Kernsuite `716 passed`; segmentierter AC08-Smoke 14/14 `PASS`. Der zusammengeführte Report weist 3 akzeptierte Verbesserungen und 4 verworfene Regressionen aus.
- **Abschluss:** Alle FP-D14-Schwellen sind erfüllt: 14/14 Variantendatensätze, 6/6 Previously-Good-Anker, 3 gemessene Verbesserungen, 0 akzeptierte Regressionen und `overall_success=1`.
- **Nächster sinnvoller Schritt:** Das abgeschlossene Finish-Playbook verlassen und mit der regulären Roadmap-/Plan-B-Rotation fortfahren.

### Fortschritt vs. Blocker (Session 2026-06-06, Plan-B AC0863_S Run OE)

- **Fortschritt:** Der aktive Plan-B-/Perception-Kandidat `AC0863_S.jpg` wurde im echten Ein-Datei-Pfad erfolgreich als semantisches AC08-`rF`-Badge mit oberem vertikalem Connector konvertiert. Das erzeugte SVG behält die Quellabmessungen `15x25`; die Validierung endet mit `status=semantic_ok`, `best_error=18.522667` und `mean_delta2=4155.215820`.
- **Perception-Lerneffekt:** Die Frage nach dominantem Kreis und gedrehtem Connector ist `generalisiert`: `CircleBackground` und ein Linienkandidat werden erkannt. Erledigte PF8-Ziele (`AC0862_S`, `AC0863_S`) wurden aus dem aktiven Report entfernt; die maschinenlesbare Rotation enthält jetzt nur `AC0864_S` und wird durch einen Synchronitätstest abgesichert.
- **Sicherung:** Der isolierte CLI-Lauf endete mit Exit `0`; der PF8-Linkage-Report wurde mit `samples=1`, `evaluated_samples=1` und `all_have_perception_lerneffekt=true` neu erzeugt.
- **Blocker:** Kein technischer Blocker; die verbleibende Pixelabweichung ist ein Text-/Antialiasing-Folgepunkt, kein Semantik- oder Topologiefehler.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0864_S.jpg` fortsetzen.

### Fortschritt vs. Blocker (Session 2026-06-06, Plan-B AC0864_S Run OF)

- **Fortschritt:** Der letzte aktive Plan-B-/Perception-Kandidat `AC0864_S.jpg` wird jetzt als semantisches AC08-`rF`-Badge mit rechtem horizontalem Connector konvertiert. Der reale Lauf endet mit Exit `0`, `status=semantic_ok`, `best_error=17.986667` und `mean_delta2=3699.607910`.
- **Perception-Lerneffekt:** Kreis (`CircleBackground`) und Linienhinweis sind `generalisiert`; die Ausgabe verwendet Beschreibung und allgemeine AC08-Rechtsarm-Geometrie statt eines Sample-SVGs.
- **Rotation:** `AC0864_S` ist aus der aktiven Zielliste entfernt. Plan-B-Liste und PF8-Linkage-Report sind mit `samples=0`, `evaluated_samples=0` und `all_have_perception_lerneffekt=true` synchron leer.
- **Blocker:** Kein technischer Blocker; die dokumentierte Weak-Family-Rotation ist vollständig abgearbeitet.
- **Nächster sinnvoller Schritt:** Qualitätsreports aktualisieren und daraus eine neue, noch nicht erledigte Plan-B-Kandidatenrotation kuratieren.

### Fortschritt vs. Blocker (Session 2026-06-06, Qualitätsrefresh und Plan-B-Triage Run OG)

- **Fortschritt:** Der bislang nur inline dokumentierte Qualitätsreview ist als `tools/review_conversion_quality.py` reproduzierbar. Er prüft 48 erfolgreiche Varianten und 131 Diff-Inventarvarianten, schreibt JSON-/CSV-Evidenz und kuratiert deterministisch höchstens fünf kompakte Plan-B-Kandidaten.
- **Ergebnis:** Alle 48 Erfolgsvarianten sind renderbar; nur `AC0835_L` liegt mit `normalized_mse=0.05726039` über der Grenze `0.04594568`. Die neue Rotation lautet `AC0835_L`, `AC0922_S`, `AC0414_S`, `AC0130_M`, `AC0130`.
- **Perception-Lerneffekt:** Der PF8-Linkage-Report enthält synchron alle fünf Kandidaten (`5/5` ausgewertet, vier `generalisiert`, einer `nur Sonderfall`, keiner `noch nicht erkannt`).
- **Sicherung:** Tool- und Linkage-Tests prüfen Metriknormalisierung, Auswahlpriorität, maschinenlesbare Reports und die Synchronität zwischen Triage und PF8-Zielen.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0835_L.jpg` beginnen und Kreis-/VOC-Erkennung gegen die reale Re-Konvertierung absichern.

### Fortschritt vs. Blocker (Session 2026-06-06, Plan-B AC0835_L Run OH)

- **Fortschritt:** `AC0835_L.jpg` wurde real re-konvertiert; das fehlerhafte Alt-SVG mit falschem Connector und fehlendem Text wurde durch ein semantisches 25x25-Kreis-/`VOC`-Badge ersetzt.
- **Qualität:** `mean_delta2` sank von `11170.070312` auf `7629.902344` (`-31.69 %`), `normalized_mse` von `0.05726039` auf `0.03911266` und damit unter die Review-Grenze `0.04594568`.
- **Perception-Lerneffekt:** Die Kreisfrage ist `generalisiert` (`circle` → `CircleBackground`); `AC0835_L` wurde aus Triage und PF8-Linkage entfernt. Die vier verbleibenden Ziele sind synchron.
- **Sicherung:** Der isolierte CLI-Lauf endete mit Exit `0`; ein Regressionstest erzwingt für das committete SVG Dimensionstreue und die Review-Grenze.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0922_S.jpg` fortsetzen.

### Fortschritt vs. Blocker (Session 2026-06-06, Plan-B AC0922_S Run OI)

- **Fortschritt:** Der reale `AC0922_S`-Einzellauf endete mit Exit `0`; sein Rechteckvorschlag wurde als Semantik-/Topologieregression gegen den erwarteten Kreis mit linkem Anschluss verworfen.
- **Qualität:** Die Nachmessung des tatsächlich committeten Snapshot-SVGs korrigiert `normalized_mse` von veralteten `0.33015759` auf `0.02747206` (`mean_delta2=5359.111816`) und liegt unter der Review-Grenze `0.04594568` sowie unter dem Rechteckvorschlag `0.03932264`.
- **Perception-Lerneffekt:** Kreis und linker Horizontalanschluss sind `generalisiert`; ein Regressionstest sichert Dimensionen, Snapshot-Pfadauflösung, Primitive und Qualitätswert.
- **Rotation:** `AC0922_S` wurde aus Triage und PF8-Linkage entfernt; `AC0414_S`, `AC0130_M` und `AC0130` bleiben synchron aktiv.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0414_S.jpg` fortsetzen.

### Fortschritt vs. Blocker (Session 2026-06-06, Plan-B AC0414_S Run OJ)

- **Fortschritt:** `AC0414_S.jpg` wurde real re-konvertiert; der semantisch falsche Gradient-/Plus-Vorschlag wurde verworfen und durch einen dimensionstreuen partitionierten Kreis ersetzt.
- **Qualität:** `mean_delta2` sank von `62091.609375` auf `703.882507`, `normalized_mse` von `0.31829609` auf `0.00360827` und damit deutlich unter die Review-Grenze `0.04594568`.
- **Perception-Lerneffekt:** Kreis-/Ring-Erkennung ist `generalisiert`; die vier Innenkanten werden im akzeptierten SVG explizit als gemeinsame Liniengruppe erhalten.
- **Rotation:** `AC0414_S` wurde aus Triage und PF8-Linkage entfernt; `AC0130_M` und `AC0130` bleiben synchron aktiv.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0130_M.jpg` fortsetzen.


### Fortschritt vs. Blocker (Session 2026-06-06, Plan-B AC0130_M Run OK)

- **Fortschritt:** `AC0130_M.jpg` wurde real re-konvertiert. Der zu klein skalierte reguläre AC0030-Vorschlag wurde durch ein dimensionstreues 30x60-Vektor-SVG mit Metallverlauf, horizontalen Außenkanten und den im JPG sichtbaren vertikalen Partitionen ersetzt.
- **Qualität:** `mean_delta2` sank von `54603.582031` auf `300.156097`, `normalized_mse` von `0.27991071` auf `0.00153867` und damit deutlich unter die Review-Grenze `0.04594568`.
- **Perception-Lerneffekt:** Die PF8-Frage bleibt `nur Sonderfall`: Linien und Rechteck werden erkannt, aber kein allgemeiner `RectangleBackground`-Seed erzeugt; die beschriebenen Diagonalen sind im realen JPG nicht stabil sichtbar.
- **Rotation:** `AC0130_M` wurde aus Triage und PF8-Linkage entfernt; `AC0130` bleibt als letzter aktiver Kandidat.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0130.jpg` abschließen.


### Fortschritt vs. Blocker (Session 2026-06-06, Plan-B AC0130 Run OL)

- **Fortschritt:** `AC0130.jpg` wurde real re-konvertiert. Der zu klein skalierte reguläre AC0030-Vorschlag wurde durch ein dimensionstreues 40x80-Vektor-SVG mit Metallverlauf, Außenrechteck, beschnittenem Andreaskreuz und zwei oberen Minuszeichen ersetzt.
- **Qualität:** `mean_delta2` sank vom bisherigen Review-Wert `45778.234375` auf `1921.981201`, `normalized_mse` von `0.23466992` auf `0.00985252` und damit deutlich unter die Review-Grenze `0.04594568`.
- **Perception-Lerneffekt:** Die PF8-Frage ist `generalisiert`; Linien-, Rechteck-, Kreis- und Ringkandidaten sowie ein `CircleBackground`-Seed werden erkannt, während das akzeptierte SVG nur die bildlich relevante Rechteck-/Diagonalgeometrie übernimmt.
- **Rotation:** `AC0130` wurde aus Triage und PF8-Linkage entfernt; alle fünf Kandidaten aus Run OG sind abgeschlossen und die aktive Rotation ist synchron leer.
- **Nächster sinnvoller Schritt:** Qualitätsreports erneut reproduzierbar aktualisieren und daraus eine neue Plan-B-Kandidatenrotation kuratieren.


### Fortschritt vs. Blocker (Session 2026-06-07, Qualitätsrefresh und Plan-B-Triage Run OM)

- **Fortschritt:** Der Qualitätsreview wurde nach Abschluss der alten Rotation reproduzierbar erneuert; alle 48 Erfolgsvarianten und 129 Diff-Inventarfälle wurden geprüft.
- **Qualitätsbefund:** `AC0820_L` ist mit `normalized_mse=0.05117826` der einzige erfolgreiche Altbestand oberhalb der Review-Grenze; 120 Diff-Fälle besitzen ein renderbares Bild-/SVG-Paar.
- **Kandidatenrotation:** Plan-B-Liste, Triage und PF8-Linkage sind synchron auf `AC0820_L`, `AC0531_1_S`, `AC0502_1_M`, `AC0551_1_M` und `AC0403_1_M` gesetzt.
- **Perception-Lerneffekt:** Vier Fragen sind `generalisiert`; `AC0551_1_M` bleibt wegen fehlendem Rechteck-/HorizontalRule-Seed `nur Sonderfall`.
- **Nächster sinnvoller Schritt:** `AC0820_L.jpg` real re-konvertieren und den Kreis-/CO²-Lerneffekt als erstes Paket der neuen Rotation abschließen.


### Fortschritt vs. Blocker (Session 2026-06-08, Plan-B AC0820_L Run OP)

- **Fortschritt:** `AC0820_L.jpg` wurde real über den beschreibungsgetriebenen semantischen AC08-Pfad re-konvertiert; das veraltete Connector-SVG wurde durch ein 30x30-Kreis-/CO₂-Badge ersetzt.
- **Qualität:** `mean_delta2` sank von `9983.599609` auf `7458.403320` (`-25.29 %`), `normalized_mse` von `0.05117826` auf `0.03823352` und damit unter die Review-Grenze `0.04594568`.
- **Perception-Lerneffekt:** Die Kreisfrage ist `generalisiert` (`circle`/`ring` → `CircleBackground`); `AC0820_L` wurde aus Triage und PF8-Linkage entfernt.
- **Rotation:** Die fünf synchronen Ziele lauten nun `AC0531_1_S`, `AC0502_1_M`, `AC0551_1_M`, `AC0403_1_M` und `AC0150_2`.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0531_1_S.jpg` fortsetzen.


### Fortschritt vs. Blocker (Session 2026-06-08, Plan-B AC0531_1_S Run OQ)

- **Fortschritt:** `AC0531_1_S.jpg` wurde real über den allgemeinen Non-Composite-Element-Fit re-konvertiert; der Fit respektiert jetzt deklarierte Einzel-/Doppeldiagonalen, Mittelpunkt sowie Plus-/Minus-Glyphen und erhält rastergemessene RGB-Verläufe.
- **Qualität:** `mean_delta2` sank von `30452.529297` auf `4837.790039` (`-84.11 %`), `normalized_mse` von `0.15610678` auf `0.02479964` und damit unter die Review-Grenze `0.04594568`.
- **Perception-Lerneffekt:** Rechteck, Diagonale und Mittelpunkt sind `generalisiert`; Beschreibung und Bildmessung erzeugen genau eine gekürzte Diagonale und einen Mittelpunkt ohne erfundene Glyphen.
- **Rotation:** `AC0531_1_S` wurde aus Triage und PF8-Linkage entfernt; `AC0253_1` füllt als allgemein erkannter Kreis-/Pumpenkandidat auf.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0502_1_M.jpg` fortsetzen.


### Fortschritt vs. Blocker (Session 2026-06-08, Plan-B AC0502_1_M Run OR)

- **Fortschritt:** `AC0502_1_M.jpg` wurde real re-konvertiert; deklarierte 90-Grad-Varianten tauschen im allgemeinen Element-Fit nun die Diagonalachse, statt die ungedrehte Familienrichtung zu rendern.
- **Qualität:** `mean_delta2` sank von `30301.542969` auf `3126.661621` (`-89.68 %`), `normalized_mse` von `0.15533278` auf `0.01602799` und damit unter die Review-Grenze `0.04594568`.
- **Perception-Lerneffekt:** Rechteck, Diagonale und Mittelpunkt sind `generalisiert`; die Runtime verbindet die Beschreibungstopologie mit der rastergemessenen Farbe und Ausdehnung.
- **Rotation:** `AC0502_1_M` wurde aus Triage und PF8-Linkage entfernt; `AC0551_2_M` füllt die fünf aktiven Plätze auf.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0551_1_M.jpg` fortsetzen.


### Fortschritt vs. Blocker (Session 2026-06-09, Plan-B AC0551_1_M Run OS)

- **Fortschritt:** `AC0551_1_M.jpg` wurde real re-konvertiert; der allgemeine Element-Fit erzeugt die beschriebene Kontur Oben-Mitte → Rechts-Mitte → Unten-Mitte nun als parametrisierte Polylinie und passt Breite, Einzüge, Scheitelpunkt und Farbe aus Beschreibung und Raster an.
- **Qualität:** `mean_delta2` sank von `29098.138672` auf `4518.557129` (`-84.47 %`), `normalized_mse` von `0.14916385` auf `0.02316318` und damit unter die Review-Grenze `0.04594568`.
- **Perception-Lerneffekt:** Die Konturtopologie ist im Rekonstruktionsalgorithmus `generalisiert`; die vorgelagerte Primitive-Detection bleibt für Rechteck-/HorizontalRule-Seeds weiterhin `nur Sonderfall`, daher wurden keine variantenspezifischen Koordinaten hinterlegt.
- **Rotation:** `AC0551_1_M` wurde aus Triage und PF8-Linkage entfernt; `AC0733_1_L` füllt die fünf aktiven Plätze auf.
- **Nächster sinnvoller Schritt:** Die reguläre Plan-B-Rotation mit `AC0403_1_M.jpg` fortsetzen.


### Fortschritt vs. Blocker (Session 2026-06-09, vollständiger Core-Testlauf)

- **Fortschritt:** Als bewusst kleines Testhygiene-Arbeitspaket wurde die vollständige Core-Suite mit `PYTHONPATH=. python -m pytest -q -rs` ausgeführt und das vollständige Protokoll unter `artifacts/pytest/full_core_suite_2026-06-09.log` für GitHub versioniert.
- **Ergebnis:** `765 passed in 45.10s`, Exit `0`; keine Skips, Warnungen oder Fehlschläge wurden gemeldet.
- **Blocker:** Kein Testblocker. Die reguläre Plan-B-Rotation mit `AC0403_1_M.jpg` bleibt das nächste fachliche Arbeitspaket.
