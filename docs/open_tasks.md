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

- [ ] D5: Metrik-Fortsetzung als Multi-Objective-Prototyp evaluieren.
  - Hintergrund: Reiner Pixel-Fehler kann Anti-Aliasing-Effekte übergewichten und so semantisch plausible Geometrie verdrängen.
  - Umsetzungsidee:
    - Experimenteller Score: `pixel_error + geometry_penalty + semantic_penalty` (gewichtete Summe).
    - A/B-Vergleich gegen den aktuellen Score auf einer fixierten Problemfallliste.
  - Akzeptanzkriterien:
    - Dokumentierter Vorher/Nachher-Vergleich in `docs/` inkl. Parametergewichten, Gewinnerliste und Fehlertypen.
    - Kein Rückschritt beim AC08-Success-Gate.

- [ ] C1: `src/imageCompositeConverter.py` schrittweise in Module mit Blöcken von ca. 100 Zeilen aufteilen.
  - Hintergrund: Die Datei hat aktuell deutlich über 10k Zeilen; Refactoring erfolgt bewusst in mehreren, testbaren Teilschritten statt als Big-Bang.
  - Vorgehen: pro Teilbereich (z. B. Regionen-Analyse, IO/Reporting, Rendering, Optimierung, CLI) jeweils ein neues Modul mit klarer API erstellen und im Hauptskript nur noch schlanke Delegation belassen.
  - Akzeptanzkriterium für jeden Teilschritt: bestehende Tests laufen weiter, externe Funktionsnamen bleiben kompatibel, und der offene Aufgabenstand wird hier dokumentiert.
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
  - Nächster geplanter Schritt: weitere IO-/Reporting-Teilstrecken in denselben kleinen Schritten extrahieren.

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
- [x] B3: Deterministischen Diagnosemodus für die Dateireihenfolge ergänzen (ohne `shuffle`), um schwer reproduzierbare Batchfehler schneller zu isolieren.
  - 2026-04-03: Neuer CLI-Schalter `--deterministic-order` ergänzt.
  - Der Modus deaktiviert Shuffle bei Dateiliste, Quality-Pass-Kandidaten sowie Template-Transfer-Donor/Scale-Reihenfolge.
  - Für reproduzierbare Läufe wird `Action.STOCHASTIC_RUN_SEED` in diesem Modus auf `0` gesetzt.



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
