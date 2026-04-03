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
from src.iCCModules import imageCompositeConverterOptimizationGlobalVector as global_vector_optimization_helpers
from src.iCCModules import imageCompositeConverterMaskGeometry as mask_geometry_helpers
from src.iCCModules import imageCompositeConverterTemplateTransfer as template_transfer_helpers
from src.iCCModules import imageCompositeConverterSemanticHarmonization as semantic_harmonization_helpers
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
    hist = [0] * 256
    total = 0
    for row in grayscale:
        for value in row:
            hist[value] += 1
            total += 1
    if total == 0:
        return 220
    sum_total = sum(i * hist[i] for i in range(256))
    sum_bg = 0.0
    weight_bg = 0
    max_var = -1.0
    threshold = 220
    for t in range(256):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        between_var = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if between_var > max_var:
            max_var = between_var
            threshold = t
    return threshold


def _adaptiveThreshold(grayscale: list[list[int]], block_size: int = 15, c: int = 5) -> list[list[int]]:
    h = len(grayscale)
    w = len(grayscale[0]) if h else 0
    out = [[0] * w for _ in range(h)]
    r = block_size // 2
    for y in range(h):
        for x in range(w):
            y0, y1 = max(0, y-r), min(h, y+r+1)
            x0, x1 = max(0, x-r), min(w, x+r+1)
            vals = [grayscale[yy][xx] for yy in range(y0, y1) for xx in range(x0, x1)]
            thresh = (sum(vals) / max(1, len(vals))) - c
            out[y][x] = 1 if grayscale[y][x] < thresh else 0
    return out


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
    inter = union = 0
    for y in range(len(a)):
        for x in range(len(a[0])):
            av, bv = a[y][x], b[y][x]
            if av and bv:
                inter += 1
            if av or bv:
                union += 1
    return inter / union if union else 0.0


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
    def _parseSemanticBadgeLayoutOverrides(text: str) -> dict[str, float | str]:
        return semantic_helpers.parse_semantic_badge_layout_overrides(text)

    @staticmethod
    def _parse_semantic_badge_layout_overrides(text: str) -> dict[str, float | str]:
        return Reflection._parseSemanticBadgeLayoutOverrides(text)
def _renderSvgToNumpyInprocess(svg_string: str, size_w: int, size_h: int):
    if fitz is None or np is None or cv2 is None:
        return None

    svg_string = str(svg_string or "")
    if re.search(r"(?<![A-Za-z])(nan|inf)(?![A-Za-z])", svg_string, flags=re.IGNORECASE):
        return None

    attempts = [svg_string]
    normalized_svg = re.sub(r">\s+<", "><", svg_string.strip())
    if normalized_svg and normalized_svg != svg_string:
        attempts.append(normalized_svg)

    for candidate_svg in attempts:
        page = None
        pix = None
        try:
            with fitz.open("pdf", candidate_svg.encode("utf-8")) as doc:
                page = doc.load_page(0)
                zoom_x = size_w / page.rect.width if page.rect.width > 0 else 1
                zoom_y = size_h / page.rect.height if page.rect.height > 0 else 1
                mat = fitz.Matrix(zoom_x, zoom_y)
                pix = page.get_pixmap(matrix=mat, alpha=True)
            rgba = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 4).astype(np.float32)
            rgb = rgba[:, :, :3]
            alpha = (rgba[:, :, 3:4] / 255.0)
            # PyMuPDF's RGBA pixmap uses premultiplied RGB for alpha=True.
            # Composite onto white directly from premultiplied RGB.
            composited = rgb + (255.0 * (1.0 - alpha))
            composited = np.clip(composited, 0.0, 255.0)
            img = composited.astype(np.uint8)
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        except Exception:
            continue
        finally:
            # Free native MuPDF resources eagerly to avoid accumulation over
            # large AC08 range batches.
            if pix is not None:
                del pix
            if page is not None:
                del page
            gc.collect()
    return None


def _renderSvgToNumpyViaSubprocess(svg_string: str, size_w: int, size_h: int):
    if np is None:
        return None
    payload = json.dumps(
        {"svg": str(svg_string or ""), "w": int(size_w), "h": int(size_h)},
        ensure_ascii=False,
    ).encode("utf-8")
    cmd = [sys.executable, "-m", "src.imageCompositeConverter", "--_render-svg-subprocess"]
    try:
        completed = subprocess.run(
            cmd,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=SVG_RENDER_SUBPROCESS_TIMEOUT_SEC,
        )
    except Exception:
        return None
    if completed.returncode != 0 or not completed.stdout:
        return None
    try:
        response = json.loads(completed.stdout.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(response, dict) or not response.get("ok", False):
        return None
    try:
        w = int(response["w"])
        h = int(response["h"])
        raw = base64.b64decode(str(response["data"]).encode("ascii"))
        return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3).copy()
    except Exception:
        return None


def _render_svg_to_numpy_inprocess(svg_string: str, size_w: int, size_h: int):
    """Snake-case compatibility wrapper for tests and helper call sites."""
    return _renderSvgToNumpyInprocess(svg_string, size_w, size_h)


def _render_svg_to_numpy_via_subprocess(svg_string: str, size_w: int, size_h: int):
    """Snake-case compatibility wrapper for tests and helper call sites."""
    return _renderSvgToNumpyViaSubprocess(svg_string, size_w, size_h)


def _is_fitz_open_monkeypatched() -> bool:
    """Detect test monkeypatching so render failure tests can exercise in-process behavior."""
    if fitz is None:
        return False
    open_fn = getattr(fitz, "open", None)
    if open_fn is None:
        return False
    expected_module = getattr(fitz, "__name__", "")
    actual_module = getattr(open_fn, "__module__", "")
    if not actual_module:
        return False
    allowed_modules = {expected_module, "pymupdf", "fitz"}
    return actual_module not in allowed_modules


def _is_inprocess_renderer_monkeypatched() -> bool:
    inprocess_fn = globals().get("_renderSvgToNumpyInprocess")
    if inprocess_fn is None:
        return False
    module_name = getattr(inprocess_fn, "__module__", "")
    return bool(module_name) and module_name != __name__


def _bbox_to_dict(label: str, bbox: tuple[int, int, int, int], color: tuple[int, int, int]) -> dict[str, object]:
    """Snake-case compatibility helper kept for legacy tests and imports."""
    x0, y0, x1, y1 = bbox
    return {
        "label": label,
        "bbox": {
            "x0": int(x0),
            "y0": int(y0),
            "x1": int(x1),
            "y1": int(y1),
            "width": int(x1 - x0 + 1),
            "height": int(y1 - y0 + 1),
        },
        "color_bgr": [int(color[0]), int(color[1]), int(color[2])],
    }


def _runSvgRenderSubprocessEntrypoint() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    except Exception:
        return 2
    svg = str(payload.get("svg", ""))
    w = int(payload.get("w", 0))
    h = int(payload.get("h", 0))
    if w <= 0 or h <= 0:
        return 2
    rendered = _renderSvgToNumpyInprocess(svg, w, h)
    if rendered is None:
        sys.stdout.write('{"ok": false}\n')
        return 0
    response = {
        "ok": True,
        "w": int(rendered.shape[1]),
        "h": int(rendered.shape[0]),
        "data": base64.b64encode(rendered.tobytes()).decode("ascii"),
    }
    sys.stdout.write(json.dumps(response, separators=(",", ":")))
    return 0


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

    class _ScalarRng:
        def __init__(self, seed: int) -> None:
            self._rng = random.Random(int(seed))

        def uniform(self, low: float, high: float) -> float:
            return float(self._rng.uniform(float(low), float(high)))

        def normal(self, mean: float, sigma: float) -> float:
            return float(self._rng.gauss(float(mean), float(sigma)))

    @staticmethod
    def _makeRng(seed: int):
        if np is not None:
            return np.random.default_rng(int(seed))
        return Action._ScalarRng(int(seed))

    @staticmethod
    def _argminIndex(values: list[float]) -> int:
        return min(range(len(values)), key=lambda i: float(values[i]))

    @staticmethod
    def _snapIntPx(value: float, minimum: float = 1.0) -> float:
        return float(max(int(round(float(minimum))), int(round(float(value)))))

    @staticmethod
    def _maxCircleRadiusInsideCanvas(cx: float, cy: float, w: int, h: int, stroke: float = 0.0) -> float:
        """Return the largest circle radius that stays inside the SVG viewport."""
        if w <= 0 or h <= 0:
            return 1.0
        edge_margin = min(float(cx), float(w) - float(cx), float(cy), float(h) - float(cy))
        return float(max(1.0, edge_margin - (max(0.0, float(stroke)) / 2.0)))

    @staticmethod
    def _isCircleWithText(params: dict) -> bool:
        """Return True when the badge encodes a circle-with-text shape."""
        return bool(params.get("circle_enabled", True)) and bool(params.get("draw_text", False))

    @staticmethod
    def _applyCircleTextWidthConstraint(params: dict, radius: float, w: int) -> float:
        """Enforce CircleWithText constraint: 2 * radius < image width."""
        if not Action._isCircleWithText(params):
            return float(radius)
        # Keep a tiny strict margin so the optimized radius remains strictly below w/2.
        width_cap = (float(w) / 2.0) - 1e-3
        return float(min(float(radius), width_cap))

    @staticmethod
    def _applyCircleTextRadiusFloor(params: dict, radius: float) -> float:
        """Enforce CircleWithText lower bound: radius must exceed half text width."""
        if not Action._isCircleWithText(params):
            return float(radius)
        x1, _y1, x2, _y2 = Action._textBbox(params)
        text_width = max(0.0, float(x2) - float(x1))
        if text_width <= 0.0:
            return float(radius)
        # Keep strict inequality: radius > (text_width / 2).
        lower_bound = (text_width / 2.0) + 1e-3
        return float(max(float(radius), lower_bound))

    @staticmethod
    def _clampCircleInsideCanvas(params: dict, w: int, h: int) -> dict:
        """Clamp circle center/radius so no part of the ring exceeds the viewport."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(max(0.0, min(float(w), float(p.get("cx", 0.0)))))
        cy = float(max(0.0, min(float(h), float(p.get("cy", 0.0)))))
        stroke = float(p.get("stroke_circle", 0.0))
        max_r = Action._maxCircleRadiusInsideCanvas(cx, cy, w, h, stroke)
        max_r = Action._applyCircleTextWidthConstraint(p, max_r, w)
        min_r = float(
            max(
                1.0,
                float(p.get("min_circle_radius", 1.0)),
                float(p.get("circle_radius_lower_bound_px", 1.0)),
            )
        )
        min_r = Action._applyCircleTextRadiusFloor(p, min_r)
        if not bool(p.get("allow_circle_overflow", False)):
            min_r = min(min_r, max_r)

        p["cx"] = cx
        p["cy"] = cy
        if bool(p.get("allow_circle_overflow", False)):
            p["r"] = float(max(min_r, float(p.get("r", min_r))))
        else:
            p["r"] = float(max(min_r, min(max_r, float(p.get("r", min_r)))))
        return p

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
        """Keep circle+connector "lollipop" geometry centered around the connector axis."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(p["cx"])
        cy = float(p["cy"])
        r = float(p["r"])

        if p.get("stem_enabled") and "stem_width" in p:
            p["stem_x"] = cx - (float(p["stem_width"]) / 2.0)

        if p.get("arm_enabled") and all(k in p for k in ("arm_x1", "arm_y1", "arm_x2", "arm_y2")):
            x1 = float(p["arm_x1"])
            y1 = float(p["arm_y1"])
            x2 = float(p["arm_x2"])
            y2 = float(p["arm_y2"])

            vertical = abs(x2 - x1) <= abs(y2 - y1)
            if vertical:
                p["arm_x1"] = cx
                p["arm_x2"] = cx
                end_is_p2 = abs(y2 - cy) <= abs(y1 - cy)
                if end_is_p2:
                    p["arm_y2"] = cy - r if y1 <= cy else cy + r
                else:
                    p["arm_y1"] = cy - r if y2 <= cy else cy + r
            else:
                p["arm_y1"] = cy
                p["arm_y2"] = cy
                end_is_p2 = abs(x2 - cx) <= abs(x1 - cx)
                if end_is_p2:
                    p["arm_x2"] = cx - r if x1 <= cx else cx + r
                else:
                    p["arm_x1"] = cx - r if x2 <= cx else cx + r

        if "stem_x" in p and "stem_width" in p:
            p["stem_x"] = max(0.0, min(float(w) - float(p["stem_width"]), float(p["stem_x"])))
        for key in ("arm_x1", "arm_x2"):
            if key in p:
                p[key] = max(0.0, min(float(w), float(p[key])))
        for key in ("arm_y1", "arm_y2"):
            if key in p:
                p[key] = max(0.0, min(float(h), float(p[key])))
        return p

    @staticmethod
    def _quantizeBadgeParams(params: dict, w: int, h: int) -> dict:
        """Quantize geometry for bitmap-like sources.

        - Coordinates/lengths use 0.5px steps.
        - Line widths use integer pixel steps.
        """
        p = dict(params)
        raw_circle_radius = float(p["r"]) if p.get("circle_enabled", True) and "r" in p else None

        half_keys = (
            "cx",
            "cy",
            "r",
            "stem_x",
            "stem_top",
            "stem_bottom",
            "arm_x1",
            "arm_y1",
            "arm_x2",
            "arm_y2",
            "tx",
            "ty",
            "co2_dy",
        )
        for key in half_keys:
            if key in p:
                p[key] = Action._snapHalf(float(p[key]))

        int_width_keys = ("stroke_circle", "arm_stroke", "stem_width")
        for key in int_width_keys:
            if key in p:
                p[key] = Action._snapIntPx(float(p[key]), minimum=1.0)

        if "stem_width_max" in p:
            p["stem_width_max"] = max(1.0, Action._snapHalf(float(p["stem_width_max"])))

        if p.get("stem_enabled") and "cx" in p and "stem_width" in p:
            p["stem_x"] = Action._snapHalf(float(p["cx"]) - (float(p["stem_width"]) / 2.0))

        if "stem_x" in p and "stem_width" in p:
            p["stem_x"] = max(0.0, min(float(w) - float(p["stem_width"]), float(p["stem_x"])))
        if "stem_top" in p:
            p["stem_top"] = max(0.0, min(float(h), float(p["stem_top"])))
        if "stem_bottom" in p:
            p["stem_bottom"] = max(0.0, min(float(h), float(p["stem_bottom"])))

        p = Action._enforceCircleConnectorSymmetry(p, w, h)
        p = Action._clampCircleInsideCanvas(p, w, h)

        if (
            raw_circle_radius is not None
            and "cx" in p
            and "cy" in p
            and "r" in p
        ):
            canvas_fit_r = float(
                Action._maxCircleRadiusInsideCanvas(
                    float(p["cx"]),
                    float(p["cy"]),
                    w,
                    h,
                    float(p.get("stroke_circle", 0.0)),
                )
            )
            snapped_canvas_fit_r = float(Action._snapHalf(canvas_fit_r))
            radius_gap_to_canvas = canvas_fit_r - raw_circle_radius
            if (
                snapped_canvas_fit_r > float(p["r"])
                and radius_gap_to_canvas >= 0.0
                and radius_gap_to_canvas <= 0.5
                and (canvas_fit_r - float(p["r"])) <= 0.5
            ):
                p["r"] = float(
                    max(
                        float(p.get("min_circle_radius", 1.0)),
                        min(snapped_canvas_fit_r, canvas_fit_r),
                    )
                )

        # Symmetry enforcement may reintroduce non-snapped values.
        for key in half_keys:
            if key in p:
                p[key] = Action._snapHalf(float(p[key]))

        return p

    @staticmethod
    def _normalizeLightCircleColors(params: dict) -> dict:
        params["fill_gray"] = Action.LIGHT_CIRCLE_FILL_GRAY
        params["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        if params.get("stem_enabled"):
            params["stem_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        if params.get("draw_text", True) and "text_gray" in params:
            params["text_gray"] = Action.LIGHT_CIRCLE_TEXT_GRAY
        return params

    @staticmethod
    def _normalizeAc08LineWidths(params: dict) -> dict:
        """For AC08xx symbols: prefer a uniform 1px circle/connector stroke."""
        p = dict(params)
        prev_circle_stroke = float(p.get("stroke_circle", Action.AC08_STROKE_WIDTH_PX))
        p["stroke_circle"] = Action.AC08_STROKE_WIDTH_PX
        if bool(p.pop("preserve_outer_diameter_on_stroke_normalization", False)) and p.get("circle_enabled", True) and "r" in p and prev_circle_stroke > 0.0:
            # Keep the visual outer diameter stable when normalizing to the
            # canonical AC08 1px stroke. Otherwise tiny plain-ring badges can
            # lose more than a pixel of diameter even if the fitted geometry
            # correctly reached the canvas border.
            outer_radius = float(p["r"]) + (prev_circle_stroke / 2.0)
            p["r"] = max(1.0, outer_radius - (Action.AC08_STROKE_WIDTH_PX / 2.0))
        # Keep semantic AC08xx families on their canonical stroke thickness.
        # The later pixel-error bracketing step can otherwise over-fit anti-aliased
        # ring edges and inflate widths (e.g. 1px -> 6px for tiny circles).
        p["lock_stroke_widths"] = True
        if p.get("arm_enabled"):
            p["arm_stroke"] = Action.AC08_STROKE_WIDTH_PX
        if p.get("stem_enabled"):
            p["stem_width"] = Action.AC08_STROKE_WIDTH_PX
            if "cx" in p:
                p["stem_x"] = float(p["cx"]) - (Action.AC08_STROKE_WIDTH_PX / 2.0)
            p["stem_gray"] = int(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))
        return p

    @staticmethod
    def _estimateBorderBackgroundGray(gray: np.ndarray) -> float:
        """Estimate badge background tone from the outer image border pixels."""
        if gray.size == 0:
            return 255.0
        h, w = gray.shape
        if h < 2 or w < 2:
            return float(np.median(gray))
        border = np.concatenate((gray[0, :], gray[h - 1, :], gray[:, 0], gray[:, w - 1]))
        return float(np.median(border))

    @staticmethod
    def _estimateCircleTonesAndStroke(
        gray: np.ndarray,
        cx: float,
        cy: float,
        r: float,
        stroke_hint: float,
    ) -> tuple[float, float, float]:
        """Estimate fill/ring grayscale and stroke width for circular ring-like badges."""
        yy, xx = np.indices(gray.shape)
        dist = np.sqrt((xx - float(cx)) ** 2 + (yy - float(cy)) ** 2)

        inner_mask = dist <= max(1.0, float(r) * 0.78)
        fill_gray = float(np.median(gray[inner_mask])) if np.any(inner_mask) else float(np.median(gray))

        search_band = max(2.0, min(float(r) * 0.30, 5.0))
        ring_search = np.abs(dist - float(r)) <= search_band
        ring_vals = gray[ring_search] if np.any(ring_search) else gray
        ring_gray = float(np.median(ring_vals))

        # Prefer the darker contour around the estimated radius when present.
        dark_cut = fill_gray - 2.0
        dark_ring = ring_search & (gray <= dark_cut)
        if np.any(dark_ring):
            ring_gray = float(np.median(gray[dark_ring]))
            d = np.abs(dist - float(r))[dark_ring]
            stroke_est = float(max(1.0, min(6.0, np.percentile(d, 72) * 2.0)))
        else:
            stroke_est = float(max(1.0, min(6.0, stroke_hint)))

        return fill_gray, ring_gray, stroke_est

    @staticmethod
    def _persistConnectorLengthFloor(params: dict, element: str, default_ratio: float) -> None:
        """Persist a robust minimum connector length for later validation stages."""
        if element == "stem":
            length = float(params.get("stem_bottom", 0.0)) - float(params.get("stem_top", 0.0))
            min_key = "stem_len_min"
            ratio_key = "stem_len_min_ratio"
            template_length = float(params.get("template_stem_bottom", 0.0)) - float(params.get("template_stem_top", 0.0))
        elif element == "arm":
            x1 = float(params.get("arm_x1", 0.0))
            y1 = float(params.get("arm_y1", 0.0))
            x2 = float(params.get("arm_x2", 0.0))
            y2 = float(params.get("arm_y2", 0.0))
            length = float(math.hypot(x2 - x1, y2 - y1))
            min_key = "arm_len_min"
            ratio_key = "arm_len_min_ratio"
            tx1 = float(params.get("template_arm_x1", x1))
            ty1 = float(params.get("template_arm_y1", y1))
            tx2 = float(params.get("template_arm_x2", x2))
            ty2 = float(params.get("template_arm_y2", y2))
            template_length = float(math.hypot(tx2 - tx1, ty2 - ty1))
        else:
            return

        if length <= 0.0:
            return

        ratio = float(max(0.0, min(1.0, float(params.get(ratio_key, default_ratio)))))
        params[ratio_key] = ratio
        params[min_key] = float(max(float(params.get(min_key, 1.0)), length * ratio, template_length * ratio, 1.0))

    @staticmethod
    def _isAc08SmallVariant(name: str, params: dict) -> tuple[bool, str, float]:
        """Classify tiny AC08 variants so validation can use tighter `_S` heuristics."""
        normalized_name = str(name).upper()
        min_dim = float(min(float(params.get("width", 0.0) or 0.0), float(params.get("height", 0.0) or 0.0)))
        if min_dim <= 0.0:
            min_dim = max(1.0, float(params.get("r", 1.0)) * 2.0)

        variant_suffix = normalized_name.endswith("_S")
        dimension_small = min_dim <= 15.5
        is_small = variant_suffix or dimension_small
        if variant_suffix and dimension_small:
            reason = "variant_suffix+min_dim"
        elif variant_suffix:
            reason = "variant_suffix"
        elif dimension_small:
            reason = "min_dim"
        else:
            reason = "standard"
        return is_small, reason, min_dim

    @staticmethod
    def _configureAc08SmallVariantMode(name: str, params: dict) -> dict:
        """Apply `_S`-specific AC08 tuning for text, connector floors, and masks."""
        p = dict(params)
        is_small, reason, min_dim = Action._isAc08SmallVariant(name, p)
        p["ac08_small_variant_mode"] = bool(is_small)
        p["ac08_small_variant_reason"] = reason
        p["ac08_small_variant_min_dim"] = float(min_dim)
        if not is_small:
            return p

        p["validation_mask_dilate_px"] = int(max(1, int(p.get("validation_mask_dilate_px", 1))))
        p["small_variant_antialias_bias"] = float(max(0.0, float(p.get("small_variant_antialias_bias", 0.08))))

        if p.get("arm_enabled"):
            p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", 0.75)), 0.78))
            Action._persistConnectorLengthFloor(p, "arm", default_ratio=0.78)
        if p.get("stem_enabled"):
            p["stem_len_min_ratio"] = float(max(float(p.get("stem_len_min_ratio", 0.65)), 0.70))
            Action._persistConnectorLengthFloor(p, "stem", default_ratio=0.70)

        text_mode = str(p.get("text_mode", "")).lower()
        if text_mode == "co2":
            base_scale = float(p.get("co2_font_scale", 0.82))
            p["lock_text_scale"] = False
            p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.74, base_scale * 0.92)))
            p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.18)), min(1.10, base_scale * 1.12)))
            p["co2_subscript_offset_scale"] = float(min(float(p.get("co2_subscript_offset_scale", 0.24)), 0.24))
        elif text_mode == "voc":
            base_scale = float(p.get("voc_font_scale", 0.52))
            p["lock_text_scale"] = False
            p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.46, base_scale * 0.92)))
            p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.96)), min(0.96, base_scale * 1.10)))
        return p

    @staticmethod
    def _enforceTemplateCircleEdgeExtent(params: dict, w: int, h: int, *, anchor: str, retain_ratio: float = 0.97) -> dict:
        """Keep edge-anchored circles close to template edge reach.

        Generic safeguard for all edge-anchored connector families:
        if optimization shortens the anchored side too much (e.g. right arc on
        AC0812-like badges), raise `min_circle_radius` so the anchored contour
        keeps at least `retain_ratio` of the template extent.
        """
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "r" not in p:
            return p
        if "template_circle_cx" not in p or "template_circle_radius" not in p:
            return p

        retain_ratio = float(max(0.90, min(1.00, retain_ratio)))
        cx = float(p["cx"])
        template_cx = float(p["template_circle_cx"])
        template_r = max(1.0, float(p["template_circle_radius"]))
        stroke = float(max(0.0, p.get("stroke_circle", 0.0)))
        canvas_cap = float(Action._maxCircleRadiusInsideCanvas(cx, float(p.get("cy", float(h) / 2.0)), w, h, stroke))

        if anchor == "right":
            template_extent = template_cx + template_r
            required_extent = template_extent * retain_ratio
            required_r = required_extent - cx
        elif anchor == "left":
            template_extent = template_cx - template_r
            required_extent = template_extent + ((1.0 - retain_ratio) * abs(template_extent))
            required_r = cx - required_extent
        else:
            return p

        required_r = float(max(1.0, min(canvas_cap, required_r)))
        if required_r > 1.0:
            p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), required_r))
        return p


    @staticmethod
    def _tuneAc08LeftConnectorFamily(name: str, params: dict) -> dict:
        """Apply shared guardrails for left-connector AC08 families.

        Aufgabe 4.1 groups AC0812, AC0832, AC0837 and AC0882 because they all
        combine a circle on the right with a left-facing horizontal connector.
        The shared failure modes are:
        - the circle drifting left into the connector,
        - the arm collapsing until it becomes barely visible, and
        - text badges shrinking/offsetting once the circle geometry drifts.

        Keep those families on a common semantic baseline before variant-specific
        fine-tuning runs.
        """
        p = dict(params)
        symbol_name = getBaseNameFromFile(str(name)).upper().split("_", 1)[0]
        if symbol_name not in {"AC0812", "AC0832", "AC0837", "AC0882"}:
            return p

        p["connector_family_group"] = "ac08_left_connector"
        p["connector_family_direction"] = "left"
        p["lock_circle_cx"] = True
        p["lock_circle_cy"] = True
        if "template_circle_cx" in p:
            p["cx"] = float(p["template_circle_cx"])
        if "template_circle_cy" in p:
            p["cy"] = float(p["template_circle_cy"])

        has_text = bool(p.get("draw_text", False))
        text_mode = str(p.get("text_mode", "")).lower()
        is_small, _reason, min_dim = Action._isAc08SmallVariant(str(name), p)
        arm_ratio_floor = 0.82
        if has_text or text_mode == "path_t":
            arm_ratio_floor = 0.84
        if is_small:
            arm_ratio_floor = max(arm_ratio_floor, 0.86)
        p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", arm_ratio_floor)), arm_ratio_floor))

        template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
        radius_floor_ratio = 0.95 if not has_text else 0.93
        if is_small:
            radius_floor_ratio = max(radius_floor_ratio, 0.96 if not has_text else 0.94)
        p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))
        p = Action._enforceTemplateCircleEdgeExtent(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
            anchor="right",
            retain_ratio=0.97 if not is_small else 0.96,
        )

        p = Action._enforceLeftArmBadgeGeometry(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
        )

        if p.get("arm_enabled") and "cx" in p:
            max_from_arm_floor = max(1.0, float(p["cx"]) - float(p.get("arm_len_min", 1.0)))
            existing_max = float(p.get("max_circle_radius", 0.0) or 0.0)
            if existing_max > 0.0:
                p["max_circle_radius"] = float(min(existing_max, max_from_arm_floor))
            else:
                p["max_circle_radius"] = float(max_from_arm_floor)

        text_mode = str(p.get("text_mode", "")).lower()
        if text_mode == "co2":
            base_scale = float(p.get("co2_font_scale", 0.82))
            p["lock_text_scale"] = False
            p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.78, base_scale * 0.94)))
            p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.15)))
            p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "cluster"))
        elif text_mode == "voc":
            base_scale = float(p.get("voc_font_scale", 0.52))
            p["lock_text_scale"] = False
            p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.94)))
            p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.98)), min(0.98, base_scale * 1.14)))
        elif str(p.get("text_mode", "")).lower() == "path_t":
            p["s"] = float(max(float(p.get("s", 0.0)), 0.0088 if min_dim >= 18.0 else 0.0082))
            Action._centerGlyphBbox(p)
        return p

    @staticmethod
    def _tuneAc08RightConnectorFamily(name: str, params: dict) -> dict:
        """Apply shared guardrails for mirrored right-connector AC08 families.

        Aufgabe 4.2 groups AC0810, AC0814, AC0834, AC0838 and AC0839
        because they all place the circle on the left and extend the connector
        toward the right canvas edge. Their common regressions mirror the left
        connector family:
        - the circle drifts right into the connector span,
        - the arm collapses until the badge looks almost circular, and
        - tiny right-arm text badges drift down/right when text pixels dominate.

        Keep those mirrored families on one semantic baseline before applying
        family-specific CO₂/VOC or small-variant adjustments.
        """
        p = dict(params)
        symbol_name = getBaseNameFromFile(str(name)).upper().split("_", 1)[0]
        if symbol_name not in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"}:
            return p

        p["connector_family_group"] = "ac08_right_connector"
        p["connector_family_direction"] = "right"
        p["lock_circle_cx"] = True
        p["lock_circle_cy"] = True
        if "template_circle_cx" in p:
            p["cx"] = float(p["template_circle_cx"])
        if "template_circle_cy" in p:
            p["cy"] = float(p["template_circle_cy"])

        has_text = bool(p.get("draw_text", False))
        text_mode = str(p.get("text_mode", "")).lower()
        is_small, _reason, min_dim = Action._isAc08SmallVariant(str(name), p)
        arm_ratio_floor = 0.82
        if has_text or text_mode == "path_t":
            arm_ratio_floor = 0.84
        if is_small:
            arm_ratio_floor = max(arm_ratio_floor, 0.86)
        p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", arm_ratio_floor)), arm_ratio_floor))

        template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
        radius_floor_ratio = 0.95 if not has_text else 0.93
        if is_small:
            radius_floor_ratio = max(radius_floor_ratio, 0.96 if not has_text else 0.94)
        p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))
        p = Action._enforceTemplateCircleEdgeExtent(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
            anchor="left",
            retain_ratio=0.97 if not is_small else 0.96,
        )

        p = Action._enforceRightArmBadgeGeometry(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
        )

        if p.get("arm_enabled") and "cx" in p and "r" in p:
            canvas_width = float(p.get("width", 0.0) or p.get("badge_width", 0.0) or p.get("arm_x2", 0.0) or 1.0)
            right_extent = max(float(p["cx"]) + float(p["r"]), 0.0)
            max_from_arm_floor = max(1.0, canvas_width - float(p.get("arm_len_min", 1.0)) - float(p["cx"]))
            existing_max = float(p.get("max_circle_radius", 0.0) or 0.0)
            bounded_max = min(max_from_arm_floor, max(1.0, right_extent))
            if existing_max > 0.0:
                p["max_circle_radius"] = float(min(existing_max, bounded_max))
            else:
                p["max_circle_radius"] = float(bounded_max)

        text_mode = str(p.get("text_mode", "")).lower()
        if text_mode == "co2":
            base_scale = float(p.get("co2_font_scale", 0.82))
            p["lock_text_scale"] = False
            p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.78, base_scale * 0.94)))
            p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.15)))
            p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "cluster"))
        elif text_mode == "voc":
            base_scale = float(p.get("voc_font_scale", 0.52))
            p["lock_text_scale"] = False
            p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.94)))
            p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.98)), min(0.98, base_scale * 1.14)))
        return p

    @staticmethod
    def _enforceVerticalConnectorBadgeGeometry(params: dict, w: int, h: int) -> dict:
        """Ensure AC0811/AC0813-like badges keep a centered visible vertical connector."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(p["cx"])
        cy = float(p["cy"])
        r = float(p["r"])
        canvas_height = max(
            float(h),
            float(p.get("height", 0.0) or 0.0),
            float(p.get("badge_height", 0.0) or 0.0),
            float(p.get("stem_bottom", 0.0) or 0.0),
            cy + r,
        )

        if p.get("stem_enabled"):
            stem_width = float(max(1.0, p.get("stem_width", p.get("stroke_circle", Action.AC08_STROKE_WIDTH_PX))))
            p["stem_enabled"] = True
            p["stem_width"] = stem_width
            p["stem_x"] = cx - (stem_width / 2.0)
            p["stem_top"] = cy + r - (stem_width * 0.55)
            p["stem_bottom"] = canvas_height
            stem_len = float(max(0.0, canvas_height - (cy + r)))
            ratio = float(max(0.0, min(1.0, float(p.get("stem_len_min_ratio", 0.65)))))
            p["stem_len_min_ratio"] = ratio
            p["stem_len_min"] = float(max(1.0, float(p.get("stem_len_min", 1.0)), stem_len * ratio))

        if p.get("arm_enabled"):
            arm_stroke = float(max(1.0, p.get("arm_stroke", Action.AC08_STROKE_WIDTH_PX)))
            top_extent = max(0.0, cy - r)
            p["arm_enabled"] = True
            p["arm_stroke"] = arm_stroke
            p["arm_x1"] = cx
            p["arm_x2"] = cx
            p["arm_y1"] = 0.0
            p["arm_y2"] = top_extent
            arm_len = float(max(0.0, top_extent))
            ratio = float(max(0.0, min(1.0, float(p.get("arm_len_min_ratio", 0.75)))))
            p["arm_len_min_ratio"] = ratio
            p["arm_len_min"] = float(max(1.0, float(p.get("arm_len_min", 1.0)), arm_len * ratio))
        return p

    @staticmethod
    def _tuneAc08VerticalConnectorFamily(name: str, params: dict) -> dict:
        """Apply shared guardrails for AC08 families with vertical connectors.

        Aufgabe 4.3 groups AC0811, AC0813, AC0831, AC0833, AC0836 and AC0881 because
        they all depend on a vertical connector staying centered relative to the
        circle. Their main shared regressions are:
        - the stem/arm drifting sideways relative to the circle,
        - the vertical connector shrinking until the badge reads as plain circle,
        - text badges becoming top-heavy once circle and connector alignment drifts.
        """
        p = dict(params)
        symbol_name = getBaseNameFromFile(str(name)).upper().split("_", 1)[0]
        if symbol_name not in {"AC0811", "AC0813", "AC0831", "AC0833", "AC0836", "AC0881"}:
            return p

        p["connector_family_group"] = "ac08_vertical_connector"
        p["connector_family_direction"] = "vertical"
        if symbol_name in {"AC0811", "AC0831", "AC0836", "AC0881"}:
            p["stem_enabled"] = True
            p.pop("arm_enabled", None)
        elif symbol_name in {"AC0813", "AC0833"}:
            p["arm_enabled"] = True
        p["lock_circle_cx"] = True
        p["lock_circle_cy"] = True
        p["lock_stem_center_to_circle"] = bool(p.get("stem_enabled", False))
        p["lock_arm_center_to_circle"] = bool(p.get("arm_enabled", False))
        if "template_circle_cx" in p:
            p["cx"] = float(p["template_circle_cx"])
        if "template_circle_cy" in p:
            p["cy"] = float(p["template_circle_cy"])

        has_text = bool(p.get("draw_text", False))
        is_small, _reason, min_dim = Action._isAc08SmallVariant(str(name), p)
        template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
        radius_floor_ratio = 0.95 if not has_text else 0.93
        if is_small:
            radius_floor_ratio = max(radius_floor_ratio, 0.96 if not has_text else 0.95)
        p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))

        if p.get("stem_enabled"):
            stem_ratio_floor = 0.70 if not has_text else 0.72
            if is_small:
                stem_ratio_floor = max(stem_ratio_floor, 0.74)
            p["stem_len_min_ratio"] = float(max(float(p.get("stem_len_min_ratio", stem_ratio_floor)), stem_ratio_floor))
        if p.get("arm_enabled"):
            arm_ratio_floor = 0.78 if not has_text else 0.80
            if is_small:
                arm_ratio_floor = max(arm_ratio_floor, 0.82)
            p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", arm_ratio_floor)), arm_ratio_floor))

        p = Action._enforceVerticalConnectorBadgeGeometry(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
        )

        text_mode = str(p.get("text_mode", "")).lower()
        if text_mode == "co2":
            base_scale = float(p.get("co2_font_scale", 0.82))
            p["lock_text_scale"] = False
            p["co2_anchor_mode"] = "cluster"
            p["co2_optical_bias"] = float(max(float(p.get("co2_optical_bias", 0.10)), 0.10))
            p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.05 * template_r if min_dim > 0.0 else 0.0))
            p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.78, base_scale * 0.94)))
            p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.15)))
        elif text_mode == "voc":
            base_scale = float(p.get("voc_font_scale", 0.52))
            p["lock_text_scale"] = False
            p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.94)))
            p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.98)), min(0.98, base_scale * 1.14)))
        return p

    @staticmethod
    def _tuneAc08CircleTextFamily(name: str, params: dict) -> dict:
        """Apply shared guardrails for connector-free AC08 circle/text badges.

        Aufgabe 4.4 groups AC0820, AC0835 and AC0870 because they all:
        - have no connector geometry that should influence circle fitting,
        - regress when text blobs pull the circle away from the semantic center,
        - need stable text scaling without letting the ring collapse or overgrow.
        """
        p = dict(params)
        symbol_name = getBaseNameFromFile(str(name)).upper().split("_", 1)[0]
        if symbol_name not in {"AC0820", "AC0835", "AC0870"}:
            return p

        p["connector_family_group"] = "ac08_circle_text"
        p["connector_family_direction"] = "centered"
        p["lock_circle_cx"] = True
        p["lock_circle_cy"] = True

        if "template_circle_cx" in p:
            p["cx"] = float(p["template_circle_cx"])
        if "template_circle_cy" in p:
            p["cy"] = float(p["template_circle_cy"])

        template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
        min_dim = float(
            min(
                float(p.get("width", 0.0) or 0.0),
                float(p.get("height", 0.0) or 0.0),
            )
        )
        if min_dim <= 0.0:
            min_dim = max(1.0, template_r * 2.0)

        text_mode = str(p.get("text_mode", "")).lower()
        radius_floor_ratio = 0.94 if text_mode in {"co2", "voc"} else 0.96
        p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), template_r * radius_floor_ratio))

        canvas_w = int(round(float(p.get("width", 0.0) or p.get("badge_width", 0.0) or min_dim)))
        canvas_h = int(round(float(p.get("height", 0.0) or p.get("badge_height", 0.0) or min_dim)))
        if canvas_w > 0 and canvas_h > 0 and "cx" in p and "cy" in p:
            canvas_cap = Action._maxCircleRadiusInsideCanvas(
                float(p["cx"]),
                float(p["cy"]),
                canvas_w,
                canvas_h,
                float(p.get("stroke_circle", 1.0)),
            )
            relaxed_cap = max(template_r * 1.08, float(p.get("max_circle_radius", 0.0) or 0.0))
            p["max_circle_radius"] = float(min(canvas_cap, relaxed_cap)) if canvas_cap > 0.0 else float(relaxed_cap)

        if text_mode == "co2":
            base_scale = float(p.get("co2_font_scale", 0.94 if symbol_name == "AC0820" else 0.88))
            p["lock_text_scale"] = False
            p["co2_anchor_mode"] = "cluster"
            p["co2_optical_bias"] = float(max(float(p.get("co2_optical_bias", 0.125)), 0.125 if symbol_name == "AC0820" else 0.10))
            p["co2_dy"] = float(max(-0.06 * template_r, min(0.16 * template_r, float(p.get("co2_dy", 0.03 * template_r)))))
            p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.84, base_scale * 0.92)))
            p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.18)))
        elif text_mode == "voc":
            base_scale = float(p.get("voc_font_scale", 0.52))
            p["lock_text_scale"] = False
            p["voc_dy"] = float(max(-0.06 * template_r, min(0.08 * template_r, float(p.get("voc_dy", 0.0)))))
            if min_dim <= 15.5:
                p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.96)))
                p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.92)), min(0.92, max(base_scale, 0.52) * 1.05)))
            else:
                p["voc_font_scale"] = float(max(base_scale, 0.60))
                p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", p["voc_font_scale"])), 0.60))
                p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 1.02)), 1.02))
        else:
            p["s"] = float(max(float(p.get("s", 0.0100)), 0.0100))
            Action._centerGlyphBbox(p)

        return p

    @staticmethod
    def _finalizeAc08Style(name: str, params: dict) -> dict:
        """Apply AC08xx palette/stroke conventions globally for semantic conversions."""
        canonical_name = str(name).upper()
        symbol_name = canonical_name.split("_", 1)[0]
        if not symbol_name.startswith("AC08"):
            return params
        p = Action._captureCanonicalBadgeColors(Action._normalizeLightCircleColors(dict(params)))
        p["badge_symbol_name"] = symbol_name
        # During geometry fitting we intentionally keep auto-estimated colors.
        # Canonical palette values are re-applied once fitting converged.
        p = Action._normalizeAc08LineWidths(p)
        p["lock_colors"] = True
        p = Action._normalizeCenteredCo2Label(p)
        if symbol_name == "AC0831" and str(p.get("text_mode", "")).lower() == "co2":
            p["fill_gray"] = 238
            p["stroke_gray"] = 155
            p["text_gray"] = 155
            if p.get("stem_enabled"):
                p["stem_gray"] = 155
        if symbol_name == "AC0833" and str(p.get("text_mode", "")).lower() == "co2":
            p = Action._tuneAc0833Co2Badge(p)
        if symbol_name == "AC0820" and str(p.get("text_mode", "")).lower() == "co2":
            # AC0820 variants (L/M/S): keep CO² superscript rendering, but do
            # not force a centered anchor mode. The optimizer may keep center_co
            # or drift via co2_dx/co2_dy to best match the source glyph raster.
            p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "center_co"))
            # AC0820 references render CO² with a raised "2" (superscript),
            # including AC0820_L where a subscript drifts visually too low.
            p["co2_index_mode"] = "superscript"
            p["co2_superscript_offset_scale"] = float(min(float(p.get("co2_superscript_offset_scale", 0.16)), 0.18))
            # Keep the raised "2" detached from the trailing "O" in AC0820_M/S
            # where antialiasing can visually merge both glyphs.
            p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.16)), 0.16))
            p["co2_optical_bias"] = 0.125
            r = max(1.0, float(p.get("r", 1.0)))
            # Keep AC0820 text close to the cap-height used by centered path
            # glyph labels (e.g. single C) so the leading "C" is no longer
            # undersized compared to the original badge family.
            if r >= 10.0:
                p["co2_font_scale"] = 0.82
            elif r >= 6.0:
                p["co2_font_scale"] = 0.84
            else:
                p["co2_font_scale"] = 0.86
            # Keep AC0820_M/S adjustable in validation: the tiny CO run can still
            # be slightly undersized after geometric fitting, but we do not want
            # unconstrained growth that reintroduces prior over-scaling regressions.
            base_scale = float(p["co2_font_scale"])
            p["co2_font_scale_min"] = float(max(0.84, base_scale * 0.92))
            p["co2_font_scale_max"] = float(min(1.12, base_scale * 1.22))
            # AC0820 references use a slightly narrower CO² wordmark than the
            # generic Arial fallback. Apply a mild horizontal squeeze so the
            # reconstructed text width tracks the source more closely.
            if r >= 10.0:
                p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.90)), 0.90))
            elif r >= 6.0:
                p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.92)), 0.92))
            else:
                p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.94)), 0.94))
            p["co2_sub_font_scale"] = float(p.get("co2_sub_font_scale", 66.0))
            p["co2_subscript_offset_scale"] = 0.27
            template_r = float(p.get("template_circle_radius", r))
            # AC0820_L can otherwise collapse to a tiny ring in unconstrained
            # rounds. Keep the rendered radius close to the source template
            # without reintroducing global min/max guardrail metadata.
            min_radius_ratio = 1.0 if template_r >= 10.0 else 0.95
            p["r"] = float(max(float(p.get("r", template_r)), template_r * min_radius_ratio))
            image_width = float(p.get("width", p.get("badge_width", 0.0)) or 0.0)
            # General large-badge tuning (not variant-specific): for centered
            # CO² labels without connectors, a mildly tighter/lower baseline
            # produces better visual agreement across anti-aliased inputs.
            large_centered_co2 = (
                bool(p.get("circle_enabled", True))
                and not bool(p.get("arm_enabled") or p.get("stem_enabled"))
                and str(p.get("co2_anchor_mode", "center_co")).lower() == "center_co"
                and template_r >= 10.0
            )
            if large_centered_co2:
                p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.89)), 0.89))
                p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.03 * template_r))
                p["co2_center_co_bias"] = float(min(float(p.get("co2_center_co_bias", -0.05)), -0.05))
            if _needsLargeCircleOverflowGuard(p) and image_width > 0.0:
                # Generic large centered CO² rule: keep circle radius template-led
                # while enforcing the product constraint that the diameter stays
                # larger than half the badge width.
                #   2r > (w / 2)  =>  r > (w / 4)
                required_r = (image_width / 4.0) + 1e-3
                p["r"] = float(max(float(p.get("r", template_r)), template_r * 0.98, required_r))
                p["circle_radius_lower_bound_px"] = float(
                    max(float(p.get("circle_radius_lower_bound_px", 1.0)), required_r)
                )
        if p.get("circle_enabled", True):
            has_connector = bool(p.get("arm_enabled") or p.get("stem_enabled"))
            has_text = bool(p.get("draw_text", False))
            aspect_ratio = 1.0
            badge_w = float(p.get("badge_width", 0.0))
            badge_h = float(p.get("badge_height", 0.0))
            if badge_w <= 0.0 or badge_h <= 0.0:
                circle_diameter = max(1.0, float(p.get("r", 1.0)) * 2.0)
                extent_w = circle_diameter
                extent_h = circle_diameter
                if p.get("stem_enabled"):
                    stem_top = float(p.get("stem_top", float(p.get("cy", 0.0)) + float(p.get("r", 0.0))))
                    stem_bottom = float(p.get("stem_bottom", stem_top))
                    extent_h = max(extent_h, max(1.0, stem_bottom))
                if p.get("arm_enabled"):
                    arm_x1 = float(p.get("arm_x1", float(p.get("cx", 0.0)) - float(p.get("r", 0.0))))
                    arm_x2 = float(p.get("arm_x2", float(p.get("cx", 0.0)) + float(p.get("r", 0.0))))
                    arm_y1 = float(p.get("arm_y1", float(p.get("cy", 0.0))))
                    arm_y2 = float(p.get("arm_y2", float(p.get("cy", 0.0))))
                    extent_w = max(extent_w, abs(arm_x2 - arm_x1), max(abs(arm_x1), abs(arm_x2)))
                    extent_h = max(extent_h, abs(arm_y2 - arm_y1), max(abs(arm_y1), abs(arm_y2)))
                badge_w = extent_w
                badge_h = extent_h
            if badge_w > 0.0 and badge_h > 0.0:
                aspect_ratio = badge_w / badge_h

            # For all semantic AC08xx badges, keep a robust radius floor anchored
            # to the template geometry. This prevents degenerate late-stage fits
            # where noisy masks shrink circles far below their known base size.
            template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
            current_r = float(p.get("r", template_r))
            base_r = max(1.0, template_r, current_r)
            min_ratio = 0.88
            if has_text:
                # Text badges are especially sensitive to circle shrink because
                # the label scales relative to the interior diameter.
                min_ratio = 0.92 if symbol_name == "AC0820" else 0.90
            elif has_connector and (aspect_ratio >= 1.60 or aspect_ratio <= (1.0 / 1.60)):
                # Strongly elongated connector badges are vulnerable to the
                # circle-only mask under-estimating the ring and collapsing the
                # circle toward the connector. Keep them closer to the semantic
                # template while still allowing modest adaptation.
                min_ratio = 0.95
            p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), base_r * min_ratio))

            # Plain centered badges should keep their circle optically centered.
            # Otherwise min-rect alignment may drift the ring into a corner,
            # which also makes CO/VOC labels look far too small.
            if not has_connector:
                p["lock_circle_cx"] = True
                p["lock_circle_cy"] = True

            # Connector-only and connector+text badges can both lose connector
            # extraction in noisy JPEGs. Without geometric anchors the circle
            # optimizer may collapse toward unrelated border blobs (for plain
            # symbols) or text blobs (for labeled symbols). Keep the center and
            # connector alignment locked to template semantics for all connector
            # families so rotations/reflections/scales remain stable.
            if has_connector:
                p["lock_circle_cx"] = True
                p["lock_circle_cy"] = True
                if p.get("stem_enabled"):
                    p["lock_stem_center_to_circle"] = True
                    p["stem_center_lock_max_offset"] = float(max(0.35, float(p.get("stroke_circle", 1.0)) * 0.6))
                    p["allow_stem_width_tuning"] = True
                    p["stem_width_tuning_px"] = 1.0
                if p.get("arm_enabled"):
                    p["lock_arm_center_to_circle"] = True

            geometry_reanchored_to_template = False
            if bool(p.get("lock_circle_cx", False)) and "template_circle_cx" in p:
                p["cx"] = float(p["template_circle_cx"])
                geometry_reanchored_to_template = True
            if bool(p.get("lock_circle_cy", False)) and "template_circle_cy" in p:
                p["cy"] = float(p["template_circle_cy"])
                geometry_reanchored_to_template = True
            if geometry_reanchored_to_template and p.get("circle_enabled", True):
                if p.get("stem_enabled"):
                    p = Action._alignStemToCircleCenter(p)
                if p.get("arm_enabled"):
                    Action._reanchorArmToCircleEdge(p, float(p.get("r", 0.0)))
        if p.get("stem_enabled"):
            Action._persistConnectorLengthFloor(p, "stem", default_ratio=0.65)
        if p.get("arm_enabled"):
            Action._persistConnectorLengthFloor(p, "arm", default_ratio=0.75)
        if str(p.get("text_mode", "")).lower() == "co2":
            min_dim = float(min(float(p.get("width", 0.0) or 0.0), float(p.get("height", 0.0) or 0.0)))
            if min_dim <= 0.0:
                # Fallback for call sites that only pass geometry parameters.
                min_dim = max(1.0, float(p.get("r", 1.0)) * 2.0)

            # Keep AC0820 variants tunable (bounded via *_min/*_max overrides).
            # Very small CO₂ badges from other AC08xx families (e.g. AC0833_S)
            # can exhibit the same undersizing behavior after anti-aliased fitting,
            # so unlock bounded tuning for tiny variants in general.
            tiny_co2_variant = min_dim <= 15.5
            p["lock_text_scale"] = not (symbol_name == "AC0820" or tiny_co2_variant)
            if tiny_co2_variant:
                base_scale = float(p.get("co2_font_scale", 0.82))
                p["co2_font_scale_min"] = float(max(0.74, base_scale * 0.90))
                p["co2_font_scale_max"] = float(min(1.18, base_scale * 1.25))
        if str(p.get("text_mode", "")).lower() == "voc":
            min_dim = float(min(float(p.get("width", 0.0) or 0.0), float(p.get("height", 0.0) or 0.0)))
            if min_dim <= 0.0:
                min_dim = max(1.0, float(p.get("r", 1.0)) * 2.0)
            if symbol_name == "AC0835":
                # AC0835 variants use a freer VOC fitting policy than the CO₂
                # families: keep text scaling unlocked and bias the medium+
                # badges toward a readable baseline.
                p["lock_text_scale"] = False
                if min_dim <= 15.5:
                    # AC0835_S tends to over-scale VOC during text bracketing,
                    # producing a visibly heavy label compared to the source icon.
                    # Keep the historical small-badge cap stable regardless of
                    # global baseline uplifts so regression bounds remain intact.
                    legacy_base_scale = 0.52
                    p.setdefault("voc_font_scale_min", float(max(0.58, legacy_base_scale * 0.90)))
                    p.setdefault("voc_font_scale_max", float(min(0.92, legacy_base_scale * 1.05)))
                else:
                    # Medium/Large variants can start too small; pin a minimum
                    # readable baseline while still allowing upward tuning.
                    p["voc_font_scale"] = float(max(float(p.get("voc_font_scale", 0.52)), 0.60))
                    p.setdefault("voc_font_scale_min", 0.60)
                    p.pop("voc_font_scale_max", None)
        p = Action._configureAc08SmallVariantMode(name, p)
        preserve_plain_ring_geometry = symbol_name == "AC0800"
        preserved_plain_ring_keys = {
            key: p[key]
            for key in ("lock_circle_cx", "lock_circle_cy", "min_circle_radius", "max_circle_radius")
            if preserve_plain_ring_geometry and key in p
        }
        for key in (
            "lock_circle_cx",
            "lock_circle_cy",
            "lock_stem_center_to_circle",
            "lock_arm_center_to_circle",
            "lock_text_scale",
            "lock_colors",
            "min_circle_radius",
            "max_circle_radius",
            "co2_font_scale_min",
            "co2_font_scale_max",
            "voc_font_scale_min",
            "voc_font_scale_max",
            "fill_gray_min",
            "fill_gray_max",
            "stroke_gray_min",
            "stroke_gray_max",
            "stem_gray_min",
            "stem_gray_max",
            "text_gray_min",
            "text_gray_max",
            "arm_len_min",
            "arm_len_min_ratio",
            "connector_family_group",
            "connector_family_direction",
        ):
            p.pop(key, None)
        if preserve_plain_ring_geometry:
            p.update(preserved_plain_ring_keys)
            if "template_circle_cx" in p:
                p["cx"] = float(p["template_circle_cx"])
            if "template_circle_cy" in p:
                p["cy"] = float(p["template_circle_cy"])
            template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
            min_radius_ratio = 0.96
            if bool(p.get("ac08_small_variant_mode", False)):
                # AC0800_S is visually very sensitive to anti-aliased radius
                # shrinkage. Keep the small plain-ring variant at least at the
                # template radius so later validation rounds cannot undershoot
                # the original circle diameter.
                min_radius_ratio = 1.0
            # AC0800 plain rings should derive the radius floor strictly from
            # the template, not from an overgrown fitted radius estimate.
            p["min_circle_radius"] = float(max(1.0, template_r * min_radius_ratio))
            cx = float(p.get("cx", p.get("template_circle_cx", template_r)))
            cy = float(p.get("cy", p.get("template_circle_cy", template_r)))
            canvas_w = float(p.get("width", p.get("badge_width", 0.0)) or 0.0)
            canvas_h = float(p.get("height", p.get("badge_height", 0.0)) or 0.0)
            if canvas_w <= 0.0:
                canvas_w = max(float(cx * 2.0), template_r * 2.0)
            if canvas_h <= 0.0:
                canvas_h = max(float(cy * 2.0), template_r * 2.0)
            canvas_fit_r = max(1.0, min(cx, canvas_w - cx, cy, canvas_h - cy) - 0.5)
            if bool(p.get("ac08_small_variant_mode", False)):
                p["max_circle_radius"] = float(max(template_r, template_r * 1.15, canvas_fit_r))
            else:
                p["max_circle_radius"] = float(max(template_r, template_r * 1.15))
            min_r = float(max(1.0, p.get("min_circle_radius", 1.0)))
            max_r = float(max(min_r, p.get("max_circle_radius", min_r)))
            p["max_circle_radius"] = max_r
            # Keep AC0800 geometry immediately inside semantic bounds. Without
            # this clamp, fitted large variants can start validation already
            # above the plain-ring cap and never re-enter the guarded range.
            p["r"] = float(Action._clipScalar(float(p.get("r", template_r)), min_r, max_r))
        if p.get("draw_text", True) and "text_gray" in p:
            p["text_gray"] = int(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))
        return p

    @staticmethod
    def _activateAc08AdaptiveLocks(
        params: dict,
        logs: list[str],
        *,
        full_err: float,
        reason: str,
    ) -> bool:
        """Adaptive AC08 locks are disabled so semantic badge fitting stays unconstrained."""
        return False

    @staticmethod
    def _releaseAc08AdaptiveLocks(
        params: dict,
        logs: list[str],
        *,
        reason: str,
        current_error: float,
    ) -> bool:
        """Adaptive AC08 lock release is disabled because there are no AC08 locks to release."""
        return False

    @staticmethod
    def _alignStemToCircleCenter(params: dict) -> dict:
        """Ensure vertical handle/stem extension runs through circle center.

        For vertical connector badges (e.g. AC0811/AC0831/AC0836), force the
        connector start to the circle edge so quantization does not leave a
        visible gap between circle and stem.
        """
        if params.get("stem_enabled") and params.get("circle_enabled", True):
            if "stem_width" in params and "cx" in params:
                params["stem_x"] = float(params["cx"]) - (float(params["stem_width"]) / 2.0)
            if "cy" in params and "r" in params:
                stem_width = float(params.get("stem_width", params.get("stroke_circle", Action.AC08_STROKE_WIDTH_PX)))
                params["stem_top"] = float(params["cy"]) + float(params["r"]) - (stem_width * 0.55)
        return params

    @staticmethod
    def _defaultAc0870Params(w: int, h: int) -> dict:
        scale = min(w, h) / 30.0 if min(w, h) > 0 else 1.0
        b = Action.AC0870_BASE
        params = {
            "cx": b["cx"] * scale,
            "cy": b["cy"] * scale,
            "r": b["r"] * scale,
            "stroke_circle": b["stroke_width"] * scale,
            "fill_gray": b["fill_gray"],
            "stroke_gray": b["stroke_gray"],
            "text_gray": b["text_gray"],
            "label": b["label"],
            "tx": 8.7 * scale,
            "ty": 6.5 * scale,
            "s": 0.0100 * scale,
            "text_mode": "path_t",
        }
        Action._centerGlyphBbox(params)
        return Action._normalizeLightCircleColors(params)

    @staticmethod
    def _defaultAc0881Params(w: int, h: int) -> dict:
        params = Action._defaultAc0870Params(w, h)
        params["stem_enabled"] = True
        params["stem_width"] = max(1.0, params["r"] * 0.30)
        params["stem_x"] = params["cx"] - (params["stem_width"] / 2.0)
        params["stem_top"] = params["cy"] + (params["r"] * 0.60)
        params["stem_bottom"] = float(h)
        params["stem_gray"] = params["stroke_gray"]
        return params

    @staticmethod
    def _defaultAc081xShared(w: int, h: int) -> dict:
        scale = min(1.0, (min(w, h) / 25.0)) if min(w, h) > 0 else 1.0
        cx = float(w) / 2.0
        cy = float(h) / 2.0
        # AC081x reference bitmaps use a slightly larger circle than AR0100/AC0870.
        r = 9.2 * scale
        stroke_circle = 1.5 * scale
        stem_or_arm = 2.0 * scale
        # Keep connector lines long enough to match the raster source symbols.
        stem_or_arm_len = 9.0 * scale
        return {
            "cx": cx,
            "cy": cy,
            "r": r,
            "stroke_circle": stroke_circle,
            "stroke_gray": 152,
            "fill_gray": 220,
            "stem_or_arm": stem_or_arm,
            "stem_or_arm_len": stem_or_arm_len,
        }

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
        """Return circle geometry for connector badges anchored near one canvas edge.

        Elongated AC08 connector badges use a circle that is sized from the narrow
        canvas dimension and visually offset away from the edge where the connector
        originates. Using the same clearance rule for each anchor direction keeps
        the ring from appearing clipped without baking variant-specific offsets into
        one SKU.
        """
        narrow = float(min(w, h))
        stroke_circle = max(0.9, narrow / stroke_divisor)
        r = narrow * radius_ratio
        cx = float(w) / 2.0
        cy = float(h) / 2.0
        edge_clearance = max(stroke_circle * edge_clearance_stroke_factor, narrow * edge_clearance_ratio)

        anchor_key = anchor.lower()
        if anchor_key == "top":
            cy = r + edge_clearance
        elif anchor_key == "bottom":
            cy = float(h) - (r + edge_clearance)
        elif anchor_key == "left":
            cx = r + edge_clearance
        elif anchor_key == "right":
            cx = float(w) - (r + edge_clearance)
        else:
            raise ValueError(f"Unsupported anchor: {anchor}")

        return {
            "cx": cx,
            "cy": cy,
            "r": r,
            "stroke_circle": stroke_circle,
        }

    @staticmethod
    def _defaultAc0811Params(w: int, h: int) -> dict:
        """AC0811 is vertically elongated: circle sits in the upper square area."""
        if w <= 0 or h <= 0:
            return Action._defaultAc081xShared(w, h)

        circle = Action._defaultEdgeAnchoredCircleGeometry(w, h, anchor="top")
        cx = float(circle["cx"])
        cy = float(circle["cy"])
        r = float(circle["r"])
        stroke_circle = float(circle["stroke_circle"])
        stem_width = max(1.0, float(w) * 0.10)
        # AC0811 reference symbols use a visually slim vertical handle.
        # Persist an explicit width ceiling so later fitting/validation
        # steps cannot widen the stem beyond the template's intent.
        stem_width_max = max(1.0, float(w) * 0.105)
        stem_len = max(2.0, float(h) - (cy + r))

        return Action._normalizeLightCircleColors({
            "cx": cx,
            "cy": cy,
            "r": r,
            "stroke_circle": stroke_circle,
            "stroke_gray": Action.LIGHT_CIRCLE_STROKE_GRAY,
            "fill_gray": Action.LIGHT_CIRCLE_FILL_GRAY,
            "draw_text": False,
            "stem_enabled": True,
            "stem_width": stem_width,
            "stem_width_max": stem_width_max,
            "stem_x": cx - (stem_width / 2.0),
            "stem_top": cy + r,
            "stem_bottom": min(float(h), (cy + r) + stem_len),
            "stem_gray": Action.LIGHT_CIRCLE_STROKE_GRAY,
        })

    @staticmethod
    def _estimateUpperCircleFromForeground(img: np.ndarray, defaults: dict) -> tuple[float, float, float] | None:
        """Estimate circle geometry from the upper symbol region.

        AC0811_S is very small and Hough-based fitting can drift on anti-aliased
        edges. This fallback uses a simple foreground extraction in the upper part
        of the symbol and derives a robust enclosing circle from the largest blob.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        if h <= 0 or w <= 0:
            return None

        _, fg = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        top_limit = int(round(min(float(h), float(defaults.get("cy", h / 2.0)) + float(defaults.get("r", w / 3.0)) * 1.15)))
        top_limit = max(3, min(h, top_limit))
        roi = fg[:top_limit, :]
        if roi.size == 0:
            return None

        contours, _ = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        best = None
        for cnt in contours:
            area = float(cv2.contourArea(cnt))
            if area < 8.0:
                continue
            perimeter = float(cv2.arcLength(cnt, True))
            if perimeter <= 0.0:
                continue
            circularity = 4.0 * np.pi * area / max(1e-6, perimeter * perimeter)
            if circularity < 0.35:
                continue
            score = area * (0.5 + circularity)
            if best is None or score > best[0]:
                best = (score, cnt)

        if best is None:
            return None

        (_score, cnt) = best
        (cx, cy), r = cv2.minEnclosingCircle(cnt)
        min_r = max(2.0, float(w) * 0.24)
        max_r = min(float(w) * 0.52, float(top_limit) * 0.58)
        if max_r < min_r:
            max_r = min_r
        r = float(Action._clipScalar(r, min_r, max_r))
        cx = float(Action._clipScalar(cx, 0.0, float(w - 1)))
        cy = float(Action._clipScalar(cy, 0.0, float(h - 1)))
        return cx, cy, r

    @staticmethod
    def _fitAc0811ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0811 while keeping the vertical stem anchored to the lower edge.

        AC0811 source symbols are noisy for thin vertical lines. Generic stem fitting can
        under-segment the line so the generated SVG misses parts of the lower connector.
        For this family we therefore fit the circle/tones from the image, but keep the stem
        geometry constrained to the semantic template (centered under the circle, extending
        to the image bottom).
        """
        params = Action._fit_semantic_badge_from_image(img, defaults)
        h, w = img.shape[:2]

        raw_stem_width = float(params.get("stem_width", defaults.get("stem_width", max(1.0, float(w) * 0.10))))
        cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(w) / 2.0)))
        r = float(params.get("r", defaults.get("r", float(w) * 0.4)))
        stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(w) / 15.0))))
        aspect_ratio = (float(h) / float(w)) if w > 0 else 1.0
        elongated_plain_badge = aspect_ratio >= 1.60 and not bool(params.get("draw_text", False))

        # Foreground contour estimation helps stem-only badges, but for VOC/CO2
        # labels it can lock onto text blobs and shrink the fitted circle.
        allow_upper_circle_estimate = str(params.get("text_mode", "")).lower() not in {"voc", "co2"}
        upper_circle = Action._estimate_upper_circle_from_foreground(img, defaults) if allow_upper_circle_estimate else None
        if upper_circle is not None:
            ecx, ecy, er = upper_circle
            # Prefer robust foreground estimate for tiny/narrow AC0811 variants.
            trust = 0.85 if w <= 18 else 0.55
            cx = (cx * (1.0 - trust)) + (ecx * trust)
            cy = (cy * (1.0 - trust)) + (ecy * trust)
            r = (r * (1.0 - trust)) + (er * trust)
            params["cx"] = cx
            params["cy"] = cy
            params["r"] = r

        if w <= 18:
            default_cx = float(defaults.get("cx", float(w) / 2.0))
            default_cy = float(defaults.get("cy", float(w) / 2.0))

            # Ensure the fitted circle remains fully inside the canvas with stroke taken
            # into account so it is not clipped at the edges.
            radius_limit_x = max(1.0, min(default_cx, float(w) - default_cx) - (stroke_circle / 2.0))
            radius_limit_y = max(1.0, min(default_cy, float(h) - default_cy) - (stroke_circle / 2.0))
            r = float(min(r, radius_limit_x, radius_limit_y))

            params["cx"] = default_cx
            params["cy"] = cy
            params["r"] = r
            # Keep tiny AC0811 variants horizontally anchored; anti-aliased
            # min-rect alignment can otherwise pull circle/stem to one side.
            params["lock_circle_cx"] = True
            params["lock_stem_center_to_circle"] = True

        # Keep elongated plain AC0811 variants close to their semantic template.
        # The stem occupies only a thin column of dark pixels, so the generic
        # circle/stem error tends to over-value shorter stems once the circle is
        # nudged downward. Re-anchor the circle vertically and persist a stronger
        # template-based stem floor so AC0811_L keeps a visibly long connector.
        if elongated_plain_badge:
            default_cx = float(defaults.get("cx", cx))
            default_cy = float(defaults.get("cy", cy))
            default_r = float(defaults.get("r", r))
            params["cx"] = default_cx
            params["cy"] = float(Action._clipScalar(cy, default_cy - 1.0, default_cy + 1.0))
            r = float(max(r, default_r * 0.97))
            params["r"] = r
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            params["lock_stem_center_to_circle"] = True
            params["stem_len_min_ratio"] = float(max(float(params.get("stem_len_min_ratio", 0.0) or 0.0), 0.80))
            cx = float(params["cx"])
            cy = float(params["cy"])

        # Keep text badges close to template radius; otherwise under-estimation
        # shrinks both the circle and text size in variants such as AC0836_L.
        if str(params.get("text_mode", "")).lower() in {"voc", "co2"}:
            default_r = float(defaults.get("r", r))
            r = float(Action._clipScalar(r, default_r * 0.95, default_r * 1.08))
            params["r"] = r

        # AC0811 stems are intentionally thin. The generic contour fit can over-estimate
        # width when anti-aliased circle pixels bleed into the stem ROI, especially on
        # larger "_L" variants. Keep the fitted value but clamp it to a narrow, plausible
        # band derived from the circle stroke and image width.
        min_stem_width = max(1.0, stroke_circle * 0.72)
        default_stem_width_max = max(min_stem_width, min(float(w) * 0.12, stroke_circle * 1.35))
        max_stem_width = max(
            min_stem_width,
            min(float(defaults.get("stem_width_max", default_stem_width_max)), default_stem_width_max),
        )
        stem_width = max(min_stem_width, min(raw_stem_width, max_stem_width))

        params["stem_enabled"] = True
        params["stem_width"] = stem_width
        params["stem_width_max"] = max_stem_width
        params["stem_x"] = cx - (params["stem_width"] / 2.0)
        min_stem_len = 1.0 if h <= 18 else 2.0
        max_r_for_visible_stem = max(1.0, float(h) - cy - min_stem_len)
        if r > max_r_for_visible_stem:
            r = max_r_for_visible_stem
            params["r"] = r
        stem_top = cy + r
        stem_top = max(0.0, min(float(h) - min_stem_len, stem_top))
        params["stem_top"] = stem_top
        params["stem_bottom"] = float(h)
        params["stem_gray"] = int(round(params.get("stroke_gray", defaults.get("stroke_gray", 152))))
        if elongated_plain_badge:
            params["stem_len_min_ratio"] = float(max(float(params.get("stem_len_min_ratio", 0.0) or 0.0), 0.80))
            Action._persistConnectorLengthFloor(params, "stem", default_ratio=0.80)

        return Action._normalizeLightCircleColors(params)

    @staticmethod
    def _defaultAc0882Params(w: int, h: int) -> dict:
        params = Action._defaultAc081xShared(w, h)
        arm_x2 = params["cx"] - params["r"]
        arm_x1 = max(0.0, arm_x2 - params["stem_or_arm_len"])
        params.update(
            {
                "text_gray": 98,
                "label": "T",
                "text_mode": "path_t",
                "arm_enabled": True,
                "arm_x1": arm_x1,
                "arm_y1": params["cy"],
                "arm_x2": arm_x2,
                "arm_y2": params["cy"],
                "arm_stroke": params["stem_or_arm"],
                "s": 0.0088 * min(1.0, (min(w, h) / 25.0)) if min(w, h) > 0 else 0.0088,
            }
        )
        Action._centerGlyphBbox(params)
        return params

    @staticmethod
    def _applyCo2Label(params: dict) -> dict:
        params["draw_text"] = True
        params["text_mode"] = "co2"
        params["text_gray"] = int(round(params.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))
        params["co2_font_scale"] = float(params.get("co2_font_scale", 0.82 * Action.SEMANTIC_TEXT_BASE_SCALE))
        params["co2_sub_font_scale"] = float(params.get("co2_sub_font_scale", 66.0))
        params["co2_dx"] = float(params.get("co2_dx", 0.0))
        params["co2_dy"] = float(params.get("co2_dy", 0.0))
        params["co2_inner_padding_px"] = float(params.get("co2_inner_padding_px", 0.35))
        params["co2_width_scale"] = float(params.get("co2_width_scale", 1.0))
        # Keep "CO" as an explicit run so the subscript position remains stable across
        # renderers. The default mode keeps the CO baseline vertically centered, but
        # applies a small left compensation so the overall CO₂ cluster appears
        # horizontally centered in the circle.
        params["co2_anchor_mode"] = str(params.get("co2_anchor_mode", "center_co"))
        params["co2_index_mode"] = str(params.get("co2_index_mode", "subscript"))
        return params

    @staticmethod
    def _co2Layout(params: dict) -> dict[str, float | str]:
        """Compute renderer-independent CO₂ text metrics and placement."""
        cx = float(params.get("cx", 0.0))
        cy = float(params.get("cy", 0.0))
        r = max(1.0, float(params.get("r", 1.0)))
        stroke = max(0.8, float(params.get("stroke_circle", 1.0)))
        inner_diameter = max(2.0, (2.0 * r) - stroke)
        requested_font_size = max(4.0, r * float(params.get("co2_font_scale", 0.82)))
        # Keep the main CO run proportionate to the circle interior, even if
        # optimizer steps push co2_font_scale too high for anti-aliased rasters.
        max_font_size = max(
            4.0,
            inner_diameter * float(params.get("co2_max_inner_diameter_ratio", 0.50)),
        )
        inner_padding = max(0.0, float(params.get("co2_inner_padding_px", 0.35)))
        clear_span = max(1.0, inner_diameter - (2.0 * inner_padding))
        sub_scale = float(params.get("co2_sub_font_scale", 66.0))
        sub_ratio = max(0.20, sub_scale / 100.0)
        # Estimate the whole CO₂ cluster width and derive a scale that keeps
        # a small edge margin whenever geometry allows it.
        cluster_factor = 1.04 + 0.03 + (0.62 * sub_ratio)
        width_limited_font = clear_span / max(0.001, cluster_factor)
        # Preserve vertical clear-space as well.
        height_limited_font = clear_span / max(0.95, 0.95 + (0.24 * sub_ratio) + (0.35 * sub_ratio))
        auto_font_size = min(width_limited_font, height_limited_font)
        font_size = min(max_font_size, max(requested_font_size, auto_font_size))
        # Tiny badges can otherwise rasterize the subscript into a barely visible
        # blob or drop it entirely. Keep a conservative minimum pixel height.
        sub_font_px = max(4.0, font_size * (sub_scale / 100.0))
        anchor_mode = str(params.get("co2_anchor_mode", "center_co")).lower()
        index_mode = str(params.get("co2_index_mode", "subscript")).lower()

        width_scale = float(params.get("co2_width_scale", 1.0))
        width_scale = float(max(0.78, min(1.12, width_scale)))
        symbol_hint = str(params.get("badge_symbol_name", "")).upper()
        if not symbol_hint:
            symbol_hint = str(params.get("variant_name", "")).upper().split("_", 1)[0]
        if symbol_hint == "AC0820":
            # Keep AC0820 variants consistently narrower even when later
            # optimization passes try to widen the default fallback font.
            if r >= 10.0:
                width_scale = min(width_scale, 0.90)
            elif r >= 6.0:
                width_scale = min(width_scale, 0.92)
            else:
                width_scale = min(width_scale, 0.94)

        co_width = (font_size * 1.04) * width_scale
        gap = font_size * 0.03
        if index_mode == "superscript":
            # Raised CO² labels need a wider horizontal separation so the "2"
            # stays visibly detached from the "O" in all AC08 conversions.
            superscript_min_gap = font_size * float(params.get("co2_superscript_min_gap_scale", 0.130))
            gap = max(gap, superscript_min_gap)
        sub_w = (sub_font_px * 0.62) * width_scale

        if anchor_mode in {"cluster", "co"}:
            # Legacy mode: center the whole CO₂ cluster.
            cluster_shift = (gap + sub_w) / 2.0
            co_x = (cx + float(params.get("co2_dx", 0.0))) - cluster_shift
            x1 = co_x - (co_width / 2.0)
            subscript_x = co_x + (co_width / 2.0) + gap
            x2 = subscript_x + sub_w
        else:
            # Default mode: keep the "CO" run as the dominant anchor and only shift
            # if geometry constraints require it.
            # Prioritize matching the main "CO" glyphs first; if space is tight, shrink
            # or tuck the subscript before shifting the dominant "CO" run.
            visual_sub_w = (sub_font_px * float(params.get("co2_subscript_visual_width_factor", 0.62))) * width_scale
            visual_cluster_shift = (gap + visual_sub_w) / 2.0
            center_co_bias = float(params.get("co2_center_co_bias", 0.0))
            co_x = (cx + float(params.get("co2_dx", 0.0))) + (visual_cluster_shift * center_co_bias)
            x1 = co_x - (co_width / 2.0)

            local_gap = gap
            local_sub_font_px = sub_font_px
            local_sub_w = sub_w
            subscript_x = co_x + (co_width / 2.0) + local_gap
            x2 = subscript_x + local_sub_w

            stroke = max(0.8, float(params.get("stroke_circle", 1.0)))
            inner_right = cx + max(1.0, r - stroke) - inner_padding
            inner_left = cx - max(1.0, r - stroke) + inner_padding

            overflow = x2 - inner_right
            if overflow > 0.0:
                # Step 1: reduce spacing before moving CO.
                min_gap = font_size * 0.005
                if index_mode == "superscript":
                    min_gap = max(
                        min_gap,
                        font_size * float(params.get("co2_superscript_min_gap_scale", 0.130)),
                    )
                shrink_gap = min(overflow, max(0.0, local_gap - min_gap))
                local_gap -= shrink_gap
                overflow -= shrink_gap

                # Step 2: reduce subscript size (keep readable floor) before moving CO.
                if overflow > 0.0:
                    min_sub_font_px = max(4.0, font_size * 0.42)
                    max_shrink_px = max(0.0, local_sub_font_px - min_sub_font_px)
                    shrink_px = min(max_shrink_px, overflow / 0.62)
                    local_sub_font_px -= shrink_px
                    local_sub_w = (local_sub_font_px * 0.62) * width_scale

                # Recompute geometry with adjusted ₂ attachment.
                sub_font_px = local_sub_font_px
                subscript_x = co_x + (co_width / 2.0) + local_gap
                x2 = subscript_x + local_sub_w

                # Step 3: only if still necessary, shift cluster minimally left.
                overflow = x2 - inner_right
                if overflow > 0.0:
                    co_x -= overflow
                    x1 -= overflow
                    subscript_x -= overflow
                    x2 -= overflow

            # Keep the left side inside the inner circle as well.
            left_overflow = inner_left - x1
            if left_overflow > 0.0:
                co_x += left_overflow
                x1 += left_overflow
                subscript_x += left_overflow
                x2 += left_overflow

        # Capital glyphs usually appear slightly high when simply middle-anchored.
        # Apply a proportional optical correction so the label sits visually centered.
        # A stronger correction keeps the "CO" run from looking top-heavy in tiny
        # AC08xx badges where antialiasing exaggerates baseline drift.
        # Large variants (e.g. AC0820_L) can still look top-heavy with a fixed
        # correction. Nudge bigger badges slightly further down while keeping the
        # small-size behavior effectively unchanged.
        optical_bias = float(params.get("co2_optical_bias", 0.090 + (0.015 * min(1.0, r / 12.0))))
        y_base = cy + float(params.get("co2_dy", 0.0)) + (font_size * optical_bias)
        subscript_offset = font_size * float(params.get("co2_subscript_offset_scale", 0.18))
        height = font_size * 0.95

        # Keep text vertically within the circle's clear area.
        stroke = max(0.8, float(params.get("stroke_circle", 1.0)))
        inner_top = cy - max(1.0, r - stroke)
        inner_bottom = cy + max(1.0, r - stroke)
        top = y_base - (height / 2.0)
        bottom = y_base + (height / 2.0)
        if top < inner_top:
            delta = inner_top - top
            y_base += delta
        elif bottom > inner_bottom:
            delta = bottom - inner_bottom
            y_base -= delta

        # Keep the subscript readable and away from the border, but do not let it
        # drive the vertical centering of the main "CO" run.
        if index_mode == "superscript":
            min_index_offset = font_size * 0.10
            max_index_offset = font_size * 0.34
            index_offset = float(max(min_index_offset, min(max_index_offset, font_size * float(params.get("co2_superscript_offset_scale", 0.22)))))
            subscript_y = y_base - index_offset
            sub_top = subscript_y - (sub_font_px * 0.60)
            if sub_top < inner_top:
                max_offset = max(min_index_offset, y_base - inner_top - (sub_font_px * 0.60))
                index_offset = float(max(min_index_offset, min(max_index_offset, max_offset)))
                subscript_y = y_base - index_offset
            sub_bottom = subscript_y + (sub_font_px * 0.35)
            if sub_bottom > inner_bottom:
                min_offset = y_base - inner_bottom + (sub_font_px * 0.35)
                index_offset = float(max(min_index_offset, min(max_index_offset, min_offset)))
                subscript_y = y_base - index_offset
        else:
            min_subscript_offset = font_size * 0.08
            max_subscript_offset = font_size * 0.24
            subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, subscript_offset)))
            subscript_y = y_base + subscript_offset
            sub_bottom = subscript_y + (sub_font_px * 0.35)
            if sub_bottom > inner_bottom:
                max_offset = inner_bottom - y_base - (sub_font_px * 0.35)
                subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, max_offset)))
                subscript_y = y_base + subscript_offset

            sub_top = subscript_y - (sub_font_px * 0.60)
            if sub_top < inner_top:
                min_offset = inner_top - y_base + (sub_font_px * 0.60)
                subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, min_offset)))
                subscript_y = y_base + subscript_offset

        return {
            "anchor_mode": anchor_mode,
            "index_mode": index_mode,
            "width_scale": width_scale,
            "font_size": font_size,
            "sub_scale": sub_scale,
            "sub_font_px": sub_font_px,
            "co_x": co_x,
            "y_base": y_base,
            "subscript_x": subscript_x,
            "subscript_y": subscript_y,
            "x1": x1,
            "x2": x2,
            "height": height,
        }

    @staticmethod
    def _applyVocLabel(params: dict) -> dict:
        params["draw_text"] = True
        params["text_mode"] = "voc"
        params["text_gray"] = int(round(params.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))
        params["voc_font_scale"] = float(params.get("voc_font_scale", 0.52 * Action.SEMANTIC_TEXT_BASE_SCALE))
        params["voc_dy"] = float(params.get("voc_dy", -0.01 * float(params.get("r", 0.0))))
        params["voc_weight"] = int(params.get("voc_weight", 600))
        return params

    @staticmethod
    def _tuneAc0832Co2Badge(params: dict) -> dict:
        """AC0832 has a compact circle; keep CO₂ comfortably inside the ring."""
        p = dict(params)
        r = float(p.get("r", 0.0))
        p["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        p["arm_stroke"] = Action.AC08_STROKE_WIDTH_PX
        p["stroke_circle"] = Action.AC08_STROKE_WIDTH_PX
        p["co2_font_scale"] = min(float(p.get("co2_font_scale", 0.82)), 0.74)
        p["co2_sub_font_scale"] = min(float(p.get("co2_sub_font_scale", 66.0)), 62.0)
        p["co2_index_mode"] = "superscript"
        p["co2_superscript_offset_scale"] = float(min(float(p.get("co2_superscript_offset_scale", 0.11)), 0.11))
        p["co2_dy"] = float(p.get("co2_dy", 0.0)) - (0.03 * r)
        p["text_gray"] = p["stroke_gray"]
        return p

    @staticmethod
    def _tuneAc0831Co2Badge(params: dict) -> dict:
        """Stabilize AC0831 text placement for vertically elongated CO² badges."""
        p = dict(params)
        r = float(p.get("r", 0.0))
        p["stroke_gray"] = 155
        p["fill_gray"] = 238
        p["text_gray"] = p["stroke_gray"]
        p["stroke_circle"] = Action.AC08_STROKE_WIDTH_PX
        p["stem_gray"] = p["stroke_gray"]
        # Vertical connector variants read closer to the source rasters when the
        # whole CO² cluster is centered as a unit instead of keeping only "CO"
        # centered. AC0831 follows the reference with a superscript 2 and a
        # slightly higher text position than the generic vertical CO₂ family.
        p["co2_anchor_mode"] = "cluster"
        p["co2_index_mode"] = "superscript"
        p["co2_optical_bias"] = float(p.get("co2_optical_bias", 0.08))
        p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.35))
        p["co2_font_scale"] = min(float(p.get("co2_font_scale", 0.82)), 0.74)
        p["co2_sub_font_scale"] = min(float(p.get("co2_sub_font_scale", 66.0)), 48.0)
        # Keep the raised "2" clearly detached from the "O" in AC0831_L and
        # sibling variants where JPEG antialiasing tends to visually merge both.
        p["co2_superscript_offset_scale"] = float(max(float(p.get("co2_superscript_offset_scale", 0.17)), 0.17))
        p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.19)), 0.19))
        min_dim = float(
            min(
                float(p.get("width", 0.0) or 0.0),
                float(p.get("height", 0.0) or 0.0),
            )
        )
        if min_dim <= 0.0:
            min_dim = max(1.0, r * 2.0)
        if 0.0 < min_dim <= 15.5:
            # Tiny vertical CO₂ badges compress the glyph cluster into a single
            # JPEG blob. Rendering them with the generic AC0831 scale makes the
            # label look too wide/high compared to the reference raster, so keep
            # the text slightly tighter while keeping the superscript readable.
            p["co2_font_scale"] = min(float(p.get("co2_font_scale", 0.74)), 0.74)
            p["co2_sub_font_scale"] = min(float(p.get("co2_sub_font_scale", 48.0)), 48.0)
            p["co2_optical_bias"] = max(float(p.get("co2_optical_bias", 0.10)), 0.10)
            p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.35))
            p["co2_superscript_offset_scale"] = float(max(float(p.get("co2_superscript_offset_scale", 0.17)), 0.17))
            p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.19)), 0.19))
        return p

    @staticmethod
    def _tuneAc0835VocBadge(params: dict, w: int, h: int) -> dict:
        """Keep tiny AC0835 badges from rendering the VOC label too high."""
        p = dict(params)
        r = float(p.get("r", 0.0))
        p["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        p["text_gray"] = p["stroke_gray"]
        min_dim = float(min(max(0, w), max(0, h)))
        if 0.0 < min_dim <= 15.5:
            # The AC0835_S raster centers the VOC word slightly lower than the
            # generic AC0870-derived default. Preserve that optical bias up
            # front so the validator does not need to recover it from a
            # stagnating small-variant search.
            p["voc_dy"] = float(max(float(p.get("voc_dy", 0.0)), 0.13 * r))
        return p

    @staticmethod
    def _tuneAc0833Co2Badge(params: dict) -> dict:
        """Tune AC0833 CO² badges so the trailing index stays superscript."""
        p = Action._normalizeLightCircleColors(dict(params))
        p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "cluster"))
        p["co2_index_mode"] = "superscript"
        p["co2_superscript_offset_scale"] = float(max(float(p.get("co2_superscript_offset_scale", 0.16)), 0.16))
        p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.17)), 0.17))
        return p

    @staticmethod
    def _tuneAc0834Co2Badge(params: dict, w: int, h: int) -> dict:
        """Stabilize tiny AC0834 badges where fitting drifts the circle downward."""
        p = dict(params)
        p["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        p["text_gray"] = p["stroke_gray"]
        p["stroke_circle"] = Action.AC08_STROKE_WIDTH_PX
        p["arm_stroke"] = Action.AC08_STROKE_WIDTH_PX

        if min(w, h) <= 16:
            default_cy = float(h) / 2.0
            default_r = float(h) * 0.4

            p["cy"] = default_cy
            p["r"] = max(default_r * 0.95, float(p.get("r", default_r)))
            cx = float(p.get("cx", float(h) / 2.0))
            p["arm_y1"] = default_cy
            p["arm_y2"] = default_cy
            p["arm_x1"] = min(float(w), cx + float(p["r"]))
            p["arm_x2"] = float(w)

            p["co2_font_scale"] = min(float(p.get("co2_font_scale", 0.82)), 0.86)
            p["co2_sub_font_scale"] = min(float(p.get("co2_sub_font_scale", 66.0)), 64.0)

        return p

    @staticmethod
    def _defaultAc0834Params(w: int, h: int) -> dict:
        """Compatibility helper for AC0834 semantic tests and callers."""
        return Action._tuneAc0834Co2Badge(Action._applyCo2Label(Action._defaultAc0814Params(w, h)), w, h)

    @staticmethod
    def _normalizeCenteredCo2Label(params: dict) -> dict:
        """Normalize CO₂ label sizing for plain circular badges.

        This keeps CO₂ text proportionate to the inner circle diameter for any
        centered (connector-free) semantic badge instead of tuning a single SKU.
        """
        p = dict(params)
        if str(p.get("text_mode", "")).lower() != "co2":
            return p
        if p.get("arm_enabled") or p.get("stem_enabled"):
            return p
        if not p.get("circle_enabled", True):
            return p

        r = max(1.0, float(p.get("r", 1.0)))
        stroke = max(0.8, float(p.get("stroke_circle", 1.0)))
        inner_diameter = max(2.0, (2.0 * r) - stroke)

        cur_scale = float(p.get("co2_font_scale", 0.82))
        cur_font = max(4.0, r * cur_scale)
        cur_width = cur_font * 1.45
        # Keep centered CO₂ labels readable but prevent oversized "CO" glyphs
        # that can visually rival the ring diameter on AC0820-like badges.
        target_width = inner_diameter * 0.68

        adjusted_scale = cur_scale * (target_width / max(1e-6, cur_width))
        min_scale = 0.72 if r >= 8.0 else 0.74
        p["co2_font_scale"] = float(max(min_scale, min(0.96, adjusted_scale)))
        p["co2_sub_font_scale"] = float(max(60.0, min(68.0, float(p.get("co2_sub_font_scale", 66.0)))))
        p["co2_dx"] = float(max(-0.18 * r, min(0.18 * r, float(p.get("co2_dx", -0.04 * r)))))
        p["co2_dy"] = float(max(-0.20 * r, min(0.20 * r, float(p.get("co2_dy", 0.03 * r)))))
        p["text_gray"] = int(round(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))
        return p

    @staticmethod
    def _defaultAc0812Params(w: int, h: int) -> dict:
        """AC0812 is horizontally elongated: left arm, circle on the right."""
        if w <= 0 or h <= 0:
            return Action._defaultAc081xShared(w, h)

        # Like AC0811/AC0813, size from the narrow side so tiny variants keep
        # the intended visual circle diameter.
        # AC0812 source rasters leave a slightly larger vertical margin around the
        # ring than AC0811/AC0813. Using 0.40*h tends to over-size the circle.
        r = float(h) * 0.36
        stroke_circle = max(0.9, float(h) / 15.0)
        cx = float(w) - (float(h) / 2.0)
        cy = float(h) / 2.0
        arm_stroke = max(1.0, float(h) * 0.10)

        return Action._normalizeLightCircleColors(
            {
                "cx": cx,
                "cy": cy,
                "r": r,
                "stroke_circle": stroke_circle,
                "stroke_gray": Action.LIGHT_CIRCLE_STROKE_GRAY,
                "fill_gray": Action.LIGHT_CIRCLE_FILL_GRAY,
                "draw_text": False,
                "arm_enabled": True,
                "arm_x1": 0.0,
                "arm_y1": cy,
                "arm_x2": max(0.0, cx - r - (arm_stroke / 2.0)),
                "arm_y2": cy,
                "arm_stroke": arm_stroke,
                "arm_len_min_ratio": 0.75,
            }
        )

    @staticmethod
    def _fitAc0812ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0812 while keeping the horizontal arm anchored to the left edge."""
        params = Action._fit_semantic_badge_from_image(img, defaults)
        h, w = img.shape[:2]
        aspect_ratio = (float(w) / float(h)) if h > 0 else 1.0

        raw_arm_stroke = float(params.get("arm_stroke", defaults.get("arm_stroke", max(1.0, float(h) * 0.10))))
        cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
        r = float(params.get("r", defaults.get("r", float(h) * 0.4)))
        stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(h) / 15.0))))

        min_arm_stroke = max(1.0, stroke_circle * 0.75)
        max_arm_stroke = max(min_arm_stroke, min(float(h) * 0.14, stroke_circle * 1.6))
        arm_stroke = max(min_arm_stroke, min(raw_arm_stroke, max_arm_stroke))

        default_r = float(defaults.get("r", float(h) * 0.4))
        # Why circles can become too large here:
        # - AC0812 has a circle touching the right side and an extra left arm.
        # - On anti-aliased rasters, contour/Hough fitting may merge ring edge,
        #   arm and border pixels into one oversized blob.
        # Keep fitting adaptive, but bounded by generic geometric plausibility
        # instead of variant-specific hard caps. This keeps elongated connector
        # symbols (including AC0812_L-like forms) free to grow when needed while
        # still avoiding runaway radii from anti-aliased merged contours.
        canvas_r_limit = Action._maxCircleRadiusInsideCanvas(cx, cy, w, h, stroke_circle)
        max_r = max(default_r * 1.45, default_r + 3.0)
        max_r = min(max_r, canvas_r_limit)
        r = min(r, max_r)

        if h <= 15 and not bool(params.get("draw_text", True)):
            # Tiny plain connector badges can lose roughly one anti-aliased ring
            # pixel in contour/Hough fitting; keep them close to template size.
            r = max(r, default_r * 0.98)

        # Elongated connector badges are prone to under-estimating the ring when
        # the connector bleeds into the contour mask. Apply a generic floor for
        # broad, no-text forms rather than pinning a single SKU.
        if aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True)):
            r = max(r, default_r * 0.95)

        params["r"] = r

        params["arm_enabled"] = True
        params["arm_stroke"] = arm_stroke
        params["arm_x1"] = 0.0
        params["arm_y1"] = cy
        attach_offset = max(0.0, arm_stroke / 2.0)
        params["arm_x2"] = max(0.0, cx - r - attach_offset)
        params["arm_y2"] = cy
        current_arm_len = float(math.hypot(params["arm_x2"] - params["arm_x1"], params["arm_y2"] - params["arm_y1"]))
        default_arm_len = max(
            0.0,
            float(defaults.get("cx", float(w) / 2.0)) - float(defaults.get("r", float(h) * 0.4)),
        )
        # Keep AC0812 connector geometry anchored to the semantic template. If we
        # derive the minimum arm length from an already-overgrown fitted circle,
        # later circle optimization can converge to the same unstable large-radius
        # solution. Use the template arm span as the lower bound baseline instead.
        semantic_arm_len_min = max(1.0, default_arm_len * 0.75)
        params["arm_len_min"] = max(1.0, current_arm_len * 0.75, semantic_arm_len_min)
        min_arm_len_ratio = 0.75
        # For elongated AC0812 variants (L-like forms), preserve a visibly long
        # connector arm so circle-fitting noise cannot eat too much horizontal
        # span. This keeps the left arm close to the semantic template.
        if aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True)):
            min_arm_len_ratio = 0.82
        params["arm_len_min_ratio"] = float(max(float(params.get("arm_len_min_ratio", min_arm_len_ratio)), min_arm_len_ratio))
        params["arm_len_min"] = max(
            float(params["arm_len_min"]),
            max(1.0, current_arm_len * float(params["arm_len_min_ratio"]), semantic_arm_len_min),
        )

        # Expose a stable upper radius bound for later stochastic/adaptive circle
        # searches. This prevents left-arm AC0812 variants from re-growing the
        # circle and shortening the mandatory connector arm during optimization.
        max_r_from_arm_span = max(1.0, cx - params["arm_len_min"])
        params["max_circle_radius"] = float(min(canvas_r_limit, max_r_from_arm_span))
        return Action._normalizeLightCircleColors(params)

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
        """AC0813 is AC0812 rotated 90° clockwise (vertical arm from top to circle)."""
        if w <= 0 or h <= 0:
            return Action._defaultAc081xShared(w, h)

        # Like other edge-anchored connector badges, size from the narrow side and
        # keep a small optical clearance from the anchored edge.
        circle = Action._defaultEdgeAnchoredCircleGeometry(w, h, anchor="bottom")
        cx = float(circle["cx"])
        cy = float(circle["cy"])
        r = float(circle["r"])
        stroke_circle = float(circle["stroke_circle"])
        arm_stroke = max(1.0, float(w) * 0.10)

        return Action._normalizeLightCircleColors(
            {
                "cx": cx,
                "cy": cy,
                "r": r,
                "stroke_circle": stroke_circle,
                "stroke_gray": Action.LIGHT_CIRCLE_STROKE_GRAY,
                "fill_gray": Action.LIGHT_CIRCLE_FILL_GRAY,
                "draw_text": False,
                "arm_enabled": True,
                "arm_x1": cx,
                "arm_y1": 0.0,
                "arm_x2": cx,
                "arm_y2": max(0.0, cy - r),
                "arm_stroke": arm_stroke,
            }
        )

    @staticmethod
    def _fitAc0813ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0813 while keeping the vertical arm anchored to the upper edge."""
        params = Action._fit_semantic_badge_from_image(img, defaults)
        h, w = img.shape[:2]
        aspect_ratio = (float(h) / float(w)) if w > 0 else 1.0

        raw_arm_stroke = float(params.get("arm_stroke", defaults.get("arm_stroke", max(1.0, float(w) * 0.10))))
        cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(h) - (float(w) / 2.0))))
        r = float(params.get("r", defaults.get("r", float(w) * 0.4)))
        stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(w) / 15.0))))
        default_r = float(defaults.get("r", float(w) * 0.4))

        min_arm_stroke = max(1.0, stroke_circle * 0.75)
        max_arm_stroke = max(min_arm_stroke, min(float(w) * 0.14, stroke_circle * 1.6))
        arm_stroke = max(min_arm_stroke, min(raw_arm_stroke, max_arm_stroke))

        if w <= 15 and not bool(params.get("draw_text", True)):
            # Tiny plain connector badges can lose roughly one anti-aliased ring
            # pixel in contour/Hough fitting; keep them near template size.
            r = max(r, default_r * 0.98)

        elongated_plain_badge = aspect_ratio >= 1.60 and w >= 20 and not bool(params.get("draw_text", True))
        if elongated_plain_badge:
            # AC0813_L-like forms are the vertical counterpart of AC0812_L/AC0814_L:
            # JPEG antialiasing around the top connector often biases the detected
            # ring inward, so preserve a tighter semantic radius floor here too.
            r = max(r, default_r * 0.95)
            params["min_circle_radius"] = float(max(float(params.get("min_circle_radius", 1.0)), default_r * 0.95))

        params["r"] = r

        # Tiny vertical badges with text overlays (e.g. AC0833_S / AC0838_S)
        # tend to be over-influenced by anti-aliased text pixels during contour
        # fitting. This can pull the circle downward and shrink its radius, which
        # shortens the visible top connector. Keep small variants close to the
        # semantic template geometry and only allow minimal vertical drift.
        if w <= 15 and bool(params.get("draw_text", False)):
            default_cx = float(defaults.get("cx", float(w) / 2.0))
            default_cy = float(defaults.get("cy", float(h) - (float(w) / 2.0)))
            default_r = float(defaults.get("r", float(w) * 0.4))
            params["cx"] = default_cx
            params["cy"] = float(Action._clipScalar(cy, default_cy - 0.8, default_cy + 0.8))
            params["r"] = max(r, default_r * 0.94)
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            params["lock_arm_center_to_circle"] = True
            cx = float(params["cx"])
            cy = float(params["cy"])
            r = float(params["r"])

        params["arm_enabled"] = True
        params["arm_stroke"] = arm_stroke
        params["arm_x1"] = cx
        params["arm_y1"] = 0.0
        params["arm_x2"] = cx
        params["arm_y2"] = max(0.0, cy - r)
        return Action._normalizeLightCircleColors(params)

    @staticmethod
    def _rotateSemanticBadgeClockwise(params: dict, w: int, h: int) -> dict:
        cx = float(w) / 2.0
        cy = float(h) / 2.0

        def rotateClockwise(x: float, y: float) -> tuple[float, float]:
            # image-space clockwise description maps to mathematically counter-clockwise
            # because y grows downward in raster coordinates.
            return cx - (y - cy), cy + (x - cx)

        rotated = dict(params)
        rotated["cx"], rotated["cy"] = rotateClockwise(float(params["cx"]), float(params["cy"]))
        rotated["arm_x1"], rotated["arm_y1"] = rotateClockwise(float(params["arm_x1"]), float(params["arm_y1"]))
        rotated["arm_x2"], rotated["arm_y2"] = rotateClockwise(float(params["arm_x2"]), float(params["arm_y2"]))
        return rotated

    @staticmethod
    def _defaultAc0814Params(w: int, h: int) -> dict:
        """AC0814 is horizontally elongated: circle on the left, arm to the right."""
        if w <= 0 or h <= 0:
            return Action._defaultAc081xShared(w, h)

        # AC0814_L-like originals use a noticeably larger ring than the earlier
        # generic AC081x template and keep a visible left margin before the
        # circle. A tighter template gets much closer to the hand-traced sample.
        r = float(h) * 0.46
        stroke_circle = max(0.9, float(h) / 25.0)
        left_margin = max(stroke_circle * 0.5, float(h) * 0.18)
        cx = r + left_margin
        cy = float(h) / 2.0
        arm_stroke = max(1.0, stroke_circle)

        return Action._normalizeLightCircleColors(
            {
                "cx": cx,
                "cy": cy,
                "r": r,
                "stroke_circle": stroke_circle,
                "stroke_gray": Action.LIGHT_CIRCLE_STROKE_GRAY,
                "fill_gray": Action.LIGHT_CIRCLE_FILL_GRAY,
                "draw_text": False,
                "arm_enabled": True,
                "arm_x1": min(float(w), cx + r),
                "arm_y1": cy,
                "arm_x2": float(w),
                "arm_y2": cy,
                "arm_stroke": arm_stroke,
                "arm_len_min": max(1.0, (float(w) - min(float(w), cx + r)) * 0.75),
                "arm_len_min_ratio": 0.75,
            }
        )

    @staticmethod
    def _fitAc0814ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0814 while keeping the horizontal arm anchored to the right edge."""
        params = Action._fit_semantic_badge_from_image(img, defaults)
        h, w = img.shape[:2]
        aspect_ratio = (float(w) / float(h)) if h > 0 else 1.0

        raw_arm_stroke = float(params.get("arm_stroke", defaults.get("arm_stroke", max(1.0, float(h) * 0.10))))
        cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
        r = float(params.get("r", defaults.get("r", float(h) * 0.4)))
        stroke_circle = float(params.get("stroke_circle", defaults.get("stroke_circle", max(0.9, float(h) / 15.0))))
        default_r = float(defaults.get("r", float(h) * 0.4))

        min_arm_stroke = max(1.0, stroke_circle * 0.75)
        max_arm_stroke = max(min_arm_stroke, min(float(h) * 0.14, stroke_circle * 1.6))
        arm_stroke = max(min_arm_stroke, min(raw_arm_stroke, max_arm_stroke))

        cx = float(params.get("cx", defaults.get("cx", float(h) / 2.0)))
        cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
        r = float(params.get("r", defaults.get("r", float(h) * 0.4)))

        tiny_plain_badge = h <= 18 and not bool(params.get("draw_text", True))
        if tiny_plain_badge:
            # Tiny plain connector badges can lose roughly one anti-aliased ring
            # pixel in contour/Hough fitting; keep them near template size.
            r = max(r, default_r * 0.98)
            default_cx = float(defaults.get("cx", float(w) / 2.0))
            default_cy = float(defaults.get("cy", float(h) / 2.0))
            # AC0814_S has very little empty space around the ring. Even a
            # sub-pixel pose drift is visually obvious, so keep the traced circle
            # anchored to the semantic template and only allow a tiny vertical
            # correction for raster antialiasing.
            params["cx"] = default_cx
            params["cy"] = float(Action._clipScalar(cy, default_cy - 0.5, default_cy + 0.5))
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            params["lock_arm_center_to_circle"] = True
            cx = float(params["cx"])
            cy = float(params["cy"])

        elongated_plain_badge = aspect_ratio >= 1.60 and h >= 20 and not bool(params.get("draw_text", True))
        if elongated_plain_badge:
            # AC0814_L-like forms are the mirrored counterpart of AC0812_L: JPEG
            # antialiasing near the connector often makes the ring fit under-size.
            # Keep a tighter semantic floor so later validation cannot preserve an
            # already shrunken circle as the new optimum.
            r = max(r, default_r * 0.95)
            params["min_circle_radius"] = float(max(float(params.get("min_circle_radius", 1.0)), default_r * 0.95))

            default_cx = float(defaults.get("cx", float(w) / 2.0))
            default_cy = float(defaults.get("cy", float(h) / 2.0))
            # AC0814_M was hand-traced with a noticeably stable left circle margin
            # and a perfectly horizontal connector. In medium/large plain variants
            # the raster fit can still drift the ring toward the connector. Keep
            # the circle near the semantic template, but allow a bounded leftward
            # correction for medium canvases where the traced source circle sits
            # slightly further left than the generic template baseline.
            medium_plain_canvas = h <= 22 and w <= 38
            max_left_correction = max(0.0, default_r * 0.14) if medium_plain_canvas else 0.0
            corrected_cx = default_cx
            if max_left_correction > 0.0:
                corrected_cx = float(Action._clipScalar(cx, default_cx - max_left_correction, default_cx))
            params["cx"] = corrected_cx
            if medium_plain_canvas:
                params["template_circle_cx"] = corrected_cx
            params["cy"] = float(Action._clipScalar(cy, default_cy - 0.6, default_cy + 0.6))
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            params["lock_arm_center_to_circle"] = True
            cx = float(params["cx"])
            cy = float(params["cy"])

        params["r"] = r

        params["arm_enabled"] = True
        params["arm_stroke"] = arm_stroke
        params["arm_x1"] = min(float(w), cx + r)
        params["arm_y1"] = cy
        params["arm_x2"] = float(w)
        params["arm_y2"] = cy
        current_arm_len = float(math.hypot(params["arm_x2"] - params["arm_x1"], params["arm_y2"] - params["arm_y1"]))
        default_arm_len = max(
            0.0,
            float(w) - (float(defaults.get("cx", float(h) / 2.0)) + float(defaults.get("r", float(h) * 0.4))),
        )
        semantic_arm_len_min = max(1.0, default_arm_len * 0.75)
        min_arm_len_ratio = 0.75
        if elongated_plain_badge:
            min_arm_len_ratio = 0.82
        params["arm_len_min_ratio"] = float(max(float(params.get("arm_len_min_ratio", min_arm_len_ratio)), min_arm_len_ratio))
        params["arm_len_min"] = max(
            1.0,
            current_arm_len * float(params["arm_len_min_ratio"]),
            semantic_arm_len_min,
        )
        return Action._normalizeLightCircleColors(params)

    @staticmethod
    def _defaultAc0810Params(w: int, h: int) -> dict:
        """AC0810 uses the same right-arm geometry as AC0814 (circle on the left)."""
        return Action._defaultAc0814Params(w, h)

    @staticmethod
    def _fitAc0810ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0810 with the same right-anchored arm behavior as AC0814."""
        return Action._fit_ac0814_params_from_image(img, defaults)

    @staticmethod
    def _glyphBbox(text_mode: str) -> tuple[int, int, int, int]:
        if text_mode == "path_t":
            return Action.T_XMIN, Action.T_YMIN, Action.T_XMAX, Action.T_YMAX
        return Action.M_XMIN, Action.M_YMIN, Action.M_XMAX, Action.M_YMAX

    @staticmethod
    def _centerGlyphBbox(params: dict) -> None:
        if "s" not in params or "cx" not in params or "cy" not in params:
            return
        xmin, ymin, xmax, ymax = Action._glyphBbox(params.get("text_mode", "path"))
        glyph_width = (xmax - xmin) * params["s"]
        glyph_height = (ymax - ymin) * params["s"]
        params["tx"] = float(params["cx"] - (glyph_width / 2.0))
        params["ty"] = float(params["cy"] - (glyph_height / 2.0))

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
            scale = min(w, h) / 25.0 if min(w, h) > 0 else 1.0
            b = Action.AR0100_BASE
            params = {
                "cx": b["cx"] * scale,
                "cy": b["cy"] * scale,
                "r": b["r"] * scale,
                "stroke_circle": b["stroke_width"] * scale,
                "fill_gray": b["fill_gray"],
                "stroke_gray": b["stroke_gray"],
                "text_gray": b["text_gray"],
                "tx": b["tx"] * scale,
                "ty": b["ty"] * scale,
                "s": b["s"] * scale,
                "label": "M",
                "text_mode": "path",
            }
            Action._centerGlyphBbox(params)
            return params

        if name == "AC0870":
            defaults = Action._defaultAc0870Params(w, h)
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fitAc0870ParamsFromImage(img, defaults))

        if name == "AC0800":
            scale = min(w, h) / 30.0 if min(w, h) > 0 else 1.0
            defaults = {
                "cx": 15.0 * scale,
                "cy": 15.0 * scale,
                "r": 10.8 * scale,
                "stroke_circle": 1.5 * scale,
                "fill_gray": 220,
                "stroke_gray": 152,
                "draw_text": False,
            }
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fit_semantic_badge_from_image(img, defaults))

        if name == "AC0811":
            defaults = Action._defaultAc0811Params(w, h)
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fit_ac0811_params_from_image(img, defaults))

        if name == "AC0810":
            defaults = Action._defaultAc0810Params(w, h)
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fitAc0810ParamsFromImage(img, defaults))

        if name == "AC0812":
            defaults = Action._defaultAc0812Params(w, h)
            if img is None:
                return Action._enforceLeftArmBadgeGeometry(Action._finalizeAc08Style(name, defaults), w, h)
            return Action._enforceLeftArmBadgeGeometry(
                Action._finalizeAc08Style(name, Action._fit_ac0812_params_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0813":
            defaults = Action._defaultAc0813Params(w, h)
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fitAc0813ParamsFromImage(img, defaults))

        if name == "AC0814":
            defaults = Action._defaultAc0814Params(w, h)
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fit_ac0814_params_from_image(img, defaults))

        if name == "AC0881":
            defaults = Action._defaultAc0881Params(w, h)
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fit_semantic_badge_from_image(img, defaults))

        if name == "AC0882":
            defaults = Action._defaultAc0882Params(w, h)
            if img is None:
                return Action._enforceLeftArmBadgeGeometry(Action._finalizeAc08Style(name, defaults), w, h)
            return Action._enforceLeftArmBadgeGeometry(
                Action._finalizeAc08Style(name, Action._fit_semantic_badge_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0820":
            defaults = Action._applyCo2Label(Action._defaultAc0870Params(w, h))
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._applyCo2Label(Action._fit_semantic_badge_from_image(img, defaults)))

        if name == "AC0831":
            defaults = Action._applyCo2Label(Action._defaultAc0881Params(w, h))
            if img is None:
                return Action._finalizeAc08Style(name, Action._tuneAc0831Co2Badge(defaults))
            return Action._finalizeAc08Style(
                name,
                Action._tuneAc0831Co2Badge(Action._fit_ac0811_params_from_image(img, defaults)),
            )

        if name == "AC0832":
            defaults = Action._applyCo2Label(Action._defaultAc0812Params(w, h))
            if img is None:
                return Action._enforceLeftArmBadgeGeometry(
                    Action._finalizeAc08Style(name, Action._tuneAc0832Co2Badge(defaults)),
                    w,
                    h,
                )
            return Action._enforceLeftArmBadgeGeometry(
                Action._finalizeAc08Style(
                    name,
                    Action._tuneAc0832Co2Badge(Action._fit_ac0812_params_from_image(img, defaults)),
                ),
                w,
                h,
            )

        if name == "AC0833":
            defaults = Action._tuneAc0833Co2Badge(Action._applyCo2Label(Action._defaultAc0813Params(w, h)))
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._tuneAc0833Co2Badge(Action._fitAc0813ParamsFromImage(img, defaults)))

        if name == "AC0834":
            defaults = Action._applyCo2Label(Action._defaultAc0814Params(w, h))
            if img is None:
                return Action._finalizeAc08Style(name, Action._tuneAc0834Co2Badge(defaults, w, h))
            return Action._finalizeAc08Style(
                name,
                Action._tuneAc0834Co2Badge(
                    Action._fit_ac0814_params_from_image(img, defaults),
                    w,
                    h,
                ),
            )

        if name == "AC0835":
            # AC0835 belongs to the right-arm VOC connector family.
            defaults = Action._applyVocLabel(Action._defaultAc0814Params(w, h))
            if img is None:
                return Action._finalizeAc08Style(name, Action._tuneAc0835VocBadge(defaults, w, h))
            return Action._finalizeAc08Style(
                name,
                Action._tuneAc0835VocBadge(
                    Action._fit_ac0814_params_from_image(img, defaults),
                    w,
                    h,
                ),
            )

        if name == "AC0836":
            defaults = Action._applyVocLabel(Action._defaultAc0881Params(w, h))
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fit_ac0811_params_from_image(img, defaults))

        if name == "AC0837":
            defaults = Action._applyVocLabel(Action._defaultAc0812Params(w, h))
            if img is None:
                return Action._enforceLeftArmBadgeGeometry(Action._finalizeAc08Style(name, defaults), w, h)
            return Action._enforceLeftArmBadgeGeometry(
                Action._finalizeAc08Style(name, Action._fit_ac0812_params_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0838":
            # AC0838 is part of the right-arm VOC family (same geometry class as
            # AC0814/AC0839), not the top-stem family.
            defaults = Action._applyVocLabel(Action._defaultAc0814Params(w, h))
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fit_ac0814_params_from_image(img, defaults))

        if name == "AC0839":
            defaults = Action._applyVocLabel(Action._defaultAc0814Params(w, h))
            if img is None:
                return Action._finalizeAc08Style(name, defaults)
            return Action._finalizeAc08Style(name, Action._fit_ac0814_params_from_image(img, defaults))

        return None

    @staticmethod
    def generateBadgeSvg(w: int, h: int, p: dict) -> str:
        p = Action._alignStemToCircleCenter(dict(p))
        p = Action._quantizeBadgeParams(p, w, h)
        elements = [
            f'<svg width="{w}px" height="{h}px" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        ]

        background_fill = p.get("background_fill")
        if background_fill:
            elements.append(
                f'  <rect x="0" y="0" width="{float(w):.4f}" height="{float(h):.4f}" fill="{background_fill}"/>'
            )

        if p.get("arm_enabled"):
            arm_x1 = float(Action._clipScalar(float(p.get("arm_x1", 0.0)), 0.0, float(w)))
            arm_y1 = float(Action._clipScalar(float(p.get("arm_y1", p.get("arm_y", 0.0))), 0.0, float(h)))
            arm_x2 = float(Action._clipScalar(float(p.get("arm_x2", 0.0)), 0.0, float(w)))
            arm_y2 = float(Action._clipScalar(float(p.get("arm_y2", p.get("arm_y", arm_y1))), 0.0, float(h)))
            arm_stroke = float(p["arm_stroke"])

            elements.append(
                (
                    f'  <line x1="{arm_x1:.4f}" y1="{arm_y1:.4f}" '
                    f'x2="{arm_x2:.4f}" y2="{arm_y2:.4f}" '
                    f'stroke="{Action.grayhex(p.get("stroke_gray", 152))}" '
                    f'stroke-width="{arm_stroke:.4f}" stroke-linecap="round"/>'
                )
            )

        if p.get("stem_enabled"):
            stem_x = float(Action._clipScalar(float(p.get("stem_x", 0.0)), 0.0, float(w)))
            stem_top = float(Action._clipScalar(float(p.get("stem_top", 0.0)), 0.0, float(h)))
            stem_width = max(0.0, min(float(p.get("stem_width", 0.0)), max(0.0, float(w) - stem_x)))
            stem_bottom = float(Action._clipScalar(float(p.get("stem_bottom", 0.0)), stem_top, float(h)))
            elements.append(
                (
                    f'  <rect x="{stem_x:.4f}" y="{stem_top:.4f}" '
                    f'width="{stem_width:.4f}" height="{max(0.0, stem_bottom - stem_top):.4f}" '
                    f'fill="{Action.grayhex(p.get("stem_gray", p["stroke_gray"]))}"/>'
                )
            )

        if p.get("circle_enabled", True):
            elements.append(
                (
                    f'  <circle cx="{p["cx"]:.4f}" cy="{p["cy"]:.4f}" r="{p["r"]:.4f}" '
                    f'fill="{Action.grayhex(p["fill_gray"])}" stroke="{Action.grayhex(p["stroke_gray"])}" '
                    f'stroke-width="{p["stroke_circle"]:.4f}"/>'
                )
            )

        if p.get("draw_text", True):
            if p.get("text_mode") == "path_t":
                elements.append(
                    (
                        f'  <path d="{Action.T_PATH_D}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'transform="translate({p["tx"]:.4f},{p["ty"]:.4f}) '
                        f'scale({p["s"]:.6f},{-p["s"]:.6f}) '
                        f'translate({-Action.T_XMIN},{-Action.T_YMAX})"/>'
                    )
                )
            elif p.get("text_mode") == "co2":
                layout = Action._co2Layout(p)
                font_size = float(layout["font_size"])
                y_text = float(layout["y_base"])
                width_scale = float(layout.get("width_scale", 1.0))
                elements.append(
                    (
                        f'  <text x="{float(layout["co_x"]):.4f}" y="{y_text:.4f}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.4f}px" '
                        f'font-style="normal" font-weight="600" text-anchor="middle" dominant-baseline="middle" '
                        f'transform="translate({float(layout["co_x"]):.4f} {y_text:.4f}) scale({width_scale:.4f} 1) '
                        f'translate({-float(layout["co_x"]):.4f} {-y_text:.4f})">CO</text>'
                    )
                )
                elements.append(
                    (
                        f'  <text x="{float(layout["subscript_x"]):.4f}" y="{float(layout["subscript_y"]):.4f}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'font-family="Arial, Helvetica, sans-serif" font-size="{float(layout["sub_font_px"]):.4f}px" '
                        f'font-style="normal" font-weight="600" text-anchor="start" dominant-baseline="middle" '
                        f'transform="translate({float(layout["subscript_x"]):.4f} {float(layout["subscript_y"]):.4f}) scale({width_scale:.4f} 1) '
                        f'translate({-float(layout["subscript_x"]):.4f} {-float(layout["subscript_y"]):.4f})">2</text>'
                    )
                )
            elif p.get("text_mode") == "voc":
                radius = p.get("r", min(w, h) * 0.4)
                font_size = max(4.0, radius * p.get("voc_font_scale", 0.52))
                voc_dy = p.get("voc_dy", 0.0)
                voc_weight = int(p.get("voc_weight", 600))
                elements.append(
                    (
                        f'  <text x="{p["cx"]:.4f}" y="{(p["cy"] + voc_dy):.4f}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.4f}px" '
                        f'font-style="normal" font-weight="{voc_weight}" letter-spacing="0.01em" '
                        f'text-anchor="middle" dominant-baseline="middle">VOC</text>'
                    )
                )
            else:
                elements.append(
                    (
                        f'  <path d="{Action.M_PATH_D}" fill="{Action.grayhex(p["text_gray"])}" '
                        f'transform="translate({p["tx"]:.4f},{p["ty"]:.4f}) '
                        f'scale({p["s"]:.6f},{-p["s"]:.6f}) '
                        f'translate({-Action.M_XMIN},{-Action.M_YMAX})"/>'
                    )
                )

        elements.append("</svg>")
        return "\n".join(elements)

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
        if img_segment is None or img_segment.size == 0:
            return []

        data = np.float32(img_segment).reshape((-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)
        _, labels, centers = cv2.kmeans(data, 4, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
        img_quant = centers[labels.flatten()].reshape(img_segment.shape)

        unique, counts = np.unique(img_quant.reshape(-1, 3), axis=0, return_counts=True)
        bg_color = unique[np.argmax(counts)]

        paths: list[str] = []
        for color in unique:
            if np.array_equal(color, bg_color):
                continue

            mask = cv2.inRange(img_quant, color, color)
            # Keep the raw contour points and let approxPolyDP control how much
            # simplification is applied via `epsilon_factor`.
            #
            # With CHAIN_APPROX_SIMPLE, OpenCV already drops many intermediate
            # points, which can make the iterative epsilon sweep effectively a
            # no-op (same polygon across all iterations).
            contours, _ = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
            hex_color = rgbToHex(color[::-1])

            for contour in contours:
                if cv2.contourArea(contour) < 10:
                    continue

                epsilon = epsilon_factor * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                path_d = "M " + " L ".join(
                    [
                        (
                            f"{(pt[0][0] * scale_x) + offset_x:.3f},"
                            f"{(pt[0][1] * scale_y) + offset_y:.3f}"
                        )
                        for pt in approx
                    ]
                ) + " Z"
                paths.append(f'  <path d="{path_d}" fill="{hex_color}" stroke="none" />')
        return paths

    @staticmethod
    def generateCompositeSvg(w: int, h: int, params: dict, folder_path: str, epsilon: float) -> str:
        svg_elements = [
            (
                f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
                'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">'
            )
        ]

        if params["top_source_ref"]:
            ref_path = None
            for ext in [".jpg", ".JPG", ".jpeg", ".JPEG", ".bmp", ".png", ".PNG"]:
                p = os.path.join(folder_path, params["top_source_ref"] + ext)
                if os.path.exists(p):
                    ref_path = p
                    break

            if ref_path:
                ref_img = cv2.imread(ref_path)
                ref_h, ref_w = ref_img.shape[:2]
                cut_ratio = 0.55
                cut_y = max(1, int(round(ref_h * cut_ratio)))
                top_half_img = ref_img[0:cut_y, 0:ref_w]
                target_top_h = max(1, int(round(h * cut_ratio)))
                scale_x = w / ref_w if ref_w > 0 else 1.0
                scale_y = target_top_h / cut_y if cut_y > 0 else 1.0
                svg_elements.extend(
                    Action.traceImageSegment(
                        top_half_img,
                        epsilon,
                        scale_x=scale_x,
                        scale_y=scale_y,
                    )
                )

        if params["bottom_shape"] == "square_cross":
            cx = w / 2
            cy = h * 0.75
            s = min(w, h) * 0.15
            sw = w * 0.02
            svg_elements.append(
                f'  <rect x="{cx-s}" y="{cy-s}" width="{s*2}" height="{s*2}" fill="#e6e6e6" stroke="#4d4d4d" stroke-width="{sw}"/>'
            )
            svg_elements.append(
                f'  <line x1="{cx-s}" y1="{cy-s}" x2="{cx+s}" y2="{cy+s}" stroke="#4d4d4d" stroke-width="{sw}"/>'
            )
            svg_elements.append(
                f'  <line x1="{cx+s}" y1="{cy-s}" x2="{cx-s}" y2="{cy+s}" stroke="#4d4d4d" stroke-width="{sw}"/>'
            )

        svg_elements.append("</svg>")
        return "\n".join(svg_elements)

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
        """Return mean/std of per-pixel squared RGB deltas.

        Per-pixel metric:
            delta2 = (ΔR)^2 + (ΔG)^2 + (ΔB)^2
        """
        if img_svg is None:
            return float("inf"), float("inf")
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
        diff = img_orig.astype(np.float32) - img_svg.astype(np.float32)
        delta2 = np.sum(diff * diff, axis=2)
        return float(np.mean(delta2)), float(np.std(delta2))

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
        changed = False
        scale = float(Action._clipScalar(diag_scale, 0.85, 1.18))

        if element == "circle" and apply_circle_geometry_penalty:
            old_cx = float(params["cx"])
            old_cy = float(params["cy"])
            old_r = float(params["r"])
            min_r = float(max(1.0, params.get("min_circle_radius", 1.0)))
            if "circle_radius_lower_bound_px" in params:
                min_r = float(max(min_r, float(params.get("circle_radius_lower_bound_px", min_r))))
            max_r = float(min(w, h)) * 0.48
            if bool(params.get("allow_circle_overflow", False)):
                max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
            if bool(params.get("lock_circle_cx", False)):
                params["cx"] = old_cx
            else:
                params["cx"] = float(Action._clipScalar(old_cx + center_dx * 0.65, 0.0, float(w - 1)))
            if bool(params.get("lock_circle_cy", False)):
                params["cy"] = old_cy
            else:
                params["cy"] = float(Action._clipScalar(old_cy + center_dy * 0.65, 0.0, float(h - 1)))
            params["r"] = float(Action._clipScalar(old_r * scale, min_r, max_r))
            changed = (
                abs(params["cx"] - old_cx) > 0.02
                or abs(params["cy"] - old_cy) > 0.02
                or abs(params["r"] - old_r) > 0.02
            )

        elif element == "stem" and params.get("stem_enabled"):
            old_x = float(params["stem_x"])
            old_w = float(params["stem_width"])
            old_top = float(params["stem_top"])
            old_bottom = float(params["stem_bottom"])

            stem_cx = old_x + (old_w / 2.0)
            if bool(params.get("lock_stem_center_to_circle", False)):
                stem_cx = float(params.get("cx", stem_cx))
            else:
                stem_cx = float(Action._clipScalar(stem_cx + center_dx * 0.75, 0.0, float(w - 1)))
            new_w = float(Action._clipScalar(old_w * scale, 1.0, float(w) * 0.22))
            params["stem_width"] = new_w
            params["stem_x"] = float(Action._clipScalar(stem_cx - (new_w / 2.0), 0.0, float(w) - new_w))
            params["stem_top"] = float(Action._clipScalar(old_top + center_dy * 0.45, 0.0, float(h - 2)))
            params["stem_bottom"] = float(Action._clipScalar(old_bottom + center_dy * 0.25, params["stem_top"] + 1.0, float(h - 1)))
            changed = (
                abs(params["stem_x"] - old_x) > 0.02
                or abs(params["stem_width"] - old_w) > 0.02
                or abs(params["stem_top"] - old_top) > 0.02
                or abs(params["stem_bottom"] - old_bottom) > 0.02
            )

        elif element == "arm" and params.get("arm_enabled"):
            old_x1 = float(params["arm_x1"])
            old_x2 = float(params["arm_x2"])
            old_y1 = float(params["arm_y1"])
            old_y2 = float(params["arm_y2"])
            old_stroke = float(params.get("arm_stroke", params.get("stem_or_arm", 1.0)))

            ax1 = old_x1 + center_dx * 0.75
            ax2 = old_x2 + center_dx * 0.75
            ay1 = old_y1 + center_dy * 0.75
            ay2 = old_y2 + center_dy * 0.75
            acx = (ax1 + ax2) / 2.0
            acy = (ay1 + ay2) / 2.0
            vx = (ax2 - ax1) * scale
            vy = (ay2 - ay1) * scale

            params["arm_x1"] = float(Action._clipScalar(acx - (vx / 2.0), 0.0, float(w - 1)))
            params["arm_x2"] = float(Action._clipScalar(acx + (vx / 2.0), 0.0, float(w - 1)))
            params["arm_y1"] = float(Action._clipScalar(acy - (vy / 2.0), 0.0, float(h - 1)))
            params["arm_y2"] = float(Action._clipScalar(acy + (vy / 2.0), 0.0, float(h - 1)))
            params["arm_stroke"] = float(Action._clipScalar(old_stroke * scale, 1.0, float(min(w, h)) * 0.18))
            changed = (
                abs(params["arm_x1"] - old_x1) > 0.02
                or abs(params["arm_x2"] - old_x2) > 0.02
                or abs(params["arm_y1"] - old_y1) > 0.02
                or abs(params["arm_y2"] - old_y2) > 0.02
                or abs(params["arm_stroke"] - old_stroke) > 0.02
            )

        elif element == "text" and params.get("draw_text", True):
            mode = str(params.get("text_mode", "")).lower()
            r = max(1.0, float(params.get("r", min(w, h) * 0.45)))

            # Keep text alignment iterative on the vertical axis so badges such as
            # AC0820_L can converge against the source when "CO" drifts too high.
            if mode == "co2":
                old_dy = float(params.get("co2_dy", 0.0))
                params["co2_dy"] = float(Action._clipScalar(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
                changed = abs(params["co2_dy"] - old_dy) > 0.02
            elif mode == "voc":
                old_dy = float(params.get("voc_dy", 0.0))
                params["voc_dy"] = float(Action._clipScalar(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
                changed = abs(params["voc_dy"] - old_dy) > 0.02
            elif "ty" in params:
                old_ty = float(params.get("ty", 0.0))
                params["ty"] = float(Action._clipScalar(old_ty + center_dy * 0.75, 0.0, float(h - 1)))
                changed = abs(params["ty"] - old_ty) > 0.02

        return changed

    @staticmethod
    def _estimateVerticalStemFromMask(
        mask: np.ndarray,
        expected_cx: float,
        y_start: int,
        y_end: int,
    ) -> tuple[float, float] | None:
        """Estimate stem center/width from foreground mask rows.

        The estimate is intentionally iterative: we repeatedly reject outliers around
        the running median width so anti-aliased pixels at the circle junction do not
        inflate the final width.
        """
        h, w = mask.shape[:2]
        y1 = max(0, min(h, int(y_start)))
        y2 = max(y1, min(h, int(y_end)))
        if y2 <= y1:
            return None

        # The rows directly below the circle/stem junction are frequently widened
        # by anti-aliased ring pixels. Bias the estimator towards the lower stem
        # segment so thin stems (e.g. tall AC0811 variants) are not over-thickened.
        span = y2 - y1
        if span >= 8:
            y1 = min(y2 - 1, y1 + int(round(span * 0.25)))

        widths: list[float] = []
        centers: list[float] = []
        cx_idx = int(round(expected_cx))

        for y in range(y1, y2):
            row = mask[y]
            xs = np.where(row)[0]
            if xs.size == 0:
                continue

            split_points = np.where(np.diff(xs) > 1)[0]
            runs = np.split(xs, split_points + 1)
            if not runs:
                continue

            # Prefer the run that contains the expected center, otherwise nearest run.
            chosen = None
            nearest_dist = float("inf")
            for run in runs:
                rx1, rx2 = int(run[0]), int(run[-1])
                if rx1 <= cx_idx <= rx2:
                    chosen = run
                    break
                dist = min(abs(cx_idx - rx1), abs(cx_idx - rx2))
                if dist < nearest_dist:
                    nearest_dist = dist
                    chosen = run

            if chosen is None:
                continue

            rw = float((chosen[-1] - chosen[0]) + 1)
            rcx = float((chosen[0] + chosen[-1]) / 2.0)
            widths.append(rw)
            centers.append(rcx)

        if not widths:
            return None

        widths_arr = np.array(widths, dtype=np.float32)
        centers_arr = np.array(centers, dtype=np.float32)
        keep = np.ones(widths_arr.shape[0], dtype=bool)

        for _ in range(3):
            sel_w = widths_arr[keep]
            if sel_w.size < 3:
                break
            med = float(np.median(sel_w))
            tol = max(1.0, med * 0.35)
            new_keep = keep & (np.abs(widths_arr - med) <= tol)
            if int(np.sum(new_keep)) == int(np.sum(keep)):
                break
            keep = new_keep

        if int(np.sum(keep)) == 0:
            return None

        est_width = float(np.median(widths_arr[keep]))
        est_cx = float(np.median(centers_arr[keep]))
        est_width = max(1.0, min(est_width, float(w)))
        return est_cx, est_width

    @staticmethod
    def _ringAndFillMasks(h: int, w: int, params: dict) -> tuple[np.ndarray, np.ndarray]:
        yy, xx = np.indices((h, w))
        dist = np.sqrt((xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2)
        ring_half = max(0.7, params["stroke_circle"])
        ring = np.abs(dist - params["r"]) <= ring_half
        fill = dist <= max(0.5, params["r"] - ring_half)
        return ring, fill

    @staticmethod
    def _meanGrayForMask(img: np.ndarray, mask: np.ndarray) -> float | None:
        if int(mask.sum()) == 0:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        vals = gray[mask]
        if vals.size == 0:
            return None
        return float(np.mean(vals))

    @staticmethod
    def _elementRegionMask(
        h: int,
        w: int,
        params: dict,
        element: str,
        apply_circle_geometry_penalty: bool = True,
    ) -> np.ndarray | None:
        yy, xx = np.indices((h, w))
        context_pad = max(2.0, float(min(h, w)) * 0.12)
        if element == "circle" and apply_circle_geometry_penalty:
            radius_with_context = params["r"] + context_pad
            circle = (xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2 <= radius_with_context**2
            top = yy <= (params["cy"] + params["r"] + context_pad)
            return circle & top
        if element == "stem" and params.get("stem_enabled"):
            x1 = max(0.0, params["stem_x"] - context_pad)
            x2 = min(float(w), params["stem_x"] + params["stem_width"] + context_pad)
            y1 = max(0.0, params["stem_top"] - context_pad)
            y2 = min(float(h), params["stem_bottom"] + context_pad)
            return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)
        if element == "arm" and params.get("arm_enabled"):
            x1 = max(0.0, min(params.get("arm_x1", 0.0), params.get("arm_x2", 0.0)) - context_pad)
            x2 = min(float(w), max(params.get("arm_x1", 0.0), params.get("arm_x2", 0.0)) + context_pad)
            y1 = max(0.0, min(params.get("arm_y1", 0.0), params.get("arm_y2", 0.0)) - context_pad)
            y2 = min(float(h), max(params.get("arm_y1", 0.0), params.get("arm_y2", 0.0)) + context_pad)
            pad = max(1.0, params.get("arm_stroke", params.get("stem_or_arm", 1.0)) * 0.8)
            return (xx >= (x1 - pad)) & (xx <= (x2 + pad)) & (yy >= (y1 - pad)) & (yy <= (y2 + pad))
        if element == "text" and params.get("draw_text", True):
            x1, y1, x2, y2 = Action._textBbox(params)
            x1 = max(0.0, x1 - context_pad)
            y1 = max(0.0, y1 - context_pad)
            x2 = min(float(w), x2 + context_pad)
            y2 = min(float(h), y2 + context_pad)
            return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)
        return None

    @staticmethod
    def _textBbox(params: dict) -> tuple[float, float, float, float]:
        """Approximate text bounding box for semantic badge text modes."""
        cx = float(params.get("cx", 0.0))
        cy = float(params.get("cy", 0.0))
        r = max(1.0, float(params.get("r", 1.0)))
        mode = str(params.get("text_mode", "")).lower()

        if mode == "voc":
            font_size = max(4.0, r * float(params.get("voc_font_scale", 0.52)))
            width = font_size * 1.95
            height = font_size * 0.90
            y = cy + float(params.get("voc_dy", 0.0))
            return (cx - (width / 2.0), y - (height / 2.0), cx + (width / 2.0), y + (height / 2.0))

        if mode == "co2":
            layout = Action._co2Layout(params)
            x1 = float(layout["x1"])
            x2 = float(layout["x2"])
            y = float(layout["y_base"])
            height = float(layout["height"])
            return (x1, y - (height / 2.0), x2, y + (height / 2.0))

        # path/path_t fallback via known glyph bounds.
        s = float(params.get("s", 0.0))
        tx = float(params.get("tx", cx))
        ty = float(params.get("ty", cy))
        xmin, ymin, xmax, ymax = Action._glyphBbox(params.get("text_mode", "path"))
        x1 = tx + (xmin * s)
        y1 = ty + (ymin * s)
        x2 = tx + (xmax * s)
        y2 = ty + (ymax * s)
        return (x1, y1, x2, y2)

    @staticmethod
    def _foregroundMask(img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, fg_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Tiny anti-aliased badges can have only a few gray levels; a pure Otsu
        # split then frequently drops the ring entirely. Blend in a gentle local
        # contrast cue so faint circular strokes remain available to downstream
        # semantic checks without over-activating the white background.
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        local_contrast = cv2.absdiff(gray, blur)
        contrast_thresh = max(2, int(round(float(np.percentile(local_contrast, 82)))))
        fg_contrast = local_contrast >= contrast_thresh

        fg = (fg_otsu > 0) | fg_contrast
        fg_u8 = fg.astype(np.uint8) * 255
        kernel = np.ones((2, 2), dtype=np.uint8)
        fg_u8 = cv2.morphologyEx(fg_u8, cv2.MORPH_CLOSE, kernel, iterations=1)
        return fg_u8 > 0

    @staticmethod
    def _circleFromForegroundMask(fg_mask: np.ndarray) -> tuple[float, float, float] | None:
        """Infer a coarse circle from the foreground mask when Hough is too brittle."""
        mask_u8 = (fg_mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        h, w = fg_mask.shape[:2]
        min_side = float(max(1, min(h, w)))
        best: tuple[float, float, float, float] | None = None

        for cnt in contours:
            area = float(cv2.contourArea(cnt))
            if area < max(4.0, min_side * 0.35):
                continue
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < 3 or bh < 3:
                continue
            aspect = float(bw) / max(1.0, float(bh))
            if not (0.65 <= aspect <= 1.35):
                continue

            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            radius = float(radius)
            if radius < max(2.5, min_side * 0.10) or radius > max(8.0, min_side * 0.55):
                continue

            dist = np.sqrt((cnt[:, 0, 0].astype(np.float32) - cx) ** 2 + (cnt[:, 0, 1].astype(np.float32) - cy) ** 2)
            if dist.size == 0:
                continue
            radial_residual = float(np.mean(np.abs(dist - radius)))
            circle_area = math.pi * radius * radius
            fill_ratio = area / max(1.0, circle_area)
            if fill_ratio < 0.30:
                continue
            bins = 12
            coverage_bins = np.zeros(bins, dtype=np.uint8)
            for px, py in cnt[:, 0, :]:
                ang = math.atan2(float(py) - cy, float(px) - cx)
                idx = int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins
                coverage_bins[idx] = 1
            coverage = int(np.sum(coverage_bins))
            if coverage < 6:
                continue

            bbox_fill_ratio = area / max(1.0, float(bw * bh))
            # Favor thin ring-like circles or broadly circular contour support.
            if bbox_fill_ratio > 0.82 and radial_residual > max(1.0, radius * 0.22):
                continue

            score = radial_residual + abs(1.0 - aspect) * 3.0 + max(0, 7 - coverage) * 0.75
            if best is None or score < best[0]:
                best = (score, float(cx), float(cy), radius)

        if best is None:
            return None
        return best[1], best[2], best[3]

    @staticmethod
    def _maskSupportsCircle(mask: np.ndarray | None) -> bool:
        if mask is None:
            return False
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count < 4:
            return False

        bbox = Action._maskBbox(mask)
        if bbox is None:
            return False
        x1, y1, x2, y2 = bbox
        width = max(1.0, (x2 - x1) + 1.0)
        height = max(1.0, (y2 - y1) + 1.0)
        if not (0.60 <= (width / height) <= 1.40):
            return False

        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        approx_radius = max(1.0, (width + height) * 0.25)
        area = width * height
        density = float(pixel_count) / max(1.0, area)
        if density < 0.04:
            return False

        ys, xs = np.where(mask)
        bins = 12
        coverage_bins = np.zeros(bins, dtype=np.uint8)
        ring_tol = max(1.2, approx_radius * 0.45)
        near_ring = 0
        for py, px in zip(ys, xs, strict=False):
            dist = math.hypot(float(px) - cx, float(py) - cy)
            if abs(dist - approx_radius) > ring_tol:
                continue
            near_ring += 1
            ang = math.atan2(float(py) - cy, float(px) - cx)
            idx = int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins
            coverage_bins[idx] = 1

        coverage = int(np.sum(coverage_bins))
        if coverage >= 4 and near_ring >= max(4, int(round(pixel_count * 0.35))):
            return True

        mask_u8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        cnt = max(contours, key=cv2.contourArea)
        perimeter = float(cv2.arcLength(cnt, True))
        if perimeter <= 0.0:
            return False
        contour_area = float(cv2.contourArea(cnt))
        circularity = (4.0 * math.pi * contour_area) / max(1e-6, perimeter * perimeter)
        return circularity >= 0.28 and density <= 0.72

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
        only = dict(params)
        only["draw_text"] = bool(params.get("draw_text", True) and element == "text")
        only["circle_enabled"] = element == "circle"
        only["stem_enabled"] = bool(params.get("stem_enabled") and element == "stem")
        only["arm_enabled"] = bool(params.get("arm_enabled") and element == "arm")
        return only

    @staticmethod
    def _maskedError(img_orig: np.ndarray, img_svg: np.ndarray, mask: np.ndarray | None) -> float:
        if img_svg is None or mask is None or int(mask.sum()) == 0:
            return float("inf")
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
        gray_diff = cv2.cvtColor(cv2.absdiff(img_orig, img_svg), cv2.COLOR_BGR2GRAY).astype(np.float32)
        valid = mask.astype(np.float32)
        if float(np.sum(valid)) <= 0.0:
            return float("inf")
        weighted = gray_diff * valid
        return float(np.sum(weighted))

    @staticmethod
    def _unionBboxFromMasks(mask_a: np.ndarray | None, mask_b: np.ndarray | None) -> tuple[int, int, int, int] | None:
        boxes: list[tuple[float, float, float, float]] = []
        if mask_a is not None:
            box_a = Action._maskBbox(mask_a)
            if box_a is not None:
                boxes.append(box_a)
        if mask_b is not None:
            box_b = Action._maskBbox(mask_b)
            if box_b is not None:
                boxes.append(box_b)
        if not boxes:
            return None

        x1 = int(np.floor(min(b[0] for b in boxes)))
        y1 = int(np.floor(min(b[1] for b in boxes)))
        x2 = int(np.ceil(max(b[2] for b in boxes)))
        y2 = int(np.ceil(max(b[3] for b in boxes)))
        return x1, y1, x2, y2

    @staticmethod
    def _maskedUnionErrorInBbox(
        img_orig: np.ndarray,
        img_svg: np.ndarray,
        mask_orig: np.ndarray | None,
        mask_svg: np.ndarray | None,
    ) -> float:
        """Symmetric masked error, cropped to the smallest rectangle around both masks."""
        if img_svg is None or mask_orig is None or mask_svg is None:
            return float("inf")
        if not hasattr(img_orig, "__getitem__"):
            return 0.0
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)

        bbox = Action._unionBboxFromMasks(mask_orig, mask_svg)
        if bbox is None:
            return float("inf")

        h, w = img_orig.shape[:2]
        x1, y1, x2, y2 = bbox
        x1 = max(0, min(w - 1, x1))
        y1 = max(0, min(h - 1, y1))
        x2 = max(x1, min(w - 1, x2))
        y2 = max(y1, min(h - 1, y2))

        orig_crop = img_orig[y1 : y2 + 1, x1 : x2 + 1]
        svg_crop = img_svg[y1 : y2 + 1, x1 : x2 + 1]
        union_mask = mask_orig[y1 : y2 + 1, x1 : x2 + 1] | mask_svg[y1 : y2 + 1, x1 : x2 + 1]
        if int(np.sum(union_mask)) <= 0:
            return float("inf")

        gray_diff = cv2.cvtColor(cv2.absdiff(orig_crop, svg_crop), cv2.COLOR_BGR2GRAY).astype(np.float32)
        return float(np.sum(gray_diff * union_mask.astype(np.float32)))

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
        p = dict(params)
        p["target_fill_gray"] = int(round(float(p.get("fill_gray", Action.LIGHT_CIRCLE_FILL_GRAY))))
        p["target_stroke_gray"] = int(round(float(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))))
        if p.get("stem_enabled"):
            p["target_stem_gray"] = int(round(float(p.get("stem_gray", p["target_stroke_gray"]))))
        if p.get("draw_text", True) and "text_gray" in p:
            p["target_text_gray"] = int(round(float(p.get("text_gray", Action.LIGHT_CIRCLE_TEXT_GRAY))))
        return p

    @staticmethod
    def _applyCanonicalBadgeColors(params: dict) -> dict:
        p = dict(params)
        if "target_fill_gray" in p:
            p["fill_gray"] = int(p["target_fill_gray"])
        if "target_stroke_gray" in p:
            p["stroke_gray"] = int(p["target_stroke_gray"])
        if p.get("stem_enabled") and "target_stem_gray" in p:
            p["stem_gray"] = int(p["target_stem_gray"])
        if p.get("draw_text", True) and "target_text_gray" in p:
            p["text_gray"] = int(p["target_text_gray"])
        return p

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
        """Global multi-parameter baseline search over the shared vector."""
        if not bool(params.get("enable_global_search_mode", False)):
            return False

        near_optimum_eps_floor = 0.06
        near_optimum_eps_rel = 0.02

        h, w = img_orig.shape[:2]
        bounds = Action._globalParameterVectorBounds(params, w, h)
        vector = GlobalParameterVector.fromParams(params)

        active_keys: list[str] = []
        for key in ("cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y", "text_scale"):
            value = getattr(vector, key)
            if value is None:
                continue
            _low, _high, locked, _source = bounds[key]
            if locked:
                continue
            active_keys.append(key)

        if len(active_keys) < 4:
            logs.append(
                "global-search: übersprungen (zu wenige aktive Parameter; benötigt >=4)"
            )
            return False

        def clampVector(candidate: GlobalParameterVector) -> GlobalParameterVector:
            data = dataclasses.asdict(candidate)
            for key in active_keys:
                low, high, _locked, _source = bounds[key]
                current_value = float(data[key])
                clipped = float(Action._clip_scalar(current_value, low, high))
                if key in {"cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y"}:
                    clipped = float(Action._snap_half(clipped))
                data[key] = clipped
            return GlobalParameterVector(**data)

        def evalVector(candidate: GlobalParameterVector) -> float:
            probe = candidate.apply_to_params(params)
            if probe.get("arm_enabled"):
                Action._reanchorArmToCircleEdge(probe, float(probe.get("r", 0.0)))
            if probe.get("stem_enabled"):
                probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe.get("r", 0.0))
                if bool(probe.get("lock_stem_center_to_circle", False)):
                    stem_w = float(probe.get("stem_width", 1.0))
                    probe["stem_x"] = Action._snap_half(
                        max(0.0, min(float(w) - stem_w, float(probe.get("cx", 0.0)) - (stem_w / 2.0)))
                    )
            return Action._full_badge_error_for_params(img_orig, probe)

        def withinHardBounds(candidate: GlobalParameterVector) -> tuple[bool, str]:
            for key in active_keys:
                low, high, _locked, _source = bounds[key]
                value = float(getattr(candidate, key))
                if value < low - 1e-6 or value > high + 1e-6:
                    return False, f"{key}={value:.3f} außerhalb [{low:.3f}, {high:.3f}]"
            return True, "ok"

        rng = Action._make_rng(4099 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))
        best = clampVector(vector)
        best_err = evalVector(best)
        if not math.isfinite(best_err):
            return False
        improved = False

        spans = {key: max(0.25, float(bounds[key][1] - bounds[key][0]) * 0.20) for key in active_keys}
        plateau_rounds: list[dict[str, float | int]] = []
        logs.append(
            f"global-search: gestartet (aktive_parameter={','.join(active_keys)}, samples_pro_runde={max(8, int(samples_per_round))}, start_err={best_err:.3f})"
        )
        logs.append(
            f"global-search: near-optimum-definition (err <= best_err + epsilon, epsilon=max({near_optimum_eps_floor:.2f}, best_err*{near_optimum_eps_rel:.2f}))"
        )

        for round_idx in range(max(1, int(rounds))):
            accepted = 0
            finite_round: list[tuple[GlobalParameterVector, float]] = [(best, best_err)]
            for _ in range(max(8, int(samples_per_round))):
                sample_data = dataclasses.asdict(best)
                for key in active_keys:
                    low, high, _locked, _source = bounds[key]
                    sigma = spans[key]
                    sample_data[key] = float(Action._clip_scalar(rng.normal(float(sample_data[key]), sigma), low, high))
                candidate = clampVector(GlobalParameterVector(**sample_data))
                candidate_err = evalVector(candidate)
                if math.isfinite(candidate_err):
                    finite_round.append((candidate, candidate_err))
                if math.isfinite(candidate_err) and candidate_err + 0.05 < best_err:
                    best = candidate
                    best_err = candidate_err
                    accepted += 1
                    improved = True

            round_best_err = min(err for _cand, err in finite_round)
            round_best = min(finite_round, key=lambda item: item[1])[0]
            epsilon = max(near_optimum_eps_floor, round_best_err * near_optimum_eps_rel)
            plateau = [(cand, err) for cand, err in finite_round if err <= round_best_err + epsilon]
            span_labels: list[str] = []
            mean_span = 0.0
            if plateau:
                span_values: list[float] = []
                for key in active_keys:
                    key_values = [float(getattr(cand, key)) for cand, _err in plateau]
                    key_span = max(key_values) - min(key_values)
                    span_values.append(key_span)
                    span_labels.append(f"{key}:{key_span:.3f}")
                mean_span = sum(span_values) / max(1, len(span_values))

            representative = round_best
            representative_err = round_best_err
            representative_source = "best_sample"
            representative_reason = "niedrigster Fehler in dieser Runde"

            if plateau:
                weighted_data = dataclasses.asdict(round_best)
                weight_sum = 0.0
                for cand, cand_err in plateau:
                    weight = 1.0 / (1.0 + max(0.0, float(cand_err) - round_best_err))
                    weight_sum += weight
                    for key in active_keys:
                        weighted_data[key] = float(weighted_data[key]) + (float(getattr(cand, key)) * weight)
                if weight_sum > 0.0:
                    for key in active_keys:
                        weighted_data[key] = float(weighted_data[key]) / (1.0 + weight_sum)
                    centroid_raw = GlobalParameterVector(**weighted_data)
                    centroid = clampVector(centroid_raw)
                    centroid_safe, centroid_msg = withinHardBounds(centroid)
                    if not centroid_safe:
                        logs.append(
                            f"global-search: schwerpunkt verworfen (runde={round_idx + 1}, grund={centroid_msg})"
                        )
                    else:
                        centroid_err = evalVector(centroid)
                        if math.isfinite(centroid_err):
                            near_best_margin = max(0.02, epsilon * 0.30)
                            if centroid_err <= round_best_err + near_best_margin and len(plateau) >= 3:
                                representative = centroid
                                representative_err = centroid_err
                                representative_source = "schwerpunkt"
                                representative_reason = (
                                    "nahe am Bestpunkt und robuster Zentrumskandidat des Plateau-Bereichs"
                                )
                            elif centroid_err < round_best_err:
                                representative = centroid
                                representative_err = centroid_err
                                representative_source = "schwerpunkt"
                                representative_reason = "geringerer Fehler als best_sample"
                        else:
                            logs.append(
                                "global-search: schwerpunkt verworfen "
                                f"(runde={round_idx + 1}, grund=fehlerbewertung nicht endlich)"
                            )

            if representative_source == "schwerpunkt":
                if representative_err <= best_err + 0.02:
                    best = representative
                    best_err = representative_err
                    improved = True
            elif representative_err + 0.01 < best_err:
                best = representative
                best_err = representative_err
                improved = True

            stability = "n/a"
            if plateau_rounds:
                prev_center = float(plateau_rounds[-1]["center_mean"])
                center_now = 0.0
                if plateau:
                    center_now = sum(
                        float(getattr(plateau[0][0], key) if len(plateau) == 1 else (min(float(getattr(cand, key)) for cand, _ in plateau) + max(float(getattr(cand, key)) for cand, _ in plateau)) / 2.0)
                        for key in active_keys
                    ) / max(1, len(active_keys))
                center_shift = abs(center_now - prev_center)
                stability = "stabil" if center_shift <= 0.35 else "dynamisch"
                plateau_rounds.append({"size": len(plateau), "mean_span": mean_span, "center_mean": center_now})
            else:
                center_now = 0.0
                if plateau:
                    center_now = sum(
                        float(getattr(plateau[0][0], key) if len(plateau) == 1 else (min(float(getattr(cand, key)) for cand, _ in plateau) + max(float(getattr(cand, key)) for cand, _ in plateau)) / 2.0)
                        for key in active_keys
                    ) / max(1, len(active_keys))
                plateau_rounds.append({"size": len(plateau), "mean_span": mean_span, "center_mean": center_now})
            for key in active_keys:
                spans[key] = max(0.12, spans[key] * 0.78)
            logs.append(
                f"global-search: Runde {round_idx + 1} best_err={best_err:.3f}, akzeptierte_kandidaten={accepted}, sigma_mittel={sum(spans.values()) / max(1, len(spans)):.3f}"
            )
            logs.append(
                "global-search: near-optimum-plateau "
                f"(runde={round_idx + 1}, punkte={len(plateau)}, epsilon={epsilon:.3f}, "
                f"mittlere_spannweite={mean_span:.3f}, stabilitaet={stability}, "
                f"spannweite={'; '.join(span_labels) if span_labels else 'n/a'})"
            )
            logs.append(
                "global-search: plateau-repräsentant "
                f"(runde={round_idx + 1}, kandidat={representative_source}, err={representative_err:.3f}, "
                f"begründung={representative_reason})"
            )

        if not improved:
            logs.append("global-search: keine relevante Verbesserung")
            return False

        old_values = {key: float(getattr(vector, key)) for key in active_keys}
        new_values = {key: float(getattr(best, key)) for key in active_keys}
        params.update(best.applyToParams(params))
        delta_labels = [
            f"{key} {old_values[key]:.3f}->{new_values[key]:.3f}"
            for key in active_keys
            if abs(new_values[key] - old_values[key]) >= 0.01
        ]
        if params.get("arm_enabled"):
            Action._reanchorArmToCircleEdge(params, float(params.get("r", 0.0)))
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + float(params.get("r", 0.0))
        Action._logGlobalParameterVector(logs, params, w, h, label="global-search: final")
        logs.append(
            "global-search: übernommen "
            f"(best_err={best_err:.3f}, verbessert={', '.join(delta_labels) if delta_labels else 'keine sichtbare delta-liste'})"
        )
        return True

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
        """Refine stem width/position when validation detects a geometric mismatch."""
        orig_bbox = Action._maskBbox(mask_orig)
        svg_bbox = Action._maskBbox(mask_svg)
        if orig_bbox is None or svg_bbox is None:
            return False, None

        ox1, _oy1, ox2, _oy2 = orig_bbox
        sx1, _sy1, sx2, _sy2 = svg_bbox
        orig_w = max(1.0, (ox2 - ox1) + 1.0)
        svg_w = max(1.0, (sx2 - sx1) + 1.0)
        ratio = svg_w / orig_w

        expected_cx = float(params.get("cx", (ox1 + ox2) / 2.0))
        stroke = float(params.get("stroke_circle", 1.0))
        # Skip a small band right below the circle edge so anti-aliased ring/fill
        # pixels do not inflate stem width estimation.
        y_start = float(params.get("stem_top", 0.0)) + max(1.0, stroke * 2.0)
        y_end = float(params.get("stem_bottom", mask_orig.shape[0]))
        est = Action._estimateVerticalStemFromMask(mask_orig, expected_cx, int(y_start), int(y_end))

        if est is not None:
            est_cx, est_width = est
            min_w = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.70)
            max_w = max(
                min_w,
                min(
                    float(params.get("stem_width_max", float(w) * 0.18)),
                    min(float(w) * 0.18, float(params.get("r", 1.0)) * 0.80),
                ),
            )
            target_width = max(min_w, min(est_width, max_w))
            if bool(params.get("lock_stem_center_to_circle", False)):
                circle_cx = float(params.get("cx", est_cx))
                max_offset = float(params.get("stem_center_lock_max_offset", max(0.35, target_width * 0.75)))
                target_cx = float(Action._clipScalar(est_cx, circle_cx - max_offset, circle_cx + max_offset))
            else:
                target_cx = est_cx
            estimate_mode = "iter"
        else:
            if 0.95 <= ratio <= 1.05:
                return False, None
            target_width = float(params.get("stem_width", svg_w)) * (orig_w / svg_w)
            stem_width_cap = float(params.get("stem_width_max", float(w) * 0.20))
            target_width = max(1.0, min(target_width, min(float(w) * 0.20, stem_width_cap)))
            target_cx = (ox1 + ox2) / 2.0
            estimate_mode = "bbox"

        old_width = float(params.get("stem_width", svg_w))
        width_delta = abs(target_width - old_width)
        ratio_after = target_width / max(1.0, orig_w)

        if width_delta < 0.05 and 0.90 <= ratio_after <= 1.12:
            return False, None

        stem_width_cap = float(params.get("stem_width_max", float(w) * 0.20))
        target_width = min(target_width, stem_width_cap)
        target_width = Action._snapIntPx(target_width, minimum=1.0)
        old_x = float(params.get("stem_x", 0.0))
        old_w = float(params.get("stem_width", 1.0))
        new_x = Action._snapHalf(max(0.0, min(float(w) - target_width, target_cx - (target_width / 2.0))))
        if abs(target_width - old_w) < 0.05 and abs(new_x - old_x) < 0.05:
            return False, None
        params["stem_width"] = target_width
        params["stem_x"] = new_x
        return True, (
            f"stem: Breitenkorrektur mode={estimate_mode}, ratio={ratio:.3f}, "
            f"alt={old_width:.3f}, neu={target_width:.3f}"
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
        h, w = img_orig.shape[:2]
        logs: list[str] = []
        elements = ["circle"]
        if params.get("stem_enabled"):
            elements.append("stem")
        if params.get("arm_enabled"):
            elements.append("arm")
        if params.get("draw_text", True):
            elements.append("text")
        best_params = copy.deepcopy(params)
        best_full_err = float("inf")
        previous_round_state: tuple[tuple[tuple[str, float], ...], float] | None = None
        fallback_search_active = False
        if bool(params.get("ac08_small_variant_mode", False)):
            logs.append(
                "small_variant_mode_active: "
                f"reason={params.get('ac08_small_variant_reason', 'unknown')}, "
                f"min_dim={float(params.get('ac08_small_variant_min_dim', 0.0)):.3f}, "
                f"mask_dilate_px={int(params.get('validation_mask_dilate_px', 0) or 0)}, "
                f"text_mode={params.get('text_mode', '')}, "
                f"arm_min_ratio={float(params.get('arm_len_min_ratio', 0.0)):.3f}, "
                f"stem_min_ratio={float(params.get('stem_len_min_ratio', 0.0)):.3f}"
            )

        def _stagnationFingerprint(current_params: dict) -> tuple[tuple[str, float], ...]:
            tracked_keys = (
                "cx",
                "cy",
                "r",
                "arm_len",
                "stem_width",
                "arm_stroke",
                "text_scale",
                "co2_font_scale",
                "voc_scale",
            )
            fingerprint: list[tuple[str, float]] = []
            for key in tracked_keys:
                value = current_params.get(key)
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    continue
                fingerprint.append((key, round(numeric_value, 4)))
            return tuple(fingerprint)

        for round_idx in range(max_rounds):
            logs.append(f"Runde {round_idx + 1}: elementweise Validierung gestartet")
            full_svg = Action.generate_badge_svg(w, h, params)
            full_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(full_svg, w, h))
            if full_render is None:
                logs.append("Abbruch: SVG konnte nicht gerendert werden")
                break

            if debug_out_dir:
                full_diff = Action.create_diff_image(img_orig, full_render)
                cv2.imwrite(os.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_full_diff.png"), full_diff)

            round_changed = False
            for element in elements:
                elem_svg = Action.generate_badge_svg(w, h, Action._elementOnlyParams(params, element))
                elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
                if elem_render is None:
                    logs.append(f"{element}: Element-SVG konnte nicht gerendert werden")
                    continue

                mask_orig = Action.extract_badge_element_mask(img_orig, params, element)
                mask_svg = Action.extract_badge_element_mask(elem_render, params, element)
                if mask_orig is None or mask_svg is None:
                    logs.append(f"{element}: Element konnte nicht extrahiert werden")
                    continue

                if debug_out_dir:
                    elem_focus_mask = Action._elementRegionMask(h, w, params, element)
                    elem_diff = Action.create_diff_image(img_orig, elem_render, elem_focus_mask)
                    cv2.imwrite(
                        os.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_{element}_diff.png"),
                        elem_diff,
                    )

                elem_err = Action._element_match_error(img_orig, elem_render, params, element, mask_orig=mask_orig, mask_svg=mask_svg)
                logs.append(f"{element}: Fehler={elem_err:.3f}")

                if element == "stem" and params.get("stem_enabled"):
                    changed, refine_log = Action._refineStemGeometryFromMasks(params, mask_orig, mask_svg, w)
                    if refine_log:
                        logs.append(refine_log)
                    if changed:
                        round_changed = True
                        logs.append("stem: Geometrie nach Elementabgleich aktualisiert")

                width_changed = Action._optimize_element_width_bracket(img_orig, params, element, logs)
                if width_changed:
                    round_changed = True

                extent_changed = Action._optimize_element_extent_bracket(img_orig, params, element, logs)
                if extent_changed:
                    round_changed = True

                circle_geometry_penalty_active = apply_circle_geometry_penalty and not fallback_search_active
                if element == "circle" and circle_geometry_penalty_active:
                    center_changed = Action._optimize_circle_center_bracket(img_orig, params, logs)
                    if center_changed:
                        round_changed = True
                    radius_changed = Action._optimize_circle_radius_bracket(img_orig, params, logs)
                    if radius_changed:
                        round_changed = True

                # Color fitting is intentionally deferred to the end so
                # geometry convergence is not biased by temporary palette noise.

            global_search_changed = Action._optimize_global_parameter_vector_sampling(
                img_orig,
                params,
                logs,
            )
            if global_search_changed:
                round_changed = True

            full_svg = Action.generate_badge_svg(w, h, params)
            full_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(full_svg, w, h))
            full_err = Action.calculate_error(img_orig, full_render)
            logs.append(f"Runde {round_idx + 1}: Gesamtfehler={full_err:.3f}")
            if math.isfinite(full_err) and full_err < best_full_err:
                best_full_err = full_err
                best_params = copy.deepcopy(params)

            current_round_state = (_stagnationFingerprint(params), round(float(full_err), 6))
            if previous_round_state is not None:
                same_fingerprint = current_round_state[0] == previous_round_state[0]
                nearly_same_error = abs(current_round_state[1] - previous_round_state[1]) <= 1e-6
                if same_fingerprint and nearly_same_error:
                    logs.append(
                        "stagnation_detected: identischer Parameter-Fingerprint und praktisch unveränderter Gesamtfehler"
                    )
                    adaptive_unlock_applied = Action._activateAc08AdaptiveLocks(
                        params,
                        logs,
                        full_err=full_err,
                        reason="identical_fingerprint",
                    )
                    if adaptive_unlock_applied:
                        previous_round_state = None
                        fallback_search_active = True
                        if round_idx + 1 < max_rounds:
                            logs.append(
                                "switch_to_fallback_search: adaptive family-unlocks aktiviert und Circle-Geometry-Penalty deaktiviert"
                            )
                            continue
                    if not fallback_search_active and round_idx + 1 < max_rounds:
                        Action._releaseAc08AdaptiveLocks(
                            params,
                            logs,
                            reason="stagnation_same_fingerprint",
                            current_error=full_err,
                        )
                        fallback_search_active = True
                        logs.append(
                            "switch_to_fallback_search: deaktiviere Circle-Geometry-Penalty für eine letzte Ausweichrunde"
                        )
                        previous_round_state = current_round_state
                        continue
                    logs.append("stopped_due_to_stagnation: Validierung vorzeitig beendet")
                    break
            previous_round_state = current_round_state

            if full_err <= 8.0:
                if stop_when_error_below_threshold:
                    logs.append("Gesamtfehler unter Schwellwert, Validierung beendet")
                    break
                logs.append("Gesamtfehler unter Schwellwert, Suche nach besserem Optimum wird fortgesetzt")
            elif round_idx >= 1:
                Action._releaseAc08AdaptiveLocks(
                    params,
                    logs,
                    reason="high_residual_error",
                    current_error=full_err,
                )

            if round_idx + 1 >= max_rounds:
                break

            if not round_changed:
                adaptive_unlock_applied = Action._activateAc08AdaptiveLocks(
                    params,
                    logs,
                    full_err=full_err,
                    reason="no_geometry_movement",
                )
                if adaptive_unlock_applied:
                    previous_round_state = None
                    fallback_search_active = True
                    if round_idx + 1 < max_rounds:
                        logs.append(
                            "switch_to_fallback_search: adaptive family-unlocks aktiviert und Circle-Geometry-Penalty deaktiviert"
                        )
                        continue
                if not fallback_search_active and round_idx + 1 < max_rounds:
                    Action._release_ac08_adaptive_locks(
                        params,
                        logs,
                        reason="stagnation_no_geometry_change",
                        current_error=full_err,
                    )
                    fallback_search_active = True
                    logs.append(
                        "stagnation_detected: keine relevante Geometrieänderung in der letzten Validierungsrunde"
                    )
                    logs.append(
                        "switch_to_fallback_search: deaktiviere Circle-Geometry-Penalty für eine letzte Ausweichrunde"
                    )
                    continue
                logs.append("stopped_due_to_stagnation: keine weitere Parameterbewegung erkennbar")
                break

        if math.isfinite(best_full_err):
            params.clear()
            params.update(best_params)

        for element in elements:
            if element == "text" and not params.get("draw_text", True):
                continue
            mask_orig = Action.extract_badge_element_mask(img_orig, params, element)
            if mask_orig is None:
                continue
            color_changed = Action._optimize_element_color_bracket(img_orig, params, element, mask_orig, logs)
            if color_changed:
                logs.append(f"{element}: Farboptimierung in Abschlussphase angewendet")

        params.update(Action._apply_canonical_badge_colors(params))

        return logs


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
    if not os.path.exists(log_path):
        return {}
    details: dict[str, str] = {}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or ": " in line.split("=", 1)[0]:
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                details[key] = value
    except OSError:
        return {}
    return details


def _writeBatchFailureSummary(reports_out_dir: str, failures: list[dict[str, str]]) -> None:
    summary_path = os.path.join(reports_out_dir, "batch_failure_summary.csv")
    with open(summary_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["filename", "status", "reason", "details", "log_file"])
        for failure in failures:
            writer.writerow([
                failure.get("filename", ""),
                failure.get("status", ""),
                failure.get("reason", ""),
                failure.get("details", ""),
                failure.get("log_file", ""),
            ])



def _collectDescriptionFragments(raw_desc: dict[str, str], base_name: str, img_filename: str) -> list[dict[str, str]]:
    """Return the ordered description fragments consulted for one variant lookup."""
    variant_name = os.path.splitext(img_filename)[0]
    canonical_base = getBaseNameFromFile(base_name).upper()
    canonical_variant = getBaseNameFromFile(variant_name).upper()

    lookup_keys = [
        ("base_name", str(base_name)),
        ("variant_name", str(variant_name)),
        ("canonical_base", canonical_base),
        ("canonical_variant", canonical_variant),
    ]
    fragments: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source, key in lookup_keys:
        normalized_key = str(key or "").strip()
        if not normalized_key:
            continue
        marker = (source, normalized_key)
        if marker in seen:
            continue
        seen.add(marker)
        value = str(raw_desc.get(normalized_key, "") or "").strip()
        if not value:
            continue
        fragments.append({"source": source, "key": normalized_key, "text": value})
    return fragments


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
    reports_path = Path(_reportsOutputDir(output_root)) / "Iteration_Log.csv"
    svg_out_dir = Path(_convertedSvgOutputDir(output_root))
    if not reports_path.exists() or not svg_out_dir.exists():
        return []

    rows: list[dict[str, object]] = []
    try:
        with reports_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for raw_row in reader:
                filename = str(raw_row.get("Dateiname", "")).strip()
                if not filename:
                    continue

                variant = os.path.splitext(filename)[0].upper()
                svg_path = svg_out_dir / f"{variant}.svg"
                if not svg_path.exists():
                    continue

                geometry = _readSvgGeometry(str(svg_path))
                if geometry is None:
                    continue
                w, h, params = geometry
                base = getBaseNameFromFile(variant).upper()
                if _isSemanticTemplateVariant(base, params):
                    params["mode"] = "semantic_badge"

                error_per_pixel_raw = str(raw_row.get("FehlerProPixel", "")).strip().replace(",", ".")
                diff_score_raw = str(raw_row.get("Diff-Score", "")).strip().replace(",", ".")
                best_iter_raw = str(raw_row.get("Beste Iteration", "")).strip()
                image_path = Path(folder_path) / filename
                if image_path.exists():
                    try:
                        width, height = _sniffRasterSize(image_path)
                        w = int(width)
                        h = int(height)
                    except Exception:
                        pass

                try:
                    error_per_pixel = float(error_per_pixel_raw)
                except ValueError:
                    error_per_pixel = float("inf")
                try:
                    best_error = float(diff_score_raw)
                except ValueError:
                    best_error = float("inf")
                try:
                    best_iter = int(best_iter_raw)
                except ValueError:
                    best_iter = 0

                rows.append(
                    {
                        "filename": filename,
                        "params": params,
                        "best_iter": best_iter,
                        "best_error": best_error,
                        "error_per_pixel": error_per_pixel,
                        "w": int(w),
                        "h": int(h),
                        "base": base,
                        "variant": variant,
                    }
                )
    except OSError:
        return []

    return [
        row
        for row in rows
        if math.isfinite(float(row.get("error_per_pixel", float("inf"))))
    ]


def _sniffRasterSize(path: str | Path) -> tuple[int, int]:
    file_path = Path(path)
    with file_path.open("rb") as fh:
        header = fh.read(32)

    if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
        return struct.unpack(">II", header[16:24])

    if header[:6] in {b"GIF87a", b"GIF89a"} and len(header) >= 10:
        return struct.unpack("<HH", header[6:10])

    if header.startswith(b"BM"):
        with file_path.open("rb") as fh:
            fh.seek(18)
            dib = fh.read(8)
        if len(dib) == 8:
            width, height = struct.unpack("<ii", dib)
            return abs(int(width)), abs(int(height))

    if header.startswith(b"\xff\xd8"):
        with file_path.open("rb") as fh:
            fh.seek(2)
            while True:
                marker_prefix = fh.read(1)
                if not marker_prefix:
                    break
                if marker_prefix != b"\xff":
                    continue
                marker = fh.read(1)
                while marker == b"\xff":
                    marker = fh.read(1)
                if marker in {b"\xd8", b"\xd9"}:
                    continue
                size_bytes = fh.read(2)
                if len(size_bytes) != 2:
                    break
                segment_size = struct.unpack(">H", size_bytes)[0]
                if marker in {
                    b"\xc0", b"\xc1", b"\xc2", b"\xc3",
                    b"\xc5", b"\xc6", b"\xc7",
                    b"\xc9", b"\xca", b"\xcb",
                    b"\xcd", b"\xce", b"\xcf",
                }:
                    payload = fh.read(5)
                    if len(payload) != 5:
                        break
                    height, width = struct.unpack(">HH", payload[1:5])
                    return int(width), int(height)
                fh.seek(max(0, segment_size - 2), os.SEEK_CUR)

    raise ValueError(f"Unsupported or unreadable raster image: {file_path}")


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
    if not os.path.exists(svg_path):
        return None

    text = open(svg_path, "r", encoding="utf-8").read()

    svg_match = re.search(r"<svg[^>]*viewBox=\"0 0 (\d+) (\d+)\"", text)
    if not svg_match:
        return None
    w = int(svg_match.group(1))
    h = int(svg_match.group(2))

    def _grayFromHex(color: str, fallback: int) -> int:
        m = re.match(r"#([0-9a-fA-F]{6})", color.strip())
        if not m:
            return fallback
        hex_value = m.group(1)
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
        return int(round((r + g + b) / 3.0))

    params: dict[str, float | bool | int | str] = {
        "fill_gray": 220,
        "stroke_gray": 152,
        "text_gray": 98,
        "draw_text": False,
        "text_mode": "path",
        "circle_enabled": False,
        "stem_enabled": False,
        "arm_enabled": False,
    }

    circle_match = re.search(
        r"<circle[^>]*cx=\"([0-9.]+)\"[^>]*cy=\"([0-9.]+)\"[^>]*r=\"([0-9.]+)\"[^>]*stroke-width=\"([0-9.]+)\"",
        text,
    )
    if circle_match:
        params["circle_enabled"] = True
        params["cx"] = float(circle_match.group(1))
        params["cy"] = float(circle_match.group(2))
        params["r"] = float(circle_match.group(3))
        params["stroke_circle"] = float(circle_match.group(4))
        circle_tag_match = re.search(r"(<circle[^>]*>)", text)
        if circle_tag_match:
            circle_tag = circle_tag_match.group(1)
            fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', circle_tag)
            stroke_match = re.search(r'stroke="(#[0-9a-fA-F]{6})"', circle_tag)
            if fill_match:
                params["fill_gray"] = _grayFromHex(fill_match.group(1), int(params["fill_gray"]))
            if stroke_match:
                params["stroke_gray"] = _grayFromHex(stroke_match.group(1), int(params["stroke_gray"]))

    rect_match = re.search(
        r"<rect[^>]*x=\"([0-9.]+)\"[^>]*y=\"([0-9.]+)\"[^>]*width=\"([0-9.]+)\"[^>]*height=\"([0-9.]+)\"",
        text,
    )
    if rect_match:
        x = float(rect_match.group(1))
        y = float(rect_match.group(2))
        width = float(rect_match.group(3))
        height = float(rect_match.group(4))
        params["stem_enabled"] = True
        params["stem_x"] = x
        params["stem_width"] = width
        params["stem_top"] = y
        params["stem_bottom"] = y + height
        rect_tag_match = re.search(r"(<rect[^>]*>)", text)
        if rect_tag_match:
            rect_fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', rect_tag_match.group(1))
            if rect_fill_match:
                params["stem_gray"] = _grayFromHex(rect_fill_match.group(1), int(params["stroke_gray"]))
            else:
                params["stem_gray"] = int(params["stroke_gray"])
        else:
            params["stem_gray"] = int(params["stroke_gray"])

    line_match = re.search(
        r"<line[^>]*x1=\"([0-9.]+)\"[^>]*y1=\"([0-9.]+)\"[^>]*x2=\"([0-9.]+)\"[^>]*y2=\"([0-9.]+)\"[^>]*stroke-width=\"([0-9.]+)\"",
        text,
    )
    if line_match:
        params["arm_enabled"] = True
        params["arm_x1"] = float(line_match.group(1))
        params["arm_y1"] = float(line_match.group(2))
        params["arm_x2"] = float(line_match.group(3))
        params["arm_y2"] = float(line_match.group(4))
        params["arm_stroke"] = float(line_match.group(5))

    text_matches = re.findall(r"(<text[^>]*>)([^<]*)</text>", text)
    if text_matches:
        for text_tag, _text_content in text_matches:
            fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', text_tag)
            if fill_match:
                params["text_gray"] = _grayFromHex(fill_match.group(1), int(params["text_gray"]))
                break

        text_tokens = [content.strip().upper() for _tag, content in text_matches if content and content.strip()]
        normalized_tokens = [token.replace("₂", "2").replace("^", "").replace("_", "") for token in text_tokens]
        merged_text = "".join(normalized_tokens)

        if any(token == "VOC" for token in normalized_tokens):
            params["draw_text"] = True
            params["text_mode"] = "voc"
        elif merged_text == "CO2" or any(token == "CO2" for token in normalized_tokens):
            # Support both single-node CO₂ labels (<text>CO2</text>, <text>CO₂</text>)
            # and split-node output (<text>CO</text><text>2</text>).
            params["draw_text"] = True
            params["text_mode"] = "co2"

    text_path_match = re.search(r"(<path[^>]*>)", text)
    if text_path_match:
        path_tag = text_path_match.group(1)
        fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', path_tag)
        params["draw_text"] = True
        if fill_match:
            params["text_gray"] = _grayFromHex(fill_match.group(1), int(params["text_gray"]))
        if Action.T_PATH_D in path_tag:
            params["text_mode"] = "path_t"
        else:
            params["text_mode"] = "path"

    if params.get("draw_text") and params.get("text_mode") in {"path", "path_t"} and (
        "tx" not in params or "ty" not in params or "s" not in params
    ):
        # Fallback for older path-glyph SVGs where we only need compositing geometry
        # during harmonization. Keep native <text>-based modes (CO₂/VOC) intact.
        params["draw_text"] = False

    return w, h, params


def _normalizedGeometrySignature(w: int, h: int, params: dict) -> dict[str, float]:
    sig: dict[str, float] = {}
    scale = max(1.0, float(min(w, h)))

    if params.get("circle_enabled"):
        sig["cx"] = float(params["cx"]) / max(1.0, float(w))
        sig["cy"] = float(params["cy"]) / max(1.0, float(h))
        sig["r"] = float(params["r"]) / scale
        sig["stroke_circle"] = float(params["stroke_circle"]) / scale

    if params.get("stem_enabled"):
        sig["stem_x"] = float(params["stem_x"]) / max(1.0, float(w))
        sig["stem_width"] = float(params["stem_width"]) / max(1.0, float(w))
        sig["stem_top"] = float(params["stem_top"]) / max(1.0, float(h))
        sig["stem_bottom"] = float(params["stem_bottom"]) / max(1.0, float(h))

    if params.get("arm_enabled"):
        sig["arm_x1"] = float(params["arm_x1"]) / max(1.0, float(w))
        sig["arm_y1"] = float(params["arm_y1"]) / max(1.0, float(h))
        sig["arm_x2"] = float(params["arm_x2"]) / max(1.0, float(w))
        sig["arm_y2"] = float(params["arm_y2"]) / max(1.0, float(h))
        sig["arm_stroke"] = float(params["arm_stroke"]) / scale

    return sig


def _maxSignatureDelta(sig_a: dict[str, float], sig_b: dict[str, float]) -> float:
    keys = sorted(set(sig_a.keys()).intersection(sig_b.keys()))
    if not keys:
        return 1.0
    return max(abs(sig_a[k] - sig_b[k]) for k in keys)


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
    """Write a reproducible manifest for the fixed AC08 regression subset."""
    if sorted(selected_variants) != sorted(AC08_REGRESSION_VARIANTS):
        return

    csv_manifest_path = os.path.join(reports_out_dir, "ac08_regression_set.csv")
    with open(csv_manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["set", "variant", "focus", "reason"])
        for case in AC08_REGRESSION_CASES:
            variant = str(case["variant"])
            focus = str(case["focus"])
            reason = str(case["reason"])
            if variant == "AC0811_L" and focus == "stable_good":
                reason = "Known regression-safe good conversion anchor"
            writer.writerow([AC08_REGRESSION_SET_NAME, variant, focus, reason])

    summary_lines = [
        f"set={AC08_REGRESSION_SET_NAME}",
        f"images_total={len(AC08_REGRESSION_CASES)}",
        f"iterations={int(iterations)}",
        f"folder_path={folder_path}",
        f"csv_path={csv_path}",
        "expected_reports=Iteration_Log.csv,quality_tercile_passes.csv,pixel_delta2_ranking.csv,pixel_delta2_summary.txt,ac08_weak_family_status.csv,ac08_weak_family_status.txt,ac08_success_metrics.csv,ac08_success_criteria.txt",
        "expected_logs=variant_harmonization.log,shape_catalog.csv",
        (
            "recommended_command=python -m src.imageCompositeConverter "
            f"{folder_path} --csv-path {csv_path} --ac08-regression-set {int(iterations)}"
        ),
    ]
    with open(os.path.join(reports_out_dir, "ac08_regression_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")


def _summarizePreviousGoodAc08Variants(reports_out_dir: str) -> dict[str, object]:
    """Summarize whether previously good AC08 variants stayed semantic_ok in the latest run."""
    preserved: list[str] = []
    regressed: list[str] = []
    missing: list[str] = []

    for variant in AC08_PREVIOUSLY_GOOD_VARIANTS:
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")
        if not os.path.exists(log_path):
            missing.append(variant)
            continue
        with open(log_path, "r", encoding="utf-8") as f:
            log_text = f.read()
        if "status=semantic_ok" in log_text and "status=semantic_mismatch" not in log_text:
            preserved.append(variant)
        else:
            regressed.append(variant)

    return {
        "expected": list(AC08_PREVIOUSLY_GOOD_VARIANTS),
        "preserved": preserved,
        "regressed": regressed,
        "missing": missing,
    }


def _writeAc08SuccessCriteriaReport(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
) -> dict[str, object] | None:
    """Persist the written AC08 success criteria and the current measured status."""
    if sorted(selected_variants) != sorted(AC08_REGRESSION_VARIANTS):
        return None

    expected_variants = sorted(selected_variants)
    iteration_rows: list[dict[str, str]] = []
    iteration_log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    if os.path.exists(iteration_log_path):
        with open(iteration_log_path, "r", encoding="utf-8-sig", newline="") as f:
            iteration_rows = list(csv.DictReader(f, delimiter=";"))

    quality_rows: list[dict[str, str]] = []
    quality_path = os.path.join(reports_out_dir, "quality_tercile_passes.csv")
    if os.path.exists(quality_path):
        with open(quality_path, "r", encoding="utf-8", newline="") as f:
            quality_rows = list(csv.DictReader(f, delimiter=";"))

    converted_variants = {
        os.path.splitext(str(row.get("Dateiname", "")).strip())[0].upper()
        for row in iteration_rows
        if str(row.get("Dateiname", "")).strip()
    }
    missing_variants = [variant for variant in expected_variants if variant not in converted_variants]

    improved_error_count = 0
    improved_mean_delta2_count = 0
    rejected_regression_count = 0
    accepted_regression_count = 0
    for row in quality_rows:
        decision = str(row.get("decision", "")).strip()
        old_error = float(row.get("old_error_per_pixel", "inf"))
        new_error = float(row.get("new_error_per_pixel", "inf"))
        old_delta2 = float(row.get("old_mean_delta2", "inf"))
        new_delta2 = float(row.get("new_mean_delta2", "inf"))
        if math.isfinite(old_error) and math.isfinite(new_error) and new_error + 1e-9 < old_error:
            improved_error_count += 1
        if math.isfinite(old_delta2) and math.isfinite(new_delta2) and new_delta2 + 1e-6 < old_delta2:
            improved_mean_delta2_count += 1
        if decision == "rejected_regression":
            rejected_regression_count += 1
        if decision == "accepted_regression":
            accepted_regression_count += 1

    semantic_mismatch_count = 0
    render_failure_count = 0
    validation_round_counts: list[int] = []
    for variant in expected_variants:
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")
        if not os.path.exists(log_path):
            continue
        with open(log_path, "r", encoding="utf-8") as f:
            log_text = f.read()
        if "status=semantic_mismatch" in log_text:
            semantic_mismatch_count += 1
        if "konnte nicht gerendert werden" in log_text or "Abbruch: SVG konnte nicht gerendert werden" in log_text:
            render_failure_count += 1
        rounds = len(re.findall(r"^Runde\s+\d+: elementweise Validierung gestartet$", log_text, flags=re.MULTILINE))
        if rounds > 0:
            validation_round_counts.append(rounds)

    batch_abort_count = len(missing_variants) + render_failure_count
    mean_validation_rounds = (
        sum(validation_round_counts) / float(len(validation_round_counts))
        if validation_round_counts
        else 0.0
    )

    previous_good = _summarizePreviousGoodAc08Variants(reports_out_dir)
    previous_good_preserved_count = len(previous_good["preserved"])
    previous_good_regressed_count = len(previous_good["regressed"])
    previous_good_missing_count = len(previous_good["missing"])

    regression_set_improved = improved_error_count > 0 or improved_mean_delta2_count > 0
    no_new_batch_aborts = batch_abort_count == 0
    no_accepted_regressions = accepted_regression_count == 0
    validation_rounds_recorded = mean_validation_rounds > 0.0
    stable_families_not_worse = (
        no_accepted_regressions
        and previous_good_regressed_count == 0
        and previous_good_missing_count == 0
    )
    overall_success = (
        no_new_batch_aborts
        and no_accepted_regressions
        and validation_rounds_recorded
        and regression_set_improved
        and stable_families_not_worse
    )

    metrics_path = os.path.join(reports_out_dir, "ac08_success_metrics.csv")
    with open(metrics_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["metric", "value"])
        writer.writerow(["regression_set", AC08_REGRESSION_SET_NAME])
        writer.writerow(["images_expected", len(expected_variants)])
        writer.writerow(["images_converted", len(converted_variants)])
        writer.writerow(["images_missing", len(missing_variants)])
        writer.writerow(["improved_error_per_pixel_count", improved_error_count])
        writer.writerow(["improved_mean_delta2_count", improved_mean_delta2_count])
        writer.writerow(["semantic_mismatch_count", semantic_mismatch_count])
        writer.writerow(["batch_abort_or_render_failure_count", batch_abort_count])
        writer.writerow(["rejected_regression_count", rejected_regression_count])
        writer.writerow(["accepted_regression_count", accepted_regression_count])
        writer.writerow(["previous_good_expected", len(previous_good["expected"])])
        writer.writerow(["previous_good_preserved_count", previous_good_preserved_count])
        writer.writerow(["previous_good_regressed_count", previous_good_regressed_count])
        writer.writerow(["previous_good_missing_count", previous_good_missing_count])
        writer.writerow(["mean_validation_rounds_per_file", f"{mean_validation_rounds:.3f}"])
        writer.writerow(["criterion_no_new_batch_aborts", int(no_new_batch_aborts)])
        writer.writerow(["criterion_no_accepted_regressions", int(no_accepted_regressions)])
        writer.writerow(["criterion_validation_rounds_recorded", int(validation_rounds_recorded)])
        writer.writerow(["criterion_regression_set_improved", int(regression_set_improved)])
        writer.writerow(["criterion_stable_families_not_worse", int(stable_families_not_worse)])
        writer.writerow(["overall_success", int(overall_success)])

    summary_lines = [
        f"set={AC08_REGRESSION_SET_NAME}",
        "goal=Abschluss einer AC08-Maßnahme objektiv bewerten",
        "success_metrics=improved_error_per_pixel_count,improved_mean_delta2_count,semantic_mismatch_count,batch_abort_or_render_failure_count,mean_validation_rounds_per_file",
        (
            "success_definition=no_new_batch_aborts && no_accepted_regressions "
            "&& validation_rounds_recorded && regression_set_improved && stable_families_not_worse"
        ),
        f"images_expected={len(expected_variants)}",
        f"images_converted={len(converted_variants)}",
        f"images_missing={len(missing_variants)}",
        f"improved_error_per_pixel_count={improved_error_count}",
        f"improved_mean_delta2_count={improved_mean_delta2_count}",
        f"semantic_mismatch_count={semantic_mismatch_count}",
        f"batch_abort_or_render_failure_count={batch_abort_count}",
        f"rejected_regression_count={rejected_regression_count}",
        f"accepted_regression_count={accepted_regression_count}",
        f"previous_good_expected={len(previous_good['expected'])}",
        f"previous_good_preserved_count={previous_good_preserved_count}",
        f"previous_good_regressed_count={previous_good_regressed_count}",
        f"previous_good_missing_count={previous_good_missing_count}",
        f"mean_validation_rounds_per_file={mean_validation_rounds:.3f}",
        f"criterion_no_new_batch_aborts={int(no_new_batch_aborts)}",
        f"criterion_no_accepted_regressions={int(no_accepted_regressions)}",
        f"criterion_validation_rounds_recorded={int(validation_rounds_recorded)}",
        f"criterion_regression_set_improved={int(regression_set_improved)}",
        f"criterion_stable_families_not_worse={int(stable_families_not_worse)}",
        f"overall_success={int(overall_success)}",
    ]
    if missing_variants:
        summary_lines.append("missing_variants=" + ",".join(missing_variants))
    if previous_good["preserved"]:
        summary_lines.append("previous_good_preserved=" + ",".join(previous_good["preserved"]))
    if previous_good["regressed"]:
        summary_lines.append("previous_good_regressed=" + ",".join(previous_good["regressed"]))
    if previous_good["missing"]:
        summary_lines.append("previous_good_missing=" + ",".join(previous_good["missing"]))

    with open(os.path.join(reports_out_dir, "ac08_success_criteria.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")

    return {
        "overall_success": overall_success,
        "criterion_no_new_batch_aborts": no_new_batch_aborts,
        "criterion_no_accepted_regressions": no_accepted_regressions,
        "criterion_validation_rounds_recorded": validation_rounds_recorded,
        "criterion_regression_set_improved": regression_set_improved,
        "criterion_stable_families_not_worse": stable_families_not_worse,
        "mean_validation_rounds_per_file": mean_validation_rounds,
    }


def _writeAc08WeakFamilyStatusReport(
    reports_out_dir: str,
    *,
    selected_variants: list[str],
    ranking_threshold: float = 18.0,
) -> None:
    """Summarize currently weak AC08 families and the mitigation status implemented in code."""
    normalized_variants = sorted({str(variant).strip().upper() for variant in selected_variants if str(variant).strip()})
    if not normalized_variants or any(not variant.startswith("AC08") for variant in normalized_variants):
        return

    ranking_rows: list[dict[str, str]] = []
    ranking_path = os.path.join(reports_out_dir, "pixel_delta2_ranking.csv")
    if os.path.exists(ranking_path):
        with open(ranking_path, "r", encoding="utf-8", newline="") as f:
            ranking_rows = list(csv.DictReader(f, delimiter=";"))

    ranking_by_variant: dict[str, dict[str, str]] = {}
    for row in ranking_rows:
        image_name = str(row.get("image", "")).strip()
        if not image_name:
            continue
        variant = os.path.splitext(image_name)[0].upper()
        ranking_by_variant[variant] = row

    focus_by_variant = {case["variant"].upper(): case["focus"] for case in AC08_REGRESSION_CASES}
    weak_rows: list[dict[str, str]] = []
    for variant in normalized_variants:
        base = variant.split("_", 1)[0]
        ranking_row = ranking_by_variant.get(variant, {})
        mean_delta2_raw = str(ranking_row.get("mean_delta2", "")).strip()
        try:
            mean_delta2 = float(mean_delta2_raw) if mean_delta2_raw else float("nan")
        except ValueError:
            mean_delta2 = float("nan")
        is_weak = (not math.isfinite(mean_delta2)) or mean_delta2 > ranking_threshold
        if not is_weak:
            continue

        mitigation = AC08_MITIGATION_STATUS.get(base, {})
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")
        log_text = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                log_text = f.read()

        active_markers: list[str] = []
        if "adaptive_unlock_applied" in log_text:
            active_markers.append("adaptive_unlock_applied")
        if "small_variant_mode_active" in log_text:
            active_markers.append("small_variant_mode_active")
        if "semantic_audit_status=" in log_text:
            active_markers.append("semantic_audit_logged")
        if "stopped_due_to_stagnation" in log_text:
            active_markers.append("stagnation_guard_triggered")

        weak_rows.append({
            "variant": variant,
            "base_family": base,
            "focus": focus_by_variant.get(variant, "review"),
            "mean_delta2": "nan" if not math.isfinite(mean_delta2) else f"{mean_delta2:.6f}",
            "risk": str(mitigation.get("risk", "unknown")),
            "family_group": str(mitigation.get("family", "unknown")),
            "implemented_mitigations": str(mitigation.get("implemented", "manual_review")),
            "active_log_markers": ",".join(active_markers) if active_markers else "none_observed",
            "status": str(mitigation.get("status", "No family-specific mitigation documented yet; inspect logs and ranking manually.")),
        })

    weak_rows.sort(
        key=lambda row: (
            -float("inf") if row["mean_delta2"] == "nan" else float(row["mean_delta2"]),
            row["variant"],
        ),
        reverse=True,
    )

    csv_path = os.path.join(reports_out_dir, "ac08_weak_family_status.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "variant",
            "base_family",
            "focus",
            "mean_delta2",
            "risk",
            "family_group",
            "implemented_mitigations",
            "active_log_markers",
            "status",
        ])
        for row in weak_rows:
            writer.writerow([
                row["variant"],
                row["base_family"],
                row["focus"],
                row["mean_delta2"],
                row["risk"],
                row["family_group"],
                row["implemented_mitigations"],
                row["active_log_markers"],
                row["status"],
            ])

    summary_lines = [
        f"ranking_threshold_mean_delta2={ranking_threshold:.3f}",
        f"weak_variants={len(weak_rows)}",
        "goal=Verbleibende AC08-Schwachfamilien und ihren aktuellen Mitigation-Status dokumentieren",
    ]
    if weak_rows:
        summary_lines.append("variants=" + ",".join(row["variant"] for row in weak_rows))
        for row in weak_rows:
            summary_lines.append(
                f"{row['variant']}: mean_delta2={row['mean_delta2']}; risk={row['risk']}; markers={row['active_log_markers']}; status={row['status']}"
            )
    else:
        summary_lines.append("variants=none")
        summary_lines.append("All selected AC08 variants are currently at or below the weak-family threshold.")

    with open(os.path.join(reports_out_dir, "ac08_weak_family_status.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")


def _writePixelDelta2Ranking(folder_path: str, svg_out_dir: str, reports_out_dir: str, threshold: float = 18.0) -> None:
    ranking: list[dict[str, float | str]] = []
    for svg_name in sorted(f for f in os.listdir(svg_out_dir) if f.lower().endswith(".svg")):
        stem = os.path.splitext(svg_name)[0]
        orig_path = None
        for ext in (".jpg", ".png", ".bmp"):
            candidate = os.path.join(folder_path, f"{stem}{ext}")
            if os.path.exists(candidate):
                orig_path = candidate
                break
        if orig_path is None:
            continue

        img_orig = cv2.imread(orig_path)
        if img_orig is None:
            continue

        with open(os.path.join(svg_out_dir, svg_name), "r", encoding="utf-8") as f:
            svg_content = f.read()

        h, w = img_orig.shape[:2]
        rendered = Action.render_svg_to_numpy(svg_content, w, h)
        if rendered is None:
            continue

        mean_delta2, std_delta2 = Action.calculateDelta2Stats(img_orig, rendered)
        ranking.append(
            {
                "image": os.path.basename(orig_path),
                "mean_delta2": float(mean_delta2),
                "std_delta2": float(std_delta2),
            }
        )

    ranking.sort(key=lambda row: float(row["mean_delta2"]), reverse=True)
    csv_path = os.path.join(reports_out_dir, "pixel_delta2_ranking.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["image", "mean_delta2", "std_delta2"])
        for row in ranking:
            writer.writerow([row["image"], f"{float(row['mean_delta2']):.6f}", f"{float(row['std_delta2']):.6f}"])

    valid = [row for row in ranking if math.isfinite(float(row["mean_delta2"]))]
    count_ok = sum(1 for row in valid if float(row["mean_delta2"]) <= threshold)
    summary_lines = [
        f"images_total={len(valid)}",
        f"threshold_mean_delta2={threshold:.3f}",
        f"images_with_mean_delta2_le_threshold={count_ok}",
    ]
    with open(os.path.join(reports_out_dir, "pixel_delta2_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")


def _loadIterationLogRows(reports_out_dir: str) -> dict[str, dict[str, str]]:
    """Load Iteration_Log.csv keyed by uppercase filename stem."""
    path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    if not os.path.exists(path):
        return {}

    rows: dict[str, dict[str, str]] = {}
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            filename = str(row.get('Dateiname', '')).strip()
            if not filename:
                continue
            rows[os.path.splitext(filename)[0].upper()] = dict(row)
    return rows


def _findImagePathByVariant(folder_path: str, variant: str) -> str | None:
    """Return the raster image path for ``variant`` if present."""
    for ext in ('.jpg', '.png', '.bmp', '.gif'):
        candidate = os.path.join(folder_path, f'{variant}{ext}')
        if os.path.exists(candidate):
            return candidate
    return None


def collectSuccessfulConversionQualityMetrics(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> list[dict[str, object]]:
    """Collect quality metrics for variants listed as successful conversions."""
    if cv2 is None or np is None:
        missing = []
        if cv2 is None:
            missing.append('cv2')
        if np is None:
            missing.append('numpy')
        raise RuntimeError('Required image dependencies are missing: ' + ', '.join(missing))

    variants = [str(v).strip().upper() for v in (successful_variants or SUCCESSFUL_CONVERSIONS) if str(v).strip()]
    iteration_rows = _loadIterationLogRows(reports_out_dir)
    metrics: list[dict[str, object]] = []
    seen: set[str] = set()
    for variant in variants:
        if variant in seen:
            continue
        seen.add(variant)
        image_path = _findImagePathByVariant(folder_path, variant)
        svg_path = os.path.join(svg_out_dir, f'{variant}.svg')
        log_path = os.path.join(reports_out_dir, f'{variant}_element_validation.log')

        row: dict[str, object] = {
            'variant': variant,
            'image_found': os.path.exists(image_path) if image_path else False,
            'svg_found': os.path.exists(svg_path),
            'log_found': os.path.exists(log_path),
            'status': '',
            'best_iteration': '',
            'diff_score': float('nan'),
            'error_per_pixel': float('nan'),
            'pixel_count': 0,
            'total_delta2': float('nan'),
            'mean_delta2': float('nan'),
            'std_delta2': float('nan'),
        }

        details = _readValidationLogDetails(log_path) if os.path.exists(log_path) else {}
        row['status'] = details.get('status', '')

        iteration = iteration_rows.get(variant, {})
        row['best_iteration'] = str(iteration.get('Beste Iteration', '')).strip()
        try:
            row['diff_score'] = float(str(iteration.get('Diff-Score', '')).strip().replace(',', '.'))
        except ValueError:
            row['diff_score'] = float('nan')
        try:
            row['error_per_pixel'] = float(str(iteration.get('FehlerProPixel', '')).strip().replace(',', '.'))
        except ValueError:
            row['error_per_pixel'] = float('nan')

        if not image_path or not os.path.exists(image_path) or not os.path.exists(svg_path):
            metrics.append(row)
            continue

        img_orig = cv2.imread(image_path)
        if img_orig is None:
            metrics.append(row)
            continue
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        rendered = Action.render_svg_to_numpy(svg_content, img_orig.shape[1], img_orig.shape[0])
        if rendered is None:
            metrics.append(row)
            continue

        diff = img_orig.astype(np.float32) - rendered.astype(np.float32)
        delta2 = np.sum(diff * diff, axis=2)
        row['pixel_count'] = int(delta2.shape[0] * delta2.shape[1])
        row['total_delta2'] = float(np.sum(delta2))
        row['mean_delta2'] = float(np.mean(delta2))
        row['std_delta2'] = float(np.std(delta2))
        metrics.append(row)

    metrics.sort(key=lambda item: str(item.get('variant', '')))
    return metrics


def _successfulConversionMetricsAvailable(metrics: dict[str, object]) -> bool:
    """Return whether a metrics row contains fresh conversion data worth persisting."""
    status = str(metrics.get('status', '')).strip()
    if status:
        return True

    best_iteration = str(metrics.get('best_iteration', '')).strip()
    if best_iteration:
        return True

    pixel_count = int(metrics.get('pixel_count', 0) or 0)
    if pixel_count > 0:
        return True

    for key in ('diff_score', 'error_per_pixel', 'total_delta2', 'mean_delta2', 'std_delta2'):
        value = float(metrics.get(key, float('nan')))
        if math.isfinite(value):
            return True
    return False


def _parseSuccessfulConversionManifestLine(raw_line: str) -> tuple[str, dict[str, object]]:
    """Parse one successful-conversions manifest line into variant plus metrics."""
    stripped = raw_line.split('#', 1)[0].strip()
    if not stripped:
        return '', {}

    parts = [part.strip() for part in stripped.split(';') if part.strip()]
    if not parts:
        return '', {}

    variant = parts[0].upper()
    metrics: dict[str, object] = {'variant': variant}
    for field in parts[1:]:
        if '=' not in field:
            continue
        key, value = [token.strip() for token in field.split('=', 1)]
        if not key:
            continue
        if key == 'pixel_count':
            with contextlib.suppress(ValueError):
                metrics[key] = int(value)
            continue
        if key in {'diff_score', 'error_per_pixel', 'total_delta2', 'mean_delta2', 'std_delta2'}:
            with contextlib.suppress(ValueError):
                metrics[key] = float(value.replace(',', '.'))
            continue
        metrics[key] = value
    return variant, metrics


def _readSuccessfulConversionManifestMetrics(manifest_path: Path) -> dict[str, dict[str, object]]:
    """Load persisted best-list metrics keyed by variant."""
    if not manifest_path.exists():
        return {}

    rows: dict[str, dict[str, object]] = {}
    for raw_line in manifest_path.read_text(encoding='utf-8').splitlines():
        variant, metrics = _parseSuccessfulConversionManifestLine(raw_line)
        if variant:
            rows[variant] = metrics
    return rows


def _successfulConversionSnapshotDir(reports_out_dir: str) -> Path:
    """Directory used to persist best-of artifacts for successful conversions."""
    return Path(reports_out_dir) / 'successful_conversions_bestlist'


def _successfulConversionSnapshotPaths(reports_out_dir: str, variant: str) -> dict[str, Path]:
    base_dir = _successfulConversionSnapshotDir(reports_out_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return {
        'svg': base_dir / f'{variant}.svg',
        'log': base_dir / f'{variant}_element_validation.log',
        'metrics': base_dir / f'{variant}.json',
    }


def _restoreSuccessfulConversionSnapshot(variant: str, svg_out_dir: str, reports_out_dir: str) -> bool:
    """Restore the previous best conversion for ``variant`` if a snapshot exists."""
    snapshot_paths = _successfulConversionSnapshotPaths(reports_out_dir, variant)
    restored = False

    target_svg = Path(svg_out_dir) / f'{variant}.svg'
    if snapshot_paths['svg'].exists():
        target_svg.parent.mkdir(parents=True, exist_ok=True)
        target_svg.write_text(snapshot_paths['svg'].read_text(encoding='utf-8'), encoding='utf-8')
        restored = True

    target_log = Path(reports_out_dir) / f'{variant}_element_validation.log'
    if snapshot_paths['log'].exists():
        target_log.write_text(snapshot_paths['log'].read_text(encoding='utf-8'), encoding='utf-8')
        restored = True

    return restored


def _storeSuccessfulConversionSnapshot(variant: str, metrics: dict[str, object], svg_out_dir: str, reports_out_dir: str) -> None:
    """Persist the current best conversion artifacts for later rollback/restoration."""
    snapshot_paths = _successfulConversionSnapshotPaths(reports_out_dir, variant)
    target_svg = Path(svg_out_dir) / f'{variant}.svg'
    if target_svg.exists():
        snapshot_paths['svg'].write_text(target_svg.read_text(encoding='utf-8'), encoding='utf-8')

    target_log = Path(reports_out_dir) / f'{variant}_element_validation.log'
    if target_log.exists():
        snapshot_paths['log'].write_text(target_log.read_text(encoding='utf-8'), encoding='utf-8')

    snapshot_paths['metrics'].write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding='utf-8',
    )


def _isSuccessfulConversionCandidateBetter(
    previous_metrics: dict[str, object] | None,
    candidate_metrics: dict[str, object],
) -> bool:
    """Accept a new best-list candidate only when it improves quality."""
    if not _successfulConversionMetricsAvailable(candidate_metrics):
        return False
    if not previous_metrics or not _successfulConversionMetricsAvailable(previous_metrics):
        return True

    previous_status = str(previous_metrics.get('status', '')).strip().lower()
    candidate_status = str(candidate_metrics.get('status', '')).strip().lower()
    if previous_status == 'semantic_ok' and candidate_status != 'semantic_ok':
        return False
    if previous_status != 'semantic_ok' and candidate_status == 'semantic_ok':
        return True

    improved, _decision, _prev_error, _new_error, _prev_delta, _new_delta = _evaluateQualityPassCandidate(
        previous_metrics,
        candidate_metrics,
    )
    return improved


def _mergeSuccessfulConversionMetrics(
    baseline: dict[str, object],
    override: dict[str, object],
) -> dict[str, object]:
    """Merge ``override`` into ``baseline`` while keeping row-level defaults."""
    merged = dict(baseline)
    for key, value in override.items():
        if key == 'variant':
            continue
        merged[key] = value
    merged['variant'] = str(override.get('variant', baseline.get('variant', ''))).strip().upper()
    return merged


def _formatSuccessfulConversionManifestLine(existing_line: str, metrics: dict[str, object]) -> str:
    """Render one enriched successful-conversions manifest line."""
    if not _successfulConversionMetricsAvailable(metrics):
        return existing_line.rstrip('\n')

    variant = str(metrics.get('variant', '')).strip().upper()
    prefix, comment = existing_line, ''
    if '#' in existing_line:
        prefix, comment = existing_line.split('#', 1)
        comment = '#' + comment.rstrip('\n').rstrip('\r').rstrip()
    prefix = prefix.strip()
    if not prefix:
        return existing_line.rstrip('\n')

    fields = [variant]
    status = str(metrics.get('status', '')).strip()
    if status:
        fields.append(f'status={status}')
    best_iteration = str(metrics.get('best_iteration', '')).strip()
    if best_iteration:
        fields.append(f'best_iteration={best_iteration}')
    for key, precision in (
        ('diff_score', 6),
        ('error_per_pixel', 8),
        ('total_delta2', 6),
        ('mean_delta2', 6),
        ('std_delta2', 6),
    ):
        value = float(metrics.get(key, float('nan')))
        if math.isfinite(value):
            fields.append(f'{key}={value:.{precision}f}')
    pixel_count = int(metrics.get('pixel_count', 0) or 0)
    if pixel_count > 0:
        fields.append(f'pixel_count={pixel_count}')

    line = ' ; '.join(fields)
    if comment:
        line += '  ' + comment
    return line


def _latestFailedConversionManifestEntry(reports_out_dir: str) -> dict[str, object] | None:
    """Return the most recent failed conversion as a manifest-like row."""
    summary_path = Path(reports_out_dir) / "batch_failure_summary.csv"
    if not summary_path.exists():
        return None

    latest_row: dict[str, str] | None = None
    try:
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                filename = str(row.get("filename", "")).strip()
                status = str(row.get("status", "")).strip().lower()
                if not filename or status not in {"render_failure", "batch_error", "semantic_mismatch"}:
                    continue
                latest_row = row
    except OSError:
        return None

    if latest_row is None:
        return None

    variant = Path(str(latest_row.get("filename", "")).strip()).stem.upper()
    if not variant:
        return None

    return {
        "variant": variant,
        "status": "failed",
        "failure_reason": str(latest_row.get("reason", "")).strip(),
    }


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
    """Sort successful-conversion rows by converted image name/variant."""
    return sorted(metrics, key=lambda row: str(row.get('variant', '')).upper())


def _writeSuccessfulConversionCsvTable(csv_path: str | os.PathLike[str], metrics: list[dict[str, object]]) -> str:
    """Write the successful-conversions leaderboard as a CSV table."""
    csv_path = os.fspath(csv_path)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([
            'variant', 'status', 'image_found', 'svg_found', 'log_found', 'best_iteration',
            'diff_score', 'error_per_pixel', 'pixel_count', 'total_delta2', 'mean_delta2', 'std_delta2',
        ])
        for row in _sortedSuccessfulConversionMetricsRows(metrics):
            writer.writerow([
                row['variant'],
                row['status'],
                int(bool(row['image_found'])),
                int(bool(row['svg_found'])),
                int(bool(row['log_found'])),
                row['best_iteration'],
                '' if not math.isfinite(float(row['diff_score'])) else f"{float(row['diff_score']):.6f}",
                '' if not math.isfinite(float(row['error_per_pixel'])) else f"{float(row['error_per_pixel']):.8f}",
                int(row['pixel_count']),
                '' if not math.isfinite(float(row['total_delta2'])) else f"{float(row['total_delta2']):.6f}",
                '' if not math.isfinite(float(row['mean_delta2'])) else f"{float(row['mean_delta2']):.6f}",
                '' if not math.isfinite(float(row['std_delta2'])) else f"{float(row['std_delta2']):.6f}",
            ])
    return csv_path


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
