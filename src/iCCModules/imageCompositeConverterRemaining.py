from __future__ import annotations

import importlib
from pathlib import Path

from src.iCCModules import imageCompositeConverterDependencies as dependency_helpers
from src.iCCModules import imageCompositeConverterDualArrowBadge as dual_arrow_badge_helpers
from src.iCCModules import imageCompositeConverterElementDecomposition as element_decomposition_helpers
from src.iCCModules import imageCompositeConverterGradientStripeStrategy as gradient_stripe_strategy_helpers
from src.iCCModules import imageCompositeConverterImageLoading as image_loading_helpers
from src.iCCModules import imageCompositeConverterIterationInitialization as iteration_initialization_helpers
from src.iCCModules import imageCompositeConverterIterationBindings as iteration_bindings_helpers
from src.iCCModules import imageCompositeConverterIterationContext as iteration_context_helpers
from src.iCCModules import imageCompositeConverterIterationDispatch as iteration_dispatch_helpers
from src.iCCModules import imageCompositeConverterIterationExecution as iteration_execution_helpers
from src.iCCModules import imageCompositeConverterIterationExecutionContext as iteration_execution_context_helpers
from src.iCCModules import imageCompositeConverterIterationFinalization as iteration_finalization_helpers
from src.iCCModules import imageCompositeConverterIterationModeRuntime as iteration_mode_runtime_helpers
from src.iCCModules import imageCompositeConverterIterationModeDependencies as iteration_mode_dependency_helpers
from src.iCCModules import imageCompositeConverterIterationModeDependencySetup as iteration_mode_dependency_setup_helpers
from src.iCCModules import imageCompositeConverterIterationModePreparation as iteration_mode_preparation_helpers
from src.iCCModules import imageCompositeConverterIterationModeRuntimePreparation as iteration_mode_runtime_preparation_helpers
from src.iCCModules import imageCompositeConverterIterationModeSetup as iteration_mode_setup_helpers
from src.iCCModules import imageCompositeConverterIterationOrchestration as iteration_orchestration_helpers
from src.iCCModules import imageCompositeConverterIterationPreparation as iteration_preparation_helpers
from src.iCCModules import imageCompositeConverterIterationRunPreparation as iteration_run_preparation_helpers
from src.iCCModules import imageCompositeConverterIterationRuntime as iteration_runtime_helpers
from src.iCCModules import imageCompositeConverterIterationSetup as iteration_setup_helpers
from src.iCCModules import imageCompositeConverterNaming as naming_helpers
from src.iCCModules import imageCompositeConverterMaskMetrics as mask_metrics_helpers
from src.iCCModules import imageCompositeConverterPerceptionGeometry as perception_geometry_helpers
from src.iCCModules import imageCompositeConverterSemanticAuditLogging as semantic_audit_logging_helpers
from src.iCCModules import imageCompositeConverterSemanticAc0223Runtime as semantic_ac0223_runtime_helpers
from src.iCCModules import imageCompositeConverterSemanticValidationContext as semantic_validation_context_helpers
from src.iCCModules import imageCompositeConverterSemanticValidationLogging as semantic_validation_logging_helpers
from src.iCCModules import imageCompositeConverterSemanticValidationRuntime as semantic_validation_runtime_helpers
from src.iCCModules import imageCompositeConverterSemanticValidationFinalization as semantic_validation_finalization_helpers
from src.iCCModules import imageCompositeConverterSemanticMismatchReporting as semantic_mismatch_reporting_helpers
from src.iCCModules import imageCompositeConverterSemanticMismatchRuntime as semantic_mismatch_runtime_helpers
from src.iCCModules import imageCompositeConverterSemanticAuditRuntime as semantic_audit_runtime_helpers
from src.iCCModules import imageCompositeConverterSemanticAuditBootstrap as semantic_audit_bootstrap_helpers
from src.iCCModules import imageCompositeConverterSemanticIterationFinalization as semantic_iteration_finalization_helpers
from src.iCCModules import imageCompositeConverterSemanticPostValidation as semantic_post_validation_helpers
from src.iCCModules import imageCompositeConverterSemanticVisualOverride as semantic_visual_override_helpers
from src.iCCModules import imageCompositeConverterSemanticBadgeRuntime as semantic_badge_runtime_helpers
from src.iCCModules import imageCompositeConverterDualArrowRuntime as dual_arrow_runtime_helpers
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as non_composite_runtime_helpers
from src.iCCModules.imageCompositeConverterPerceptionReflection import Perception, Reflection

def detectRelevantRegions(img) -> list[dict[str, object]]:
    return detectRelevantRegionsImpl(img, cv2_module=cv2, np_module=np)

def annotateImageRegions(img, regions: list[dict[str, object]]):
    return annotateImageRegionsImpl(img, regions, cv2_module=cv2)

def analyzeRange(folder_path: str, output_root: str | None = None, start_ref: str = "", end_ref: str = "ZZZZZZ") -> str:
    return analyzeRangeImpl(
        folder_path=folder_path,
        output_root=output_root,
        start_ref=start_ref,
        end_ref=end_ref,
        default_output_root_fn=_defaultConvertedSymbolsRoot,
        in_requested_range_fn=_inRequestedRange,
        detect_regions_fn=detectRelevantRegions,
        annotate_regions_fn=annotateImageRegions,
        cv2_module=cv2,
        np_module=np,
    )

def _optionalDependencyBaseDir() -> Path:
    return _optional_dependency_base_dir()

def _vendoredSitePackagesDirs() -> list[Path]:
    return _vendored_site_packages_dirs()

def _clearPartialModuleImport(module_name: str) -> None:
    dependency_helpers.clear_partial_module_import(module_name)

def _describeOptionalDependencyError(module_name: str, exc: BaseException, attempted_paths: list[Path]) -> str:
    return _describe_optional_dependency_error(module_name, exc, attempted_paths)

def _loadOptionalModule(module_name: str):
    return _load_optional_module(module_name)

def _importWithVendoredFallback(module_name: str):
    return _import_with_vendored_fallback(module_name)

def _optional_dependency_base_dir() -> Path:
    return dependency_helpers.optional_dependency_base_dir()

def _vendored_site_packages_dirs() -> list[Path]:
    return dependency_helpers.vendored_site_packages_dirs(base_dir_fn=_optional_dependency_base_dir)

def _describe_optional_dependency_error(module_name: str, exc: BaseException, attempted_paths: list[Path]) -> str:
    return dependency_helpers.describe_optional_dependency_error(module_name, exc, attempted_paths)

def _load_optional_module(module_name: str):
    return dependency_helpers.load_optional_module(
        module_name,
        vendored_dirs_fn=_vendored_site_packages_dirs,
        import_module_fn=importlib.import_module,
    )

def _import_with_vendored_fallback(module_name: str):
    return dependency_helpers.import_with_vendored_fallback(
        module_name,
        vendored_dirs_fn=_vendored_site_packages_dirs,
        import_module_fn=importlib.import_module,
    )

def _clip(value, low, high):
    return color_utils_helpers.clipImpl(
        value,
        low,
        high,
        np_module=np,
        clip_scalar_fn=Action._clipScalar,
    )

def loadGrayscaleImage(path: Path) -> list[list[int]]:
    return image_loading_helpers.loadGrayscaleImageImpl(
        path,
        import_with_vendored_fallback_fn=_importWithVendoredFallback,
    )

def _createDiffImageWithoutCv2(input_path: str | Path, svg_content: str):
    return diffing_helpers.createDiffImageWithoutCv2Impl(
        input_path,
        svg_content,
        fitz_module=fitz,
    )

def _computeOtsuThreshold(grayscale: list[list[int]]) -> int:
    return thresholding_helpers.computeOtsuThresholdImpl(grayscale)

def _adaptiveThreshold(grayscale: list[list[int]], block_size: int = 15, c: int = 5) -> list[list[int]]:
    return thresholding_helpers.adaptiveThresholdImpl(grayscale, block_size=block_size, c=c)

def loadBinaryImageWithMode(path: Path, *, threshold: int = 220, mode: str = "global") -> list[list[int]]:
    return image_loading_helpers.loadBinaryImageWithModeImpl(
        path,
        threshold=threshold,
        mode=mode,
        load_grayscale_image_fn=loadGrayscaleImage,
        compute_otsu_threshold_fn=_computeOtsuThreshold,
        adaptive_threshold_fn=_adaptiveThreshold,
    )

def renderCandidateMask(candidate: Candidate, width: int, height: int) -> list[list[int]]:
    return element_search_optimization_helpers.renderCandidateMaskImpl(
        candidate,
        width,
        height,
    )

def _iou(a: list[list[int]], b: list[list[int]]) -> float:
    return mask_metrics_helpers.iouImpl(a, b)

def scoreCandidate(target: list[list[int]], candidate: Candidate) -> float:
    return element_search_optimization_helpers.scoreCandidateImpl(
        target,
        candidate,
        render_candidate_mask_fn=renderCandidateMask,
        iou_fn=mask_metrics_helpers.iouImpl,
    )

def score_candidate(target: list[list[int]], candidate: Candidate) -> float:
    """Snake-case compatibility wrapper for scoreCandidate."""
    return scoreCandidate(target, candidate)

def randomNeighbor(base: Candidate, scale: float, rng: random.Random) -> Candidate:
    return element_search_optimization_helpers.randomNeighborImpl(
        base,
        scale,
        rng,
        candidate_factory=Candidate,
    )

def optimizeElement(target: list[list[int]], init: Candidate, *, max_iter: int, plateau_limit: int, seed: int) -> tuple[Candidate, float]:
    return element_search_optimization_helpers.optimizeElementImpl(
        target,
        init,
        max_iter=max_iter,
        plateau_limit=plateau_limit,
        seed=seed,
        score_candidate_fn=scoreCandidate,
        random_neighbor_fn=randomNeighbor,
    )

def optimize_element(target: list[list[int]], init: Candidate, *, max_iter: int, plateau_limit: int, seed: int) -> tuple[Candidate, float]:
    """Snake-case compatibility wrapper for optimizeElement."""
    return optimizeElement(target, init, max_iter=max_iter, plateau_limit=plateau_limit, seed=seed)

def _grayToHex(v: float) -> str:
    return color_utils_helpers.grayToHexImpl(v)

def estimateStrokeStyle(grayscale: list[list[int]], element: Element, candidate: Candidate) -> tuple[str, str | None, float | None]:
    return element_decomposition_helpers.estimateStrokeStyleImpl(
        grayscale,
        element,
        candidate,
        gray_to_hex_fn=_grayToHex,
    )


def candidateToSvg(candidate: Candidate, gx: int, gy: int, fill_color: str, stroke_color: str | None = None, stroke_width: float | None = None) -> str:
    return element_decomposition_helpers.candidateToSvgImpl(
        candidate,
        gx,
        gy,
        fill_color,
        stroke_color,
        stroke_width,
    )


def decomposeCircleWithStem(grayscale: list[list[int]], element: Element, candidate: Candidate) -> list[str] | None:
    return element_decomposition_helpers.decomposeCircleWithStemImpl(
        grayscale,
        element,
        candidate,
        candidate_to_svg_fn=candidateToSvg,
        estimate_stroke_style_fn=estimateStrokeStyle,
    )

def _missingRequiredImageDependencies() -> list[str]:
    return dependency_helpers.missingRequiredImageDependenciesImpl(cv2_module=cv2, np_module=np)

def _bootstrapRequiredImageDependencies() -> list[str]:
    missing = _missingRequiredImageDependencies()
    def _load_cv2_module():
        import cv2 as _cv2

        return _cv2

    def _load_np_module():
        import numpy as _np

        return _np

    def _set_modules(*, cv2_module, np_module) -> None:
        global cv2, np
        if cv2_module is not None:
            cv2 = cv2_module
        if np_module is not None:
            np = np_module

    return dependency_helpers.bootstrapRequiredImageDependenciesImpl(
        missing=missing,
        sys_executable=sys.executable,
        run_fn=subprocess.run,
        print_fn=print,
        load_cv2_fn=_load_cv2_module,
        load_np_fn=_load_np_module,
        set_modules_fn=_set_modules,
    )

def rgbToHex(rgb: np.ndarray) -> str:
    return color_utils_helpers.rgbToHexImpl(rgb)

def getBaseNameFromFile(filename: str) -> str:
    return naming_helpers.getBaseNameFromFileImpl(filename)

def _loadDescriptionMapping(path: str) -> dict[str, str]:
    return description_mapping_helpers.loadDescriptionMappingImpl(
        path,
        get_base_name_from_file_fn=getBaseNameFromFile,
    )

def _loadDescriptionMappingFromCsv(path: str) -> dict[str, str]:
    return description_mapping_helpers.loadDescriptionMappingFromCsvImpl(path)

def _loadDescriptionMappingFromXml(path: str) -> dict[str, str]:
    return description_mapping_helpers.loadDescriptionMappingFromXmlImpl(
        path,
        get_base_name_from_file_fn=getBaseNameFromFile,
    )

def _resolveDescriptionXmlPath(path: str) -> str | None:
    return description_mapping_helpers.resolveDescriptionXmlPathImpl(path)

def _requiredVendorPackages() -> list[str]:
    return vendor_install_helpers.requiredVendorPackagesImpl()

def buildLinuxVendorInstallCommand(
    vendor_dir: str = "vendor",
    platform_tag: str = "manylinux2014_x86_64",
    python_version: str | None = None,
) -> list[str]:
    return vendor_install_helpers.buildLinuxVendorInstallCommandImpl(
        vendor_dir=vendor_dir,
        platform_tag=platform_tag,
        python_version=python_version,
    )

def _renderSvgToNumpyInprocess(svg_string: str, size_w: int, size_h: int):
    return rendering_helpers.render_svg_to_numpy_inprocess(
        svg_string,
        size_w,
        size_h,
        fitz_module=fitz,
        np_module=np,
        cv2_module=cv2,
    )

def _renderSvgToNumpyViaSubprocess(svg_string: str, size_w: int, size_h: int):
    return rendering_helpers.render_svg_to_numpy_via_subprocess(
        svg_string,
        size_w,
        size_h,
        np_module=np,
        timeout_sec=SVG_RENDER_SUBPROCESS_TIMEOUT_SEC,
    )

def _render_svg_to_numpy_inprocess(svg_string: str, size_w: int, size_h: int):
    """Snake-case compatibility wrapper for tests and helper call sites."""
    return _renderSvgToNumpyInprocess(svg_string, size_w, size_h)

def _render_svg_to_numpy_via_subprocess(svg_string: str, size_w: int, size_h: int):
    """Snake-case compatibility wrapper for tests and helper call sites."""
    return _renderSvgToNumpyViaSubprocess(svg_string, size_w, size_h)

def _is_fitz_open_monkeypatched() -> bool:
    return rendering_runtime_helpers.is_fitz_open_monkeypatched(fitz_module=fitz)

def _is_inprocess_renderer_monkeypatched() -> bool:
    return rendering_runtime_helpers.is_inprocess_renderer_monkeypatched(
        inprocess_fn=globals().get("_renderSvgToNumpyInprocess"),
        module_name=__name__,
    )

def _bbox_to_dict(label: str, bbox: tuple[int, int, int, int], color: tuple[int, int, int]) -> dict[str, object]:
    """Snake-case compatibility helper kept for legacy tests and imports."""
    return rendering_runtime_helpers.bbox_to_dict(label, bbox, color)

def _runSvgRenderSubprocessEntrypoint() -> int:
    status_code, response = rendering_runtime_helpers.run_svg_render_subprocess_entrypoint(
        stdin_bytes=sys.stdin.buffer.read(),
        render_svg_to_numpy_inprocess=_renderSvgToNumpyInprocess,
    )
    if response:
        sys.stdout.write(response)
    return status_code

def _semanticQualityFlags(base_name: str, validation_logs: list[str]) -> list[str]:
    """Derive non-fatal quality markers from semantic element-validation logs.

    Semantic structure checks can pass even when one fitted element is still a
    visually weak match. We keep the conversion successful, but annotate such
    cases in the per-image validation log so downstream review can spot them.
    """

    return quality_helpers.semanticQualityFlagsImpl(
        base_name=base_name,
        validation_logs=validation_logs,
        get_base_name_fn=getBaseNameFromFile,
    )


def _looksLikeElongatedForegroundRect(img, *, white_threshold: int = 245) -> bool:
    return perception_geometry_helpers.looksLikeElongatedForegroundRectImpl(
        img,
        np_module=np,
        white_threshold=white_threshold,
    )

def runIterationPipeline(
    img_path: str,
    csv_path: str,
    max_iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str | None = None,
    debug_ac0811_dir: str | None = None,
    debug_element_diff_dir: str | None = None,
    badge_validation_rounds: int = 6,
):
    dependency_helpers.ensureConversionRuntimeDependenciesImpl(
        cv2_module=cv2,
        np_module=np,
        fitz_module=fitz,
    )

    run_locals = iteration_run_preparation_helpers.prepareRunIterationPipelineLocalsForRunImpl(
        **iteration_run_preparation_helpers.buildPrepareRunIterationPipelineLocalsForRunCallKwargsImpl(
            img_path=img_path,
            csv_path=csv_path,
            reports_out_dir=reports_out_dir,
            svg_out_dir=svg_out_dir,
            diff_out_dir=diff_out_dir,
            run_seed=int(Action.STOCHASTIC_RUN_SEED),
            pass_seed_offset=int(Action.STOCHASTIC_SEED_OFFSET),
            action_cls=Action,
            perception_cls=Perception,
            reflection_cls=Reflection,
            get_base_name_from_file_fn=getBaseNameFromFile,
            semantic_audit_record_fn=_semanticAuditRecord,
            semantic_quality_flags_fn=_semanticQualityFlags,
            looks_like_elongated_foreground_rect_fn=_looksLikeElongatedForegroundRect,
            render_embedded_raster_svg_fn=_renderEmbeddedRasterSvg,
            np_module=np,
            cv2_module=cv2,
            print_fn=print,
            time_ns_fn=time.time_ns,
            iteration_run_preparation_helpers=iteration_run_preparation_helpers,
            iteration_bindings_helpers=iteration_bindings_helpers,
            iteration_initialization_helpers=iteration_initialization_helpers,
            iteration_setup_helpers=iteration_setup_helpers,
            iteration_runtime_helpers=iteration_runtime_helpers,
            iteration_mode_runtime_preparation_helpers=iteration_mode_runtime_preparation_helpers,
            iteration_mode_setup_helpers=iteration_mode_setup_helpers,
            iteration_mode_preparation_helpers=iteration_mode_preparation_helpers,
            iteration_mode_dependency_setup_helpers=iteration_mode_dependency_setup_helpers,
            iteration_mode_dependency_helpers=iteration_mode_dependency_helpers,
            iteration_mode_runtime_helpers=iteration_mode_runtime_helpers,
            iteration_orchestration_helpers=iteration_orchestration_helpers,
            iteration_context_helpers=iteration_context_helpers,
            iteration_preparation_helpers=iteration_preparation_helpers,
            gradient_stripe_strategy_helpers=gradient_stripe_strategy_helpers,
            semantic_audit_bootstrap_helpers=semantic_audit_bootstrap_helpers,
            semantic_audit_logging_helpers=semantic_audit_logging_helpers,
            semantic_audit_runtime_helpers=semantic_audit_runtime_helpers,
            semantic_mismatch_reporting_helpers=semantic_mismatch_reporting_helpers,
            semantic_validation_logging_helpers=semantic_validation_logging_helpers,
            semantic_mismatch_runtime_helpers=semantic_mismatch_runtime_helpers,
            semantic_validation_context_helpers=semantic_validation_context_helpers,
            semantic_validation_runtime_helpers=semantic_validation_runtime_helpers,
            semantic_post_validation_helpers=semantic_post_validation_helpers,
            semantic_validation_finalization_helpers=semantic_validation_finalization_helpers,
            semantic_iteration_finalization_helpers=semantic_iteration_finalization_helpers,
            semantic_ac0223_runtime_helpers=semantic_ac0223_runtime_helpers,
            semantic_visual_override_helpers=semantic_visual_override_helpers,
            non_composite_runtime_helpers=non_composite_runtime_helpers,
            conversion_composite_helpers=conversion_composite_helpers,
            semantic_badge_runtime_helpers=semantic_badge_runtime_helpers,
            dual_arrow_badge_helpers=dual_arrow_badge_helpers,
            dual_arrow_runtime_helpers=dual_arrow_runtime_helpers,
        )
    )
    return iteration_execution_context_helpers.runIterationPipelineForRunImpl(
        **iteration_execution_context_helpers.buildRunIterationPipelineForRunCallKwargsImpl(
            run_locals=run_locals,
            img_path=img_path,
            max_iterations=max_iterations,
            badge_validation_rounds=badge_validation_rounds,
            debug_element_diff_dir=debug_element_diff_dir,
            debug_ac0811_dir=debug_ac0811_dir,
            calculate_error_fn=Action.calculate_error,
            print_fn=print,
            build_prepared_mode_builder_kwargs_fn=iteration_execution_helpers.buildPreparedModeBuilderKwargsImpl,
            run_prepared_iteration_and_finalize_fn=iteration_execution_helpers.runPreparedIterationAndFinalizeImpl,
            build_prepared_iteration_mode_kwargs_fn=iteration_context_helpers.buildPreparedIterationModeKwargsImpl,
            run_prepared_iteration_mode_fn=iteration_dispatch_helpers.runPreparedIterationModeImpl,
            finalize_iteration_result_fn=iteration_finalization_helpers.finalizeIterationResultImpl,
            math_module=math,
        )
    )

def _extractRefParts(name: str) -> tuple[str, int] | None:
    return range_helpers.extractRefPartsImpl(name)

def _normalizeRangeToken(value: str) -> str:
    return range_helpers.normalizeRangeTokenImpl(value, get_base_name_fn=getBaseNameFromFile)

def _normalizeExplicitRangeToken(value: str) -> str:
    return range_helpers.normalizeExplicitRangeTokenImpl(value)

def _isExplicitSizeVariantToken(token: str) -> bool:
    return range_helpers.isExplicitSizeVariantTokenImpl(token)

def _compactRangeToken(value: str) -> str:
    return range_helpers.compactRangeTokenImpl(value, normalize_range_token_fn=_normalizeRangeToken)

def _sharedPartialRangeToken(start_ref: str, end_ref: str) -> str:
    return range_helpers.sharedPartialRangeTokenImpl(
        start_ref,
        end_ref,
        normalize_range_token_fn=_normalizeRangeToken,
        compact_range_token_fn=_compactRangeToken,
    )

def _matchesPartialRangeToken(filename: str, start_ref: str, end_ref: str) -> bool:
    return range_helpers.matchesPartialRangeTokenImpl(
        filename,
        start_ref,
        end_ref,
        shared_partial_range_token_fn=_sharedPartialRangeToken,
        normalize_range_token_fn=_normalizeRangeToken,
        get_base_name_fn=getBaseNameFromFile,
    )

def _extractSymbolFamily(name: str) -> str | None:
    return range_helpers.extractSymbolFamilyImpl(name)

def _matchesExactPrefixFilter(filename: str, start_ref: str, end_ref: str) -> bool:
    return range_helpers.matchesExactPrefixFilterImpl(
        filename,
        start_ref,
        end_ref,
        normalize_range_token_fn=_normalizeRangeToken,
        normalize_explicit_range_token_fn=_normalizeExplicitRangeToken,
        is_explicit_size_variant_token_fn=_isExplicitSizeVariantToken,
        get_base_name_fn=getBaseNameFromFile,
    )

def _inRequestedRange(filename: str, start_ref: str, end_ref: str) -> bool:
    return range_helpers.inRequestedRangeImpl(
        filename,
        start_ref,
        end_ref,
        get_base_name_fn=getBaseNameFromFile,
        extract_ref_parts_fn=_extractRefParts,
        normalize_explicit_range_token_fn=_normalizeExplicitRangeToken,
        normalize_range_token_fn=_normalizeRangeToken,
        matches_exact_prefix_filter_fn=_matchesExactPrefixFilter,
        is_explicit_size_variant_token_fn=_isExplicitSizeVariantToken,
        matches_partial_range_token_fn=_matchesPartialRangeToken,
    )

def _conversionRandom() -> random.Random:
    return random_helpers.conversionRandomImpl(seed_env_var="TINY_ICC_RANDOM_SEED")

def _writeIterationLogAndCollectSemanticResults(
    files: list[str],
    result_map: dict[str, dict[str, object]],
    log_path: str,
) -> list[dict[str, object]]:
    return iteration_log_helpers.writeIterationLogAndCollectSemanticImpl(
        files=files,
        result_map=result_map,
        log_path=log_path,
    )

def _runPostConversionReporting(
    *,
    folder_path: str,
    csv_path: str,
    iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str,
    normalized_selected_variants: set[str],
    result_map: dict[str, dict[str, object]],
) -> dict[str, str]:
    return conversion_reporting_helpers.runPostConversionReportingImpl(
        folder_path=folder_path,
        csv_path=csv_path,
        iterations=iterations,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        reports_out_dir=reports_out_dir,
        normalized_selected_variants=normalized_selected_variants,
        result_map=result_map,
        write_semantic_audit_report_fn=_writeSemanticAuditReport,
        write_pixel_delta2_ranking_fn=_writePixelDelta2Ranking,
        write_ac08_weak_family_status_report_fn=_writeAc08WeakFamilyStatusReport,
        write_ac08_regression_manifest_fn=_writeAc08RegressionManifest,
        write_ac08_success_criteria_report_fn=_writeAc08SuccessCriteriaReport,
        emit_ac08_success_gate_status_fn=_emitAc08SuccessGateStatus,
        successful_conversions_manifest=SUCCESSFUL_CONVERSIONS_MANIFEST,
        update_successful_conversions_manifest_fn=updateSuccessfulConversionsManifestWithMetrics,
        generate_conversion_overviews_fn=generateConversionOverviews,
        print_fn=print,
    )

def _defaultConvertedSymbolsRoot() -> str:
    return output_path_helpers.defaultConvertedSymbolsRootImpl(module_file=__file__)

def _convertedSvgOutputDir(output_root: str) -> str:
    return output_path_helpers.convertedSvgOutputDirImpl(output_root)

def _readValidationLogDetails(log_path: str) -> dict[str, str]:
    return batch_reporting_helpers.readValidationLogDetailsImpl(log_path)

def _writeBatchFailureSummary(reports_out_dir: str, failures: list[dict[str, str]]) -> None:
    return batch_reporting_helpers.writeBatchFailureSummaryImpl(reports_out_dir, failures)

def _writeStrategySwitchTemplateTransfersReport(
    reports_out_dir: str,
    strategy_rows: list[dict[str, object]],
) -> None:
    return batch_reporting_helpers.writeStrategySwitchTemplateTransfersImpl(reports_out_dir, strategy_rows)

def _collectDescriptionFragments(raw_desc: dict[str, str], base_name: str, img_filename: str) -> list[dict[str, str]]:
    return audit_helpers.collectDescriptionFragmentsImpl(
        raw_desc,
        base_name=base_name,
        img_filename=img_filename,
        get_base_name_fn=getBaseNameFromFile,
    )

def _semanticAuditRecord(
    *,
    base_name: str,
    filename: str,
    description_fragments: list[dict[str, str]],
    semantic_elements: list[str],
    status: str,
    mismatch_reasons: list[str] | None = None,
    semantic_priority_order: list[str] | None = None,
    semantic_conflicts: list[str] | None = None,
    semantic_sources: dict[str, object] | None = None,
) -> dict[str, object]:
    return audit_helpers.semanticAuditRecordImpl(
        base_name=base_name,
        filename=filename,
        description_fragments=description_fragments,
        semantic_elements=semantic_elements,
        status=status,
        mismatch_reasons=mismatch_reasons,
        semantic_priority_order=semantic_priority_order,
        semantic_conflicts=semantic_conflicts,
        semantic_sources=semantic_sources,
        get_base_name_fn=getBaseNameFromFile,
    )

def _writeSemanticAuditReport(reports_out_dir: str, audit_rows: list[dict[str, object]]) -> None:
    return audit_helpers.writeSemanticAuditReportImpl(reports_out_dir, audit_rows)

def _diffOutputDir(output_root: str) -> str:
    return output_path_helpers.diffOutputDirImpl(output_root)

def _reportsOutputDir(output_root: str) -> str:
    return output_path_helpers.reportsOutputDirImpl(output_root)

def _isSemanticTemplateVariant(base_name: str, params: dict[str, object] | None = None) -> bool:
    return audit_helpers.isSemanticTemplateVariantImpl(
        base_name=base_name,
        params=params,
        get_base_name_fn=getBaseNameFromFile,
    )

def _loadExistingConversionRows(output_root: str, folder_path: str) -> list[dict[str, object]]:
    """Load previously converted variants so they can act as donor templates.

    This lets an earlier conversion batch (for example the already converted
    ``AC08*`` symbols) improve later runs without requiring a fresh full pass.
    """
    return conversion_row_helpers.loadExistingConversionRowsImpl(
        output_root=output_root,
        folder_path=folder_path,
        reports_output_dir_fn=_reportsOutputDir,
        converted_svg_output_dir_fn=_convertedSvgOutputDir,
        read_svg_geometry_fn=_readSvgGeometry,
        get_base_name_fn=getBaseNameFromFile,
        is_semantic_template_variant_fn=_isSemanticTemplateVariant,
        sniff_raster_size_fn=_sniffRasterSize,
    )

def _sniffRasterSize(path: str | Path) -> tuple[int, int]:
    return conversion_row_helpers.sniffRasterSizeImpl(path)

def _svgHrefMimeType(path: str | Path) -> str:
    return quality_config_helpers.svgHrefMimeTypeImpl(path)

def _renderEmbeddedRasterSvg(input_path: str | Path) -> str:
    return quality_config_helpers.renderEmbeddedRasterSvgImpl(
        input_path,
        sniff_raster_size_fn=_sniffRasterSize,
    )

def _qualityConfigPath(reports_out_dir: str) -> str:
    return quality_config_helpers.qualityConfigPathImpl(reports_out_dir)

def _loadQualityConfig(reports_out_dir: str) -> dict[str, object]:
    return quality_config_helpers.loadQualityConfigImpl(
        reports_out_dir,
        quality_config_path_fn=_qualityConfigPath,
    )

def _writeQualityConfig(
    reports_out_dir: str,
    *,
    allowed_error_per_pixel: float,
    skipped_variants: list[str],
    source: str,
) -> None:
    quality_config_helpers.writeQualityConfigImpl(
        reports_out_dir,
        allowed_error_per_pixel=allowed_error_per_pixel,
        skipped_variants=skipped_variants,
        source=source,
        quality_config_path_fn=_qualityConfigPath,
    )

def _resolveAllowedErrorPerPixel(
    current_rows: list[dict[str, object]],
    cfg: dict[str, object],
) -> tuple[float, str, float, float]:
    return quality_threshold_helpers.resolveAllowedErrorPerPixelImpl(
        current_rows,
        cfg,
        quality_sort_key_fn=_qualitySortKey,
        successful_threshold_fn=_computeSuccessfulConversionsErrorThreshold,
    )

def _qualitySortKey(row: dict[str, object]) -> float:
    return optimization_pass_helpers.qualitySortKeyImpl(row)

def _computeSuccessfulConversionsErrorThreshold(
    rows: list[dict[str, object]],
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> float:
    """Return mean(error_per_pixel) + 2*std(error_per_pixel) for successful rows.

    The successful set is sourced from ``successful_conversions.txt`` (via
    ``SUCCESSFUL_CONVERSIONS``) unless explicitly provided. Returns ``inf`` when
    no finite samples are available.
    """
    return optimization_pass_helpers.computeSuccessfulConversionsErrorThresholdImpl(
        rows,
        successful_variants=successful_variants or SUCCESSFUL_CONVERSIONS,
    )

def _selectMiddleLowerTercile(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return optimization_pass_helpers.selectMiddleLowerTercileImpl(rows)

def _selectOpenQualityCases(
    rows: list[dict[str, object]],
    *,
    allowed_error_per_pixel: float,
    skip_variants: set[str] | None = None,
) -> list[dict[str, object]]:
    """Return unresolved quality cases sorted from worst to best.

    "Open" means the case is finite, not explicitly skipped, and still above the
    accepted quality threshold.
    """
    return optimization_pass_helpers.selectOpenQualityCasesImpl(
        rows,
        allowed_error_per_pixel=allowed_error_per_pixel,
        skip_variants=skip_variants,
    )

def _iterationStrategyForPass(pass_idx: int, base_iterations: int) -> tuple[int, int]:
    return optimization_pass_helpers.iterationStrategyForPassImpl(pass_idx, base_iterations)

def _adaptiveIterationBudgetForQualityRow(row: dict[str, object], planned_budget: int) -> int:
    return optimization_pass_helpers.adaptiveIterationBudgetForQualityRowImpl(row, planned_budget)

def _writeQualityPassReport(
    reports_out_dir: str,
    pass_rows: list[dict[str, object]],
) -> None:
    return optimization_pass_reporting_helpers.writeQualityPassReportImpl(reports_out_dir, pass_rows)

def _evaluateQualityPassCandidate(
    old_row: dict[str, object],
    new_row: dict[str, object],
) -> tuple[bool, str, float, float, float, float]:
    """Return whether a quality-pass candidate should replace the previous result.

    The acceptance rule mirrors AC08 task 1.1: keep the new candidate only when
    at least one core quality metric improves (`error_per_pixel` or
    `mean_delta2`). The caller also receives the normalized metrics so reporting
    can use one consistent decision path for stochastic re-runs and fallback
    template transfers.
    """

    return optimization_pass_reporting_helpers.evaluateQualityPassCandidateImpl(old_row, new_row)

def _extractSvgInner(svg_text: str) -> str:
    return template_transfer_helpers.extractSvgInnerImpl(svg_text)

def _buildTransformedSvgFromTemplate(
    template_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
    scale: float,
) -> str:
    return template_transfer_helpers.buildTransformedSvgFromTemplateImpl(
        template_svg_text,
        target_w,
        target_h,
        rotation_deg=rotation_deg,
        scale=scale,
        extract_svg_inner_fn=_extractSvgInner,
    )

def _templateTransferScaleCandidates(base_scale: float) -> list[float]:
    return template_transfer_helpers.templateTransferScaleCandidatesImpl(base_scale)

def _estimateTemplateTransferScale(
    img_orig: np.ndarray,
    donor_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
) -> float | None:
    return template_transfer_helpers.estimateTemplateTransferScaleImpl(
        img_orig,
        donor_svg_text,
        target_w,
        target_h,
        rotation_deg=rotation_deg,
        render_svg_to_numpy_fn=Action.renderSvgToNumpy,
        build_transformed_svg_from_template_fn=_buildTransformedSvgFromTemplate,
        foreground_mask_fn=Action._foregroundMask,
        mask_bbox_fn=Action._maskBbox,
    )

def _templateTransferTransformCandidates(
    target_variant: str,
    donor_variant: str,
    *,
    estimated_scale_by_rotation: dict[int, float] | None = None,
) -> list[tuple[int, float]]:
    return template_transfer_helpers.templateTransferTransformCandidatesImpl(
        target_variant,
        donor_variant,
        estimated_scale_by_rotation=estimated_scale_by_rotation,
        template_transfer_scale_candidates_fn=_templateTransferScaleCandidates,
    )

def _rankTemplateTransferDonors(
    target_row: dict[str, object],
    donor_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return template_transfer_helpers.rankTemplateTransferDonorsImpl(
        target_row,
        donor_rows,
        normalized_geometry_signature_fn=_normalizedGeometrySignature,
        max_signature_delta_fn=_maxSignatureDelta,
    )

def _templateTransferDonorFamilyCompatible(
    target_base: str,
    donor_base: str,
    *,
    documented_alias_refs: set[str] | None = None,
) -> bool:
    return template_transfer_helpers.templateTransferDonorFamilyCompatibleImpl(
        target_base,
        donor_base,
        documented_alias_refs=documented_alias_refs,
        extract_symbol_family_fn=_extractSymbolFamily,
    )

def _semanticTransferRotations(target_params: dict[str, object], donor_params: dict[str, object]) -> tuple[int, ...]:
    return transfer_helpers.semanticTransferRotationsImpl(target_params, donor_params)

def _semanticTransferIsCompatible(target_params: dict[str, object], donor_params: dict[str, object]) -> bool:
    return transfer_helpers.semanticTransferIsCompatibleImpl(
        target_params,
        donor_params,
        connector_arm_direction_fn=_connectorArmDirection,
        connector_stem_direction_fn=_connectorStemDirection,
    )

def _connectorArmDirection(params: dict[str, object]) -> int | None:
    return transfer_helpers.connectorArmDirectionImpl(params)

def _connectorStemDirection(params: dict[str, object]) -> int | None:
    return transfer_helpers.connectorStemDirectionImpl(params)

def _semanticTransferScaleCandidates(base_scale: float) -> list[float]:
    return transfer_helpers.semanticTransferScaleCandidatesImpl(
        base_scale,
        template_transfer_scale_candidates_fn=_templateTransferScaleCandidates,
    )

def _semanticTransferBadgeParams(
    donor_params: dict[str, object],
    target_params: dict[str, object],
    *,
    target_w: int,
    target_h: int,
    rotation_deg: int,
    scale: float,
) -> dict[str, object]:
    return transfer_helpers.semanticTransferBadgeParamsImpl(
        donor_params,
        target_params,
        target_w=target_w,
        target_h=target_h,
        rotation_deg=rotation_deg,
        scale=scale,
        light_circle_fill_gray=Action.LIGHT_CIRCLE_FILL_GRAY,
        light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
        light_circle_text_gray=Action.LIGHT_CIRCLE_TEXT_GRAY,
        clip_scalar_fn=Action._clipScalar,
        finalize_ac08_style_fn=Action._finalizeAc08Style,
    )

def _tryTemplateTransfer(
    *,
    target_row: dict[str, object],
    donor_rows: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    diff_out_dir: str,
    rng: random.Random | None = None,
    deterministic_order: bool = False,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    return template_transfer_helpers.tryTemplateTransferImpl(
        target_row=target_row,
        donor_rows=donor_rows,
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        rng=rng,
        deterministic_order=deterministic_order,
        cv2_module=cv2,
        read_svg_geometry_fn=_readSvgGeometry,
        rank_template_transfer_donors_fn=_rankTemplateTransferDonors,
        template_transfer_donor_family_compatible_fn=_templateTransferDonorFamilyCompatible,
        semantic_transfer_is_compatible_fn=_semanticTransferIsCompatible,
        semantic_transfer_scale_candidates_fn=_semanticTransferScaleCandidates,
        semantic_transfer_rotations_fn=_semanticTransferRotations,
        semantic_transfer_badge_params_fn=_semanticTransferBadgeParams,
        estimate_template_transfer_scale_fn=_estimateTemplateTransferScale,
        template_transfer_transform_candidates_fn=_templateTransferTransformCandidates,
        build_transformed_svg_from_template_fn=_buildTransformedSvgFromTemplate,
        render_svg_to_numpy_fn=Action.renderSvgToNumpy,
        calculate_error_fn=Action.calculateError,
        create_diff_image_fn=Action.createDiffImage,
        calculate_delta2_stats_fn=Action.calculateDelta2Stats,
        generate_badge_svg_fn=Action.generateBadgeSvg,
    )

def _runEmbeddedRasterFallback(
    *,
    files: list[str],
    folder_path: str,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str,
) -> None:
    fallback_helpers.runEmbeddedRasterFallbackImpl(
        files=files,
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        reports_out_dir=reports_out_dir,
        render_embedded_raster_svg_fn=_renderEmbeddedRasterSvg,
        create_diff_image_without_cv2_fn=_createDiffImageWithoutCv2,
        generate_conversion_overviews_fn=generateConversionOverviews,
        fitz_module=fitz,
    )

def _listRequestedImageFiles(
    folder_path: str,
    start_ref: str,
    end_ref: str,
    *,
    selected_variants: set[str] | None,
) -> tuple[set[str], list[str]]:
    return conversion_input_helpers.listRequestedImageFilesImpl(
        folder_path=folder_path,
        start_ref=start_ref,
        end_ref=end_ref,
        selected_variants=selected_variants,
        in_requested_range_fn=_inRequestedRange,
    )

def convertRange(
    folder_path: str,
    csv_path: str,
    iterations: int,
    start_ref: str = "AR0102",
    end_ref: str = "AR0104",
    debug_ac0811_dir: str | None = None,
    debug_element_diff_dir: str | None = None,
    output_root: str | None = None,
    selected_variants: set[str] | None = None,
    deterministic_order: bool = False,
) -> str:
    out_root = output_root or _defaultConvertedSymbolsRoot()
    svg_out_dir = _convertedSvgOutputDir(out_root)
    diff_out_dir = _diffOutputDir(out_root)
    reports_out_dir = _reportsOutputDir(out_root)

    os.makedirs(svg_out_dir, exist_ok=True)
    os.makedirs(diff_out_dir, exist_ok=True)
    os.makedirs(reports_out_dir, exist_ok=True)

    normalized_selected_variants, files = _listRequestedImageFiles(
        folder_path,
        start_ref,
        end_ref,
        selected_variants=selected_variants,
    )
    if not files:
        summary_text = conversion_input_helpers.inputSelectionSummaryImpl(
            folder_path=folder_path,
            start_ref=start_ref,
            end_ref=end_ref,
            selected_variants=normalized_selected_variants,
            matched_files=files,
        )
        (Path(reports_out_dir) / "input_selection_summary.txt").write_text(summary_text, encoding="utf-8")
        print(summary_text.rstrip())
    if cv2 is None or np is None:
        _runEmbeddedRasterFallback(
            files=files,
            folder_path=folder_path,
            svg_out_dir=svg_out_dir,
            diff_out_dir=diff_out_dir,
            reports_out_dir=reports_out_dir,
        )
        return out_root
    rng = _conversionRandom()
    run_seed = 0 if deterministic_order else rng.randrange(1 << 30)
    Action.STOCHASTIC_RUN_SEED = int(run_seed)
    process_files = list(files)
    if not deterministic_order:
        rng.shuffle(process_files)

    base_iterations = max(1, int(iterations))
    # Continue quality iterations while a pass still improves at least one case.
    # Abort as soon as the next pass cannot beat the previous state.
    # Single-reference diagnostics should finish quickly, therefore we skip
    # extra quality passes when only one variant or one exact reference is
    # requested.
    normalized_start_ref = str(start_ref or "").strip().upper()
    normalized_end_ref = str(end_ref or "").strip().upper()
    is_single_reference_run = bool(normalized_start_ref) and normalized_start_ref == normalized_end_ref
    max_quality_passes = 0 if (len(process_files) <= 1 or is_single_reference_run) else 4
    quality_logs: list[dict[str, object]] = []
    result_map: dict[str, dict[str, object]] = {}
    conversion_bestlist_path = _conversionBestlistManifestPath(reports_out_dir)
    conversion_bestlist_rows = _readConversionBestlistMetrics(conversion_bestlist_path, svg_out_dir)
    batch_failures: list[dict[str, str]] = []
    stop_after_failure = False
    existing_donor_rows = _loadExistingConversionRows(out_root, folder_path)

    def _convertOne(filename: str, iteration_budget: int, badge_rounds: int) -> tuple[dict[str, object] | None, bool]:
        return conversion_execution_helpers.convertOneImpl(
            filename=filename,
            folder_path=folder_path,
            csv_path=csv_path,
            iteration_budget=iteration_budget,
            badge_rounds=badge_rounds,
            svg_out_dir=svg_out_dir,
            diff_out_dir=diff_out_dir,
            reports_out_dir=reports_out_dir,
            debug_ac0811_dir=debug_ac0811_dir,
            debug_element_diff_dir=debug_element_diff_dir,
            run_iteration_pipeline_fn=runIterationPipeline,
            read_validation_log_details_fn=_readValidationLogDetails,
            render_svg_to_numpy_fn=Action.renderSvgToNumpy,
            calculate_delta2_stats_fn=Action.calculateDelta2Stats,
            get_base_name_from_file_fn=getBaseNameFromFile,
            cv2_module=cv2,
            render_embedded_raster_svg_fn=_renderEmbeddedRasterSvg,
            append_batch_failure_fn=batch_failures.append,
            print_fn=print,
        )

    # Initial conversion pass for all forms.
    stop_after_failure = conversion_initial_pass_helpers.runInitialConversionPassImpl(
        process_files=process_files,
        result_map=result_map,
        existing_donor_rows=existing_donor_rows,
        conversion_bestlist_rows=conversion_bestlist_rows,
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        rng=rng,
        deterministic_order=deterministic_order,
        base_iterations=base_iterations,
        convert_one_fn=_convertOne,
        try_template_transfer_fn=_tryTemplateTransfer,
        is_conversion_bestlist_candidate_better_fn=_isConversionBestlistCandidateBetter,
        store_conversion_bestlist_snapshot_fn=lambda variant, row: _storeConversionBestlistSnapshot(
            variant,
            row,
            svg_out_dir,
            reports_out_dir,
        ),
        restore_conversion_bestlist_snapshot_fn=lambda variant: _restoreConversionBestlistSnapshot(
            variant,
            svg_out_dir,
            reports_out_dir,
        ),
        choose_conversion_bestlist_row_fn=_chooseConversionBestlistRow,
    )

    current_rows = [
        row
        for row in result_map.values()
        if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
    ]
    cfg = _loadQualityConfig(reports_out_dir)
    allowed_error_pp, threshold_source, _successful_threshold, _initial_threshold = _resolveAllowedErrorPerPixel(
        current_rows,
        cfg,
    )

    # Global policy: do not freeze individual variants. Every quality pass keeps
    # all variants eligible so each run can re-evaluate with stochastic search
    # while still converging by only accepting strict improvements.
    skip_variants: set[str] = set()

    _writeQualityConfig(
        reports_out_dir,
        allowed_error_per_pixel=allowed_error_pp,
        skipped_variants=sorted(v for v in skip_variants if v),
        source=threshold_source,
    )

    # Iteratively refine unresolved quality cases while preserving all already
    # successful outputs (replace only when strictly better).
    strategy_logs: list[dict[str, object]] = []
    if max_quality_passes > 0:
        stop_after_failure = conversion_quality_pass_helpers.runQualityPassesImpl(
            max_quality_passes=max_quality_passes,
            stop_after_failure=stop_after_failure,
            deterministic_order=deterministic_order,
            rng=rng,
            base_iterations=base_iterations,
            allowed_error_per_pixel=allowed_error_pp,
            skip_variants=skip_variants,
            result_map=result_map,
            quality_logs=quality_logs,
            conversion_bestlist_rows=conversion_bestlist_rows,
            convert_one_fn=_convertOne,
            select_open_quality_cases_fn=_selectOpenQualityCases,
            select_middle_lower_tercile_fn=_selectMiddleLowerTercile,
            iteration_strategy_for_pass_fn=_iterationStrategyForPass,
            adaptive_iteration_budget_for_quality_row_fn=_adaptiveIterationBudgetForQualityRow,
            evaluate_quality_pass_candidate_fn=_evaluateQualityPassCandidate,
            store_conversion_bestlist_snapshot_fn=lambda variant, row: _storeConversionBestlistSnapshot(
                variant,
                row,
                svg_out_dir,
                reports_out_dir,
            ),
            restore_conversion_bestlist_snapshot_fn=lambda variant: _restoreConversionBestlistSnapshot(
                variant,
                svg_out_dir,
                reports_out_dir,
            ),
            before_pass_fn=lambda pass_idx: setattr(Action, "STOCHASTIC_SEED_OFFSET", pass_idx),
        )

    conversion_finalization_helpers.runConversionFinalizationImpl(
        reports_out_dir=reports_out_dir,
        quality_logs=quality_logs,
        conversion_bestlist_path=conversion_bestlist_path,
        conversion_bestlist_rows=conversion_bestlist_rows,
        batch_failures=batch_failures,
        strategy_logs=strategy_logs,
        files=files,
        result_map=result_map,
        folder_path=folder_path,
        csv_path=csv_path,
        iterations=iterations,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        normalized_selected_variants=normalized_selected_variants,
        write_quality_pass_report_fn=_writeQualityPassReport,
        write_conversion_bestlist_metrics_fn=_writeConversionBestlistMetrics,
        write_batch_failure_summary_fn=_writeBatchFailureSummary,
        write_strategy_switch_template_transfers_report_fn=_writeStrategySwitchTemplateTransfersReport,
        write_iteration_log_and_collect_semantic_results_fn=_writeIterationLogAndCollectSemanticResults,
        harmonize_semantic_size_variants_fn=_harmonizeSemanticSizeVariants,
        run_post_conversion_reporting_fn=_runPostConversionReporting,
    )

    Action.STOCHASTIC_SEED_OFFSET = 0
    Action.STOCHASTIC_RUN_SEED = 0
    return out_root

def _readSvgGeometry(svg_path: str) -> tuple[int, int, dict] | None:
    return semantic_geometry_helpers.readSvgGeometryImpl(svg_path, action_t_path_d=Action.T_PATH_D)

def _normalizedGeometrySignature(w: int, h: int, params: dict) -> dict[str, float]:
    return semantic_geometry_helpers.normalizedGeometrySignatureImpl(w, h, params)

def _maxSignatureDelta(sig_a: dict[str, float], sig_b: dict[str, float]) -> float:
    return semantic_geometry_helpers.maxSignatureDeltaImpl(sig_a, sig_b)

def _needsLargeCircleOverflowGuard(params: dict) -> bool:
    return semantic_harmonization_helpers.needsLargeCircleOverflowGuardImpl(params)

def _scaleBadgeParams(
    anchor: dict,
    anchor_w: int,
    anchor_h: int,
    target_w: int,
    target_h: int,
    *,
    target_variant: str = "",
) -> dict:
    return semantic_harmonization_helpers.scaleBadgeParamsImpl(
        anchor,
        anchor_w,
        anchor_h,
        target_w,
        target_h,
        clip_scalar_fn=Action._clipScalar,
        needs_large_circle_overflow_guard_fn=_needsLargeCircleOverflowGuard,
    )

def _harmonizationAnchorPriority(suffix: str, prefer_large: bool) -> int:
    return semantic_harmonization_helpers.harmonizationAnchorPriorityImpl(suffix, prefer_large)

def _clipGray(value: float) -> int:
    return semantic_harmonization_helpers.clipGrayImpl(value)

def _captureCanonicalBadgeColors(params: dict) -> dict:
    return semantic_harmonization_helpers.captureCanonicalBadgeColorsImpl(
        params,
        light_circle_fill_gray=Action.LIGHT_CIRCLE_FILL_GRAY,
        light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
        light_circle_text_gray=Action.LIGHT_CIRCLE_TEXT_GRAY,
    )

def _applyCanonicalBadgeColors(params: dict) -> dict:
    return semantic_harmonization_helpers.applyCanonicalBadgeColorsImpl(params)

def _familyHarmonizedBadgeColors(variant_rows: list[dict[str, object]]) -> dict[str, int]:
    return semantic_harmonization_helpers.familyHarmonizedBadgeColorsImpl(variant_rows)

def _harmonizeSemanticSizeVariants(
    results: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
) -> None:
    semantic_harmonization_helpers.harmonizeSemanticSizeVariantsImpl(
        results=results,
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        read_svg_geometry_fn=_readSvgGeometry,
        normalized_geometry_signature_fn=_normalizedGeometrySignature,
        max_signature_delta_fn=_maxSignatureDelta,
        harmonization_anchor_priority_fn=_harmonizationAnchorPriority,
        family_harmonized_badge_colors_fn=_familyHarmonizedBadgeColors,
        scale_badge_params_fn=_scaleBadgeParams,
        generate_badge_svg_fn=Action.generateBadgeSvg,
        render_svg_to_numpy_fn=Action.renderSvgToNumpy,
        calculate_error_fn=Action.calculateError,
        cv2_module=cv2,
    )

def _writeAc08RegressionManifest(
    reports_out_dir: str,
    *,
    folder_path: str,
    csv_path: str,
    iterations: int,
    selected_variants: list[str],
) -> None:
    ac08_reporting_helpers.writeAc08RegressionManifestImpl(
        reports_out_dir,
        folder_path=folder_path,
        csv_path=csv_path,
        iterations=iterations,
        selected_variants=selected_variants,
        ac08_regression_variants=AC08_REGRESSION_VARIANTS,
        ac08_regression_cases=AC08_REGRESSION_CASES,
        ac08_regression_set_name=AC08_REGRESSION_SET_NAME,
    )

def _summarizePreviousGoodAc08Variants(reports_out_dir: str) -> dict[str, object]:
    return ac08_reporting_helpers.summarizePreviousGoodAc08VariantsImpl(
        reports_out_dir,
        previous_good_variants=AC08_PREVIOUSLY_GOOD_VARIANTS,
    )

def _writeAc08SuccessCriteriaReport(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
) -> dict[str, object] | None:
    return ac08_reporting_helpers.writeAc08SuccessCriteriaReportImpl(
        reports_out_dir,
        selected_variants=selected_variants,
        ac08_regression_variants=AC08_REGRESSION_VARIANTS,
        ac08_regression_set_name=AC08_REGRESSION_SET_NAME,
        summarize_previous_good_fn=_summarizePreviousGoodAc08Variants,
    )

def _emitAc08SuccessGateStatus(ac08_success_gate: dict[str, object] | None) -> None:
    ac08_gate_helpers.emitAc08SuccessGateStatusImpl(ac08_success_gate, print_fn=print)

def _writeAc08WeakFamilyStatusReport(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
    ranking_threshold: float = 18.0,
) -> None:
    ac08_reporting_helpers.writeAc08WeakFamilyStatusReportImpl(
        reports_out_dir,
        selected_variants=selected_variants,
        ac08_regression_cases=AC08_REGRESSION_CASES,
        ac08_mitigation_status=AC08_MITIGATION_STATUS,
        ranking_threshold=ranking_threshold,
    )

def _writePixelDelta2Ranking(folder_path: str, svg_out_dir: str, reports_out_dir: str, threshold: float = 18.0) -> None:
    ranking_helpers.writePixelDelta2RankingImpl(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        threshold=threshold,
        cv2_module=cv2,
        render_svg_to_numpy_fn=Action.render_svg_to_numpy,
        calculate_delta2_stats_fn=Action.calculateDelta2Stats,
    )

def _loadIterationLogRows(reports_out_dir: str) -> dict[str, dict[str, str]]:
    return successful_conversion_quality_helpers.loadIterationLogRowsImpl(reports_out_dir)

def _findImagePathByVariant(folder_path: str, variant: str) -> str | None:
    return successful_conversion_quality_helpers.findImagePathByVariantImpl(folder_path, variant)

def collectSuccessfulConversionQualityMetrics(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> list[dict[str, object]]:
    return successful_conversion_quality_helpers.collectSuccessfulConversionQualityMetricsImpl(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        successful_variants=successful_variants or SUCCESSFUL_CONVERSIONS,
        successful_conversions=SUCCESSFUL_CONVERSIONS,
        load_iteration_log_rows_fn=_loadIterationLogRows,
        find_image_path_by_variant_fn=_findImagePathByVariant,
        read_validation_log_details_fn=_readValidationLogDetails,
        render_svg_to_numpy_fn=Action.render_svg_to_numpy,
        cv2_module=cv2,
        np_module=np,
    )

def _successfulConversionMetricsAvailable(metrics: dict[str, object]) -> bool:
    return successful_conversions_helpers.successfulConversionMetricsAvailableImpl(metrics)

def _parseSuccessfulConversionManifestLine(raw_line: str) -> tuple[str, dict[str, object]]:
    return successful_conversions_helpers.parseSuccessfulConversionManifestLineImpl(raw_line)

def _readSuccessfulConversionManifestMetrics(manifest_path: Path) -> dict[str, dict[str, object]]:
    return successful_conversions_helpers.readSuccessfulConversionManifestMetricsImpl(
        manifest_path,
        parse_manifest_line_fn=_parseSuccessfulConversionManifestLine,
    )

def _successfulConversionSnapshotDir(reports_out_dir: str) -> Path:
    return successful_conversions_helpers.successfulConversionSnapshotDirImpl(reports_out_dir)

def _successfulConversionSnapshotPaths(reports_out_dir: str, variant: str) -> dict[str, Path]:
    return successful_conversions_helpers.successfulConversionSnapshotPathsImpl(
        reports_out_dir,
        variant,
        snapshot_dir_fn=_successfulConversionSnapshotDir,
    )

def _restoreSuccessfulConversionSnapshot(variant: str, svg_out_dir: str, reports_out_dir: str) -> bool:
    return successful_conversions_helpers.restoreSuccessfulConversionSnapshotImpl(
        variant=variant,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        snapshot_paths_fn=_successfulConversionSnapshotPaths,
    )

def _storeSuccessfulConversionSnapshot(variant: str, metrics: dict[str, object], svg_out_dir: str, reports_out_dir: str) -> None:
    return successful_conversions_helpers.storeSuccessfulConversionSnapshotImpl(
        variant=variant,
        metrics=metrics,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        snapshot_paths_fn=_successfulConversionSnapshotPaths,
    )

def _isSuccessfulConversionCandidateBetter(
    previous_metrics: dict[str, object] | None,
    candidate_metrics: dict[str, object],
) -> bool:
    return successful_conversions_helpers.isSuccessfulConversionCandidateBetterImpl(
        previous_metrics=previous_metrics,
        candidate_metrics=candidate_metrics,
        metrics_available_fn=_successfulConversionMetricsAvailable,
        evaluate_candidate_fn=_evaluateQualityPassCandidate,
    )

def _mergeSuccessfulConversionMetrics(
    baseline: dict[str, object],
    override: dict[str, object],
) -> dict[str, object]:
    return successful_conversions_helpers.mergeSuccessfulConversionMetricsImpl(baseline, override)

def _formatSuccessfulConversionManifestLine(existing_line: str, metrics: dict[str, object]) -> str:
    return successful_conversions_helpers.formatSuccessfulConversionManifestLineImpl(
        existing_line=existing_line,
        metrics=metrics,
        metrics_available_fn=_successfulConversionMetricsAvailable,
    )

def _conversionBestlistManifestPath(reports_out_dir: str) -> Path:
    return conversion_bestlist_helpers.conversionBestlistManifestPathImpl(reports_out_dir)

def _readConversionBestlistMetrics(manifest_path: Path, svg_out_dir: str) -> dict[str, dict[str, object]]:
    rows = conversion_bestlist_helpers.readConversionBestlistMetricsImpl(manifest_path)
    return conversion_bestlist_helpers.pruneConversionBestlistRowsWithoutSvgImpl(rows, svg_out_dir)

def _writeConversionBestlistMetrics(manifest_path: Path, rows: dict[str, dict[str, object]]) -> None:
    conversion_bestlist_helpers.writeConversionBestlistMetricsImpl(manifest_path, rows)

def _storeConversionBestlistSnapshot(variant: str, row: dict[str, object], svg_out_dir: str, reports_out_dir: str) -> None:
    conversion_bestlist_helpers.storeConversionBestlistSnapshotImpl(variant, row, svg_out_dir, reports_out_dir)

def _restoreConversionBestlistSnapshot(variant: str, svg_out_dir: str, reports_out_dir: str) -> dict[str, object] | None:
    return conversion_bestlist_helpers.restoreConversionBestlistSnapshotImpl(variant, svg_out_dir, reports_out_dir)

def _isConversionBestlistCandidateBetter(previous_row: dict[str, object] | None, candidate_row: dict[str, object]) -> bool:
    return conversion_bestlist_helpers.isConversionBestlistCandidateBetterImpl(
        previous_row,
        candidate_row,
        evaluate_candidate_fn=_evaluateQualityPassCandidate,
    )

def _chooseConversionBestlistRow(
    candidate_row: dict[str, object],
    previous_row: dict[str, object] | None,
    restored_row: dict[str, object] | None,
) -> dict[str, object]:
    return conversion_bestlist_helpers.chooseConversionBestlistRowImpl(
        candidate_row=candidate_row,
        previous_row=previous_row,
        restored_row=restored_row,
    )


def repairAc0223BestlistArtifacts(output_root: str) -> dict[str, object]:
    return conversion_bestlist_helpers.repairAc0223BestlistArtifactsImpl(output_root)

def _latestFailedConversionManifestEntry(reports_out_dir: str) -> dict[str, object] | None:
    return successful_conversions_helpers.latestFailedConversionManifestEntryImpl(reports_out_dir)

def updateSuccessfulConversionsManifestWithMetrics(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    manifest_path: Path | None = None,
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    return successful_conversions_helpers.updateSuccessfulConversionsManifestWithMetricsImpl(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        collect_quality_metrics_fn=collectSuccessfulConversionQualityMetrics,
        load_successful_conversions_fn=_loadSuccessfulConversions,
        read_manifest_metrics_fn=_readSuccessfulConversionManifestMetrics,
        is_candidate_better_fn=_isSuccessfulConversionCandidateBetter,
        store_snapshot_fn=_storeSuccessfulConversionSnapshot,
        merge_metrics_fn=_mergeSuccessfulConversionMetrics,
        restore_snapshot_fn=_restoreSuccessfulConversionSnapshot,
        format_manifest_line_fn=_formatSuccessfulConversionManifestLine,
        latest_failed_entry_fn=_latestFailedConversionManifestEntry,
        sorted_rows_fn=_sortedSuccessfulConversionMetricsRows,
        manifest_path=manifest_path,
        successful_variants=successful_variants,
    )

def _sortedSuccessfulConversionMetricsRows(
    metrics: list[dict[str, object]],
) -> list[dict[str, object]]:
    return successful_conversions_helpers.sortedSuccessfulConversionMetricsRowsImpl(metrics)

def _writeSuccessfulConversionCsvTable(csv_path: str | os.PathLike[str], metrics: list[dict[str, object]]) -> str:
    return successful_conversions_helpers.writeSuccessfulConversionCsvTableImpl(
        csv_path=csv_path,
        metrics=metrics,
        sorted_rows_fn=_sortedSuccessfulConversionMetricsRows,
    )

def writeSuccessfulConversionQualityReport(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...] | None = None,
    output_name: str = 'successful_conversion_quality',
) -> tuple[str, str, list[dict[str, object]]]:
    """Backward-compatible wrapper that now also refreshes the manifest."""
    return successful_conversion_report_helpers.writeSuccessfulConversionQualityReportImpl(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        update_manifest_fn=updateSuccessfulConversionsManifestWithMetrics,
        sort_rows_fn=_sortedSuccessfulConversionMetricsRows,
        write_csv_fn=_writeSuccessfulConversionCsvTable,
        successful_variants=successful_variants,
        output_name=output_name,
    )

def parseArgs(argv: list[str] | None = None) -> argparse.Namespace:
    return cli_helpers.parseArgsImpl(
        argv=argv,
        ac08_regression_set_name=AC08_REGRESSION_SET_NAME,
        ac08_regression_variants=AC08_REGRESSION_VARIANTS,
        svg_render_subprocess_timeout_sec=SVG_RENDER_SUBPROCESS_TIMEOUT_SEC,
    )

def _optionalLogCapture(log_path: str):
    with cli_helpers.optionalLogCaptureImpl(log_path):
        yield

def _autoDetectCsvPath(folder_path: str) -> str | None:
    return cli_helpers.autoDetectCsvPathImpl(folder_path)

def _resolveCliCsvAndOutput(args: argparse.Namespace) -> tuple[str, str | None]:
    return cli_helpers.resolveCliCsvAndOutputImpl(
        args,
        auto_detect_csv_path_fn=_autoDetectCsvPath,
        resolve_xml_path_fn=_resolveDescriptionXmlPath,
    )

def _formatUserDiagnostic(exc: BaseException) -> str:
    return cli_helpers.formatUserDiagnosticImpl(
        exc,
        description_mapping_error_type=DescriptionMappingError,
    )

def _promptInteractiveRange(args: argparse.Namespace) -> tuple[str, str]:
    return cli_helpers.promptInteractiveRangeImpl(
        args,
        shared_partial_range_token_fn=_sharedPartialRangeToken,
        extract_ref_parts_fn=_extractRefParts,
    )

def convertImage(input_path: str, output_path: str, *, max_iter: int = 120, plateau_limit: int = 14, seed: int = 42) -> Path:
    """Backward-compatible single-image entrypoint.

    - For raster targets (e.g. ``.png``), write an annotated image plus JSON coordinates.
    - For SVG targets or missing image deps, preserve the historical embedded-raster fallback.
    """
    del max_iter, plateau_limit, seed
    return legacy_api_helpers.convertImageImpl(
        input_path=input_path,
        output_path=output_path,
        render_embedded_raster_svg_fn=_renderEmbeddedRasterSvg,
        detect_relevant_regions_fn=detectRelevantRegions,
        annotate_image_regions_fn=annotateImageRegions,
        cv2_module=cv2,
        np_module=np,
    )

def convertImageWithRuntimeBindings(
    input_path: str,
    output_path: str,
    *,
    render_embedded_raster_svg_fn,
    detect_relevant_regions_fn,
    annotate_image_regions_fn,
    cv2_module,
    np_module,
    max_iter: int = 120,
    plateau_limit: int = 14,
    seed: int = 42,
) -> Path:
    """Compatibility helper to keep legacy runtime monkeypatch hooks in the caller module."""
    del max_iter, plateau_limit, seed
    return legacy_api_helpers.convertImageImpl(
        input_path=input_path,
        output_path=output_path,
        render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
        detect_relevant_regions_fn=detect_relevant_regions_fn,
        annotate_image_regions_fn=annotate_image_regions_fn,
        cv2_module=cv2_module,
        np_module=np_module,
    )

def convertImageVariants(*args, **kwargs):
    """Compatibility shim kept for tooling imports."""
    return legacy_api_helpers.convertImageVariantsImpl(*args, convert_range_fn=convertRange, **kwargs)
