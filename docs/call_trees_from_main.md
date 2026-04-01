# Call Trees ab `main()`

Automatisch erzeugte, **statische** Aufrufbäume (AST-basiert) ausgehend von den dokumentierten Einstiegspunkten.

## `src/imageCompositeConverter.py`

- `main()`
  - `parseArgs()`
  - `_runSvgRenderSubprocessEntrypoint()`
    - `_renderSvgToNumpyInprocess()`
  - `_optionalLogCapture()`
  - `buildLinuxVendorInstallCommand()`
    - `_requiredVendorPackages()`
  - `_promptInteractiveRange()`
  - `_sharedPartialRangeToken()`
  - `_normalizeRangeToken()`
  - `getBaseNameFromFile()`
  - `_compactRangeToken()`
  - `_extractRefParts()`
  - `_resolveCliCsvAndOutput()`
    - `_autoDetectCsvPath()`
  - `_resolveDescriptionXmlPath()`
  - `_loadDescriptionMapping()`
    - `_loadDescriptionMappingFromXml()`
    - `_loadDescriptionMappingFromCsv()`
  - `_bootstrapRequiredImageDependencies()`
    - `_missingRequiredImageDependencies()`
  - `analyzeRange()`
  - `convertRange()`
    - `_defaultConvertedSymbolsRoot()`
    - `_convertedSvgOutputDir()`
    - `_diffOutputDir()`
    - `_reportsOutputDir()`
    - `_inRequestedRange()`
      - `_normalizeExplicitRangeToken()`
      - `_matchesExactPrefixFilter()`
      - `_isExplicitSizeVariantToken()`
      - `_matchesPartialRangeToken()`
    - `_renderEmbeddedRasterSvg()`
      - `_svgHrefMimeType()`
    - `_sniffRasterSize()`
    - `_createDiffImageWithoutCv2()`
    - `_conversionRandom()`
    - `_loadExistingConversionRows()`
      - `_isSemanticTemplateVariant()`
    - `_readSvgGeometry()`
    - `runIterationPipeline()`
      - `_semanticAuditRecord()`
      - `_semanticQualityFlags()`
    - `_readValidationLogDetails()`
    - `_tryTemplateTransfer()`
      - `_rankTemplateTransferDonors()`
      - `_templateTransferDonorFamilyCompatible()`
        - `_extractSymbolFamily()`
      - `_estimateTemplateTransferScale()`
      - `_buildTransformedSvgFromTemplate()`
      - `_extractSvgInner()`
      - `_semanticTransferIsCompatible()`
        - `_connectorArmDirection()`
        - `_connectorStemDirection()`
      - `_semanticTransferScaleCandidates()`
      - `_templateTransferScaleCandidates()`
      - `_semanticTransferRotations()`
      - `_semanticTransferBadgeParams()`
      - `_templateTransferTransformCandidates()`
    - `_normalizedGeometrySignature()`
    - `_maxSignatureDelta()`
    - `_computeSuccessfulConversionsErrorThreshold()`
    - `_loadQualityConfig()`
    - `_qualityConfigPath()`
    - `_writeQualityConfig()`
    - `_selectOpenQualityCases()`
    - `_selectMiddleLowerTercile()`
    - `_iterationStrategyForPass()`
    - `_adaptiveIterationBudgetForQualityRow()`
    - `_evaluateQualityPassCandidate()`
    - `_writeQualityPassReport()`
    - `_writeBatchFailureSummary()`
    - `_harmonizeSemanticSizeVariants()`
      - `_harmonizationAnchorPriority()`
      - `_familyHarmonizedBadgeColors()`
        - `_clipGray()`
      - `_scaleBadgeParams()`
        - `_needsLargeCircleOverflowGuard()`
    - `_writeSemanticAuditReport()`
    - `_writePixelDelta2Ranking()`
    - `_writeAc08WeakFamilyStatusReport()`
    - `_writeAc08RegressionManifest()`
    - `_writeAc08SuccessCriteriaReport()`
      - `_summarizePreviousGoodAc08Variants()`
    - `updateSuccessfulConversionsManifestWithMetrics()`
      - `_readSuccessfulConversionManifestMetrics()`
        - `_parseSuccessfulConversionManifestLine()`
      - `collectSuccessfulConversionQualityMetrics()`
        - `_loadIterationLogRows()`
        - `_findImagePathByVariant()`
      - `_isSuccessfulConversionCandidateBetter()`
      - `_successfulConversionMetricsAvailable()`
      - `_storeSuccessfulConversionSnapshot()`
      - `_successfulConversionSnapshotPaths()`
      - `_successfulConversionSnapshotDir()`
      - `_mergeSuccessfulConversionMetrics()`
      - `_restoreSuccessfulConversionSnapshot()`
      - `_formatSuccessfulConversionManifestLine()`
      - `_latestFailedConversionManifestEntry()`
      - `_sortedSuccessfulConversionMetricsRows()`
  - `_formatUserDiagnostic()`

## `src/imageCompositeConverterRegions.py`

- Einstieg über `analyzeRangeImpl()`
  - `analyzeRangeImpl()`

## `src/overviewTiles.py`

- Einstieg über `generateConversionOverviews()`
  - `generateConversionOverviews()`
    - `createTiledOverviewImage()`
      - `_resolveOptionalDependencies()`
      - `_readPreview()`
        - `_renderSvg()`
        - `_readRaster()`

- Einstieg über `createTiledOverviewImage()`
  - `createTiledOverviewImage()`
    - `_resolveOptionalDependencies()`
    - `_readPreview()`
      - `_renderSvg()`
      - `_readRaster()`

- Einstieg über `_resolveOptionalDependencies()`
  - `_resolveOptionalDependencies()`

- Einstieg über `_readPreview()`
  - `_readPreview()`
    - `_renderSvg()`
    - `_resolveOptionalDependencies()`
    - `_readRaster()`

- Einstieg über `_readRaster()`
  - `_readRaster()`
    - `_resolveOptionalDependencies()`
