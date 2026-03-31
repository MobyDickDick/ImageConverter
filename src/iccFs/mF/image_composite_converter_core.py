"""Image-to-composite-SVG conversion pipeline.

Ported from the user-provided prototype and exposed as a Python helper module
for direct CLI and module-based execution.
"""

from __future__ import annotations

import argparse
import ast
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

if __package__ in {None, ""}:
    # Allow direct CLI execution via ``python src/image_composite_converter.py``
    # from the repository root without requiring PYTHONPATH to be preset.
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from src.overviewTiles import generateConversionOverviews
from src.imageCompositeConverterRegions import (
    ANNOTATION_COLORS,
    _bbox_to_dict,
    analyzeRangeImpl,
    annotateImageRegionsImpl,
    detectRelevantRegionsImpl,
)
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

_load_successful_conversions = _loadSuccessfulConversions


DEFAULT_CALL_TREE_CSV_PATH = "artifacts/converted_images/reports/call_tree_image_composite_converter.csv"

OPTIONAL_DEPENDENCY_ERRORS: dict[str, str] = {}

SVG_RENDER_SUBPROCESS_ENABLED = os.environ.get("IMAGE_CONVERTER_ISOLATE_SVG_RENDER", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
try:
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = max(
        1.0,
        float(os.environ.get("IMAGE_CONVERTER_ISOLATE_SVG_RENDER_TIMEOUT_SEC", "20").strip() or "20"),
    )
except ValueError:
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = 20.0


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


def detect_relevant_regions(img) -> list[dict[str, object]]:
    return detectRelevantRegionsImpl(img, cv2_module=cv2, np_module=np)


def annotate_image_regions(img, regions: list[dict[str, object]]):
    return annotateImageRegionsImpl(img, regions, cv2_module=cv2)




def _optional_dependency_base_dir() -> Path:
    """Return the repository root used for vendored dependency discovery."""
    return Path(__file__).resolve().parents[2]


def _vendored_site_packages_dirs() -> list[Path]:
    """Return repo-local site-packages directories that may contain bundled deps."""
    base = _optional_dependency_base_dir()
    linux_candidates = [
        base / "vendor" / "linux" / "site-packages",
        base / "vendor" / "linux-py310" / "site-packages",
        base / "vendor" / "linux-py311" / "site-packages",
        base / "vendor" / "linux-py312" / "site-packages",
        base / "vendor" / "linux-py313" / "site-packages",
        base / "vendor" / "linux-py314" / "site-packages",
    ]
    windows_candidates = [
        base / "vendor" / "win" / "site-packages",
        base / "vendor" / "win-py310" / "site-packages",
        base / "vendor" / "win-py311" / "site-packages",
        base / "vendor" / "win-py312" / "site-packages",
        base / "vendor" / "win-py313" / "site-packages",
        base / "vendor" / "win-py314" / "site-packages",
        base / ".venv" / "Lib" / "site-packages",
    ]
    posix_venv_candidates = [
        base / ".venv" / "lib" / "python3.10" / "site-packages",
        base / ".venv" / "lib" / "python3.11" / "site-packages",
        base / ".venv" / "lib" / "python3.12" / "site-packages",
        base / ".venv" / "lib" / "python3.13" / "site-packages",
        base / ".venv" / "lib" / "python3.14" / "site-packages",
    ]
    if os.name == "nt":
        candidates = windows_candidates + linux_candidates + posix_venv_candidates
    else:
        candidates = linux_candidates + posix_venv_candidates + windows_candidates

    seen: set[str] = set()
    existing: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            existing.append(candidate)
    return existing


def _clear_partial_module_import(module_name: str) -> None:
    """Discard partially imported package state before the next fallback attempt."""
    for imported_name in [name for name in list(sys.modules) if name == module_name or name.startswith(f"{module_name}.")]:
        sys.modules.pop(imported_name, None)


def _describe_optional_dependency_error(module_name: str, exc: BaseException, attempted_paths: list[Path]) -> str:
    detail = f"{type(exc).__name__}: {exc}"
    lower = detail.lower()
    if "add_dll_directory" in lower or ".pyd" in lower:
        return (
            f"{detail}. Repo-local Paket gefunden, aber es wirkt wie ein Windows-Build "
            f"und ist unter dieser Linux-Umgebung nicht ladbar"
        )
    if "elf" in lower or "wrong elf class" in lower:
        return f"{detail}. Repo-lokales Binary ist nicht mit dieser Laufzeit kompatibel"
    if attempted_paths:
        joined = ", ".join(str(path) for path in attempted_paths)
        return f"{detail}. Zusätzliche Importpfade geprüft: {joined}"
    return detail


def _load_optional_module(module_name: str):
    """Import optional dependencies, including repo-vendored site-packages."""
    attempted_paths: list[Path] = []
    try:
        return importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
        last_exc: BaseException = exc
        _clear_partial_module_import(module_name)

    for site_packages in _vendored_site_packages_dirs():
        attempted_paths.append(site_packages)
        path_str = str(site_packages)
        added = False
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            added = True
        try:
            return importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
            last_exc = exc
            _clear_partial_module_import(module_name)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(path_str)

    OPTIONAL_DEPENDENCY_ERRORS[module_name] = _describe_optional_dependency_error(module_name, last_exc, attempted_paths)
    return None


def _import_with_vendored_fallback(module_name: str):
    """Import a module, retrying with repo-vendored site-packages on sys.path."""
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        last_exc: BaseException = exc
        _clear_partial_module_import(module_name)

    for site_packages in _vendored_site_packages_dirs():
        path_str = str(site_packages)
        added = False
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            added = True
        try:
            return importlib.import_module(module_name)
        except Exception as exc:
            last_exc = exc
            _clear_partial_module_import(module_name)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(path_str)

    raise last_exc


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
        return Action._clip_scalar(float(value), float(low), float(high))
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

    def to_hex(self) -> str:
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

    def to_svg(self, width: int, height: int, *, clip_to_canvas: bool = True) -> str:
        """Render the ladle as SVG. Handle is drawn first (background), then circle."""
        handle_stroke = max(1.0, float(self.kreis.randbreite))
        cx = float(self.kreis.mittelpunkt.x)
        cy = float(self.kreis.mittelpunkt.y)
        radius = float(self.kreis.radius)
        handle = (
            f'<line x1="{self.griff.anfang.x:.2f}" y1="{self.griff.anfang.y:.2f}" '
            f'x2="{self.griff.ende.x:.2f}" y2="{self.griff.ende.y:.2f}" '
            f'stroke="{self.kreis.rand_farbe.to_hex()}" stroke-width="{handle_stroke:.2f}" stroke-linecap="round"/>'
        )
        circle = (
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{radius:.2f}" '
            f'fill="{self.kreis.hintergrundfarbe.to_hex()}" stroke="{self.kreis.rand_farbe.to_hex()}" '
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


def build_oriented_kelle(
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
    def from_params(params: dict) -> "GlobalParameterVector":
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

    def apply_to_params(self, params: dict) -> dict:
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

def load_grayscale_image(path: Path) -> list[list[int]]:
    image_module = _import_with_vendored_fallback("PIL.Image")
    gray = image_module.open(path).convert("L")
    w, h = gray.size
    px = gray.load()
    return [[int(px[x, y]) for x in range(w)] for y in range(h)]


def _create_diff_image_without_cv2(input_path: str | Path, svg_content: str):
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


def _compute_otsu_threshold(grayscale: list[list[int]]) -> int:
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


def _adaptive_threshold(grayscale: list[list[int]], block_size: int = 15, c: int = 5) -> list[list[int]]:
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


def load_binary_image_with_mode(path: Path, *, threshold: int = 220, mode: str = "global") -> list[list[int]]:
    grayscale = load_grayscale_image(path)
    m = str(mode).lower()
    if m == 'global':
        return [[1 if v < threshold else 0 for v in row] for row in grayscale]
    if m == 'otsu':
        t = _compute_otsu_threshold(grayscale)
        return [[1 if v < t else 0 for v in row] for row in grayscale]
    if m == 'adaptive':
        return _adaptive_threshold(grayscale)
    raise ValueError(f"Unknown threshold mode '{mode}'.")


def render_candidate_mask(candidate: Candidate, width: int, height: int) -> list[list[int]]:
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


def score_candidate(target: list[list[int]], candidate: Candidate) -> float:
    return _iou(target, render_candidate_mask(candidate, len(target[0]), len(target)))


def random_neighbor(base: Candidate, scale: float, rng: random.Random) -> Candidate:
    return Candidate(base.shape, base.cx + rng.uniform(-scale, scale), base.cy + rng.uniform(-scale, scale), max(1.0, base.w + rng.uniform(-scale, scale) * 1.4), max(1.0, base.h + rng.uniform(-scale, scale) * 1.4))


def optimize_element(target: list[list[int]], init: Candidate, *, max_iter: int, plateau_limit: int, seed: int) -> tuple[Candidate, float]:
    rng = random.Random(seed)
    best = init
    best_score = score_candidate(target, best)
    scale = max(1.0, max(best.w, best.h) * 0.2)
    plateau = 0
    for _ in range(max_iter):
        cand = random_neighbor(best, scale, rng)
        s = score_candidate(target, cand)
        if s >= best_score:
            best, best_score, plateau = cand, s, 0
        else:
            plateau += 1
        if plateau > plateau_limit:
            scale = max(0.5, scale * 0.7)
            plateau = 0
    return best, best_score


def _gray_to_hex(v: float) -> str:
    g = max(0, min(255, int(round(v))))
    return f"#{g:02x}{g:02x}{g:02x}"


def estimate_stroke_style(grayscale: list[list[int]], element: Element, candidate: Candidate) -> tuple[str, str | None, float | None]:
    vals = [grayscale[y + element.y0][x + element.x0] for y,row in enumerate(element.pixels) for x,v in enumerate(row) if v]
    fill = _gray_to_hex(sum(vals) / max(1, len(vals)))
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
        return _gray_to_hex(sum(inner)/len(inner)), _gray_to_hex(sum(outer)/len(outer)), max(1.0, r*0.2)
    return fill, None, None


def candidate_to_svg(candidate: Candidate, gx: int, gy: int, fill_color: str, stroke_color: str | None = None, stroke_width: float | None = None) -> str:
    if candidate.shape == 'circle':
        r = max(1.0, (candidate.w + candidate.h) / 4.0)
        if stroke_color is not None and stroke_width is not None:
            r = max(0.5, r - (float(stroke_width) / 2.0))
        stroke_attr = '' if stroke_color is None else f' stroke="{stroke_color}" stroke-width="{float(stroke_width or 1.0):.2f}"'
        return f'<circle cx="{candidate.cx + gx:.2f}" cy="{candidate.cy + gy:.2f}" r="{r:.2f}" fill="{fill_color}"{stroke_attr} />'
    rx = max(1.0, candidate.w / 2.0)
    ry = max(1.0, candidate.h / 2.0)
    return f'<ellipse cx="{candidate.cx + gx:.2f}" cy="{candidate.cy + gy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" fill="{fill_color}" />'


def decompose_circle_with_stem(grayscale: list[list[int]], element: Element, candidate: Candidate) -> list[str] | None:
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
    stem_color = _gray_to_hex(round(sum(stem_values) / max(1, len(stem_values))))

    fill_color, stroke_color, stroke_width = estimate_stroke_style(grayscale, element, candidate)

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
    circle = candidate_to_svg(
        candidate,
        element.x0,
        element.y0,
        fill_color if fill_color else _gray_to_hex(sum(circle_vals) / max(1, len(circle_vals))),
        stroke_color,
        stroke_width,
    )
    return [rect, circle]

def _missing_required_image_dependencies() -> list[str]:
    missing: list[str] = []
    if cv2 is None:
        missing.append("opencv-python-headless")
    if np is None:
        missing.append("numpy")
    return missing




def rgb_to_hex(rgb: np.ndarray) -> str:
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def get_base_name_from_file(filename: str) -> str:
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
        self.base_name = get_base_name_from_file(os.path.basename(self.img_path))
        self.img = cv2.imread(self.img_path)
        self.raw_desc = self._load_descriptions()

    def _load_descriptions(self) -> dict[str, str]:
        return _load_description_mapping(self.csv_path)


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




def _load_description_mapping_from_csv(path: str) -> dict[str, str]:
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


def _load_description_mapping_from_xml(path: str) -> dict[str, str]:
    raw_desc: dict[str, str] = {}
    resolved_path = _resolve_description_xml_path(path)
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

    def _register_description(key: str, description: str) -> None:
        normalized_desc = str(description or "").strip()
        if not normalized_desc:
            return

        for candidate in {
            str(key or "").strip(),
            str(key or "").strip().upper(),
            str(key or "").strip().lower(),
            get_base_name_from_file(str(key or "").strip()),
            get_base_name_from_file(str(key or "").strip()).upper(),
            get_base_name_from_file(str(key or "").strip()).lower(),
            os.path.splitext(str(key or "").strip())[0],
            os.path.splitext(str(key or "").strip())[0].upper(),
            os.path.splitext(str(key or "").strip())[0].lower(),
        }:
            if candidate:
                raw_desc[candidate] = normalized_desc

    def _merge_entry_and_image_desc(entry_desc: str, image_desc: str) -> str:
        e = entry_desc.strip()
        i = image_desc.strip()
        if e and i and e != i:
            return f"{e} {i}".strip()
        return i or e

    def _extract_image_specific_description(entry: ET.Element, image_name: str) -> str:
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
            _register_description(root_form, desc)
        if key and desc:
            _register_description(key, desc)

        for image_tag in entry.findall("./bilder/bild"):
            image_name = (image_tag.text or "").strip()
            image_stem = os.path.splitext(image_name)[0].strip()
            image_specific_desc = _extract_image_specific_description(entry, image_name)
            merged_desc = _merge_entry_and_image_desc(desc, image_specific_desc)
            if merged_desc:
                _register_description(image_name, merged_desc)
                _register_description(image_stem, merged_desc)

    return raw_desc


def _resolve_description_xml_path(path: str) -> str | None:
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


def _required_vendor_packages() -> list[str]:
    return [
        "numpy",
        "opencv-python-headless",
        "Pillow",
        "PyMuPDF",
    ]




class Reflection:
    def __init__(self, raw_desc: dict[str, str]):
        self.raw_desc = raw_desc

    def parse_description(self, base_name: str, img_filename: str):
        canonical_base = get_base_name_from_file(base_name).upper()
        if not canonical_base:
            canonical_base = get_base_name_from_file(img_filename).upper()
        description_fragments = _collect_description_fragments(self.raw_desc, base_name, img_filename)
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
            "documented_alias_refs": sorted(Reflection._extract_documented_alias_refs(desc)),
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

        if base_upper in {
            "AR0100",
            "AC0800",
            "AC0811",
            "AC0810",
            "AC0812",
            "AC0813",
            "AC0814",
            "AC0820",
            "AC0831",
            "AC0832",
            "AC0833",
            "AC0834",
            "AC0835",
            "AC0836",
            "AC0837",
            "AC0838",
            "AC0839",
            "AC0870",
            "AC0881",
            "AC0882",
        }:
            params["mode"] = "semantic_badge"
            family_elements: list[str] = []
            heuristic_elements: list[str] = []
            if base_upper in {"AC0800", "AC0810", "AC0811", "AC0812", "AC0813", "AC0814"}:
                family_elements.append("SEMANTIC: Kreis ohne Buchstabe")
                params["label"] = ""
            elif re.search(r"\bco(?:[_\s\-\^]*2|₂)\b", desc):
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO_2")
                params["label"] = "CO_2"
            elif re.search(r"\bco\b", desc):
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO")
                params["label"] = "CO"
            elif "voc" in desc:
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe VOC")
                params["label"] = "VOC"
            elif "buchstabe" in desc:
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
                params["label"] = "M" if symbol_upper == "AR0100" else "T"
            else:
                heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
                params["label"] = "M" if base_upper == "AR0100" else "T"
            if base_upper in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"}:
                family_elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")
            if base_upper in {"AC0811", "AC0881", "AC0831", "AC0836"}:
                family_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")
            if base_upper in {"AC0813", "AC0833"}:
                family_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
            if base_upper in {"AC0812", "AC0832", "AC0837", "AC0882"}:
                family_elements.append("SEMANTIC: waagrechter Strich links vom Kreis")
            if "waagrechter strich rechts" in desc:
                heuristic_elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")
            if "senkrechter strich oben" in desc:
                heuristic_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
            if "senkrechter strich hinter" in desc:
                heuristic_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")

            params["semantic_sources"] = {
                "family_rule": list(dict.fromkeys(family_elements)),
                "description_heuristic": list(dict.fromkeys(heuristic_elements)),
            }
            params["elements"].extend(params["semantic_sources"]["family_rule"])
            params["semantic_sources"]["description_heuristic"] = list(
                dict.fromkeys(params["semantic_sources"]["description_heuristic"])
            )
            for element in params["semantic_sources"]["description_heuristic"]:
                if element not in params["elements"]:
                    params["elements"].append(element)

            layout_overrides = Reflection._parse_semantic_badge_layout_overrides(desc)
            if layout_overrides:
                params["badge_overrides"] = layout_overrides
                params["semantic_sources"]["layout_override"] = sorted(layout_overrides)
                params["elements"].append("SEMANTIC: Layout-Override für Badge-Text")

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


    @staticmethod
    def _extract_documented_alias_refs(text: str) -> set[str]:
        """Extract explicit "Wie AC0000" style alias references from descriptions."""
        if not text:
            return set()

        refs = {
            match.upper()
            for match in re.findall(r"\bwie(?:\s+in)?\s+([a-z]{2}\d{3,4})\b", text, flags=re.IGNORECASE)
        }
        return refs

    @staticmethod
    def _parse_semantic_badge_layout_overrides(text: str) -> dict[str, float | str]:
        """Extract optional layout directives from semantic badge descriptions."""
        if not text:
            return {}

        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        overrides: dict[str, float | str] = {}

        # Example phrases we intentionally support:
        # - "CO bezüglich des Kreises vertikal zentriert"
        # - "CO_2 bezüglich des Kreises horizontal zentriert"
        if re.search(r"\bco\b[^.\n]*vertikal\s+zentriert", normalized):
            overrides["co2_dy"] = 0.0
            overrides["co2_optical_bias"] = 0.0

        if re.search(r"\bco(?:[_\s-]*2|₂)\b[^.\n]*horizontal\s+zentriert", normalized):
            # Horizontal centering explicitly targets the full CO₂ cluster,
            # not just the dominant "CO" run.
            overrides["co2_anchor_mode"] = "cluster"
            overrides["co2_dx"] = 0.0

        return overrides
def _render_svg_to_numpy_inprocess(svg_string: str, size_w: int, size_h: int):
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


def _render_svg_to_numpy_via_subprocess(svg_string: str, size_w: int, size_h: int):
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
    def _snap_half(value: float) -> float:
        return round(float(value) * 2.0) / 2.0

    @staticmethod
    def _clip_scalar(value: float, low: float, high: float) -> float:
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
    def _make_rng(seed: int):
        if np is not None:
            return np.random.default_rng(int(seed))
        return Action._ScalarRng(int(seed))

    @staticmethod
    def _argmin_index(values: list[float]) -> int:
        return min(range(len(values)), key=lambda i: float(values[i]))

    @staticmethod
    def _snap_int_px(value: float, minimum: float = 1.0) -> float:
        return float(max(int(round(float(minimum))), int(round(float(value)))))

    @staticmethod
    def _max_circle_radius_inside_canvas(cx: float, cy: float, w: int, h: int, stroke: float = 0.0) -> float:
        """Return the largest circle radius that stays inside the SVG viewport."""
        if w <= 0 or h <= 0:
            return 1.0
        edge_margin = min(float(cx), float(w) - float(cx), float(cy), float(h) - float(cy))
        return float(max(1.0, edge_margin - (max(0.0, float(stroke)) / 2.0)))

    @staticmethod
    def _is_circle_with_text(params: dict) -> bool:
        """Return True when the badge encodes a circle-with-text shape."""
        return bool(params.get("circle_enabled", True)) and bool(params.get("draw_text", False))

    @staticmethod
    def _apply_circle_text_width_constraint(params: dict, radius: float, w: int) -> float:
        """Enforce CircleWithText constraint: 2 * radius < image width."""
        if not Action._is_circle_with_text(params):
            return float(radius)
        # Keep a tiny strict margin so the optimized radius remains strictly below w/2.
        width_cap = (float(w) / 2.0) - 1e-3
        return float(min(float(radius), width_cap))

    @staticmethod
    def _apply_circle_text_radius_floor(params: dict, radius: float) -> float:
        """Enforce CircleWithText lower bound: radius must exceed half text width."""
        if not Action._is_circle_with_text(params):
            return float(radius)
        x1, _y1, x2, _y2 = Action._text_bbox(params)
        text_width = max(0.0, float(x2) - float(x1))
        if text_width <= 0.0:
            return float(radius)
        # Keep strict inequality: radius > (text_width / 2).
        lower_bound = (text_width / 2.0) + 1e-3
        return float(max(float(radius), lower_bound))

    @staticmethod
    def _clamp_circle_inside_canvas(params: dict, w: int, h: int) -> dict:
        """Clamp circle center/radius so no part of the ring exceeds the viewport."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(max(0.0, min(float(w), float(p.get("cx", 0.0)))))
        cy = float(max(0.0, min(float(h), float(p.get("cy", 0.0)))))
        stroke = float(p.get("stroke_circle", 0.0))
        max_r = Action._max_circle_radius_inside_canvas(cx, cy, w, h, stroke)
        max_r = Action._apply_circle_text_width_constraint(p, max_r, w)
        min_r = float(
            max(
                1.0,
                float(p.get("min_circle_radius", 1.0)),
                float(p.get("circle_radius_lower_bound_px", 1.0)),
            )
        )
        min_r = Action._apply_circle_text_radius_floor(p, min_r)
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
    def apply_redraw_variation(params: dict, w: int, h: int) -> tuple[dict, list[str]]:
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
        rng = Action._make_rng(seed)

        def _uniform(delta: float) -> float:
            return float(rng.uniform(-abs(float(delta)), abs(float(delta))))

        jitter_entries: list[str] = []

        def _apply_numeric_jitter(key: str, delta: float, *, minimum: float | None = None, maximum: float | None = None) -> None:
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

        _apply_numeric_jitter("cx", max(0.15, float(w) * 0.01), minimum=0.0, maximum=float(w))
        _apply_numeric_jitter("cy", max(0.15, float(h) * 0.01), minimum=0.0, maximum=float(h))
        _apply_numeric_jitter("r", max(0.10, float(min(w, h)) * 0.008), minimum=1.0)
        _apply_numeric_jitter("stroke_circle", 0.12, minimum=0.4)
        _apply_numeric_jitter("arm_len", max(0.12, float(w) * 0.012), minimum=0.5, maximum=float(max(w, h)))
        _apply_numeric_jitter("arm_stroke", 0.12, minimum=0.4)
        _apply_numeric_jitter("stem_height", max(0.12, float(h) * 0.012), minimum=0.5, maximum=float(max(w, h)))
        _apply_numeric_jitter("stem_width", 0.12, minimum=0.4, maximum=float(max(1, w)))
        _apply_numeric_jitter("text_scale", 0.03, minimum=0.35, maximum=4.0)
        _apply_numeric_jitter("text_x", max(0.10, float(w) * 0.01), minimum=0.0, maximum=float(w))
        _apply_numeric_jitter("text_y", max(0.10, float(h) * 0.01), minimum=0.0, maximum=float(h))
        _apply_numeric_jitter("co2_dx", 0.08)
        _apply_numeric_jitter("co2_dy", 0.08)
        _apply_numeric_jitter("voc_scale", 0.03, minimum=0.35, maximum=4.0)

        p = Action._clamp_circle_inside_canvas(p, w, h)
        if p.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(p, float(p.get("r", 1.0)))
        if p.get("stem_enabled") and "cy" in p and "r" in p:
            p["stem_top"] = float(p.get("cy", 0.0)) + float(p.get("r", 0.0))

        if jitter_entries:
            variation_logs.append(
                "redraw_variation: seed="
                f"{seed} changed_params=" + " | ".join(jitter_entries)
            )
        return p, variation_logs

    @staticmethod
    def _enforce_circle_connector_symmetry(params: dict, w: int, h: int) -> dict:
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
    def _quantize_badge_params(params: dict, w: int, h: int) -> dict:
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
                p[key] = Action._snap_half(float(p[key]))

        int_width_keys = ("stroke_circle", "arm_stroke", "stem_width")
        for key in int_width_keys:
            if key in p:
                p[key] = Action._snap_int_px(float(p[key]), minimum=1.0)

        if "stem_width_max" in p:
            p["stem_width_max"] = max(1.0, Action._snap_half(float(p["stem_width_max"])))

        if p.get("stem_enabled") and "cx" in p and "stem_width" in p:
            p["stem_x"] = Action._snap_half(float(p["cx"]) - (float(p["stem_width"]) / 2.0))

        if "stem_x" in p and "stem_width" in p:
            p["stem_x"] = max(0.0, min(float(w) - float(p["stem_width"]), float(p["stem_x"])))
        if "stem_top" in p:
            p["stem_top"] = max(0.0, min(float(h), float(p["stem_top"])))
        if "stem_bottom" in p:
            p["stem_bottom"] = max(0.0, min(float(h), float(p["stem_bottom"])))

        p = Action._enforce_circle_connector_symmetry(p, w, h)
        p = Action._clamp_circle_inside_canvas(p, w, h)

        if (
            raw_circle_radius is not None
            and "cx" in p
            and "cy" in p
            and "r" in p
        ):
            canvas_fit_r = float(
                Action._max_circle_radius_inside_canvas(
                    float(p["cx"]),
                    float(p["cy"]),
                    w,
                    h,
                    float(p.get("stroke_circle", 0.0)),
                )
            )
            snapped_canvas_fit_r = float(Action._snap_half(canvas_fit_r))
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
                p[key] = Action._snap_half(float(p[key]))

        return p

    @staticmethod
    def _normalize_light_circle_colors(params: dict) -> dict:
        params["fill_gray"] = Action.LIGHT_CIRCLE_FILL_GRAY
        params["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        if params.get("stem_enabled"):
            params["stem_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        if params.get("draw_text", True) and "text_gray" in params:
            params["text_gray"] = Action.LIGHT_CIRCLE_TEXT_GRAY
        return params

    @staticmethod
    def _normalize_ac08_line_widths(params: dict) -> dict:
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
    def _estimate_border_background_gray(gray: np.ndarray) -> float:
        """Estimate badge background tone from the outer image border pixels."""
        if gray.size == 0:
            return 255.0
        h, w = gray.shape
        if h < 2 or w < 2:
            return float(np.median(gray))
        border = np.concatenate((gray[0, :], gray[h - 1, :], gray[:, 0], gray[:, w - 1]))
        return float(np.median(border))

    @staticmethod
    def _estimate_circle_tones_and_stroke(
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
    def _persist_connector_length_floor(params: dict, element: str, default_ratio: float) -> None:
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
    def _is_ac08_small_variant(name: str, params: dict) -> tuple[bool, str, float]:
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
    def _configure_ac08_small_variant_mode(name: str, params: dict) -> dict:
        """Apply `_S`-specific AC08 tuning for text, connector floors, and masks."""
        p = dict(params)
        is_small, reason, min_dim = Action._is_ac08_small_variant(name, p)
        p["ac08_small_variant_mode"] = bool(is_small)
        p["ac08_small_variant_reason"] = reason
        p["ac08_small_variant_min_dim"] = float(min_dim)
        if not is_small:
            return p

        p["validation_mask_dilate_px"] = int(max(1, int(p.get("validation_mask_dilate_px", 1))))
        p["small_variant_antialias_bias"] = float(max(0.0, float(p.get("small_variant_antialias_bias", 0.08))))

        if p.get("arm_enabled"):
            p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", 0.75)), 0.78))
            Action._persist_connector_length_floor(p, "arm", default_ratio=0.78)
        if p.get("stem_enabled"):
            p["stem_len_min_ratio"] = float(max(float(p.get("stem_len_min_ratio", 0.65)), 0.70))
            Action._persist_connector_length_floor(p, "stem", default_ratio=0.70)

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
    def _enforce_template_circle_edge_extent(params: dict, w: int, h: int, *, anchor: str, retain_ratio: float = 0.97) -> dict:
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
        canvas_cap = float(Action._max_circle_radius_inside_canvas(cx, float(p.get("cy", float(h) / 2.0)), w, h, stroke))

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
    def _tune_ac08_left_connector_family(name: str, params: dict) -> dict:
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
        symbol_name = get_base_name_from_file(str(name)).upper().split("_", 1)[0]
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
        is_small, _reason, min_dim = Action._is_ac08_small_variant(str(name), p)
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
        p = Action._enforce_template_circle_edge_extent(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
            anchor="right",
            retain_ratio=0.97 if not is_small else 0.96,
        )

        p = Action._enforce_left_arm_badge_geometry(
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
            Action._center_glyph_bbox(p)
        return p

    @staticmethod
    def _tune_ac08_right_connector_family(name: str, params: dict) -> dict:
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
        symbol_name = get_base_name_from_file(str(name)).upper().split("_", 1)[0]
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
        is_small, _reason, min_dim = Action._is_ac08_small_variant(str(name), p)
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
        p = Action._enforce_template_circle_edge_extent(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
            anchor="left",
            retain_ratio=0.97 if not is_small else 0.96,
        )

        p = Action._enforce_right_arm_badge_geometry(
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
    def _enforce_vertical_connector_badge_geometry(params: dict, w: int, h: int) -> dict:
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
    def _tune_ac08_vertical_connector_family(name: str, params: dict) -> dict:
        """Apply shared guardrails for AC08 families with vertical connectors.

        Aufgabe 4.3 groups AC0811, AC0813, AC0831, AC0833, AC0836 and AC0881 because
        they all depend on a vertical connector staying centered relative to the
        circle. Their main shared regressions are:
        - the stem/arm drifting sideways relative to the circle,
        - the vertical connector shrinking until the badge reads as plain circle,
        - text badges becoming top-heavy once circle and connector alignment drifts.
        """
        p = dict(params)
        symbol_name = get_base_name_from_file(str(name)).upper().split("_", 1)[0]
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
        is_small, _reason, min_dim = Action._is_ac08_small_variant(str(name), p)
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

        p = Action._enforce_vertical_connector_badge_geometry(
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
    def _tune_ac08_circle_text_family(name: str, params: dict) -> dict:
        """Apply shared guardrails for connector-free AC08 circle/text badges.

        Aufgabe 4.4 groups AC0820, AC0835 and AC0870 because they all:
        - have no connector geometry that should influence circle fitting,
        - regress when text blobs pull the circle away from the semantic center,
        - need stable text scaling without letting the ring collapse or overgrow.
        """
        p = dict(params)
        symbol_name = get_base_name_from_file(str(name)).upper().split("_", 1)[0]
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
            canvas_cap = Action._max_circle_radius_inside_canvas(
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
            Action._center_glyph_bbox(p)

        return p

    @staticmethod
    def _finalize_ac08_style(name: str, params: dict) -> dict:
        """Apply AC08xx palette/stroke conventions globally for semantic conversions."""
        canonical_name = str(name).upper()
        symbol_name = canonical_name.split("_", 1)[0]
        if not symbol_name.startswith("AC08"):
            return params
        p = Action._capture_canonical_badge_colors(Action._normalize_light_circle_colors(dict(params)))
        p = Action._enforce_semantic_component_contract(canonical_name, p)
        p["badge_symbol_name"] = symbol_name
        # During geometry fitting we intentionally keep auto-estimated colors.
        # Canonical palette values are re-applied once fitting converged.
        p = Action._normalize_ac08_line_widths(p)
        p["lock_colors"] = True
        p = Action._normalize_centered_co2_label(p)
        if symbol_name == "AC0831" and str(p.get("text_mode", "")).lower() == "co2":
            p["fill_gray"] = 238
            p["stroke_gray"] = 155
            p["text_gray"] = 155
            if p.get("stem_enabled"):
                p["stem_gray"] = 155
        if symbol_name == "AC0833" and str(p.get("text_mode", "")).lower() == "co2":
            p = Action._tune_ac0833_co2_badge(p)
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
            if _needs_large_circle_overflow_guard(p) and image_width > 0.0:
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
                    p = Action._align_stem_to_circle_center(p)
                if p.get("arm_enabled"):
                    Action._reanchor_arm_to_circle_edge(p, float(p.get("r", 0.0)))
        if p.get("stem_enabled"):
            Action._persist_connector_length_floor(p, "stem", default_ratio=0.65)
        if p.get("arm_enabled"):
            Action._persist_connector_length_floor(p, "arm", default_ratio=0.75)
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
        p = Action._configure_ac08_small_variant_mode(name, p)
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
            # AC0800 variants are plain rings only. Template transfer can carry
            # connector metadata from donor symbols (e.g. AC0811/AC0812), which
            # must be stripped so L/S variants never render tiny residual grips.
            p.pop("stem_enabled", None)
            p.pop("arm_enabled", None)
            for connector_key in (
                "stem_x",
                "stem_top",
                "stem_bottom",
                "stem_width",
                "stem_gray",
                "arm_x1",
                "arm_y1",
                "arm_x2",
                "arm_y2",
                "arm_stroke",
            ):
                p.pop(connector_key, None)
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
            p["r"] = float(Action._clip_scalar(float(p.get("r", template_r)), min_r, max_r))
        if p.get("draw_text", True) and "text_gray" in p:
            p["text_gray"] = int(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))
        return p

    @staticmethod
    def _enforce_semantic_component_contract(name: str, params: dict) -> dict:
        """Strip components that are not part of the semantic symbol definition."""
        p = dict(params)
        canonical_name = str(name).upper()
        symbol_name = canonical_name.split("_", 1)[0]

        no_text_symbols = {"AC0800", "AC0810", "AC0811", "AC0812", "AC0813", "AC0814", "AC0881", "AC0882"}
        no_connector_symbols = {"AC0800", "AC0820", "AC0835", "AC0870"}
        arm_only_symbols = {"AC0810", "AC0812", "AC0813", "AC0814", "AC0832", "AC0833", "AC0834", "AC0837", "AC0838", "AC0839", "AC0882"}
        stem_only_symbols = {"AC0811", "AC0831", "AC0836", "AC0881"}

        if symbol_name in no_text_symbols:
            p["draw_text"] = False
            p["label"] = ""
            p.pop("text_mode", None)

        if symbol_name in no_connector_symbols or symbol_name in stem_only_symbols:
            p.pop("arm_enabled", None)
            for key in ("arm_x1", "arm_y1", "arm_x2", "arm_y2", "arm_stroke"):
                p.pop(key, None)

        if symbol_name in no_connector_symbols or symbol_name in arm_only_symbols:
            p.pop("stem_enabled", None)
            for key in ("stem_x", "stem_top", "stem_bottom", "stem_width", "stem_gray"):
                p.pop(key, None)

        return p

    @staticmethod
    def _activate_ac08_adaptive_locks(
        params: dict,
        logs: list[str],
        *,
        full_err: float,
        reason: str,
    ) -> bool:
        """Adaptive AC08 locks are disabled so semantic badge fitting stays unconstrained."""
        return False

    @staticmethod
    def _release_ac08_adaptive_locks(
        params: dict,
        logs: list[str],
        *,
        reason: str,
        current_error: float,
    ) -> bool:
        """Adaptive AC08 lock release is disabled because there are no AC08 locks to release."""
        return False

    @staticmethod
    def _align_stem_to_circle_center(params: dict) -> dict:
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
    def _default_ac0870_params(w: int, h: int) -> dict:
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
        Action._center_glyph_bbox(params)
        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def _default_ac0881_params(w: int, h: int) -> dict:
        params = Action._default_ac0870_params(w, h)
        params["stem_enabled"] = True
        params["stem_width"] = max(1.0, params["r"] * 0.30)
        params["stem_x"] = params["cx"] - (params["stem_width"] / 2.0)
        params["stem_top"] = params["cy"] + (params["r"] * 0.60)
        params["stem_bottom"] = float(h)
        params["stem_gray"] = params["stroke_gray"]
        return params

    @staticmethod
    def _default_ac081x_shared(w: int, h: int) -> dict:
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
    def _default_edge_anchored_circle_geometry(
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
    def _default_ac0811_params(w: int, h: int) -> dict:
        """AC0811 is vertically elongated: circle sits in the upper square area."""
        if w <= 0 or h <= 0:
            return Action._default_ac081x_shared(w, h)

        circle = Action._default_edge_anchored_circle_geometry(w, h, anchor="top")
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

        return Action._normalize_light_circle_colors({
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
    def _estimate_upper_circle_from_foreground(img: np.ndarray, defaults: dict) -> tuple[float, float, float] | None:
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
        r = float(Action._clip_scalar(r, min_r, max_r))
        cx = float(Action._clip_scalar(cx, 0.0, float(w - 1)))
        cy = float(Action._clip_scalar(cy, 0.0, float(h - 1)))
        return cx, cy, r

    @staticmethod
    def _fit_ac0811_params_from_image(img: np.ndarray, defaults: dict) -> dict:
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
            params["cy"] = float(Action._clip_scalar(cy, default_cy - 1.0, default_cy + 1.0))
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
            r = float(Action._clip_scalar(r, default_r * 0.95, default_r * 1.08))
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
            Action._persist_connector_length_floor(params, "stem", default_ratio=0.80)

        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def _default_ac0882_params(w: int, h: int) -> dict:
        params = Action._default_ac081x_shared(w, h)
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
        Action._center_glyph_bbox(params)
        return params

    @staticmethod
    def _apply_co2_label(params: dict) -> dict:
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
    def _co2_layout(params: dict) -> dict[str, float | str]:
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
    def _apply_voc_label(params: dict) -> dict:
        params["draw_text"] = True
        params["text_mode"] = "voc"
        params["text_gray"] = int(round(params.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))
        params["voc_font_scale"] = float(params.get("voc_font_scale", 0.52 * Action.SEMANTIC_TEXT_BASE_SCALE))
        params["voc_dy"] = float(params.get("voc_dy", -0.01 * float(params.get("r", 0.0))))
        params["voc_weight"] = int(params.get("voc_weight", 600))
        return params

    @staticmethod
    def _tune_ac0832_co2_badge(params: dict) -> dict:
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
    def _tune_ac0831_co2_badge(params: dict) -> dict:
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
    def _tune_ac0835_voc_badge(params: dict, w: int, h: int) -> dict:
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
    def _tune_ac0833_co2_badge(params: dict) -> dict:
        """Tune AC0833 CO² badges so the trailing index stays superscript."""
        p = Action._normalize_light_circle_colors(dict(params))
        p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "cluster"))
        p["co2_index_mode"] = "superscript"
        p["co2_superscript_offset_scale"] = float(max(float(p.get("co2_superscript_offset_scale", 0.16)), 0.16))
        p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.17)), 0.17))
        return p

    @staticmethod
    def _tune_ac0834_co2_badge(params: dict, w: int, h: int) -> dict:
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
    def _default_ac0834_params(w: int, h: int) -> dict:
        """Compatibility helper for AC0834 semantic tests and callers."""
        return Action._tune_ac0834_co2_badge(Action._apply_co2_label(Action._default_ac0814_params(w, h)), w, h)

    @staticmethod
    def _normalize_centered_co2_label(params: dict) -> dict:
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
    def _default_ac0812_params(w: int, h: int) -> dict:
        """AC0812 is horizontally elongated: left arm, circle on the right."""
        if w <= 0 or h <= 0:
            return Action._default_ac081x_shared(w, h)

        # Like AC0811/AC0813, size from the narrow side so tiny variants keep
        # the intended visual circle diameter.
        # AC0812 source rasters leave a slightly larger vertical margin around the
        # ring than AC0811/AC0813. Using 0.40*h tends to over-size the circle.
        r = float(h) * 0.36
        stroke_circle = max(0.9, float(h) / 15.0)
        cx = float(w) - (float(h) / 2.0)
        cy = float(h) / 2.0
        arm_stroke = max(1.0, float(h) * 0.10)

        return Action._normalize_light_circle_colors(
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
    def _fit_ac0812_params_from_image(img: np.ndarray, defaults: dict) -> dict:
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
        canvas_r_limit = Action._max_circle_radius_inside_canvas(cx, cy, w, h, stroke_circle)
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
        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def _enforce_left_arm_badge_geometry(params: dict, w: int, h: int) -> dict:
        """Ensure AC0812-like badges always keep a visible left connector arm."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(p["cx"])
        cy = float(p["cy"])
        r = float(p["r"])
        arm_stroke = float(max(1.0, p.get("arm_stroke", Action.AC08_STROKE_WIDTH_PX)))
        attach_offset = max(0.0, arm_stroke / 2.0)
        arm_x2 = max(0.0, cx - r - attach_offset)

        p["arm_enabled"] = True
        p["arm_x1"] = 0.0
        p["arm_y1"] = cy
        p["arm_x2"] = arm_x2
        p["arm_y2"] = cy
        p["arm_stroke"] = arm_stroke

        arm_len = float(max(0.0, arm_x2))
        ratio = float(max(0.0, min(1.0, float(p.get("arm_len_min_ratio", 0.75)))))
        p["arm_len_min_ratio"] = ratio
        p["arm_len_min"] = float(max(1.0, float(p.get("arm_len_min", 1.0)), arm_len * ratio))
        return p

    @staticmethod
    def _enforce_right_arm_badge_geometry(params: dict, w: int, h: int) -> dict:
        """Ensure AC0810/AC0814-like badges always keep a visible right connector arm."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(p["cx"])
        cy = float(p["cy"])
        r = float(p["r"])
        arm_stroke = float(max(1.0, p.get("arm_stroke", Action.AC08_STROKE_WIDTH_PX)))
        attach_offset = max(0.0, arm_stroke / 2.0)
        canvas_width = max(float(w), float(p.get("arm_x2", 0.0) or 0.0), float(p.get("width", 0.0) or 0.0), float(p.get("badge_width", 0.0) or 0.0), cx + r)
        ratio = float(max(0.0, min(1.0, float(p.get("arm_len_min_ratio", 0.75)))))
        requested_min_len = float(max(1.0, float(p.get("arm_len_min", 1.0))))
        requested_min_len = float(min(requested_min_len, canvas_width * 0.35))
        semantic_min_len = float(
            max(
                requested_min_len,
                ratio * max(1.0, canvas_width * 0.20),
            )
        )
        if str(p.get("text_mode", "")).lower() in {"co2", "voc"}:
            semantic_min_len = float(max(semantic_min_len, canvas_width * 0.20))
        arm_start = cx + r + attach_offset
        max_arm_start = max(0.0, canvas_width - semantic_min_len)
        if arm_start > max_arm_start:
            cx = max(r + attach_offset, cx - (arm_start - max_arm_start))
            p["cx"] = cx
        max_r_for_semantic_span = max(1.0, canvas_width - semantic_min_len - attach_offset - cx)
        if r > max_r_for_semantic_span:
            r = max_r_for_semantic_span
            p["r"] = r
        arm_x1 = min(canvas_width, cx + r + attach_offset)

        p["arm_enabled"] = True
        p["arm_x1"] = arm_x1
        p["arm_y1"] = cy
        p["arm_x2"] = canvas_width
        p["arm_y2"] = cy
        p["arm_stroke"] = arm_stroke

        arm_len = float(max(0.0, canvas_width - arm_x1))
        p["arm_len_min_ratio"] = ratio
        p["arm_len_min"] = float(max(semantic_min_len, arm_len * ratio))
        return p

    @staticmethod
    def _default_ac0813_params(w: int, h: int) -> dict:
        """AC0813 is AC0812 rotated 90° clockwise (vertical arm from top to circle)."""
        if w <= 0 or h <= 0:
            return Action._default_ac081x_shared(w, h)

        # Like other edge-anchored connector badges, size from the narrow side and
        # keep a small optical clearance from the anchored edge.
        circle = Action._default_edge_anchored_circle_geometry(w, h, anchor="bottom")
        cx = float(circle["cx"])
        cy = float(circle["cy"])
        r = float(circle["r"])
        stroke_circle = float(circle["stroke_circle"])
        arm_stroke = max(1.0, float(w) * 0.10)

        return Action._normalize_light_circle_colors(
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
    def _fit_ac0813_params_from_image(img: np.ndarray, defaults: dict) -> dict:
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
            params["cy"] = float(Action._clip_scalar(cy, default_cy - 0.8, default_cy + 0.8))
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
        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def _rotate_semantic_badge_clockwise(params: dict, w: int, h: int) -> dict:
        cx = float(w) / 2.0
        cy = float(h) / 2.0

        def rotate_clockwise(x: float, y: float) -> tuple[float, float]:
            # image-space clockwise description maps to mathematically counter-clockwise
            # because y grows downward in raster coordinates.
            return cx - (y - cy), cy + (x - cx)

        rotated = dict(params)
        rotated["cx"], rotated["cy"] = rotate_clockwise(float(params["cx"]), float(params["cy"]))
        rotated["arm_x1"], rotated["arm_y1"] = rotate_clockwise(float(params["arm_x1"]), float(params["arm_y1"]))
        rotated["arm_x2"], rotated["arm_y2"] = rotate_clockwise(float(params["arm_x2"]), float(params["arm_y2"]))
        return rotated

    @staticmethod
    def _default_ac0814_params(w: int, h: int) -> dict:
        """AC0814 is horizontally elongated: circle on the left, arm to the right."""
        if w <= 0 or h <= 0:
            return Action._default_ac081x_shared(w, h)

        # AC0814_L-like originals use a noticeably larger ring than the earlier
        # generic AC081x template and keep a visible left margin before the
        # circle. A tighter template gets much closer to the hand-traced sample.
        r = float(h) * 0.46
        stroke_circle = max(0.9, float(h) / 25.0)
        left_margin = max(stroke_circle * 0.5, float(h) * 0.18)
        cx = r + left_margin
        cy = float(h) / 2.0
        arm_stroke = max(1.0, stroke_circle)

        return Action._normalize_light_circle_colors(
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
    def _fit_ac0814_params_from_image(img: np.ndarray, defaults: dict) -> dict:
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
            params["cy"] = float(Action._clip_scalar(cy, default_cy - 0.5, default_cy + 0.5))
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
                corrected_cx = float(Action._clip_scalar(cx, default_cx - max_left_correction, default_cx))
            params["cx"] = corrected_cx
            if medium_plain_canvas:
                params["template_circle_cx"] = corrected_cx
            params["cy"] = float(Action._clip_scalar(cy, default_cy - 0.6, default_cy + 0.6))
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
        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def _default_ac0810_params(w: int, h: int) -> dict:
        """AC0810 uses the same right-arm geometry as AC0814 (circle on the left)."""
        return Action._default_ac0814_params(w, h)

    @staticmethod
    def _fit_ac0810_params_from_image(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0810 with the same right-anchored arm behavior as AC0814."""
        return Action._fit_ac0814_params_from_image(img, defaults)

    @staticmethod
    def _glyph_bbox(text_mode: str) -> tuple[int, int, int, int]:
        if text_mode == "path_t":
            return Action.T_XMIN, Action.T_YMIN, Action.T_XMAX, Action.T_YMAX
        return Action.M_XMIN, Action.M_YMIN, Action.M_XMAX, Action.M_YMAX

    @staticmethod
    def _center_glyph_bbox(params: dict) -> None:
        if "s" not in params or "cx" not in params or "cy" not in params:
            return
        xmin, ymin, xmax, ymax = Action._glyph_bbox(params.get("text_mode", "path"))
        glyph_width = (xmax - xmin) * params["s"]
        glyph_height = (ymax - ymin) * params["s"]
        params["tx"] = float(params["cx"] - (glyph_width / 2.0))
        params["ty"] = float(params["cy"] - (glyph_height / 2.0))

    @staticmethod
    def _stabilize_semantic_circle_pose(params: dict, defaults: dict, w: int, h: int) -> dict:
        """Bound fitted circle pose to semantic template geometry.

        Tiny, low-information raster variants are especially sensitive to JPEG
        edge artifacts. For connector-only badges without text, prefer the
        semantic template center and keep radius from collapsing.
        """
        if "r" not in defaults:
            return params

        default_cx = float(defaults.get("cx", float(w) / 2.0))
        default_cy = float(defaults.get("cy", float(h) / 2.0))
        default_r = float(defaults.get("r", 0.0))
        if default_r <= 0.0:
            return params

        has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
        has_text = bool(params.get("draw_text", False))
        if not has_connector:
            return params

        if not has_text and min(w, h) <= 16:
            params["r"] = max(float(params.get("r", default_r)), default_r * 0.96)
            params["lock_circle_cx"] = True
            params["lock_circle_cy"] = True
            return params

        # Keep semantic drift bounded, but allow enough travel that larger source
        # variants (especially AC081x line+circle symbols) can still land on the
        # visually correct center when Hough/contours detect a shifted ring.
        cx_tolerance = max(1.5, float(min(w, h)) * 0.18)
        cy_tolerance = max(1.5, float(min(w, h)) * 0.18)
        current_cx = float(params.get("cx", default_cx))
        current_cy = float(params.get("cy", default_cy))
        params["cx"] = float(max(default_cx - cx_tolerance, min(default_cx + cx_tolerance, current_cx)))
        params["cy"] = float(max(default_cy - cy_tolerance, min(default_cy + cy_tolerance, current_cy)))
        min_radius = max(1.0, default_r * 0.80)
        max_radius = max(min_radius, default_r * 1.45)
        current_r = float(params.get("r", default_r))
        params["r"] = float(max(min_radius, min(max_radius, current_r)))
        return params

    def _fit_ac0870_params_from_image(img: np.ndarray, defaults: dict) -> dict:
        params = dict(defaults)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        min_side = float(min(h, w))
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(8.0, min_side * 0.5),
            param1=100,
            param2=10,
            minRadius=max(4, int(round(min_side * 0.25))),
            maxRadius=max(6, int(round(min_side * 0.48))),
        )

        if circles is not None and circles.size > 0:
            c = circles[0][0]
            params["cx"] = float(c[0])
            params["cy"] = float(c[1])
            params["r"] = float(c[2])

        yy, xx = np.indices(gray.shape)
        dist = np.sqrt((xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2)
        inner_mask = dist <= params["r"] * 0.88
        ring_mask = np.abs(dist - params["r"]) <= max(1.0, params["stroke_circle"])

        if np.any(inner_mask):
            inner_vals = gray[inner_mask]
            text_threshold = min(150, int(np.percentile(inner_vals, 20) + 3))
            text_mask = (gray <= text_threshold) & inner_mask

            kernel = np.ones((2, 2), np.uint8)
            text_mask_u8 = cv2.morphologyEx(text_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(text_mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                contour = max(contours, key=cv2.contourArea)
                x, y, tw, th = cv2.boundingRect(contour)
                if tw > 2 and th > 2:
                    t_width_units = 1636 - Action.T_XMIN
                    t_height_units = Action.T_YMAX
                    sx = tw / t_width_units
                    sy = th / t_height_units
                    s = float(max(0.004, min(0.04, (sx + sy) / 2.0)))
                    params["s"] = s
                    params["text_gray"] = int(np.median(gray[text_mask_u8 > 0]))

            Action._center_glyph_bbox(params)

            params["fill_gray"] = int(np.median(inner_vals))

        if np.any(ring_mask):
            params["stroke_gray"] = int(np.median(gray[ring_mask]))

        return params

    @staticmethod
    def _fit_semantic_badge_from_image(img: np.ndarray, defaults: dict) -> dict:
        """Fit common semantic badge primitives (circle/stem/arm) directly from image content."""
        params = dict(defaults)
        if "r" in params and "template_circle_radius" not in params:
            params["template_circle_radius"] = float(params["r"])
        if "cx" in params and "template_circle_cx" not in params:
            params["template_circle_cx"] = float(params["cx"])
        if "cy" in params and "template_circle_cy" not in params:
            params["template_circle_cy"] = float(params["cy"])
        if "stem_top" in params and "template_stem_top" not in params:
            params["template_stem_top"] = float(params["stem_top"])
        if "stem_bottom" in params and "template_stem_bottom" not in params:
            params["template_stem_bottom"] = float(params["stem_bottom"])
        if "arm_x1" in params and "template_arm_x1" not in params:
            params["template_arm_x1"] = float(params["arm_x1"])
        if "arm_y1" in params and "template_arm_y1" not in params:
            params["template_arm_y1"] = float(params["arm_y1"])
        if "arm_x2" in params and "template_arm_x2" not in params:
            params["template_arm_x2"] = float(params["arm_x2"])
        if "arm_y2" in params and "template_arm_y2" not in params:
            params["template_arm_y2"] = float(params["arm_y2"])
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        min_side = float(min(h, w))
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(6.0, min_side * 0.35),
            param1=80,
            param2=9,
            minRadius=max(3, int(round(min_side * 0.14))),
            maxRadius=max(6, int(round(min_side * 0.60))),
        )

        if circles is not None and circles.size > 0:
            best = None
            template_cx = float(defaults.get("cx", params.get("cx", float(w) / 2.0)))
            template_cy = float(defaults.get("cy", params.get("cy", float(h) / 2.0)))
            template_r = float(defaults.get("r", params.get("r", max(1.0, min_side * 0.35))))
            max_center_offset = max(2.0, min_side * 0.42)
            max_radius_delta = max(2.0, template_r * 0.70)
            for c in circles[0]:
                cx, cy, r = float(c[0]), float(c[1]), float(c[2])
                center_offset = float(math.hypot(cx - template_cx, cy - template_cy))
                # Semantic AC08xx badges follow a fixed layout. Reject detections
                # that drift too far away from the expected template center; on
                # tiny CO₂/VOC symbols those are usually text blobs, not circles.
                if center_offset > max_center_offset:
                    continue
                yy, xx = np.indices(gray.shape)
                dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
                fill_mask = dist <= max(1.0, r * 0.82)
                ring_mask = np.abs(dist - r) <= max(1.0, params.get("stroke_circle", 1.2))
                if not np.any(fill_mask) or not np.any(ring_mask):
                    continue
                fill_gray = float(np.median(gray[fill_mask]))
                ring_gray = float(np.median(gray[ring_mask]))
                # Generalized scoring for circle+ring symbols:
                # - prefer ring darker than fill with clear contrast,
                # - keep geometric closeness to semantic template.
                contrast = fill_gray - ring_gray
                tone_penalty = 0.0
                if contrast < 4.0:
                    tone_penalty += (4.0 - contrast) * 4.0
                if ring_gray >= fill_gray:
                    tone_penalty += (ring_gray - fill_gray + 1.0) * 6.0
                score = tone_penalty
                # Prefer circles that stay close to the semantic template size/
                # position so all AC08xx variants remain stable across JPEG noise.
                score += (center_offset / max_center_offset) * 9.0
                score += (abs(r - template_r) / max_radius_delta) * 6.0
                if best is None or score < best[0]:
                    best = (score, cx, cy, r, fill_gray, ring_gray)

            if best is not None:
                _, cx, cy, r, fill_gray, ring_gray = best
                params["cx"] = cx
                params["cy"] = cy
                params["r"] = r
                est_fill, est_ring, est_stroke = Action._estimate_circle_tones_and_stroke(
                    gray,
                    cx,
                    cy,
                    r,
                    float(params.get("stroke_circle", defaults.get("stroke_circle", 1.2))),
                )
                params["fill_gray"] = int(round(est_fill))
                params["stroke_gray"] = int(round(est_ring))
                has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
                has_text = bool(params.get("draw_text", False))
                if not has_connector and not has_text:
                    params["stroke_circle"] = float(max(1.0, est_stroke))
                    bg_gray = Action._estimate_border_background_gray(gray)
                    if bg_gray >= 240.0:
                        params["background_fill"] = "#ffffff"

        if not bool(params.get("arm_enabled") or params.get("stem_enabled")) and not bool(params.get("draw_text", False)):
            fg_mask = Action._foreground_mask(img)
            edge_touch_min = max(2, int(round(min_side * 0.20)))
            touches_all_edges = all(
                int(np.count_nonzero(edge)) >= edge_touch_min
                for edge in (fg_mask[0, :], fg_mask[-1, :], fg_mask[:, 0], fg_mask[:, -1])
            )
            if not touches_all_edges:
                # JPEG-soft tiny rings may miss foreground pixels on one edge.
                # Use a grayscale border cue as permissive fallback.
                bg_gray = Action._estimate_border_background_gray(gray)
                edge_dark_min = 1
                touches_all_edges = all(
                    int(np.count_nonzero(edge <= (bg_gray - 6.0))) >= edge_dark_min
                    for edge in (gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1])
                )
            if touches_all_edges:
                # Border-touch fallback should recover the visual outer circle
                # extent, not the inner fill radius after stroke normalization.
                # For tiny plain rings (e.g. AC0800_S) this keeps the fitted
                # radius aligned with the expected canvas-fitting geometry.
                border_fit_r = max(1.0, (min_side / 2.0) - 0.5)
                if float(params.get("r", 0.0)) < (border_fit_r - 0.35):
                    params["cx"] = float(defaults.get("cx", float(w) / 2.0))
                    params["cy"] = float(defaults.get("cy", float(h) / 2.0))
                    params["r"] = float(border_fit_r)
                    params["preserve_outer_diameter_on_stroke_normalization"] = True

        # Keep contour/Hough noise from collapsing circles far below the semantic
        # template size. This was most visible for compact centered badges
        # (e.g. AC0820_M), but the guard is intentionally generic for the full
        # semantic badge family.
        if "r" in defaults and "r" in params:
            default_r = float(defaults.get("r", 0.0))
            if default_r > 0.0:
                has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
                has_text = bool(params.get("draw_text", False))
                min_ratio = 0.80
                if not has_connector:
                    min_ratio = 0.88
                if has_text and not has_connector:
                    min_ratio = 0.92

                cx = float(params.get("cx", defaults.get("cx", float(w) / 2.0)))
                cy = float(params.get("cy", defaults.get("cy", float(h) / 2.0)))
                stroke = max(0.0, float(params.get("stroke_circle", defaults.get("stroke_circle", 1.0))))
                radius_limit_x = max(1.0, min(cx, float(w) - cx) - (stroke / 2.0))
                radius_limit_y = max(1.0, min(cy, float(h) - cy) - (stroke / 2.0))
                max_r = max(1.0, min(radius_limit_x, radius_limit_y))
                min_r = min(max_r, max(1.0, default_r * min_ratio))
                params["r"] = float(Action._clip_scalar(float(params.get("r", default_r)), min_r, max_r))

        if params.get("stem_enabled"):
            dark = gray <= min(225, int(np.percentile(gray, 75)))
            x1 = max(0, int(round(params["cx"] - params["r"] * 0.8)))
            x2 = min(w, int(round(params["cx"] + params["r"] * 0.8)))
            y1 = max(0, int(round(params["cy"] + params["r"] * 0.45)))
            roi = dark[y1:h, x1:x2]
            if roi.size > 0:
                cnts, _ = cv2.findContours(roi.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                best_rect = None
                for cnt in cnts:
                    rx, ry, rw, rh = cv2.boundingRect(cnt)
                    if rw < 1 or rh < 2 or rh <= rw:
                        continue
                    area = rw * rh
                    if best_rect is None or area > best_rect[0]:
                        best_rect = (area, rx, ry, rw, rh)
                if best_rect is not None:
                    _, rx, ry, rw, rh = best_rect
                    params["stem_x"] = float(x1 + rx)
                    params["stem_top"] = float(y1 + ry)
                    params["stem_width"] = float(max(1, rw))
                    params["stem_bottom"] = float(min(h, y1 + ry + rh))
                    stem_mask = np.zeros_like(gray, dtype=bool)
                    sx1 = int(max(0, params["stem_x"]))
                    sx2 = int(min(w, params["stem_x"] + params["stem_width"]))
                    sy1 = int(max(0, params["stem_top"]))
                    sy2 = int(min(h, params["stem_bottom"]))
                    stem_mask[sy1:sy2, sx1:sx2] = True
                    stem_vals = gray[stem_mask]
                    if stem_vals.size > 0:
                        params["stem_gray"] = int(round(np.median(stem_vals)))

        if params.get("arm_enabled"):
            dark = gray <= min(225, int(np.percentile(gray, 75)))
            is_horizontal = abs(params.get("arm_x2", 0.0) - params.get("arm_x1", 0.0)) >= abs(
                params.get("arm_y2", 0.0) - params.get("arm_y1", 0.0)
            )
            if is_horizontal:
                side = -1 if params.get("arm_x2", 0.0) <= params.get("cx", 0.0) else 1
                y1 = max(0, int(round(params["cy"] - params["r"] * 0.6)))
                y2 = min(h, int(round(params["cy"] + params["r"] * 0.6)))
                if side < 0:
                    x1 = max(0, int(round(params["cx"] - params["r"] * 2.0)))
                    x2 = max(0, int(round(params["cx"] - params["r"] * 0.4)))
                else:
                    x1 = min(w, int(round(params["cx"] + params["r"] * 0.4)))
                    x2 = min(w, int(round(params["cx"] + params["r"] * 2.0)))
            else:
                x1 = max(0, int(round(params["cx"] - params["r"] * 0.6)))
                x2 = min(w, int(round(params["cx"] + params["r"] * 0.6)))
                y1 = max(0, int(round(params["cy"] - params["r"] * 2.0)))
                y2 = max(0, int(round(params["cy"] - params["r"] * 0.4)))

            roi = dark[y1:y2, x1:x2] if y2 > y1 and x2 > x1 else None
            if roi is not None and roi.size > 0:
                cnts, _ = cv2.findContours(roi.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                best_rect = None
                for cnt in cnts:
                    rx, ry, rw, rh = cv2.boundingRect(cnt)
                    if rw < 1 or rh < 1:
                        continue
                    elong = (rw / max(1, rh)) if is_horizontal else (rh / max(1, rw))
                    if elong < 1.2:
                        continue
                    area = rw * rh
                    if best_rect is None or area > best_rect[0]:
                        best_rect = (area, rx, ry, rw, rh)
                if best_rect is not None:
                    _, rx, ry, rw, rh = best_rect
                    if is_horizontal:
                        params["arm_x1"] = float(x1 + rx)
                        params["arm_x2"] = float(x1 + rx + rw)
                        y = float(y1 + ry + rh / 2.0)
                        params["arm_y1"] = y
                        params["arm_y2"] = y
                        params["arm_stroke"] = float(max(1.0, rh))
                    else:
                        x = float(x1 + rx + rw / 2.0)
                        params["arm_x1"] = x
                        params["arm_x2"] = x
                        params["arm_y1"] = float(y1 + ry)
                        params["arm_y2"] = float(y1 + ry + rh)
                        params["arm_stroke"] = float(max(1.0, rw))

        params = Action._stabilize_semantic_circle_pose(params, defaults, w, h)

        if params.get("draw_text", True) and params.get("text_mode") in {"path", "path_t"}:
            Action._center_glyph_bbox(params)
        return Action._normalize_light_circle_colors(params)

    @staticmethod
    def make_badge_params(w: int, h: int, base_name: str, img: np.ndarray | None = None) -> dict | None:
        name = get_base_name_from_file(base_name).upper()

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
            Action._center_glyph_bbox(params)
            return params

        if name == "AC0870":
            defaults = Action._default_ac0870_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0870_params_from_image(img, defaults))

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
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_semantic_badge_from_image(img, defaults))

        if name == "AC0811":
            defaults = Action._default_ac0811_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0811_params_from_image(img, defaults))

        if name == "AC0810":
            defaults = Action._default_ac0810_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0810_params_from_image(img, defaults))

        if name == "AC0812":
            defaults = Action._default_ac0812_params(w, h)
            if img is None:
                return Action._enforce_left_arm_badge_geometry(Action._finalize_ac08_style(name, defaults), w, h)
            return Action._enforce_left_arm_badge_geometry(
                Action._finalize_ac08_style(name, Action._fit_ac0812_params_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0813":
            defaults = Action._default_ac0813_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0813_params_from_image(img, defaults))

        if name == "AC0814":
            defaults = Action._default_ac0814_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0814_params_from_image(img, defaults))

        if name == "AC0881":
            defaults = Action._default_ac0881_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_semantic_badge_from_image(img, defaults))

        if name == "AC0882":
            defaults = Action._default_ac0882_params(w, h)
            if img is None:
                return Action._enforce_left_arm_badge_geometry(Action._finalize_ac08_style(name, defaults), w, h)
            return Action._enforce_left_arm_badge_geometry(
                Action._finalize_ac08_style(name, Action._fit_semantic_badge_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0820":
            defaults = Action._apply_co2_label(Action._default_ac0870_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._apply_co2_label(Action._fit_semantic_badge_from_image(img, defaults)))

        if name == "AC0831":
            defaults = Action._apply_co2_label(Action._default_ac0881_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, Action._tune_ac0831_co2_badge(defaults))
            return Action._finalize_ac08_style(
                name,
                Action._tune_ac0831_co2_badge(Action._fit_ac0811_params_from_image(img, defaults)),
            )

        if name == "AC0832":
            defaults = Action._apply_co2_label(Action._default_ac0812_params(w, h))
            if img is None:
                return Action._enforce_left_arm_badge_geometry(
                    Action._finalize_ac08_style(name, Action._tune_ac0832_co2_badge(defaults)),
                    w,
                    h,
                )
            return Action._enforce_left_arm_badge_geometry(
                Action._finalize_ac08_style(
                    name,
                    Action._tune_ac0832_co2_badge(Action._fit_ac0812_params_from_image(img, defaults)),
                ),
                w,
                h,
            )

        if name == "AC0833":
            defaults = Action._tune_ac0833_co2_badge(Action._apply_co2_label(Action._default_ac0813_params(w, h)))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._tune_ac0833_co2_badge(Action._fit_ac0813_params_from_image(img, defaults)))

        if name == "AC0834":
            defaults = Action._apply_co2_label(Action._default_ac0814_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, Action._tune_ac0834_co2_badge(defaults, w, h))
            return Action._finalize_ac08_style(
                name,
                Action._tune_ac0834_co2_badge(
                    Action._fit_ac0814_params_from_image(img, defaults),
                    w,
                    h,
                ),
            )

        if name == "AC0835":
            # AC0835 belongs to the right-arm VOC connector family.
            defaults = Action._apply_voc_label(Action._default_ac0814_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, Action._tune_ac0835_voc_badge(defaults, w, h))
            return Action._finalize_ac08_style(
                name,
                Action._tune_ac0835_voc_badge(
                    Action._fit_ac0814_params_from_image(img, defaults),
                    w,
                    h,
                ),
            )

        if name == "AC0836":
            defaults = Action._apply_voc_label(Action._default_ac0881_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0811_params_from_image(img, defaults))

        if name == "AC0837":
            defaults = Action._apply_voc_label(Action._default_ac0812_params(w, h))
            if img is None:
                return Action._enforce_left_arm_badge_geometry(Action._finalize_ac08_style(name, defaults), w, h)
            return Action._enforce_left_arm_badge_geometry(
                Action._finalize_ac08_style(name, Action._fit_ac0812_params_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0838":
            # AC0838 is part of the right-arm VOC family (same geometry class as
            # AC0814/AC0839), not the top-stem family.
            defaults = Action._apply_voc_label(Action._default_ac0814_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0814_params_from_image(img, defaults))

        if name == "AC0839":
            defaults = Action._apply_voc_label(Action._default_ac0814_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0814_params_from_image(img, defaults))

        return None

    @staticmethod
    def generate_badge_svg(w: int, h: int, p: dict) -> str:
        p = Action._align_stem_to_circle_center(dict(p))
        p = Action._quantize_badge_params(p, w, h)
        elements = [
            f'<svg width="{w}px" height="{h}px" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        ]

        background_fill = p.get("background_fill")
        if background_fill:
            elements.append(
                f'  <rect x="0" y="0" width="{float(w):.4f}" height="{float(h):.4f}" fill="{background_fill}"/>'
            )

        if p.get("arm_enabled"):
            arm_x1 = float(Action._clip_scalar(float(p.get("arm_x1", 0.0)), 0.0, float(w)))
            arm_y1 = float(Action._clip_scalar(float(p.get("arm_y1", p.get("arm_y", 0.0))), 0.0, float(h)))
            arm_x2 = float(Action._clip_scalar(float(p.get("arm_x2", 0.0)), 0.0, float(w)))
            arm_y2 = float(Action._clip_scalar(float(p.get("arm_y2", p.get("arm_y", arm_y1))), 0.0, float(h)))
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
            stem_x = float(Action._clip_scalar(float(p.get("stem_x", 0.0)), 0.0, float(w)))
            stem_top = float(Action._clip_scalar(float(p.get("stem_top", 0.0)), 0.0, float(h)))
            stem_width = max(0.0, min(float(p.get("stem_width", 0.0)), max(0.0, float(w) - stem_x)))
            stem_bottom = float(Action._clip_scalar(float(p.get("stem_bottom", 0.0)), stem_top, float(h)))
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
                layout = Action._co2_layout(p)
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
    def trace_image_segment(
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
            hex_color = rgb_to_hex(color[::-1])

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
    def generate_composite_svg(w: int, h: int, params: dict, folder_path: str, epsilon: float) -> str:
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
                    Action.trace_image_segment(
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
    def render_svg_to_numpy(svg_string: str, size_w: int, size_h: int):
        if SVG_RENDER_SUBPROCESS_ENABLED:
            rendered = _render_svg_to_numpy_via_subprocess(svg_string, size_w, size_h)
            if rendered is not None:
                return rendered
        return _render_svg_to_numpy_inprocess(svg_string, size_w, size_h)

    @staticmethod
    def create_diff_image(
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
    def calculate_error(img_orig: np.ndarray, img_svg: np.ndarray) -> float:
        if img_svg is None:
            return float("inf")
        if img_svg.shape[:2] != img_orig.shape[:2]:
            img_svg = cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
        return float(np.mean(cv2.absdiff(img_orig, img_svg)))

    @staticmethod
    def calculate_delta2_stats(img_orig: np.ndarray, img_svg: np.ndarray) -> tuple[float, float]:
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
    def _fit_to_original_size(img_orig: np.ndarray, img_svg: np.ndarray | None) -> np.ndarray | None:
        if img_svg is None:
            return None
        if img_svg.shape[:2] == img_orig.shape[:2]:
            return img_svg
        return cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)

    @staticmethod
    def _mask_centroid_radius(mask: np.ndarray) -> tuple[float, float, float] | None:
        ys, xs = np.where(mask)
        if xs.size < 5:
            return None
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        r = float(np.sqrt(xs.size / np.pi))
        return cx, cy, r

    @staticmethod
    def _mask_bbox(mask: np.ndarray) -> tuple[float, float, float, float] | None:
        ys, xs = np.where(mask)
        if xs.size < 3:
            return None
        x1, x2 = float(xs.min()), float(xs.max())
        y1, y2 = float(ys.min()), float(ys.max())
        return x1, y1, x2, y2

    @staticmethod
    def _mask_center_size(mask: np.ndarray) -> tuple[float, float, float] | None:
        bbox = Action._mask_bbox(mask)
        if bbox is None:
            return None
        x1, y1, x2, y2 = bbox
        width = max(1.0, (x2 - x1) + 1.0)
        height = max(1.0, (y2 - y1) + 1.0)
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        size = width * height
        return cx, cy, size

    @staticmethod
    def _mask_min_rect_center_diag(mask: np.ndarray) -> tuple[float, float, float] | None:
        mask_u8 = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(mask_u8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(cnt) < 2.0:
            return None

        (cx, cy), (rw, rh), _angle = cv2.minAreaRect(cnt)
        diag = float(math.hypot(float(rw), float(rh)))
        if not math.isfinite(diag) or diag <= 0.0:
            return None
        return float(cx), float(cy), diag

    @staticmethod
    def _element_bbox_change_is_plausible(
        mask_orig: np.ndarray,
        mask_svg: np.ndarray,
    ) -> tuple[bool, str | None]:
        """Reject clearly implausible box drifts between source and converted element."""
        orig_bbox = Action._mask_bbox(mask_orig)
        svg_bbox = Action._mask_bbox(mask_svg)
        if orig_bbox is None or svg_bbox is None:
            return True, None

        ox1, oy1, ox2, oy2 = orig_bbox
        sx1, sy1, sx2, sy2 = svg_bbox

        ow = max(1.0, (ox2 - ox1) + 1.0)
        oh = max(1.0, (oy2 - oy1) + 1.0)
        sw = max(1.0, (sx2 - sx1) + 1.0)
        sh = max(1.0, (sy2 - sy1) + 1.0)

        ocx = (ox1 + ox2) / 2.0
        ocy = (oy1 + oy2) / 2.0
        scx = (sx1 + sx2) / 2.0
        scy = (sy1 + sy2) / 2.0

        center_dist = float(math.hypot(scx - ocx, scy - ocy))
        orig_diag = float(math.hypot(ow, oh))
        max_center_dist = max(2.0, orig_diag * 0.42)

        w_ratio = sw / ow
        h_ratio = sh / oh
        area_ratio = (sw * sh) / max(1.0, ow * oh)

        if center_dist > max_center_dist:
            return (
                False,
                (
                    "Box-Check verworfen "
                    f"(Δcenter={center_dist:.3f} > {max_center_dist:.3f})"
                ),
            )

        if not (0.55 <= w_ratio <= 1.85 and 0.55 <= h_ratio <= 1.85 and 0.40 <= area_ratio <= 2.40):
            return (
                False,
                (
                    "Box-Check verworfen "
                    f"(w_ratio={w_ratio:.3f}, h_ratio={h_ratio:.3f}, area_ratio={area_ratio:.3f})"
                ),
            )

        return True, None

    @staticmethod
    def _apply_element_alignment_step(
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
        scale = float(Action._clip_scalar(diag_scale, 0.85, 1.18))

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
                params["cx"] = float(Action._clip_scalar(old_cx + center_dx * 0.65, 0.0, float(w - 1)))
            if bool(params.get("lock_circle_cy", False)):
                params["cy"] = old_cy
            else:
                params["cy"] = float(Action._clip_scalar(old_cy + center_dy * 0.65, 0.0, float(h - 1)))
            params["r"] = float(Action._clip_scalar(old_r * scale, min_r, max_r))
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
                stem_cx = float(Action._clip_scalar(stem_cx + center_dx * 0.75, 0.0, float(w - 1)))
            new_w = float(Action._clip_scalar(old_w * scale, 1.0, float(w) * 0.22))
            params["stem_width"] = new_w
            params["stem_x"] = float(Action._clip_scalar(stem_cx - (new_w / 2.0), 0.0, float(w) - new_w))
            params["stem_top"] = float(Action._clip_scalar(old_top + center_dy * 0.45, 0.0, float(h - 2)))
            params["stem_bottom"] = float(Action._clip_scalar(old_bottom + center_dy * 0.25, params["stem_top"] + 1.0, float(h - 1)))
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

            params["arm_x1"] = float(Action._clip_scalar(acx - (vx / 2.0), 0.0, float(w - 1)))
            params["arm_x2"] = float(Action._clip_scalar(acx + (vx / 2.0), 0.0, float(w - 1)))
            params["arm_y1"] = float(Action._clip_scalar(acy - (vy / 2.0), 0.0, float(h - 1)))
            params["arm_y2"] = float(Action._clip_scalar(acy + (vy / 2.0), 0.0, float(h - 1)))
            params["arm_stroke"] = float(Action._clip_scalar(old_stroke * scale, 1.0, float(min(w, h)) * 0.18))
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
                params["co2_dy"] = float(Action._clip_scalar(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
                changed = abs(params["co2_dy"] - old_dy) > 0.02
            elif mode == "voc":
                old_dy = float(params.get("voc_dy", 0.0))
                params["voc_dy"] = float(Action._clip_scalar(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
                changed = abs(params["voc_dy"] - old_dy) > 0.02
            elif "ty" in params:
                old_ty = float(params.get("ty", 0.0))
                params["ty"] = float(Action._clip_scalar(old_ty + center_dy * 0.75, 0.0, float(h - 1)))
                changed = abs(params["ty"] - old_ty) > 0.02

        return changed

    @staticmethod
    def _estimate_vertical_stem_from_mask(
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
    def _ring_and_fill_masks(h: int, w: int, params: dict) -> tuple[np.ndarray, np.ndarray]:
        yy, xx = np.indices((h, w))
        dist = np.sqrt((xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2)
        ring_half = max(0.7, params["stroke_circle"])
        ring = np.abs(dist - params["r"]) <= ring_half
        fill = dist <= max(0.5, params["r"] - ring_half)
        return ring, fill

    @staticmethod
    def _mean_gray_for_mask(img: np.ndarray, mask: np.ndarray) -> float | None:
        if int(mask.sum()) == 0:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        vals = gray[mask]
        if vals.size == 0:
            return None
        return float(np.mean(vals))

    @staticmethod
    def _element_region_mask(
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
            x1, y1, x2, y2 = Action._text_bbox(params)
            x1 = max(0.0, x1 - context_pad)
            y1 = max(0.0, y1 - context_pad)
            x2 = min(float(w), x2 + context_pad)
            y2 = min(float(h), y2 + context_pad)
            return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)
        return None

    @staticmethod
    def _text_bbox(params: dict) -> tuple[float, float, float, float]:
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
            layout = Action._co2_layout(params)
            x1 = float(layout["x1"])
            x2 = float(layout["x2"])
            y = float(layout["y_base"])
            height = float(layout["height"])
            return (x1, y - (height / 2.0), x2, y + (height / 2.0))

        # path/path_t fallback via known glyph bounds.
        s = float(params.get("s", 0.0))
        tx = float(params.get("tx", cx))
        ty = float(params.get("ty", cy))
        xmin, ymin, xmax, ymax = Action._glyph_bbox(params.get("text_mode", "path"))
        x1 = tx + (xmin * s)
        y1 = ty + (ymin * s)
        x2 = tx + (xmax * s)
        y2 = ty + (ymax * s)
        return (x1, y1, x2, y2)

    @staticmethod
    def _foreground_mask(img: np.ndarray) -> np.ndarray:
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
    def _circle_from_foreground_mask(fg_mask: np.ndarray) -> tuple[float, float, float] | None:
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
    def _mask_supports_circle(mask: np.ndarray | None) -> bool:
        if mask is None:
            return False
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count < 4:
            return False

        bbox = Action._mask_bbox(mask)
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
    def extract_badge_element_mask(img_orig: np.ndarray, params: dict, element: str) -> np.ndarray | None:
        h, w = img_orig.shape[:2]
        region_mask = Action._element_region_mask(h, w, params, element)
        if region_mask is None:
            return None

        fg_bool = Action._foreground_mask(img_orig)
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
    def _element_only_params(params: dict, element: str) -> dict:
        only = dict(params)
        only["draw_text"] = bool(params.get("draw_text", True) and element == "text")
        only["circle_enabled"] = element == "circle"
        only["stem_enabled"] = bool(params.get("stem_enabled") and element == "stem")
        only["arm_enabled"] = bool(params.get("arm_enabled") and element == "arm")
        return only

    @staticmethod
    def _masked_error(img_orig: np.ndarray, img_svg: np.ndarray, mask: np.ndarray | None) -> float:
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
    def _union_bbox_from_masks(mask_a: np.ndarray | None, mask_b: np.ndarray | None) -> tuple[int, int, int, int] | None:
        boxes: list[tuple[float, float, float, float]] = []
        if mask_a is not None:
            box_a = Action._mask_bbox(mask_a)
            if box_a is not None:
                boxes.append(box_a)
        if mask_b is not None:
            box_b = Action._mask_bbox(mask_b)
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
    def _masked_union_error_in_bbox(
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

        bbox = Action._union_bbox_from_masks(mask_orig, mask_svg)
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
    def _element_match_error(
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

        photo_err = float(Action._masked_union_error_in_bbox(img_orig, img_svg, local_mask_orig, local_mask_svg))
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
            src_circle = Action._mask_centroid_radius(local_mask_orig)
            cand_circle = Action._mask_centroid_radius(local_mask_svg)
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
    def _capture_canonical_badge_colors(params: dict) -> dict:
        p = dict(params)
        p["target_fill_gray"] = int(round(float(p.get("fill_gray", Action.LIGHT_CIRCLE_FILL_GRAY))))
        p["target_stroke_gray"] = int(round(float(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))))
        if p.get("stem_enabled"):
            p["target_stem_gray"] = int(round(float(p.get("stem_gray", p["target_stroke_gray"]))))
        if p.get("draw_text", True) and "text_gray" in p:
            p["target_text_gray"] = int(round(float(p.get("text_gray", Action.LIGHT_CIRCLE_TEXT_GRAY))))
        return p

    @staticmethod
    def _apply_canonical_badge_colors(params: dict) -> dict:
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
    def _circle_bounds(params: dict, w: int, h: int) -> tuple[float, float, float, float, float, float]:
        min_r = float(max(1.0, params.get("min_circle_radius", 1.0)))
        if "circle_radius_lower_bound_px" in params:
            min_r = float(max(min_r, float(params.get("circle_radius_lower_bound_px", min_r))))
        allow_overflow = bool(params.get("allow_circle_overflow", False))
        max_r = max(min_r, float(min(w, h)) * 0.48)
        cx = float(params.get("cx", float(w) / 2.0))
        cy = float(params.get("cy", float(h) / 2.0))
        stroke = float(params.get("stroke_circle", 0.0))
        if allow_overflow:
            max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
        else:
            max_r = min(max_r, Action._max_circle_radius_inside_canvas(cx, cy, w, h, stroke))
        if "max_circle_radius" in params:
            max_r = min(max_r, float(params.get("max_circle_radius", max_r)))
        return 0.0, float(w - 1), 0.0, float(h - 1), min_r, max_r

    @staticmethod
    def _global_parameter_vector_bounds(params: dict, w: int, h: int) -> dict[str, tuple[float, float, bool, str]]:
        """Return central bounds/lock metadata for the shared optimization vector."""
        x_low, x_high, y_low, y_high, r_low, r_high = Action._circle_bounds(params, w, h)
        max_x = float(max(0, w - 1))
        max_y = float(max(0, h - 1))
        text_scale = float(params.get("text_scale", 1.0))
        text_scale_min = float(params.get("text_scale_min", max(0.2, text_scale * 0.5)))
        text_scale_max = float(params.get("text_scale_max", max(text_scale_min, text_scale * 1.8)))
        return {
            "cx": (x_low, x_high, bool(params.get("lock_circle_cx", False)), "canvas"),
            "cy": (y_low, y_high, bool(params.get("lock_circle_cy", False)), "canvas"),
            "r": (r_low, r_high, False, "template/semantic"),
            "arm_x1": (0.0, max_x, bool(params.get("lock_arm", False)), "canvas"),
            "arm_y1": (0.0, max_y, bool(params.get("lock_arm", False)), "canvas"),
            "arm_x2": (0.0, max_x, bool(params.get("lock_arm", False)), "template"),
            "arm_y2": (0.0, max_y, bool(params.get("lock_arm", False)), "template"),
            "arm_stroke": (1.0, max(1.0, min(float(min(w, h)) * 0.20, float(params.get("r", min(w, h))) * 0.9)), bool(params.get("lock_stroke_widths", False)), "semantic"),
            "stem_x": (0.0, max_x, bool(params.get("lock_stem", False)), "template"),
            "stem_top": (0.0, max_y, bool(params.get("lock_stem", False)), "template"),
            "stem_bottom": (0.0, max_y, bool(params.get("lock_stem", False)), "template"),
            "stem_width": (1.0, max(1.0, min(float(w) * 0.25, float(params.get("stem_width_max", float(w) * 0.25)))), bool(params.get("lock_stroke_widths", False)), "semantic"),
            "text_x": (0.0, max_x, bool(params.get("lock_text_position", False)), "template"),
            "text_y": (0.0, max_y, bool(params.get("lock_text_position", False)), "template"),
            "text_scale": (text_scale_min, text_scale_max, bool(params.get("lock_text_scale", False)), "semantic"),
        }

    @staticmethod
    def _log_global_parameter_vector(logs: list[str], params: dict, w: int, h: int, *, label: str) -> None:
        vector = GlobalParameterVector.from_params(params)
        bounds = Action._global_parameter_vector_bounds(params, w, h)

        def _fmt_value(value: float | None) -> str:
            return "-" if value is None else f"{float(value):.3f}"

        entries = []
        for name in (
            "cx",
            "cy",
            "r",
            "arm_x1",
            "arm_y1",
            "arm_x2",
            "arm_y2",
            "arm_stroke",
            "stem_x",
            "stem_top",
            "stem_bottom",
            "stem_width",
            "text_x",
            "text_y",
            "text_scale",
        ):
            low, high, locked, source = bounds[name]
            value = getattr(vector, name)
            entries.append(
                f"{name}={_fmt_value(value)} [{low:.2f},{high:.2f}] lock={'ja' if locked else 'nein'} src={source}"
            )
        logs.append(f"{label}: global_vector " + "; ".join(entries))

    @staticmethod
    def _stochastic_survivor_scalar(
        current_value: float,
        low: float,
        high: float,
        evaluate,
        *,
        snap,
        seed: int,
        iterations: int = 20,
    ) -> tuple[float, float, bool]:
        """Random 3-candidate survivor search for a scalar parameter."""
        cur = float(snap(float(Action._clip_scalar(current_value, low, high))))
        best_value = cur
        best_err = float(evaluate(best_value))
        if not math.isfinite(best_err):
            return best_value, best_err, False

        rng = Action._make_rng(int(seed) + int(Action.STOCHASTIC_SEED_OFFSET))
        span = max(0.5, abs(high - low) * 0.22)
        improved = False
        stable_rounds = 0

        for _ in range(max(1, iterations)):
            candidates = [best_value]
            for _j in range(2):
                sample = float(Action._clip_scalar(rng.normal(best_value, span), low, high))
                candidates.append(float(snap(sample)))

            scored: list[tuple[float, float]] = []
            for cand in candidates:
                err = float(evaluate(cand))
                if math.isfinite(err):
                    scored.append((cand, err))
            if not scored:
                continue
            scored.sort(key=lambda pair: pair[1])
            cand_best, cand_err = scored[0]
            if cand_err + 0.05 < best_err:
                best_value, best_err = cand_best, cand_err
                improved = True
                stable_rounds = 0
            else:
                stable_rounds += 1

            span = max(0.2, span * 0.90)
            if stable_rounds >= 6:
                break

        return best_value, best_err, improved

    @staticmethod
    def _optimize_circle_pose_stochastic_survivor(
        img_orig: np.ndarray,
        params: dict,
        logs: list[str],
        *,
        iterations: int = 24,
    ) -> bool:
        """Stochastic 3-candidate survivor search for circle pose.

        Draw 3 random candidates per round, discard the worst, and continue from
        the best survivor with shrinking perturbation.
        """
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        Action._log_global_parameter_vector(logs, params, w, h, label="circle: survivor-start")
        x_low, x_high, y_low, y_high, r_low, r_high = Action._circle_bounds(params, w, h)
        current = (
            Action._snap_half(float(params.get("cx", (w - 1) / 2.0))),
            Action._snap_half(float(params.get("cy", (h - 1) / 2.0))),
            Action._snap_half(float(params.get("r", max(1.0, min(w, h) * 0.3)))),
        )
        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))
        rng = Action._make_rng(835 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))

        def eval_pose(candidate: tuple[float, float, float]) -> float:
            cx, cy, rad = candidate
            return float(
                Action._element_error_for_circle_pose(
                    img_orig,
                    params,
                    cx_value=cx,
                    cy_value=cy,
                    radius_value=rad,
                )
            )

        best = current
        best_err = eval_pose(best)
        if not math.isfinite(best_err):
            return False

        spread_xy = max(1.0, float(min(w, h)) * 0.10)
        spread_r = max(0.6, float(best[2]) * 0.18)
        improved = False
        stable_rounds = 0

        for _ in range(max(1, iterations)):
            candidates: list[tuple[tuple[float, float, float], float]] = [(best, best_err)]
            for _j in range(2):
                if lock_cx:
                    cx = best[0]
                else:
                    cx = Action._snap_half(float(Action._clip_scalar(rng.normal(best[0], spread_xy), x_low, x_high)))
                if lock_cy:
                    cy = best[1]
                else:
                    cy = Action._snap_half(float(Action._clip_scalar(rng.normal(best[1], spread_xy), y_low, y_high)))
                rad = Action._snap_half(float(Action._clip_scalar(rng.normal(best[2], spread_r), r_low, r_high)))
                cand = (cx, cy, rad)
                candidates.append((cand, eval_pose(cand)))

            finite = [pair for pair in candidates if math.isfinite(pair[1])]
            if not finite:
                continue
            finite.sort(key=lambda item: item[1])
            round_best, round_err = finite[0]
            if round_err + 0.05 < best_err:
                best, best_err = round_best, round_err
                improved = True
                stable_rounds = 0
            else:
                stable_rounds += 1

            spread_xy = max(0.4, spread_xy * 0.92)
            spread_r = max(0.35, spread_r * 0.90)
            if stable_rounds >= 7:
                break

        if not improved:
            logs.append("circle: Stochastic-Survivor keine relevante Verbesserung")
            return False

        updated_vector = GlobalParameterVector.from_params(params)
        updated_vector = dataclasses.replace(updated_vector, cx=best[0], cy=best[1], r=best[2])
        params.update(updated_vector.apply_to_params(params))
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, best[2])
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best[2]
        Action._log_global_parameter_vector(logs, params, w, h, label="circle: survivor-final")
        logs.append(
            f"circle: Stochastic-Survivor übernommen (cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f}, err={best_err:.3f})"
        )
        return True

    @staticmethod
    def _optimize_circle_pose_adaptive_domain(
        img_orig: np.ndarray,
        params: dict,
        logs: list[str],
        *,
        rounds: int = 4,
        samples_per_round: int = 18,
    ) -> bool:
        """Adaptive random-domain search with iterative domain shrinking.

        Strategy:
        1) Start from a broad but plausible 3D domain (cx, cy, r).
        2) Evaluate random samples and keep a near-optimal plateau.
        3) Estimate a surrogate minimum from the plateau center and best sample.
        4) Shrink the domain and repeat.
        """
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        Action._log_global_parameter_vector(logs, params, w, h, label="circle: adaptive-start")
        x_low, x_high, y_low, y_high, r_low, r_high = Action._circle_bounds(params, w, h)
        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))

        current = (
            Action._snap_half(float(params.get("cx", (w - 1) / 2.0))),
            Action._snap_half(float(params.get("cy", (h - 1) / 2.0))),
            Action._snap_half(float(params.get("r", max(1.0, min(w, h) * 0.3)))),
        )

        def clamp_pose(candidate: tuple[float, float, float]) -> tuple[float, float, float]:
            cx, cy, rad = candidate
            if lock_cx:
                cx = current[0]
            else:
                cx = Action._snap_half(float(Action._clip_scalar(cx, x_low, x_high)))
            if lock_cy:
                cy = current[1]
            else:
                cy = Action._snap_half(float(Action._clip_scalar(cy, y_low, y_high)))
            rad = Action._snap_half(float(Action._clip_scalar(rad, r_low, r_high)))
            return cx, cy, rad

        cache: dict[tuple[float, float, float], float] = {}

        def eval_pose(candidate: tuple[float, float, float]) -> float:
            pose = clamp_pose(candidate)
            if pose not in cache:
                cache[pose] = float(
                    Action._element_error_for_circle_pose(
                        img_orig,
                        params,
                        cx_value=pose[0],
                        cy_value=pose[1],
                        radius_value=pose[2],
                    )
                )
            return cache[pose]

        best = clamp_pose(current)
        best_err = eval_pose(best)
        if not math.isfinite(best_err):
            return False

        domain = {
            "cx_low": x_low,
            "cx_high": x_high,
            "cy_low": y_low,
            "cy_high": y_high,
            "r_low": r_low,
            "r_high": r_high,
        }

        rng = Action._make_rng(2027 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))
        improved = False
        flat_plateau_hits = 0

        logs.append(
            (
                "circle: Adaptive-Domain-Suche gestartet "
                f"(Möglichkeitsraum: cx=[{domain['cx_low']:.2f},{domain['cx_high']:.2f}], "
                f"cy=[{domain['cy_low']:.2f},{domain['cy_high']:.2f}], "
                f"r=[{domain['r_low']:.2f},{domain['r_high']:.2f}], "
                f"samples_pro_runde={max(8, int(samples_per_round))})"
            )
        )

        for _round in range(max(1, rounds)):
            samples: list[tuple[tuple[float, float, float], float]] = [(best, best_err)]
            for _ in range(max(8, int(samples_per_round))):
                if lock_cx:
                    cx = current[0]
                else:
                    cx = float(rng.uniform(domain["cx_low"], domain["cx_high"]))
                if lock_cy:
                    cy = current[1]
                else:
                    cy = float(rng.uniform(domain["cy_low"], domain["cy_high"]))
                rad = float(rng.uniform(domain["r_low"], domain["r_high"]))
                pose = clamp_pose((cx, cy, rad))
                samples.append((pose, eval_pose(pose)))

            finite = [pair for pair in samples if math.isfinite(pair[1])]
            if not finite:
                continue
            finite.sort(key=lambda item: item[1])
            round_best, round_best_err = finite[0]

            # Build a near-optimal plateau and use its center as a smooth surrogate.
            plateau_eps = max(0.06, round_best_err * 0.02)
            plateau = [pose for pose, err in finite if err <= round_best_err + plateau_eps]
            if len(plateau) >= 4:
                flat_plateau_hits += 1

            plateau_points = plateau if plateau else [round_best]
            pmin_cx = min(p[0] for p in plateau_points)
            pmin_cy = min(p[1] for p in plateau_points)
            pmin_r = min(p[2] for p in plateau_points)
            pmax_cx = max(p[0] for p in plateau_points)
            pmax_cy = max(p[1] for p in plateau_points)
            pmax_r = max(p[2] for p in plateau_points)
            plateau_mid = clamp_pose(((pmin_cx + pmax_cx) / 2.0, (pmin_cy + pmax_cy) / 2.0, (pmin_r + pmax_r) / 2.0))
            plateau_mid_err = eval_pose(plateau_mid)

            candidate_best = round_best
            candidate_err = round_best_err
            if math.isfinite(plateau_mid_err) and plateau_mid_err < candidate_err:
                candidate_best = plateau_mid
                candidate_err = plateau_mid_err

            if candidate_err + 0.05 < best_err:
                best = candidate_best
                best_err = candidate_err
                improved = True

            logs.append(
                (
                    f"circle: Runde {_round + 1} random-samples={len(samples) - 1}, "
                    f"Error-Minimum={best_err:.3f} bei "
                    f"(cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f})"
                )
            )
            round_vector = GlobalParameterVector.from_params(params)
            round_vector = dataclasses.replace(round_vector, cx=best[0], cy=best[1], r=best[2])
            round_params = round_vector.apply_to_params(params)
            Action._log_global_parameter_vector(logs, round_params, w, h, label=f"circle: Runde {_round + 1}")

            # Iteratively shrink domain around the stable near-optimal region.
            shrink = 0.58
            if not lock_cx:
                half_span = max(0.5, float((domain["cx_high"] - domain["cx_low"]) * shrink * 0.5))
                focus = float(best[0] if len(plateau) <= 1 else (pmin_cx + pmax_cx) / 2.0)
                domain["cx_low"] = max(x_low, focus - half_span)
                domain["cx_high"] = min(x_high, focus + half_span)
            if not lock_cy:
                half_span = max(0.5, float((domain["cy_high"] - domain["cy_low"]) * shrink * 0.5))
                focus = float(best[1] if len(plateau) <= 1 else (pmin_cy + pmax_cy) / 2.0)
                domain["cy_low"] = max(y_low, focus - half_span)
                domain["cy_high"] = min(y_high, focus + half_span)
            half_span_r = max(0.5, float((domain["r_high"] - domain["r_low"]) * shrink * 0.5))
            focus_r = float(best[2] if len(plateau) <= 1 else (pmin_r + pmax_r) / 2.0)
            domain["r_low"] = max(r_low, focus_r - half_span_r)
            domain["r_high"] = min(r_high, focus_r + half_span_r)

            logs.append(
                (
                    f"circle: Runde {_round + 1} Möglichkeitsraum eingegrenzt auf "
                    f"cx=[{domain['cx_low']:.2f},{domain['cx_high']:.2f}], "
                    f"cy=[{domain['cy_low']:.2f},{domain['cy_high']:.2f}], "
                    f"r=[{domain['r_low']:.2f},{domain['r_high']:.2f}]"
                )
            )

        if not improved:
            logs.append("circle: Adaptive-Domain-Suche keine relevante Verbesserung")
            return False

        updated_vector = GlobalParameterVector.from_params(params)
        updated_vector = dataclasses.replace(updated_vector, cx=best[0], cy=best[1], r=best[2])
        params.update(updated_vector.apply_to_params(params))
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, best[2])
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best[2]
        Action._log_global_parameter_vector(logs, params, w, h, label="circle: adaptive-final")

        boundary_hit = (
            (not lock_cx and (abs(best[0] - x_low) <= 0.01 or abs(best[0] - x_high) <= 0.01))
            or (not lock_cy and (abs(best[1] - y_low) <= 0.01 or abs(best[1] - y_high) <= 0.01))
            or abs(best[2] - r_low) <= 0.01
            or abs(best[2] - r_high) <= 0.01
        )
        flat_hint = flat_plateau_hits >= 2
        logs.append(
            "circle: Adaptive-Domain-Suche übernommen "
            f"(cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f}, err={best_err:.3f}, "
            f"rand_optimum={'ja' if boundary_hit else 'nein'}, flaches_optimum={'ja' if flat_hint else 'nein'})"
        )
        return True

    @staticmethod
    def _full_badge_error_for_params(img_orig: np.ndarray, params: dict) -> float:
        """Evaluate full-image error for an already prepared badge parameter dict."""
        h, w = img_orig.shape[:2]
        render = Action._fit_to_original_size(
            img_orig,
            Action.render_svg_to_numpy(Action.generate_badge_svg(w, h, params), w, h),
        )
        if render is None:
            return float("inf")
        return float(Action.calculate_error(img_orig, render))

    @staticmethod
    def _optimize_global_parameter_vector_sampling(
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
        bounds = Action._global_parameter_vector_bounds(params, w, h)
        vector = GlobalParameterVector.from_params(params)

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

        def clamp_vector(candidate: GlobalParameterVector) -> GlobalParameterVector:
            data = dataclasses.asdict(candidate)
            for key in active_keys:
                low, high, _locked, _source = bounds[key]
                current_value = float(data[key])
                clipped = float(Action._clip_scalar(current_value, low, high))
                if key in {"cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y"}:
                    clipped = float(Action._snap_half(clipped))
                data[key] = clipped
            return GlobalParameterVector(**data)

        def eval_vector(candidate: GlobalParameterVector) -> float:
            probe = candidate.apply_to_params(params)
            if probe.get("arm_enabled"):
                Action._reanchor_arm_to_circle_edge(probe, float(probe.get("r", 0.0)))
            if probe.get("stem_enabled"):
                probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe.get("r", 0.0))
                if bool(probe.get("lock_stem_center_to_circle", False)):
                    stem_w = float(probe.get("stem_width", 1.0))
                    probe["stem_x"] = Action._snap_half(
                        max(0.0, min(float(w) - stem_w, float(probe.get("cx", 0.0)) - (stem_w / 2.0)))
                    )
            return Action._full_badge_error_for_params(img_orig, probe)

        def within_hard_bounds(candidate: GlobalParameterVector) -> tuple[bool, str]:
            for key in active_keys:
                low, high, _locked, _source = bounds[key]
                value = float(getattr(candidate, key))
                if value < low - 1e-6 or value > high + 1e-6:
                    return False, f"{key}={value:.3f} außerhalb [{low:.3f}, {high:.3f}]"
            return True, "ok"

        rng = Action._make_rng(4099 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))
        best = clamp_vector(vector)
        best_err = eval_vector(best)
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
                candidate = clamp_vector(GlobalParameterVector(**sample_data))
                candidate_err = eval_vector(candidate)
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
                    centroid = clamp_vector(centroid_raw)
                    centroid_safe, centroid_msg = within_hard_bounds(centroid)
                    if not centroid_safe:
                        logs.append(
                            f"global-search: schwerpunkt verworfen (runde={round_idx + 1}, grund={centroid_msg})"
                        )
                    else:
                        centroid_err = eval_vector(centroid)
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
        params.update(best.apply_to_params(params))
        delta_labels = [
            f"{key} {old_values[key]:.3f}->{new_values[key]:.3f}"
            for key in active_keys
            if abs(new_values[key] - old_values[key]) >= 0.01
        ]
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, float(params.get("r", 0.0)))
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + float(params.get("r", 0.0))
        Action._log_global_parameter_vector(logs, params, w, h, label="global-search: final")
        logs.append(
            "global-search: übernommen "
            f"(best_err={best_err:.3f}, verbessert={', '.join(delta_labels) if delta_labels else 'keine sichtbare delta-liste'})"
        )
        return True

    @staticmethod
    def _enforce_semantic_connector_expectation(base_name: str, semantic_elements: list[str], params: dict, w: int, h: int) -> dict:
        """Restore mandatory connector geometry for directional semantic badges."""
        normalized_base = get_base_name_from_file(str(base_name)).upper()
        normalized_elements = [str(elem).lower() for elem in (semantic_elements or [])]
        expects_left_arm = any("waagrechter strich links" in elem for elem in normalized_elements)
        expects_right_arm = any("waagrechter strich rechts" in elem for elem in normalized_elements)

        # AC0812/AC0837/AC0882 are directional left-arm families. If noisy element
        # extraction temporarily drops arm flags, regenerate canonical connector geometry
        # from the fitted circle before final SVG serialization.
        if normalized_base in {"AC0812", "AC0837", "AC0882"} or expects_left_arm:
            return Action._enforce_left_arm_badge_geometry(params, w, h)
        if normalized_base in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"} or expects_right_arm:
            return Action._enforce_right_arm_badge_geometry(params, w, h)
        return params

    @staticmethod
    def _element_width_key_and_bounds(
        element: str, params: dict, w: int, h: int, img_orig: np.ndarray | None = None
    ) -> tuple[str, float, float] | None:
        lock_strokes = bool(params.get("lock_stroke_widths"))
        min_dim = float(min(w, h))
        if element == "stem" and params.get("stem_enabled"):
            if lock_strokes:
                fixed = float(Action.AC08_STROKE_WIDTH_PX)
                if not bool(params.get("allow_stem_width_tuning", False)):
                    return "stem_width", fixed, fixed
                high = min(
                    float(params.get("stem_width_max", fixed + 1.0)),
                    max(fixed, fixed + float(params.get("stem_width_tuning_px", 1.0))),
                )
                return "stem_width", fixed, max(fixed, high)
            low = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.65)
            high = max(low, min(float(w) * 0.25, float(params.get("stem_width_max", float(w) * 0.25))))
            return "stem_width", low, high
        if element == "arm" and params.get("arm_enabled"):
            if lock_strokes:
                fixed = float(Action.AC08_STROKE_WIDTH_PX)
                return "arm_stroke", fixed, fixed
            low = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.65)
            high = max(low, min(float(min(w, h)) * 0.20, float(params.get("r", min(w, h))) * 0.9))
            return "arm_stroke", low, high
        if element == "circle" and params.get("circle_enabled", True):
            if lock_strokes:
                fixed = float(Action.AC08_STROKE_WIDTH_PX)
                return "stroke_circle", fixed, fixed
            low = max(0.8, float(params.get("stroke_circle", 1.0)) * 0.6)
            high = max(low, min(float(min(w, h)) * 0.22, float(params.get("r", min(w, h))) * 0.9))
            return "stroke_circle", low, high
        if element == "text" and params.get("draw_text", True):
            mode = str(params.get("text_mode", "")).lower()
            if mode == "voc":
                cur = float(params.get("voc_font_scale", 0.52))
                if bool(params.get("lock_text_scale", False)):
                    return "voc_font_scale", cur, cur
                # Start with broad generic bounds so the optimizer can follow
                # text-mask error rather than artificial variant caps.
                low = max(0.30, min(cur * 0.60, 0.45))
                # Keep a broad generic search window unless a specific badge
                # family constrains it via explicit min/max overrides.
                high = 1.60
                if img_orig is not None:
                    text_mask = Action.extract_badge_element_mask(img_orig, params, "text")
                    bbox = Action._mask_bbox(text_mask) if text_mask is not None else None
                    if bbox is not None:
                        x1, y1, x2, y2 = bbox
                        text_w = max(1.0, (float(x2) - float(x1)) + 1.0)
                        text_h = max(1.0, (float(y2) - float(y1)) + 1.0)
                        implied_scale = max(
                            text_w / max(1.0, float(w) * 0.38),
                            text_h / max(1.0, float(h) * 0.18),
                            text_w / max(1.0, float(params.get("r", min_dim)) * 2.8),
                        )
                        low = max(low, min(0.90, implied_scale * 0.70))
                        high = max(high, min(2.40, implied_scale * 1.35))
                if "voc_font_scale_min" in params:
                    low = max(low, float(params["voc_font_scale_min"]))
                if "voc_font_scale_max" in params:
                    high = min(high, float(params["voc_font_scale_max"]))
                return "voc_font_scale", low, max(low, high)
            if mode == "co2":
                cur = float(params.get("co2_font_scale", 0.82))
                if bool(params.get("lock_text_scale", False)):
                    return "co2_font_scale", cur, cur
                # CO₂ labels in large variants can require a noticeably larger font
                # than the historical cap of 1.20 to match the source symbol.
                low = max(0.45, cur * 0.72)
                high = min(1.55, cur * 1.45)
                if "co2_font_scale_min" in params:
                    low = max(low, float(params["co2_font_scale_min"]))
                if "co2_font_scale_max" in params:
                    high = min(high, float(params["co2_font_scale_max"]))
                return "co2_font_scale", low, max(low, high)
        return None

    @staticmethod
    def _element_error_for_width(img_orig: np.ndarray, params: dict, element: str, width_value: float) -> float:
        h, w = img_orig.shape[:2]
        probe = dict(params)
        info = Action._element_width_key_and_bounds(element, probe, w, h, img_orig=img_orig)
        if info is None:
            return float("inf")
        key, low, high = info
        probe[key] = float(Action._clip_scalar(width_value, low, high))
        if key == "stem_width" and probe.get("stem_enabled"):
            probe["stem_x"] = float(probe.get("cx", probe.get("stem_x", 0.0))) - (probe["stem_width"] / 2.0)
        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, element))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")
        mask_orig = Action.extract_badge_element_mask(img_orig, probe, element)
        if mask_orig is None:
            return float("inf")
        return Action._element_match_error(img_orig, elem_render, probe, element, mask_orig=mask_orig)

    @staticmethod
    def _element_error_for_circle_radius(img_orig: np.ndarray, params: dict, radius_value: float) -> float:
        h, w = img_orig.shape[:2]
        if not params.get("circle_enabled", True):
            return float("inf")

        probe = dict(params)
        min_r = float(
            max(
                1.0,
                float(probe.get("min_circle_radius", 1.0)),
                float(probe.get("circle_radius_lower_bound_px", 1.0)),
            )
        )
        max_r = max(min_r, (float(min(w, h)) * 0.48))
        if bool(probe.get("allow_circle_overflow", False)):
            max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
        probe["r"] = float(Action._clip_scalar(radius_value, min_r, max_r))
        probe = Action._clamp_circle_inside_canvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, "circle"))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        # Keep the source mask conservative across radius probes.
        # - For shrink probes, stay anchored to the current radius so we don't
        #   hide missing source pixels (collapse bias, observed on AC0833_L).
        # - For growth probes, expand the source mask context to the larger
        #   radius so underestimated starts (e.g. AC0812_L) can still move up.
        source_mask_params = dict(params)
        source_mask_params["r"] = max(float(params.get("r", 0.0)), float(probe["r"]))
        if source_mask_params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(source_mask_params, float(source_mask_params["r"]))
        if source_mask_params.get("stem_enabled"):
            source_mask_params["stem_top"] = float(source_mask_params.get("cy", 0.0)) + float(source_mask_params["r"])

        mask_orig = Action.extract_badge_element_mask(img_orig, source_mask_params, "circle")
        if mask_orig is None:
            return float("inf")
        mask_svg = Action.extract_badge_element_mask(elem_render, probe, "circle")
        if mask_svg is None:
            return float("inf")

        return Action._element_match_error(
            img_orig,
            elem_render,
            probe,
            "circle",
            mask_orig=mask_orig,
            mask_svg=mask_svg,
        )

    @staticmethod
    def _full_badge_error_for_circle_radius(img_orig: np.ndarray, params: dict, radius_value: float) -> float:
        """Evaluate the full SVG roundtrip error for a specific circle radius."""
        h, w = img_orig.shape[:2]
        if not params.get("circle_enabled", True):
            return float("inf")

        probe = dict(params)
        min_r = float(
            max(
                1.0,
                float(probe.get("min_circle_radius", 1.0)),
                float(probe.get("circle_radius_lower_bound_px", 1.0)),
            )
        )
        max_r = max(min_r, (float(min(w, h)) * 0.48))
        if bool(probe.get("allow_circle_overflow", False)):
            max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
        probe["r"] = float(Action._clip_scalar(radius_value, min_r, max_r))
        probe = Action._clamp_circle_inside_canvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(Action.generate_badge_svg(w, h, probe), w, h))
        if render is None:
            return float("inf")
        return float(Action.calculate_error(img_orig, render))

    @staticmethod
    def _select_circle_radius_plateau_candidate(
        img_orig: np.ndarray,
        params: dict,
        evaluations: dict[float, float],
        current_radius: float,
    ) -> tuple[float, float, float]:
        """Pick a stable radius from a near-optimal plateau instead of a noisy local minimum."""
        finite = sorted((float(radius), float(err)) for radius, err in evaluations.items() if math.isfinite(err))
        if not finite:
            return current_radius, float("inf"), float("inf")

        best_radius, best_err = min(finite, key=lambda pair: pair[1])
        plateau_eps = max(0.06, best_err * 0.02)
        plateau = [(radius, err) for radius, err in finite if err <= best_err + plateau_eps]
        if not plateau:
            try:
                full_err = float(Action._full_badge_error_for_circle_radius(img_orig, params, best_radius))
            except Exception:
                full_err = float("inf")
            return best_radius, best_err, full_err

        plateau_mid = Action._snap_half((plateau[0][0] + plateau[-1][0]) / 2.0)
        candidate_radii = {best_radius, plateau_mid}
        if len(plateau) >= 2:
            candidate_radii.add(plateau[-1][0])

        min_r = float(
            max(
                1.0,
                params.get("min_circle_radius", 1.0),
                params.get("circle_radius_lower_bound_px", 1.0),
            )
        )
        max_r = float(params.get("max_circle_radius", max(radius for radius, _err in finite)))
        if bool(params.get("allow_circle_overflow", False)):
            max_r = max(max_r, min_r + 0.5)
        bounded_candidates = sorted(
            float(Action._clip_scalar(Action._snap_half(float(radius)), min_r, max_r))
            for radius in candidate_radii
        )

        choice_pool: list[tuple[float, float, float, float]] = []
        for radius in bounded_candidates:
            if radius in evaluations:
                elem_err = float(evaluations[radius])
            else:
                try:
                    elem_err = float(Action._element_error_for_circle_radius(img_orig, params, radius))
                except Exception:
                    elem_err = float("inf")
            try:
                full_err = float(Action._full_badge_error_for_circle_radius(img_orig, params, radius))
            except Exception:
                full_err = float("inf")
            if not math.isfinite(elem_err) and not math.isfinite(full_err):
                continue
            distance_to_mid = abs(radius - plateau_mid)
            choice_pool.append((radius, elem_err, full_err, distance_to_mid))

        if not choice_pool:
            return current_radius, best_err, float("inf")

        chosen_radius, chosen_elem_err, chosen_full_err, _distance_to_mid = min(
            choice_pool,
            key=lambda item: (
                round(item[2], 6),
                round(item[1], 6),
                item[3],
                abs(item[0] - current_radius),
            ),
        )
        return chosen_radius, chosen_elem_err, chosen_full_err


    @staticmethod
    def _element_error_for_circle_pose(
        img_orig: np.ndarray,
        params: dict,
        *,
        cx_value: float,
        cy_value: float,
        radius_value: float,
    ) -> float:
        h, w = img_orig.shape[:2]
        if not params.get("circle_enabled", True):
            return float("inf")

        probe = dict(params)
        max_r = max(1.0, (float(min(w, h)) * 0.48))
        probe["cx"] = Action._snap_half(float(Action._clip_scalar(cx_value, 0.0, float(w - 1))))
        probe["cy"] = Action._snap_half(float(Action._clip_scalar(cy_value, 0.0, float(h - 1))))
        min_r = float(max(1.0, probe.get("min_circle_radius", 1.0)))
        probe["r"] = Action._snap_half(float(Action._clip_scalar(radius_value, min_r, max_r)))
        probe = Action._clamp_circle_inside_canvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, "circle"))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        # See `_element_error_for_circle_radius`: use a stable source mask that
        # is independent from the tested candidate pose.
        mask_orig = Action.extract_badge_element_mask(img_orig, params, "circle")
        if mask_orig is None:
            return float("inf")
        mask_svg = Action.extract_badge_element_mask(elem_render, probe, "circle")
        if mask_svg is None:
            return float("inf")

        return Action._element_match_error(
            img_orig,
            elem_render,
            probe,
            "circle",
            mask_orig=mask_orig,
            mask_svg=mask_svg,
        )

    @staticmethod
    def _reanchor_arm_to_circle_edge(params: dict, radius: float) -> None:
        """Keep arm orientation but snap the circle-side endpoint to the new radius."""
        if not params.get("arm_enabled"):
            return
        if not all(k in params for k in ("arm_x1", "arm_y1", "arm_x2", "arm_y2", "cx", "cy")):
            return

        cx = float(params.get("cx", 0.0))
        cy = float(params.get("cy", 0.0))
        x1 = float(params.get("arm_x1", cx))
        y1 = float(params.get("arm_y1", cy))
        x2 = float(params.get("arm_x2", cx))
        y2 = float(params.get("arm_y2", cy))
        arm_stroke = float(max(0.0, params.get("arm_stroke", 0.0)))
        attach_offset = arm_stroke / 2.0

        # Preserve dominant orientation (horizontal vs. vertical).
        is_horizontal = abs(x2 - x1) >= abs(y2 - y1)
        if is_horizontal:
            params["arm_y1"] = cy
            params["arm_y2"] = cy
            p1_dist = abs(x1 - cx)
            p2_dist = abs(x2 - cx)
            if p2_dist <= p1_dist:
                params["arm_x2"] = (cx - radius - attach_offset) if x1 <= cx else (cx + radius + attach_offset)
            else:
                params["arm_x1"] = (cx - radius - attach_offset) if x2 <= cx else (cx + radius + attach_offset)
        else:
            params["arm_x1"] = cx
            params["arm_x2"] = cx
            p1_dist = abs(y1 - cy)
            p2_dist = abs(y2 - cy)
            if p2_dist <= p1_dist:
                params["arm_y2"] = (cy - radius - attach_offset) if y1 <= cy else (cy + radius + attach_offset)
            else:
                params["arm_y1"] = (cy - radius - attach_offset) if y2 <= cy else (cy + radius + attach_offset)

    @staticmethod
    def _optimize_circle_center_bracket(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        current_cx = float(params.get("cx", -1.0))
        current_cy = float(params.get("cy", -1.0))
        current_r = float(params.get("r", 0.0))
        if current_r <= 0.0 or current_cx < 0.0 or current_cy < 0.0:
            return False

        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))
        if lock_cx and lock_cy:
            return False

        max_shift = max(1.0, float(min(w, h)) * 0.16)
        x_low = Action._snap_half(max(0.0, current_cx - max_shift))
        x_high = Action._snap_half(min(float(w - 1), current_cx + max_shift))
        y_low = Action._snap_half(max(0.0, current_cy - max_shift))
        y_high = Action._snap_half(min(float(h - 1), current_cy + max_shift))

        evaluations: dict[tuple[float, float], float] = {}

        def eval_center(cx_value: float, cy_value: float) -> float:
            cx_snap = Action._snap_half(float(Action._clip_scalar(cx_value, 0.0, float(w - 1))))
            cy_snap = Action._snap_half(float(Action._clip_scalar(cy_value, 0.0, float(h - 1))))
            key = (cx_snap, cy_snap)
            if key not in evaluations:
                probe = dict(params)
                probe["cx"] = cx_snap
                probe["cy"] = cy_snap
                evaluations[key] = float(Action._element_error_for_circle_radius(img_orig, probe, current_r))
            return evaluations[key]

        def optimize_axis(low: float, high: float, fixed: float, axis: str) -> float:
            if high - low < 0.05:
                return Action._snap_half((low + high) / 2.0)
            mid = Action._snap_half((low + high) / 2.0)
            for _ in range(8):
                if axis == "x":
                    low_err = eval_center(low, fixed)
                    mid_err = eval_center(mid, fixed)
                    high_err = eval_center(high, fixed)
                else:
                    low_err = eval_center(fixed, low)
                    mid_err = eval_center(fixed, mid)
                    high_err = eval_center(fixed, high)

                if not all(math.isfinite(v) for v in (low_err, mid_err, high_err)):
                    return mid

                if mid_err <= low_err and mid_err <= high_err:
                    if low_err <= high_err:
                        high = mid
                    else:
                        low = mid
                elif low_err <= mid_err and low_err <= high_err:
                    high = mid
                else:
                    low = mid

                if high - low < 0.05:
                    break
                next_mid = Action._snap_half((low + high) / 2.0)
                if abs(next_mid - mid) < 0.02:
                    break
                mid = next_mid
            points = [low, mid, high]
            if axis == "x":
                return min(points, key=lambda v: eval_center(v, fixed))
            return min(points, key=lambda v: eval_center(fixed, v))

        best_cx = current_cx
        best_cy = current_cy
        if not lock_cx:
            best_cx = optimize_axis(x_low, x_high, current_cy, "x")
        if not lock_cy:
            best_cy = optimize_axis(y_low, y_high, best_cx, "y")

        best_err = eval_center(best_cx, best_cy)
        if not math.isfinite(best_err):
            logs.append("circle: Mittelpunkt-Bracketing abgebrochen wegen nicht-finitem Fehler")
            return False

        if abs(best_cx - current_cx) < 0.02 and abs(best_cy - current_cy) < 0.02:
            logs.append(
                f"circle: Mittelpunkt-Bracketing keine relevante Änderung (cx={current_cx:.3f}, cy={current_cy:.3f}, best_err={best_err:.3f})"
            )
            return False

        params["cx"] = best_cx
        params["cy"] = best_cy
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, current_r)
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + current_r
            if bool(params.get("lock_stem_center_to_circle", False)):
                stem_w = float(params.get("stem_width", 1.0))
                params["stem_x"] = Action._snap_half(max(0.0, min(float(w) - stem_w, best_cx - (stem_w / 2.0))))

        logs.append(
            f"circle: Mittelpunkt-Bracketing cx {current_cx:.3f}->{best_cx:.3f}, cy {current_cy:.3f}->{best_cy:.3f} (best_err={best_err:.3f})"
        )
        return True

    @staticmethod
    def _optimize_circle_radius_bracket(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        current = float(params.get("r", 0.0))
        if current <= 0.0:
            return False

        min_dim = float(min(w, h))
        low_bound = max(1.0, min_dim * 0.14)
        low_bound = max(low_bound, float(params.get("min_circle_radius", 1.0)))
        low_bound = max(low_bound, float(params.get("circle_radius_lower_bound_px", 1.0)))
        has_connector = bool(params.get("arm_enabled") or params.get("stem_enabled"))
        if has_connector:
            # Connector badges (AC081x/AC083x families) are geometrically tied to
            # a semantic template. If radius bracketing can dive to the generic
            # min-dimension floor, the circle may detach from that template and
            # the connector degenerates into a tiny corner artifact.
            template_r = float(params.get("template_circle_radius", current))
            low_bound = max(low_bound, template_r * 0.88)
            # Also prevent one-shot collapses from noisy element masks.
            low_bound = max(low_bound, current * 0.90)
        # Tiny badges are especially sensitive to anti-aliasing noise in the
        # circle-only error mask. Prevent aggressive downward jumps that make
        # AC0800_S noticeably smaller than the medium/large variants.
        if min_dim <= 22.0:
            low_bound = max(low_bound, current * 0.9)
        allow_overflow = bool(params.get("allow_circle_overflow", False))
        high_bound = min_dim * 0.48
        if allow_overflow:
            high_bound = max(high_bound, float(max(w, h)) * 1.25, low_bound + 0.5)
        if "max_circle_radius" in params:
            high_bound = min(high_bound, float(params.get("max_circle_radius", high_bound)))
        if not has_connector:
            # Plain circles should use a local bracket around the current
            # estimate; broad global ranges are noisy on tiny crops.
            low_bound = max(low_bound, current - 1.0)
            high_bound = min(high_bound, current + 1.0)
        if not low_bound < high_bound:
            return False

        low = math.floor(low_bound * 2.0) / 2.0
        high = math.ceil(high_bound * 2.0) / 2.0
        low = float(Action._clip_scalar(low, low_bound, high_bound))
        high = float(Action._clip_scalar(high, low_bound, high_bound))
        mid = Action._snap_half(float(Action._clip_scalar(current, low, high)))
        mid = float(Action._clip_scalar(mid, low, high))
        if high - low < 0.05:
            return False

        evaluations: dict[float, float] = {}

        def eval_radius(radius: float) -> float:
            clipped = float(Action._clip_scalar(radius, low_bound, high_bound))
            snapped = float(round(clipped, 3))
            if snapped not in evaluations:
                try:
                    evaluations[snapped] = float(Action._element_error_for_circle_radius(img_orig, params, snapped))
                except Exception:
                    evaluations[snapped] = float("inf")
            return evaluations[snapped]

        max_rounds = 12
        for _ in range(max_rounds):
            low_err = eval_radius(low)
            mid_err = eval_radius(mid)
            high_err = eval_radius(high)
            if not all(math.isfinite(v) for v in (low_err, mid_err, high_err)):
                # Gracefully contract away from unsupported samples (e.g. in
                # tests that patch radius evaluators for a sparse subset).
                if not math.isfinite(high_err) and math.isfinite(mid_err):
                    high = mid
                    continue
                if not math.isfinite(low_err) and math.isfinite(mid_err):
                    low = mid
                    continue
                logs.append(
                    "circle: Radius-Bracketing abgebrochen wegen nicht-finiten Fehlern "
                    + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in sorted(evaluations.items()))
                )
                return False

            # Drei-Punkt-Bracketing: immer den besten Punkt und seinen besseren Nachbarn behalten.
            if mid_err <= low_err and mid_err <= high_err:
                if low_err <= high_err:
                    high = mid
                else:
                    low = mid
            elif low_err <= mid_err and low_err <= high_err:
                high = mid
            else:
                low = mid

            if high - low < 0.05:
                break
            next_mid = Action._snap_half((low + high) / 2.0)
            if abs(next_mid - mid) < 0.02:
                break
            mid = next_mid

        best_r, best_err, best_full_err = Action._select_circle_radius_plateau_candidate(img_orig, params, evaluations, current)
        candidate_dump = ", ".join(f"{v:.3f}->{e:.3f}" for v, e in sorted(evaluations.items()))
        if abs(best_r - current) < 0.02:
            logs.append(
                f"circle: Radius-Bracketing keine relevante Änderung (r: {current:.3f}, best_err={best_err:.3f}, full_err={best_full_err:.3f}); Kandidaten="
                + candidate_dump
            )
            return False

        old_r = current
        params["r"] = best_r
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, best_r)
            # Preserve strictly vertical arm orientation for AC0813/AC0833-like
            # badges: the circle-side endpoint must stay exactly on the circle
            # edge after radius updates.
            ax1 = float(params.get("arm_x1", 0.0))
            ay1 = float(params.get("arm_y1", 0.0))
            ax2 = float(params.get("arm_x2", 0.0))
            ay2 = float(params.get("arm_y2", 0.0))
            if abs(ax1 - ax2) < 1e-6:
                cx = float(params.get("cx", ax1))
                cy = float(params.get("cy", 0.0))
                top_edge = cy - best_r
                bottom_edge = cy + best_r
                params["arm_x1"] = cx
                params["arm_x2"] = cx
                if ay1 <= ay2:
                    params["arm_y2"] = top_edge
                else:
                    params["arm_y1"] = bottom_edge
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best_r

        logs.append(
            f"circle: Radius-Bracketing r {old_r:.3f}->{best_r:.3f} (best_err={best_err:.3f}, full_err={best_full_err:.3f}); Kandidaten="
            + candidate_dump
        )
        return True

    @staticmethod
    def _optimize_circle_pose_multistart(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
        """Jointly optimize circle center+radius via a compact multi-start grid."""
        if not params.get("circle_enabled", True):
            return False

        h, w = img_orig.shape[:2]
        current_cx = float(params.get("cx", -1.0))
        current_cy = float(params.get("cy", -1.0))
        current_r = float(params.get("r", 0.0))
        if current_r <= 0.0 or current_cx < 0.0 or current_cy < 0.0:
            return False

        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))

        shift = max(0.5, float(min(w, h)) * 0.08)
        radius_span = max(0.5, current_r * 0.12)
        _x_low, _x_high, _y_low, _y_high, min_r, max_r = Action._circle_bounds(params, w, h)

        fine_shift = min(1.0, shift)
        fine_radius = min(0.5, radius_span)

        if lock_cx:
            cx_candidates = [float(current_cx)]
        else:
            cx_candidates = [
                float(Action._clip_scalar(current_cx + offset, 0.0, float(w - 1)))
                for offset in (-shift, -fine_shift, 0.0, fine_shift, shift)
            ]
        if lock_cy:
            cy_candidates = [float(current_cy)]
        else:
            cy_candidates = [
                float(Action._clip_scalar(current_cy + offset, 0.0, float(h - 1)))
                for offset in (-shift, -fine_shift, 0.0, fine_shift, shift)
            ]

        r_candidates = [
            float(Action._clip_scalar(current_r + offset, min_r, max_r))
            for offset in (-radius_span, -fine_radius, 0.0, fine_radius, radius_span)
        ]

        evaluations: dict[tuple[float, float, float], float] = {}

        def eval_pose(cx: float, cy: float, rad: float) -> float:
            key = (cx, cy, rad)
            if key not in evaluations:
                evaluations[key] = float(
                    Action._element_error_for_circle_pose(
                        img_orig,
                        params,
                        cx_value=cx,
                        cy_value=cy,
                        radius_value=rad,
                    )
                )
            return evaluations[key]

        best = (float(current_cx), float(current_cy), float(current_r))
        best_err = eval_pose(*best)

        for cx in cx_candidates:
            for cy in cy_candidates:
                for rad in r_candidates:
                    err = eval_pose(cx, cy, rad)
                    if math.isfinite(err) and err + 0.05 < best_err:
                        best = (cx, cy, rad)
                        best_err = err

        best_cx, best_cy, best_r = best
        if (
            abs(best_cx - current_cx) < 0.02
            and abs(best_cy - current_cy) < 0.02
            and abs(best_r - current_r) < 0.02
        ):
            logs.append(
                f"circle: Joint-Multistart keine relevante Änderung (cx={current_cx:.3f}, cy={current_cy:.3f}, r={current_r:.3f}, best_err={best_err:.3f})"
            )
            return False

        params["cx"] = best_cx
        params["cy"] = best_cy
        params["r"] = best_r
        if params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(params, best_r)
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best_r
            if bool(params.get("lock_stem_center_to_circle", False)):
                stem_w = float(params.get("stem_width", 1.0))
                params["stem_x"] = Action._snap_half(max(0.0, min(float(w) - stem_w, best_cx - (stem_w / 2.0))))

        logs.append(
            f"circle: Joint-Multistart cx {current_cx:.3f}->{best_cx:.3f}, cy {current_cy:.3f}->{best_cy:.3f}, r {current_r:.3f}->{best_r:.3f} (best_err={best_err:.3f})"
        )

        at_boundary = (
            (not lock_cx and (best_cx <= 0.01 or best_cx >= float(w - 1) - 0.01))
            or (not lock_cy and (best_cy <= 0.01 or best_cy >= float(h - 1) - 0.01))
            or abs(best_r - min_r) <= 0.01
            or abs(best_r - max_r) <= 0.01
        )
        if at_boundary:
            logs.append("circle: Joint-Multistart liegt am Rand; starte adaptive Domain-Suche")
            improved = Action._optimize_circle_pose_adaptive_domain(img_orig, params, logs)
            if not improved:
                logs.append("circle: Adaptive-Domain-Suche ohne Gewinn; fallback auf stochastic survivor")
                Action._optimize_circle_pose_stochastic_survivor(img_orig, params, logs)
        return True

    @staticmethod
    def _element_error_for_extent(img_orig: np.ndarray, params: dict, element: str, extent_value: float) -> float:
        h, w = img_orig.shape[:2]
        probe = dict(params)

        if element == "stem" and probe.get("stem_enabled"):
            min_len = 1.0
            max_len = float(h)
            new_len = float(Action._clip_scalar(extent_value, min_len, max_len))
            center = (float(probe.get("stem_top", 0.0)) + float(probe.get("stem_bottom", 0.0))) / 2.0
            half = new_len / 2.0
            probe["stem_top"] = float(Action._clip_scalar(center - half, 0.0, float(h - 1)))
            probe["stem_bottom"] = float(Action._clip_scalar(center + half, probe["stem_top"] + 1.0, float(h)))

        elif element == "arm" and probe.get("arm_enabled"):
            x1 = float(probe.get("arm_x1", 0.0))
            y1 = float(probe.get("arm_y1", 0.0))
            x2 = float(probe.get("arm_x2", 0.0))
            y2 = float(probe.get("arm_y2", 0.0))
            dx = x2 - x1
            dy = y2 - y1
            cur_len = float(math.hypot(dx, dy))
            if cur_len <= 1e-6:
                return float("inf")
            new_len = float(Action._clip_scalar(extent_value, 1.0, float(max(w, h))))
            ux = dx / cur_len
            uy = dy / cur_len

            if probe.get("circle_enabled", True) and all(k in probe for k in ("cx", "cy", "r")):
                # Keep the endpoint at the circle edge fixed and optimize the free side
                # length only. Symmetric center-scaling shortens both ends and can make
                # AC0812/AC0814 horizontal connectors visibly too short.
                Action._reanchor_arm_to_circle_edge(probe, float(probe.get("r", 0.0)))
                ax1 = float(probe.get("arm_x1", x1))
                ay1 = float(probe.get("arm_y1", y1))
                ax2 = float(probe.get("arm_x2", x2))
                ay2 = float(probe.get("arm_y2", y2))

                cx = float(probe.get("cx", 0.0))
                cy = float(probe.get("cy", 0.0))
                d1 = float(math.hypot(ax1 - cx, ay1 - cy))
                d2 = float(math.hypot(ax2 - cx, ay2 - cy))

                if d1 <= d2:
                    ix, iy = ax1, ay1
                    probe["arm_x2"] = float(Action._clip_scalar(ix + (ux * new_len), 0.0, float(w - 1)))
                    probe["arm_y2"] = float(Action._clip_scalar(iy + (uy * new_len), 0.0, float(h - 1)))
                else:
                    ix, iy = ax2, ay2
                    probe["arm_x1"] = float(Action._clip_scalar(ix - (ux * new_len), 0.0, float(w - 1)))
                    probe["arm_y1"] = float(Action._clip_scalar(iy - (uy * new_len), 0.0, float(h - 1)))
            else:
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                half = new_len / 2.0
                probe["arm_x1"] = float(Action._clip_scalar(cx - (ux * half), 0.0, float(w - 1)))
                probe["arm_y1"] = float(Action._clip_scalar(cy - (uy * half), 0.0, float(h - 1)))
                probe["arm_x2"] = float(Action._clip_scalar(cx + (ux * half), 0.0, float(w - 1)))
                probe["arm_y2"] = float(Action._clip_scalar(cy + (uy * half), 0.0, float(h - 1)))
        else:
            return float("inf")

        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, element))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        mask_orig = Action.extract_badge_element_mask(img_orig, probe, element)
        if mask_orig is None:
            return float("inf")

        return Action._element_match_error(img_orig, elem_render, probe, element, mask_orig=mask_orig)

    @staticmethod
    def _optimize_element_extent_bracket(img_orig: np.ndarray, params: dict, element: str, logs: list[str]) -> bool:
        h, w = img_orig.shape[:2]
        if element == "stem" and params.get("stem_enabled"):
            current = float(params.get("stem_bottom", 0.0)) - float(params.get("stem_top", 0.0))
            key_label = "stem_len"
            low_bound = 1.0
            high_bound = float(h)
            forced_abs_min = params.get("stem_len_min")
            if forced_abs_min is not None:
                low_bound = max(low_bound, float(forced_abs_min))
            forced_min_ratio = params.get("stem_len_min_ratio")
            if forced_min_ratio is not None:
                min_ratio = float(max(0.0, min(1.0, float(forced_min_ratio))))
                low_bound = max(low_bound, current * min_ratio)
            if h <= 15 and not bool(params.get("draw_text", True)):
                low_bound = max(low_bound, 5.5)
            # Keep bottom-anchored stem variants (e.g. AC0811_S) from collapsing
            # into near-invisible stubs when anti-aliased extraction under-segments
            # thin line pixels in element-only masks.
            is_bottom_anchored = float(params.get("stem_bottom", 0.0)) >= float(h) - 0.5
            if (
                forced_min_ratio is None
                and is_bottom_anchored
                and params.get("circle_enabled", True)
                and all(k in params for k in ("cy", "r"))
            ):
                min_ratio = float(params.get("stem_len_min_ratio", 0.65))
                low_bound = max(low_bound, current * max(0.0, min(1.0, min_ratio)))
                # Tiny AC0811-like badges need a visibly readable stem even when
                # contour extraction underestimates the semantic template length.
                if h <= 15 and not bool(params.get("draw_text", True)):
                    low_bound = max(low_bound, 5.5)
        elif element == "arm" and params.get("arm_enabled"):
            dx = float(params.get("arm_x2", 0.0)) - float(params.get("arm_x1", 0.0))
            dy = float(params.get("arm_y2", 0.0)) - float(params.get("arm_y1", 0.0))
            current = float(math.hypot(dx, dy))
            key_label = "arm_len"
            low_bound = 1.0
            high_bound = float(max(w, h))
            forced_abs_min = params.get("arm_len_min")
            if forced_abs_min is not None:
                low_bound = max(low_bound, float(forced_abs_min))
            forced_min_ratio = params.get("arm_len_min_ratio")
            if forced_min_ratio is not None:
                min_ratio = float(max(0.0, min(1.0, float(forced_min_ratio))))
                low_bound = max(low_bound, current * min_ratio)
            # Keep edge-anchored connector variants (e.g. AC0832_S) from collapsing
            # to tiny stubs when element-only error masks under-segment thin lines.
            is_edge_anchored = any(
                (
                    float(params.get(key, 0.0)) <= 0.5
                    or float(params.get(key, 0.0)) >= float(limit) - 0.5
                )
                for key, limit in (
                    ("arm_x1", w),
                    ("arm_x2", w),
                    ("arm_y1", h),
                    ("arm_y2", h),
                )
            )
            if forced_min_ratio is None and is_edge_anchored and params.get("circle_enabled", True):
                min_ratio = float(params.get("arm_len_min_ratio", 0.75))
                low_bound = max(low_bound, current * max(0.0, min(1.0, min_ratio)))
        else:
            return False

        if current <= 0.0:
            return False

        low = float(low_bound)
        high = float(high_bound)
        if not (low < high):
            logs.append(
                f"{element}: Längen-Bracketing übersprungen ({key_label}: current={current:.3f}, "
                f"Range={low_bound:.3f}..{high_bound:.3f})"
            )
            return False

        candidates = sorted(
            {
                Action._snap_half(low),
                Action._snap_half(low + (high - low) * 0.25),
                Action._snap_half((low + high) / 2.0),
                Action._snap_half(low + (high - low) * 0.75),
                Action._snap_half(high),
                Action._snap_half(Action._clip_scalar(current, low, high)),
            }
        )
        candidate_errors = [Action._element_error_for_extent(img_orig, params, element, v) for v in candidates]
        if not all(math.isfinite(e) for e in candidate_errors):
            logs.append(
                f"{element}: Längen-Bracketing abgebrochen ({key_label}) wegen nicht-finiten Fehlern "
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
            )
            return False

        best_idx = Action._argmin_index(candidate_errors)
        best_len = float(candidates[best_idx])

        boundary_best = abs(best_len - low) < 0.02 or abs(best_len - high) < 0.02
        if boundary_best:
            s_best, s_err, s_improved = Action._stochastic_survivor_scalar(
                current,
                low,
                high,
                lambda v: Action._element_error_for_extent(img_orig, params, element, float(v)),
                snap=Action._snap_half,
                seed=1103 if element == "stem" else 1109,
            )
            if s_improved:
                best_len = float(s_best)
                logs.append(
                    f"{element}: Längen-Stochastic-Survivor aktiviert (best_len={best_len:.3f}, err={s_err:.3f})"
                )

        if abs(best_len - current) < 0.02:
            logs.append(
                f"{element}: Längen-Bracketing keine relevante Änderung ({key_label}: {current:.3f}); "
                f"Kandidaten="
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
            )
            return False

        if element == "stem":
            if params.get("circle_enabled", True) and all(k in params for k in ("cy", "r")):
                # Keep tiny bottom-anchored stems visibly long by preserving the
                # bottom anchor and moving the free top endpoint upward.
                is_bottom_anchored = float(params.get("stem_bottom", 0.0)) >= float(h) - 0.5
                if is_bottom_anchored and h <= 15 and not bool(params.get("draw_text", True)):
                    bottom = float(h)
                    top = float(Action._clip_scalar(bottom - best_len, 0.0, bottom - 1.0))
                    params["stem_top"] = top
                    params["stem_bottom"] = bottom
                else:
                    # Keep the stem attached to the circle edge and optimize only the free end.
                    top = float(Action._clip_scalar(float(params.get("cy", 0.0)) + float(params.get("r", 0.0)), 0.0, float(h - 1)))
                    params["stem_top"] = top
                    params["stem_bottom"] = float(Action._clip_scalar(top + best_len, top + 1.0, float(h)))
            else:
                center = (float(params.get("stem_top", 0.0)) + float(params.get("stem_bottom", 0.0))) / 2.0
                half = best_len / 2.0
                params["stem_top"] = float(Action._clip_scalar(center - half, 0.0, float(h - 1)))
                params["stem_bottom"] = float(Action._clip_scalar(center + half, params["stem_top"] + 1.0, float(h)))
        else:
            x1 = float(params.get("arm_x1", 0.0))
            y1 = float(params.get("arm_y1", 0.0))
            x2 = float(params.get("arm_x2", 0.0))
            y2 = float(params.get("arm_y2", 0.0))
            dx = x2 - x1
            dy = y2 - y1
            cur_len = float(math.hypot(dx, dy))
            if cur_len <= 1e-6:
                return False
            ux = dx / cur_len
            uy = dy / cur_len

            if params.get("circle_enabled", True) and all(k in params for k in ("cx", "cy", "r")):
                Action._reanchor_arm_to_circle_edge(params, float(params.get("r", 0.0)))
                ax1 = float(params.get("arm_x1", x1))
                ay1 = float(params.get("arm_y1", y1))
                ax2 = float(params.get("arm_x2", x2))
                ay2 = float(params.get("arm_y2", y2))

                cx = float(params.get("cx", 0.0))
                cy = float(params.get("cy", 0.0))
                d1 = float(math.hypot(ax1 - cx, ay1 - cy))
                d2 = float(math.hypot(ax2 - cx, ay2 - cy))

                if d1 <= d2:
                    ix, iy = ax1, ay1
                    if abs(uy) <= 0.35:
                        iy = cy
                        ix = cx - float(params.get("r", 0.0)) if ix <= cx else cx + float(params.get("r", 0.0))
                    params["arm_x2"] = float(Action._clip_scalar(ix + (ux * best_len), 0.0, float(w - 1)))
                    params["arm_y2"] = float(Action._clip_scalar(iy + (uy * best_len), 0.0, float(h - 1)))
                    params["arm_x1"] = float(ix)
                    params["arm_y1"] = float(iy)
                else:
                    ix, iy = ax2, ay2
                    if abs(uy) <= 0.35:
                        iy = cy
                        ix = cx - float(params.get("r", 0.0)) if ix <= cx else cx + float(params.get("r", 0.0))
                    params["arm_x1"] = float(Action._clip_scalar(ix - (ux * best_len), 0.0, float(w - 1)))
                    params["arm_y1"] = float(Action._clip_scalar(iy - (uy * best_len), 0.0, float(h - 1)))
                    params["arm_x2"] = float(ix)
                    params["arm_y2"] = float(iy)
            else:
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                half = best_len / 2.0
                params["arm_x1"] = float(Action._clip_scalar(cx - (ux * half), 0.0, float(w - 1)))
                params["arm_y1"] = float(Action._clip_scalar(cy - (uy * half), 0.0, float(h - 1)))
                params["arm_x2"] = float(Action._clip_scalar(cx + (ux * half), 0.0, float(w - 1)))
                params["arm_y2"] = float(Action._clip_scalar(cy + (uy * half), 0.0, float(h - 1)))

        logs.append(
            f"{element}: Längen-Bracketing {key_label} {current:.3f}->{best_len:.3f}; Kandidaten="
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return True

    @staticmethod
    def _optimize_element_width_bracket(img_orig: np.ndarray, params: dict, element: str, logs: list[str]) -> bool:
        h, w = img_orig.shape[:2]
        info = Action._element_width_key_and_bounds(element, params, w, h, img_orig=img_orig)
        if info is None:
            return False

        key, low_bound, high_bound = info
        current = float(params.get(key, 0.0))
        if current <= 0.0:
            return False

        # Breiteres Mehrpunkt-Bracketing über den gesamten plausiblen Bereich.
        low = float(low_bound)
        high = float(high_bound)
        if not (low < high):
            logs.append(
                f"{element}: Breiten-Bracketing übersprungen ({key}: current={current:.3f}, "
                f"Range={low_bound:.3f}..{high_bound:.3f})"
            )
            return False

        if key.endswith("_font_scale"):
            candidates = sorted(
                {
                    round(low, 3),
                    round(low + (high - low) * 0.15, 3),
                    round(low + (high - low) * 0.30, 3),
                    round(low + (high - low) * 0.50, 3),
                    round(low + (high - low) * 0.70, 3),
                    round(low + (high - low) * 0.85, 3),
                    round(high, 3),
                    round(max(low, min(high, current * 0.85)), 3),
                    round(max(low, min(high, current)), 3),
                    round(max(low, min(high, current * 1.15)), 3),
                }
            )
        else:
            candidates = sorted(
                {
                    Action._snap_half(low),
                    Action._snap_half(low + (high - low) * 0.25),
                    Action._snap_half((low + high) / 2.0),
                    Action._snap_half(low + (high - low) * 0.75),
                    Action._snap_half(high),
                    Action._snap_half(Action._clip_scalar(current, low, high)),
                }
            )
        candidate_errors = [Action._element_error_for_width(img_orig, params, element, v) for v in candidates]
        if not all(math.isfinite(e) for e in candidate_errors):
            logs.append(
                f"{element}: Breiten-Bracketing abgebrochen ({key}) wegen nicht-finiten Fehlern "
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
            )
            return False

        best_idx = Action._argmin_index(candidate_errors)
        best_width = candidates[best_idx]

        boundary_best = abs(float(best_width) - low) < 0.02 or abs(float(best_width) - high) < 0.02
        if boundary_best:
            snap_fn = (lambda v: float(round(v, 3))) if key.endswith("_font_scale") else Action._snap_half
            s_best, s_err, s_improved = Action._stochastic_survivor_scalar(
                current,
                low,
                high,
                lambda v: Action._element_error_for_width(img_orig, params, element, float(v)),
                snap=snap_fn,
                seed=1201,
            )
            if s_improved:
                best_width = float(s_best)
                logs.append(
                    f"{element}: Breiten-Stochastic-Survivor aktiviert ({key}={best_width:.3f}, err={s_err:.3f})"
                )

        old = float(params.get(key, current))
        if abs(best_width - old) < 0.02:
            logs.append(
                f"{element}: Breiten-Bracketing keine relevante Änderung ({key}: {old:.3f}); "
                f"Kandidaten="
                + ", ".join(
                    f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False)
                )
            )
            return False

        if key in {"stroke_circle", "arm_stroke", "stem_width"}:
            best_width = Action._snap_int_px(best_width, minimum=1.0)
        elif key.endswith("_font_scale"):
            best_width = float(round(best_width, 3))
        else:
            best_width = Action._snap_half(best_width)

        params[key] = best_width
        if key == "stem_width" and params.get("stem_enabled"):
            params["stem_x"] = Action._snap_half(float(params.get("cx", params.get("stem_x", 0.0))) - (params["stem_width"] / 2.0))
        logs.append(
            f"{element}: Breiten-Bracketing {key} {old:.3f}->{best_width:.3f}; "
            f"Kandidaten="
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return True


    @staticmethod
    def _element_color_keys(element: str, params: dict) -> list[str]:
        if element == "circle" and params.get("circle_enabled", True):
            return ["fill_gray", "stroke_gray"]
        if element == "stem" and params.get("stem_enabled"):
            return ["stem_gray"]
        if element == "arm" and params.get("arm_enabled"):
            return ["stroke_gray"]
        if element == "text" and params.get("draw_text", True):
            return ["text_gray"]
        return []

    @staticmethod
    def _element_error_for_color(
        img_orig: np.ndarray,
        params: dict,
        element: str,
        color_key: str,
        color_value: int,
        mask_orig: np.ndarray,
    ) -> float:
        probe = dict(params)
        probe[color_key] = int(Action._clip_scalar(color_value, 0, 255))

        h, w = img_orig.shape[:2]
        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, element))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        if element == "circle":
            # Color-only circle probing should be photometric against a stable
            # source region. Do not let threshold-induced mask area changes in
            # candidate renders bias toward darker/larger-looking circles.
            return Action._masked_union_error_in_bbox(img_orig, elem_render, mask_orig, mask_orig)

        return Action._element_match_error(
            img_orig,
            elem_render,
            probe,
            element,
            mask_orig=mask_orig,
        )

    @staticmethod
    def _optimize_element_color_bracket(
        img_orig: np.ndarray,
        params: dict,
        element: str,
        mask_orig: np.ndarray,
        logs: list[str],
    ) -> bool:
        if bool(params.get("lock_colors", False)):
            logs.append(f"{element}: Farb-Bracketing übersprungen (Farben gesperrt)")
            return False
        if mask_orig is None or int(mask_orig.sum()) == 0:
            return False

        changed_any = False
        local_gray = Action._mean_gray_for_mask(img_orig, mask_orig)
        sampled = int(round(local_gray)) if local_gray is not None else None

        for color_key in Action._element_color_keys(element, params):
            current = int(round(float(params.get(color_key, 128))))
            low_limit = int(Action._clip_scalar(int(params.get(f"{color_key}_min", 0)), 0, 255))
            high_limit = int(Action._clip_scalar(int(params.get(f"{color_key}_max", 255)), 0, 255))
            if low_limit > high_limit:
                low_limit, high_limit = high_limit, low_limit
            candidates = {
                int(Action._clip_scalar(current - 32, low_limit, high_limit)),
                int(Action._clip_scalar(current - 16, low_limit, high_limit)),
                int(Action._clip_scalar(current - 8, low_limit, high_limit)),
                int(Action._clip_scalar(current, low_limit, high_limit)),
                int(Action._clip_scalar(current + 8, low_limit, high_limit)),
                int(Action._clip_scalar(current + 16, low_limit, high_limit)),
                int(Action._clip_scalar(current + 32, low_limit, high_limit)),
            }
            if sampled is not None:
                candidates.add(int(Action._clip_scalar(sampled, low_limit, high_limit)))
            if element == "circle" and color_key == "fill_gray":
                candidates.update(int(Action._clip_scalar(v, low_limit, high_limit)) for v in {200, 210, 220, 230, 240})
            if color_key in {"stroke_gray", "stem_gray", "text_gray"}:
                candidates.update(int(Action._clip_scalar(v, low_limit, high_limit)) for v in {96, 112, 128, 144, 152, 160, 171})

            values = sorted(v for v in candidates if low_limit <= v <= high_limit)
            errs = [
                Action._element_error_for_color(img_orig, params, element, color_key, v, mask_orig)
                for v in values
            ]
            if not all(math.isfinite(e) for e in errs):
                logs.append(
                    f"{element}: Farb-Bracketing abgebrochen ({color_key}) wegen nicht-finiten Fehlern "
                    + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
                )
                continue

            best_idx = Action._argmin_index(errs)
            best_value = int(values[best_idx])

            if best_value == min(values) or best_value == max(values):
                s_best, s_err, s_improved = Action._stochastic_survivor_scalar(
                    float(current),
                    float(min(values)),
                    float(max(values)),
                    lambda v: Action._element_error_for_color(
                        img_orig,
                        params,
                        element,
                        color_key,
                        int(Action._clip_scalar(int(round(v)), low_limit, high_limit)),
                        mask_orig,
                    ),
                    snap=lambda v: int(Action._clip_scalar(int(round(v)), low_limit, high_limit)),
                    seed=1301,
                )
                if s_improved:
                    best_value = int(Action._clip_scalar(int(round(s_best)), low_limit, high_limit))
                    logs.append(
                        f"{element}: Farb-Stochastic-Survivor aktiviert ({color_key}={best_value}, err={s_err:.3f})"
                    )

            if best_value == current:
                logs.append(
                    f"{element}: Farb-Bracketing keine relevante Änderung ({color_key}: {current}); Kandidaten="
                    + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
                )
                continue

            params[color_key] = int(best_value)
            changed_any = True
            logs.append(
                f"{element}: Farb-Bracketing {color_key} {current}->{best_value}; Kandidaten="
                + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
            )

        return changed_any

    @staticmethod
    def _refine_stem_geometry_from_masks(params: dict, mask_orig: np.ndarray, mask_svg: np.ndarray, w: int) -> tuple[bool, str | None]:
        """Refine stem width/position when validation detects a geometric mismatch."""
        orig_bbox = Action._mask_bbox(mask_orig)
        svg_bbox = Action._mask_bbox(mask_svg)
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
        est = Action._estimate_vertical_stem_from_mask(mask_orig, expected_cx, int(y_start), int(y_end))

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
                target_cx = float(Action._clip_scalar(est_cx, circle_cx - max_offset, circle_cx + max_offset))
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
        target_width = Action._snap_int_px(target_width, minimum=1.0)
        old_x = float(params.get("stem_x", 0.0))
        old_w = float(params.get("stem_width", 1.0))
        new_x = Action._snap_half(max(0.0, min(float(w) - target_width, target_cx - (target_width / 2.0))))
        if abs(target_width - old_w) < 0.05 and abs(new_x - old_x) < 0.05:
            return False, None
        params["stem_width"] = target_width
        params["stem_x"] = new_x
        return True, (
            f"stem: Breitenkorrektur mode={estimate_mode}, ratio={ratio:.3f}, "
            f"alt={old_width:.3f}, neu={target_width:.3f}"
        )

    @staticmethod
    def _expected_semantic_presence(semantic_elements: list[str]) -> dict[str, bool]:
        normalized = [str(elem).lower() for elem in semantic_elements]
        has_text = any(
            ("kreis + buchstabe" in elem)
            or (("buchstab" in elem) and ("ohne buchstabe" not in elem))
            or ("voc" in elem)
            or ("co_2" in elem)
            or ("co₂" in elem)
            for elem in normalized
        )
        has_circle = any("kreis" in elem for elem in normalized)
        return {
            "circle": has_circle,
            "stem": any("senkrechter strich" in elem for elem in normalized),
            "arm": any("waagrechter strich" in elem for elem in normalized),
            "text": has_text,
        }

    @staticmethod
    def _semantic_presence_mismatches(expected: dict[str, bool], observed: dict[str, bool]) -> list[str]:
        labels = {
            "circle": "Kreis",
            "stem": "senkrechter Strich",
            "arm": "waagrechter Strich",
            "text": "Buchstabe/Text",
        }
        issues: list[str] = []
        for key in ("circle", "stem", "arm", "text"):
            exp = bool(expected.get(key, False))
            obs = bool(observed.get(key, False))
            if exp and not obs:
                issues.append(f"Beschreibung erwartet {labels[key]}, im Bild aber nicht robust erkennbar")
            if obs and not exp:
                issues.append(f"Im Bild ist {labels[key]} erkennbar, aber nicht in der Beschreibung enthalten")
        return issues

    @staticmethod
    def _detect_semantic_primitives(
        img_orig: np.ndarray,
        badge_params: dict | None = None,
    ) -> dict[str, bool | int | str]:
        """Detect coarse semantic primitives directly from the raw bitmap.

        This guard is intentionally conservative: it should flag obvious non-badge
        inserts (e.g. arbitrary crossing lines) before we accept semantic badge
        reconstruction from templated defaults.
        """
        h, w = img_orig.shape[:2]
        if h <= 0 or w <= 0:
            return {
                "circle": False,
                "stem": False,
                "arm": False,
                "text": False,
                "circle_detection_source": "none",
                "connector_orientation": "none",
                "horizontal_line_candidates": 0,
                "vertical_line_candidates": 0,
            }

        gray = cv2.cvtColor(img_orig, cv2.COLOR_BGR2GRAY)
        fg_mask = Action._foreground_mask(img_orig).astype(np.uint8)
        min_side = max(1, min(h, w))
        small_variant = bool((badge_params or {}).get("ac08_small_variant_mode", False))
        symbol_hint = str((badge_params or {}).get("badge_symbol_name", "")).upper()
        circle_detection_source = "none"

        # Circle cue: require at least one plausible Hough circle.
        circles = cv2.HoughCircles(
            cv2.GaussianBlur(gray, (5, 5), 0),
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=max(8.0, min_side * 0.30),
            param1=90,
            param2=max(8, int(round(min_side * 0.22))),
            minRadius=max(3, int(round(min_side * 0.12))),
            maxRadius=max(8, int(round(min_side * 0.48))),
        )
        has_circle = False
        circle_geom: tuple[float, float, float] | None = None
        if circles is not None and circles.size > 0:
            circle_candidates = np.round(circles[0, :]).astype(int)
            for cx, cy, radius in circle_candidates:
                r = int(max(3, radius))
                yy, xx = np.ogrid[:h, :w]
                dist = np.sqrt((xx - int(cx)) ** 2 + (yy - int(cy)) ** 2)
                ring = np.abs(dist - float(r)) <= max(1.2, float(r) * 0.20)
                ring_count = int(np.sum(ring))
                if ring_count <= 0:
                    continue

                support = fg_mask[ring] > 0
                support_ratio = float(np.mean(support))
                if support_ratio < 0.24:
                    continue

                # Require broad angular coverage so tiny arcs/noisy crescents
                # cannot pass as semantic circles.
                bins = 12
                coverage_bins = np.zeros(bins, dtype=np.uint8)
                ring_coords = np.argwhere(ring)
                for py, px in ring_coords:
                    if fg_mask[py, px] <= 0:
                        continue
                    ang = math.atan2(float(py - cy), float(px - cx))
                    idx = int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins
                    coverage_bins[idx] = 1
                if int(np.sum(coverage_bins)) < 6:
                    continue

                has_circle = True
                circle_geom = (float(cx), float(cy), float(r))
                circle_detection_source = "hough"
                break

        if not has_circle:
            fallback_circle = Action._circle_from_foreground_mask(fg_mask > 0)
            if fallback_circle is not None:
                has_circle = True
                circle_geom = fallback_circle
                circle_detection_source = "foreground_mask"

        if not has_circle and badge_params:
            # `_S` AC08 families can keep a visually correct ring while Hough and
            # contour-only extraction both fail due to anti-aliased compression.
            # Validate the family template circle directly against foreground ring
            # support so the semantic gate can still accept robust circle evidence.
            if small_variant and symbol_hint in {"AC0811", "AC0814", "AC0870"}:
                exp_cx = float(badge_params.get("cx", float(w) / 2.0))
                exp_cy = float(badge_params.get("cy", float(h) / 2.0))
                exp_r = float(badge_params.get("r", max(2.0, float(min_side) * 0.28)))
                exp_r = float(Action._clip_scalar(exp_r, 2.0, float(min_side) * 0.60))
                yy, xx = np.ogrid[:h, :w]
                ring_tol = max(1.2, exp_r * 0.32)
                ring = np.abs(np.sqrt((xx - exp_cx) ** 2 + (yy - exp_cy) ** 2) - exp_r) <= ring_tol
                ring_count = int(np.count_nonzero(ring))
                if ring_count > 0:
                    support_ratio = float(np.mean(fg_mask[ring] > 0))
                    if support_ratio >= 0.18:
                        bins = 12
                        coverage_bins = np.zeros(bins, dtype=np.uint8)
                        ring_coords = np.argwhere(ring)
                        for py, px in ring_coords:
                            if fg_mask[py, px] <= 0:
                                continue
                            ang = math.atan2(float(py) - exp_cy, float(px) - exp_cx)
                            idx = int(((ang + math.pi) / (2.0 * math.pi)) * bins) % bins
                            coverage_bins[idx] = 1
                        if int(np.sum(coverage_bins)) >= 5:
                            has_circle = True
                            circle_geom = (exp_cx, exp_cy, exp_r)
                            circle_detection_source = "family_fallback"

        # Connector cues: long near-axis-aligned segment via probabilistic Hough.
        has_arm = False
        has_stem = False
        horizontal_candidates = 0
        vertical_candidates = 0
        strongest_horizontal = 0
        strongest_vertical = 0
        edges = cv2.Canny(gray, 45, 140)
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180.0,
            threshold=max(8, int(round(min_side * 0.28))),
            minLineLength=max(6, int(round(float(w) * 0.22))),
            maxLineGap=max(3, int(round(min_side * 0.06))),
        )
        if lines is not None:
            for seg in lines.reshape(-1, 4):
                x1, y1, x2, y2 = [int(v) for v in seg]
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)
                is_horizontal = dx >= max(6, int(round(float(w) * 0.20))) and dy <= max(1, int(round(dx * 0.18)))
                is_vertical = dy >= max(6, int(round(float(h) * 0.20))) and dx <= max(1, int(round(dy * 0.18)))
                if not is_horizontal and not is_vertical:
                    continue
                if circle_geom is not None:
                    cx, cy, radius = circle_geom
                    endpoint_d1 = math.hypot(float(x1) - cx, float(y1) - cy)
                    endpoint_d2 = math.hypot(float(x2) - cx, float(y2) - cy)
                    expanded_r = float(radius) + max(1.5, float(radius) * 0.10)
                    # Ignore short bars that stay inside the circle (e.g. the top
                    # bar of a "T" glyph). A semantic arm must visibly leave the
                    # circle silhouette on at least one side.
                    if endpoint_d1 <= expanded_r and endpoint_d2 <= expanded_r:
                        continue
                    outside_len = 0.0
                    if endpoint_d1 > expanded_r:
                        outside_len += max(0.0, endpoint_d1 - expanded_r)
                    if endpoint_d2 > expanded_r:
                        outside_len += max(0.0, endpoint_d2 - expanded_r)
                    if outside_len < max(2.0, float(w) * 0.08):
                        continue
                    sample_count = max(8, max(dx, dy) + 1)
                    near_ring = 0
                    outside_samples = 0
                    for step in range(sample_count):
                        t = step / max(1, sample_count - 1)
                        sx = float(x1) + (float(x2) - float(x1)) * t
                        sy = float(y1) + (float(y2) - float(y1)) * t
                        dist = math.hypot(sx - cx, sy - cy)
                        if dist > expanded_r:
                            outside_samples += 1
                        if abs(dist - radius) <= max(1.2, float(radius) * 0.16):
                            near_ring += 1
                    # Tiny circle arcs can appear as horizontal line segments in
                    # HoughLinesP. Treat them as ring evidence, not as external arms,
                    # when most samples cling to the circle circumference and only a
                    # small fraction actually leaves the circle silhouette.
                    if near_ring >= int(round(sample_count * 0.55)) and outside_samples <= int(round(sample_count * 0.35)):
                        continue
                    if is_horizontal:
                        # Real semantic arms must sit mostly on one side of the circle.
                        mid_x = (float(x1) + float(x2)) / 2.0
                        if abs(mid_x - cx) < max(1.5, float(radius) * 0.35):
                            continue
                    if is_vertical:
                        # Real semantic stems/vertical arms must sit mostly above or
                        # below the circle rather than through its center.
                        mid_y = (float(y1) + float(y2)) / 2.0
                        if abs(mid_y - cy) < max(1.5, float(radius) * 0.35):
                            continue
                if is_horizontal:
                    has_arm = True
                    horizontal_candidates += 1
                    strongest_horizontal = max(strongest_horizontal, dx)
                if is_vertical:
                    has_stem = True
                    vertical_candidates += 1
                    strongest_vertical = max(strongest_vertical, dy)
                if has_arm and has_stem:
                    break

        # Text cue: several small-ish connected components in center ROI.
        has_text = False
        x1 = max(0, int(round(float(w) * 0.15)))
        x2 = min(w, int(round(float(w) * 0.85)))
        y1 = max(0, int(round(float(h) * 0.20)))
        y2 = min(h, int(round(float(h) * 0.80)))
        roi = fg_mask[y1:y2, x1:x2]
        if roi.size > 0:
            n_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(roi, connectivity=8)
            small_component_count = 0
            total_small_area = 0
            compact_component_count = 0
            max_small_area = max(3, int(round(float(roi.shape[0] * roi.shape[1]) * 0.12)))
            for label_idx in range(1, n_labels):
                area = int(stats[label_idx, cv2.CC_STAT_AREA])
                if 2 <= area <= max_small_area:
                    width = int(stats[label_idx, cv2.CC_STAT_WIDTH])
                    height = int(stats[label_idx, cv2.CC_STAT_HEIGHT])
                    aspect = float(width) / max(1.0, float(height))
                    if circle_geom is not None:
                        cx, cy, radius = circle_geom
                        comp_cx = x1 + float(stats[label_idx, cv2.CC_STAT_LEFT] + (width / 2.0))
                        comp_cy = y1 + float(stats[label_idx, cv2.CC_STAT_TOP] + (height / 2.0))
                        if math.hypot(comp_cx - cx, comp_cy - cy) > float(radius) * 0.72:
                            continue
                    small_component_count += 1
                    total_small_area += area
                    if 0.25 <= aspect <= 4.0:
                        compact_component_count += 1
            has_text = (
                small_component_count >= 2
                and compact_component_count >= 2
                and total_small_area >= max(6, int(round(float(min_side) * 0.45)))
            )

        connector_orientation = "none"
        if strongest_horizontal > 0 and strongest_vertical > 0:
            shorter = min(strongest_horizontal, strongest_vertical)
            longer = max(strongest_horizontal, strongest_vertical)
            if shorter / max(1.0, float(longer)) >= 0.75:
                connector_orientation = "ambiguous"
            elif strongest_vertical > strongest_horizontal:
                connector_orientation = "vertical"
            else:
                connector_orientation = "horizontal"
        elif strongest_vertical > 0:
            connector_orientation = "vertical"
        elif strongest_horizontal > 0:
            connector_orientation = "horizontal"

        return {
            "circle": bool(has_circle),
            "stem": bool(has_stem),
            "arm": bool(has_arm),
            "text": bool(has_text),
            "circle_detection_source": circle_detection_source,
            "connector_orientation": connector_orientation,
            "horizontal_line_candidates": int(horizontal_candidates),
            "vertical_line_candidates": int(vertical_candidates),
        }

    @staticmethod
    def validate_semantic_description_alignment(
        img_orig: np.ndarray,
        semantic_elements: list[str],
        badge_params: dict,
    ) -> list[str]:
        expected = Action._expected_semantic_presence(semantic_elements)
        expected_co2 = any("co_2" in str(elem).lower() or "co₂" in str(elem).lower() for elem in semantic_elements)
        try:
            structural = Action._detect_semantic_primitives(img_orig, badge_params)
        except TypeError:
            # Test doubles may still patch the legacy one-argument variant.
            structural = Action._detect_semantic_primitives(img_orig)
        circle_mask = Action.extract_badge_element_mask(img_orig, badge_params, "circle")
        stem_mask = Action.extract_badge_element_mask(img_orig, badge_params, "stem")
        arm_mask = Action.extract_badge_element_mask(img_orig, badge_params, "arm")
        text_mask = Action.extract_badge_element_mask(img_orig, badge_params, "text")

        def _mask_supports_element(mask: np.ndarray | None, element: str) -> bool:
            if mask is None:
                return False
            pixel_count = int(np.count_nonzero(mask))
            if pixel_count < 3:
                return False
            bbox = Action._mask_bbox(mask)
            if bbox is None:
                return False
            x1, y1, x2, y2 = bbox
            width = max(1.0, (x2 - x1) + 1.0)
            height = max(1.0, (y2 - y1) + 1.0)
            area = width * height
            density = float(pixel_count) / max(1.0, area)
            small_variant = bool(badge_params.get("ac08_small_variant_mode", False))
            if element == "circle":
                if Action._mask_supports_circle(mask):
                    return True
                if small_variant:
                    # `_S` AC08 crops frequently merge anti-aliased ring pixels into a
                    # compact blob. Keep a permissive geometric fallback so robust circle
                    # evidence from the local mask is not rejected only because contour
                    # circularity deteriorates at 15x25px scale.
                    aspect = width / max(1.0, height)
                    return (
                        0.58 <= aspect <= 1.55
                        and density >= 0.34
                        and pixel_count >= 10
                    )
                return False
            if element == "stem":
                ratio = height / max(1.0, width)
                connector_text_badge = str(badge_params.get("text_mode", "")).lower() in {"co2", "voc"}
                if small_variant or connector_text_badge:
                    return pixel_count >= 4 and ratio >= 1.30
                return pixel_count >= 5 and ratio >= 2.2
            if element == "arm":
                ratio = width / max(1.0, height)
                connector_text_badge = str(badge_params.get("text_mode", "")).lower() in {"co2", "voc"}
                if small_variant or connector_text_badge:
                    return pixel_count >= 4 and ratio >= 1.30
                return pixel_count >= 5 and ratio >= 2.2
            if element == "text":
                return pixel_count >= max(4, int(round(min(width, height) * 0.35))) and density >= 0.08
            return pixel_count >= 4

        connector_direction = str(badge_params.get("connector_family_direction", "")).lower()
        arm_is_vertical = bool(
            badge_params.get("arm_enabled", False)
            and abs(float(badge_params.get("arm_x2", 0.0)) - float(badge_params.get("arm_x1", 0.0)))
            <= abs(float(badge_params.get("arm_y2", 0.0)) - float(badge_params.get("arm_y1", 0.0)))
        )
        vertical_connector_family = bool(
            connector_direction == "vertical"
            or (
                expected.get("stem", False)
                and not expected.get("arm", False)
                and (
                    (bool(badge_params.get("stem_enabled", False)) and not bool(badge_params.get("arm_enabled", False)))
                    or arm_is_vertical
                )
            )
        )
        local_support = {
            "circle": _mask_supports_element(circle_mask, "circle"),
            "stem": bool(
                _mask_supports_element(stem_mask, "stem")
                or (
                    vertical_connector_family
                    and bool(badge_params.get("arm_enabled", False))
                    and _mask_supports_element(arm_mask, "stem")
                )
            ),
            "arm": bool(
                not vertical_connector_family
                and _mask_supports_element(arm_mask, "arm")
            ),
            "text": _mask_supports_element(text_mask, "text"),
        }
        allow_circle_mask_fallback = expected.get("circle", False) and not (
            expected.get("stem", False) or expected.get("arm", False) or expected.get("text", False)
        )
        connector_circle_mask_fallback = bool(
            expected.get("circle", False)
            and vertical_connector_family
            and local_support["circle"]
            and not local_support["arm"]
        )
        small_connector_circle_mask_fallback = bool(
            expected.get("circle", False)
            and bool(badge_params.get("ac08_small_variant_mode", False))
            and local_support["circle"]
            and (expected.get("stem", False) or expected.get("arm", False))
        )
        plain_circle_badge = bool(
            expected.get("circle", False)
            and not expected.get("stem", False)
            and not expected.get("arm", False)
            and not expected.get("text", False)
            and not bool(badge_params.get("stem_enabled", False))
            and not bool(badge_params.get("arm_enabled", False))
            and not bool(badge_params.get("draw_text", False))
        )
        require_circle_mask_confirmation = expected.get("circle", False) and not (
            allow_circle_mask_fallback or connector_circle_mask_fallback
        )
        suppress_structural_stem_for_horizontal_connector = bool(
            expected.get("arm", False)
            and not expected.get("stem", False)
            and local_support["arm"]
            and not local_support["stem"]
        )
        observed = {
            "circle": bool(
                (structural.get("circle", False) and (local_support["circle"] if require_circle_mask_confirmation else True))
                or (allow_circle_mask_fallback and local_support["circle"])
                or connector_circle_mask_fallback
                or small_connector_circle_mask_fallback
            ),
            "stem": bool(
                local_support["stem"]
                or (
                    structural.get("stem", False)
                    and not plain_circle_badge
                    and not suppress_structural_stem_for_horizontal_connector
                )
            ),
            "arm": bool(
                local_support["arm"]
                or (
                    structural.get("arm", False)
                    and not structural.get("stem", False)
                    and not plain_circle_badge
                    and not (
                        vertical_connector_family
                        and expected.get("arm", False) is False
                        and local_support["circle"]
                        and local_support["arm"] is False
                    )
                )
            ),
            "text": bool(local_support["text"] or (structural.get("text", False) and not plain_circle_badge)),
        }
        issues = Action._semantic_presence_mismatches(expected, observed)
        if expected.get("circle") and not observed["circle"]:
            issues.append("Strukturprüfung: Kein belastbarer Kreis-Kandidat im Rohbild erkannt")
        if expected.get("arm") and not observed["arm"]:
            issues.append("Strukturprüfung: Kein belastbarer waagrechter Linien-Kandidat im Rohbild erkannt")
        if expected.get("text") and not observed["text"]:
            issues.append("Strukturprüfung: Keine belastbare Textstruktur (z.B. CO₂) im Rohbild erkannt")
        if expected_co2 and expected.get("text"):
            if text_mask is None:
                issues.append("Strukturprüfung: CO₂-Textregion enthält keine verwertbaren Vordergrundpixel")
            else:
                ys, xs = np.where(text_mask)
                if ys.size == 0 or xs.size == 0:
                    issues.append("Strukturprüfung: CO₂-Textregion konnte nicht lokalisiert werden")
                else:
                    x1, x2 = int(xs.min()), int(xs.max())
                    y1, y2 = int(ys.min()), int(ys.max())
                    roi = Action._foreground_mask(img_orig)[y1 : y2 + 1, x1 : x2 + 1].astype(np.uint8)
                    n_labels, _labels, stats, _centroids = cv2.connectedComponentsWithStats(roi, connectivity=8)
                    compact = 0
                    merged_text_blob = False
                    roi_h, roi_w = roi.shape[:2]
                    roi_area = max(1, roi_h * roi_w)
                    for idx in range(1, n_labels):
                        area = int(stats[idx, cv2.CC_STAT_AREA])
                        if area < 2:
                            continue
                        width = int(stats[idx, cv2.CC_STAT_WIDTH])
                        height = int(stats[idx, cv2.CC_STAT_HEIGHT])
                        aspect = float(width) / max(1.0, float(height))
                        if 0.2 <= aspect <= 4.5:
                            compact += 1
                            density = float(area) / max(1.0, float(width * height))
                            coverage = float(area) / float(roi_area)
                            # JPEG anti-aliasing can merge the full CO₂ cluster into
                            # a single compact foreground island, especially in
                            # elongated connector badges such as AC0831_L. Accept
                            # that case when the blob is large/dense enough to be a
                            # plausible merged text cluster instead of noise.
                            if (
                                compact == 1
                                and 0.75 <= aspect <= 1.80
                                and density >= 0.30
                                and coverage >= 0.18
                            ):
                                merged_text_blob = True
                    if compact < 2 and not merged_text_blob:
                        issues.append("Strukturprüfung: Erwartete CO₂-Glyphenstruktur nicht ausreichend belegt")
        return issues

    @staticmethod
    def validate_badge_by_elements(
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

        def _stagnation_fingerprint(current_params: dict) -> tuple[tuple[str, float], ...]:
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
                elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(params, element))
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
                    elem_focus_mask = Action._element_region_mask(h, w, params, element)
                    elem_diff = Action.create_diff_image(img_orig, elem_render, elem_focus_mask)
                    cv2.imwrite(
                        os.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_{element}_diff.png"),
                        elem_diff,
                    )

                elem_err = Action._element_match_error(img_orig, elem_render, params, element, mask_orig=mask_orig, mask_svg=mask_svg)
                logs.append(f"{element}: Fehler={elem_err:.3f}")

                if element == "stem" and params.get("stem_enabled"):
                    changed, refine_log = Action._refine_stem_geometry_from_masks(params, mask_orig, mask_svg, w)
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

            current_round_state = (_stagnation_fingerprint(params), round(float(full_err), 6))
            if previous_round_state is not None:
                same_fingerprint = current_round_state[0] == previous_round_state[0]
                nearly_same_error = abs(current_round_state[1] - previous_round_state[1]) <= 1e-6
                if same_fingerprint and nearly_same_error:
                    logs.append(
                        "stagnation_detected: identischer Parameter-Fingerprint und praktisch unveränderter Gesamtfehler"
                    )
                    adaptive_unlock_applied = Action._activate_ac08_adaptive_locks(
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
                        Action._release_ac08_adaptive_locks(
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
                Action._release_ac08_adaptive_locks(
                    params,
                    logs,
                    reason="high_residual_error",
                    current_error=full_err,
                )

            if round_idx + 1 >= max_rounds:
                break

            if not round_changed:
                adaptive_unlock_applied = Action._activate_ac08_adaptive_locks(
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


def _semantic_quality_flags(base_name: str, validation_logs: list[str]) -> list[str]:
    """Derive non-fatal quality markers from semantic element-validation logs.

    Semantic structure checks can pass even when one fitted element is still a
    visually weak match. We keep the conversion successful, but annotate such
    cases in the per-image validation log so downstream review can spot them.
    """

    if get_base_name_from_file(base_name).upper() != "AC0811":
        return []

    error_pattern = re.compile(r"^(circle|stem|arm|text): Fehler=([0-9]+(?:\.[0-9]+)?)$")
    element_errors: dict[str, float] = {}
    for entry in validation_logs:
        match = error_pattern.match(str(entry).strip())
        if not match:
            continue
        element_errors[match.group(1)] = float(match.group(2))

    if not element_errors:
        return []

    highest_element, highest_error = max(element_errors.items(), key=lambda item: item[1])
    elevated = [name for name, value in element_errors.items() if value >= 8.0]

    if highest_error < 10.0 and len(elevated) < 2:
        return []

    markers = [
        "quality=borderline",
        (
            "quality_reason="
            f"semantic_ok_trotz_hohem_elementfehler:{highest_element}={highest_error:.3f}"
        ),
    ]
    if elevated:
        markers.append("quality_elevated_elements=" + ",".join(sorted(elevated)))
    return markers


def run_iteration_pipeline(
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
    if get_base_name_from_file(perc.base_name).upper() in semantic_audit_targets:
        semantic_audit_row = _semantic_audit_record(
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

    def _write_validation_log(lines: list[str]) -> None:
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

    def _params_snapshot(snapshot: dict[str, object]) -> str:
        return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, default=str)

    def _record_render_failure(reason: str, *, svg_content: str | None = None, params_snapshot: dict[str, object] | None = None) -> None:
        if svg_content:
            _write_attempt_artifacts(svg_content, failed=True)
        lines = [
            "status=render_failure",
            f"failure_reason={reason}",
            f"filename={filename}",
        ]
        if svg_content:
            lines.append(f"best_attempt_svg={base}_failed.svg")
        if params_snapshot is not None:
            lines.append("params_snapshot=" + _params_snapshot(params_snapshot))
        _write_validation_log(lines)

    def _write_attempt_artifacts(svg_content: str, rendered_img=None, diff_img=None, *, failed: bool = False) -> None:
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
            _write_attempt_artifacts(failed_svg, failed=True)
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
                semantic_audit_row = _semantic_audit_record(
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
            _write_validation_log(
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
        quality_flags = _semantic_quality_flags(perc.base_name, validation_logs)
        if semantic_audit_row is not None:
            semantic_audit_row = _semantic_audit_record(
                base_name=perc.base_name,
                filename=filename,
                description_fragments=list(params.get("description_fragments", [])),
                semantic_elements=list(params.get("elements", [])),
                status="semantic_ok",
                semantic_priority_order=list(params.get("semantic_priority_order", [])),
                semantic_conflicts=list(params.get("semantic_conflicts", [])),
                semantic_sources=dict(params.get("semantic_sources", {})),
            )
        _write_validation_log(
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
            _record_render_failure(
                "semantic_badge_final_render_failed",
                svg_content=svg_content,
                params_snapshot=badge_params,
            )
            return None
        _write_attempt_artifacts(svg_content, svg_rendered)
        if semantic_audit_row is not None:
            params = copy.deepcopy(params)
            params["semantic_audit"] = semantic_audit_row
        return base, desc, params, 1, Action.calculate_error(perc.img, svg_rendered)

    if params["mode"] != "composite":
        print("  -> Überspringe Bild, da keine Zerschneide-Anweisung (Compositing) im Text vorliegt.")
        _write_validation_log(["status=skipped_non_composite"])
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
            _record_render_failure(
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
        _write_attempt_artifacts(best_svg, diff_img=best_diff)

    _write_validation_log([
        "status=composite_ok",
        f"convergence={stop_reason}",
        f"best_iter={int(best_iter)}",
        f"best_error={float(best_error):.6f}",
    ])
    return base, desc, params, best_iter, best_error


def _extract_ref_parts(name: str) -> tuple[str, int] | None:
    match = re.match(r"^([A-Z]{2,3})(\d{3,4})$", name.upper())
    if not match:
        return None
    return match.group(1), int(match.group(2))


def _normalize_range_token(value: str) -> str:
    base = get_base_name_from_file(str(value or "").upper())
    return re.sub(r"[^A-Z0-9]", "", base)


def _compact_range_token(value: str) -> str:
    token = _normalize_range_token(value)
    match = re.match(r"^([A-Z]+)(\d+)$", token)
    if not match:
        return token
    letters, digits = match.groups()
    return f"{letters[0]}{digits}"


def _shared_partial_range_token(start_ref: str, end_ref: str) -> str:
    start_token = _normalize_range_token(start_ref)
    end_token = _normalize_range_token(end_ref)
    compact_start = _compact_range_token(start_ref)
    compact_end = _compact_range_token(end_ref)
    if not start_token or not end_token:
        return ""
    for left, right in ((start_token, end_token), (compact_start, compact_end)):
        if left and left == right:
            return left
        if left and left in right:
            return left
        if right and right in left:
            return right

        max_len = min(len(left), len(right))
        for length in range(max_len, 2, -1):
            for idx in range(0, len(left) - length + 1):
                candidate = left[idx: idx + length]
                if candidate in right:
                    return candidate
    return ""


def _matches_partial_range_token(filename: str, start_ref: str, end_ref: str) -> bool:
    token = _shared_partial_range_token(start_ref, end_ref)
    if not token:
        return False
    stem = _normalize_range_token(get_base_name_from_file(os.path.splitext(filename)[0]))
    if not stem:
        return False
    if token in stem:
        return True

    pos = 0
    for char in stem:
        if pos < len(token) and char == token[pos]:
            pos += 1
    return pos == len(token)


def _extract_symbol_family(name: str) -> str | None:
    """Extract 2-3 letter corpus family prefixes such as AC, GE, DLG, or NAV."""
    match = re.match(r"^([A-Z]{2,3})\d{3,4}$", str(name).upper())
    if not match:
        return None
    return match.group(1)


def _matches_exact_prefix_filter(filename: str, start_ref: str, end_ref: str) -> bool:
    start_token = _normalize_range_token(start_ref)
    end_token = _normalize_range_token(end_ref)
    if not start_token or start_token != end_token:
        return False
    stem = _normalize_range_token(get_base_name_from_file(os.path.splitext(filename)[0]))
    if not stem:
        return False
    return stem.startswith(start_token)


def _in_requested_range(filename: str, start_ref: str, end_ref: str) -> bool:
    stem = get_base_name_from_file(os.path.splitext(filename)[0]).upper()
    stem_parts = _extract_ref_parts(stem)
    start_parts = _extract_ref_parts(start_ref)
    end_parts = _extract_ref_parts(end_ref)

    # Identical start/end filters should also work as a prefix selector so an
    # input like AC081..AC081 includes AC0814_L, AC0813_M, etc.
    if _matches_exact_prefix_filter(filename, start_ref, end_ref):
        return True

    # If no parseable range bounds are provided, fall back to a shared partial
    # token filter. This keeps interactive batches small, e.g. AC08..A08 -> A08*.
    if start_parts is None and end_parts is None:
        return _matches_partial_range_token(filename, start_ref, end_ref) if (start_ref or end_ref) else True

    # Files that do not follow the usual XX0000 / XXX0000 naming scheme should
    # only pass through broad whole-folder spans, not exact family-specific
    # filters like AC0811..AC0811.
    if stem_parts is None:
        if start_parts is not None and end_parts is not None:
            start_key = start_parts
            end_key = end_parts
            if start_key > end_key:
                start_key, end_key = end_key, start_key
            return start_key[0] != end_key[0]
        return False

    # Support one-sided range filters if only one boundary can be parsed.
    if start_parts is None:
        return stem_parts <= end_parts  # type: ignore[operator]
    if end_parts is None:
        return start_parts <= stem_parts

    start_key = start_parts
    end_key = end_parts
    if start_key > end_key:
        start_key, end_key = end_key, start_key

    return start_key <= stem_parts <= end_key




def _conversion_random() -> random.Random:
    """Return run-local RNG (seedable via env) for non-deterministic search order."""
    seed_raw = os.environ.get("TINY_ICC_RANDOM_SEED")
    if seed_raw is not None and str(seed_raw).strip() != "":
        try:
            return random.Random(int(str(seed_raw).strip()))
        except ValueError:
            pass
    return random.Random(time.time_ns())

def _default_converted_symbols_root() -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(repo_root, "artifacts", "converted_images")


def _converted_svg_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "converted_svgs")


def _read_validation_log_details(log_path: str) -> dict[str, str]:
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


def _write_batch_failure_summary(reports_out_dir: str, failures: list[dict[str, str]]) -> None:
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



def _collect_description_fragments(raw_desc: dict[str, str], base_name: str, img_filename: str) -> list[dict[str, str]]:
    """Return the ordered description fragments consulted for one variant lookup."""
    variant_name = os.path.splitext(img_filename)[0]
    canonical_base = get_base_name_from_file(base_name).upper()
    canonical_variant = get_base_name_from_file(variant_name).upper()

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


def _semantic_audit_record(
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
    """Build a normalized semantic-audit record for AC0811..AC0814 style families."""
    mismatch_reasons = [str(reason) for reason in (mismatch_reasons or []) if str(reason).strip()]
    joined_description = " ".join(fragment["text"] for fragment in description_fragments).strip()
    return {
        "filename": str(filename),
        "base_name": get_base_name_from_file(base_name).upper(),
        "description_fragments": description_fragments,
        "recognized_description_elements": [fragment["text"] for fragment in description_fragments],
        "description_lookup_keys": [fragment["key"] for fragment in description_fragments],
        "description_text": joined_description,
        "derived_elements": [str(element) for element in semantic_elements],
        "semantic_priority_order": [str(item) for item in (semantic_priority_order or [])],
        "semantic_conflicts": [str(item) for item in (semantic_conflicts or [])],
        "semantic_sources": dict(semantic_sources or {}),
        "status": str(status),
        "mismatch_reason": " | ".join(mismatch_reasons),
        "mismatch_reasons": mismatch_reasons,
    }


def _write_semantic_audit_report(reports_out_dir: str, audit_rows: list[dict[str, object]]) -> None:
    """Persist semantic audit rows as CSV/JSON for targeted AC0811..AC0814 review."""
    if not audit_rows:
        return

    csv_path = os.path.join(reports_out_dir, "semantic_audit_ac0811_ac0814.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "filename",
                "base_name",
                "description_lookup_keys",
                "recognized_description_elements",
                "description_text",
                "derived_elements",
                "semantic_priority_order",
                "semantic_conflicts",
                "status",
                "mismatch_reason",
            ]
        )
        for row in audit_rows:
            writer.writerow(
                [
                    row.get("filename", ""),
                    row.get("base_name", ""),
                    " | ".join(str(value) for value in row.get("description_lookup_keys", [])),
                    " | ".join(str(value) for value in row.get("recognized_description_elements", [])),
                    row.get("description_text", ""),
                    " | ".join(str(value) for value in row.get("derived_elements", [])),
                    " > ".join(str(value) for value in row.get("semantic_priority_order", [])),
                    " | ".join(str(value) for value in row.get("semantic_conflicts", [])),
                    row.get("status", ""),
                    row.get("mismatch_reason", ""),
                ]
            )

    json_path = os.path.join(reports_out_dir, "semantic_audit_ac0811_ac0814.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit_rows, f, ensure_ascii=False, indent=2)


def _diff_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "diff_pngs")


def _reports_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "reports")


def _is_semantic_template_variant(base_name: str, params: dict[str, object] | None = None) -> bool:
    """Return whether an existing converted SVG should participate as semantic donor."""
    normalized = str(get_base_name_from_file(base_name or "")).upper()
    if not normalized:
        return False
    if normalized.startswith("AC08") or normalized in {"AR0100"}:
        return True
    if isinstance(params, dict) and str(params.get("mode", "")).lower() == "semantic_badge":
        return True
    return False


def _load_existing_conversion_rows(output_root: str, folder_path: str) -> list[dict[str, object]]:
    """Load previously converted variants so they can act as donor templates.

    This lets an earlier conversion batch (for example the already converted
    ``AC08*`` symbols) improve later runs without requiring a fresh full pass.
    """
    reports_path = Path(_reports_output_dir(output_root)) / "Iteration_Log.csv"
    svg_out_dir = Path(_converted_svg_output_dir(output_root))
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

                geometry = _read_svg_geometry(str(svg_path))
                if geometry is None:
                    continue
                w, h, params = geometry
                base = get_base_name_from_file(variant).upper()
                if _is_semantic_template_variant(base, params):
                    params["mode"] = "semantic_badge"

                error_per_pixel_raw = str(raw_row.get("FehlerProPixel", "")).strip().replace(",", ".")
                diff_score_raw = str(raw_row.get("Diff-Score", "")).strip().replace(",", ".")
                best_iter_raw = str(raw_row.get("Beste Iteration", "")).strip()
                image_path = Path(folder_path) / filename
                if image_path.exists():
                    try:
                        width, height = _sniff_raster_size(image_path)
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


def _sniff_raster_size(path: str | Path) -> tuple[int, int]:
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


def _svg_href_mime_type(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def _render_embedded_raster_svg(input_path: str | Path) -> str:
    width, height = _sniff_raster_size(input_path)
    raw = Path(input_path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    mime = _svg_href_mime_type(input_path)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <image width="{width}" height="{height}" href="data:{mime};base64,{encoded}"/>\n'
        "</svg>\n"
    )


def _quality_config_path(reports_out_dir: str) -> str:
    return os.path.join(reports_out_dir, "quality_tercile_config.json")


def _load_quality_config(reports_out_dir: str) -> dict[str, object]:
    path = _quality_config_path(reports_out_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_quality_config(
    reports_out_dir: str,
    *,
    allowed_error_per_pixel: float,
    skipped_variants: list[str],
    source: str,
) -> None:
    path = _quality_config_path(reports_out_dir)
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


def _quality_sort_key(row: dict[str, object]) -> float:
    value = float(row.get("error_per_pixel", float("inf")))
    if math.isfinite(value):
        return value
    return float("inf")




def _compute_successful_conversions_error_threshold(
    rows: list[dict[str, object]],
    successful_variants: list[str] | tuple[str, ...] | None = None,
) -> float:
    """Return mean(error_per_pixel) + 2*std(error_per_pixel) for successful rows.

    The successful set is sourced from ``successful_conversions.txt`` (via
    ``SUCCESSFUL_CONVERSIONS``) unless explicitly provided. Returns ``inf`` when
    no finite samples are available.
    """
    selected = {str(v).strip().upper() for v in (successful_variants or SUCCESSFUL_CONVERSIONS) if str(v).strip()}
    if not selected:
        return float("inf")

    values: list[float] = []
    for row in rows:
        variant = str(row.get("variant", "")).strip().upper()
        if variant not in selected:
            continue
        err = float(row.get("error_per_pixel", float("inf")))
        if math.isfinite(err):
            values.append(err)

    if not values:
        return float("inf")

    mean_val = float(statistics.fmean(values))
    std_val = float(statistics.pstdev(values)) if len(values) > 1 else 0.0
    return float(mean_val + 2.0 * std_val)


def _select_middle_lower_tercile(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if len(rows) < 3:
        return []

    ranked = sorted(rows, key=_quality_sort_key)
    first_cut = max(1, len(ranked) // 3)
    return ranked[first_cut:]


def _select_open_quality_cases(
    rows: list[dict[str, object]],
    *,
    allowed_error_per_pixel: float,
    skip_variants: set[str] | None = None,
) -> list[dict[str, object]]:
    """Return unresolved quality cases sorted from worst to best.

    "Open" means the case is finite, not explicitly skipped, and still above the
    accepted quality threshold.
    """
    skips = {str(v).upper() for v in (skip_variants or set()) if str(v).strip()}
    open_rows: list[dict[str, object]] = []
    for row in rows:
        err = float(row.get("error_per_pixel", float("inf")))
        if not math.isfinite(err):
            continue
        variant = str(row.get("variant", "")).upper()
        if variant and variant in skips:
            continue
        if math.isfinite(allowed_error_per_pixel) and err <= allowed_error_per_pixel:
            continue
        open_rows.append(row)

    return sorted(open_rows, key=_quality_sort_key, reverse=True)


def _iteration_strategy_for_pass(pass_idx: int, base_iterations: int) -> tuple[int, int]:
    """Adaptive per-pass search budget for unresolved quality cases."""
    p = max(1, int(pass_idx))
    base = max(1, int(base_iterations))
    phase = (p - 1) % 3

    if phase == 0:
        return base + p, 6 + p
    if phase == 1:
        return base + 24 + (p * 2), 7 + p
    return base + 48 + (p * 3), 8 + p


def _adaptive_iteration_budget_for_quality_row(row: dict[str, object], planned_budget: int) -> int:
    """Tune per-row iteration budget using convergence/plateau quality signals.

    Heuristic goals:
    - plateau reached clearly before budget end -> reduce budget next pass
    - max-iterations hit or best-iter near budget end -> increase budget
    """
    budget = max(1, int(planned_budget))
    convergence = str(row.get("convergence", "") or "").strip().lower()
    best_iter_raw = row.get("best_iter", 0)
    try:
        best_iter = max(0, int(best_iter_raw))
    except (TypeError, ValueError):
        best_iter = 0

    usage_ratio = (best_iter / budget) if budget > 0 else 0.0

    if convergence == "plateau":
        if usage_ratio <= 0.35:
            return max(1, int(round(budget * 0.60)))
        if usage_ratio <= 0.55:
            return max(1, int(round(budget * 0.80)))
        return budget

    if convergence == "max_iterations" or usage_ratio >= 0.95:
        return max(1, int(round(budget * 1.35)))
    if usage_ratio >= 0.80:
        return max(1, int(round(budget * 1.15)))
    return budget


def _write_quality_pass_report(
    reports_out_dir: str,
    pass_rows: list[dict[str, object]],
) -> None:
    if not pass_rows:
        return

    out_path = os.path.join(reports_out_dir, "quality_tercile_passes.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "pass",
            "filename",
            "old_error_per_pixel",
            "new_error_per_pixel",
            "old_mean_delta2",
            "new_mean_delta2",
            "improved",
            "decision",
            "iteration_budget",
            "badge_validation_rounds",
        ])
        for row in pass_rows:
            writer.writerow([
                row["pass"],
                row["filename"],
                f"{float(row['old_error_per_pixel']):.8f}",
                f"{float(row['new_error_per_pixel']):.8f}",
                f"{float(row.get('old_mean_delta2', float('inf'))):.6f}",
                f"{float(row.get('new_mean_delta2', float('inf'))):.6f}",
                "1" if bool(row["improved"]) else "0",
                row.get("decision", "accepted_improvement" if bool(row["improved"]) else "rejected_regression"),
                row["iteration_budget"],
                row["badge_validation_rounds"],
            ])


def _evaluate_quality_pass_candidate(
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

    prev_error_pp = float(old_row.get("error_per_pixel", float("inf")))
    new_error_pp = float(new_row.get("error_per_pixel", float("inf")))
    prev_mean_delta2 = float(old_row.get("mean_delta2", float("inf")))
    new_mean_delta2 = float(new_row.get("mean_delta2", float("inf")))
    error_improved = new_error_pp + 1e-9 < prev_error_pp
    delta2_improved = new_mean_delta2 + 1e-6 < prev_mean_delta2
    improved = error_improved or delta2_improved
    decision = "accepted_improvement" if improved else "rejected_regression"
    return improved, decision, prev_error_pp, new_error_pp, prev_mean_delta2, new_mean_delta2


def _extract_svg_inner(svg_text: str) -> str:
    match = re.search(r"<svg[^>]*>(.*)</svg>", svg_text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return svg_text


def _build_transformed_svg_from_template(
    template_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
    scale: float,
) -> str:
    inner = _extract_svg_inner(template_svg_text)
    # Keep donor stroke widths visually stable when trying scale-based transfers.
    # This mirrors the "M->S/L while preserving line thickness" workflow that is
    # often needed for noisy small/large bitmap variants.
    inner = re.sub(
        r"<(circle|ellipse|line|path|polygon|polyline|rect)\\b([^>]*)>",
        lambda m: (
            f"<{m.group(1)}{m.group(2)}>"
            if "vector-effect=" in m.group(2)
            else f"<{m.group(1)}{m.group(2)} vector-effect=\"non-scaling-stroke\">"
        ),
        inner,
        flags=re.IGNORECASE,
    )
    cx = float(target_w) / 2.0
    cy = float(target_h) / 2.0
    return (
        f'<svg width="{target_w}" height="{target_h}" viewBox="0 0 {target_w} {target_h}" '
        'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">\n'
        f'  <g transform="translate({cx:.3f} {cy:.3f}) rotate({int(rotation_deg)}) scale({float(scale):.4f}) '
        f'translate({-cx:.3f} {-cy:.3f})">\n'
        f"{inner}\n"
        "  </g>\n"
        "</svg>"
    )


def _template_transfer_scale_candidates(base_scale: float) -> list[float]:
    """Build a compact scale ladder around an estimated best scale."""
    if not math.isfinite(base_scale) or base_scale <= 0.0:
        base_scale = 1.0

    multipliers = (1.00, 0.92, 1.08, 0.84, 1.18, 0.74, 1.35, 1.55)
    scales: list[float] = []
    seen: set[float] = set()
    for mul in multipliers:
        value = float(min(1.90, max(0.65, base_scale * mul)))
        key = round(value, 4)
        if key in seen:
            continue
        seen.add(key)
        scales.append(key)

    for fallback in (0.80, 0.90, 1.00, 1.10, 1.25):
        key = round(float(fallback), 4)
        if key not in seen:
            seen.add(key)
            scales.append(key)
    return scales


def _estimate_template_transfer_scale(
    img_orig: np.ndarray,
    donor_svg_text: str,
    target_w: int,
    target_h: int,
    *,
    rotation_deg: int,
) -> float | None:
    """Estimate donor->target scale from foreground silhouette bboxes."""
    rendered = Action.render_svg_to_numpy(
        _build_transformed_svg_from_template(
            donor_svg_text,
            target_w,
            target_h,
            rotation_deg=rotation_deg,
            scale=1.0,
        ),
        target_w,
        target_h,
    )
    if rendered is None:
        return None

    target_mask = Action._foreground_mask(img_orig)
    donor_mask = Action._foreground_mask(rendered)
    target_bbox = Action._mask_bbox(target_mask)
    donor_bbox = Action._mask_bbox(donor_mask)
    if target_bbox is None or donor_bbox is None:
        return None

    target_w_box = max(1e-6, float(target_bbox[2] - target_bbox[0] + 1.0))
    target_h_box = max(1e-6, float(target_bbox[3] - target_bbox[1] + 1.0))
    donor_w_box = max(1e-6, float(donor_bbox[2] - donor_bbox[0] + 1.0))
    donor_h_box = max(1e-6, float(donor_bbox[3] - donor_bbox[1] + 1.0))

    scale_w = target_w_box / donor_w_box
    scale_h = target_h_box / donor_h_box
    scale = math.sqrt(max(1e-6, scale_w * scale_h))
    if not math.isfinite(scale):
        return None
    return float(min(1.90, max(0.65, scale)))


def _template_transfer_transform_candidates(
    target_variant: str,
    donor_variant: str,
    *,
    estimated_scale_by_rotation: dict[int, float] | None = None,
) -> list[tuple[int, float]]:
    """Return ordered rotation/scale candidates for template-based fallback."""
    del target_variant, donor_variant  # reserved for future metadata-based policies

    candidates: list[tuple[int, float]] = []
    seen: set[tuple[int, float]] = set()
    for rotation in (0, 90, 180, 270):
        estimated = None
        if estimated_scale_by_rotation is not None:
            estimated = estimated_scale_by_rotation.get(rotation)
        for scale in _template_transfer_scale_candidates(estimated if estimated is not None else 1.0):
            candidate = (rotation, float(scale))
            key = (rotation, round(float(scale), 4))
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)
    return candidates


def _rank_template_transfer_donors(
    target_row: dict[str, object],
    donor_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Prioritize donors that are already good and geometrically close to target."""
    target_base = str(target_row.get("base", "")).upper()
    target_sig: dict[str, float] | None = None
    target_params = target_row.get("params")
    if isinstance(target_params, dict):
        target_sig = _normalized_geometry_signature(
            int(target_row.get("w", 0)),
            int(target_row.get("h", 0)),
            dict(target_params),
        )

    ranked: list[tuple[tuple[float, float, float], dict[str, object]]] = []
    for donor in donor_rows:
        donor_base = str(donor.get("base", "")).upper()
        donor_error_pp = float(donor.get("error_per_pixel", float("inf")))
        donor_sig: dict[str, float] | None = None
        donor_params = donor.get("params")
        if isinstance(donor_params, dict):
            donor_sig = _normalized_geometry_signature(int(donor.get("w", 0)), int(donor.get("h", 0)), dict(donor_params))

        delta = float("inf")
        if target_sig is not None and donor_sig is not None:
            delta = _max_signature_delta(target_sig, donor_sig)

        key = (0.0 if donor_base == target_base else 1.0, delta, donor_error_pp)
        ranked.append((key, donor))

    ranked.sort(key=lambda item: item[0])
    return [donor for _, donor in ranked]


def _template_transfer_donor_family_compatible(
    target_base: str,
    donor_base: str,
    *,
    documented_alias_refs: set[str] | None = None,
) -> bool:
    """Allow fallback transfer within family, plus documented cross-family aliases."""
    alias_refs = {str(v).upper() for v in (documented_alias_refs or set()) if str(v).strip()}
    if donor_base.upper() in alias_refs:
        return True

    target_family = _extract_symbol_family(target_base)
    donor_family = _extract_symbol_family(donor_base)
    if target_family is None or donor_family is None:
        # Keep legacy behavior for non-standard names where family extraction fails.
        return True
    return target_family == donor_family




def _semantic_transfer_rotations(target_params: dict[str, object], donor_params: dict[str, object]) -> tuple[int, ...]:
    """Rotation candidates for semantic transfer while preserving symbol semantics."""
    has_text = bool(target_params.get("draw_text", False) or donor_params.get("draw_text", False))
    has_connector = bool(
        target_params.get("arm_enabled", False)
        or target_params.get("stem_enabled", False)
        or donor_params.get("arm_enabled", False)
        or donor_params.get("stem_enabled", False)
    )
    if has_text or has_connector:
        # Directional semantic badges (e.g. AC0812 left arm) encode orientation in
        # geometry. Rotating donor templates can improve pixel error but flips the
        # meaning of connector-side symbols. Keep transfer upright/unrotated.
        return (0,)
    return (0, 90, 180, 270)






def _semantic_transfer_is_compatible(target_params: dict[str, object], donor_params: dict[str, object]) -> bool:
    """Return whether donor semantics can preserve target semantic geometry."""
    target_has_arm = bool(target_params.get("arm_enabled", False))
    target_has_stem = bool(target_params.get("stem_enabled", False))
    donor_has_arm = bool(donor_params.get("arm_enabled", False))
    donor_has_stem = bool(donor_params.get("stem_enabled", False))

    # Keep connector type stable for directional symbols (arm vs stem).
    if target_has_arm != donor_has_arm:
        return False
    if target_has_stem != donor_has_stem:
        return False

    target_has_text = bool(target_params.get("draw_text", False))
    donor_has_text = bool(donor_params.get("draw_text", False))
    if target_has_text != donor_has_text:
        return False

    # If both carry labels, require same text mode (e.g. VOC vs CO₂ path families).
    if target_has_text and donor_has_text:
        target_mode = str(target_params.get("text_mode", "")).lower()
        donor_mode = str(donor_params.get("text_mode", "")).lower()
        if target_mode and donor_mode and target_mode != donor_mode:
            return False

    # Directional connector families (e.g. AC0810 right arm vs AC0812 left arm)
    # must keep side/orientation stable during semantic transfer.
    if target_has_arm and donor_has_arm:
        target_arm_dir = _connector_arm_direction(target_params)
        donor_arm_dir = _connector_arm_direction(donor_params)
        if target_arm_dir is not None and donor_arm_dir is not None and target_arm_dir != donor_arm_dir:
            return False

    if target_has_stem and donor_has_stem:
        target_stem_dir = _connector_stem_direction(target_params)
        donor_stem_dir = _connector_stem_direction(donor_params)
        if target_stem_dir is not None and donor_stem_dir is not None and target_stem_dir != donor_stem_dir:
            return False

    return True


def _connector_arm_direction(params: dict[str, object]) -> int | None:
    """Return horizontal arm side: -1 left of circle, +1 right, or None if unknown."""
    x1 = params.get("arm_x1")
    x2 = params.get("arm_x2")
    cx = params.get("cx")
    if x1 is not None and x2 is not None and cx is not None:
        mid = (float(x1) + float(x2)) * 0.5
        delta = mid - float(cx)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1

    if x1 is not None and cx is not None:
        delta = float(x1) - float(cx)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1
    return None


def _connector_stem_direction(params: dict[str, object]) -> int | None:
    """Return vertical stem direction: -1 up, +1 down, or None if unknown."""
    y1 = params.get("arm_y1")
    y2 = params.get("arm_y2")
    if y1 is not None and y2 is not None:
        dy = float(y2) - float(y1)
        if abs(dy) > 1e-3:
            return -1 if dy < 0.0 else 1

    cy = params.get("cy")
    if y1 is not None and y2 is not None and cy is not None:
        mid = (float(y1) + float(y2)) * 0.5
        delta = mid - float(cy)
        if abs(delta) > 1e-3:
            return -1 if delta < 0.0 else 1
    return None


def _semantic_transfer_scale_candidates(base_scale: float) -> list[float]:
    """Broader scale ladder for semantic badge transfer exploration."""
    core = _template_transfer_scale_candidates(base_scale)
    extra = [0.55, 0.65, 0.75, 0.85, 1.00, 1.15, 1.30, 1.50, 1.75, 2.00]
    values = []
    seen: set[float] = set()
    for v in [*core, *extra]:
        value = float(min(2.2, max(0.5, float(v))))
        key = round(value, 4)
        if key in seen:
            continue
        seen.add(key)
        values.append(key)
    return values

def _semantic_transfer_badge_params(
    donor_params: dict[str, object],
    target_params: dict[str, object],
    *,
    target_w: int,
    target_h: int,
    rotation_deg: int,
    scale: float,
) -> dict[str, object]:
    """Rotate/scale connector geometry around circle center while preserving upright text."""
    p = dict(donor_params)
    cx = float(p.get("cx", target_w / 2.0))
    cy = float(p.get("cy", target_h / 2.0))
    tx = float(target_params.get("cx", target_w / 2.0))
    ty = float(target_params.get("cy", target_h / 2.0))

    # Always carry essential rendering colors from target/donor/defaults.
    p["fill_gray"] = int(round(float(target_params.get("fill_gray", p.get("fill_gray", Action.LIGHT_CIRCLE_FILL_GRAY)))))
    p["stroke_gray"] = int(round(float(target_params.get("stroke_gray", p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))))
    if bool(target_params.get("draw_text", p.get("draw_text", False))) or bool(p.get("draw_text", False)):
        p["text_gray"] = int(round(float(target_params.get("text_gray", p.get("text_gray", Action.LIGHT_CIRCLE_TEXT_GRAY)))))
    if bool(target_params.get("stem_enabled", p.get("stem_enabled", False))) or bool(p.get("stem_enabled", False)):
        p["stem_gray"] = int(round(float(target_params.get("stem_gray", p.get("stem_gray", p["stroke_gray"])))))

    # Prefer target anchor so center alignment remains stable between variants.
    p["cx"] = tx
    p["cy"] = ty

    if p.get("circle_enabled", True):
        p["r"] = max(1.0, float(p.get("r", 1.0)) * float(scale))

    angle = math.radians(float(rotation_deg))
    ca = math.cos(angle)
    sa = math.sin(angle)

    def _rot_scale_point(x: float, y: float) -> tuple[float, float]:
        dx = (x - cx) * float(scale)
        dy = (y - cy) * float(scale)
        rx = (dx * ca) - (dy * sa)
        ry = (dx * sa) + (dy * ca)
        return tx + rx, ty + ry

    if p.get("arm_enabled"):
        x1, y1 = _rot_scale_point(float(p.get("arm_x1", tx)), float(p.get("arm_y1", ty)))
        x2, y2 = _rot_scale_point(float(p.get("arm_x2", tx)), float(p.get("arm_y2", ty)))
        p["arm_x1"] = float(Action._clip_scalar(x1, 0.0, max(0.0, float(target_w - 1))))
        p["arm_y1"] = float(Action._clip_scalar(y1, 0.0, max(0.0, float(target_h - 1))))
        p["arm_x2"] = float(Action._clip_scalar(x2, 0.0, max(0.0, float(target_w - 1))))
        p["arm_y2"] = float(Action._clip_scalar(y2, 0.0, max(0.0, float(target_h - 1))))

    if p.get("stem_enabled"):
        stem_x = float(p.get("stem_x", tx)) + (float(p.get("stem_width", 1.0)) / 2.0)
        top = float(p.get("stem_top", ty))
        bottom = float(p.get("stem_bottom", ty))
        x1, y1 = _rot_scale_point(stem_x, top)
        x2, y2 = _rot_scale_point(stem_x, bottom)
        p["stem_x"] = float(Action._clip_scalar((x1 + x2) / 2.0 - (float(p.get("stem_width", 1.0)) / 2.0), 0.0, float(target_w)))
        p["stem_top"] = float(Action._clip_scalar(min(y1, y2), 0.0, float(target_h)))
        p["stem_bottom"] = float(Action._clip_scalar(max(y1, y2), 0.0, float(target_h)))

    # Keep text horizontally readable while preventing aggressive down-scaling
    # during template transfer. The historical sqrt(scale) shrink was often too
    # strong and produced undersized labels in converted outputs.
    if bool(p.get("draw_text", False)):
        text_scale = max(0.5, min(1.8, float(scale)))
        # Gentle response to geometric scale changes: preserve legibility for
        # downscaled transfers while still allowing moderate growth.
        text_adjust = max(0.90, min(1.18, text_scale ** 0.38))
        if "s" in p:
            p["s"] = float(max(1e-4, float(p.get("s", 0.01)) * text_adjust))
        if "co2_font_scale" in p:
            p["co2_font_scale"] = float(max(0.30, float(p.get("co2_font_scale", 0.82)) * text_adjust))
        if "voc_font_scale" in p:
            p["voc_font_scale"] = float(max(0.30, float(p.get("voc_font_scale", 0.52)) * text_adjust))

    symbol_name = str(target_params.get("label") or target_params.get("variant") or target_params.get("base") or "")
    if symbol_name:
        p = Action._finalize_ac08_style(symbol_name, p)
    return p

def _try_template_transfer(
    *,
    target_row: dict[str, object],
    donor_rows: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    diff_out_dir: str,
    rng: random.Random | None = None,
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
    target_svg_geometry = _read_svg_geometry(target_svg_path)
    target_geom_params = dict(target_svg_geometry[2]) if target_svg_geometry is not None else None
    target_params_raw = target_row.get("params")
    target_alias_refs: set[str] = set()
    if isinstance(target_params_raw, dict):
        alias_values = target_params_raw.get("documented_alias_refs", [])
        if isinstance(alias_values, list):
            target_alias_refs = {str(v).upper() for v in alias_values if str(v).strip()}
    target_is_semantic = isinstance(target_params_raw, dict) and str(target_params_raw.get("mode", "")) == "semantic_badge"
    ordered_donors = _rank_template_transfer_donors(target_row, donor_rows)
    if rng is not None and len(ordered_donors) > 1:
        head = ordered_donors[:3]
        tail = ordered_donors[3:]
        rng.shuffle(head)
        ordered_donors = head + tail
    for donor in ordered_donors:
        donor_variant = str(donor.get("variant", "")).upper()
        donor_base = str(donor.get("base", "")).upper()
        if not donor_variant or donor_variant == target_variant:
            continue
        if not target_is_semantic and not _template_transfer_donor_family_compatible(
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

        donor_svg_geometry = _read_svg_geometry(donor_svg_path)
        donor_geom_params = dict(donor_svg_geometry[2]) if donor_svg_geometry is not None else None

        estimated_scales = {
            rotation: _estimate_template_transfer_scale(
                img_orig,
                donor_svg_text,
                w,
                h,
                rotation_deg=rotation,
            )
            for rotation in (0, 90, 180, 270)
        }

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
                and _semantic_transfer_is_compatible(dict(target_params_raw), dict(donor_params_raw))
            ):
                base_scale = float(min(w, h)) / max(1.0, float(min(int(donor.get("w", w)), int(donor.get("h", h)))))
                semantic_scales = _semantic_transfer_scale_candidates(base_scale)
                if rng is not None:
                    keep = semantic_scales[:2]
                    rest = semantic_scales[2:]
                    rng.shuffle(rest)
                    semantic_scales = keep + rest
                for rotation in _semantic_transfer_rotations(dict(target_params_raw), dict(donor_params_raw)):
                    for scale in semantic_scales:
                        candidate_params = _semantic_transfer_badge_params(
                            dict(donor_geom_params),
                            dict(target_geom_params),
                            target_w=w,
                            target_h=h,
                            rotation_deg=rotation,
                            scale=float(scale),
                        )
                        try:
                            candidate_svg = Action.generate_badge_svg(w, h, candidate_params)
                            rendered = Action.render_svg_to_numpy(candidate_svg, w, h)
                        except Exception:
                            continue
                        error = Action.calculate_error(img_orig, rendered)
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

        for rotation, scale in _template_transfer_transform_candidates(
            target_variant,
            donor_variant,
            estimated_scale_by_rotation=estimated_scales,
        ):
            candidate_svg = _build_transformed_svg_from_template(
                donor_svg_text,
                w,
                h,
                rotation_deg=rotation,
                scale=scale,
            )
            rendered = Action.render_svg_to_numpy(candidate_svg, w, h)
            error = Action.calculate_error(img_orig, rendered)
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

    rendered = Action.render_svg_to_numpy(best_svg, w, h)
    mean_delta2 = float(target_row.get("mean_delta2", float("inf")))
    std_delta2 = float(target_row.get("std_delta2", float("inf")))
    if rendered is not None:
        diff = Action.create_diff_image(img_orig, rendered)
        cv2.imwrite(os.path.join(diff_out_dir, f"{stem}_diff.png"), diff)
        try:
            mean_delta2, std_delta2 = Action.calculate_delta2_stats(img_orig, rendered)
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




def _read_svg_geometry(svg_path: str) -> tuple[int, int, dict] | None:
    if not os.path.exists(svg_path):
        return None

    text = open(svg_path, "r", encoding="utf-8").read()

    svg_match = re.search(r"<svg[^>]*viewBox=\"0 0 (\d+) (\d+)\"", text)
    if not svg_match:
        return None
    w = int(svg_match.group(1))
    h = int(svg_match.group(2))

    def _gray_from_hex(color: str, fallback: int) -> int:
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
                params["fill_gray"] = _gray_from_hex(fill_match.group(1), int(params["fill_gray"]))
            if stroke_match:
                params["stroke_gray"] = _gray_from_hex(stroke_match.group(1), int(params["stroke_gray"]))

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
                params["stem_gray"] = _gray_from_hex(rect_fill_match.group(1), int(params["stroke_gray"]))
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

    text_matches = re.findall(r"(<text\b[^>]*>)(.*?)</text>", text, flags=re.IGNORECASE | re.DOTALL)
    if text_matches:
        for text_tag, _text_content in text_matches:
            fill_match = re.search(r'fill="(#[0-9a-fA-F]{6})"', text_tag)
            if fill_match:
                params["text_gray"] = _gray_from_hex(fill_match.group(1), int(params["text_gray"]))
                break

        text_tokens: list[str] = []
        for _tag, content in text_matches:
            if not content:
                continue
            # Allow nested glyph markup (<tspan>, etc.) by flattening text nodes
            # instead of requiring direct text-only children.
            flattened = re.sub(r"<[^>]+>", "", content)
            flattened = re.sub(r"\s+", " ", flattened).strip()
            if flattened:
                text_tokens.append(flattened.upper())
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
            params["text_gray"] = _gray_from_hex(fill_match.group(1), int(params["text_gray"]))
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


def _normalized_geometry_signature(w: int, h: int, params: dict) -> dict[str, float]:
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


def _max_signature_delta(sig_a: dict[str, float], sig_b: dict[str, float]) -> float:
    keys = sorted(set(sig_a.keys()).intersection(sig_b.keys()))
    if not keys:
        return 1.0
    return max(abs(sig_a[k] - sig_b[k]) for k in keys)


def _needs_large_circle_overflow_guard(params: dict) -> bool:
    """Return whether circle placement may intentionally exceed canvas bounds.

    This is a generic geometry rule for large, centered CO² badges without
    connectors. It replaces single-variant checks (for example ``AC0820_L``)
    so future families with the same structure automatically get the same
    robust radius handling.
    """
    if not bool(params.get("circle_enabled", True)):
        return False
    if bool(params.get("arm_enabled") or params.get("stem_enabled")):
        return False
    if not bool(params.get("draw_text", False)):
        return False
    if str(params.get("text_mode", "")).lower() != "co2":
        return False

    template_r = float(params.get("template_circle_radius", params.get("r", 0.0)) or 0.0)
    current_r = float(params.get("r", 0.0) or 0.0)
    width = float(params.get("width", params.get("badge_width", 0.0)) or 0.0)

    large_template = template_r >= 10.0
    large_current = current_r >= 10.0
    wide_canvas = width >= 30.0
    return bool(large_template or large_current or wide_canvas)


def _scale_badge_params(
    anchor: dict,
    anchor_w: int,
    anchor_h: int,
    target_w: int,
    target_h: int,
    *,
    target_variant: str = "",
) -> dict:
    scaled = dict(anchor)
    scale = max(1e-6, float(min(target_w, target_h)) / max(1.0, float(min(anchor_w, anchor_h))))
    scale_x = max(1e-6, float(target_w) / max(1.0, float(anchor_w)))
    scale_y = max(1e-6, float(target_h) / max(1.0, float(anchor_h)))

    if scaled.get("circle_enabled", True):
        scaled["cx"] = float(anchor["cx"]) * scale_x
        scaled["cy"] = float(anchor["cy"]) * scale_y
        scaled["r"] = float(anchor["r"]) * scale
        # Intentionally preserve stroke thickness across size variants.
        scaled["stroke_circle"] = float(anchor["stroke_circle"])

    if scaled.get("stem_enabled"):
        scaled["stem_x"] = float(anchor["stem_x"]) * scale_x
        scaled["stem_width"] = float(anchor["stem_width"])
        scaled["stem_top"] = float(anchor["stem_top"]) * scale_y
        scaled["stem_bottom"] = float(anchor["stem_bottom"]) * scale_y

    if scaled.get("arm_enabled"):
        scaled["arm_x1"] = float(anchor["arm_x1"]) * scale_x
        scaled["arm_y1"] = float(anchor["arm_y1"]) * scale_y
        scaled["arm_x2"] = float(anchor["arm_x2"]) * scale_x
        scaled["arm_y2"] = float(anchor["arm_y2"]) * scale_y
        scaled["arm_stroke"] = float(anchor["arm_stroke"])

    template_scalars = {
        "template_circle_cx": scale_x,
        "template_circle_cy": scale_y,
        "template_circle_radius": scale,
        "template_stem_top": scale_y,
        "template_stem_bottom": scale_y,
        "template_arm_x1": scale_x,
        "template_arm_y1": scale_y,
        "template_arm_x2": scale_x,
        "template_arm_y2": scale_y,
        "stem_len_min": scale_y,
        "arm_len_min": max(scale_x, scale_y),
    }
    for key, factor in template_scalars.items():
        if key in scaled:
            scaled[key] = float(anchor[key]) * float(factor)

    if scaled.get("circle_enabled", True):
        overflow_guard = _needs_large_circle_overflow_guard(scaled)
        required_r = (float(target_w) / 2.0) + 0.5 if overflow_guard else 1.0
        if overflow_guard:
            scaled["allow_circle_overflow"] = True
            scaled["circle_radius_lower_bound_px"] = float(
                max(float(scaled.get("circle_radius_lower_bound_px", 1.0)), required_r)
            )
        stroke = max(0.0, float(scaled.get("stroke_circle", 1.0)))
        half_stroke = stroke / 2.0
        cx = float(scaled.get("cx", target_w / 2.0))
        cy = float(scaled.get("cy", target_h / 2.0))
        r = max(1.0, float(scaled.get("r", 1.0)), required_r)

        max_fit_r = max(1.0, (min(float(target_w), float(target_h)) / 2.0) - half_stroke)
        if not overflow_guard and r > max_fit_r:
            r = max_fit_r

        min_cx = r + half_stroke
        max_cx = float(target_w) - r - half_stroke
        min_cy = r + half_stroke
        max_cy = float(target_h) - r - half_stroke

        if min_cx > max_cx:
            cx = float(target_w) / 2.0 if not overflow_guard else float(Action._clip_scalar(cx, 0.0, float(target_w)))
        else:
            cx = float(Action._clip_scalar(cx, min_cx, max_cx))

        if min_cy > max_cy:
            cy = float(target_h) / 2.0 if not overflow_guard else float(Action._clip_scalar(cy, 0.0, float(target_h)))
        else:
            cy = float(Action._clip_scalar(cy, min_cy, max_cy))

        if scaled.get("stem_enabled") and "stem_width" in scaled:
            stem_width = max(1e-6, float(scaled["stem_width"]))
            scaled["stem_x"] = cx - (stem_width / 2.0)
            if "stem_top" in scaled:
                bottom_anchored = float(scaled.get("stem_bottom", 0.0)) >= (float(target_h) - 0.5)
                reanchored_top = cy + r - (stem_width * 0.55)
                if bottom_anchored:
                    scaled["stem_top"] = float(Action._clip_scalar(reanchored_top, 0.0, float(target_h)))
                    scaled["stem_bottom"] = float(target_h)
                else:
                    stem_len = max(1.0, float(scaled.get("stem_bottom", reanchored_top)) - float(scaled.get("stem_top", reanchored_top)))
                    scaled["stem_top"] = float(Action._clip_scalar(reanchored_top, 0.0, float(target_h - 1)))
                    scaled["stem_bottom"] = float(
                        Action._clip_scalar(float(scaled["stem_top"]) + stem_len, float(scaled["stem_top"]) + 1.0, float(target_h))
                    )

        scaled["cx"] = cx
        scaled["cy"] = cy
        scaled["r"] = r

    return scaled


def _harmonization_anchor_priority(suffix: str, prefer_large: bool) -> int:
    """Return size-priority rank for L/M/S harmonization anchors."""
    if prefer_large:
        # For connector families we keep L authoritative to avoid undersized
        # large variants caused by propagating medium geometry upwards.
        return {"L": 0, "M": 1, "S": 2}.get(str(suffix), 3)
    # Plain circles remain more stable when M is used as anchor.
    return {"M": 0, "L": 1, "S": 2}.get(str(suffix), 3)


def _clip_gray(value: float) -> int:
    return int(max(0, min(255, round(float(value)))))


def _family_harmonized_badge_colors(variant_rows: list[dict[str, object]]) -> dict[str, int]:
    """Derive a family palette from L/M/S variants and slightly boost contrast."""
    buckets: dict[str, list[float]] = {
        "fill_gray": [],
        "stroke_gray": [],
        "text_gray": [],
        "stem_gray": [],
    }
    for row in variant_rows:
        params = dict(row["params"])
        for key in buckets:
            value = params.get(key)
            if value is None:
                continue
            try:
                buckets[key].append(float(value))
            except (TypeError, ValueError):
                continue

    fill_avg = sum(buckets["fill_gray"]) / max(1, len(buckets["fill_gray"]))
    stroke_avg = sum(buckets["stroke_gray"]) / max(1, len(buckets["stroke_gray"]))
    if fill_avg < stroke_avg:
        fill_avg, stroke_avg = stroke_avg, fill_avg

    center = (fill_avg + stroke_avg) / 2.0
    delta = abs(fill_avg - stroke_avg)
    boosted_delta = max(18.0, delta * 1.12)
    fill_gray = _clip_gray(center + (boosted_delta / 2.0))
    stroke_gray = _clip_gray(center - (boosted_delta / 2.0))
    if fill_gray <= stroke_gray:
        fill_gray = _clip_gray(max(fill_gray, stroke_gray + 1.0))

    colors = {
        "fill_gray": fill_gray,
        "stroke_gray": stroke_gray,
        "text_gray": stroke_gray,
        "stem_gray": stroke_gray,
    }

    if buckets["text_gray"]:
        text_avg = sum(buckets["text_gray"]) / float(len(buckets["text_gray"]))
        colors["text_gray"] = _clip_gray(min(text_avg, float(stroke_gray)))

    if buckets["stem_gray"]:
        stem_avg = sum(buckets["stem_gray"]) / float(len(buckets["stem_gray"]))
        colors["stem_gray"] = _clip_gray(min(stem_avg, float(stroke_gray)))

    return colors


def _harmonize_semantic_size_variants(
    results: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
) -> None:
    grouped: dict[str, list[dict[str, object]]] = {}
    for result in results:
        base = str(result.get("base", ""))
        grouped.setdefault(base, []).append(result)

    harmonized_logs: list[str] = []
    category_logs: list[str] = []
    for base, entries in sorted(grouped.items()):
        if len(entries) < 2:
            continue

        variant_rows: list[dict[str, object]] = []
        for entry in entries:
            variant = str(entry["variant"])
            suffix = variant.rsplit("_", 1)[-1] if "_" in variant else ""
            if suffix not in {"L", "M", "S"}:
                continue
            parsed = _read_svg_geometry(os.path.join(svg_out_dir, f"{variant}.svg"))
            if parsed is None:
                continue
            w, h, params = parsed
            variant_rows.append({"entry": entry, "variant": variant, "suffix": suffix, "w": w, "h": h, "params": params})

        if len(variant_rows) < 2:
            continue

        has_text = any(bool(dict(row["params"]).get("draw_text", False)) for row in variant_rows)
        has_stem = any(bool(dict(row["params"]).get("stem_enabled", False)) for row in variant_rows)
        has_arm = any(bool(dict(row["params"]).get("arm_enabled", False)) for row in variant_rows)
        has_connector = has_stem or has_arm
        category = "Kreise mit Buchstaben" if has_text and not has_connector else (
            "Kreise ohne Buchstaben" if (not has_text and not has_connector) else (
                "Kellen mit Buchstaben" if has_text else "Kellen ohne Buchstaben"
            )
        )
        variants_joined = "|".join(sorted(str(r["variant"]) for r in variant_rows))
        category_logs.append(f"{base};{category};{variants_joined}")

        sigs = {
            row["variant"]: _normalized_geometry_signature(int(row["w"]), int(row["h"]), dict(row["params"]))
            for row in variant_rows
        }
        max_delta = 0.0
        for i in range(len(variant_rows)):
            for j in range(i + 1, len(variant_rows)):
                vi = str(variant_rows[i]["variant"])
                vj = str(variant_rows[j]["variant"])
                max_delta = max(max_delta, _max_signature_delta(sigs[vi], sigs[vj]))

        # Do not skip families with one badly fitted outlier variant. We still
        # validate every harmonization candidate against raster error before write.

        def _anchor_rank(row: dict[str, object]) -> tuple[int, float]:
            suffix = str(row.get("suffix", ""))
            # Connector families ("Kellen") tend to under-fit large variants
            # when we derive L from M. Prefer L as harmonization anchor so the
            # largest geometry stays authoritative and M/S scale down from it.
            priority = _harmonization_anchor_priority(suffix, prefer_large=has_connector)
            err = float(dict(row["entry"]).get("error", float("inf")))
            return priority, err

        anchor = min(variant_rows, key=_anchor_rank)
        anchor_variant = str(anchor["variant"])
        anchor_w = int(anchor["w"])
        anchor_h = int(anchor["h"])
        anchor_params = dict(anchor["params"])
        family_colors = _family_harmonized_badge_colors(variant_rows)

        for row in variant_rows:
            target_variant = str(row["variant"])
            target_w = int(row["w"])
            target_h = int(row["h"])
            scaled = _scale_badge_params(
                anchor_params,
                anchor_w,
                anchor_h,
                target_w,
                target_h,
                target_variant=target_variant,
            )
            scaled.update(family_colors)
            if scaled.get("draw_text"):
                scaled["text_gray"] = int(family_colors["text_gray"])
            if scaled.get("stem_enabled"):
                scaled["stem_gray"] = int(family_colors["stem_gray"])
            svg = Action.generate_badge_svg(target_w, target_h, scaled)

            target_filename = str(dict(row["entry"])["filename"])
            target_path = os.path.join(folder_path, target_filename)
            target_img = cv2.imread(target_path)
            if target_img is None:
                harmonized_logs.append(f"{base}: {target_variant} übersprungen (Bild fehlt: {target_filename})")
                continue

            rendered = Action.render_svg_to_numpy(svg, target_w, target_h)
            candidate_error = Action.calculate_error(target_img, rendered)
            baseline_error = float(dict(row["entry"]).get("error", float("inf")))
            if candidate_error > baseline_error + 0.25:
                harmonized_logs.append(
                    (
                        f"{base}: {target_variant} nicht harmonisiert "
                        f"(Fehler {candidate_error:.2f} > Basis {baseline_error:.2f})"
                    )
                )
                continue

            with open(os.path.join(svg_out_dir, f"{target_variant}.svg"), "w", encoding="utf-8") as f:
                f.write(svg)
            harmonized_logs.append(
                (
                    f"{base}: {target_variant} aus {anchor_variant} harmonisiert "
                    f"(max_delta={max_delta:.4f}, Fehler {baseline_error:.2f}->{candidate_error:.2f}, "
                    f"Farben fill/stroke={family_colors['fill_gray']}/{family_colors['stroke_gray']})"
                )
            )

    if harmonized_logs:
        with open(os.path.join(reports_out_dir, "variant_harmonization.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(harmonized_logs).rstrip() + "\n")
    if category_logs:
        with open(os.path.join(reports_out_dir, "shape_catalog.csv"), "w", encoding="utf-8") as f:
            f.write("base;category;variants\n")
            f.write("\n".join(category_logs).rstrip() + "\n")


def _write_ac08_regression_manifest(
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


def _summarize_previous_good_ac08_variants(reports_out_dir: str) -> dict[str, object]:
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


def _write_ac08_success_criteria_report(
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

    previous_good = _summarize_previous_good_ac08_variants(reports_out_dir)
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


def _write_ac08_weak_family_status_report(
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


def _write_pixel_delta2_ranking(folder_path: str, svg_out_dir: str, reports_out_dir: str, threshold: float = 18.0) -> None:
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

        mean_delta2, std_delta2 = Action.calculate_delta2_stats(img_orig, rendered)
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


def _load_iteration_log_rows(reports_out_dir: str) -> dict[str, dict[str, str]]:
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


def _find_image_path_by_variant(folder_path: str, variant: str) -> str | None:
    """Return the raster image path for ``variant`` if present."""
    for ext in ('.jpg', '.png', '.bmp', '.gif'):
        candidate = os.path.join(folder_path, f'{variant}{ext}')
        if os.path.exists(candidate):
            return candidate
    return None


def collect_successful_conversion_quality_metrics(
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
    iteration_rows = _load_iteration_log_rows(reports_out_dir)
    metrics: list[dict[str, object]] = []
    seen: set[str] = set()
    for variant in variants:
        if variant in seen:
            continue
        seen.add(variant)
        image_path = _find_image_path_by_variant(folder_path, variant)
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

        details = _read_validation_log_details(log_path) if os.path.exists(log_path) else {}
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


def _successful_conversion_metrics_available(metrics: dict[str, object]) -> bool:
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


def _parse_successful_conversion_manifest_line(raw_line: str) -> tuple[str, dict[str, object]]:
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


def _read_successful_conversion_manifest_metrics(manifest_path: Path) -> dict[str, dict[str, object]]:
    """Load persisted best-list metrics keyed by variant."""
    if not manifest_path.exists():
        return {}

    rows: dict[str, dict[str, object]] = {}
    for raw_line in manifest_path.read_text(encoding='utf-8').splitlines():
        variant, metrics = _parse_successful_conversion_manifest_line(raw_line)
        if variant:
            rows[variant] = metrics
    return rows


def _successful_conversion_snapshot_dir(reports_out_dir: str) -> Path:
    """Directory used to persist best-of artifacts for successful conversions."""
    return Path(reports_out_dir) / 'successful_conversions_bestlist'


def _successful_conversion_snapshot_paths(reports_out_dir: str, variant: str) -> dict[str, Path]:
    base_dir = _successful_conversion_snapshot_dir(reports_out_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return {
        'svg': base_dir / f'{variant}.svg',
        'log': base_dir / f'{variant}_element_validation.log',
        'metrics': base_dir / f'{variant}.json',
    }


def _restore_successful_conversion_snapshot(variant: str, svg_out_dir: str, reports_out_dir: str) -> bool:
    """Restore the previous best conversion for ``variant`` if a snapshot exists."""
    snapshot_paths = _successful_conversion_snapshot_paths(reports_out_dir, variant)
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


def _store_successful_conversion_snapshot(variant: str, metrics: dict[str, object], svg_out_dir: str, reports_out_dir: str) -> None:
    """Persist the current best conversion artifacts for later rollback/restoration."""
    snapshot_paths = _successful_conversion_snapshot_paths(reports_out_dir, variant)
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


def _is_successful_conversion_candidate_better(
    previous_metrics: dict[str, object] | None,
    candidate_metrics: dict[str, object],
) -> bool:
    """Accept a new best-list candidate only when it improves quality."""
    if not _successful_conversion_metrics_available(candidate_metrics):
        return False
    if not previous_metrics or not _successful_conversion_metrics_available(previous_metrics):
        return True

    previous_status = str(previous_metrics.get('status', '')).strip().lower()
    candidate_status = str(candidate_metrics.get('status', '')).strip().lower()
    if previous_status == 'semantic_ok' and candidate_status != 'semantic_ok':
        return False
    if previous_status != 'semantic_ok' and candidate_status == 'semantic_ok':
        return True

    improved, _decision, _prev_error, _new_error, _prev_delta, _new_delta = _evaluate_quality_pass_candidate(
        previous_metrics,
        candidate_metrics,
    )
    return improved


def _merge_successful_conversion_metrics(
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


def _format_successful_conversion_manifest_line(existing_line: str, metrics: dict[str, object]) -> str:
    """Render one enriched successful-conversions manifest line."""
    if not _successful_conversion_metrics_available(metrics):
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


def _latest_failed_conversion_manifest_entry(reports_out_dir: str) -> dict[str, object] | None:
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


def update_successful_conversions_manifest_with_metrics(
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

    previous_manifest_metrics = _read_successful_conversion_manifest_metrics(resolved_manifest_path)
    metrics_rows = collect_successful_conversion_quality_metrics(
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
        if _is_successful_conversion_candidate_better(previous_metrics, row):
            accepted_metrics_by_variant[variant] = row
            effective_metrics_rows.append(row)
            accepted_improved_variants.add(variant)
            _store_successful_conversion_snapshot(variant, row, svg_out_dir, reports_out_dir)
        else:
            if previous_metrics is not None:
                accepted_metrics_by_variant[variant] = previous_metrics
                effective_metrics_rows.append(_merge_successful_conversion_metrics(row, previous_metrics))
            else:
                effective_metrics_rows.append(row)
            _restore_successful_conversion_snapshot(variant, svg_out_dir, reports_out_dir)

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
        updated_lines.append(_format_successful_conversion_manifest_line(raw_line, metrics))

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
                _format_successful_conversion_manifest_line(
                    variant,
                    accepted_metrics_by_variant[variant],
                )
            )

    failed_entry = _latest_failed_conversion_manifest_entry(reports_out_dir)
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
    return resolved_manifest_path, _sorted_successful_conversion_metrics_rows(effective_metrics_rows)

def _sorted_successful_conversion_metrics_rows(
    metrics: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Sort successful-conversion rows by converted image name/variant."""
    return sorted(metrics, key=lambda row: str(row.get('variant', '')).upper())


def _write_successful_conversion_csv_table(csv_path: str | os.PathLike[str], metrics: list[dict[str, object]]) -> str:
    """Write the successful-conversions leaderboard as a CSV table."""
    csv_path = os.fspath(csv_path)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([
            'variant', 'status', 'image_found', 'svg_found', 'log_found', 'best_iteration',
            'diff_score', 'error_per_pixel', 'pixel_count', 'total_delta2', 'mean_delta2', 'std_delta2',
        ])
        for row in _sorted_successful_conversion_metrics_rows(metrics):
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


def write_successful_conversion_quality_report(
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...] | None = None,
    output_name: str = 'successful_conversion_quality',
) -> tuple[str, str, list[dict[str, object]]]:
    """Backward-compatible wrapper that now also refreshes the manifest."""
    manifest_path, metrics = update_successful_conversions_manifest_with_metrics(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        successful_variants=successful_variants,
    )

    sorted_metrics = _sorted_successful_conversion_metrics_rows(metrics)
    csv_path = _write_successful_conversion_csv_table(
        os.path.join(reports_out_dir, f'{output_name}.csv'),
        sorted_metrics,
    )
    leaderboard_csv_path = _write_successful_conversion_csv_table(
        os.path.join(reports_out_dir, 'successful_conversions.csv'),
        sorted_metrics,
    )
    txt_path = os.path.join(reports_out_dir, f'{output_name}.txt')

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f'manifest_path={manifest_path}\n')
        f.write(f'leaderboard_csv_path={leaderboard_csv_path}\n')
        f.write(f'variants_updated={len(sorted_metrics)}\n')
    return csv_path, txt_path, sorted_metrics




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


def _auto_detect_csv_path(folder_path: str) -> str | None:
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






def _dotted_attr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_attr_name(node.value)
        if prefix:
            return f"{prefix}.{node.attr}"
        return node.attr
    return ""


def _module_call_edges_for_path(module_path: str | os.PathLike[str]) -> tuple[dict[str, int], list[dict[str, object]]]:
    """Return module-local callables and caller->callee edges for the given source file."""
    source_path = Path(module_path)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    callable_lines: dict[str, int] = {}
    local_function_names: set[str] = set()

    class CallableCollector(ast.NodeVisitor):
        def __init__(self):
            self._class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef):
            self._class_stack.append(node.name)
            self.generic_visit(node)
            self._class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef):
            scoped_name = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
            callable_lines[scoped_name] = node.lineno
            local_function_names.add(node.name)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            scoped_name = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
            callable_lines[scoped_name] = node.lineno
            local_function_names.add(node.name)
            self.generic_visit(node)

    CallableCollector().visit(tree)
    edges: list[dict[str, object]] = []

    class CallEdgeCollector(ast.NodeVisitor):
        def __init__(self):
            self._scope_stack: list[str] = []
            self._class_stack: list[str] = []

        def _current_scope(self) -> str:
            return ".".join(self._scope_stack)

        def visit_ClassDef(self, node: ast.ClassDef):
            self._class_stack.append(node.name)
            self.generic_visit(node)
            self._class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef):
            scoped_name = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
            self._scope_stack.append(scoped_name)
            self.generic_visit(node)
            self._scope_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
            scoped_name = ".".join(self._class_stack + [node.name]) if self._class_stack else node.name
            self._scope_stack.append(scoped_name)
            self.generic_visit(node)
            self._scope_stack.pop()

        def visit_Call(self, node: ast.Call):
            caller = self._current_scope()
            callee = ""
            raw_callee = _dotted_attr_name(node.func)
            if isinstance(node.func, ast.Name):
                if node.func.id in local_function_names:
                    callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                owner = _dotted_attr_name(node.func.value)
                attr = node.func.attr
                if owner in {"self", "cls"} and self._class_stack:
                    candidate = f"{self._class_stack[-1]}.{attr}"
                    if candidate in callable_lines:
                        callee = candidate
                elif attr in local_function_names:
                    callee = attr

            if caller and callee:
                edges.append(
                    {
                        "caller": caller,
                        "callee": callee,
                        "caller_line": callable_lines.get(caller, 0),
                        "callee_line": callable_lines.get(callee, 0),
                        "call_line": getattr(node, "lineno", 0),
                        "raw_callee": raw_callee,
                    }
                )
            self.generic_visit(node)

    CallEdgeCollector().visit(tree)
    return callable_lines, edges






_MAINFILES_DIR = Path(__file__).resolve().parent


def _load_mainfile_function(func_name: str, filename: str):
    """Lade eine ausgelagerte Funktionsdefinition aus src/iccFs/mF in dieses Modul."""
    source_path = _MAINFILES_DIR / filename
    namespace: dict[str, object] = {}
    code = compile(source_path.read_text(encoding="utf-8"), str(source_path), "exec")
    exec(code, globals(), namespace)
    loaded = namespace.get(func_name)
    if not callable(loaded):
        raise RuntimeError(f"Funktion {func_name!r} konnte aus {source_path} nicht geladen werden")
    globals()[func_name] = loaded
    return loaded


analyze_range = _load_mainfile_function("analyze_range", "analyze_range.py")
_load_description_mapping = _load_mainfile_function("_load_description_mapping", "_load_description_mapping.py")
_run_svg_render_subprocess_entrypoint = _load_mainfile_function(
    "_run_svg_render_subprocess_entrypoint", "_run_svg_render_subprocess_entrypoint.py"
)
_bootstrap_required_image_dependencies = _load_mainfile_function(
    "_bootstrap_required_image_dependencies", "_bootstrap_required_image_dependencies.py"
)
build_linux_vendor_install_command = _load_mainfile_function(
    "build_linux_vendor_install_command", "build_linux_vendor_install_command.py"
)
convert_range = _load_mainfile_function("convert_range", "convert_range.py")
export_module_call_tree_csv = _load_mainfile_function("export_module_call_tree_csv", "export_module_call_tree_csv.py")
parse_args = _load_mainfile_function("parse_args", "parse_args.py")
_optional_log_capture = contextlib.contextmanager(
    _load_mainfile_function("_optional_log_capture", "_optional_log_capture.py")
)
_resolve_cli_csv_and_output = _load_mainfile_function("_resolve_cli_csv_and_output", "_resolve_cli_csv_and_output.py")
_format_user_diagnostic = _load_mainfile_function("_format_user_diagnostic", "_format_user_diagnostic.py")
_prompt_interactive_range = _load_mainfile_function("_prompt_interactive_range", "_prompt_interactive_range.py")
convert_image = _load_mainfile_function("convert_image", "convert_image.py")
convert_image_variants = _load_mainfile_function("convert_image_variants", "convert_image_variants.py")
