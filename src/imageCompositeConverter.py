"""Image-to-composite-SVG conversion pipeline.

Ported from the user-provided prototype and exposed as a Python helper module
for direct CLI and module-based execution.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import copy
import csv
import dataclasses
import gc
import math
import os
import random
import time
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
import importlib
import struct
import statistics
from src.overviewTiles import generateConversionOverviews
from src.iCCModules.imageCompositeConverterRegions import (
    ANNOTATION_COLORS,
    analyzeRangeImpl,
    annotateImageRegionsImpl,
    detectRelevantRegionsImpl,
)
from src.iCCModules import imageCompositeConverterRange as range_helpers
from src.iCCModules import imageCompositeConverterDependencies as dependency_helpers
from src.iCCModules import imageCompositeConverterVendorInstall as vendor_install_helpers
from src.iCCModules import imageCompositeConverterDescriptions as description_mapping_helpers
from src.iCCModules import imageCompositeConverterSemantic as semantic_helpers
from src.iCCModules import imageCompositeConverterSemanticConnectors as semantic_connector_helpers
from src.iCCModules import imageCompositeConverterSemanticValidation as semantic_validation_helpers
from src.iCCModules import imageCompositeConverterSemanticChecks as semantic_checks_helpers
from src.iCCModules import imageCompositeConverterSemanticFitting as semantic_fitting_helpers
from src.iCCModules import imageCompositeConverterSemanticLabels as semantic_label_helpers
from src.iCCModules import imageCompositeConverterSemanticDefaults as semantic_default_helpers
from src.iCCModules import imageCompositeConverterSemanticAc0811 as semantic_ac0811_helpers
from src.iCCModules import imageCompositeConverterSemanticAc0812 as semantic_ac0812_helpers
from src.iCCModules import imageCompositeConverterSemanticAc0813 as semantic_ac0813_helpers
from src.iCCModules import imageCompositeConverterSemanticAc0223 as semantic_ac0223_helpers
from src.iCCModules import imageCompositeConverterSemanticAc08Params as semantic_ac08_param_helpers
from src.iCCModules import imageCompositeConverterSemanticAr0100 as semantic_ar0100_helpers
from src.iCCModules import imageCompositeConverterSemanticParams as semantic_param_helpers
from src.iCCModules import imageCompositeConverterSemanticBadgeGeometry as semantic_badge_geometry_helpers
from src.iCCModules import imageCompositeConverterSemanticBadgeSvg as semantic_badge_svg_helpers
from src.iCCModules import imageCompositeConverterSemanticAc08SmallVariants as semantic_ac08_small_variant_helpers
from src.iCCModules import imageCompositeConverterSemanticAc08Families as semantic_ac08_family_helpers
from src.iCCModules import imageCompositeConverterSemanticAc08Finalization as semantic_ac08_finalization_helpers
from src.iCCModules import imageCompositeConverterSemanticAdaptiveLocks as semantic_adaptive_lock_helpers
from src.iCCModules import imageCompositeConverterSemanticCircleStyle as semantic_circle_style_helpers
from src.iCCModules import imageCompositeConverterSemanticRedrawVariation as semantic_redraw_variation_helpers
from src.iCCModules import imageCompositeConverterQuality as quality_helpers
from src.iCCModules import imageCompositeConverterQualityConfig as quality_config_helpers
from src.iCCModules import imageCompositeConverterQualityThreshold as quality_threshold_helpers
from src.iCCModules import imageCompositeConverterAudit as audit_helpers
from src.iCCModules import imageCompositeConverterTransfer as transfer_helpers
from src.iCCModules import imageCompositeConverterGeometryBrackets as geometry_bracket_helpers
from src.iCCModules import imageCompositeConverterOptimizationGeometry as geometry_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationColor as color_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationWidth as width_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationPasses as optimization_pass_helpers
from src.iCCModules import imageCompositeConverterOptimizationPassReporting as optimization_pass_reporting_helpers
from src.iCCModules import imageCompositeConverterOptimizationCirclePose as circle_pose_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationCircleSearch as circle_search_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationCircleRadius as circle_radius_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationCircleGeometry as circle_geometry_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationElementAlignment as element_alignment_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationScalars as scalar_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationQuantization as quantization_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationGlobalVector as global_vector_optimization_helpers
from src.iCCModules import imageCompositeConverterOptimizationGlobalSearch as global_search_optimization_helpers
from src.iCCModules import imageCompositeConverterMaskGeometry as mask_geometry_helpers
from src.iCCModules import imageCompositeConverterTemplateTransfer as template_transfer_helpers
from src.iCCModules import imageCompositeConverterSemanticGeometry as semantic_geometry_helpers
from src.iCCModules import imageCompositeConverterSemanticHarmonization as semantic_harmonization_helpers
from src.iCCModules import imageCompositeConverterRendering as rendering_helpers
from src.iCCModules import imageCompositeConverterRenderRuntime as rendering_runtime_helpers
from src.iCCModules import imageCompositeConverterRenderDispatch as render_dispatch_helpers
from src.iCCModules import imageCompositeConverterBatchReporting as batch_reporting_helpers
from src.iCCModules import imageCompositeConverterConversionInputs as conversion_input_helpers
from src.iCCModules import imageCompositeConverterConversionExecution as conversion_execution_helpers
from src.iCCModules import imageCompositeConverterConversionInitialPass as conversion_initial_pass_helpers
from src.iCCModules import imageCompositeConverterConversionQualityPass as conversion_quality_pass_helpers
from src.iCCModules import imageCompositeConverterFallback as fallback_helpers
from src.iCCModules import imageCompositeConverterConversionRows as conversion_row_helpers
from src.iCCModules import imageCompositeConverterAc08Reporting as ac08_reporting_helpers
from src.iCCModules import imageCompositeConverterAc08Gate as ac08_gate_helpers
from src.iCCModules import imageCompositeConverterRanking as ranking_helpers
from src.iCCModules import imageCompositeConverterThresholding as thresholding_helpers
from src.iCCModules import imageCompositeConverterSuccessfulConversions as successful_conversions_helpers
from src.iCCModules import imageCompositeConverterSuccessfulConversionQuality as successful_conversion_quality_helpers
from src.iCCModules import imageCompositeConverterSuccessfulConversionReport as successful_conversion_report_helpers
from src.iCCModules import imageCompositeConverterBestlist as conversion_bestlist_helpers
from src.iCCModules import imageCompositeConverterCli as cli_helpers
from src.iCCModules import imageCompositeConverterOutputPaths as output_path_helpers
from src.iCCModules import imageCompositeConverterIterationArtifacts as iteration_artifact_helpers
from src.iCCModules import imageCompositeConverterIterationLog as iteration_log_helpers
from src.iCCModules import imageCompositeConverterConversionReporting as conversion_reporting_helpers
from src.iCCModules import imageCompositeConverterConversionFinalization as conversion_finalization_helpers
from src.iCCModules import imageCompositeConverterRandom as random_helpers
from src.iCCModules import imageCompositeConverterConversionComposite as conversion_composite_helpers
from src.iCCModules import imageCompositeConverterLegacyApi as legacy_api_helpers
from src.iCCModules import imageCompositeConverterElementValidation as element_validation_helpers
from src.iCCModules import imageCompositeConverterOptimizationElementSearch as element_search_optimization_helpers
from src.iCCModules import imageCompositeConverterElementMasks as element_mask_helpers
from src.iCCModules import imageCompositeConverterElementErrorMetrics as element_error_metric_helpers
from src.iCCModules import imageCompositeConverterCompositeSvg as composite_svg_helpers
from src.iCCModules import imageCompositeConverterDiffing as diffing_helpers
from src.iCCModules import imageCompositeConverterForms as forms_helpers
from src.iCCModules import imageCompositeConverterCoreClasses as core_class_helpers
from src.iCCModules.imageCompositeConverterPerceptionReflection import Perception, Reflection
from src.iCCModules import imageCompositeConverterColorUtils as color_utils_helpers
from src.successfulConversions import (
    AC08_MITIGATION_STATUS,
    AC08_PREVIOUSLY_GOOD_VARIANTS,
    AC08_REGRESSION_CASES,
    AC08_REGRESSION_SET_NAME,
    AC08_REGRESSION_VARIANTS,
    SUCCESSFUL_CONVERSIONS,
    SUCCESSFUL_CONVERSIONS_MANIFEST,
    _loadSuccessfulConversions,
)
from src.iCCModules import imageCompositeConverterRemaining as imageCompositeConverterRemaining_helpers

# Keep regression variant list deterministic and duplicate-free for batch
# selection/tests even when upstream manifests accidentally repeat entries.
AC08_REGRESSION_VARIANTS = tuple(dict.fromkeys(AC08_REGRESSION_VARIANTS))
# Keep the historical "previously good" anchor subset stable for AC08 success
# criteria reports used by this converter/test suite.
AC08_PREVIOUSLY_GOOD_VARIANTS = ("AC0800_L", "AC0800_M", "AC0800_S", "AC0811_L")

_UNDER_PYTEST_RUNTIME = "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))

SVG_RENDER_SUBPROCESS_ENABLED = os.environ.get("IMAGE_CONVERTER_ISOLATE_SVG_RENDER", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
if not SVG_RENDER_SUBPROCESS_ENABLED and _UNDER_PYTEST_RUNTIME:
    # PyMuPDF can intermittently segfault in long in-process render loops during
    # the full test suite. Use the existing isolated renderer by default for
    # pytest-driven runs (including subprocess children inheriting pytest env)
    # unless explicitly disabled via env config.
    SVG_RENDER_SUBPROCESS_ENABLED = True
_default_svg_render_subprocess_timeout_sec = 20.0
if _UNDER_PYTEST_RUNTIME and "IMAGE_CONVERTER_ISOLATE_SVG_RENDER_TIMEOUT_SEC" not in os.environ:
    # Test runs may trigger many render attempts; keep per-attempt subprocess
    # timeouts tighter to avoid long stalls when a renderer child gets wedged.
    _default_svg_render_subprocess_timeout_sec = 5.0
try:
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = max(
        1.0,
        float(
            os.environ.get(
                "IMAGE_CONVERTER_ISOLATE_SVG_RENDER_TIMEOUT_SEC",
                str(_default_svg_render_subprocess_timeout_sec),
            ).strip()
            or str(_default_svg_render_subprocess_timeout_sec)
        ),
    )
except ValueError:
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = _default_svg_render_subprocess_timeout_sec


AC08_ADAPTIVE_LOCK_PROFILES: dict[str, dict[str, float | bool]] = {
    # Known AC08 outlier families from the improvement plan. Profiles only relax
    # tightly bounded locks after validation stagnates or when the residual
    # error stays clearly above the "good enough" range.
    "AC0882": {
        "radius_floor_ratio": 0.84,
        "arm_min_ratio": 0.68,
        "color_corridor": 10.0,
    },
    "AC0837": {
        "radius_floor_ratio": 0.86,
        "arm_min_ratio": 0.70,
        "color_corridor": 10.0,
    },
    "AC0839": {
        "radius_floor_ratio": 0.86,
        "arm_min_ratio": 0.70,
        "text_scale_delta": 0.10,
        "color_corridor": 10.0,
    },
    "AC0820": {
        "radius_floor_ratio": 0.88,
        "text_scale_delta": 0.10,
        "color_corridor": 8.0,
    },
    "AC0831": {
        "radius_floor_ratio": 0.87,
        "stem_min_ratio": 0.58,
        "text_scale_delta": 0.10,
        "color_corridor": 10.0,
    },
}


def detectRelevantRegions(img) -> list[dict[str, object]]:
    return imageCompositeConverterRemaining_helpers.detectRelevantRegions(img)


def annotateImageRegions(img, regions: list[dict[str, object]]):
    return imageCompositeConverterRemaining_helpers.annotateImageRegions(img, regions)


def analyzeRange(folder_path: str, output_root: str | None = None, start_ref: str = "", end_ref: str = "ZZZZZZ") -> str:
    return imageCompositeConverterRemaining_helpers.analyzeRange(folder_path, output_root, start_ref, end_ref)


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


# Load numpy before cv2: OpenCV's Python bindings import numpy at module-import
# time and can fail permanently for this process if cv2 is attempted first while
# numpy is available only via repo-vendored site-packages.
np = _load_optional_module("numpy")
cv2 = _load_optional_module("cv2")
fitz = _load_optional_module("fitz")  # PyMuPDF for native SVG rendering



def _clip(value, low, high):
    return imageCompositeConverterRemaining_helpers._clip(value, low, high)


RGBWert = forms_helpers.RGBWert
Punkt = forms_helpers.Punkt
Kreis = forms_helpers.Kreis
Griff = forms_helpers.Griff
Kelle = forms_helpers.Kelle
abstand = forms_helpers.abstand
buildOrientedKelle = forms_helpers.buildOrientedKelle


Element = core_class_helpers.Element
Candidate = core_class_helpers.Candidate
GlobalParameterVector = core_class_helpers.GlobalParameterVector


def loadGrayscaleImage(path: Path) -> list[list[int]]:
    return imageCompositeConverterRemaining_helpers.loadGrayscaleImage(path)


def _createDiffImageWithoutCv2(input_path: str | Path, svg_content: str):
    return imageCompositeConverterRemaining_helpers._createDiffImageWithoutCv2(input_path, svg_content)


def _computeOtsuThreshold(grayscale: list[list[int]]) -> int:
    return imageCompositeConverterRemaining_helpers._computeOtsuThreshold(grayscale)


def _adaptiveThreshold(grayscale: list[list[int]], block_size: int = 15, c: int = 5) -> list[list[int]]:
    return imageCompositeConverterRemaining_helpers._adaptiveThreshold(grayscale, block_size, c)


def loadBinaryImageWithMode(path: Path, *, threshold: int = 220, mode: str = "global") -> list[list[int]]:
    return imageCompositeConverterRemaining_helpers.loadBinaryImageWithMode(path, threshold=threshold, mode=mode)


def renderCandidateMask(candidate: Candidate, width: int, height: int) -> list[list[int]]:
    return imageCompositeConverterRemaining_helpers.renderCandidateMask(candidate, width, height)


def _iou(a: list[list[int]], b: list[list[int]]) -> float:
    return mask_metrics_helpers.iouImpl(a, b)


def scoreCandidate(target: list[list[int]], candidate: Candidate) -> float:
    return imageCompositeConverterRemaining_helpers.scoreCandidate(target, candidate)


def score_candidate(target: list[list[int]], candidate: Candidate) -> float:
    return imageCompositeConverterRemaining_helpers.score_candidate(target, candidate)


def randomNeighbor(base: Candidate, scale: float, rng: random.Random) -> Candidate:
    return imageCompositeConverterRemaining_helpers.randomNeighbor(base, scale, rng)


def optimizeElement(target: list[list[int]], init: Candidate, *, max_iter: int, plateau_limit: int, seed: int) -> tuple[Candidate, float]:
    return imageCompositeConverterRemaining_helpers.optimizeElement(target, init, max_iter=max_iter, plateau_limit=plateau_limit, seed=seed)


def optimize_element(target: list[list[int]], init: Candidate, *, max_iter: int, plateau_limit: int, seed: int) -> tuple[Candidate, float]:
    return imageCompositeConverterRemaining_helpers.optimize_element(target, init, max_iter=max_iter, plateau_limit=plateau_limit, seed=seed)


def _grayToHex(v: float) -> str:
    return imageCompositeConverterRemaining_helpers._grayToHex(v)


def estimateStrokeStyle(grayscale: list[list[int]], element: Element, candidate: Candidate) -> tuple[str, str | None, float | None]:
    return imageCompositeConverterRemaining_helpers.estimateStrokeStyle(grayscale, element, candidate)


def candidateToSvg(candidate: Candidate, gx: int, gy: int, fill_color: str, stroke_color: str | None = None, stroke_width: float | None = None) -> str:
    return imageCompositeConverterRemaining_helpers.candidateToSvg(candidate, gx, gy, fill_color, stroke_color, stroke_width)


def decomposeCircleWithStem(grayscale: list[list[int]], element: Element, candidate: Candidate) -> list[str] | None:
    return imageCompositeConverterRemaining_helpers.decomposeCircleWithStem(grayscale, element, candidate)

def _missingRequiredImageDependencies() -> list[str]:
    return imageCompositeConverterRemaining_helpers._missingRequiredImageDependencies()


def _bootstrapRequiredImageDependencies() -> list[str]:
    return imageCompositeConverterRemaining_helpers._bootstrapRequiredImageDependencies()


def rgbToHex(rgb: np.ndarray) -> str:
    return imageCompositeConverterRemaining_helpers.rgbToHex(rgb)


def getBaseNameFromFile(filename: str) -> str:
    return imageCompositeConverterRemaining_helpers.getBaseNameFromFile(filename)




SourceSpan = description_mapping_helpers.SourceSpan
DescriptionMappingError = description_mapping_helpers.DescriptionMappingError


def _loadDescriptionMapping(path: str) -> dict[str, str]:
    return imageCompositeConverterRemaining_helpers._loadDescriptionMapping(path)


def _loadDescriptionMappingFromCsv(path: str) -> dict[str, str]:
    return imageCompositeConverterRemaining_helpers._loadDescriptionMappingFromCsv(path)


def _loadDescriptionMappingFromXml(path: str) -> dict[str, str]:
    return imageCompositeConverterRemaining_helpers._loadDescriptionMappingFromXml(path)


def _resolveDescriptionXmlPath(path: str) -> str | None:
    return imageCompositeConverterRemaining_helpers._resolveDescriptionXmlPath(path)


def _requiredVendorPackages() -> list[str]:
    return imageCompositeConverterRemaining_helpers._requiredVendorPackages()


def buildLinuxVendorInstallCommand(
    vendor_dir: str = "vendor",
    platform_tag: str = "manylinux2014_x86_64",
    python_version: str | None = None,
) -> list[str]:
    return imageCompositeConverterRemaining_helpers.buildLinuxVendorInstallCommand(vendor_dir, platform_tag, python_version)

def _renderSvgToNumpyInprocess(svg_string: str, size_w: int, size_h: int):
    return imageCompositeConverterRemaining_helpers._renderSvgToNumpyInprocess(svg_string, size_w, size_h)


def _renderSvgToNumpyViaSubprocess(svg_string: str, size_w: int, size_h: int):
    return imageCompositeConverterRemaining_helpers._renderSvgToNumpyViaSubprocess(svg_string, size_w, size_h)


def _render_svg_to_numpy_inprocess(svg_string: str, size_w: int, size_h: int):
    return imageCompositeConverterRemaining_helpers._render_svg_to_numpy_inprocess(svg_string, size_w, size_h)


def _render_svg_to_numpy_via_subprocess(svg_string: str, size_w: int, size_h: int):
    return imageCompositeConverterRemaining_helpers._render_svg_to_numpy_via_subprocess(svg_string, size_w, size_h)


def _is_fitz_open_monkeypatched() -> bool:
    return imageCompositeConverterRemaining_helpers._is_fitz_open_monkeypatched()


def _is_inprocess_renderer_monkeypatched() -> bool:
    return imageCompositeConverterRemaining_helpers._is_inprocess_renderer_monkeypatched()


def _bbox_to_dict(label: str, bbox: tuple[int, int, int, int], color: tuple[int, int, int]) -> dict[str, object]:
    return imageCompositeConverterRemaining_helpers._bbox_to_dict(label, bbox, color)


def _runSvgRenderSubprocessEntrypoint() -> int:
    return imageCompositeConverterRemaining_helpers._runSvgRenderSubprocessEntrypoint()


class Action:
    STOCHASTIC_SEED_OFFSET = 0
    STOCHASTIC_RUN_SEED = 0
    # DejaVuSans-Bold glyph outline in font units.
    M_PATH_D = "M188 1493H678L1018 694L1360 1493H1849V0H1485V1092L1141 287H897L553 1092V0H188Z"
    M_XMIN = 188
    M_XMAX = 1849
    M_YMIN = 0
    M_YMAX = 1493
    T_PATH_D = "M829 0V1194H381V1493H1636V1194H1188V0H829Z"
    T_XMIN = 381
    T_XMAX = 1636
    T_YMIN = 0
    T_YMAX = 1493

    # AR0100 tuned defaults for 25x25.
    AR0100_BASE = {
        "cx": 12.654,
        "cy": 12.065,
        "r": 11.280,
        "stroke_width": 1.618,
        "fill_gray": 244,
        "stroke_gray": 171,
        "text_gray": 110,
        "tx": 6.249,
        "ty": 5.946,
        "s": 0.007665,
    }

    AC0870_BASE = {
        "cx": 15.0,
        "cy": 15.0,
        "r": 12.0,
        "stroke_width": 2.0,
        "fill_gray": 220,
        "stroke_gray": 152,
        "text_gray": 98,
        "label": "T",
    }

    LIGHT_CIRCLE_FILL_GRAY = 242
    # Einheitliche AC08xx-Grauwerte (entspricht #7F7F7F).
    LIGHT_CIRCLE_STROKE_GRAY = 127
    LIGHT_CIRCLE_TEXT_GRAY = 127

    # Global guardrail for text sizing in semantic badges.
    # Historical runs were deliberately conservative to avoid overscaling on
    # noisy rasters, but this can make converted labels consistently too small.
    # Keep a mild global uplift that applies across text modes.
    SEMANTIC_TEXT_BASE_SCALE = 1.08
    AC08_STROKE_WIDTH_PX = 1.0

    @staticmethod
    def grayhex(gray: int) -> str:
        g = max(0, min(255, int(round(gray))))
        return f"#{g:02x}{g:02x}{g:02x}"

    @staticmethod
    def _snapHalf(value: float) -> float:
        return round(float(value) * 2.0) / 2.0

    @staticmethod
    def _clipScalar(value: float, low: float, high: float) -> float:
        """Return value clamped to ``[low, high]`` with ``numpy.clip`` scalar semantics."""
        lo = float(low)
        hi = float(high)
        # Mirror numpy.clip behaviour for inverted bounds (a_min > a_max):
        # any scalar collapses to the supplied upper bound.
        if lo > hi:
            return hi
        v = float(value)
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v

    @staticmethod
    def _makeRng(seed: int):
        return scalar_optimization_helpers.makeRngImpl(seed, np_module=np)

    @staticmethod
    def _argminIndex(values: list[float]) -> int:
        return scalar_optimization_helpers.argminIndexImpl(values)

    @staticmethod
    def _snapIntPx(value: float, minimum: float = 1.0) -> float:
        return scalar_optimization_helpers.snapIntPxImpl(value, minimum=minimum)

    @staticmethod
    def _maxCircleRadiusInsideCanvas(cx: float, cy: float, w: int, h: int, stroke: float = 0.0) -> float:
        return scalar_optimization_helpers.maxCircleRadiusInsideCanvasImpl(cx, cy, w, h, stroke)

    @staticmethod
    def _isCircleWithText(params: dict) -> bool:
        return scalar_optimization_helpers.isCircleWithTextImpl(params)

    @staticmethod
    def _applyCircleTextWidthConstraint(params: dict, radius: float, w: int) -> float:
        return scalar_optimization_helpers.applyCircleTextWidthConstraintImpl(params, radius, w)

    @staticmethod
    def _applyCircleTextRadiusFloor(params: dict, radius: float) -> float:
        return scalar_optimization_helpers.applyCircleTextRadiusFloorImpl(
            params,
            radius,
            text_bbox_fn=Action._textBbox,
        )

    @staticmethod
    def _clampCircleInsideCanvas(params: dict, w: int, h: int) -> dict:
        return scalar_optimization_helpers.clampCircleInsideCanvasImpl(
            params,
            w,
            h,
            text_bbox_fn=Action._textBbox,
        )

    @staticmethod
    def applyRedrawVariation(params: dict, w: int, h: int) -> tuple[dict, list[str]]:
        return semantic_redraw_variation_helpers.applyRedrawVariationImpl(
            params,
            w,
            h,
            stochastic_run_seed=Action.STOCHASTIC_RUN_SEED,
            stochastic_seed_offset=Action.STOCHASTIC_SEED_OFFSET,
            time_ns_fn=time.time_ns,
            make_rng_fn=Action._makeRng,
            clamp_circle_inside_canvas_fn=Action._clampCircleInsideCanvas,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
        )

    @staticmethod
    def _enforceCircleConnectorSymmetry(params: dict, w: int, h: int) -> dict:
        return quantization_optimization_helpers.enforceCircleConnectorSymmetryImpl(params, w, h)

    @staticmethod
    def _quantizeBadgeParams(params: dict, w: int, h: int) -> dict:
        return quantization_optimization_helpers.quantizeBadgeParamsImpl(
            params,
            w,
            h,
            snap_half_fn=Action._snapHalf,
            snap_int_px_fn=Action._snapIntPx,
            enforce_circle_connector_symmetry_fn=Action._enforceCircleConnectorSymmetry,
            clamp_circle_inside_canvas_fn=Action._clampCircleInsideCanvas,
            max_circle_radius_inside_canvas_fn=Action._maxCircleRadiusInsideCanvas,
        )

    @staticmethod
    def _normalizeLightCircleColors(params: dict) -> dict:
        return semantic_circle_style_helpers.normalizeLightCircleColorsImpl(
            params,
            light_circle_fill_gray=Action.LIGHT_CIRCLE_FILL_GRAY,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            light_circle_text_gray=Action.LIGHT_CIRCLE_TEXT_GRAY,
        )

    @staticmethod
    def _normalizeAc08LineWidths(params: dict) -> dict:
        return semantic_circle_style_helpers.normalizeAc08LineWidthsImpl(
            params,
            ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
        )

    @staticmethod
    def _estimateBorderBackgroundGray(gray: np.ndarray) -> float:
        return semantic_circle_style_helpers.estimateBorderBackgroundGrayImpl(gray, np_module=np)

    @staticmethod
    def _estimateCircleTonesAndStroke(
        gray: np.ndarray,
        cx: float,
        cy: float,
        r: float,
        stroke_hint: float,
    ) -> tuple[float, float, float]:
        return semantic_circle_style_helpers.estimateCircleTonesAndStrokeImpl(
            gray,
            cx,
            cy,
            r,
            stroke_hint,
            np_module=np,
        )

    @staticmethod
    def _persistConnectorLengthFloor(params: dict, element: str, default_ratio: float) -> None:
        semantic_ac08_small_variant_helpers.persistConnectorLengthFloorImpl(params, element, default_ratio)

    @staticmethod
    def _isAc08SmallVariant(name: str, params: dict) -> tuple[bool, str, float]:
        return semantic_ac08_small_variant_helpers.isAc08SmallVariantImpl(name, params)

    @staticmethod
    def _configureAc08SmallVariantMode(name: str, params: dict) -> dict:
        return semantic_ac08_small_variant_helpers.configureAc08SmallVariantModeImpl(
            name,
            params,
            is_ac08_small_variant_fn=Action._isAc08SmallVariant,
            persist_connector_length_floor_fn=Action._persistConnectorLengthFloor,
        )

    @staticmethod
    def _enforceTemplateCircleEdgeExtent(params: dict, w: int, h: int, *, anchor: str, retain_ratio: float = 0.97) -> dict:
        return semantic_ac08_family_helpers.enforceTemplateCircleEdgeExtentImpl(
            params,
            w,
            h,
            anchor=anchor,
            retain_ratio=retain_ratio,
            max_circle_radius_inside_canvas_fn=Action._maxCircleRadiusInsideCanvas,
        )


    @staticmethod
    def _tuneAc08LeftConnectorFamily(name: str, params: dict) -> dict:
        return semantic_ac08_family_helpers.tuneAc08LeftConnectorFamilyImpl(
            name,
            params,
            get_base_name_from_file_fn=getBaseNameFromFile,
            is_ac08_small_variant_fn=Action._isAc08SmallVariant,
            enforce_template_circle_edge_extent_fn=Action._enforceTemplateCircleEdgeExtent,
            enforce_left_arm_badge_geometry_fn=Action._enforceLeftArmBadgeGeometry,
            center_glyph_bbox_fn=Action._centerGlyphBbox,
        )

    @staticmethod
    def _tuneAc08RightConnectorFamily(name: str, params: dict) -> dict:
        return semantic_ac08_family_helpers.tuneAc08RightConnectorFamilyImpl(
            name,
            params,
            get_base_name_from_file_fn=getBaseNameFromFile,
            is_ac08_small_variant_fn=Action._isAc08SmallVariant,
            enforce_template_circle_edge_extent_fn=Action._enforceTemplateCircleEdgeExtent,
            enforce_right_arm_badge_geometry_fn=Action._enforceRightArmBadgeGeometry,
        )

    @staticmethod
    def _enforceVerticalConnectorBadgeGeometry(params: dict, w: int, h: int) -> dict:
        return semantic_ac08_family_helpers.enforceVerticalConnectorBadgeGeometryImpl(
            params,
            w,
            h,
            ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
        )

    @staticmethod
    def _tuneAc08VerticalConnectorFamily(name: str, params: dict) -> dict:
        return semantic_ac08_family_helpers.tuneAc08VerticalConnectorFamilyImpl(
            name,
            params,
            get_base_name_from_file_fn=getBaseNameFromFile,
            is_ac08_small_variant_fn=Action._isAc08SmallVariant,
            enforce_vertical_connector_badge_geometry_fn=Action._enforceVerticalConnectorBadgeGeometry,
        )

    @staticmethod
    def _tuneAc08CircleTextFamily(name: str, params: dict) -> dict:
        return semantic_ac08_family_helpers.tuneAc08CircleTextFamilyImpl(
            name,
            params,
            get_base_name_from_file_fn=getBaseNameFromFile,
            max_circle_radius_inside_canvas_fn=Action._maxCircleRadiusInsideCanvas,
            center_glyph_bbox_fn=Action._centerGlyphBbox,
        )

    @staticmethod
    def _finalizeAc08Style(name: str, params: dict) -> dict:
        return semantic_ac08_finalization_helpers.finalizeAc08StyleImpl(
            name,
            params,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            capture_canonical_badge_colors_fn=Action._captureCanonicalBadgeColors,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
            normalize_ac08_line_widths_fn=Action._normalizeAc08LineWidths,
            normalize_centered_co2_label_fn=Action._normalizeCenteredCo2Label,
            tune_ac0833_co2_badge_fn=Action._tuneAc0833Co2Badge,
            needs_large_circle_overflow_guard_fn=_needsLargeCircleOverflowGuard,
            align_stem_to_circle_center_fn=Action._alignStemToCircleCenter,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            persist_connector_length_floor_fn=Action._persistConnectorLengthFloor,
            configure_ac08_small_variant_mode_fn=Action._configureAc08SmallVariantMode,
            clip_scalar_fn=Action._clipScalar,
        )

    @staticmethod
    def _activateAc08AdaptiveLocks(
        params: dict,
        logs: list[str],
        *,
        full_err: float,
        reason: str,
    ) -> bool:
        return semantic_adaptive_lock_helpers.activateAc08AdaptiveLocksImpl(
            params,
            logs,
            full_err=full_err,
            reason=reason,
        )

    @staticmethod
    def _releaseAc08AdaptiveLocks(
        params: dict,
        logs: list[str],
        *,
        reason: str,
        current_error: float,
    ) -> bool:
        return semantic_adaptive_lock_helpers.releaseAc08AdaptiveLocksImpl(
            params,
            logs,
            reason=reason,
            current_error=current_error,
        )

    @staticmethod
    def _alignStemToCircleCenter(params: dict) -> dict:
        """Ensure vertical handle/stem extension runs through circle center.

        For vertical connector badges (e.g. AC0811/AC0831/AC0836), force the
        connector start to the circle edge so quantization does not leave a
        visible gap between circle and stem.
        """
        return semantic_badge_geometry_helpers.alignStemToCircleCenterImpl(
            params,
            default_stroke_width=Action.AC08_STROKE_WIDTH_PX,
        )

    @staticmethod
    def _defaultAc0870Params(w: int, h: int) -> dict:
        return semantic_default_helpers.defaultAc0870ParamsImpl(
            w,
            h,
            ac0870_base=Action.AC0870_BASE,
            center_glyph_bbox=Action._centerGlyphBbox,
            normalize_light_circle_colors=Action._normalizeLightCircleColors,
        )

    @staticmethod
    def _defaultAc0881Params(w: int, h: int) -> dict:
        return semantic_default_helpers.defaultAc0881ParamsImpl(
            w,
            h,
            default_ac0870_params=Action._defaultAc0870Params,
        )

    @staticmethod
    def _defaultAc081xShared(w: int, h: int) -> dict:
        return semantic_default_helpers.defaultAc081xSharedImpl(w, h)

    @staticmethod
    def _defaultEdgeAnchoredCircleGeometry(
        w: int,
        h: int,
        *,
        anchor: str,
        radius_ratio: float = 0.43,
        stroke_divisor: float = 15.0,
        edge_clearance_ratio: float = 0.08,
        edge_clearance_stroke_factor: float = 0.75,
    ) -> dict[str, float]:
        return semantic_ac0811_helpers.defaultEdgeAnchoredCircleGeometryImpl(
            w,
            h,
            anchor=anchor,
            radius_ratio=radius_ratio,
            stroke_divisor=stroke_divisor,
            edge_clearance_ratio=edge_clearance_ratio,
            edge_clearance_stroke_factor=edge_clearance_stroke_factor,
        )

    @staticmethod
    def _defaultAc0811Params(w: int, h: int) -> dict:
        return semantic_ac0811_helpers.defaultAc0811ParamsImpl(
            w,
            h,
            default_ac081x_shared=Action._defaultAc081xShared,
            default_edge_anchored_circle_geometry=Action._defaultEdgeAnchoredCircleGeometry,
            normalize_light_circle_colors=Action._normalizeLightCircleColors,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            light_circle_fill_gray=Action.LIGHT_CIRCLE_FILL_GRAY,
        )

    @staticmethod
    def _estimateUpperCircleFromForeground(img: np.ndarray, defaults: dict) -> tuple[float, float, float] | None:
        return semantic_ac0811_helpers.estimateUpperCircleFromForegroundImpl(
            img,
            defaults,
            cv2_module=cv2,
            np_module=np,
            clip_scalar_fn=Action._clipScalar,
        )

    @staticmethod
    def _fitAc0811ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        return semantic_ac0811_helpers.fitAc0811ParamsFromImageImpl(
            img,
            defaults,
            fit_semantic_badge_from_image_fn=Action._fit_semantic_badge_from_image,
            estimate_upper_circle_from_foreground_fn=Action._estimate_upper_circle_from_foreground,
            clip_scalar_fn=Action._clipScalar,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
            persist_connector_length_floor_fn=Action._persistConnectorLengthFloor,
        )

    @staticmethod
    def _defaultAc0882Params(w: int, h: int) -> dict:
        return semantic_default_helpers.defaultAc0882ParamsImpl(
            w,
            h,
            default_ac081x_shared=Action._defaultAc081xShared,
            center_glyph_bbox=Action._centerGlyphBbox,
        )

    @staticmethod
    def _applyCo2Label(params: dict) -> dict:
        return semantic_label_helpers.applyCo2LabelImpl(
            params,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            semantic_text_base_scale=Action.SEMANTIC_TEXT_BASE_SCALE,
        )

    @staticmethod
    def _co2Layout(params: dict) -> dict[str, float | str]:
        """Compute renderer-independent CO₂ text metrics and placement."""
        return semantic_label_helpers.co2LayoutImpl(params)


    @staticmethod
    def _applyVocLabel(params: dict) -> dict:
        return semantic_label_helpers.applyVocLabelImpl(
            params,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            semantic_text_base_scale=Action.SEMANTIC_TEXT_BASE_SCALE,
        )

    @staticmethod
    def _tuneAc0832Co2Badge(params: dict) -> dict:
        return semantic_label_helpers.tuneAc0832Co2BadgeImpl(
            params,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
        )

    @staticmethod
    def _tuneAc0831Co2Badge(params: dict) -> dict:
        return semantic_label_helpers.tuneAc0831Co2BadgeImpl(
            params,
            ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
        )

    @staticmethod
    def _tuneAc0835VocBadge(params: dict, w: int, h: int) -> dict:
        return semantic_label_helpers.tuneAc0835VocBadgeImpl(
            params,
            w,
            h,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
        )

    @staticmethod
    def _tuneAc0833Co2Badge(params: dict) -> dict:
        return semantic_label_helpers.tuneAc0833Co2BadgeImpl(
            params,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
        )

    @staticmethod
    def _tuneAc0834Co2Badge(params: dict, w: int, h: int) -> dict:
        return semantic_label_helpers.tuneAc0834Co2BadgeImpl(
            params,
            w,
            h,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
        )

    @staticmethod
    def _defaultAc0834Params(w: int, h: int) -> dict:
        """Compatibility helper for AC0834 semantic tests and callers."""
        return semantic_label_helpers.defaultAc0834ParamsImpl(
            w,
            h,
            default_ac0814_params_fn=Action._defaultAc0814Params,
            apply_co2_label_fn=Action._applyCo2Label,
            tune_ac0834_co2_badge_fn=Action._tuneAc0834Co2Badge,
        )

    @staticmethod
    def _normalizeCenteredCo2Label(params: dict) -> dict:
        """Normalize CO₂ label sizing for plain circular badges."""
        normalized = semantic_label_helpers.normalizeCenteredCo2LabelImpl(params)
        normalized["text_gray"] = int(round(normalized.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))
        return normalized


    @staticmethod
    def _defaultAc0812Params(w: int, h: int) -> dict:
        return semantic_ac0812_helpers.defaultAc0812ParamsImpl(
            w,
            h,
            default_ac081x_shared=Action._defaultAc081xShared,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            light_circle_fill_gray=Action.LIGHT_CIRCLE_FILL_GRAY,
        )

    @staticmethod
    def _fitAc0812ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        return semantic_ac0812_helpers.fitAc0812ParamsFromImageImpl(
            img,
            defaults,
            fit_semantic_badge_from_image_fn=Action._fit_semantic_badge_from_image,
            max_circle_radius_inside_canvas_fn=Action._maxCircleRadiusInsideCanvas,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
        )

    @staticmethod
    def _enforceLeftArmBadgeGeometry(params: dict, w: int, h: int) -> dict:
        """Ensure AC0812-like badges always keep a visible left connector arm."""
        return semantic_connector_helpers.enforceLeftArmBadgeGeometryImpl(
            params,
            ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
        )

    @staticmethod
    def _enforceRightArmBadgeGeometry(params: dict, w: int, h: int) -> dict:
        """Ensure AC0810/AC0814-like badges always keep a visible right connector arm."""
        return semantic_connector_helpers.enforceRightArmBadgeGeometryImpl(
            params,
            w=w,
            ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
        )

    @staticmethod
    def _defaultAc0813Params(w: int, h: int) -> dict:
        return semantic_ac0813_helpers.defaultAc0813ParamsImpl(
            w,
            h,
            default_ac081x_shared=Action._defaultAc081xShared,
            default_edge_anchored_circle_geometry_fn=Action._defaultEdgeAnchoredCircleGeometry,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            light_circle_fill_gray=Action.LIGHT_CIRCLE_FILL_GRAY,
        )

    @staticmethod
    def _fitAc0813ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        return semantic_ac0813_helpers.fitAc0813ParamsFromImageImpl(
            img,
            defaults,
            fit_semantic_badge_from_image_fn=Action._fit_semantic_badge_from_image,
            clip_scalar_fn=Action._clipScalar,
            enforce_directional_circle_side_fn=semantic_fitting_helpers.enforceDirectionalCircleSideImpl,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
        )

    @staticmethod
    def _rotateSemanticBadgeClockwise(params: dict, w: int, h: int) -> dict:
        return semantic_badge_geometry_helpers.rotateSemanticBadgeClockwiseImpl(params, w, h)

    @staticmethod
    def _defaultAc0814Params(w: int, h: int) -> dict:
        return semantic_ac0813_helpers.defaultAc0814ParamsImpl(
            w,
            h,
            default_ac081x_shared=Action._defaultAc081xShared,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
            light_circle_stroke_gray=Action.LIGHT_CIRCLE_STROKE_GRAY,
            light_circle_fill_gray=Action.LIGHT_CIRCLE_FILL_GRAY,
        )

    @staticmethod
    def _fitAc0814ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        return semantic_ac0813_helpers.fitAc0814ParamsFromImageImpl(
            img,
            defaults,
            fit_semantic_badge_from_image_fn=Action._fit_semantic_badge_from_image,
            clip_scalar_fn=Action._clipScalar,
            enforce_directional_circle_side_fn=semantic_fitting_helpers.enforceDirectionalCircleSideImpl,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
        )

    @staticmethod
    def _defaultAc0810Params(w: int, h: int) -> dict:
        return semantic_ac0813_helpers.defaultAc0810ParamsImpl(
            w,
            h,
            default_ac0814_params_fn=Action._defaultAc0814Params,
        )

    @staticmethod
    def _fitAc0810ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        return semantic_ac0813_helpers.fitAc0810ParamsFromImageImpl(
            img,
            defaults,
            fit_ac0814_params_from_image_fn=Action._fit_ac0814_params_from_image,
        )

    @staticmethod
    def _glyphBbox(text_mode: str) -> tuple[int, int, int, int]:
        return semantic_badge_geometry_helpers.glyphBboxImpl(
            text_mode,
            t_xmin=Action.T_XMIN,
            t_ymin=Action.T_YMIN,
            t_xmax=Action.T_XMAX,
            t_ymax=Action.T_YMAX,
            m_xmin=Action.M_XMIN,
            m_ymin=Action.M_YMIN,
            m_xmax=Action.M_XMAX,
            m_ymax=Action.M_YMAX,
        )

    @staticmethod
    def _centerGlyphBbox(params: dict) -> None:
        semantic_badge_geometry_helpers.centerGlyphBboxImpl(
            params,
            glyph_bbox_fn=Action._glyphBbox,
        )

    @staticmethod
    def _stabilizeSemanticCirclePose(params: dict, defaults: dict, w: int, h: int) -> dict:
        return semantic_fitting_helpers.stabilizeSemanticCirclePoseImpl(params, defaults, w, h)

    def _fitAc0870ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        return semantic_fitting_helpers.fitAc0870ParamsFromImageImpl(
            img,
            defaults,
            cv2=cv2,
            np=np,
            t_xmin=Action.T_XMIN,
            t_ymax=Action.T_YMAX,
            center_glyph_bbox_fn=Action._centerGlyphBbox,
        )

    @staticmethod
    def _fitSemanticBadgeFromImage(img: np.ndarray, defaults: dict) -> dict:
        return semantic_fitting_helpers.fitSemanticBadgeFromImageImpl(
            img,
            defaults,
            cv2=cv2,
            np=np,
            estimate_circle_tones_and_stroke_fn=Action._estimateCircleTonesAndStroke,
            estimate_border_background_gray_fn=Action._estimateBorderBackgroundGray,
            foreground_mask_fn=Action._foregroundMask,
            clip_scalar_fn=Action._clipScalar,
            center_glyph_bbox_fn=Action._centerGlyphBbox,
            stabilize_semantic_circle_pose_fn=Action._stabilizeSemanticCirclePose,
            normalize_light_circle_colors_fn=Action._normalizeLightCircleColors,
        )

    @staticmethod
    def _default_ac0811_params(w: int, h: int) -> dict:
        return Action._defaultAc0811Params(w, h)

    @staticmethod
    def make_badge_params(w: int, h: int, base_name: str, img: np.ndarray | None = None) -> dict | None:
        return Action.makeBadgeParams(w, h, base_name, img)

    @staticmethod
    def validate_semantic_description_alignment(
        img_orig,
        semantic_elements: list[str],
        badge_params: dict,
    ) -> list[str]:
        return Action.validateSemanticDescriptionAlignment(img_orig, semantic_elements, badge_params)

    @staticmethod
    def validate_badge_by_elements(
        img_orig,
        badge_params: dict,
        *,
        max_rounds: int = 2,
        debug_out_dir: str | None = None,
        stop_when_error_below_threshold: bool = False,
    ) -> list[str]:
        return Action.validateBadgeByElements(
            img_orig,
            badge_params,
            max_rounds=max_rounds,
            debug_out_dir=debug_out_dir,
            stop_when_error_below_threshold=stop_when_error_below_threshold,
        )

    @staticmethod
    def generate_badge_svg(w: int, h: int, params: dict) -> str:
        return Action.generateBadgeSvg(w, h, params)

    @staticmethod
    def render_svg_to_numpy(svg_content: str, w: int, h: int):
        return Action.renderSvgToNumpy(svg_content, w, h)

    @staticmethod
    def _detect_semantic_primitives(
        img_orig: np.ndarray,
        badge_params: dict | None = None,
    ) -> dict[str, bool | int | str]:
        return Action._detectSemanticPrimitives(img_orig, badge_params)

    @staticmethod
    def _foreground_mask(img: np.ndarray) -> np.ndarray:
        return Action._foregroundMask(img)

    @staticmethod
    def _circle_from_foreground_mask(fg_mask: np.ndarray) -> tuple[float, float, float] | None:
        return Action._circleFromForegroundMask(fg_mask)

    @staticmethod
    def _mask_supports_circle(mask: np.ndarray | None) -> bool:
        return Action._maskSupportsCircle(mask)

    @staticmethod
    def _mask_bbox(mask: np.ndarray) -> tuple[float, float, float, float] | None:
        return Action._maskBbox(mask)

    @staticmethod
    def _mask_centroid_radius(mask: np.ndarray) -> tuple[float, float, float] | None:
        return Action._maskCentroidRadius(mask)

    @staticmethod
    def extract_badge_element_mask(img_orig: np.ndarray, params: dict, element: str) -> np.ndarray | None:
        return Action.extractBadgeElementMask(img_orig, params, element)

    @staticmethod
    def _enforce_semantic_connector_expectation(
        base_name: str,
        semantic_elements: list[str],
        badge_params: dict,
        w: int,
        h: int,
    ) -> dict:
        return Action._enforceSemanticConnectorExpectation(base_name, semantic_elements, badge_params, w, h)

    @staticmethod
    def apply_redraw_variation(params: dict, w: int, h: int) -> tuple[dict, list[str]]:
        return Action.applyRedrawVariation(params, w, h)

    @staticmethod
    def calculate_error(img1, img2) -> float:
        return Action.calculateError(img1, img2)

    @staticmethod
    def create_diff_image(img1, img2, focus_mask=None):
        return Action.createDiffImage(img1, img2, focus_mask=focus_mask)

    @staticmethod
    def makeBadgeParams(w: int, h: int, base_name: str, img: np.ndarray | None = None) -> dict | None:
        return semantic_param_helpers.makeBadgeParamsImpl(
            w,
            h,
            base_name,
            img,
            get_base_name_fn=getBaseNameFromFile,
            build_ar0100_badge_params_fn=lambda _w, _h, name: (
                semantic_ar0100_helpers.buildAr0100BadgeParamsImpl(
                    _w,
                    _h,
                    ar0100_base=Action.AR0100_BASE,
                    center_glyph_bbox_fn=Action._centerGlyphBbox,
                )
                if name == "AR0100"
                else None
            ),
            build_ac0223_badge_params_fn=lambda _w, _h, name, _img: (
                (
                    semantic_ac0223_helpers.defaultAc0223ParamsImpl(
                        _w,
                        _h,
                        default_ac0813_params_fn=Action._defaultAc0813Params,
                    )
                    if _img is None
                    else semantic_ac0223_helpers.fitAc0223ParamsFromImageImpl(
                        _img,
                        semantic_ac0223_helpers.defaultAc0223ParamsImpl(
                            _w,
                            _h,
                            default_ac0813_params_fn=Action._defaultAc0813Params,
                        ),
                        fit_ac0813_params_from_image_fn=Action._fitAc0813ParamsFromImage,
                    )
                )
                if name == "AC0223"
                else None
            ),
            make_ac08_badge_params_fn=lambda _w, _h, name, _img: semantic_ac08_param_helpers.makeAc08BadgeParamsImpl(
                _w,
                _h,
                name,
                _img,
                default_ac0870_params_fn=Action._defaultAc0870Params,
                default_ac0811_params_fn=Action._defaultAc0811Params,
                default_ac0810_params_fn=Action._defaultAc0810Params,
                default_ac0812_params_fn=Action._defaultAc0812Params,
                default_ac0813_params_fn=Action._defaultAc0813Params,
                default_ac0814_params_fn=Action._defaultAc0814Params,
                default_ac0881_params_fn=Action._defaultAc0881Params,
                default_ac0882_params_fn=Action._defaultAc0882Params,
                fit_ac0870_params_from_image_fn=Action._fitAc0870ParamsFromImage,
                fit_semantic_badge_from_image_fn=Action._fit_semantic_badge_from_image,
                fit_ac0811_params_from_image_fn=Action._fit_ac0811_params_from_image,
                fit_ac0810_params_from_image_fn=Action._fitAc0810ParamsFromImage,
                fit_ac0812_params_from_image_fn=Action._fit_ac0812_params_from_image,
                fit_ac0813_params_from_image_fn=Action._fitAc0813ParamsFromImage,
                fit_ac0814_params_from_image_fn=Action._fit_ac0814_params_from_image,
                apply_co2_label_fn=Action._applyCo2Label,
                apply_voc_label_fn=Action._applyVocLabel,
                tune_ac0831_co2_badge_fn=Action._tuneAc0831Co2Badge,
                tune_ac0832_co2_badge_fn=Action._tuneAc0832Co2Badge,
                tune_ac0833_co2_badge_fn=Action._tuneAc0833Co2Badge,
                tune_ac0834_co2_badge_fn=Action._tuneAc0834Co2Badge,
                tune_ac0835_voc_badge_fn=Action._tuneAc0835VocBadge,
                finalize_ac08_style_fn=Action._finalizeAc08Style,
                enforce_left_arm_badge_geometry_fn=Action._enforceLeftArmBadgeGeometry,
            ),
        )

    @staticmethod
    def generateBadgeSvg(w: int, h: int, p: dict) -> str:
        return semantic_badge_svg_helpers.generateBadgeSvgImpl(
            w,
            h,
            p,
            align_stem_to_circle_center_fn=Action._alignStemToCircleCenter,
            quantize_badge_params_fn=Action._quantizeBadgeParams,
            clip_scalar_fn=Action._clipScalar,
            grayhex_fn=Action.grayhex,
            co2_layout_fn=Action._co2Layout,
            t_path_d=Action.T_PATH_D,
            t_xmin=Action.T_XMIN,
            t_ymax=Action.T_YMAX,
            m_path_d=Action.M_PATH_D,
            m_xmin=Action.M_XMIN,
            m_ymax=Action.M_YMAX,
        )

    @staticmethod
    def traceImageSegment(
        img_segment: np.ndarray,
        epsilon_factor: float,
        *,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> list[str]:
        return composite_svg_helpers.traceImageSegmentImpl(
            img_segment,
            epsilon_factor,
            scale_x=scale_x,
            scale_y=scale_y,
            offset_x=offset_x,
            offset_y=offset_y,
            cv2_module=cv2,
            np_module=np,
            rgb_to_hex_fn=rgbToHex,
        )

    @staticmethod
    def generateCompositeSvg(w: int, h: int, params: dict, folder_path: str, epsilon: float) -> str:
        return composite_svg_helpers.generateCompositeSvgImpl(
            w,
            h,
            params,
            folder_path,
            epsilon,
            os_module=os,
            cv2_module=cv2,
            trace_image_segment_fn=Action.traceImageSegment,
        )

    @staticmethod
    def renderSvgToNumpy(svg_string: str, size_w: int, size_h: int):
        return render_dispatch_helpers.renderSvgToNumpyImpl(
            svg_string,
            size_w,
            size_h,
            svg_render_subprocess_enabled=SVG_RENDER_SUBPROCESS_ENABLED,
            under_pytest_runtime=_UNDER_PYTEST_RUNTIME,
            is_fitz_open_monkeypatched_fn=_is_fitz_open_monkeypatched,
            render_svg_to_numpy_via_subprocess_fn=_render_svg_to_numpy_via_subprocess,
            is_inprocess_renderer_monkeypatched_fn=_is_inprocess_renderer_monkeypatched,
            render_svg_to_numpy_inprocess_fn=_render_svg_to_numpy_inprocess,
        )

    @staticmethod
    def createDiffImage(
        img_orig: np.ndarray,
        img_svg: np.ndarray,
        focus_mask: np.ndarray | None = None,
    ) -> np.ndarray:
        return diffing_helpers.createDiffImageImpl(
            img_orig,
            img_svg,
            cv2_module=cv2,
            np_module=np,
            focus_mask=focus_mask,
        )

    @staticmethod
    def calculateError(img_orig: np.ndarray, img_svg: np.ndarray) -> float:
        return diffing_helpers.calculateErrorImpl(
            img_orig,
            img_svg,
            cv2_module=cv2,
            np_module=np,
        )

    @staticmethod
    def calculateDelta2Stats(img_orig: np.ndarray, img_svg: np.ndarray) -> tuple[float, float]:
        return element_error_metric_helpers.calculateDelta2StatsImpl(
            img_orig,
            img_svg,
            cv2_module=cv2,
            np_module=np,
        )

    @staticmethod
    def _fitToOriginalSize(img_orig: np.ndarray, img_svg: np.ndarray | None) -> np.ndarray | None:
        return mask_geometry_helpers.fitToOriginalSizeImpl(img_orig, img_svg, cv2)

    @staticmethod
    def _maskCentroidRadius(mask: np.ndarray) -> tuple[float, float, float] | None:
        return mask_geometry_helpers.maskCentroidRadiusImpl(mask)

    @staticmethod
    def _maskBbox(mask: np.ndarray) -> tuple[float, float, float, float] | None:
        return mask_geometry_helpers.maskBboxImpl(mask)

    @staticmethod
    def _maskCenterSize(mask: np.ndarray) -> tuple[float, float, float] | None:
        return mask_geometry_helpers.maskCenterSizeImpl(mask, mask_bbox_fn=Action._maskBbox)

    @staticmethod
    def _maskMinRectCenterDiag(mask: np.ndarray) -> tuple[float, float, float] | None:
        return mask_geometry_helpers.maskMinRectCenterDiagImpl(mask, cv2=cv2)

    @staticmethod
    def _elementBboxChangeIsPlausible(
        mask_orig: np.ndarray,
        mask_svg: np.ndarray,
    ) -> tuple[bool, str | None]:
        return mask_geometry_helpers.elementBboxChangeIsPlausibleImpl(
            mask_orig,
            mask_svg,
            mask_bbox_fn=Action._maskBbox,
        )

    @staticmethod
    def _applyElementAlignmentStep(
        params: dict,
        element: str,
        center_dx: float,
        center_dy: float,
        diag_scale: float,
        w: int,
        h: int,
        apply_circle_geometry_penalty: bool = True,
    ) -> bool:
        return element_validation_helpers.applyElementAlignmentStepImpl(
            params,
            element,
            center_dx,
            center_dy,
            diag_scale,
            w,
            h,
            clip_scalar_fn=Action._clipScalar,
            apply_circle_geometry_penalty=apply_circle_geometry_penalty,
        )

    @staticmethod
    def _estimateVerticalStemFromMask(
        mask: np.ndarray,
        expected_cx: float,
        y_start: int,
        y_end: int,
    ) -> tuple[float, float] | None:
        return element_alignment_optimization_helpers.estimateVerticalStemFromMaskImpl(
            mask,
            expected_cx,
            y_start,
            y_end,
            np_module=np,
        )

    @staticmethod
    def _ringAndFillMasks(h: int, w: int, params: dict) -> tuple[np.ndarray, np.ndarray]:
        return element_mask_helpers.ringAndFillMasksImpl(h, w, params, np_module=np)

    @staticmethod
    def _meanGrayForMask(img: np.ndarray, mask: np.ndarray) -> float | None:
        return element_mask_helpers.meanGrayForMaskImpl(img, mask, cv2_module=cv2, np_module=np)

    @staticmethod
    def _elementRegionMask(
        h: int,
        w: int,
        params: dict,
        element: str,
        apply_circle_geometry_penalty: bool = True,
    ) -> np.ndarray | None:
        return element_mask_helpers.elementRegionMaskImpl(
            h,
            w,
            params,
            element,
            np_module=np,
            text_bbox_fn=Action._textBbox,
            apply_circle_geometry_penalty=apply_circle_geometry_penalty,
        )

    @staticmethod
    def _textBbox(params: dict) -> tuple[float, float, float, float]:
        return element_mask_helpers.textBboxImpl(
            params,
            co2_layout_fn=Action._co2Layout,
            glyph_bbox_fn=Action._glyphBbox,
        )

    @staticmethod
    def _foregroundMask(img: np.ndarray) -> np.ndarray:
        return element_mask_helpers.foregroundMaskImpl(img, cv2_module=cv2, np_module=np)

    @staticmethod
    def _circleFromForegroundMask(fg_mask: np.ndarray) -> tuple[float, float, float] | None:
        return element_mask_helpers.circleFromForegroundMaskImpl(
            fg_mask,
            cv2_module=cv2,
            np_module=np,
            math_module=math,
        )

    @staticmethod
    def _maskSupportsCircle(mask: np.ndarray | None) -> bool:
        return element_mask_helpers.maskSupportsCircleImpl(
            mask,
            mask_bbox_fn=Action._maskBbox,
            cv2_module=cv2,
            np_module=np,
            math_module=math,
        )

    @staticmethod
    def extractBadgeElementMask(img_orig: np.ndarray, params: dict, element: str) -> np.ndarray | None:
        return element_mask_helpers.extractBadgeElementMaskImpl(
            img_orig,
            params,
            element,
            element_region_mask_fn=Action._elementRegionMask,
            foreground_mask_fn=Action._foregroundMask,
            cv2_module=cv2,
            np_module=np,
        )

    @staticmethod
    def _elementOnlyParams(params: dict, element: str) -> dict:
        return element_error_metric_helpers.elementOnlyParamsImpl(params, element)

    @staticmethod
    def _maskedError(img_orig: np.ndarray, img_svg: np.ndarray, mask: np.ndarray | None) -> float:
        return element_error_metric_helpers.maskedErrorImpl(
            img_orig,
            img_svg,
            mask,
            cv2_module=cv2,
            np_module=np,
        )

    @staticmethod
    def _unionBboxFromMasks(mask_a: np.ndarray | None, mask_b: np.ndarray | None) -> tuple[int, int, int, int] | None:
        return element_error_metric_helpers.unionBboxFromMasksImpl(
            mask_a,
            mask_b,
            mask_bbox_fn=Action._maskBbox,
            np_module=np,
        )

    @staticmethod
    def _maskedUnionErrorInBbox(
        img_orig: np.ndarray,
        img_svg: np.ndarray,
        mask_orig: np.ndarray | None,
        mask_svg: np.ndarray | None,
    ) -> float:
        return element_error_metric_helpers.maskedUnionErrorInBboxImpl(
            img_orig,
            img_svg,
            mask_orig,
            mask_svg,
            cv2_module=cv2,
            np_module=np,
            union_bbox_from_masks_fn=Action._unionBboxFromMasks,
        )

    @staticmethod
    def _elementMatchError(
        img_orig: np.ndarray,
        img_svg: np.ndarray,
        params: dict,
        element: str,
        *,
        mask_orig: np.ndarray | None = None,
        mask_svg: np.ndarray | None = None,
        apply_circle_geometry_penalty: bool = True,
    ) -> float:
        return element_error_metric_helpers.elementMatchErrorImpl(
            img_orig,
            img_svg,
            params,
            element,
            mask_orig=mask_orig,
            mask_svg=mask_svg,
            apply_circle_geometry_penalty=apply_circle_geometry_penalty,
            cv2_module=cv2,
            np_module=np,
            math_module=math,
            extract_badge_element_mask_fn=Action.extractBadgeElementMask,
            masked_union_error_in_bbox_fn=Action._maskedUnionErrorInBbox,
            mask_centroid_radius_fn=Action._maskCentroidRadius,
        )

    @staticmethod
    def _captureCanonicalBadgeColors(params: dict) -> dict:
        return _captureCanonicalBadgeColors(params)

    @staticmethod
    def _applyCanonicalBadgeColors(params: dict) -> dict:
        return _applyCanonicalBadgeColors(params)

    @staticmethod
    def _circleBounds(params: dict, w: int, h: int) -> tuple[float, float, float, float, float, float]:
        return global_vector_optimization_helpers.circleBoundsImpl(
            params,
            w,
            h,
            max_circle_radius_inside_canvas_fn=Action._maxCircleRadiusInsideCanvas,
        )

    @staticmethod
    def _globalParameterVectorBounds(params: dict, w: int, h: int) -> dict[str, tuple[float, float, bool, str]]:
        return global_vector_optimization_helpers.globalParameterVectorBoundsImpl(
            params,
            w,
            h,
            circle_bounds_fn=Action._circle_bounds,
        )

    @staticmethod
    def _logGlobalParameterVector(logs: list[str], params: dict, w: int, h: int, *, label: str) -> None:
        global_vector_optimization_helpers.logGlobalParameterVectorImpl(
            logs,
            params,
            w,
            h,
            label=label,
            global_parameter_vector_cls=GlobalParameterVector,
            global_parameter_vector_bounds_fn=Action._global_parameter_vector_bounds,
        )

    @staticmethod
    def _stochasticSurvivorScalar(
        current_value: float,
        low: float,
        high: float,
        evaluate,
        *,
        snap,
        seed: int,
        iterations: int = 20,
    ) -> tuple[float, float, bool]:
        return circle_search_optimization_helpers.stochasticSurvivorScalarImpl(
            current_value,
            low,
            high,
            evaluate,
            snap=snap,
            seed=seed,
            make_rng_fn=Action._makeRng,
            clip_scalar_fn=Action._clipScalar,
            stochastic_seed_offset=Action.STOCHASTIC_SEED_OFFSET,
            iterations=iterations,
        )

    @staticmethod
    def _optimizeCirclePoseStochasticSurvivor(
        img_orig: np.ndarray,
        params: dict,
        logs: list[str],
        *,
        iterations: int = 24,
    ) -> bool:
        return circle_search_optimization_helpers.optimizeCirclePoseStochasticSurvivorImpl(
            img_orig,
            params,
            logs,
            snap_half_fn=Action._snapHalf,
            clip_scalar_fn=Action._clipScalar,
            make_rng_fn=Action._makeRng,
            circle_bounds_fn=Action._circleBounds,
            element_error_for_circle_pose_fn=Action._elementErrorForCirclePose,
            log_global_parameter_vector_fn=Action._logGlobalParameterVector,
            global_parameter_vector_cls=GlobalParameterVector,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            stochastic_run_seed=Action.STOCHASTIC_RUN_SEED,
            stochastic_seed_offset=Action.STOCHASTIC_SEED_OFFSET,
            iterations=iterations,
        )

    @staticmethod
    def _optimizeCirclePoseAdaptiveDomain(
        img_orig: np.ndarray,
        params: dict,
        logs: list[str],
        *,
        rounds: int = 4,
        samples_per_round: int = 18,
    ) -> bool:
        return circle_search_optimization_helpers.optimizeCirclePoseAdaptiveDomainImpl(
            img_orig,
            params,
            logs,
            snap_half_fn=Action._snapHalf,
            clip_scalar_fn=Action._clipScalar,
            make_rng_fn=Action._makeRng,
            circle_bounds_fn=Action._circleBounds,
            element_error_for_circle_pose_fn=Action._elementErrorForCirclePose,
            log_global_parameter_vector_fn=Action._logGlobalParameterVector,
            global_parameter_vector_cls=GlobalParameterVector,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            stochastic_run_seed=Action.STOCHASTIC_RUN_SEED,
            stochastic_seed_offset=Action.STOCHASTIC_SEED_OFFSET,
            rounds=rounds,
            samples_per_round=samples_per_round,
        )

    @staticmethod
    def _fullBadgeErrorForParams(img_orig: np.ndarray, params: dict) -> float:
        return global_search_optimization_helpers.fullBadgeErrorForParamsImpl(
            img_orig,
            params,
            fit_to_original_size_fn=Action._fitToOriginalSize,
            render_svg_to_numpy_fn=Action.renderSvgToNumpy,
            generate_badge_svg_fn=Action.generateBadgeSvg,
            calculate_error_fn=Action.calculateError,
        )

    @staticmethod
    def _optimizeGlobalParameterVectorSampling(
        img_orig: np.ndarray,
        params: dict,
        logs: list[str],
        *,
        rounds: int = 3,
        samples_per_round: int = 16,
    ) -> bool:
        return global_search_optimization_helpers.optimizeGlobalParameterVectorSamplingImpl(
            img_orig,
            params,
            logs,
            rounds=rounds,
            samples_per_round=samples_per_round,
            global_parameter_vector_cls=GlobalParameterVector,
            global_parameter_vector_bounds_fn=Action._globalParameterVectorBounds,
            clip_scalar_fn=Action._clip_scalar,
            snap_half_fn=Action._snap_half,
            make_rng_fn=Action._make_rng,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            full_badge_error_for_params_fn=Action._full_badge_error_for_params,
            log_global_parameter_vector_fn=Action._logGlobalParameterVector,
            stochastic_run_seed=Action.STOCHASTIC_RUN_SEED,
            stochastic_seed_offset=Action.STOCHASTIC_SEED_OFFSET,
        )

    @staticmethod
    def _enforceSemanticConnectorExpectation(base_name: str, semantic_elements: list[str], params: dict, w: int, h: int) -> dict:
        """Restore mandatory connector geometry for directional semantic badges."""
        return semantic_connector_helpers.enforceSemanticConnectorExpectationImpl(
            base_name,
            semantic_elements,
            params,
            normalize_base_name_fn=getBaseNameFromFile,
            enforce_left_fn=lambda p: Action._enforceLeftArmBadgeGeometry(p, w, h),
            enforce_right_fn=lambda p: Action._enforceRightArmBadgeGeometry(p, w, h),
            enforce_top_fn=lambda p: semantic_connector_helpers.enforceTopStemBadgeGeometryImpl(
                p,
                h=h,
                ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
            ),
        )

    @staticmethod
    def _elementWidthKeyAndBounds(
        element: str, params: dict, w: int, h: int, img_orig: np.ndarray | None = None
    ) -> tuple[str, float, float] | None:
        return width_optimization_helpers.elementWidthKeyAndBoundsImpl(
            element,
            params,
            w,
            h,
            ac08_stroke_width_px=Action.AC08_STROKE_WIDTH_PX,
            extract_badge_element_mask_fn=Action.extract_badge_element_mask,
            mask_bbox_fn=Action._maskBbox,
            img_orig=img_orig,
        )

    @staticmethod
    def _elementErrorForWidth(img_orig: np.ndarray, params: dict, element: str, width_value: float) -> float:
        return width_optimization_helpers.elementErrorForWidthImpl(
            img_orig,
            params,
            element,
            width_value,
            element_width_key_and_bounds_fn=lambda elem, p, width, height, image: Action._elementWidthKeyAndBounds(
                elem,
                p,
                width,
                height,
                img_orig=image,
            ),
            clip_scalar_fn=Action._clip_scalar,
            generate_badge_svg_fn=Action.generate_badge_svg,
            element_only_params_fn=Action._elementOnlyParams,
            fit_to_original_size_fn=Action._fit_to_original_size,
            render_svg_to_numpy_fn=Action.render_svg_to_numpy,
            extract_badge_element_mask_fn=Action.extract_badge_element_mask,
            element_match_error_fn=Action._element_match_error,
        )

    @staticmethod
    def _elementErrorForCircleRadius(img_orig: np.ndarray, params: dict, radius_value: float) -> float:
        return circle_radius_optimization_helpers.elementErrorForCircleRadiusImpl(
            img_orig,
            params,
            radius_value,
            clip_scalar_fn=Action._clip_scalar,
            clamp_circle_inside_canvas_fn=Action._clampCircleInsideCanvas,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            generate_badge_svg_fn=Action.generate_badge_svg,
            element_only_params_fn=Action._elementOnlyParams,
            fit_to_original_size_fn=Action._fit_to_original_size,
            render_svg_to_numpy_fn=Action.render_svg_to_numpy,
            extract_badge_element_mask_fn=Action.extract_badge_element_mask,
            element_match_error_fn=Action._element_match_error,
        )

    @staticmethod
    def _fullBadgeErrorForCircleRadius(img_orig: np.ndarray, params: dict, radius_value: float) -> float:
        """Evaluate the full SVG roundtrip error for a specific circle radius."""
        return circle_radius_optimization_helpers.fullBadgeErrorForCircleRadiusImpl(
            img_orig,
            params,
            radius_value,
            clip_scalar_fn=Action._clipScalar,
            clamp_circle_inside_canvas_fn=Action._clampCircleInsideCanvas,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            generate_badge_svg_fn=Action.generateBadgeSvg,
            fit_to_original_size_fn=Action._fitToOriginalSize,
            render_svg_to_numpy_fn=Action.renderSvgToNumpy,
            calculate_error_fn=Action.calculateError,
        )

    @staticmethod
    def _selectCircleRadiusPlateauCandidate(
        img_orig: np.ndarray,
        params: dict,
        evaluations: dict[float, float],
        current_radius: float,
    ) -> tuple[float, float, float]:
        """Pick a stable radius from a near-optimal plateau instead of a noisy local minimum."""
        return circle_radius_optimization_helpers.selectCircleRadiusPlateauCandidateImpl(
            img_orig,
            params,
            evaluations,
            current_radius,
            clip_scalar_fn=Action._clipScalar,
            snap_half_fn=Action._snapHalf,
            full_badge_error_for_circle_radius_fn=Action._full_badge_error_for_circle_radius,
            element_error_for_circle_radius_fn=Action._element_error_for_circle_radius,
        )


    @staticmethod
    def _elementErrorForCirclePose(
        img_orig: np.ndarray,
        params: dict,
        *,
        cx_value: float,
        cy_value: float,
        radius_value: float,
    ) -> float:
        return circle_geometry_optimization_helpers.elementErrorForCirclePoseImpl(
            img_orig,
            params,
            cx_value=cx_value,
            cy_value=cy_value,
            radius_value=radius_value,
            snap_half_fn=Action._snapHalf,
            clip_scalar_fn=Action._clipScalar,
            clamp_circle_inside_canvas_fn=Action._clampCircleInsideCanvas,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            generate_badge_svg_fn=Action.generate_badge_svg,
            element_only_params_fn=Action._element_only_params,
            fit_to_original_size_fn=Action._fit_to_original_size,
            render_svg_to_numpy_fn=Action.render_svg_to_numpy,
            extract_badge_element_mask_fn=Action.extract_badge_element_mask,
            element_match_error_fn=Action._element_match_error,
        )

    @staticmethod
    def _reanchorArmToCircleEdge(params: dict, radius: float) -> None:
        circle_geometry_optimization_helpers.reanchorArmToCircleEdgeImpl(params, radius)

    @staticmethod
    def _optimizeCircleCenterBracket(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        return geometry_bracket_helpers.optimizeCircleCenterBracketImpl(
            img_orig,
            params,
            logs,
            snap_half_fn=Action._snapHalf,
            clip_scalar_fn=Action._clipScalar,
            element_error_for_circle_radius_fn=Action._elementErrorForCircleRadius,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
        )

    @staticmethod
    def _optimizeCircleRadiusBracket(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        return geometry_bracket_helpers.optimizeCircleRadiusBracketImpl(
            img_orig,
            params,
            logs,
            clip_scalar_fn=Action._clip_scalar,
            snap_half_fn=Action._snap_half,
            element_error_for_circle_radius_fn=Action._element_error_for_circle_radius,
            select_circle_radius_plateau_candidate_fn=Action._select_circle_radius_plateau_candidate,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
        )

    @staticmethod
    def _optimizeCirclePoseMultistart(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        return circle_pose_optimization_helpers.optimizeCirclePoseMultistartImpl(
            img_orig,
            params,
            logs,
            clip_scalar_fn=Action._clipScalar,
            snap_half_fn=Action._snapHalf,
            circle_bounds_fn=Action._circleBounds,
            element_error_for_circle_pose_fn=Action._element_error_for_circle_pose,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            optimize_circle_pose_adaptive_domain_fn=Action._optimizeCirclePoseAdaptiveDomain,
            optimize_circle_pose_stochastic_survivor_fn=Action._optimizeCirclePoseStochasticSurvivor,
        )

    @staticmethod
    def _elementErrorForExtent(img_orig: np.ndarray, params: dict, element: str, extent_value: float) -> float:
        return geometry_optimization_helpers.elementErrorForExtentImpl(
            img_orig,
            params,
            element,
            extent_value,
            clip_scalar_fn=Action._clipScalar,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
            generate_badge_svg_fn=Action.generateBadgeSvg,
            element_only_params_fn=Action._elementOnlyParams,
            fit_to_original_size_fn=Action._fitToOriginalSize,
            render_svg_to_numpy_fn=Action.renderSvgToNumpy,
            extract_badge_element_mask_fn=Action.extract_badge_element_mask,
            element_match_error_fn=Action._element_match_error,
        )

    @staticmethod
    def _optimizeElementExtentBracket(img_orig: np.ndarray, params: dict, element: str, logs: list[str]) -> bool:
        return geometry_optimization_helpers.optimizeElementExtentBracketImpl(
            img_orig,
            params,
            element,
            logs,
            clip_scalar_fn=Action._clipScalar,
            snap_half_fn=Action._snapHalf,
            element_error_for_extent_fn=Action._element_error_for_extent,
            argmin_index_fn=Action._argminIndex,
            stochastic_survivor_scalar_fn=Action._stochasticSurvivorScalar,
            reanchor_arm_to_circle_edge_fn=Action._reanchorArmToCircleEdge,
        )

    @staticmethod
    def _optimizeElementWidthBracket(img_orig: np.ndarray, params: dict, element: str, logs: list[str]) -> bool:
        h, w = img_orig.shape[:2]
        return geometry_optimization_helpers.optimizeElementWidthBracketImpl(
            img_orig,
            params,
            element,
            logs,
            element_width_key_and_bounds_fn=lambda elem, p, width, height: Action._elementWidthKeyAndBounds(
                elem,
                p,
                width,
                height,
                img_orig=img_orig,
            ),
            snap_half_fn=Action._snapHalf,
            clip_scalar_fn=Action._clipScalar,
            element_error_for_width_fn=Action._elementErrorForWidth,
            argmin_index_fn=Action._argminIndex,
            stochastic_survivor_scalar_fn=Action._stochasticSurvivorScalar,
            snap_int_px_fn=lambda value: Action._snapIntPx(value, minimum=1.0),
        )


    @staticmethod
    def _elementColorKeys(element: str, params: dict) -> list[str]:
        return color_optimization_helpers.elementColorKeysImpl(element, params)

    @staticmethod
    def _elementErrorForColor(
        img_orig: np.ndarray,
        params: dict,
        element: str,
        color_key: str,
        color_value: int,
        mask_orig: np.ndarray,
    ) -> float:
        return color_optimization_helpers.elementErrorForColorImpl(
            img_orig,
            params,
            element,
            color_key,
            color_value,
            mask_orig,
            clip_scalar_fn=Action._clip_scalar,
            generate_badge_svg_fn=Action.generate_badge_svg,
            element_only_params_fn=Action._elementOnlyParams,
            fit_to_original_size_fn=Action._fit_to_original_size,
            render_svg_to_numpy_fn=Action.render_svg_to_numpy,
            masked_union_error_in_bbox_fn=Action._masked_union_error_in_bbox,
            element_match_error_fn=Action._element_match_error,
        )

    @staticmethod
    def _optimizeElementColorBracket(
        img_orig: np.ndarray,
        params: dict,
        element: str,
        mask_orig: np.ndarray,
        logs: list[str],
    ) -> bool:
        return color_optimization_helpers.optimizeElementColorBracketImpl(
            img_orig,
            params,
            element,
            mask_orig,
            logs,
            mean_gray_for_mask_fn=Action._mean_gray_for_mask,
            clip_scalar_fn=Action._clip_scalar,
            element_color_keys_fn=Action._elementColorKeys,
            element_error_for_color_fn=Action._element_error_for_color,
            argmin_index_fn=Action._argminIndex,
            stochastic_survivor_scalar_fn=Action._stochasticSurvivorScalar,
        )

    @staticmethod
    def _refineStemGeometryFromMasks(params: dict, mask_orig: np.ndarray, mask_svg: np.ndarray, w: int) -> tuple[bool, str | None]:
        return element_validation_helpers.refineStemGeometryFromMasksImpl(
            params,
            mask_orig,
            mask_svg,
            w,
            mask_bbox_fn=Action._maskBbox,
            estimate_vertical_stem_from_mask_fn=Action._estimateVerticalStemFromMask,
            clip_scalar_fn=Action._clipScalar,
            snap_int_px_fn=Action._snapIntPx,
            snap_half_fn=Action._snapHalf,
        )

    @staticmethod
    def _expectedSemanticPresence(semantic_elements: list[str]) -> dict[str, bool]:
        return semantic_validation_helpers.expectedSemanticPresenceImpl(semantic_elements)

    @staticmethod
    def _semanticPresenceMismatches(expected: dict[str, bool], observed: dict[str, bool]) -> list[str]:
        return semantic_validation_helpers.semanticPresenceMismatchesImpl(expected, observed)

    @staticmethod
    def _detectSemanticPrimitives(
        img_orig: np.ndarray,
        badge_params: dict | None = None,
    ) -> dict[str, bool | int | str]:
        """Detect coarse semantic primitives directly from the raw bitmap.

        This guard is intentionally conservative: it should flag obvious non-badge
        inserts (e.g. arbitrary crossing lines) before we accept semantic badge
        reconstruction from templated defaults.
        """
        return semantic_checks_helpers.detectSemanticPrimitivesImpl(
            img_orig,
            badge_params,
            cv2_module=cv2,
            np_module=np,
            foreground_mask_fn=Action._foregroundMask,
            circle_from_foreground_mask_fn=Action._circleFromForegroundMask,
            clip_scalar_fn=Action._clipScalar,
        )

    @staticmethod
    def validateSemanticDescriptionAlignment(
        img_orig: np.ndarray,
        semantic_elements: list[str],
        badge_params: dict,
    ) -> list[str]:
        return semantic_checks_helpers.validateSemanticDescriptionAlignmentImpl(
            img_orig,
            semantic_elements,
            badge_params,
            cv2_module=cv2,
            np_module=np,
            expected_presence_fn=Action._expectedSemanticPresence,
            semantic_presence_mismatches_fn=Action._semanticPresenceMismatches,
            detect_primitives_fn=Action._detect_semantic_primitives,
            extract_mask_fn=Action.extract_badge_element_mask,
            mask_bbox_fn=Action._mask_bbox,
            mask_supports_circle_fn=Action._mask_supports_circle,
            foreground_mask_fn=Action._foregroundMask,
        )

    @staticmethod
    def validateBadgeByElements(
        img_orig: np.ndarray,
        params: dict,
        *,
        max_rounds: int = 6,
        debug_out_dir: str | None = None,
        apply_circle_geometry_penalty: bool = True,
        stop_when_error_below_threshold: bool = False,
    ) -> list[str]:
        return element_validation_helpers.validateBadgeByElementsImpl(
            img_orig,
            params,
            max_rounds=max_rounds,
            debug_out_dir=debug_out_dir,
            apply_circle_geometry_penalty=apply_circle_geometry_penalty,
            stop_when_error_below_threshold=stop_when_error_below_threshold,
            cv2_module=cv2,
            copy_module=copy,
            math_module=math,
            os_module=os,
            time_module=time,
            generate_badge_svg_fn=Action.generate_badge_svg,
            fit_to_original_size_fn=Action._fit_to_original_size,
            render_svg_to_numpy_fn=Action.render_svg_to_numpy,
            create_diff_image_fn=Action.create_diff_image,
            write_debug_image_fn=cv2.imwrite,
            element_only_params_fn=Action._elementOnlyParams,
            extract_badge_element_mask_fn=Action.extract_badge_element_mask,
            element_region_mask_fn=Action._elementRegionMask,
            element_match_error_fn=Action._element_match_error,
            refine_stem_geometry_from_masks_fn=Action._refineStemGeometryFromMasks,
            optimize_element_width_bracket_fn=Action._optimize_element_width_bracket,
            optimize_element_extent_bracket_fn=Action._optimize_element_extent_bracket,
            optimize_circle_center_bracket_fn=Action._optimize_circle_center_bracket,
            optimize_circle_radius_bracket_fn=Action._optimize_circle_radius_bracket,
            optimize_global_parameter_vector_sampling_fn=Action._optimize_global_parameter_vector_sampling,
            calculate_error_fn=Action.calculate_error,
            activate_ac08_adaptive_locks_fn=Action._activateAc08AdaptiveLocks,
            release_ac08_adaptive_locks_fn=Action._release_ac08_adaptive_locks,
            optimize_element_color_bracket_fn=Action._optimize_element_color_bracket,
            apply_canonical_badge_colors_fn=Action._apply_canonical_badge_colors,
        )


def _semanticQualityFlags(base_name: str, validation_logs: list[str]) -> list[str]:
    return imageCompositeConverterRemaining_helpers._semanticQualityFlags(base_name, validation_logs)


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
    previous_bindings = _syncRemainingRuntimeBindings()
    try:
        return imageCompositeConverterRemaining_helpers.runIterationPipeline(img_path, csv_path, max_iterations, svg_out_dir, diff_out_dir, reports_out_dir, debug_ac0811_dir, debug_element_diff_dir, badge_validation_rounds)
    finally:
        _restoreRemainingRuntimeBindings(previous_bindings)


def _extractRefParts(name: str) -> tuple[str, int] | None:
    return imageCompositeConverterRemaining_helpers._extractRefParts(name)


def _normalizeRangeToken(value: str) -> str:
    return imageCompositeConverterRemaining_helpers._normalizeRangeToken(value)


def _normalizeExplicitRangeToken(value: str) -> str:
    return imageCompositeConverterRemaining_helpers._normalizeExplicitRangeToken(value)


def _isExplicitSizeVariantToken(token: str) -> bool:
    return imageCompositeConverterRemaining_helpers._isExplicitSizeVariantToken(token)


def _compactRangeToken(value: str) -> str:
    return imageCompositeConverterRemaining_helpers._compactRangeToken(value)


def _sharedPartialRangeToken(start_ref: str, end_ref: str) -> str:
    return imageCompositeConverterRemaining_helpers._sharedPartialRangeToken(start_ref, end_ref)


def _matchesPartialRangeToken(filename: str, start_ref: str, end_ref: str) -> bool:
    return imageCompositeConverterRemaining_helpers._matchesPartialRangeToken(filename, start_ref, end_ref)


def _extractSymbolFamily(name: str) -> str | None:
    return imageCompositeConverterRemaining_helpers._extractSymbolFamily(name)


def _matchesExactPrefixFilter(filename: str, start_ref: str, end_ref: str) -> bool:
    return imageCompositeConverterRemaining_helpers._matchesExactPrefixFilter(filename, start_ref, end_ref)


def _inRequestedRange(filename: str, start_ref: str, end_ref: str) -> bool:
    return imageCompositeConverterRemaining_helpers._inRequestedRange(filename, start_ref, end_ref)


def _conversionRandom() -> random.Random:
    return imageCompositeConverterRemaining_helpers._conversionRandom()


def _writeIterationLogAndCollectSemanticResults(
    files: list[str],
    result_map: dict[str, dict[str, object]],
    log_path: str,
) -> list[dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._writeIterationLogAndCollectSemanticResults(files, result_map, log_path)


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
    return imageCompositeConverterRemaining_helpers._runPostConversionReporting(folder_path=folder_path, csv_path=csv_path, iterations=iterations, svg_out_dir=svg_out_dir, diff_out_dir=diff_out_dir, reports_out_dir=reports_out_dir, normalized_selected_variants=normalized_selected_variants, result_map=result_map)


def _defaultConvertedSymbolsRoot() -> str:
    return imageCompositeConverterRemaining_helpers._defaultConvertedSymbolsRoot()


def _convertedSvgOutputDir(output_root: str) -> str:
    return imageCompositeConverterRemaining_helpers._convertedSvgOutputDir(output_root)


def _readValidationLogDetails(log_path: str) -> dict[str, str]:
    return imageCompositeConverterRemaining_helpers._readValidationLogDetails(log_path)


def _writeBatchFailureSummary(reports_out_dir: str, failures: list[dict[str, str]]) -> None:
    return imageCompositeConverterRemaining_helpers._writeBatchFailureSummary(reports_out_dir, failures)


def _writeStrategySwitchTemplateTransfersReport(
    reports_out_dir: str,
    strategy_rows: list[dict[str, object]],
) -> None:
    return imageCompositeConverterRemaining_helpers._writeStrategySwitchTemplateTransfersReport(reports_out_dir, strategy_rows)



def _collectDescriptionFragments(raw_desc: dict[str, str], base_name: str, img_filename: str) -> list[dict[str, str]]:
    return imageCompositeConverterRemaining_helpers._collectDescriptionFragments(raw_desc, base_name, img_filename)


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
    return imageCompositeConverterRemaining_helpers._semanticAuditRecord(base_name=base_name, filename=filename, description_fragments=description_fragments, semantic_elements=semantic_elements, status=status, mismatch_reasons=mismatch_reasons, semantic_priority_order=semantic_priority_order, semantic_conflicts=semantic_conflicts, semantic_sources=semantic_sources)


def _writeSemanticAuditReport(reports_out_dir: str, audit_rows: list[dict[str, object]]) -> None:
    return imageCompositeConverterRemaining_helpers._writeSemanticAuditReport(reports_out_dir, audit_rows)


def _diffOutputDir(output_root: str) -> str:
    return imageCompositeConverterRemaining_helpers._diffOutputDir(output_root)


def _reportsOutputDir(output_root: str) -> str:
    return imageCompositeConverterRemaining_helpers._reportsOutputDir(output_root)


def _isSemanticTemplateVariant(base_name: str, params: dict[str, object] | None = None) -> bool:
    return imageCompositeConverterRemaining_helpers._isSemanticTemplateVariant(base_name, params)


def _loadExistingConversionRows(output_root: str, folder_path: str) -> list[dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._loadExistingConversionRows(output_root, folder_path)


def _sniffRasterSize(path: str | Path) -> tuple[int, int]:
    return imageCompositeConverterRemaining_helpers._sniffRasterSize(path)


def _svgHrefMimeType(path: str | Path) -> str:
    return imageCompositeConverterRemaining_helpers._svgHrefMimeType(path)


def _renderEmbeddedRasterSvg(input_path: str | Path) -> str:
    return imageCompositeConverterRemaining_helpers._renderEmbeddedRasterSvg(input_path)


def _qualityConfigPath(reports_out_dir: str) -> str:
    return imageCompositeConverterRemaining_helpers._qualityConfigPath(reports_out_dir)


def _loadQualityConfig(reports_out_dir: str) -> dict[str, object]:
    return imageCompositeConverterRemaining_helpers._loadQualityConfig(reports_out_dir)


def _writeQualityConfig(
    reports_out_dir: str,
    *,
    allowed_error_per_pixel: float,
    skipped_variants: list[str],
    source: str,
) -> None:
    return imageCompositeConverterRemaining_helpers._writeQualityConfig(reports_out_dir, allowed_error_per_pixel=allowed_error_per_pixel, skipped_variants=skipped_variants, source=source)


def _resolveAllowedErrorPerPixel(
    current_rows: list[dict[str, object]],
    cfg: dict[str, object],
) -> tuple[float, str, float, float]:
    return imageCompositeConverterRemaining_helpers._resolveAllowedErrorPerPixel(current_rows, cfg)


def _qualitySortKey(row: dict[str, object]) -> float:
    return imageCompositeConverterRemaining_helpers._qualitySortKey(row)




def _computeSuccessfulConversionsErrorThreshold(
    rows: list[dict[str, object]],
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> float:
    return imageCompositeConverterRemaining_helpers._computeSuccessfulConversionsErrorThreshold(rows, successful_variants)


def _selectMiddleLowerTercile(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._selectMiddleLowerTercile(rows)


def _selectOpenQualityCases(
    rows: list[dict[str, object]],
    *,
    allowed_error_per_pixel: float,
    skip_variants: set[str] | None = None,
) -> list[dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._selectOpenQualityCases(rows, allowed_error_per_pixel=allowed_error_per_pixel, skip_variants=skip_variants)


def _iterationStrategyForPass(pass_idx: int, base_iterations: int) -> tuple[int, int]:
    return imageCompositeConverterRemaining_helpers._iterationStrategyForPass(pass_idx, base_iterations)


def _adaptiveIterationBudgetForQualityRow(row: dict[str, object], planned_budget: int) -> int:
    return imageCompositeConverterRemaining_helpers._adaptiveIterationBudgetForQualityRow(row, planned_budget)


def _writeQualityPassReport(
    reports_out_dir: str,
    pass_rows: list[dict[str, object]],
) -> None:
    return imageCompositeConverterRemaining_helpers._writeQualityPassReport(reports_out_dir, pass_rows)


def _evaluateQualityPassCandidate(
    old_row: dict[str, object],
    new_row: dict[str, object],
) -> tuple[bool, str, float, float, float, float]:
    return imageCompositeConverterRemaining_helpers._evaluateQualityPassCandidate(old_row, new_row)


def _extractSvgInner(svg_text: str) -> str:
    return imageCompositeConverterRemaining_helpers._extractSvgInner(svg_text)


def _buildTransformedSvgFromTemplate(
    template_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
    scale: float,
) -> str:
    return imageCompositeConverterRemaining_helpers._buildTransformedSvgFromTemplate(template_svg_text, target_w, target_h, rotation_deg=rotation_deg, scale=scale)


def _templateTransferScaleCandidates(base_scale: float) -> list[float]:
    return imageCompositeConverterRemaining_helpers._templateTransferScaleCandidates(base_scale)


def _estimateTemplateTransferScale(
    img_orig: np.ndarray,
    donor_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
) -> float | None:
    return imageCompositeConverterRemaining_helpers._estimateTemplateTransferScale(img_orig, donor_svg_text, target_w, target_h, rotation_deg=rotation_deg)


def _templateTransferTransformCandidates(
    target_variant: str,
    donor_variant: str,
    *,
    estimated_scale_by_rotation: dict[int, float] | None = None,
) -> list[tuple[int, float]]:
    return imageCompositeConverterRemaining_helpers._templateTransferTransformCandidates(target_variant, donor_variant, estimated_scale_by_rotation=estimated_scale_by_rotation)


def _rankTemplateTransferDonors(
    target_row: dict[str, object],
    donor_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._rankTemplateTransferDonors(target_row, donor_rows)


def _templateTransferDonorFamilyCompatible(
    target_base: str,
    donor_base: str,
    *,
    documented_alias_refs: set[str] | None = None,
) -> bool:
    return imageCompositeConverterRemaining_helpers._templateTransferDonorFamilyCompatible(target_base, donor_base, documented_alias_refs=documented_alias_refs)




def _semanticTransferRotations(target_params: dict[str, object], donor_params: dict[str, object]) -> tuple[int, ...]:
    return imageCompositeConverterRemaining_helpers._semanticTransferRotations(target_params, donor_params)






def _semanticTransferIsCompatible(target_params: dict[str, object], donor_params: dict[str, object]) -> bool:
    return imageCompositeConverterRemaining_helpers._semanticTransferIsCompatible(target_params, donor_params)


def _connectorArmDirection(params: dict[str, object]) -> int | None:
    return imageCompositeConverterRemaining_helpers._connectorArmDirection(params)


def _connectorStemDirection(params: dict[str, object]) -> int | None:
    return imageCompositeConverterRemaining_helpers._connectorStemDirection(params)


def _semanticTransferScaleCandidates(base_scale: float) -> list[float]:
    return imageCompositeConverterRemaining_helpers._semanticTransferScaleCandidates(base_scale)

def _semanticTransferBadgeParams(
    donor_params: dict[str, object],
    target_params: dict[str, object],
    *,
    target_w: int,
    target_h: int,
    rotation_deg: int,
    scale: float,
) -> dict[str, object]:
    return imageCompositeConverterRemaining_helpers._semanticTransferBadgeParams(donor_params, target_params, target_w=target_w, target_h=target_h, rotation_deg=rotation_deg, scale=scale)

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
    return imageCompositeConverterRemaining_helpers._tryTemplateTransfer(target_row=target_row, donor_rows=donor_rows, folder_path=folder_path, svg_out_dir=svg_out_dir, diff_out_dir=diff_out_dir, rng=rng, deterministic_order=deterministic_order)


def _runEmbeddedRasterFallback(
    *,
    files: list[str],
    folder_path: str,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str,
) -> None:
    return imageCompositeConverterRemaining_helpers._runEmbeddedRasterFallback(files=files, folder_path=folder_path, svg_out_dir=svg_out_dir, diff_out_dir=diff_out_dir, reports_out_dir=reports_out_dir)


def _listRequestedImageFiles(
    folder_path: str,
    start_ref: str,
    end_ref: str,
    *,
    selected_variants: set[str] | None,
) -> tuple[set[str], list[str]]:
    return imageCompositeConverterRemaining_helpers._listRequestedImageFiles(folder_path, start_ref, end_ref, selected_variants=selected_variants)


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
    previous_bindings = _syncRemainingRuntimeBindings()
    try:
        return imageCompositeConverterRemaining_helpers.convertRange(folder_path, csv_path, iterations, start_ref, end_ref, debug_ac0811_dir, debug_element_diff_dir, output_root, selected_variants, deterministic_order)
    finally:
        _restoreRemainingRuntimeBindings(previous_bindings)


def _readSvgGeometry(svg_path: str) -> tuple[int, int, dict] | None:
    return imageCompositeConverterRemaining_helpers._readSvgGeometry(svg_path)


def _normalizedGeometrySignature(w: int, h: int, params: dict) -> dict[str, float]:
    return imageCompositeConverterRemaining_helpers._normalizedGeometrySignature(w, h, params)


def _maxSignatureDelta(sig_a: dict[str, float], sig_b: dict[str, float]) -> float:
    return imageCompositeConverterRemaining_helpers._maxSignatureDelta(sig_a, sig_b)


def _needsLargeCircleOverflowGuard(params: dict) -> bool:
    return imageCompositeConverterRemaining_helpers._needsLargeCircleOverflowGuard(params)


def _scaleBadgeParams(
    anchor: dict,
    anchor_w: int,
    anchor_h: int,
    target_w: int,
    target_h: int,
    *,
    target_variant: str = "",
) -> dict:
    return imageCompositeConverterRemaining_helpers._scaleBadgeParams(anchor, anchor_w, anchor_h, target_w, target_h, target_variant=target_variant)


def _harmonizationAnchorPriority(suffix: str, prefer_large: bool) -> int:
    return imageCompositeConverterRemaining_helpers._harmonizationAnchorPriority(suffix, prefer_large)


def _clipGray(value: float) -> int:
    return imageCompositeConverterRemaining_helpers._clipGray(value)


def _captureCanonicalBadgeColors(params: dict) -> dict:
    return imageCompositeConverterRemaining_helpers._captureCanonicalBadgeColors(params)


def _applyCanonicalBadgeColors(params: dict) -> dict:
    return imageCompositeConverterRemaining_helpers._applyCanonicalBadgeColors(params)


def _familyHarmonizedBadgeColors(variant_rows: list[dict[str, object]]) -> dict[str, int]:
    return imageCompositeConverterRemaining_helpers._familyHarmonizedBadgeColors(variant_rows)


def _harmonizeSemanticSizeVariants(
    results: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
) -> None:
    return imageCompositeConverterRemaining_helpers._harmonizeSemanticSizeVariants(results, folder_path, svg_out_dir, reports_out_dir)


def _writeAc08RegressionManifest(
    reports_out_dir: str,
    *,
    folder_path: str,
    csv_path: str,
    iterations: int,
    selected_variants: list[str],
) -> None:
    return imageCompositeConverterRemaining_helpers._writeAc08RegressionManifest(reports_out_dir, folder_path=folder_path, csv_path=csv_path, iterations=iterations, selected_variants=selected_variants)


def _summarizePreviousGoodAc08Variants(reports_out_dir: str) -> dict[str, object]:
    return imageCompositeConverterRemaining_helpers._summarizePreviousGoodAc08Variants(reports_out_dir)


def _writeAc08SuccessCriteriaReport(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
) -> dict[str, object] | None:
    return imageCompositeConverterRemaining_helpers._writeAc08SuccessCriteriaReport(reports_out_dir, selected_variants=selected_variants)


def _emitAc08SuccessGateStatus(ac08_success_gate: dict[str, object] | None) -> None:
    return imageCompositeConverterRemaining_helpers._emitAc08SuccessGateStatus(ac08_success_gate)


def _writeAc08WeakFamilyStatusReport(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
    ranking_threshold: float = 18.0,
) -> None:
    return imageCompositeConverterRemaining_helpers._writeAc08WeakFamilyStatusReport(reports_out_dir, selected_variants=selected_variants, ranking_threshold=ranking_threshold)


def _writePixelDelta2Ranking(folder_path: str, svg_out_dir: str, reports_out_dir: str, threshold: float = 18.0) -> None:
    return imageCompositeConverterRemaining_helpers._writePixelDelta2Ranking(folder_path, svg_out_dir, reports_out_dir, threshold)


def _loadIterationLogRows(reports_out_dir: str) -> dict[str, dict[str, str]]:
    return imageCompositeConverterRemaining_helpers._loadIterationLogRows(reports_out_dir)


def _findImagePathByVariant(folder_path: str, variant: str) -> str | None:
    return imageCompositeConverterRemaining_helpers._findImagePathByVariant(folder_path, variant)


def collectSuccessfulConversionQualityMetrics(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> list[dict[str, object]]:
    return imageCompositeConverterRemaining_helpers.collectSuccessfulConversionQualityMetrics(folder_path, svg_out_dir, reports_out_dir, successful_variants)


def _successfulConversionMetricsAvailable(metrics: dict[str, object]) -> bool:
    return imageCompositeConverterRemaining_helpers._successfulConversionMetricsAvailable(metrics)


def _parseSuccessfulConversionManifestLine(raw_line: str) -> tuple[str, dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._parseSuccessfulConversionManifestLine(raw_line)


def _readSuccessfulConversionManifestMetrics(manifest_path: Path) -> dict[str, dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._readSuccessfulConversionManifestMetrics(manifest_path)


def _successfulConversionSnapshotDir(reports_out_dir: str) -> Path:
    return imageCompositeConverterRemaining_helpers._successfulConversionSnapshotDir(reports_out_dir)


def _successfulConversionSnapshotPaths(reports_out_dir: str, variant: str) -> dict[str, Path]:
    return imageCompositeConverterRemaining_helpers._successfulConversionSnapshotPaths(reports_out_dir, variant)


def _restoreSuccessfulConversionSnapshot(variant: str, svg_out_dir: str, reports_out_dir: str) -> bool:
    return imageCompositeConverterRemaining_helpers._restoreSuccessfulConversionSnapshot(variant, svg_out_dir, reports_out_dir)


def _storeSuccessfulConversionSnapshot(variant: str, metrics: dict[str, object], svg_out_dir: str, reports_out_dir: str) -> None:
    return imageCompositeConverterRemaining_helpers._storeSuccessfulConversionSnapshot(variant, metrics, svg_out_dir, reports_out_dir)


def _isSuccessfulConversionCandidateBetter(
    previous_metrics: dict[str, object] | None,
    candidate_metrics: dict[str, object],
) -> bool:
    return imageCompositeConverterRemaining_helpers._isSuccessfulConversionCandidateBetter(previous_metrics, candidate_metrics)


def _mergeSuccessfulConversionMetrics(
    baseline: dict[str, object],
    override: dict[str, object],
) -> dict[str, object]:
    return imageCompositeConverterRemaining_helpers._mergeSuccessfulConversionMetrics(baseline, override)


def _formatSuccessfulConversionManifestLine(existing_line: str, metrics: dict[str, object]) -> str:
    return imageCompositeConverterRemaining_helpers._formatSuccessfulConversionManifestLine(existing_line, metrics)




def _conversionBestlistManifestPath(reports_out_dir: str) -> Path:
    return imageCompositeConverterRemaining_helpers._conversionBestlistManifestPath(reports_out_dir)


def _readConversionBestlistMetrics(manifest_path: Path, svg_out_dir: str) -> dict[str, dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._readConversionBestlistMetrics(manifest_path, svg_out_dir)


def _writeConversionBestlistMetrics(manifest_path: Path, rows: dict[str, dict[str, object]]) -> None:
    return imageCompositeConverterRemaining_helpers._writeConversionBestlistMetrics(manifest_path, rows)


def _storeConversionBestlistSnapshot(variant: str, row: dict[str, object], svg_out_dir: str, reports_out_dir: str) -> None:
    return imageCompositeConverterRemaining_helpers._storeConversionBestlistSnapshot(variant, row, svg_out_dir, reports_out_dir)


def _restoreConversionBestlistSnapshot(variant: str, svg_out_dir: str, reports_out_dir: str) -> dict[str, object] | None:
    return imageCompositeConverterRemaining_helpers._restoreConversionBestlistSnapshot(variant, svg_out_dir, reports_out_dir)


def _isConversionBestlistCandidateBetter(previous_row: dict[str, object] | None, candidate_row: dict[str, object]) -> bool:
    return imageCompositeConverterRemaining_helpers._isConversionBestlistCandidateBetter(previous_row, candidate_row)


def _chooseConversionBestlistRow(
    candidate_row: dict[str, object],
    previous_row: dict[str, object] | None,
    restored_row: dict[str, object] | None,
) -> dict[str, object]:
    return imageCompositeConverterRemaining_helpers._chooseConversionBestlistRow(candidate_row, previous_row, restored_row)

def _latestFailedConversionManifestEntry(reports_out_dir: str) -> dict[str, object] | None:
    return imageCompositeConverterRemaining_helpers._latestFailedConversionManifestEntry(reports_out_dir)


def updateSuccessfulConversionsManifestWithMetrics(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    manifest_path: Path | None = None,
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    return imageCompositeConverterRemaining_helpers.updateSuccessfulConversionsManifestWithMetrics(folder_path, svg_out_dir, reports_out_dir, manifest_path, successful_variants)

def _sortedSuccessfulConversionMetricsRows(
    metrics: list[dict[str, object]],
) -> list[dict[str, object]]:
    return imageCompositeConverterRemaining_helpers._sortedSuccessfulConversionMetricsRows(metrics)


def _writeSuccessfulConversionCsvTable(csv_path: str | os.PathLike[str], metrics: list[dict[str, object]]) -> str:
    return imageCompositeConverterRemaining_helpers._writeSuccessfulConversionCsvTable(csv_path, metrics)


def writeSuccessfulConversionQualityReport(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...] | None = None,
    output_name: str = 'successful_conversion_quality',
) -> tuple[str, str, list[dict[str, object]]]:
    return imageCompositeConverterRemaining_helpers.writeSuccessfulConversionQualityReport(folder_path, svg_out_dir, reports_out_dir, successful_variants, output_name)


def parseArgs(argv: list[str] | None = None) -> argparse.Namespace:
    return imageCompositeConverterRemaining_helpers.parseArgs(argv)


@contextlib.contextmanager
def _optionalLogCapture(log_path: str):
    return imageCompositeConverterRemaining_helpers._optionalLogCapture(log_path)


def _autoDetectCsvPath(folder_path: str) -> str | None:
    return imageCompositeConverterRemaining_helpers._autoDetectCsvPath(folder_path)


def _resolveCliCsvAndOutput(args: argparse.Namespace) -> tuple[str, str | None]:
    return imageCompositeConverterRemaining_helpers._resolveCliCsvAndOutput(args)


def _formatUserDiagnostic(exc: BaseException) -> str:
    return imageCompositeConverterRemaining_helpers._formatUserDiagnostic(exc)


def _promptInteractiveRange(args: argparse.Namespace) -> tuple[str, str]:
    return imageCompositeConverterRemaining_helpers._promptInteractiveRange(args)


def repairAc0223BestlistArtifacts(output_root: str) -> dict[str, object]:
    return imageCompositeConverterRemaining_helpers.repairAc0223BestlistArtifacts(output_root)


def main(argv: list[str] | None = None) -> int:
    args = parseArgs(argv)
    return cli_helpers.runMainImpl(
        args,
        run_svg_render_subprocess_entrypoint_fn=_runSvgRenderSubprocessEntrypoint,
        set_svg_render_subprocess_enabled_fn=lambda enabled: globals().__setitem__("SVG_RENDER_SUBPROCESS_ENABLED", bool(enabled)),
        set_svg_render_subprocess_timeout_fn=lambda timeout: globals().__setitem__("SVG_RENDER_SUBPROCESS_TIMEOUT_SEC", float(timeout)),
        optional_log_capture_fn=_optionalLogCapture,
        build_linux_vendor_install_command_fn=buildLinuxVendorInstallCommand,
        prompt_interactive_range_fn=_promptInteractiveRange,
        resolve_cli_csv_and_output_fn=_resolveCliCsvAndOutput,
        load_description_mapping_fn=_loadDescriptionMapping,
        bootstrap_required_image_dependencies_fn=_bootstrapRequiredImageDependencies,
        analyze_range_fn=analyzeRange,
        convert_range_fn=convertRange,
        repair_ac0223_bestlist_fn=repairAc0223BestlistArtifacts,
        format_user_diagnostic_fn=_formatUserDiagnostic,
        description_mapping_error_type=DescriptionMappingError,
        ac08_regression_set_name=AC08_REGRESSION_SET_NAME,
        ac08_regression_variants=AC08_REGRESSION_VARIANTS,
    )

def convertImage(input_path: str, output_path: str, *, max_iter: int = 120, plateau_limit: int = 14, seed: int = 42) -> Path:
    return imageCompositeConverterRemaining_helpers.convertImageWithRuntimeBindings(
        input_path=input_path,
        output_path=output_path,
        render_embedded_raster_svg_fn=_renderEmbeddedRasterSvg,
        detect_relevant_regions_fn=detectRelevantRegions,
        annotate_image_regions_fn=annotateImageRegions,
        cv2_module=cv2,
        np_module=np,
        max_iter=max_iter,
        plateau_limit=plateau_limit,
        seed=seed,
    )


def convertImageVariants(*args, **kwargs):
    return legacy_api_helpers.convertImageVariantsImpl(
        *args,
        convert_range_fn=convertRange,
        **kwargs,
    )
OPTIONAL_DEPENDENCY_ERRORS = dependency_helpers.OPTIONAL_DEPENDENCY_ERRORS

# Backward-compatible snake_case aliases expected by legacy tests/tooling.
_ACTION_SNAKE_CASE_ALIASES: dict[str, str] = {
    "_apply_co2_label": "_applyCo2Label",
    "_apply_voc_label": "_applyVocLabel",
    "_co2_layout": "_co2Layout",
    "_text_bbox": "_textBbox",
    "_circle_bounds": "_circleBounds",
    "_clamp_circle_inside_canvas": "_clampCircleInsideCanvas",
    "_default_edge_anchored_circle_geometry": "_defaultEdgeAnchoredCircleGeometry",
    "_max_circle_radius_inside_canvas": "_maxCircleRadiusInsideCanvas",
    "_default_ac0812_params": "_defaultAc0812Params",
    "_default_ac0813_params": "_defaultAc0813Params",
    "_default_ac0814_params": "_defaultAc0814Params",
    "_default_ac0834_params": "_defaultAc0834Params",
    "_default_ac0870_params": "_defaultAc0870Params",
    "_default_ac0881_params": "_defaultAc0881Params",
    "_default_ac0882_params": "_defaultAc0882Params",
    "_fit_ac0811_params_from_image": "_fitAc0811ParamsFromImage",
    "_fit_ac0812_params_from_image": "_fitAc0812ParamsFromImage",
    "_fit_ac0814_params_from_image": "_fitAc0814ParamsFromImage",
    "_fit_semantic_badge_from_image": "_fitSemanticBadgeFromImage",
    "_finalize_ac08_style": "_finalizeAc08Style",
    "_estimate_vertical_stem_from_mask": "_estimateVerticalStemFromMask",
    "_enforce_left_arm_badge_geometry": "_enforceLeftArmBadgeGeometry",
    "_expected_semantic_presence": "_expectedSemanticPresence",
    "_normalize_centered_co2_label": "_normalizeCenteredCo2Label",
    "_persist_connector_length_floor": "_persistConnectorLengthFloor",
    "_quantize_badge_params": "_quantizeBadgeParams",
    "_tune_ac0832_co2_badge": "_tuneAc0832Co2Badge",
    "_tune_ac0834_co2_badge": "_tuneAc0834Co2Badge",
    "_tune_ac0835_voc_badge": "_tuneAc0835VocBadge",
    "_tune_ac08_left_connector_family": "_tuneAc08LeftConnectorFamily",
    "_activate_ac08_adaptive_locks": "_activateAc08AdaptiveLocks",
    "_release_ac08_adaptive_locks": "_releaseAc08AdaptiveLocks",
    "_global_parameter_vector_bounds": "_globalParameterVectorBounds",
    "_optimize_global_parameter_vector_sampling": "_optimizeGlobalParameterVectorSampling",
    "_optimize_circle_pose_multistart": "_optimizeCirclePoseMultistart",
    "_optimize_circle_pose_adaptive_domain": "_optimizeCirclePoseAdaptiveDomain",
    "_optimize_circle_radius_bracket": "_optimizeCircleRadiusBracket",
    "_select_circle_radius_plateau_candidate": "_selectCircleRadiusPlateauCandidate",
    "_optimize_element_color_bracket": "_optimizeElementColorBracket",
    "_optimize_element_extent_bracket": "_optimizeElementExtentBracket",
    "_optimize_element_width_bracket": "_optimizeElementWidthBracket",
    "_element_error_for_color": "_elementErrorForColor",
    "_element_error_for_circle_radius": "_elementErrorForCircleRadius",
    "_element_error_for_circle_pose": "_elementErrorForCirclePose",
    "_element_match_error": "_elementMatchError",
    "_element_width_key_and_bounds": "_elementWidthKeyAndBounds",
}
for _snake_name, _camel_name in _ACTION_SNAKE_CASE_ALIASES.items():
    if hasattr(Action, _camel_name) and not hasattr(Action, _snake_name):
        setattr(Action, _snake_name, staticmethod(getattr(Action, _camel_name)))
for _name in dir(Action):
    if _name.startswith("__") or "_" not in _name and _name.lower() == _name:
        continue
    if not any(ch.isupper() for ch in _name):
        continue
    _snake = []
    for _idx, _ch in enumerate(_name):
        if _ch.isupper() and _idx > 0 and _name[_idx - 1] != "_":
            _snake.append("_")
        _snake.append(_ch.lower())
    _snake_name = "".join(_snake)
    if not _snake_name.startswith("_"):
        _snake_name = f"_{_snake_name}"
    if not hasattr(Action, _snake_name):
        setattr(Action, _snake_name, staticmethod(getattr(Action, _name)))
if hasattr(Action, "traceImageSegment") and not hasattr(Action, "trace_image_segment"):
    Action.trace_image_segment = staticmethod(Action.traceImageSegment)
if hasattr(Action, "generateCompositeSvg") and not hasattr(Action, "generate_composite_svg"):
    Action.generate_composite_svg = staticmethod(Action.generateCompositeSvg)
if "ScalarRng" in globals() and not hasattr(Action, "_ScalarRng"):
    Action._ScalarRng = ScalarRng
if hasattr(GlobalParameterVector, "fromParams") and not hasattr(GlobalParameterVector, "from_params"):
    GlobalParameterVector.from_params = staticmethod(GlobalParameterVector.fromParams)
if hasattr(GlobalParameterVector, "applyToParams") and not hasattr(GlobalParameterVector, "apply_to_params"):
    GlobalParameterVector.apply_to_params = GlobalParameterVector.applyToParams

# The extracted "remaining" helper module executes in its own global namespace
# but still references converter-level symbols (classes/helpers/modules).
# Keep that namespace synchronized without overriding implementation functions.
for _ctx_name, _ctx_value in list(globals().items()):
    imageCompositeConverterRemaining_helpers.__dict__.setdefault(_ctx_name, _ctx_value)


def _syncRemainingRuntimeBindings() -> dict[str, object]:
    """Sync monkeypatched runtime symbols to the extracted remaining module."""

    remaining_globals = imageCompositeConverterRemaining_helpers.__dict__
    previous: dict[str, object] = {}
    for name, baselines in _REMAINING_RUNTIME_BINDING_TARGETS.items():
        local_baseline, remaining_baseline = baselines
        previous[name] = remaining_globals.get(name)
        current = globals().get(name, remaining_baseline)
        remaining_globals[name] = (
            remaining_baseline if current is local_baseline else current
        )
    return previous


def _restoreRemainingRuntimeBindings(previous_bindings: dict[str, object]) -> None:
    """Restore remaining-module bindings after a temporary runtime sync."""

    remaining_globals = imageCompositeConverterRemaining_helpers.__dict__
    for name, previous in previous_bindings.items():
        remaining_globals[name] = previous


_REMAINING_RUNTIME_BINDING_TARGETS = {
    name: (globals().get(name), imageCompositeConverterRemaining_helpers.__dict__.get(name))
    for name in (
        "cv2",
        "np",
        "fitz",
        "_conversionRandom",
        "_inRequestedRange",
        "_renderEmbeddedRasterSvg",
        "generateConversionOverviews",
        "_loadQualityConfig",
        "_writeQualityConfig",
        "_writeQualityPassReport",
        "_harmonizeSemanticSizeVariants",
        "_writePixelDelta2Ranking",
        "_selectOpenQualityCases",
        "_selectMiddleLowerTercile",
        "_tryTemplateTransfer",
        "_defaultConvertedSymbolsRoot",
        "runIterationPipeline",
    )
}

# Module-level camelCase -> snake_case aliases for legacy tests/tooling.
for _name, _obj in list(globals().items()):
    if _name.startswith("__") or not callable(_obj):
        continue
    if not any(ch.isupper() for ch in _name):
        continue
    _snake = []
    for _idx, _ch in enumerate(_name):
        if _ch.isupper() and _idx > 0 and _name[_idx - 1] != "_":
            _snake.append("_")
        _snake.append(_ch.lower())
    _snake_name = "".join(_snake)
    if _snake_name not in globals():
        globals()[_snake_name] = _obj


if __name__ == "__main__":
    raise SystemExit(main())
