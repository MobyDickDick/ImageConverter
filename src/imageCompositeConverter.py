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
import json
import math
import os
import random
import time
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
import importlib
import io
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
from src.iCCModules import imageCompositeConverterSemanticAc08Params as semantic_ac08_param_helpers
from src.iCCModules import imageCompositeConverterSemanticAr0100 as semantic_ar0100_helpers
from src.iCCModules import imageCompositeConverterSemanticBadgeGeometry as semantic_badge_geometry_helpers
from src.iCCModules import imageCompositeConverterSemanticBadgeSvg as semantic_badge_svg_helpers
from src.iCCModules import imageCompositeConverterSemanticAc08SmallVariants as semantic_ac08_small_variant_helpers
from src.iCCModules import imageCompositeConverterSemanticAc08Families as semantic_ac08_family_helpers
from src.iCCModules import imageCompositeConverterSemanticAc08Finalization as semantic_ac08_finalization_helpers
from src.iCCModules import imageCompositeConverterSemanticAdaptiveLocks as semantic_adaptive_lock_helpers
from src.iCCModules import imageCompositeConverterSemanticCircleStyle as semantic_circle_style_helpers
from src.iCCModules import imageCompositeConverterQuality as quality_helpers
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
from src.iCCModules import imageCompositeConverterBatchReporting as batch_reporting_helpers
from src.iCCModules import imageCompositeConverterConversionRows as conversion_row_helpers
from src.iCCModules import imageCompositeConverterAc08Reporting as ac08_reporting_helpers
from src.iCCModules import imageCompositeConverterRanking as ranking_helpers
from src.iCCModules import imageCompositeConverterThresholding as thresholding_helpers
from src.iCCModules import imageCompositeConverterSuccessfulConversions as successful_conversions_helpers
from src.iCCModules import imageCompositeConverterSuccessfulConversionQuality as successful_conversion_quality_helpers
from src.iCCModules import imageCompositeConverterBestlist as conversion_bestlist_helpers
from src.iCCModules import imageCompositeConverterElementValidation as element_validation_helpers
from src.iCCModules import imageCompositeConverterElementMasks as element_mask_helpers
from src.iCCModules import imageCompositeConverterElementErrorMetrics as element_error_metric_helpers
from src.iCCModules import imageCompositeConverterCompositeSvg as composite_svg_helpers
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


# Load numpy before cv2: OpenCV's Python bindings import numpy at module-import
# time and can fail permanently for this process if cv2 is attempted first while
# numpy is available only via repo-vendored site-packages.
np = _load_optional_module("numpy")
cv2 = _load_optional_module("cv2")
fitz = _load_optional_module("fitz")  # PyMuPDF for native SVG rendering



def _clip(value, low, high):
    """Clip scalar/array values without hard-requiring numpy at runtime."""
    if np is not None:
        return np.clip(value, low, high)
    if isinstance(value, (int, float)):
        return Action._clipScalar(float(value), float(low), float(high))
    raise RuntimeError("numpy is required for non-scalar clip operations")





@dataclass(frozen=True)
class RGBWert:
    """RGB value constrained to Nummer(256) semantics (0..255)."""

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for channel_name, channel in (("r", self.r), ("g", self.g), ("b", self.b)):
            if not isinstance(channel, int):
                raise TypeError(f"RGB channel '{channel_name}' must be an integer.")
            if channel < 0 or channel >= 256:
                raise ValueError(f"RGB channel '{channel_name}' must satisfy 0 <= x < 256.")

    def toHex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


@dataclass(frozen=True)
class Punkt:
    x: float
    y: float


@dataclass(frozen=True)
class Kreis:
    mittelpunkt: Punkt
    radius: float
    randbreite: float
    rand_farbe: RGBWert
    hintergrundfarbe: RGBWert

    def __post_init__(self) -> None:
        if float(self.radius) <= 0:
            raise ValueError("Kreis.radius must be > 0.")
        if float(self.randbreite) < 0:
            raise ValueError("Kreis.randbreite must be >= 0.")
        if float(self.randbreite) > float(self.radius):
            raise ValueError("Constraint verletzt: Randbreite <= Radius.")


@dataclass(frozen=True)
class Griff:
    anfang: Punkt
    ende: Punkt

    @property
    def laenge(self) -> float:
        return abstand(self.anfang, self.ende)


@dataclass(frozen=True)
class Kelle:
    griff: Griff
    kreis: Kreis

    def __post_init__(self) -> None:
        if self.griff.anfang != self.kreis.mittelpunkt:
            raise ValueError("Constraint verletzt: Griff.Anfang == Kreis.Mittelpunkt.")
        if self.griff.laenge <= float(self.kreis.radius):
            raise ValueError("Constraint verletzt: Griff.Länge > Kreis.Radius.")

    def toSvg(self, width: int, height: int, *, clip_to_canvas: bool = True) -> str:
        """Render the ladle as SVG. Handle is drawn first (background), then circle."""
        handle_stroke = max(1.0, float(self.kreis.randbreite))
        cx = float(self.kreis.mittelpunkt.x)
        cy = float(self.kreis.mittelpunkt.y)
        radius = float(self.kreis.radius)
        handle = (
            f'<line x1="{self.griff.anfang.x:.2f}" y1="{self.griff.anfang.y:.2f}" '
            f'x2="{self.griff.ende.x:.2f}" y2="{self.griff.ende.y:.2f}" '
            f'stroke="{self.kreis.rand_farbe.toHex()}" stroke-width="{handle_stroke:.2f}" stroke-linecap="round"/>'
        )
        circle = (
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" '
            f'fill="{self.kreis.hintergrundfarbe.toHex()}" stroke="{self.kreis.rand_farbe.toHex()}" '
            f'stroke-width="{float(self.kreis.randbreite):.2f}"/>'
        )
        if not clip_to_canvas:
            body = f"{handle}{circle}"
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{body}</svg>'

        clip_id = "canvasClip"
        body = (
            f'<defs><clipPath id="{clip_id}"><rect x="0" y="0" width="{width}" height="{height}" /></clipPath></defs>'
            f'<g clip-path="url(#{clip_id})">{handle}{circle}</g>'
        )
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{body}</svg>'


def abstand(punkt1: Punkt, punkt2: Punkt) -> float:
    return math.hypot(float(punkt1.x) - float(punkt2.x), float(punkt1.y) - float(punkt2.y))


def buildOrientedKelle(
    orientation: str,
    *,
    mittelpunkt: Punkt,
    radius: float,
    griff_laenge: float,
    randbreite: float,
    rand_farbe: RGBWert,
    hintergrundfarbe: RGBWert,
) -> Kelle:
    """Create a Kelle with handle orientation in {left, right, top, bottom/down}."""
    orient = str(orientation).strip().lower()
    if orient in {"bottom", "down", "unten"}:
        endpunkt = Punkt(mittelpunkt.x, mittelpunkt.y + float(griff_laenge))
    elif orient in {"top", "up", "oben"}:
        endpunkt = Punkt(mittelpunkt.x, mittelpunkt.y - float(griff_laenge))
    elif orient in {"left", "links"}:
        endpunkt = Punkt(mittelpunkt.x - float(griff_laenge), mittelpunkt.y)
    elif orient in {"right", "rechts"}:
        endpunkt = Punkt(mittelpunkt.x + float(griff_laenge), mittelpunkt.y)
    else:
        raise ValueError("orientation must be one of: left, right, top/up, bottom/down")

    kelle = Kelle(
        griff=Griff(anfang=mittelpunkt, ende=endpunkt),
        kreis=Kreis(
            mittelpunkt=mittelpunkt,
            radius=float(radius),
            randbreite=float(randbreite),
            rand_farbe=rand_farbe,
            hintergrundfarbe=hintergrundfarbe,
        ),
    )
    return kelle

@dataclass
class Element:
    pixels: list[list[int]]
    x0: int
    y0: int
    x1: int
    y1: int


@dataclass
class Candidate:
    shape: str
    cx: float
    cy: float
    w: float
    h: float


@dataclass(frozen=True)
class GlobalParameterVector:
    """Unified optimization vector for badge/kelle geometry and text layout."""

    cx: float
    cy: float
    r: float
    arm_x1: float | None = None
    arm_y1: float | None = None
    arm_x2: float | None = None
    arm_y2: float | None = None
    arm_stroke: float | None = None
    stem_x: float | None = None
    stem_top: float | None = None
    stem_bottom: float | None = None
    stem_width: float | None = None
    text_x: float | None = None
    text_y: float | None = None
    text_scale: float | None = None

    @staticmethod
    def fromParams(params: dict) -> "GlobalParameterVector":
        return GlobalParameterVector(
            cx=float(params.get("cx", 0.0)),
            cy=float(params.get("cy", 0.0)),
            r=float(params.get("r", 1.0)),
            arm_x1=float(params["arm_x1"]) if "arm_x1" in params else None,
            arm_y1=float(params["arm_y1"]) if "arm_y1" in params else None,
            arm_x2=float(params["arm_x2"]) if "arm_x2" in params else None,
            arm_y2=float(params["arm_y2"]) if "arm_y2" in params else None,
            arm_stroke=float(params["arm_stroke"]) if "arm_stroke" in params else None,
            stem_x=float(params["stem_x"]) if "stem_x" in params else None,
            stem_top=float(params["stem_top"]) if "stem_top" in params else None,
            stem_bottom=float(params["stem_bottom"]) if "stem_bottom" in params else None,
            stem_width=float(params["stem_width"]) if "stem_width" in params else None,
            text_x=float(params["text_x"]) if "text_x" in params else None,
            text_y=float(params["text_y"]) if "text_y" in params else None,
            text_scale=float(params["text_scale"]) if "text_scale" in params else None,
        )

    def applyToParams(self, params: dict) -> dict:
        out = dict(params)
        out["cx"] = float(self.cx)
        out["cy"] = float(self.cy)
        out["r"] = float(self.r)
        optional_values = {
            "arm_x1": self.arm_x1,
            "arm_y1": self.arm_y1,
            "arm_x2": self.arm_x2,
            "arm_y2": self.arm_y2,
            "arm_stroke": self.arm_stroke,
            "stem_x": self.stem_x,
            "stem_top": self.stem_top,
            "stem_bottom": self.stem_bottom,
            "stem_width": self.stem_width,
            "text_x": self.text_x,
            "text_y": self.text_y,
            "text_scale": self.text_scale,
        }
        for key, value in optional_values.items():
            if value is not None:
                out[key] = float(value)
        return out

def loadGrayscaleImage(path: Path) -> list[list[int]]:
    image_module = _importWithVendoredFallback("PIL.Image")
    gray = image_module.open(path).convert("L")
    w, h = gray.size
    px = gray.load()
    return [[int(px[x, y]) for x in range(w)] for y in range(h)]


def _createDiffImageWithoutCv2(input_path: str | Path, svg_content: str):
    """Create a normalized signed red/cyan diff image when numpy/opencv are unavailable."""
    if fitz is None:
        raise RuntimeError("Fallback diff generation requires fitz (PyMuPDF).")

    with fitz.open(str(input_path)) as original_doc, fitz.open("pdf", svg_content.encode("utf-8")) as svg_doc:
        original_pix = original_doc[0].get_pixmap(alpha=False)

        # Render SVG with alpha and composite onto white so transparent
        # backgrounds do not appear black in the diff viewer.
        svg_pix = svg_doc[0].get_pixmap(alpha=True)
        if (svg_pix.width, svg_pix.height) != (original_pix.width, original_pix.height):
            svg_pix = fitz.Pixmap(svg_pix, original_pix.width, original_pix.height)

        original_samples = original_pix.samples
        svg_samples = svg_pix.samples
        diff_samples = bytearray(len(original_samples))

        for idx in range(0, len(diff_samples), 3):
            r0, g0, b0 = original_samples[idx : idx + 3]
            sidx = (idx // 3) * 4
            rs, gs, bs, sa = svg_samples[sidx : sidx + 4]
            alpha = float(sa) / 255.0
            # PyMuPDF delivers premultiplied RGB when alpha=True. Composite onto
            # white without multiplying RGB by alpha a second time.
            rs = int(round(min(255.0, max(0.0, float(rs) + (255.0 * (1.0 - alpha))))))
            gs = int(round(min(255.0, max(0.0, float(gs) + (255.0 * (1.0 - alpha))))))
            bs = int(round(min(255.0, max(0.0, float(bs) + (255.0 * (1.0 - alpha))))))
            dx = float(rs - r0) + float(gs - g0) + float(bs - b0)
            norm = max(-1.0, min(1.0, dx / (3.0 * 255.0)))
            magnitude = abs(norm)
            mean_tone = (float(r0) + float(g0) + float(b0) + float(rs) + float(gs) + float(bs)) / 6.0
            up = int(round(mean_tone + magnitude * (255.0 - mean_tone)))
            down = int(round(mean_tone * (1.0 - magnitude)))
            if norm >= 0.0:
                # Positive delta (generated image brighter than source): cyan tint from base tone.
                diff_samples[idx] = down
                diff_samples[idx + 1] = up
                diff_samples[idx + 2] = up
            else:
                # Negative delta (generated image darker than source): red tint from base tone.
                diff_samples[idx] = up
                diff_samples[idx + 1] = down
                diff_samples[idx + 2] = down

        diff_pix = fitz.Pixmap(fitz.csRGB, original_pix.width, original_pix.height, bytes(diff_samples), 0)
        # Explicitly release temporary MuPDF objects before returning the diff
        # pixmap to reduce native-memory pressure in long AC08 batch runs.
        del svg_pix
        del original_pix
        return diff_pix


def _computeOtsuThreshold(grayscale: list[list[int]]) -> int:
    return thresholding_helpers.computeOtsuThresholdImpl(grayscale)


def _adaptiveThreshold(grayscale: list[list[int]], block_size: int = 15, c: int = 5) -> list[list[int]]:
    return thresholding_helpers.adaptiveThresholdImpl(grayscale, block_size=block_size, c=c)


def loadBinaryImageWithMode(path: Path, *, threshold: int = 220, mode: str = "global") -> list[list[int]]:
    grayscale = loadGrayscaleImage(path)
    m = str(mode).lower()
    if m == 'global':
        return [[1 if v < threshold else 0 for v in row] for row in grayscale]
    if m == 'otsu':
        t = _computeOtsuThreshold(grayscale)
        return [[1 if v < t else 0 for v in row] for row in grayscale]
    if m == 'adaptive':
        return _adaptiveThreshold(grayscale)
    raise ValueError(f"Unknown threshold mode '{mode}'.")


def renderCandidateMask(candidate: Candidate, width: int, height: int) -> list[list[int]]:
    mask = [[0 for _ in range(width)] for _ in range(height)]
    rx = max(1.0, (candidate.w + candidate.h) / 4.0) if candidate.shape == 'circle' else max(1.0, candidate.w / 2.0)
    ry = rx if candidate.shape == 'circle' else max(1.0, candidate.h / 2.0)
    inv_rx2 = 1.0 / (rx * rx)
    inv_ry2 = 1.0 / (ry * ry)
    for y in range(height):
        for x in range(width):
            if ((x - candidate.cx) ** 2) * inv_rx2 + ((y - candidate.cy) ** 2) * inv_ry2 <= 1.0:
                mask[y][x] = 1
    return mask


def _iou(a: list[list[int]], b: list[list[int]]) -> float:
    return thresholding_helpers.iouImpl(a, b)


def scoreCandidate(target: list[list[int]], candidate: Candidate) -> float:
    return _iou(target, renderCandidateMask(candidate, len(target[0]), len(target)))


def score_candidate(target: list[list[int]], candidate: Candidate) -> float:
    """Snake-case compatibility wrapper for scoreCandidate."""
    return scoreCandidate(target, candidate)


def randomNeighbor(base: Candidate, scale: float, rng: random.Random) -> Candidate:
    return Candidate(base.shape, base.cx + rng.uniform(-scale, scale), base.cy + rng.uniform(-scale, scale), max(1.0, base.w + rng.uniform(-scale, scale) * 1.4), max(1.0, base.h + rng.uniform(-scale, scale) * 1.4))


def optimizeElement(target: list[list[int]], init: Candidate, *, max_iter: int, plateau_limit: int, seed: int) -> tuple[Candidate, float]:
    rng = random.Random(seed)
    best = init
    best_score = scoreCandidate(target, best)
    scale = max(1.0, max(best.w, best.h) * 0.2)
    plateau = 0
    for _ in range(max_iter):
        cand = randomNeighbor(best, scale, rng)
        s = scoreCandidate(target, cand)
        if s >= best_score:
            best, best_score, plateau = cand, s, 0
        else:
            plateau += 1
        if plateau > plateau_limit:
            scale = max(0.5, scale * 0.7)
            plateau = 0
    return best, best_score


def optimize_element(target: list[list[int]], init: Candidate, *, max_iter: int, plateau_limit: int, seed: int) -> tuple[Candidate, float]:
    """Snake-case compatibility wrapper for optimizeElement."""
    return optimizeElement(target, init, max_iter=max_iter, plateau_limit=plateau_limit, seed=seed)


def _grayToHex(v: float) -> str:
    g = max(0, min(255, int(round(v))))
    return f"#{g:02x}{g:02x}{g:02x}"


def estimateStrokeStyle(grayscale: list[list[int]], element: Element, candidate: Candidate) -> tuple[str, str | None, float | None]:
    vals = [grayscale[y + element.y0][x + element.x0] for y,row in enumerate(element.pixels) for x,v in enumerate(row) if v]
    fill = _grayToHex(sum(vals) / max(1, len(vals)))
    if candidate.shape != 'circle':
        return fill, None, None
    r = max(1.0, (candidate.w + candidate.h) / 4.0)
    inner=[]; outer=[]
    for y,row in enumerate(element.pixels):
        for x,v in enumerate(row):
            if not v: continue
            d=((x-candidate.cx)**2 + (y-candidate.cy)**2) ** 0.5
            px = grayscale[y + element.y0][x + element.x0]
            if d >= r*0.84:
                outer.append(px)
            elif d <= r*0.65:
                inner.append(px)
    if outer and inner and (sum(outer)/len(outer)) < (sum(inner)/len(inner)) - 10:
        return _grayToHex(sum(inner)/len(inner)), _grayToHex(sum(outer)/len(outer)), max(1.0, r*0.2)
    return fill, None, None


def candidateToSvg(candidate: Candidate, gx: int, gy: int, fill_color: str, stroke_color: str | None = None, stroke_width: float | None = None) -> str:
    if candidate.shape == 'circle':
        r = max(1.0, (candidate.w + candidate.h) / 4.0)
        if stroke_color is not None and stroke_width is not None:
            r = max(0.5, r - (float(stroke_width) / 2.0))
        stroke_attr = '' if stroke_color is None else f' stroke="{stroke_color}" stroke-width="{float(stroke_width or 1.0):.2f}"'
        return f'<circle cx="{candidate.cx + gx:.2f}" cy="{candidate.cy + gy:.2f}" r="{r:.2f}" fill="{fill_color}"{stroke_attr} />'
    rx = max(1.0, candidate.w / 2.0)
    ry = max(1.0, candidate.h / 2.0)
    return f'<ellipse cx="{candidate.cx + gx:.2f}" cy="{candidate.cy + gy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{fill_color}" />'


def decomposeCircleWithStem(grayscale: list[list[int]], element: Element, candidate: Candidate) -> list[str] | None:
    if not element.pixels or not element.pixels[0]:
        return None

    r = max(1.0, (candidate.w + candidate.h) / 4.0)
    cx = float(candidate.cx)
    cy = float(candidate.cy)

    # Residual foreground outside the candidate circle corresponds to connectors.
    residual: list[tuple[int, int]] = []
    circle_pixels: list[tuple[int, int]] = []
    for y, row in enumerate(element.pixels):
        for x, v in enumerate(row):
            if not v:
                continue
            d = math.hypot(float(x) - cx, float(y) - cy)
            if d <= (r * 1.02):
                circle_pixels.append((x, y))
            elif d >= (r * 0.90):
                residual.append((x, y))

    if not residual:
        return None

    # Keep only the dominant connected residual cluster.
    residual_set = set(residual)
    visited: set[tuple[int, int]] = set()
    best_cluster: list[tuple[int, int]] = []
    for seed in residual:
        if seed in visited:
            continue
        stack = [seed]
        cluster: list[tuple[int, int]] = []
        visited.add(seed)
        while stack:
            px, py = stack.pop()
            cluster.append((px, py))
            for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                if (nx, ny) in residual_set and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    stack.append((nx, ny))
        if len(cluster) > len(best_cluster):
            best_cluster = cluster

    if not best_cluster:
        return None

    xs = [x for x, _ in best_cluster]
    ys = [y for _, y in best_cluster]
    sx0, sx1 = min(xs), max(xs)
    sy0, sy1 = min(ys), max(ys)
    stem_w = max(1, sx1 - sx0 + 1)
    stem_h = max(1, sy1 - sy0 + 1)

    # infer connector orientation relative to circle center.
    mean_x = sum(xs) / max(1, len(xs))
    mean_y = sum(ys) / max(1, len(ys))
    dx = abs(mean_x - cx)
    dy = abs(mean_y - cy)
    if dx >= dy:
        stem_direction = "right" if mean_x >= cx else "left"
    else:
        stem_direction = "bottom" if mean_y >= cy else "top"

    stem_values = [grayscale[element.y0 + y][element.x0 + x] for x, y in best_cluster]
    stem_color = _grayToHex(round(sum(stem_values) / max(1, len(stem_values))))

    fill_color, stroke_color, stroke_width = estimateStrokeStyle(grayscale, element, candidate)

    stem_x = float(element.x0 + sx0)
    stem_y = float(element.y0 + sy0)
    stem_wf = float(stem_w)
    stem_hf = float(stem_h)
    overlap = max(0.6, float(stroke_width or 0.0) * 0.55)

    if stem_direction in {"bottom", "top"}:
        circle_cx = float(element.x0) + cx
        circle_cy = float(element.y0) + cy
        stem_x = circle_cx - (stem_wf / 2.0)
        old_bottom = float(element.y0 + sy1 + 1)
        old_top = float(element.y0 + sy0)
        if stem_direction == "bottom":
            stem_y = circle_cy + r - overlap
            stem_hf = max(1.0, old_bottom - stem_y)
        else:
            stem_y = old_top
            stem_hf = max(1.0, (circle_cy - r + overlap) - stem_y)
    else:
        circle_cx = float(element.x0) + cx
        circle_cy = float(element.y0) + cy
        stem_y = circle_cy - (stem_hf / 2.0)
        old_right = float(element.x0 + sx1 + 1)
        old_left = float(element.x0 + sx0)
        overlap_lr = min(0.2, overlap)
        if stem_direction == "right":
            stem_x = circle_cx + r - overlap_lr
            stem_wf = max(1.0, old_right - stem_x)
        else:
            stem_x = old_left
            stem_wf = max(1.0, (circle_cx - r + overlap_lr) - stem_x)

    rect = (
        f'<rect x="{stem_x:.2f}" y="{stem_y:.2f}" '
        f'width="{stem_wf:.2f}" height="{stem_hf:.2f}" fill="{stem_color}"/>'
    )
    circle_vals = [grayscale[element.y0 + y][element.x0 + x] for x, y in circle_pixels] or stem_values
    circle = candidateToSvg(
        candidate,
        element.x0,
        element.y0,
        fill_color if fill_color else _grayToHex(sum(circle_vals) / max(1, len(circle_vals))),
        stroke_color,
        stroke_width,
    )
    return [rect, circle]

def _missingRequiredImageDependencies() -> list[str]:
    missing: list[str] = []
    if cv2 is None:
        missing.append("opencv-python-headless")
    if np is None:
        missing.append("numpy")
    return missing


def _bootstrapRequiredImageDependencies() -> list[str]:
    missing = _missingRequiredImageDependencies()
    if not missing:
        return []

    cmd = [sys.executable, "-m", "pip", "install", *missing]
    print(f"[INFO] Fehlende Bild-Abhängigkeiten gefunden: {', '.join(missing)}")
    print(f"[INFO] Installiere via: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Automatische Installation fehlgeschlagen. "
            "Bitte Abhängigkeiten manuell installieren oder Proxy/Netzwerk prüfen."
        ) from exc

    # Re-import in current process so conversion can run without restart.
    global cv2, np
    if "opencv-python-headless" in missing:
        import cv2 as _cv2

        cv2 = _cv2
    if "numpy" in missing:
        import numpy as _np

        np = _np

    return missing


def rgbToHex(rgb: np.ndarray) -> str:
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def getBaseNameFromFile(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r"(-\d+)$", "", name)
    while True:
        prev = name
        name = re.sub(r"_([1-9]|L|M|S|[1-9]S|W|X)$", "", name, flags=re.IGNORECASE)
        if name == prev:
            break
    return name


@dataclass
class Perception:
    img_path: str
    csv_path: str

    def __post_init__(self) -> None:
        self.base_name = getBaseNameFromFile(os.path.basename(self.img_path))
        self.img = cv2.imread(self.img_path)
        self.raw_desc = self._loadDescriptions()

    def _loadDescriptions(self) -> dict[str, str]:
        return _loadDescriptionMapping(self.csv_path)


@dataclass(frozen=True)
class SourceSpan:
    """Optional source location attached to diagnostics for user-facing data files."""

    path: str
    line: int | None = None
    column: int | None = None

    def format(self) -> str:
        location = self.path
        if self.line is not None:
            location += f":{self.line}"
            if self.column is not None:
                location += f":{self.column}"
        return location


class DescriptionMappingError(ValueError):
    """Structured loader error with an optional source span for diagnostics."""

    def __init__(self, message: str, *, span: SourceSpan | None = None):
        super().__init__(message)
        self.message = message
        self.span = span

    def __str__(self) -> str:
        if self.span is None:
            return self.message
        return f"{self.message} ({self.span.format()})"


def _loadDescriptionMapping(path: str) -> dict[str, str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xml":
        return _loadDescriptionMappingFromXml(path)
    return _loadDescriptionMappingFromCsv(path)


def _loadDescriptionMappingFromCsv(path: str) -> dict[str, str]:
    raw_desc: dict[str, str] = {}
    if not os.path.exists(path):
        return raw_desc

    with open(path, mode="r", encoding="utf-8-sig") as f:
        content = f.read()
        delimiter = ";" if ";" in content.split("\n", 1)[0] else ","
        f.seek(0)
        reader = csv.reader(f, delimiter=delimiter)
        headers = next(reader, None)
        if not headers:
            return raw_desc

        root_idx, desc_idx = -1, -1
        for i, h in enumerate(headers):
            low = h.lower()
            if "wurzelform" in low:
                root_idx = i
            elif "beschreibung" in low:
                desc_idx = i
        if root_idx == -1:
            root_idx = 1
        if desc_idx == -1:
            desc_idx = 2

        for row_number, row in enumerate(reader, start=2):
            if len(row) > max(root_idx, desc_idx):
                root_name = row[root_idx].strip()
                desc = row[desc_idx].strip()
                if root_name:
                    raw_desc[root_name] = desc
                continue

            expected_columns = max(root_idx, desc_idx) + 1
            raise DescriptionMappingError(
                (
                    "Description table row is missing expected columns "
                    f"(expected at least {expected_columns}, got {len(row)})."
                ),
                span=SourceSpan(path=path, line=row_number, column=1),
            )
    return raw_desc


def _loadDescriptionMappingFromXml(path: str) -> dict[str, str]:
    raw_desc: dict[str, str] = {}
    resolved_path = _resolveDescriptionXmlPath(path)
    if resolved_path is None:
        return raw_desc

    try:
        tree = ET.parse(resolved_path)
    except ET.ParseError as exc:
        raise DescriptionMappingError(
            "Description XML could not be parsed.",
            span=SourceSpan(path=resolved_path, line=exc.position[0], column=exc.position[1] + 1),
        ) from exc

    root = tree.getroot()

    def _registerDescription(key: str, description: str) -> None:
        normalized_desc = str(description or "").strip()
        if not normalized_desc:
            return

        for candidate in {
            str(key or "").strip(),
            str(key or "").strip().upper(),
            str(key or "").strip().lower(),
            getBaseNameFromFile(str(key or "").strip()),
            getBaseNameFromFile(str(key or "").strip()).upper(),
            getBaseNameFromFile(str(key or "").strip()).lower(),
            os.path.splitext(str(key or "").strip())[0],
            os.path.splitext(str(key or "").strip())[0].upper(),
            os.path.splitext(str(key or "").strip())[0].lower(),
        }:
            if candidate:
                raw_desc[candidate] = normalized_desc

    def _mergeEntryAndImageDesc(entry_desc: str, image_desc: str) -> str:
        e = entry_desc.strip()
        i = image_desc.strip()
        if e and i and e != i:
            return f"{e} {i}".strip()
        return i or e

    def _extractImageSpecificDescription(entry: ET.Element, image_name: str) -> str:
        image_name = str(image_name or "").strip()
        if not image_name:
            return ""

        # Variante 1: <bilder><bild beschreibung="...">datei.jpg</bild></bilder>
        for image_tag in entry.findall("./bilder/bild"):
            tag_name = (image_tag.text or "").strip()
            if tag_name == image_name:
                attr_desc = (image_tag.attrib.get("beschreibung") or "").strip()
                if attr_desc:
                    return attr_desc
                child_desc = (image_tag.findtext("beschreibung") or "").strip()
                if child_desc:
                    return child_desc

        # Variante 2: <bildbeschreibungen><bildbeschreibung bild="datei.jpg">...</bildbeschreibung></bildbeschreibungen>
        for detail_tag in entry.findall("./bildbeschreibungen/bildbeschreibung"):
            detail_name = (detail_tag.attrib.get("bild") or detail_tag.attrib.get("image") or "").strip()
            if detail_name and detail_name == image_name:
                text_desc = ("".join(detail_tag.itertext()) or "").strip()
                if text_desc:
                    return re.sub(r"\s+", " ", text_desc).strip()
        return ""

    for entry in root.findall(".//entry"):
        desc = (entry.findtext("beschreibung") or "").strip()
        root_form = (entry.findtext("wurzelform") or "").strip()
        key = str(entry.attrib.get("key", "")).strip()

        if root_form and desc:
            _registerDescription(root_form, desc)
        if key and desc:
            _registerDescription(key, desc)

        for image_tag in entry.findall("./bilder/bild"):
            image_name = (image_tag.text or "").strip()
            image_stem = os.path.splitext(image_name)[0].strip()
            image_specific_desc = _extractImageSpecificDescription(entry, image_name)
            merged_desc = _mergeEntryAndImageDesc(desc, image_specific_desc)
            if merged_desc:
                _registerDescription(image_name, merged_desc)
                _registerDescription(image_stem, merged_desc)

    return raw_desc


def _resolveDescriptionXmlPath(path: str) -> str | None:
    candidate = Path(path)
    if candidate.exists():
        return str(candidate)

    basename = candidate.name
    if not basename:
        return None

    fallback_candidates = [
        Path("artifacts/descriptions") / basename,
        Path("artifacts/images_to_convert") / basename,
    ]
    for fallback in fallback_candidates:
        if fallback.exists():
            return str(fallback)
    return None


def _requiredVendorPackages() -> list[str]:
    return [
        "numpy",
        "opencv-python-headless",
        "Pillow",
        "PyMuPDF",
    ]


def buildLinuxVendorInstallCommand(
    vendor_dir: str = "vendor",
    platform_tag: str = "manylinux2014_x86_64",
    python_version: str | None = None,
) -> list[str]:
    if python_version is None:
        python_version = f"{sys.version_info.major}{sys.version_info.minor}"

    return [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        vendor_dir,
        "--platform",
        platform_tag,
        "--implementation",
        "cp",
        "--python-version",
        python_version,
        "--only-binary=:all:",
        "--upgrade-strategy",
        "eager",
        *_requiredVendorPackages(),
    ]


class Reflection:
    def __init__(self, raw_desc: dict[str, str]):
        self.raw_desc = raw_desc

    def parseDescription(self, base_name: str, img_filename: str):
        canonical_base = getBaseNameFromFile(base_name).upper()
        if not canonical_base:
            canonical_base = getBaseNameFromFile(img_filename).upper()
        description_fragments = _collectDescriptionFragments(self.raw_desc, base_name, img_filename)
        desc_raw = " ".join(fragment["text"] for fragment in description_fragments)
        desc = desc_raw.lower().strip()
        base_upper = canonical_base or base_name.upper()
        symbol_upper = canonical_base or base_upper

        params = {
            "mode": "auto",
            "top_source_ref": None,
            "bottom_shape": None,
            "elements": [],
            "label": "M",
            "variant_name": os.path.splitext(str(img_filename))[0].upper(),
            "documented_alias_refs": sorted(Reflection._extractDocumentedAliasRefs(desc)),
            "description_fragments": description_fragments,
            "semantic_priority_order": [
                "family_rule",
                "layout_override",
                "description_heuristic",
            ],
            "semantic_conflicts": [],
            "semantic_sources": {},
        }

        semantic_symbol = symbol_upper.startswith("AC08") or symbol_upper == "AR0100"
        if semantic_symbol:
            params["mode"] = "semantic_badge"

        if semantic_helpers.apply_semantic_badge_family_rules(
            base_upper=base_upper,
            symbol_upper=symbol_upper,
            desc=desc,
            params=params,
        ):
            return desc, params

        non_traceable_hint = Reflection._detect_non_traceable_hint(desc)
        if non_traceable_hint:
            params["mode"] = "manual_review"
            params["review_reason"] = non_traceable_hint
            params["elements"].append(f"MANUELL: {non_traceable_hint}")
            return desc, params

        match = re.search(r"\boven\b.*?\bwie(?:\s+in)?\s+([a-z]{2}\d{3,4})\b", desc)
        if match:
            params["mode"] = "composite"
            params["top_source_ref"] = match.group(1).upper()
            params["elements"].append(
                f"OBEN: Geschnitten aus Originaldatei {params['top_source_ref']}"
            )

        if "unten" in desc and "viereck" in desc and "kreuz" in desc:
            params["mode"] = "composite"
            params["bottom_shape"] = "square_cross"
            params["elements"].append("UNTEN: Parametrisch generiertes Viereck mit Kreuz")

        return desc, params

    def parse_description(self, base_name: str, img_filename: str):
        return self.parseDescription(base_name, img_filename)

    @staticmethod
    def _extractDocumentedAliasRefs(text: str) -> set[str]:
        return semantic_helpers.extract_documented_alias_refs(text)

    @staticmethod
    def _extract_documented_alias_refs(text: str) -> set[str]:
        return Reflection._extractDocumentedAliasRefs(text)

    @staticmethod
    def _detect_non_traceable_hint(text: str) -> str | None:
        normalized = re.sub(r"\s+", " ", str(text or "").lower()).strip()
        if not normalized:
            return None
        hint_patterns = [
            (r"nicht automatisch nachzeichnbar", "Beschreibung markiert Symbol als nicht automatisch nachzeichnbar."),
            (r"nur eingeschränkt.*reproduzierbar", "Beschreibung markiert Symbol als nur eingeschränkt reproduzierbar."),
            (r"außerhalb der robust unterstützten standard-geometrien", "Beschreibung markiert Symbol außerhalb der robust unterstützten Standard-Geometrien."),
            (r"bitte einer finalen wurzelform-kategorie zuordnen", "Beschreibung fordert manuelle Zuordnung zu einer finalen Wurzelform-Kategorie."),
            (r"noch nicht fachlich klassifiziert", "Beschreibung markiert Symbol als fachlich noch nicht klassifiziert."),
        ]
        for pattern, message in hint_patterns:
            if re.search(pattern, normalized):
                return message
        return None

    @staticmethod
    def _parseSemanticBadgeLayoutOverrides(text: str) -> dict[str, float | str]:
        return semantic_helpers.parse_semantic_badge_layout_overrides(text)

    @staticmethod
    def _parse_semantic_badge_layout_overrides(text: str) -> dict[str, float | str]:
        return Reflection._parseSemanticBadgeLayoutOverrides(text)
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
        """Apply a slight per-run redraw jitter and describe it for the log."""
        p = copy.deepcopy(params)
        variation_logs: list[str] = []
        if w <= 0 or h <= 0:
            return p, variation_logs

        seed = (
            int(Action.STOCHASTIC_RUN_SEED) * 1009
            + int(Action.STOCHASTIC_SEED_OFFSET) * 101
            + int(time.time_ns() % 1_000_000_007)
        )
        rng = Action._makeRng(seed)

        def _uniform(delta: float) -> float:
            return float(rng.uniform(-abs(float(delta)), abs(float(delta))))

        jitter_entries: list[str] = []

        def _applyNumericJitter(key: str, delta: float, *, minimum: float | None = None, maximum: float | None = None) -> None:
            if key not in p:
                return
            try:
                old_float = float(p.get(key))
            except (TypeError, ValueError):
                return
            new_value = old_float + _uniform(delta)
            if minimum is not None:
                new_value = max(float(minimum), new_value)
            if maximum is not None:
                new_value = min(float(maximum), new_value)
            p[key] = float(new_value)
            jitter_entries.append(f"{key}:{old_float:.3f}->{new_value:.3f}")

        _applyNumericJitter("cx", max(0.15, float(w) * 0.01), minimum=0.0, maximum=float(w))
        _applyNumericJitter("cy", max(0.15, float(h) * 0.01), minimum=0.0, maximum=float(h))
        _applyNumericJitter("r", max(0.10, float(min(w, h)) * 0.008), minimum=1.0)
        _applyNumericJitter("stroke_circle", 0.12, minimum=0.4)
        _applyNumericJitter("arm_len", max(0.12, float(w) * 0.012), minimum=0.5, maximum=float(max(w, h)))
        _applyNumericJitter("arm_stroke", 0.12, minimum=0.4)
        _applyNumericJitter("stem_height", max(0.12, float(h) * 0.012), minimum=0.5, maximum=float(max(w, h)))
        _applyNumericJitter("stem_width", 0.12, minimum=0.4, maximum=float(max(1, w)))
        _applyNumericJitter("text_scale", 0.03, minimum=0.35, maximum=4.0)
        _applyNumericJitter("text_x", max(0.10, float(w) * 0.01), minimum=0.0, maximum=float(w))
        _applyNumericJitter("text_y", max(0.10, float(h) * 0.01), minimum=0.0, maximum=float(h))
        _applyNumericJitter("co2_dx", 0.08)
        _applyNumericJitter("co2_dy", 0.08)
        _applyNumericJitter("voc_scale", 0.03, minimum=0.35, maximum=4.0)

        p = Action._clampCircleInsideCanvas(p, w, h)
        if p.get("arm_enabled"):
            Action._reanchorArmToCircleEdge(p, float(p.get("r", 1.0)))
        if p.get("stem_enabled") and "cy" in p and "r" in p:
            p["stem_top"] = float(p.get("cy", 0.0)) + float(p.get("r", 0.0))

        if jitter_entries:
            variation_logs.append(
                "redraw_variation: seed="
                f"{seed} changed_params=" + " | ".join(jitter_entries)
            )
        return p, variation_logs

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
        name = getBaseNameFromFile(base_name).upper()

        if name == "AR0100":
            return semantic_ar0100_helpers.buildAr0100BadgeParamsImpl(
                w,
                h,
                ar0100_base=Action.AR0100_BASE,
                center_glyph_bbox_fn=Action._centerGlyphBbox,
            )

        ac08_params = semantic_ac08_param_helpers.makeAc08BadgeParamsImpl(
            w,
            h,
            name,
            img,
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
        )
        if ac08_params is not None:
            return ac08_params
        return None

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
        if SVG_RENDER_SUBPROCESS_ENABLED and not _is_fitz_open_monkeypatched():
            rendered = _render_svg_to_numpy_via_subprocess(svg_string, size_w, size_h)
            if rendered is not None:
                return rendered
            if _UNDER_PYTEST_RUNTIME and not _is_inprocess_renderer_monkeypatched():
                # Avoid unstable in-process PyMuPDF fallback in long pytest
                # sessions; dedicated tests can still exercise fallback by
                # monkeypatching the in-process renderer helper.
                return None
        return _render_svg_to_numpy_inprocess(svg_string, size_w, size_h)

    @staticmethod
    def createDiffImage(
        img_orig: np.ndarray,
        img_svg: np.ndarray,
        focus_mask: np.ndarray | None = None,
    ) -> np.ndarray:
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
        orig = img_orig.astype(np.int16)
        svg = img_svg.astype(np.int16)
        # Signed RGB sum difference as requested by the user:
        # dx = (r2-r1) + (g2-g1) + (b2-b1), normalized to [-1, 1].
        dx = np.sum(svg - orig, axis=2, dtype=np.int32).astype(np.float32)
        norm = np.clip(dx / (3.0 * 255.0), -1.0, 1.0)

        mask = None
        if focus_mask is not None:
            if focus_mask.shape[:2] != img_orig.shape[:2]:
                focus_mask = cv2.resize(
                    focus_mask.astype(np.uint8),
                    (img_orig.shape[1], img_orig.shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )
            mask = focus_mask > 0
            norm = np.where(mask, norm, 0.0)

        # Base tone comes from the mean luminance of both pixels.
        # This keeps identical bright pixels white, while identical dark pixels
        # stay dark instead of being forced to black or white.
        mean_tone = np.mean(np.concatenate((orig, svg), axis=2), axis=2).astype(np.float32)
        magnitude = np.clip(np.abs(norm), 0.0, 1.0)
        positive = norm >= 0.0

        # Interpolate from grayscale base tone towards signed endpoint colors.
        up = mean_tone + magnitude * (255.0 - mean_tone)
        down = mean_tone * (1.0 - magnitude)

        diff = np.zeros_like(img_orig)
        diff[:, :, 0] = np.where(positive, up, down).astype(np.uint8)
        diff[:, :, 1] = np.where(positive, up, down).astype(np.uint8)
        diff[:, :, 2] = np.where(positive, down, up).astype(np.uint8)
        if mask is not None:
            diff = np.where(mask[:, :, None], diff, 0)
        return diff

    @staticmethod
    def calculateError(img_orig: np.ndarray, img_svg: np.ndarray) -> float:
        if img_svg is None:
            return float("inf")
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
        return float(np.mean(cv2.absdiff(img_orig, img_svg)))

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
        h, w = img_orig.shape[:2]
        region_mask = Action._elementRegionMask(h, w, params, element)
        if region_mask is None:
            return None

        fg_bool = Action._foregroundMask(img_orig)
        mask = fg_bool & region_mask

        dilate_px = int(params.get("validation_mask_dilate_px", 0) or 0)
        if dilate_px > 0 and bool(params.get("ac08_small_variant_mode", False)):
            kernel_size = max(2, (dilate_px * 2) + 1)
            kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
            mask = cv2.dilate(mask.astype(np.uint8) * 255, kernel, iterations=1) > 0
            mask &= region_mask

        if int(mask.sum()) < 3:
            return None
        return mask

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
        """Element score for optimization: localization + redraw + symmetric compare.

        The score combines:
        - photometric difference in the union bbox of source/candidate element masks
        - overlap quality (IoU)
        - explicit penalties for missing source pixels and extra candidate pixels

        This keeps exploration broad, but accepts candidates only when the element
        truly matches better (not merely by shrinking or drifting outside the source mask).
        """
        if img_svg is None:
            return float("inf")
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)

        local_mask_orig = mask_orig if mask_orig is not None else Action.extract_badge_element_mask(img_orig, params, element)
        local_mask_svg = mask_svg if mask_svg is not None else Action.extract_badge_element_mask(img_svg, params, element)
        if local_mask_orig is None or local_mask_svg is None:
            return float("inf")

        orig_area = float(np.sum(local_mask_orig))
        svg_area = float(np.sum(local_mask_svg))
        if orig_area <= 0.0 or svg_area <= 0.0:
            return float("inf")

        photo_err = float(Action._maskedUnionErrorInBbox(img_orig, img_svg, local_mask_orig, local_mask_svg))
        if not math.isfinite(photo_err):
            return float("inf")

        inter = float(np.sum(local_mask_orig & local_mask_svg))
        union = float(np.sum(local_mask_orig | local_mask_svg))
        if union <= 0.0:
            return float("inf")

        miss = float(np.sum(local_mask_orig & (~local_mask_svg))) / orig_area
        extra = float(np.sum(local_mask_svg & (~local_mask_orig))) / orig_area
        if bool(params.get("ac08_small_variant_mode", False)):
            aa_bias = float(max(0.0, params.get("small_variant_antialias_bias", 0.0)))
            miss = max(0.0, miss - aa_bias)
            extra = max(0.0, extra - (aa_bias * 0.75))
        iou = inter / union

        # Normalize photometric term by source element area so comparisons stay
        # meaningful across sizes (S/M/L variants).
        photo_norm = photo_err / max(1.0, orig_area)

        # Circle optimization should prefer concentric matches and avoid shrinking
        # to the smallest ring that still overlaps the arm/label neighborhood.
        # The mask overlap terms above are necessary but can be too permissive
        # when anti-aliased JPEG edges blur circle/connector boundaries.
        if element == "circle" and apply_circle_geometry_penalty:
            src_circle = Action._maskCentroidRadius(local_mask_orig)
            cand_circle = Action._maskCentroidRadius(local_mask_svg)
            if src_circle is not None and cand_circle is not None:
                src_cx, src_cy, src_r = src_circle
                cand_cx, cand_cy, cand_r = cand_circle
                center_dist = float(math.hypot(cand_cx - src_cx, cand_cy - src_cy))
                center_norm = center_dist / max(1.0, src_r)
                # Penalize undersized rings more strongly than oversized ones so
                # AC0812-like badges keep a readable radius in optimization.
                undersize_ratio = max(0.0, (src_r - cand_r) / max(1.0, src_r))
                extra += undersize_ratio * 0.35
                miss += undersize_ratio * 0.45
                iou = max(0.0, iou - min(0.35, undersize_ratio * 0.55))
                photo_norm += center_norm * 2.8

        return float(photo_norm + (38.0 * miss) + (24.0 * extra) + (18.0 * (1.0 - iou)))

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
        """Evaluate full-image error for an already prepared badge parameter dict."""
        h, w = img_orig.shape[:2]
        render = Action._fitToOriginalSize(
            img_orig,
            Action.renderSvgToNumpy(Action.generateBadgeSvg(w, h, params), w, h),
        )
        if render is None:
            return float("inf")
        return float(Action.calculateError(img_orig, render))

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
    if cv2 is None or np is None:
        missing = []
        if cv2 is None:
            missing.append("cv2")
        if np is None:
            missing.append("numpy")
        raise RuntimeError(
            "Required image dependencies are missing: " + ", ".join(missing) + ". "
            "Install dependencies before running the conversion pipeline."
        )
    if fitz is None:
        raise RuntimeError(
            "Required SVG renderer dependency is missing: fitz (PyMuPDF). "
            "Install PyMuPDF before running the conversion pipeline."
        )

    folder_path = os.path.dirname(img_path)
    filename = os.path.basename(img_path)

    perc = Perception(img_path, csv_path)
    if perc.img is None:
        return None
    h, w = perc.img.shape[:2]

    ref = Reflection(perc.raw_desc)
    desc, params = ref.parse_description(perc.base_name, filename)
    semantic_audit_targets = {"AC0811", "AC0812", "AC0813", "AC0814"}
    semantic_audit_row: dict[str, object] | None = None
    if getBaseNameFromFile(perc.base_name).upper() in semantic_audit_targets:
        semantic_audit_row = _semanticAuditRecord(
            base_name=perc.base_name,
            filename=filename,
            description_fragments=list(params.get("description_fragments", [])),
            semantic_elements=list(params.get("elements", [])),
            status="semantic_pending",
            semantic_priority_order=list(params.get("semantic_priority_order", [])),
            semantic_conflicts=list(params.get("semantic_conflicts", [])),
            semantic_sources=dict(params.get("semantic_sources", {})),
        )

    if not desc.strip() and params["mode"] != "semantic_badge":
        print("  -> Überspringe Bild, da keine begleitende textliche Beschreibung vorliegt.")
        return None

    print(f"\n--- Verarbeite {filename} ---")
    description_fragments = params.get("description_fragments", [])
    description_text = " ".join(
        str(fragment.get("text", "")).strip()
        for fragment in description_fragments
        if isinstance(fragment, dict)
    ).strip()
    if description_text:
        print(f"Bildbeschreibung: {description_text}")
    elements = ", ".join(params["elements"]) if params["elements"] else "Kein Compositing-Befehl gefunden"
    print(f"Befehl erkannt: {elements}")

    os.makedirs(svg_out_dir, exist_ok=True)
    os.makedirs(diff_out_dir, exist_ok=True)
    if reports_out_dir:
        os.makedirs(reports_out_dir, exist_ok=True)

    base = os.path.splitext(filename)[0]
    log_path = None
    if reports_out_dir:
        log_path = os.path.join(reports_out_dir, f"{base}_element_validation.log")

    def _writeValidationLog(lines: list[str]) -> None:
        if not log_path:
            return
        payload = [
            (
                "run-meta: "
                f"run_seed={int(Action.STOCHASTIC_RUN_SEED)} "
                f"pass_seed_offset={int(Action.STOCHASTIC_SEED_OFFSET)} "
                f"nonce_ns={time.time_ns()}"
            )
        ]
        payload.extend(str(line) for line in lines)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(payload).rstrip() + "\n")

    def _paramsSnapshot(snapshot: dict[str, object]) -> str:
        return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, default=str)

    def _recordRenderFailure(reason: str, *, svg_content: str | None = None, params_snapshot: dict[str, object] | None = None) -> None:
        if svg_content:
            _writeAttemptArtifacts(svg_content, failed=True)
        lines = [
            "status=render_failure",
            f"failure_reason={reason}",
            f"filename={filename}",
        ]
        if svg_content:
            lines.append(f"best_attempt_svg={base}_failed.svg")
        if params_snapshot is not None:
            lines.append("params_snapshot=" + _paramsSnapshot(params_snapshot))
        _writeValidationLog(lines)

    def _writeAttemptArtifacts(svg_content: str, rendered_img=None, diff_img=None, *, failed: bool = False) -> None:
        suffix = "_failed" if failed else ""
        svg_path = os.path.join(svg_out_dir, f"{base}{suffix}.svg")
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        # Failed attempts are tracked in logs/leaderboard but should not emit
        # additional diff artifacts.
        if failed:
            return

        render = rendered_img
        if render is None:
            render = Action.render_svg_to_numpy(svg_content, w, h)
        if render is None:
            return
        diff = diff_img if diff_img is not None else Action.create_diff_image(perc.img, render)
        cv2.imwrite(os.path.join(diff_out_dir, f"{base}{suffix}_diff.png"), diff)

    if params["mode"] == "semantic_badge":
        badge_params = Action.make_badge_params(w, h, perc.base_name, perc.img)
        if badge_params is None:
            return None
        # Persist source raster dimensions so variant-specific finalizers can
        # enforce width/height-relative geometry rules reliably.
        badge_params.setdefault("width", float(w))
        badge_params.setdefault("height", float(h))
        badge_overrides = params.get("badge_overrides")
        if isinstance(badge_overrides, dict):
            badge_params.update(badge_overrides)

        semantic_issues = Action.validate_semantic_description_alignment(
            perc.img,
            list(params.get("elements", [])),
            badge_params,
        )
        if semantic_issues:
            failed_svg = Action.generate_badge_svg(w, h, badge_params)
            _writeAttemptArtifacts(failed_svg, failed=True)
            structural = Action._detect_semantic_primitives(perc.img, badge_params)
            connector_orientation = str(structural.get("connector_orientation", "unknown"))
            circle_source = str(structural.get("circle_detection_source", "unknown"))
            connector_debug_line = (
                "semantic_connector_classification="
                f"{connector_orientation};"
                f"circle_source={circle_source};"
                f"horizontal_candidates={int(structural.get('horizontal_line_candidates', 0) or 0)};"
                f"vertical_candidates={int(structural.get('vertical_line_candidates', 0) or 0)}"
            )
            print("[ERROR] Semantik-Abgleich fehlgeschlagen:")
            print(f"  - {connector_debug_line}")
            for issue in semantic_issues:
                print(f"  - {issue}")
            if semantic_audit_row is not None:
                semantic_audit_row = _semanticAuditRecord(
                    base_name=perc.base_name,
                    filename=filename,
                    description_fragments=list(params.get("description_fragments", [])),
                    semantic_elements=list(params.get("elements", [])),
                    status="semantic_mismatch",
                    mismatch_reasons=semantic_issues,
                    semantic_priority_order=list(params.get("semantic_priority_order", [])),
                    semantic_conflicts=list(params.get("semantic_conflicts", [])),
                    semantic_sources=dict(params.get("semantic_sources", {})),
                )
            _writeValidationLog(
                [
                    "status=semantic_mismatch",
                    f"best_attempt_svg={base}_failed.svg",
                    connector_debug_line,
                    *(
                        [
                            f"semantic_audit_status={semantic_audit_row.get('status', '')}",
                            "semantic_audit_lookup_keys=" + " | ".join(
                                str(value) for value in semantic_audit_row.get("description_lookup_keys", [])
                            ),
                            "semantic_audit_recognized_description_elements=" + " | ".join(
                                str(value) for value in semantic_audit_row.get("recognized_description_elements", [])
                            ),
                            "semantic_audit_derived_elements=" + " | ".join(
                                str(value) for value in semantic_audit_row.get("derived_elements", [])
                            ),
                            "semantic_audit_priority_order=" + " > ".join(
                                str(value) for value in semantic_audit_row.get("semantic_priority_order", [])
                            ),
                            "semantic_audit_conflicts=" + " | ".join(
                                str(value) for value in semantic_audit_row.get("semantic_conflicts", [])
                            ),
                            f"semantic_audit_mismatch_reason={semantic_audit_row.get('mismatch_reason', '')}",
                        ]
                        if semantic_audit_row is not None
                        else []
                    ),
                    *[f"issue={issue}" for issue in semantic_issues],
                ]
            )
            return None

        validation_logs: list[str] = []
        debug_dir = None
        if debug_element_diff_dir:
            debug_dir = os.path.join(debug_element_diff_dir, os.path.splitext(filename)[0])
            os.makedirs(debug_dir, exist_ok=True)
        elif debug_ac0811_dir and perc.base_name.upper() == "AC0811":
            debug_dir = os.path.join(debug_ac0811_dir, os.path.splitext(filename)[0])
            os.makedirs(debug_dir, exist_ok=True)
        if not bool(badge_params.get("draw_text", False)):
            validation_logs.append("semantic-guard: Text bewusst deaktiviert (plain-ring Familie ohne Buchstabe).")
        else:
            validation_logs.append(
                "semantic-guard: Textmodus aktiv ("
                + str(badge_params.get("text_mode", "unknown"))
                + ")."
            )
        validation_logs.extend(
            Action.validate_badge_by_elements(
            perc.img,
            badge_params,
            max_rounds=max(1, int(badge_validation_rounds)),
            debug_out_dir=debug_dir,
            )
        )
        badge_params = Action._enforce_semantic_connector_expectation(
            perc.base_name,
            list(params.get("elements", [])),
            badge_params,
            w,
            h,
        )
        badge_params, redraw_variation_logs = Action.apply_redraw_variation(badge_params, w, h)
        if badge_params.get("arm_enabled"):
            validation_logs.append(
                "semantic-guard: Erwartete Arm-Geometrie bestätigt/wiederhergestellt (z.B. AC0812 links)."
            )
        quality_flags = _semanticQualityFlags(perc.base_name, validation_logs)
        if semantic_audit_row is not None:
            semantic_audit_row = _semanticAuditRecord(
                base_name=perc.base_name,
                filename=filename,
                description_fragments=list(params.get("description_fragments", [])),
                semantic_elements=list(params.get("elements", [])),
                status="semantic_ok",
                semantic_priority_order=list(params.get("semantic_priority_order", [])),
                semantic_conflicts=list(params.get("semantic_conflicts", [])),
                semantic_sources=dict(params.get("semantic_sources", {})),
            )
        _writeValidationLog(
            [
                "status=semantic_ok",
                *(
                    [
                        f"semantic_audit_status={semantic_audit_row.get('status', '')}",
                        "semantic_audit_lookup_keys=" + " | ".join(
                            str(value) for value in semantic_audit_row.get("description_lookup_keys", [])
                        ),
                        "semantic_audit_recognized_description_elements=" + " | ".join(
                            str(value) for value in semantic_audit_row.get("recognized_description_elements", [])
                        ),
                        "semantic_audit_derived_elements=" + " | ".join(
                            str(value) for value in semantic_audit_row.get("derived_elements", [])
                        ),
                        "semantic_audit_priority_order=" + " > ".join(
                            str(value) for value in semantic_audit_row.get("semantic_priority_order", [])
                        ),
                        "semantic_audit_conflicts=" + " | ".join(
                            str(value) for value in semantic_audit_row.get("semantic_conflicts", [])
                        ),
                    ]
                    if semantic_audit_row is not None
                    else []
                ),
                *quality_flags,
                *redraw_variation_logs,
                *validation_logs,
            ]
        )

        svg_content = Action.generate_badge_svg(w, h, badge_params)
        svg_rendered = Action.render_svg_to_numpy(svg_content, w, h)
        if svg_rendered is None:
            _recordRenderFailure(
                "semantic_badge_final_render_failed",
                svg_content=svg_content,
                params_snapshot=badge_params,
            )
            return None
        _writeAttemptArtifacts(svg_content, svg_rendered)
        if semantic_audit_row is not None:
            params = copy.deepcopy(params)
            params["semantic_audit"] = semantic_audit_row
        return base, desc, params, 1, Action.calculate_error(perc.img, svg_rendered)

    if params["mode"] != "composite":
        if params["mode"] == "manual_review":
            reason = str(params.get("review_reason", "Manuelle Prüfung erforderlich.")).strip()
            print(f"  -> Überspringe Bild: {reason}")
            _writeValidationLog(
                [
                    "status=skipped_manual_review",
                    f"manual_review_reason={reason}",
                ]
            )
        else:
            print("  -> Überspringe Bild, da keine Zerschneide-Anweisung (Compositing) im Text vorliegt.")
            _writeValidationLog(["status=skipped_non_composite"])
        return None

    best_error = float("inf")
    best_svg = ""
    best_diff = None
    best_iter = 0

    epsilon_factors = np.linspace(0.05, 0.0005, max_iterations)
    plateau_tolerance = 1e-6
    min_plateau_iterations = min(max_iterations, 12)
    plateau_patience = min(max_iterations, max(8, max_iterations // 6))
    plateau_streak = 0
    previous_error: float | None = None
    stop_reason = "max_iterations"
    for i, eps in enumerate(epsilon_factors):
        svg_content = Action.generate_composite_svg(w, h, params, folder_path, float(eps))

        svg_rendered = Action.render_svg_to_numpy(svg_content, w, h)
        if svg_rendered is None:
            _recordRenderFailure(
                "composite_iteration_render_failed",
                svg_content=svg_content,
                params_snapshot=params,
            )
            return None
        error = Action.calculate_error(perc.img, svg_rendered)

        if previous_error is not None and abs(error - previous_error) <= plateau_tolerance:
            plateau_streak += 1
        else:
            plateau_streak = 0

        improved = error < best_error
        if improved or i == 0 or (i + 1) == max_iterations:
            print(f"  [Iter {i+1}/{max_iterations}] Epsilon={eps:.4f} -> Diff-Fehler: {error:.2f}")

        if improved:
            best_error, best_svg, best_iter = error, svg_content, i + 1
            best_diff = Action.create_diff_image(perc.img, svg_rendered)

        previous_error = error

        if (i + 1) >= min_plateau_iterations and plateau_streak >= plateau_patience:
            print(
                "  -> Früher Abbruch: Diff-Fehler blieb "
                f"{plateau_streak + 1} Iterationen innerhalb ±{plateau_tolerance:.0e}"
            )
            stop_reason = "plateau"
            break

    print(f"-> Bester Match in Iteration {best_iter} (Fehler auf {best_error:.2f} reduziert)")
    if stop_reason == "plateau":
        if best_iter <= 1:
            print("-> Konvergenzdiagnose: Plateau ohne messbare Verbesserung (Parameterraum ggf. erweitern)")
        else:
            print("-> Konvergenzdiagnose: Plateau nach Verbesserung erreicht (lokales Optimum wahrscheinlich)")
    else:
        print("-> Konvergenzdiagnose: Iterationsbudget ausgeschöpft (Optimum unklar, ggf. Suchraum erweitern)")

    if best_svg:
        _writeAttemptArtifacts(best_svg, diff_img=best_diff)

    _writeValidationLog([
        "status=composite_ok",
        f"convergence={stop_reason}",
        f"best_iter={int(best_iter)}",
        f"best_error={float(best_error):.6f}",
    ])
    return base, desc, params, best_iter, best_error


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
    """Return run-local RNG (seedable via env) for non-deterministic search order."""
    seed_raw = os.environ.get("TINY_ICC_RANDOM_SEED")
    if seed_raw is not None and str(seed_raw).strip() != "":
        try:
            return random.Random(int(str(seed_raw).strip()))
        except ValueError:
            pass
    return random.Random(time.time_ns())

def _defaultConvertedSymbolsRoot() -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(repo_root, "artifacts", "converted_images")


def _convertedSvgOutputDir(output_root: str) -> str:
    return os.path.join(output_root, "converted_svgs")


def _readValidationLogDetails(log_path: str) -> dict[str, str]:
    return batch_reporting_helpers.readValidationLogDetailsImpl(log_path)


def _writeBatchFailureSummary(reports_out_dir: str, failures: list[dict[str, str]]) -> None:
    return batch_reporting_helpers.writeBatchFailureSummaryImpl(reports_out_dir, failures)



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
    return os.path.join(output_root, "diff_pngs")


def _reportsOutputDir(output_root: str) -> str:
    return os.path.join(output_root, "reports")


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
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def _renderEmbeddedRasterSvg(input_path: str | Path) -> str:
    width, height = _sniffRasterSize(input_path)
    raw = Path(input_path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    mime = _svgHrefMimeType(input_path)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <image width="{width}" height="{height}" href="data:{mime};base64,{encoded}"/>\n'
        "</svg>\n"
    )


def _qualityConfigPath(reports_out_dir: str) -> str:
    return os.path.join(reports_out_dir, "quality_tercile_config.json")


def _loadQualityConfig(reports_out_dir: str) -> dict[str, object]:
    path = _qualityConfigPath(reports_out_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _writeQualityConfig(
    reports_out_dir: str,
    *,
    allowed_error_per_pixel: float,
    skipped_variants: list[str],
    source: str,
) -> None:
    path = _qualityConfigPath(reports_out_dir)
    normalized_error_pp = float(allowed_error_per_pixel) if math.isfinite(allowed_error_per_pixel) else 0.0
    payload = {
        "allowed_error_per_pixel": float(max(0.0, normalized_error_pp)),
        "skip_variants": sorted(set(skipped_variants)),
        "notes": (
            "Varianten in skip_variants werden in Folge-Pässen nicht erneut konvertiert. "
            "Loeschen der Datei setzt den Ablauf zurueck, dann werden wieder alle Bitmaps bearbeitet."
        ),
        "source": source,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


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
    filename = str(target_row.get("filename", ""))
    if not filename:
        return None, None

    img_path = os.path.join(folder_path, filename)
    img_orig = cv2.imread(img_path)
    if img_orig is None:
        return None, None

    h, w = img_orig.shape[:2]
    pixel_count = float(max(1, w * h))
    prev_error_pp = float(target_row.get("error_per_pixel", float("inf")))

    best_svg: str | None = None
    best_error = float(target_row.get("best_error", float("inf")))
    best_error_pp = prev_error_pp
    best_donor = ""
    best_rotation = 0
    best_scale = 1.0

    target_variant = str(target_row.get("variant", "")).upper()
    target_base = str(target_row.get("base", "")).upper()
    target_svg_path = os.path.join(svg_out_dir, f"{target_variant}.svg")
    target_svg_geometry = _readSvgGeometry(target_svg_path)
    target_geom_params = dict(target_svg_geometry[2]) if target_svg_geometry is not None else None
    target_params_raw = target_row.get("params")
    target_alias_refs: set[str] = set()
    if isinstance(target_params_raw, dict):
        alias_values = target_params_raw.get("documented_alias_refs", [])
        if isinstance(alias_values, list):
            target_alias_refs = {str(v).upper() for v in alias_values if str(v).strip()}
    target_is_semantic = isinstance(target_params_raw, dict) and str(target_params_raw.get("mode", "")) == "semantic_badge"
    ordered_donors = _rankTemplateTransferDonors(target_row, donor_rows)
    if rng is not None and not deterministic_order and len(ordered_donors) > 1:
        head = ordered_donors[:3]
        tail = ordered_donors[3:]
        rng.shuffle(head)
        ordered_donors = head + tail
    for donor in ordered_donors:
        donor_variant = str(donor.get("variant", "")).upper()
        donor_base = str(donor.get("base", "")).upper()
        if not donor_variant or donor_variant == target_variant:
            continue
        if not target_is_semantic and not _templateTransferDonorFamilyCompatible(
            target_base,
            donor_base,
            documented_alias_refs=target_alias_refs,
        ):
            continue
        donor_svg_path = os.path.join(svg_out_dir, f"{donor_variant}.svg")
        if not os.path.exists(donor_svg_path):
            continue
        try:
            donor_svg_text = open(donor_svg_path, "r", encoding="utf-8").read()
        except OSError:
            continue

        donor_svg_geometry = _readSvgGeometry(donor_svg_path)
        donor_geom_params = dict(donor_svg_geometry[2]) if donor_svg_geometry is not None else None

        donor_params_raw = donor.get("params")
        donor_is_semantic = isinstance(donor_params_raw, dict) and str(donor_params_raw.get("mode", "")) == "semantic_badge"
        if target_is_semantic and not donor_is_semantic:
            continue

        if isinstance(target_params_raw, dict) and isinstance(donor_params_raw, dict):
            if (
                target_is_semantic
                and donor_is_semantic
                and target_geom_params is not None
                and donor_geom_params is not None
                and _semanticTransferIsCompatible(dict(target_params_raw), dict(donor_params_raw))
            ):
                base_scale = float(min(w, h)) / max(1.0, float(min(int(donor.get("w", w)), int(donor.get("h", h)))))
                semantic_scales = _semanticTransferScaleCandidates(base_scale)
                if rng is not None and not deterministic_order:
                    keep = semantic_scales[:2]
                    rest = semantic_scales[2:]
                    rng.shuffle(rest)
                    semantic_scales = keep + rest
                for rotation in _semanticTransferRotations(dict(target_params_raw), dict(donor_params_raw)):
                    for scale in semantic_scales:
                        candidate_params = _semanticTransferBadgeParams(
                            dict(donor_geom_params),
                            dict(target_geom_params),
                            target_w=w,
                            target_h=h,
                            rotation_deg=rotation,
                            scale=float(scale),
                        )
                        try:
                            candidate_svg = Action.generateBadgeSvg(w, h, candidate_params)
                            rendered = Action.renderSvgToNumpy(candidate_svg, w, h)
                        except Exception:
                            continue
                        error = Action.calculateError(img_orig, rendered)
                        error_pp = float(error) / pixel_count
                        if error_pp + 1e-9 < best_error_pp:
                            best_error = float(error)
                            best_error_pp = error_pp
                            best_svg = candidate_svg
                            best_donor = donor_variant
                            best_rotation = rotation
                            best_scale = float(scale)

        if target_is_semantic:
            # Semantic badges encode meaning in connector/text geometry.
            # Generic donor SVG transforms can remove those semantics.
            continue

        estimated_scales = {
            rotation: _estimateTemplateTransferScale(
                img_orig,
                donor_svg_text,
                w,
                h,
                rotation_deg=rotation,
            )
            for rotation in (0, 90, 180, 270)
        }

        for rotation, scale in _templateTransferTransformCandidates(
            target_variant,
            donor_variant,
            estimated_scale_by_rotation=estimated_scales,
        ):
            candidate_svg = _buildTransformedSvgFromTemplate(
                donor_svg_text,
                w,
                h,
                rotation_deg=rotation,
                scale=scale,
            )
            rendered = Action.renderSvgToNumpy(candidate_svg, w, h)
            error = Action.calculateError(img_orig, rendered)
            error_pp = float(error) / pixel_count
            if error_pp + 1e-9 < best_error_pp:
                best_error = float(error)
                best_error_pp = error_pp
                best_svg = candidate_svg
                best_donor = donor_variant
                best_rotation = rotation
                best_scale = scale

    if best_svg is None:
        return None, None

    stem = os.path.splitext(filename)[0]
    svg_path = os.path.join(svg_out_dir, f"{stem}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(best_svg)

    rendered = Action.renderSvgToNumpy(best_svg, w, h)
    mean_delta2 = float(target_row.get("mean_delta2", float("inf")))
    std_delta2 = float(target_row.get("std_delta2", float("inf")))
    if rendered is not None:
        diff = Action.createDiffImage(img_orig, rendered)
        cv2.imwrite(os.path.join(diff_out_dir, f"{stem}_diff.png"), diff)
        try:
            mean_delta2, std_delta2 = Action.calculateDelta2Stats(img_orig, rendered)
        except Exception:
            mean_delta2 = float(target_row.get("mean_delta2", float("inf")))
            std_delta2 = float(target_row.get("std_delta2", float("inf")))

    updated_row = dict(target_row)
    updated_row["best_error"] = float(best_error)
    updated_row["error_per_pixel"] = float(best_error_pp)
    updated_row["mean_delta2"] = float(mean_delta2)
    updated_row["std_delta2"] = float(std_delta2)

    detail = {
        "filename": filename,
        "donor_variant": best_donor,
        "rotation_deg": int(best_rotation),
        "scale": float(best_scale),
        "old_error_per_pixel": float(prev_error_pp),
        "new_error_per_pixel": float(best_error_pp),
        "old_mean_delta2": float(target_row.get("mean_delta2", float("inf"))),
        "new_mean_delta2": float(mean_delta2),
    }
    return updated_row, detail


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

    normalized_selected_variants = {str(v).upper() for v in (selected_variants or set()) if str(v).strip()}
    files = sorted(
        f
        for f in os.listdir(folder_path)
        if f.lower().endswith((".bmp", ".jpg", ".png", ".gif"))
        and _inRequestedRange(f, start_ref, end_ref)
        and (not normalized_selected_variants or os.path.splitext(f)[0].upper() in normalized_selected_variants)
    )
    if cv2 is None or np is None:
        log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
        with open(log_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Dateiname", "Gefundene Elemente", "Beste Iteration", "Diff-Score", "FehlerProPixel"])
            for filename in files:
                stem = os.path.splitext(filename)[0]
                image_path = os.path.join(folder_path, filename)
                svg_content = _renderEmbeddedRasterSvg(image_path)
                svg_path = os.path.join(svg_out_dir, f"{stem}.svg")
                with open(svg_path, "w", encoding="utf-8") as svg_file:
                    svg_file.write(svg_content)
                if fitz is not None:
                    diff = _createDiffImageWithoutCv2(image_path, svg_content)
                    diff.save(os.path.join(diff_out_dir, f"{stem}_diff.png"))
                writer.writerow([filename, "embedded-raster", 0, "0.00", "0.00000000"])
        with open(os.path.join(reports_out_dir, "fallback_mode.txt"), "w", encoding="utf-8") as f:
            f.write(
                "Fallback-Modus aktiv: fehlende numpy/opencv-Abhängigkeiten; "
                "SVG-Dateien wurden als eingebettete Rasterbilder erzeugt"
                + (" und Differenzbilder via Pillow/PyMuPDF geschrieben.\n" if fitz is not None else ".\n")
            )
        generateConversionOverviews(diff_out_dir, svg_out_dir, reports_out_dir)
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
    max_quality_passes = 4
    quality_logs: list[dict[str, object]] = []
    result_map: dict[str, dict[str, object]] = {}
    conversion_bestlist_path = _conversionBestlistManifestPath(reports_out_dir)
    conversion_bestlist_rows = _readConversionBestlistMetrics(conversion_bestlist_path)
    batch_failures: list[dict[str, str]] = []
    stop_after_failure = False
    existing_donor_rows = _loadExistingConversionRows(out_root, folder_path)

    def _convertOne(filename: str, iteration_budget: int, badge_rounds: int) -> tuple[dict[str, object] | None, bool]:
        image_path = os.path.join(folder_path, filename)
        base = os.path.splitext(filename)[0]
        log_file = os.path.join(reports_out_dir, f"{base}_element_validation.log")
        try:
            res = runIterationPipeline(
                image_path,
                csv_path,
                max(1, int(iteration_budget)),
                svg_out_dir,
                diff_out_dir,
                reports_out_dir,
                debug_ac0811_dir,
                debug_element_diff_dir,
                badge_validation_rounds=max(1, int(badge_rounds)),
            )
        except Exception as exc:
            batch_failures.append(
                {
                    "filename": filename,
                    "status": "batch_error",
                    "reason": type(exc).__name__,
                    "details": str(exc),
                    "log_file": os.path.basename(log_file),
                }
            )
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"status=batch_error\nfilename={filename}\nreason={type(exc).__name__}\ndetails={exc}\n")
            print(f"[WARN] {filename}: Batchlauf setzt nach Fehler fort ({type(exc).__name__}: {exc})")
            return None, True
        if not res:
            details = _readValidationLogDetails(log_file)
            status = details.get("status", "")
            if status in {"render_failure", "batch_error"}:
                batch_failures.append(
                    {
                        "filename": filename,
                        "status": status,
                        "reason": details.get("failure_reason", details.get("reason", "unknown")),
                        "details": details.get("params_snapshot", details.get("details", "")),
                        "log_file": os.path.basename(log_file),
                    }
                )
                print(f"[WARN] {filename}: Fehler protokolliert, Batchlauf wird fortgesetzt ({status}).")
                return None, True
            if status == "semantic_mismatch":
                batch_failures.append(
                    {
                        "filename": filename,
                        "status": status,
                        "reason": "semantic_mismatch",
                        "details": details.get("issue", ""),
                        "log_file": os.path.basename(log_file),
                    }
                )
                print(f"[WARN] {filename}: Semantischer Fehlmatch, Batchlauf stoppt nach diesem Fehler.")
                return None, True
            return None, False

        _base, _desc, params, best_iter, best_error = res
        details = _readValidationLogDetails(log_file)
        img = cv2.imread(image_path)
        pixel_count = 1.0
        width = 0
        height = 0
        mean_delta2 = float("inf")
        std_delta2 = float("inf")
        if img is not None:
            height, width = img.shape[:2]
            pixel_count = float(max(1, width * height))
            svg_path = os.path.join(svg_out_dir, f"{os.path.splitext(filename)[0]}.svg")
            if os.path.exists(svg_path):
                try:
                    with open(svg_path, "r", encoding="utf-8") as f:
                        svg_content = f.read()
                except OSError:
                    svg_content = ""
                if svg_content:
                    rendered = Action.renderSvgToNumpy(svg_content, width, height)
                    mean_delta2, std_delta2 = Action.calculateDelta2Stats(img, rendered)

        return {
            "filename": filename,
            "params": params,
            "best_iter": int(best_iter),
            "best_error": float(best_error),
            "convergence": str(details.get("convergence", "")).strip().lower(),
            "error_per_pixel": float(best_error) / pixel_count,
            "mean_delta2": float(mean_delta2),
            "std_delta2": float(std_delta2),
            "w": int(width),
            "h": int(height),
            "base": getBaseNameFromFile(os.path.splitext(filename)[0]).upper(),
            "variant": os.path.splitext(filename)[0].upper(),
        }, False

    # Initial conversion pass for all forms.
    for filename in process_files:
        row, failed = _convertOne(filename, iteration_budget=base_iterations, badge_rounds=6)
        if failed:
            stop_after_failure = True
            break
        if row is None:
            continue

        donor_rows = [
            prev
            for key, prev in result_map.items()
            if key != filename and math.isfinite(float(prev.get("error_per_pixel", float("inf"))))
        ]
        donor_rows.extend(prev for prev in existing_donor_rows if str(prev.get("filename", "")) != filename)
        if donor_rows:
            transferred, _detail = _tryTemplateTransfer(
                target_row=row,
                donor_rows=donor_rows,
                folder_path=folder_path,
                svg_out_dir=svg_out_dir,
                diff_out_dir=diff_out_dir,
                rng=rng,
                deterministic_order=deterministic_order,
            )
            if transferred is not None and float(transferred.get("error_per_pixel", float("inf"))) + 1e-9 < float(row.get("error_per_pixel", float("inf"))):
                row = transferred

        variant = str(row.get("variant", "")).strip().upper()
        previous_row = conversion_bestlist_rows.get(variant)
        if _isConversionBestlistCandidateBetter(previous_row, row):
            result_map[filename] = row
            conversion_bestlist_rows[variant] = dict(row)
            _storeConversionBestlistSnapshot(variant, row, svg_out_dir, reports_out_dir)
        else:
            restored_row = _restoreConversionBestlistSnapshot(variant, svg_out_dir, reports_out_dir)
            if previous_row is not None:
                fallback_row = dict(row)
                for key in ("best_iter", "best_error", "error_per_pixel", "mean_delta2", "std_delta2", "status"):
                    if key in previous_row:
                        fallback_row[key] = previous_row[key]
                if isinstance(restored_row, dict):
                    for key in ("best_iter", "best_error", "error_per_pixel", "mean_delta2", "std_delta2", "status"):
                        if key in restored_row:
                            fallback_row[key] = restored_row[key]
                result_map[filename] = fallback_row
            else:
                result_map[filename] = row

    current_rows = [
        row
        for row in result_map.values()
        if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
    ]
    ranked_rows = sorted(current_rows, key=_qualitySortKey)
    first_cut = max(1, len(ranked_rows) // 3) if ranked_rows else 0
    initial_top_tercile = ranked_rows[:first_cut]
    initial_threshold = float(initial_top_tercile[-1]["error_per_pixel"]) if initial_top_tercile else float("inf")

    successful_threshold = _computeSuccessfulConversionsErrorThreshold(current_rows)
    threshold_source = "successful-conversions-mean-plus-2std"
    if not math.isfinite(successful_threshold):
        successful_threshold = initial_threshold
        threshold_source = "initial-first-tercile"

    cfg = _loadQualityConfig(reports_out_dir)
    allowed_error_pp = successful_threshold
    cfg_value = cfg.get("allowed_error_per_pixel")
    if cfg_value is not None:
        try:
            allowed_error_pp = max(0.0, float(cfg_value))
            threshold_source = "manual-config"
        except (TypeError, ValueError):
            allowed_error_pp = successful_threshold

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
    for pass_idx in range(1, max_quality_passes + 1):
        if stop_after_failure:
            break
        Action.STOCHASTIC_SEED_OFFSET = pass_idx
        current_rows = [
            row
            for row in result_map.values()
            if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
        ]
        candidates = _selectOpenQualityCases(
            current_rows,
            allowed_error_per_pixel=allowed_error_pp,
            skip_variants=skip_variants,
        )
        # Fallback to the historical selection when no explicit open set exists
        # (e.g. without threshold config).
        if not candidates:
            candidates = _selectMiddleLowerTercile(current_rows)
        if not candidates:
            break

        improved_in_pass = False
        iteration_budget, badge_rounds = _iterationStrategyForPass(pass_idx, base_iterations)
        if len(candidates) > 1 and not deterministic_order:
            rng.shuffle(candidates)
        for row in candidates:
            filename = str(row["filename"])
            adaptive_iteration_budget = _adaptiveIterationBudgetForQualityRow(row, iteration_budget)
            new_row, failed = _convertOne(filename, iteration_budget=adaptive_iteration_budget, badge_rounds=badge_rounds)
            if failed:
                stop_after_failure = True
                break
            if new_row is None:
                continue

            improved, decision, prev_error_pp, new_error_pp, prev_mean_delta2, new_mean_delta2 = _evaluateQualityPassCandidate(
                row,
                new_row,
            )
            if improved:
                result_map[filename] = new_row
                improved_in_pass = True
                variant = str(new_row.get("variant", "")).strip().upper()
                if variant:
                    conversion_bestlist_rows[variant] = dict(new_row)
                    _storeConversionBestlistSnapshot(variant, new_row, svg_out_dir, reports_out_dir)
            else:
                variant = str(row.get("variant", "")).strip().upper()
                if variant:
                    _restoreConversionBestlistSnapshot(variant, svg_out_dir, reports_out_dir)

            quality_logs.append(
                {
                    "pass": pass_idx,
                    "filename": filename,
                    "old_error_per_pixel": prev_error_pp,
                    "new_error_per_pixel": new_error_pp,
                    "old_mean_delta2": prev_mean_delta2,
                    "new_mean_delta2": new_mean_delta2,
                    "improved": improved,
                    "decision": decision,
                    "iteration_budget": adaptive_iteration_budget,
                    "badge_validation_rounds": badge_rounds,
                }
            )

        # Stop as soon as a full pass yields no strict improvement.
        if stop_after_failure or not improved_in_pass:
            break

    _writeQualityPassReport(reports_out_dir, quality_logs)
    _writeConversionBestlistMetrics(conversion_bestlist_path, conversion_bestlist_rows)
    _writeBatchFailureSummary(reports_out_dir, batch_failures)
    if strategy_logs:
        strategy_path = os.path.join(reports_out_dir, "strategy_switch_template_transfers.csv")
        with open(strategy_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([
                "filename",
                "donor_variant",
                "rotation_deg",
                "scale",
                "old_error_per_pixel",
                "new_error_per_pixel",
            ])
            for row in strategy_logs:
                writer.writerow([
                    row["filename"],
                    row["donor_variant"],
                    row["rotation_deg"],
                    f"{float(row['scale']):.4f}",
                    f"{float(row['old_error_per_pixel']):.8f}",
                    f"{float(row['new_error_per_pixel']):.8f}",
                ])

    log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    semantic_results: list[dict[str, object]] = []
    with open(log_path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Dateiname", "Gefundene Elemente", "Beste Iteration", "Diff-Score", "FehlerProPixel"])
        for filename in files:
            row = result_map.get(filename)
            if row is None:
                continue
            params = dict(row["params"])
            writer.writerow([
                filename,
                " + ".join(params.get("elements", [])),
                int(row["best_iter"]),
                f"{float(row['best_error']):.2f}",
                f"{float(row['error_per_pixel']):.8f}",
            ])

            if params.get("mode") == "semantic_badge":
                semantic_results.append(
                    {
                        "filename": filename,
                        "base": row["base"],
                        "variant": row["variant"],
                        "w": int(row.get("w", 0)),
                        "h": int(row.get("h", 0)),
                        "error": float(row["best_error"]),
                    }
                )

    _harmonizeSemanticSizeVariants(semantic_results, folder_path, svg_out_dir, reports_out_dir)
    semantic_audit_rows = [
        dict(audit)
        for row in result_map.values()
        for audit in [dict(row.get("params", {}).get("semantic_audit", {}))]
        if audit
    ]
    _writeSemanticAuditReport(reports_out_dir, semantic_audit_rows)
    _writePixelDelta2Ranking(folder_path, svg_out_dir, reports_out_dir)
    _writeAc08WeakFamilyStatusReport(
        reports_out_dir,
        selected_variants=sorted(normalized_selected_variants),
    )
    _writeAc08RegressionManifest(
        reports_out_dir,
        folder_path=folder_path,
        csv_path=csv_path,
        iterations=iterations,
        selected_variants=sorted(normalized_selected_variants),
    )
    ac08_success_gate = _writeAc08SuccessCriteriaReport(
        reports_out_dir,
        selected_variants=sorted(normalized_selected_variants),
    )
    if ac08_success_gate is not None:
        failed_criteria = [
            key
            for key in (
                "criterion_no_new_batch_aborts",
                "criterion_no_accepted_regressions",
                "criterion_validation_rounds_recorded",
                "criterion_regression_set_improved",
                "criterion_stable_families_not_worse",
            )
            if not bool(ac08_success_gate.get(key, False))
        ]
        if failed_criteria:
            print(
                "[WARN] AC08 success gate failed: "
                + ", ".join(failed_criteria)
                + f" (mean_validation_rounds_per_file={float(ac08_success_gate.get('mean_validation_rounds_per_file', 0.0)):.3f})"
            )
        else:
            print(
                "[INFO] AC08 success gate passed "
                f"(mean_validation_rounds_per_file={float(ac08_success_gate.get('mean_validation_rounds_per_file', 0.0)):.3f})."
            )
    if SUCCESSFUL_CONVERSIONS_MANIFEST.exists():
        updateSuccessfulConversionsManifestWithMetrics(
            folder_path=folder_path,
            svg_out_dir=svg_out_dir,
            reports_out_dir=reports_out_dir,
            manifest_path=SUCCESSFUL_CONVERSIONS_MANIFEST,
        )
    generated_overviews = generateConversionOverviews(diff_out_dir, svg_out_dir, reports_out_dir)
    if generated_overviews:
        print(
            "[INFO] Übersichts-Kacheln erzeugt: "
            + ", ".join(f"{key}={path}" for key, path in sorted(generated_overviews.items()))
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


def _readConversionBestlistMetrics(manifest_path: Path) -> dict[str, dict[str, object]]:
    return conversion_bestlist_helpers.readConversionBestlistMetricsImpl(manifest_path)


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

def _latestFailedConversionManifestEntry(reports_out_dir: str) -> dict[str, object] | None:
    return successful_conversions_helpers.latestFailedConversionManifestEntryImpl(reports_out_dir)


def updateSuccessfulConversionsManifestWithMetrics(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    manifest_path: Path | None = None,
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    """Update ``successful_conversions.txt`` as an in-place best list.

    New conversion data is only accepted when it improves the persisted quality
    metrics. Regressions are rejected, and whenever a previous best snapshot is
    available the converter output/log for that variant is restored so the
    working output stays aligned with the manifest.
    """
    resolved_manifest_path = Path(manifest_path) if manifest_path is not None else Path(reports_out_dir) / 'successful_conversions.txt'
    if not resolved_manifest_path.exists():
        raise FileNotFoundError(f'Successful-conversions manifest not found: {resolved_manifest_path}')

    previous_manifest_metrics = _readSuccessfulConversionManifestMetrics(resolved_manifest_path)
    metrics_rows = collectSuccessfulConversionQualityMetrics(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        successful_variants=successful_variants or _loadSuccessfulConversions(resolved_manifest_path),
    )

    accepted_metrics_by_variant: dict[str, dict[str, object]] = {}
    effective_metrics_rows: list[dict[str, object]] = []
    accepted_improved_variants: set[str] = set()
    for row in metrics_rows:
        variant = str(row['variant']).upper()
        previous_metrics = previous_manifest_metrics.get(variant)
        if _isSuccessfulConversionCandidateBetter(previous_metrics, row):
            accepted_metrics_by_variant[variant] = row
            effective_metrics_rows.append(row)
            accepted_improved_variants.add(variant)
            _storeSuccessfulConversionSnapshot(variant, row, svg_out_dir, reports_out_dir)
        else:
            if previous_metrics is not None:
                accepted_metrics_by_variant[variant] = previous_metrics
                effective_metrics_rows.append(_mergeSuccessfulConversionMetrics(row, previous_metrics))
            else:
                effective_metrics_rows.append(row)
            _restoreSuccessfulConversionSnapshot(variant, svg_out_dir, reports_out_dir)

    updated_lines: list[str] = []
    manifest_variants: set[str] = set()
    for raw_line in resolved_manifest_path.read_text(encoding='utf-8').splitlines():
        stripped = raw_line.split('#', 1)[0].strip()
        if not stripped:
            updated_lines.append(raw_line)
            continue
        variant = stripped.split(';', 1)[0].strip().upper()
        manifest_variants.add(variant)
        metrics = accepted_metrics_by_variant.get(variant)
        if metrics is None:
            updated_lines.append(raw_line)
            continue
        updated_lines.append(_formatSuccessfulConversionManifestLine(raw_line, metrics))

    missing_variants = [
        variant
        for variant in sorted(accepted_metrics_by_variant)
        if variant not in manifest_variants
    ]
    if missing_variants:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append('')
        for variant in missing_variants:
            updated_lines.append(
                _formatSuccessfulConversionManifestLine(
                    variant,
                    accepted_metrics_by_variant[variant],
                )
            )

    failed_entry = _latestFailedConversionManifestEntry(reports_out_dir)
    updated_without_failed = [
        line
        for line in updated_lines
        if "status=failed" not in line.lower()
    ]
    updated_lines = updated_without_failed
    if failed_entry is not None:
        failed_variant = str(failed_entry.get("variant", "")).strip().upper()
        failure_reason = str(failed_entry.get("failure_reason", "")).strip()
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        failed_line = f"{failed_variant} ; status=failed"
        if failure_reason:
            failed_line += f" ; reason={failure_reason}"
        updated_lines.append(failed_line)

    resolved_manifest_path.write_text('\n'.join(updated_lines) + '\n', encoding='utf-8')
    return resolved_manifest_path, _sortedSuccessfulConversionMetricsRows(effective_metrics_rows)

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
    manifest_path, metrics = updateSuccessfulConversionsManifestWithMetrics(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        successful_variants=successful_variants,
    )

    sorted_metrics = _sortedSuccessfulConversionMetricsRows(metrics)
    csv_path = _writeSuccessfulConversionCsvTable(
        os.path.join(reports_out_dir, f'{output_name}.csv'),
        sorted_metrics,
    )
    leaderboard_csv_path = _writeSuccessfulConversionCsvTable(
        os.path.join(reports_out_dir, 'successful_conversions.csv'),
        sorted_metrics,
    )
    txt_path = os.path.join(reports_out_dir, f'{output_name}.txt')

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f'manifest_path={manifest_path}\n')
        f.write(f'leaderboard_csv_path={leaderboard_csv_path}\n')
        f.write(f'variants_updated={len(sorted_metrics)}\n')
    return csv_path, txt_path, sorted_metrics


def parseArgs(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verarbeite einen Bildordner entweder im Analysemodus (Bounding-Boxes/JSON) "
            "oder im Konvertierungsmodus (SVG-/Diff-/Report-Ausgaben)."
        ),
        epilog=(
            "Beispiele:\n"
            "  python -m src.imageCompositeConverter artifacts/images_to_convert "
            "--descriptions-path artifacts/images_to_convert/Finale_Wurzelformen_V3.xml "
            "--output-dir artifacts/converted_images --start AC0000 --end ZZ9999\n"
            "  python -m src.imageCompositeConverter artifacts/images_to_convert "
            "--mode annotate --output-dir artifacts/annotated --start AC0811 --end AC0814\n"
            "  python -m src.imageCompositeConverter --print-linux-vendor-command --vendor-dir vendor"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=("annotate", "convert"),
        default="convert",
        help="annotate=markiere Kreis/Kellenstiel/Schrift und schreibe Koordinaten; convert=SVG-Konvertierung mit Reports",
    )
    parser.add_argument(
        "folder_path",
        nargs="?",
        default="artifacts/images_to_convert",
        help="Pfad zum Ordner mit den Bildern (Default: artifacts/images_to_convert)",
    )
    parser.add_argument(
        "csv_or_output",
        nargs="?",
        default=None,
        help=(
            "Optional: Pfad zur CSV/TSV/XML-Export-Tabelle ODER Ausgabeverzeichnis für konvertierte Dateien. "
            "(Kompatibilität: bisheriger 2. Positionsparameter)"
        ),
    )
    parser.add_argument(
        "iterations",
        nargs="?",
        type=int,
        default=128,
        help="Anzahl der Iterationen (optional, default: 128)",
    )
    parser.add_argument(
        "--csv-path",
        "--descriptions-path",
        dest="csv_path",
        default=None,
        help="Expliziter Pfad zur CSV/TSV/XML-Export-Tabelle mit den Beschreibungen",
    )
    parser.add_argument("--output-dir", default=None, help="Explizites Ausgabeverzeichnis")
    parser.add_argument(
        "--iterations",
        dest="iterations_override",
        type=int,
        default=None,
        help="Benannter Alias für die Iterationszahl; überschreibt den optionalen Positionswert",
    )
    parser.add_argument("--start", default=None, help="Start-Referenz (inkl.); wenn nicht gesetzt, erfolgt eine Konsolenabfrage")
    parser.add_argument("--end", default=None, help="End-Referenz (inkl.); wenn nicht gesetzt, erfolgt eine Konsolenabfrage")
    parser.add_argument(
        "--interactive-range",
        action="store_true",
        help=(
            "Fragt auf der Konsole 'Namen von' und 'Namen bis' ab und verarbeitet nur diesen Bereich. "
            "Wenn beide Eingaben keine volle Referenz sind, wird nach ihrem gemeinsamen Teilstring gefiltert "
            "(z. B. AC08 und A08 => alle A08*-Dateien)."
        ),
    )
    parser.add_argument(
        "--debug-ac0811-dir",
        default=None,
        help="Optional: Ordner für AC0811 Element-Diff-Dumps pro Runde/Element",
    )
    parser.add_argument(
        "--debug-element-diff-dir",
        default=None,
        help="Optional: Ordner für Element-Diff-Dumps pro Runde/Element für alle Semantic-Badges",
    )
    parser.add_argument(
        "--bootstrap-deps",
        action="store_true",
        help=(
            "Installiert fehlende Bild-Abhängigkeiten (numpy, opencv-python-headless) "
            "automatisch via pip vor der Konvertierung."
        ),
    )
    parser.add_argument(
        "--ac08-regression-set",
        action="store_true",
        help=(
            "Verarbeitet genau das feste AC08-Regression-Set ("
            f"{AC08_REGRESSION_SET_NAME}: {', '.join(AC08_REGRESSION_VARIANTS)})"
        ),
    )
    parser.add_argument(
        "--log-file",
        default=os.environ.get("IMAGE_COMPOSITE_CONVERTER_LOG_FILE", ""),
        help=(
            "Optional: Schreibt den kompletten Konsolen-Output zusätzlich in diese Datei. "
            "Kann alternativ über IMAGE_COMPOSITE_CONVERTER_LOG_FILE gesetzt werden."
        ),
    )
    parser.add_argument(
        "--print-linux-vendor-command",
        action="store_true",
        help=(
            "Gibt einen pip-Aufruf aus, der Linux-kompatible Wheels für numpy/opencv/Pillow/PyMuPDF "
            "in das Vendor-Verzeichnis installiert."
        ),
    )
    parser.add_argument("--vendor-dir", default="vendor", help="Zielordner für vendorte Python-Pakete")
    parser.add_argument(
        "--vendor-platform",
        default="manylinux2014_x86_64",
        help="pip --platform Wert für Linux-Wheels, z. B. manylinux2014_x86_64",
    )
    parser.add_argument(
        "--vendor-python-version",
        default=None,
        help="pip --python-version Wert ohne Punkt, z. B. 311 oder 312",
    )
    parser.add_argument(
        "--isolate-svg-render",
        action="store_true",
        help=(
            "Rendert SVGs in einem isolierten Subprozess, damit native PyMuPDF-"
            "Abstürze den Hauptlauf nicht beenden."
        ),
    )
    parser.add_argument(
        "--isolate-svg-render-timeout-sec",
        type=float,
        default=SVG_RENDER_SUBPROCESS_TIMEOUT_SEC,
        help="Timeout pro isoliertem SVG-Render-Aufruf in Sekunden (Default: 20).",
    )
    parser.add_argument(
        "--deterministic-order",
        action="store_true",
        help=(
            "Deaktiviert Shuffle-Schritte bei Dateireihenfolge/Template-Donor-Auswahl "
            "für reproduzierbare Diagnoseläufe."
        ),
    )
    parser.add_argument("--_render-svg-subprocess", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.iterations_override is not None:
        args.iterations = args.iterations_override
    delattr(args, "iterations_override")
    return args


class _TeeTextIO(io.TextIOBase):
    """Mirror text writes to multiple streams."""

    def __init__(self, *streams: io.TextIOBase):
        self._streams = streams

    def write(self, s: str) -> int:
        for stream in self._streams:
            stream.write(s)
        return len(s)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


@contextlib.contextmanager
def _optionalLogCapture(log_path: str):
    """Duplicate stdout/stderr into ``log_path`` if configured."""
    if not log_path:
        yield
        return

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as logfile:
        tee_stdout = _TeeTextIO(sys.stdout, logfile)
        tee_stderr = _TeeTextIO(sys.stderr, logfile)
        with contextlib.redirect_stdout(tee_stdout), contextlib.redirect_stderr(tee_stderr):
            print(f"[INFO] Schreibe Konsolen-Output nach: {path}")
            yield


def _autoDetectCsvPath(folder_path: str) -> str | None:
    """Best-effort table lookup for CLI compatibility mode.

    Priority:
    1) CSV/TSV/XML files directly inside ``folder_path``
    2) CSV/TSV/XML files in the parent directory of ``folder_path``
    """
    candidates: list[str] = []
    roots = [folder_path, os.path.dirname(folder_path)]
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            lower = name.lower()
            if lower.endswith(".csv") or lower.endswith(".tsv") or lower.endswith(".xml"):
                candidates.append(os.path.join(root, name))
        if candidates:
            break

    if not candidates:
        return None

    # Prefer obvious mapping files if several exist.
    preferred = [
        p
        for p in candidates
        if any(tag in os.path.basename(p).lower() for tag in ("reference", "roundtrip", "export", "mapping"))
    ]
    return preferred[0] if preferred else candidates[0]


def _resolveCliCsvAndOutput(args: argparse.Namespace) -> tuple[str, str | None]:
    """Resolve effective table path and output directory from mixed CLI styles."""
    csv_path = args.csv_path
    output_dir = args.output_dir
    if args.csv_or_output:
        c = str(args.csv_or_output)
        looks_like_csv = c.lower().endswith(".csv") or c.lower().endswith(".tsv") or c.lower().endswith(".xml")
        if csv_path is None and looks_like_csv:
            csv_path = c
        elif output_dir is None and not looks_like_csv:
            output_dir = c
        elif csv_path is None:
            csv_path = c

    if csv_path is None:
        csv_path = _autoDetectCsvPath(args.folder_path) or ""
    elif str(csv_path).lower().endswith(".xml"):
        csv_path = _resolveDescriptionXmlPath(csv_path) or csv_path

    return csv_path, output_dir


def _formatUserDiagnostic(exc: BaseException) -> str:
    """Render structured loader/runtime errors into one compact CLI message."""
    if isinstance(exc, DescriptionMappingError):
        if exc.span is not None:
            return f"{exc.message} Ort: {exc.span.format()}."
        return exc.message
    return str(exc)


def _promptInteractiveRange(args: argparse.Namespace) -> tuple[str, str]:
    current_start = str(args.start or "").strip()
    current_end = str(args.end or "").strip()
    prompt_start = f"Namen von [{current_start}]: " if current_start else "Namen von: "
    prompt_end = f"Namen bis [{current_end}]: " if current_end else "Namen bis: "

    start_value = input(prompt_start).strip() or current_start
    end_value = input(prompt_end).strip() or current_end
    if not end_value:
        end_value = start_value

    shared = _sharedPartialRangeToken(start_value, end_value)
    if shared and _extractRefParts(start_value) is None and _extractRefParts(end_value) is None:
        print(f"[INFO] Verwende Teilstring-Filter '{shared}' für die Auswahl der Bilder.")
    else:
        print(f"[INFO] Verwende Bereich von '{start_value or '(Anfang)'}' bis '{end_value or '(Ende)'}'.")
    return start_value, end_value


def main(argv: list[str] | None = None) -> int:
    args = parseArgs(argv)
    if bool(getattr(args, "_render_svg_subprocess", False)):
        return _runSvgRenderSubprocessEntrypoint()
    global SVG_RENDER_SUBPROCESS_ENABLED, SVG_RENDER_SUBPROCESS_TIMEOUT_SEC
    if bool(args.isolate_svg_render):
        SVG_RENDER_SUBPROCESS_ENABLED = True
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = max(1.0, float(args.isolate_svg_render_timeout_sec))
    log_path = str(args.log_file or "").strip()
    with _optionalLogCapture(log_path):
        try:
            if args.ac08_regression_set:
                args.start = "AC0000"
                args.end = "ZZ9999"

            if args.print_linux_vendor_command:
                print(
                    " ".join(
                        buildLinuxVendorInstallCommand(
                            vendor_dir=args.vendor_dir,
                            platform_tag=args.vendor_platform,
                            python_version=args.vendor_python_version,
                        )
                    )
                )
                return 0

            if args.interactive_range or args.start is None or args.end is None:
                args.start, args.end = _promptInteractiveRange(args)
            else:
                args.start = str(args.start or "").strip()
                args.end = str(args.end or "ZZZZZZ").strip() or args.start

            csv_path, output_dir = _resolveCliCsvAndOutput(args)

            if not csv_path:
                print("[WARN] Keine CSV/TSV/XML angegeben oder gefunden. Einige Symbole können ohne Beschreibung übersprungen werden.")
            elif not os.path.exists(csv_path):
                print(f"[WARN] CSV/TSV/XML-Datei nicht gefunden: {csv_path}")
            elif args.mode == "convert":
                # Validate user-supplied description data before the batch starts so
                # malformed files fail with a precise source location even when the
                # selected image range happens to be empty.
                _loadDescriptionMapping(csv_path)

            if args.bootstrap_deps:
                try:
                    installed = _bootstrapRequiredImageDependencies()
                except RuntimeError as exc:
                    print(f"[ERROR] {exc}")
                    return 2
                if installed:
                    print(f"[INFO] Installiert: {', '.join(installed)}")

            if args.ac08_regression_set:
                print(
                    "[INFO] Verwende festes AC08-Regression-Set "
                    f"{AC08_REGRESSION_SET_NAME}: {', '.join(AC08_REGRESSION_VARIANTS)}"
                )
            selected_variants = set(AC08_REGRESSION_VARIANTS) if args.ac08_regression_set else None

            if args.mode == "annotate":
                out_dir = analyzeRange(
                    args.folder_path,
                    output_root=output_dir,
                    start_ref=args.start,
                    end_ref=args.end,
                )
            else:
                out_dir = convertRange(
                    args.folder_path,
                    csv_path,
                    args.iterations,
                    args.start,
                    args.end,
                    args.debug_ac0811_dir,
                    args.debug_element_diff_dir,
                    output_dir,
                    selected_variants,
                    bool(args.deterministic_order),
                )
            print(f"\nAbgeschlossen! Ausgaben unter: {out_dir}")
            return 0
        except DescriptionMappingError as exc:
            print(f"[ERROR] {_formatUserDiagnostic(exc)}")
            return 2

def convertImage(input_path: str, output_path: str, *, max_iter: int = 120, plateau_limit: int = 14, seed: int = 42) -> Path:
    """Backward-compatible single-image entrypoint.

    - For raster targets (e.g. ``.png``), write an annotated image plus JSON coordinates.
    - For SVG targets or missing image deps, preserve the historical embedded-raster fallback.
    """
    del max_iter, plateau_limit, seed
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.suffix.lower() == ".svg" or cv2 is None or np is None:
        target.write_text(_renderEmbeddedRasterSvg(input_path), encoding="utf-8")
        return target

    img = cv2.imread(str(input_path))
    if img is None:
        raise FileNotFoundError(f"Bild konnte nicht gelesen werden: {input_path}")
    regions = detectRelevantRegions(img)
    annotated = annotateImageRegions(img, regions)
    cv2.imwrite(str(target), annotated)
    target.with_suffix(".json").write_text(json.dumps(regions, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def convertImageVariants(*args, **kwargs):
    """Compatibility shim kept for tooling imports."""
    return convertRange(*args, **kwargs)
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
