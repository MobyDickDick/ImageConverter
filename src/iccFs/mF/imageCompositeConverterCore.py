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
    # Allow direct CLI execution via ``python src.imageCompositeConverter.py``
    # from the repository root without requiring PYTHONPATH to be preset.
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from src.iccFs.optionalDependencyBaseDir import optionalDependencyBaseDir
from src.iccFs.mF.overviewTiles import generateConversionOverviews
from src.iccFs.mF.imageCompositeConverterRegions import (
    ANNOTATION_COLORS,
    bboxToDict,
    annotateImageRegionsImpl,
    detectRelevantRegionsImpl,
)
from src.iccFs.mF.convertRangeFiles.inRequestedRange import inRequestedRange
from src.iccFs.mF.convertRangeFiles._inRequestedRangeFiles.getBaseNameFromFile import getBaseNameFromFile
from src.iccFs.mF.successfulConversions import (
    AC08_MITIGATION_STATUS,
    AC08_PREVIOUSLY_GOOD_VARIANTS,
    AC08_REGRESSION_CASES,
    AC08_REGRESSION_SET_NAME,
    AC08_REGRESSION_VARIANTS,
    SUCCESSFUL_CONVERSIONS,
    SUCCESSFUL_CONVERSIONS_MANIFEST,
    loadSuccessfulConversions,
)
from src.iccFs.mF.convertRangeFiles.adaptiveIterationBudgetForQualityRow import adaptiveIterationBudgetForQualityRow
from src.iccFs.mF.convertRangeFiles.evaluateQualityPassCandidate import evaluateQualityPassCandidate
from src.iccFs.mF.convertRangeFiles._harmonizeSemanticSizeVariantsFiles._familyHarmonizedBadgeColorsFiles.clipGray import clipGray
from src.iccFs.mF.convertRangeFiles._harmonizeSemanticSizeVariantsFiles.maxSignatureDelta import maxSignatureDelta
from src.iccFs.mF.convertRangeFiles._harmonizeSemanticSizeVariantsFiles.normalizedGeometrySignature import normalizedGeometrySignature
from src.iccFs.mF.convertRangeFiles._harmonizeSemanticSizeVariantsFiles._scaleBadgeParamsFiles.needsLargeCircleOverflowGuard import needsLargeCircleOverflowGuard
from src.iccFs.mF.convertRangeFiles.iterationStrategyForPass import iterationStrategyForPass
from src.iccFs.mF.convertRangeFiles._tryTemplateTransferFiles._semanticTransferIsCompatibleFiles.connectorArmDirection import connectorArmDirection
from src.iccFs.mF.convertRangeFiles._tryTemplateTransferFiles._semanticTransferIsCompatibleFiles.connectorStemDirection import connectorStemDirection
from src.iccFs.mF.convertRangeFiles._tryTemplateTransferFiles.semanticTransferRotations import semanticTransferRotations
from src.iccFs.mF.convertRangeFiles.updateSuccessfulConversionsManifestWithMetricsFiles.mergeSuccessfulConversionMetrics import mergeSuccessfulConversionMetrics
from src.iccFs.mF.convertRangeFiles.updateSuccessfulConversionsManifestWithMetricsFiles.sortedSuccessfulConversionMetricsRows import sortedSuccessfulConversionMetricsRows
from src.iccFs.mF.buildLinuxVendorInstallCommandFiles.requiredVendorPackages import requiredVendorPackages

# Keep regression variant list deterministic and duplicate-free for batch
# selection/tests even when upstream manifests accidentally repeat entries.
AC08_REGRESSION_VARIANTS = tuple(dict.fromkeys(AC08_REGRESSION_VARIANTS))
# Keep the historical "previously good" anchor subset stable for AC08 success
# criteria reports used by this converter/test suite.
AC08_PREVIOUSLY_GOOD_VARIANTS = ("AC0800_L", "AC0800_M", "AC0800_S", "AC0811_L")

loadSuccessfulConversions = loadSuccessfulConversions


DEFAULT_CALL_TREE_CSV_PATH = "artifacts/converted_images/reports/call_tree_image_composite_converter.csv"

OPTIONAL_DEPENDENCY_ERRORS: dict[str, str] = {}

_svg_render_isolation_env = os.environ.get("IMAGE_CONVERTER_ISOLATE_SVG_RENDER", "").strip().lower()
if _svg_render_isolation_env in {"0", "false", "no", "off"}:
    SVG_RENDER_SUBPROCESS_ENABLED = False
elif _svg_render_isolation_env in {"1", "true", "yes", "on"}:
    SVG_RENDER_SUBPROCESS_ENABLED = True
elif "PYTEST_VERSION" in os.environ:
    # Pytest runs execute hundreds of small render calls; spawning a Python
    # subprocess for each render makes focused unit tests look "hung".
    SVG_RENDER_SUBPROCESS_ENABLED = False
else:
    # Default to isolated rendering because native PyMuPDF crashes (SIGSEGV)
    # are not catchable in-process and would otherwise abort long conversions.
    SVG_RENDER_SUBPROCESS_ENABLED = True
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


def detectRelevantRegions(img) -> list[dict[str, object]]:
    return detectRelevantRegionsImpl(img, cv2_module=cv2, np_module=np)


def annotateImageRegions(img, regions: list[dict[str, object]]):
    return annotateImageRegionsImpl(img, regions, cv2_module=cv2)


_optional_dependency_base_dir = optionalDependencyBaseDir


def vendoredSitePackagesDirs() -> list[Path]:
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


def clearPartialModuleImport(module_name: str) -> None:
    """Discard partially imported package state before the next fallback attempt."""
    for imported_name in [name for name in list(sys.modules) if name == module_name or name.startswith(f"{module_name}.")]:
        sys.modules.pop(imported_name, None)


def describeOptionalDependencyError(module_name: str, exc: BaseException, attempted_paths: list[Path]) -> str:
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






# Load numpy before cv2: OpenCV's Python bindings import numpy at module-import
# time and can fail permanently for this process if cv2 is attempted first while
# numpy is available only via repo-vendored site-packages.
np = loadOptionalModule("numpy")
cv2 = loadOptionalModule("cv2")
fitz = loadOptionalModule("fitz")  # PyMuPDF for native SVG rendering








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




































@dataclass
class Perception:
    img_path: str
    csv_path: str

    def __post_init__(self) -> None:
        self.base_name = getBaseNameFromFile(os.path.basename(self.img_path))
        self.img = cv2.imread(self.img_path)
        self.raw_desc = self.loadDescriptions()

    def loadDescriptions(self) -> dict[str, str]:
        return loadDescriptionMapping(self.csv_path)


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














class Reflection:
    def __init__(self, raw_desc: dict[str, str]):
        self.raw_desc = raw_desc

    def parseDescription(self, base_name: str, img_filename: str):
        canonical_base = getBaseNameFromFile(base_name).upper()
        if not canonical_base:
            canonical_base = getBaseNameFromFile(img_filename).upper()
        description_fragments = collectDescriptionFragments(self.raw_desc, base_name, img_filename)
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
            "documented_alias_refs": sorted(Reflection.extractDocumentedAliasRefs(desc)),
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

            layout_overrides = Reflection.parseSemanticBadgeLayoutOverrides(desc)
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
    def extractDocumentedAliasRefs(text: str) -> set[str]:
        """Extract explicit "Wie AC0000" style alias references from descriptions."""
        if not text:
            return set()

        refs = {
            match.upper()
            for match in re.findall(r"\bwie(?:\s+in)?\s+([a-z]{2}\d{3,4})\b", text, flags=re.IGNORECASE)
        }
        return refs

    @staticmethod
    def parseSemanticBadgeLayoutOverrides(text: str) -> dict[str, float | str]:
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
    def snapHalf(value: float) -> float:
        return round(float(value) * 2.0) / 2.0

    @staticmethod
    def clipScalar(value: float, low: float, high: float) -> float:
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
    def makeRng(seed: int):
        if np is not None:
            return np.random.default_rng(int(seed))
        return Action._ScalarRng(int(seed))

    @staticmethod
    def argminIndex(values: list[float]) -> int:
        return min(range(len(values)), key=lambda i: float(values[i]))

    @staticmethod
    def snapIntPx(value: float, minimum: float = 1.0) -> float:
        return float(max(int(round(float(minimum))), int(round(float(value)))))

    @staticmethod
    def maxCircleRadiusInsideCanvas(cx: float, cy: float, w: int, h: int, stroke: float = 0.0) -> float:
        """Return the largest circle radius that stays inside the SVG viewport."""
        if w <= 0 or h <= 0:
            return 1.0
        edge_margin = min(float(cx), float(w) - float(cx), float(cy), float(h) - float(cy))
        return float(max(1.0, edge_margin - (max(0.0, float(stroke)) / 2.0)))

    @staticmethod
    def isCircleWithText(params: dict) -> bool:
        """Return True when the badge encodes a circle-with-text shape."""
        return bool(params.get("circle_enabled", True)) and bool(params.get("draw_text", False))

    @staticmethod
    def applyCircleTextWidthConstraint(params: dict, radius: float, w: int) -> float:
        """Enforce CircleWithText constraint: 2 * radius < image width."""
        if not Action.isCircleWithText(params):
            return float(radius)
        # Keep a tiny strict margin so the optimized radius remains strictly below w/2.
        width_cap = (float(w) / 2.0) - 1e-3
        return float(min(float(radius), width_cap))

    @staticmethod
    def applyCircleTextRadiusFloor(params: dict, radius: float) -> float:
        """Enforce CircleWithText lower bound: radius must exceed half text width."""
        if not Action.isCircleWithText(params):
            return float(radius)
        x1, _y1, x2, _y2 = Action.textBbox(params)
        text_width = max(0.0, float(x2) - float(x1))
        if text_width <= 0.0:
            return float(radius)
        # Keep strict inequality: radius > (text_width / 2).
        lower_bound = (text_width / 2.0) + 1e-3
        return float(max(float(radius), lower_bound))

    @staticmethod
    def clampCircleInsideCanvas(params: dict, w: int, h: int) -> dict:
        """Clamp circle center/radius so no part of the ring exceeds the viewport."""
        p = dict(params)
        if not p.get("circle_enabled", True):
            return p
        if "cx" not in p or "cy" not in p or "r" not in p:
            return p

        cx = float(max(0.0, min(float(w), float(p.get("cx", 0.0)))))
        cy = float(max(0.0, min(float(h), float(p.get("cy", 0.0)))))
        stroke = float(p.get("stroke_circle", 0.0))
        max_r = Action.maxCircleRadiusInsideCanvas(cx, cy, w, h, stroke)
        max_r = Action.applyCircleTextWidthConstraint(p, max_r, w)
        min_r = float(
            max(
                1.0,
                float(p.get("min_circle_radius", 1.0)),
                float(p.get("circle_radius_lower_bound_px", 1.0)),
            )
        )
        min_r = Action.applyCircleTextRadiusFloor(p, min_r)
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
        rng = Action.makeRng(seed)

        def uniform(delta: float) -> float:
            return float(rng.uniform(-abs(float(delta)), abs(float(delta))))

        jitter_entries: list[str] = []

        def applyNumericJitter(key: str, delta: float, *, minimum: float | None = None, maximum: float | None = None) -> None:
            if key not in p:
                return
            try:
                old_float = float(p.get(key))
            except (TypeError, ValueError):
                return
            new_value = old_float + uniform(delta)
            if minimum is not None:
                new_value = max(float(minimum), new_value)
            if maximum is not None:
                new_value = min(float(maximum), new_value)
            p[key] = float(new_value)
            jitter_entries.append(f"{key}:{old_float:.3f}->{new_value:.3f}")

        applyNumericJitter("cx", max(0.15, float(w) * 0.01), minimum=0.0, maximum=float(w))
        applyNumericJitter("cy", max(0.15, float(h) * 0.01), minimum=0.0, maximum=float(h))
        applyNumericJitter("r", max(0.10, float(min(w, h)) * 0.008), minimum=1.0)
        applyNumericJitter("stroke_circle", 0.12, minimum=0.4)
        applyNumericJitter("arm_len", max(0.12, float(w) * 0.012), minimum=0.5, maximum=float(max(w, h)))
        applyNumericJitter("arm_stroke", 0.12, minimum=0.4)
        applyNumericJitter("stem_height", max(0.12, float(h) * 0.012), minimum=0.5, maximum=float(max(w, h)))
        applyNumericJitter("stem_width", 0.12, minimum=0.4, maximum=float(max(1, w)))
        applyNumericJitter("text_scale", 0.03, minimum=0.35, maximum=4.0)
        applyNumericJitter("text_x", max(0.10, float(w) * 0.01), minimum=0.0, maximum=float(w))
        applyNumericJitter("text_y", max(0.10, float(h) * 0.01), minimum=0.0, maximum=float(h))
        applyNumericJitter("co2_dx", 0.08)
        applyNumericJitter("co2_dy", 0.08)
        applyNumericJitter("voc_scale", 0.03, minimum=0.35, maximum=4.0)

        p = Action.clampCircleInsideCanvas(p, w, h)
        if p.get("arm_enabled"):
            Action.reanchorArmToCircleEdge(p, float(p.get("r", 1.0)))
        if p.get("stem_enabled") and "cy" in p and "r" in p:
            p["stem_top"] = float(p.get("cy", 0.0)) + float(p.get("r", 0.0))

        if jitter_entries:
            variation_logs.append(
                "redraw_variation: seed="
                f"{seed} changed_params=" + " | ".join(jitter_entries)
            )
        return p, variation_logs

    @staticmethod
    def enforceCircleConnectorSymmetry(params: dict, w: int, h: int) -> dict:
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
    def quantizeBadgeParams(params: dict, w: int, h: int) -> dict:
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
                p[key] = Action.snapHalf(float(p[key]))

        int_width_keys = ("stroke_circle", "arm_stroke", "stem_width")
        for key in int_width_keys:
            if key in p:
                p[key] = Action.snapIntPx(float(p[key]), minimum=1.0)

        if "stem_width_max" in p:
            p["stem_width_max"] = max(1.0, Action.snapHalf(float(p["stem_width_max"])))

        if p.get("stem_enabled") and "cx" in p and "stem_width" in p:
            p["stem_x"] = Action.snapHalf(float(p["cx"]) - (float(p["stem_width"]) / 2.0))

        if "stem_x" in p and "stem_width" in p:
            p["stem_x"] = max(0.0, min(float(w) - float(p["stem_width"]), float(p["stem_x"])))
        if "stem_top" in p:
            p["stem_top"] = max(0.0, min(float(h), float(p["stem_top"])))
        if "stem_bottom" in p:
            p["stem_bottom"] = max(0.0, min(float(h), float(p["stem_bottom"])))

        p = Action.enforceCircleConnectorSymmetry(p, w, h)
        p = Action.clampCircleInsideCanvas(p, w, h)

        if (
            raw_circle_radius is not None
            and "cx" in p
            and "cy" in p
            and "r" in p
        ):
            canvas_fit_r = float(
                Action.maxCircleRadiusInsideCanvas(
                    float(p["cx"]),
                    float(p["cy"]),
                    w,
                    h,
                    float(p.get("stroke_circle", 0.0)),
                )
            )
            snapped_canvas_fit_r = float(Action.snapHalf(canvas_fit_r))
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
                p[key] = Action.snapHalf(float(p[key]))

        return p

    @staticmethod
    def normalizeLightCircleColors(params: dict) -> dict:
        params["fill_gray"] = Action.LIGHT_CIRCLE_FILL_GRAY
        params["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        if params.get("stem_enabled"):
            params["stem_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        if params.get("draw_text", True) and "text_gray" in params:
            params["text_gray"] = Action.LIGHT_CIRCLE_TEXT_GRAY
        return params

    @staticmethod
    def normalizeAc08LineWidths(params: dict) -> dict:
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
    def estimateBorderBackgroundGray(gray: np.ndarray) -> float:
        """Estimate badge background tone from the outer image border pixels."""
        if gray.size == 0:
            return 255.0
        h, w = gray.shape
        if h < 2 or w < 2:
            return float(np.median(gray))
        border = np.concatenate((gray[0, :], gray[h - 1, :], gray[:, 0], gray[:, w - 1]))
        return float(np.median(border))

    @staticmethod
    def estimateCircleTonesAndStroke(
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
    def persistConnectorLengthFloor(params: dict, element: str, default_ratio: float) -> None:
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
    def isAc08SmallVariant(name: str, params: dict) -> tuple[bool, str, float]:
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
    def configureAc08SmallVariantMode(name: str, params: dict) -> dict:
        """Apply `_S`-specific AC08 tuning for text, connector floors, and masks."""
        p = dict(params)
        is_small, reason, min_dim = Action.isAc08SmallVariant(name, p)
        p["ac08_small_variant_mode"] = bool(is_small)
        p["ac08_small_variant_reason"] = reason
        p["ac08_small_variant_min_dim"] = float(min_dim)
        if not is_small:
            return p

        p["validation_mask_dilate_px"] = int(max(1, int(p.get("validation_mask_dilate_px", 1))))
        p["small_variant_antialias_bias"] = float(max(0.0, float(p.get("small_variant_antialias_bias", 0.08))))

        if p.get("arm_enabled"):
            p["arm_len_min_ratio"] = float(max(float(p.get("arm_len_min_ratio", 0.75)), 0.78))
            Action.persistConnectorLengthFloor(p, "arm", default_ratio=0.78)
        if p.get("stem_enabled"):
            p["stem_len_min_ratio"] = float(max(float(p.get("stem_len_min_ratio", 0.65)), 0.70))
            Action.persistConnectorLengthFloor(p, "stem", default_ratio=0.70)

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
    def enforceTemplateCircleEdgeExtent(params: dict, w: int, h: int, *, anchor: str, retain_ratio: float = 0.97) -> dict:
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
        canvas_cap = float(Action.maxCircleRadiusInsideCanvas(cx, float(p.get("cy", float(h) / 2.0)), w, h, stroke))

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
    def tuneAc08LeftConnectorFamily(name: str, params: dict) -> dict:
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
        is_small, _reason, min_dim = Action.isAc08SmallVariant(str(name), p)
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
        p = Action.enforceTemplateCircleEdgeExtent(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
            anchor="right",
            retain_ratio=0.97 if not is_small else 0.96,
        )

        p = Action.enforceLeftArmBadgeGeometry(
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
            Action.centerGlyphBbox(p)
        return p

    @staticmethod
    def tuneAc08RightConnectorFamily(name: str, params: dict) -> dict:
        """Apply shared guardrails for mirrored right-connector AC08 families.

        Aufgabe 4.2 groups AC0810, AC0814, AC0834, AC0835, AC0838 and AC0839
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
        if symbol_name not in {"AC0810", "AC0814", "AC0834", "AC0835", "AC0838", "AC0839"}:
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
        is_small, _reason, min_dim = Action.isAc08SmallVariant(str(name), p)
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
        p = Action.enforceTemplateCircleEdgeExtent(
            p,
            int(round(float(p.get("width", 0.0) or 0.0))) or int(round(float(p.get("badge_width", 0.0) or 0.0))) or 1,
            int(round(float(p.get("height", 0.0) or 0.0))) or int(round(float(p.get("badge_height", 0.0) or 0.0))) or 1,
            anchor="left",
            retain_ratio=0.97 if not is_small else 0.96,
        )

        p = Action.enforceRightArmBadgeGeometry(
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
    def enforceVerticalConnectorBadgeGeometry(params: dict, w: int, h: int) -> dict:
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
    def tuneAc08VerticalConnectorFamily(name: str, params: dict) -> dict:
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
        is_small, _reason, min_dim = Action.isAc08SmallVariant(str(name), p)
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

        p = Action.enforceVerticalConnectorBadgeGeometry(
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
    def tuneAc08CircleTextFamily(name: str, params: dict) -> dict:
        """Apply shared guardrails for connector-free AC08 circle/text badges.

        Aufgabe 4.4 groups AC0820 and AC0870 because they both:
        - have no connector geometry that should influence circle fitting,
        - regress when text blobs pull the circle away from the semantic center,
        - need stable text scaling without letting the ring collapse or overgrow.
        """
        p = dict(params)
        symbol_name = getBaseNameFromFile(str(name)).upper().split("_", 1)[0]
        if symbol_name not in {"AC0820", "AC0870"}:
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
            canvas_cap = Action.maxCircleRadiusInsideCanvas(
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
            Action.centerGlyphBbox(p)

        return p

    @staticmethod
    def finalizeAc08Style(name: str, params: dict) -> dict:
        """Apply AC08xx palette/stroke conventions globally for semantic conversions."""
        canonical_name = str(name).upper()
        symbol_name = canonical_name.split("_", 1)[0]
        if not symbol_name.startswith("AC08"):
            return params
        p = Action.captureCanonicalBadgeColors(Action.normalizeLightCircleColors(dict(params)))
        p = Action.enforceSemanticComponentContract(canonical_name, p)
        p["badge_symbol_name"] = symbol_name
        # During geometry fitting we intentionally keep auto-estimated colors.
        # Canonical palette values are re-applied once fitting converged.
        p = Action.normalizeAc08LineWidths(p)
        p["lock_colors"] = True
        p = Action.normalizeCenteredCo2Label(p)
        if symbol_name == "AC0831" and str(p.get("text_mode", "")).lower() == "co2":
            p["fill_gray"] = 238
            p["stroke_gray"] = 155
            p["text_gray"] = 155
            if p.get("stem_enabled"):
                p["stem_gray"] = 155
        if symbol_name == "AC0833" and str(p.get("text_mode", "")).lower() == "co2":
            p = Action.tuneAc0833Co2Badge(p)
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
            if needsLargeCircleOverflowGuard(p) and image_width > 0.0:
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
                    p = Action.alignStemToCircleCenter(p)
                if p.get("arm_enabled"):
                    Action.reanchorArmToCircleEdge(p, float(p.get("r", 0.0)))
        if p.get("stem_enabled"):
            Action.persistConnectorLengthFloor(p, "stem", default_ratio=0.65)
        if p.get("arm_enabled"):
            Action.persistConnectorLengthFloor(p, "arm", default_ratio=0.75)
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
        p = Action.configureAc08SmallVariantMode(name, p)
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
            p["r"] = float(Action.clipScalar(float(p.get("r", template_r)), min_r, max_r))
        if p.get("draw_text", True) and "text_gray" in p:
            p["text_gray"] = int(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))
        return p

    @staticmethod
    def enforceSemanticComponentContract(name: str, params: dict) -> dict:
        """Strip components that are not part of the semantic symbol definition."""
        p = dict(params)
        canonical_name = str(name).upper()
        symbol_name = canonical_name.split("_", 1)[0]

        no_text_symbols = {"AC0800", "AC0810", "AC0811", "AC0812", "AC0813", "AC0814", "AC0881", "AC0882"}
        no_connector_symbols = {"AC0800", "AC0820", "AC0870"}
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
    def activateAc08AdaptiveLocks(
        params: dict,
        logs: list[str],
        *,
        full_err: float,
        reason: str,
    ) -> bool:
        """Adaptive AC08 locks are disabled so semantic badge fitting stays unconstrained."""
        return False

    @staticmethod
    def releaseAc08AdaptiveLocks(
        params: dict,
        logs: list[str],
        *,
        reason: str,
        current_error: float,
    ) -> bool:
        """Adaptive AC08 lock release is disabled because there are no AC08 locks to release."""
        return False

    @staticmethod
    def alignStemToCircleCenter(params: dict) -> dict:
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
    def defaultAc0870Params(w: int, h: int) -> dict:
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
        Action.centerGlyphBbox(params)
        return Action.normalizeLightCircleColors(params)

    @staticmethod
    def defaultAc0881Params(w: int, h: int) -> dict:
        params = Action.defaultAc0870Params(w, h)
        params["stem_enabled"] = True
        params["stem_width"] = max(1.0, params["r"] * 0.30)
        params["stem_x"] = params["cx"] - (params["stem_width"] / 2.0)
        params["stem_top"] = params["cy"] + (params["r"] * 0.60)
        params["stem_bottom"] = float(h)
        params["stem_gray"] = params["stroke_gray"]
        return params

    @staticmethod
    def defaultAc081xShared(w: int, h: int) -> dict:
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
    def defaultEdgeAnchoredCircleGeometry(
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
    def defaultAc0811Params(w: int, h: int) -> dict:
        """AC0811 is vertically elongated: circle sits in the upper square area."""
        if w <= 0 or h <= 0:
            return Action.defaultAc081xShared(w, h)

        circle = Action.defaultEdgeAnchoredCircleGeometry(w, h, anchor="top")
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

        return Action.normalizeLightCircleColors({
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
    def estimateUpperCircleFromForeground(img: np.ndarray, defaults: dict) -> tuple[float, float, float] | None:
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
        r = float(Action.clipScalar(r, min_r, max_r))
        cx = float(Action.clipScalar(cx, 0.0, float(w - 1)))
        cy = float(Action.clipScalar(cy, 0.0, float(h - 1)))
        return cx, cy, r

    @staticmethod
    def fitAc0811ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0811 while keeping the vertical stem anchored to the lower edge.

        AC0811 source symbols are noisy for thin vertical lines. Generic stem fitting can
        under-segment the line so the generated SVG misses parts of the lower connector.
        For this family we therefore fit the circle/tones from the image, but keep the stem
        geometry constrained to the semantic template (centered under the circle, extending
        to the image bottom).
        """
        params = Action.fitSemanticBadgeFromImage(img, defaults)
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
        upper_circle = Action.estimateUpperCircleFromForeground(img, defaults) if allow_upper_circle_estimate else None
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
            params["cy"] = float(Action.clipScalar(cy, default_cy - 1.0, default_cy + 1.0))
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
            r = float(Action.clipScalar(r, default_r * 0.95, default_r * 1.08))
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
            Action.persistConnectorLengthFloor(params, "stem", default_ratio=0.80)

        return Action.normalizeLightCircleColors(params)

    @staticmethod
    def defaultAc0882Params(w: int, h: int) -> dict:
        params = Action.defaultAc081xShared(w, h)
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
        Action.centerGlyphBbox(params)
        return params

    @staticmethod
    def applyCo2Label(params: dict) -> dict:
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
    def co2Layout(params: dict) -> dict[str, float | str]:
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
    def applyVocLabel(params: dict) -> dict:
        params["draw_text"] = True
        params["text_mode"] = "voc"
        params["text_gray"] = int(round(params.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))
        params["voc_font_scale"] = float(params.get("voc_font_scale", 0.52 * Action.SEMANTIC_TEXT_BASE_SCALE))
        params["voc_dy"] = float(params.get("voc_dy", -0.01 * float(params.get("r", 0.0))))
        params["voc_weight"] = int(params.get("voc_weight", 600))
        return params

    @staticmethod
    def tuneAc0832Co2Badge(params: dict) -> dict:
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
    def tuneAc0831Co2Badge(params: dict) -> dict:
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
    def tuneAc0835VocBadge(params: dict, w: int, h: int) -> dict:
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
    def tuneAc0833Co2Badge(params: dict) -> dict:
        """Tune AC0833 CO² badges so the trailing index stays superscript."""
        p = Action.normalizeLightCircleColors(dict(params))
        p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "cluster"))
        p["co2_index_mode"] = "superscript"
        p["co2_superscript_offset_scale"] = float(max(float(p.get("co2_superscript_offset_scale", 0.16)), 0.16))
        p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.17)), 0.17))
        return p

    @staticmethod
    def tuneAc0834Co2Badge(params: dict, w: int, h: int) -> dict:
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
    def defaultAc0834Params(w: int, h: int) -> dict:
        """Compatibility helper for AC0834 semantic tests and callers."""
        return Action.tuneAc0834Co2Badge(Action.applyCo2Label(Action.defaultAc0814Params(w, h)), w, h)

    @staticmethod
    def normalizeCenteredCo2Label(params: dict) -> dict:
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
    def defaultAc0812Params(w: int, h: int) -> dict:
        """AC0812 is horizontally elongated: left arm, circle on the right."""
        if w <= 0 or h <= 0:
            return Action.defaultAc081xShared(w, h)

        # Like AC0811/AC0813, size from the narrow side so tiny variants keep
        # the intended visual circle diameter.
        # AC0812 source rasters leave a slightly larger vertical margin around the
        # ring than AC0811/AC0813. Using 0.40*h tends to over-size the circle.
        r = float(h) * 0.36
        stroke_circle = max(0.9, float(h) / 15.0)
        cx = float(w) - (float(h) / 2.0)
        cy = float(h) / 2.0
        arm_stroke = max(1.0, float(h) * 0.10)

        return Action.normalizeLightCircleColors(
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
    def fitAc0812ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0812 while keeping the horizontal arm anchored to the left edge."""
        params = Action.fitSemanticBadgeFromImage(img, defaults)
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
        canvas_r_limit = Action.maxCircleRadiusInsideCanvas(cx, cy, w, h, stroke_circle)
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
        return Action.normalizeLightCircleColors(params)

    @staticmethod
    def enforceLeftArmBadgeGeometry(params: dict, w: int, h: int) -> dict:
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
    def enforceRightArmBadgeGeometry(params: dict, w: int, h: int) -> dict:
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
    def defaultAc0813Params(w: int, h: int) -> dict:
        """AC0813 is AC0812 rotated 90° clockwise (vertical arm from top to circle)."""
        if w <= 0 or h <= 0:
            return Action.defaultAc081xShared(w, h)

        # Like other edge-anchored connector badges, size from the narrow side and
        # keep a small optical clearance from the anchored edge.
        circle = Action.defaultEdgeAnchoredCircleGeometry(w, h, anchor="bottom")
        cx = float(circle["cx"])
        cy = float(circle["cy"])
        r = float(circle["r"])
        stroke_circle = float(circle["stroke_circle"])
        arm_stroke = max(1.0, float(w) * 0.10)

        return Action.normalizeLightCircleColors(
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
    def fitAc0813ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0813 while keeping the vertical arm anchored to the upper edge."""
        params = Action.fitSemanticBadgeFromImage(img, defaults)
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
            params["cy"] = float(Action.clipScalar(cy, default_cy - 0.8, default_cy + 0.8))
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
        return Action.normalizeLightCircleColors(params)

    @staticmethod
    def rotateSemanticBadgeClockwise(params: dict, w: int, h: int) -> dict:
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
    def defaultAc0814Params(w: int, h: int) -> dict:
        """AC0814 is horizontally elongated: circle on the left, arm to the right."""
        if w <= 0 or h <= 0:
            return Action.defaultAc081xShared(w, h)

        # AC0814_L-like originals use a noticeably larger ring than the earlier
        # generic AC081x template and keep a visible left margin before the
        # circle. A tighter template gets much closer to the hand-traced sample.
        r = float(h) * 0.46
        stroke_circle = max(0.9, float(h) / 25.0)
        left_margin = max(stroke_circle * 0.5, float(h) * 0.18)
        cx = r + left_margin
        cy = float(h) / 2.0
        arm_stroke = max(1.0, stroke_circle)

        return Action.normalizeLightCircleColors(
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
    def fitAc0814ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0814 while keeping the horizontal arm anchored to the right edge."""
        params = Action.fitSemanticBadgeFromImage(img, defaults)
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
            params["cy"] = float(Action.clipScalar(cy, default_cy - 0.5, default_cy + 0.5))
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
                corrected_cx = float(Action.clipScalar(cx, default_cx - max_left_correction, default_cx))
            params["cx"] = corrected_cx
            if medium_plain_canvas:
                params["template_circle_cx"] = corrected_cx
            params["cy"] = float(Action.clipScalar(cy, default_cy - 0.6, default_cy + 0.6))
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
        return Action.normalizeLightCircleColors(params)

    @staticmethod
    def defaultAc0810Params(w: int, h: int) -> dict:
        """AC0810 uses the same right-arm geometry as AC0814 (circle on the left)."""
        return Action.defaultAc0814Params(w, h)

    @staticmethod
    def fitAc0810ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
        """Fit AC0810 with the same right-anchored arm behavior as AC0814."""
        return Action.fitAc0814ParamsFromImage(img, defaults)

    @staticmethod
    def glyphBbox(text_mode: str) -> tuple[int, int, int, int]:
        if text_mode == "path_t":
            return Action.T_XMIN, Action.T_YMIN, Action.T_XMAX, Action.T_YMAX
        return Action.M_XMIN, Action.M_YMIN, Action.M_XMAX, Action.M_YMAX

    @staticmethod
    def centerGlyphBbox(params: dict) -> None:
        if "s" not in params or "cx" not in params or "cy" not in params:
            return
        xmin, ymin, xmax, ymax = Action.glyphBbox(params.get("text_mode", "path"))
        glyph_width = (xmax - xmin) * params["s"]
        glyph_height = (ymax - ymin) * params["s"]
        params["tx"] = float(params["cx"] - (glyph_width / 2.0))
        params["ty"] = float(params["cy"] - (glyph_height / 2.0))

    @staticmethod
    def stabilizeSemanticCirclePose(params: dict, defaults: dict, w: int, h: int) -> dict:
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

    def fitAc0870ParamsFromImage(img: np.ndarray, defaults: dict) -> dict:
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

            Action.centerGlyphBbox(params)

            params["fill_gray"] = int(np.median(inner_vals))

        if np.any(ring_mask):
            params["stroke_gray"] = int(np.median(gray[ring_mask]))

        return params

    @staticmethod
    def fitSemanticBadgeFromImage(img: np.ndarray, defaults: dict) -> dict:
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
                est_fill, est_ring, est_stroke = Action.estimateCircleTonesAndStroke(
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
                    bg_gray = Action.estimateBorderBackgroundGray(gray)
                    if bg_gray >= 240.0:
                        params["background_fill"] = "#ffffff"

        if not bool(params.get("arm_enabled") or params.get("stem_enabled")) and not bool(params.get("draw_text", False)):
            fg_mask = Action.foregroundMask(img)
            edge_touch_min = max(2, int(round(min_side * 0.20)))
            touches_all_edges = all(
                int(np.count_nonzero(edge)) >= edge_touch_min
                for edge in (fg_mask[0, :], fg_mask[-1, :], fg_mask[:, 0], fg_mask[:, -1])
            )
            if not touches_all_edges:
                # JPEG-soft tiny rings may miss foreground pixels on one edge.
                # Use a grayscale border cue as permissive fallback.
                bg_gray = Action.estimateBorderBackgroundGray(gray)
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
                params["r"] = float(Action.clipScalar(float(params.get("r", default_r)), min_r, max_r))

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

        params = Action.stabilizeSemanticCirclePose(params, defaults, w, h)

        if params.get("draw_text", True) and params.get("text_mode") in {"path", "path_t"}:
            Action.centerGlyphBbox(params)
        return Action.normalizeLightCircleColors(params)

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
            Action.centerGlyphBbox(params)
            return params

        if name == "AC0870":
            defaults = Action.defaultAc0870Params(w, h)
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitAc0870ParamsFromImage(img, defaults))

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
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitSemanticBadgeFromImage(img, defaults))

        if name == "AC0811":
            defaults = Action.defaultAc0811Params(w, h)
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitAc0811ParamsFromImage(img, defaults))

        if name == "AC0810":
            defaults = Action.defaultAc0810Params(w, h)
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitAc0810ParamsFromImage(img, defaults))

        if name == "AC0812":
            defaults = Action.defaultAc0812Params(w, h)
            if img is None:
                return Action.enforceLeftArmBadgeGeometry(Action.finalizeAc08Style(name, defaults), w, h)
            return Action.enforceLeftArmBadgeGeometry(
                Action.finalizeAc08Style(name, Action.fitAc0812ParamsFromImage(img, defaults)),
                w,
                h,
            )

        if name == "AC0813":
            defaults = Action.defaultAc0813Params(w, h)
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitAc0813ParamsFromImage(img, defaults))

        if name == "AC0814":
            defaults = Action.defaultAc0814Params(w, h)
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitAc0814ParamsFromImage(img, defaults))

        if name == "AC0881":
            defaults = Action.defaultAc0881Params(w, h)
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitSemanticBadgeFromImage(img, defaults))

        if name == "AC0882":
            defaults = Action.defaultAc0882Params(w, h)
            if img is None:
                return Action.enforceLeftArmBadgeGeometry(Action.finalizeAc08Style(name, defaults), w, h)
            return Action.enforceLeftArmBadgeGeometry(
                Action.finalizeAc08Style(name, Action.fitSemanticBadgeFromImage(img, defaults)),
                w,
                h,
            )

        if name == "AC0820":
            defaults = Action.applyCo2Label(Action.defaultAc0870Params(w, h))
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.applyCo2Label(Action.fitSemanticBadgeFromImage(img, defaults)))

        if name == "AC0831":
            defaults = Action.applyCo2Label(Action.defaultAc0881Params(w, h))
            if img is None:
                return Action.finalizeAc08Style(name, Action.tuneAc0831Co2Badge(defaults))
            return Action.finalizeAc08Style(
                name,
                Action.tuneAc0831Co2Badge(Action.fitAc0811ParamsFromImage(img, defaults)),
            )

        if name == "AC0832":
            defaults = Action.applyCo2Label(Action.defaultAc0812Params(w, h))
            if img is None:
                return Action.enforceLeftArmBadgeGeometry(
                    Action.finalizeAc08Style(name, Action.tuneAc0832Co2Badge(defaults)),
                    w,
                    h,
                )
            return Action.enforceLeftArmBadgeGeometry(
                Action.finalizeAc08Style(
                    name,
                    Action.tuneAc0832Co2Badge(Action.fitAc0812ParamsFromImage(img, defaults)),
                ),
                w,
                h,
            )

        if name == "AC0833":
            defaults = Action.tuneAc0833Co2Badge(Action.applyCo2Label(Action.defaultAc0813Params(w, h)))
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.tuneAc0833Co2Badge(Action.fitAc0813ParamsFromImage(img, defaults)))

        if name == "AC0834":
            defaults = Action.applyCo2Label(Action.defaultAc0814Params(w, h))
            if img is None:
                return Action.finalizeAc08Style(name, Action.tuneAc0834Co2Badge(defaults, w, h))
            return Action.finalizeAc08Style(
                name,
                Action.tuneAc0834Co2Badge(
                    Action.fitAc0814ParamsFromImage(img, defaults),
                    w,
                    h,
                ),
            )

        if name == "AC0835":
            # AC0835 belongs to the right-arm VOC connector family.
            defaults = Action.applyVocLabel(Action.defaultAc0814Params(w, h))
            if img is None:
                return Action.finalizeAc08Style(name, Action.tuneAc0835VocBadge(defaults, w, h))
            return Action.finalizeAc08Style(
                name,
                Action.tuneAc0835VocBadge(
                    Action.fitAc0814ParamsFromImage(img, defaults),
                    w,
                    h,
                ),
            )

        if name == "AC0836":
            defaults = Action.applyVocLabel(Action.defaultAc0881Params(w, h))
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitAc0811ParamsFromImage(img, defaults))

        if name == "AC0837":
            defaults = Action.applyVocLabel(Action.defaultAc0812Params(w, h))
            if img is None:
                return Action.enforceLeftArmBadgeGeometry(Action.finalizeAc08Style(name, defaults), w, h)
            return Action.enforceLeftArmBadgeGeometry(
                Action.finalizeAc08Style(name, Action.fitAc0812ParamsFromImage(img, defaults)),
                w,
                h,
            )

        if name == "AC0838":
            # AC0838 is part of the right-arm VOC family (same geometry class as
            # AC0814/AC0839), not the top-stem family.
            defaults = Action.applyVocLabel(Action.defaultAc0814Params(w, h))
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitAc0814ParamsFromImage(img, defaults))

        if name == "AC0839":
            defaults = Action.applyVocLabel(Action.defaultAc0814Params(w, h))
            if img is None:
                return Action.finalizeAc08Style(name, defaults)
            return Action.finalizeAc08Style(name, Action.fitAc0814ParamsFromImage(img, defaults))

        return None

    @staticmethod
    def generateBadgeSvg(w: int, h: int, p: dict) -> str:
        p = Action.alignStemToCircleCenter(dict(p))
        p = Action.quantizeBadgeParams(p, w, h)
        elements = [
            f'<svg width="{w}px" height="{h}px" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        ]

        background_fill = p.get("background_fill")
        if background_fill:
            elements.append(
                f'  <rect x="0" y="0" width="{float(w):.4f}" height="{float(h):.4f}" fill="{background_fill}"/>'
            )

        if p.get("arm_enabled"):
            arm_x1 = float(Action.clipScalar(float(p.get("arm_x1", 0.0)), 0.0, float(w)))
            arm_y1 = float(Action.clipScalar(float(p.get("arm_y1", p.get("arm_y", 0.0))), 0.0, float(h)))
            arm_x2 = float(Action.clipScalar(float(p.get("arm_x2", 0.0)), 0.0, float(w)))
            arm_y2 = float(Action.clipScalar(float(p.get("arm_y2", p.get("arm_y", arm_y1))), 0.0, float(h)))
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
            stem_x = float(Action.clipScalar(float(p.get("stem_x", 0.0)), 0.0, float(w)))
            stem_top = float(Action.clipScalar(float(p.get("stem_top", 0.0)), 0.0, float(h)))
            stem_width = max(0.0, min(float(p.get("stem_width", 0.0)), max(0.0, float(w) - stem_x)))
            stem_bottom = float(Action.clipScalar(float(p.get("stem_bottom", 0.0)), stem_top, float(h)))
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
                layout = Action.co2Layout(p)
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
        if SVG_RENDER_SUBPROCESS_ENABLED:
            rendered = renderSvgToNumpyViaSubprocess(svg_string, size_w, size_h)
            if rendered is not None:
                return rendered
        return renderSvgToNumpyInprocess(svg_string, size_w, size_h)

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
    def fitToOriginalSize(img_orig: np.ndarray, img_svg: np.ndarray | None) -> np.ndarray | None:
        if img_svg is None:
            return None
        if img_svg.shape[:2] == img_orig.shape[:2]:
            return img_svg
        return cv2.resize(img_svg, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)

    @staticmethod
    def maskCentroidRadius(mask: np.ndarray) -> tuple[float, float, float] | None:
        ys, xs = np.where(mask)
        if xs.size < 5:
            return None
        cx = float(np.mean(xs))
        cy = float(np.mean(ys))
        r = float(np.sqrt(xs.size / np.pi))
        return cx, cy, r

    @staticmethod
    def maskBbox(mask: np.ndarray) -> tuple[float, float, float, float] | None:
        ys, xs = np.where(mask)
        if xs.size < 3:
            return None
        x1, x2 = float(xs.min()), float(xs.max())
        y1, y2 = float(ys.min()), float(ys.max())
        return x1, y1, x2, y2

    @staticmethod
    def maskCenterSize(mask: np.ndarray) -> tuple[float, float, float] | None:
        bbox = Action.maskBbox(mask)
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
    def maskMinRectCenterDiag(mask: np.ndarray) -> tuple[float, float, float] | None:
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
    def elementBboxChangeIsPlausible(
        mask_orig: np.ndarray,
        mask_svg: np.ndarray,
    ) -> tuple[bool, str | None]:
        """Reject clearly implausible box drifts between source and converted element."""
        orig_bbox = Action.maskBbox(mask_orig)
        svg_bbox = Action.maskBbox(mask_svg)
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
    def applyElementAlignmentStep(
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
        scale = float(Action.clipScalar(diag_scale, 0.85, 1.18))

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
                params["cx"] = float(Action.clipScalar(old_cx + center_dx * 0.65, 0.0, float(w - 1)))
            if bool(params.get("lock_circle_cy", False)):
                params["cy"] = old_cy
            else:
                params["cy"] = float(Action.clipScalar(old_cy + center_dy * 0.65, 0.0, float(h - 1)))
            params["r"] = float(Action.clipScalar(old_r * scale, min_r, max_r))
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
                stem_cx = float(Action.clipScalar(stem_cx + center_dx * 0.75, 0.0, float(w - 1)))
            new_w = float(Action.clipScalar(old_w * scale, 1.0, float(w) * 0.22))
            params["stem_width"] = new_w
            params["stem_x"] = float(Action.clipScalar(stem_cx - (new_w / 2.0), 0.0, float(w) - new_w))
            params["stem_top"] = float(Action.clipScalar(old_top + center_dy * 0.45, 0.0, float(h - 2)))
            params["stem_bottom"] = float(Action.clipScalar(old_bottom + center_dy * 0.25, params["stem_top"] + 1.0, float(h - 1)))
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

            params["arm_x1"] = float(Action.clipScalar(acx - (vx / 2.0), 0.0, float(w - 1)))
            params["arm_x2"] = float(Action.clipScalar(acx + (vx / 2.0), 0.0, float(w - 1)))
            params["arm_y1"] = float(Action.clipScalar(acy - (vy / 2.0), 0.0, float(h - 1)))
            params["arm_y2"] = float(Action.clipScalar(acy + (vy / 2.0), 0.0, float(h - 1)))
            params["arm_stroke"] = float(Action.clipScalar(old_stroke * scale, 1.0, float(min(w, h)) * 0.18))
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
                params["co2_dy"] = float(Action.clipScalar(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
                changed = abs(params["co2_dy"] - old_dy) > 0.02
            elif mode == "voc":
                old_dy = float(params.get("voc_dy", 0.0))
                params["voc_dy"] = float(Action.clipScalar(old_dy + center_dy * 0.75, -0.45 * r, 0.45 * r))
                changed = abs(params["voc_dy"] - old_dy) > 0.02
            elif "ty" in params:
                old_ty = float(params.get("ty", 0.0))
                params["ty"] = float(Action.clipScalar(old_ty + center_dy * 0.75, 0.0, float(h - 1)))
                changed = abs(params["ty"] - old_ty) > 0.02

        return changed

    @staticmethod
    def estimateVerticalStemFromMask(
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
    def ringAndFillMasks(h: int, w: int, params: dict) -> tuple[np.ndarray, np.ndarray]:
        yy, xx = np.indices((h, w))
        dist = np.sqrt((xx - params["cx"]) ** 2 + (yy - params["cy"]) ** 2)
        ring_half = max(0.7, params["stroke_circle"])
        ring = np.abs(dist - params["r"]) <= ring_half
        fill = dist <= max(0.5, params["r"] - ring_half)
        return ring, fill

    @staticmethod
    def meanGrayForMask(img: np.ndarray, mask: np.ndarray) -> float | None:
        if int(mask.sum()) == 0:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        vals = gray[mask]
        if vals.size == 0:
            return None
        return float(np.mean(vals))

    @staticmethod
    def elementRegionMask(
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
            x1, y1, x2, y2 = Action.textBbox(params)
            x1 = max(0.0, x1 - context_pad)
            y1 = max(0.0, y1 - context_pad)
            x2 = min(float(w), x2 + context_pad)
            y2 = min(float(h), y2 + context_pad)
            return (xx >= x1) & (xx <= x2) & (yy >= y1) & (yy <= y2)
        return None

    @staticmethod
    def textBbox(params: dict) -> tuple[float, float, float, float]:
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
            layout = Action.co2Layout(params)
            x1 = float(layout["x1"])
            x2 = float(layout["x2"])
            y = float(layout["y_base"])
            height = float(layout["height"])
            return (x1, y - (height / 2.0), x2, y + (height / 2.0))

        # path/path_t fallback via known glyph bounds.
        s = float(params.get("s", 0.0))
        tx = float(params.get("tx", cx))
        ty = float(params.get("ty", cy))
        xmin, ymin, xmax, ymax = Action.glyphBbox(params.get("text_mode", "path"))
        x1 = tx + (xmin * s)
        y1 = ty + (ymin * s)
        x2 = tx + (xmax * s)
        y2 = ty + (ymax * s)
        return (x1, y1, x2, y2)

    @staticmethod
    def foregroundMask(img: np.ndarray) -> np.ndarray:
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
    def circleFromForegroundMask(fg_mask: np.ndarray) -> tuple[float, float, float] | None:
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
    def maskSupportsCircle(mask: np.ndarray | None) -> bool:
        if mask is None:
            return False
        pixel_count = int(np.count_nonzero(mask))
        if pixel_count < 4:
            return False

        bbox = Action.maskBbox(mask)
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
        region_mask = Action.elementRegionMask(h, w, params, element)
        if region_mask is None:
            return None

        fg_bool = Action.foregroundMask(img_orig)
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
    def elementOnlyParams(params: dict, element: str) -> dict:
        only = dict(params)
        only["draw_text"] = bool(params.get("draw_text", True) and element == "text")
        only["circle_enabled"] = element == "circle"
        only["stem_enabled"] = bool(params.get("stem_enabled") and element == "stem")
        only["arm_enabled"] = bool(params.get("arm_enabled") and element == "arm")
        return only

    @staticmethod
    def maskedError(img_orig: np.ndarray, img_svg: np.ndarray, mask: np.ndarray | None) -> float:
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
    def unionBboxFromMasks(mask_a: np.ndarray | None, mask_b: np.ndarray | None) -> tuple[int, int, int, int] | None:
        boxes: list[tuple[float, float, float, float]] = []
        if mask_a is not None:
            box_a = Action.maskBbox(mask_a)
            if box_a is not None:
                boxes.append(box_a)
        if mask_b is not None:
            box_b = Action.maskBbox(mask_b)
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
    def maskedUnionErrorInBbox(
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

        bbox = Action.unionBboxFromMasks(mask_orig, mask_svg)
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
    def elementMatchError(
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

        local_mask_orig = mask_orig if mask_orig is not None else Action.extractBadgeElementMask(img_orig, params, element)
        local_mask_svg = mask_svg if mask_svg is not None else Action.extractBadgeElementMask(img_svg, params, element)
        if local_mask_orig is None or local_mask_svg is None:
            return float("inf")

        orig_area = float(np.sum(local_mask_orig))
        svg_area = float(np.sum(local_mask_svg))
        if orig_area <= 0.0 or svg_area <= 0.0:
            return float("inf")

        photo_err = float(Action.maskedUnionErrorInBbox(img_orig, img_svg, local_mask_orig, local_mask_svg))
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
            src_circle = Action.maskCentroidRadius(local_mask_orig)
            cand_circle = Action.maskCentroidRadius(local_mask_svg)
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
    def captureCanonicalBadgeColors(params: dict) -> dict:
        p = dict(params)
        p["target_fill_gray"] = int(round(float(p.get("fill_gray", Action.LIGHT_CIRCLE_FILL_GRAY))))
        p["target_stroke_gray"] = int(round(float(p.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY))))
        if p.get("stem_enabled"):
            p["target_stem_gray"] = int(round(float(p.get("stem_gray", p["target_stroke_gray"]))))
        if p.get("draw_text", True) and "text_gray" in p:
            p["target_text_gray"] = int(round(float(p.get("text_gray", Action.LIGHT_CIRCLE_TEXT_GRAY))))
        return p

    @staticmethod
    def applyCanonicalBadgeColors(params: dict) -> dict:
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
    def circleBounds(params: dict, w: int, h: int) -> tuple[float, float, float, float, float, float]:
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
            max_r = min(max_r, Action.maxCircleRadiusInsideCanvas(cx, cy, w, h, stroke))
        if "max_circle_radius" in params:
            max_r = min(max_r, float(params.get("max_circle_radius", max_r)))
        return 0.0, float(w - 1), 0.0, float(h - 1), min_r, max_r

    @staticmethod
    def globalParameterVectorBounds(params: dict, w: int, h: int) -> dict[str, tuple[float, float, bool, str]]:
        """Return central bounds/lock metadata for the shared optimization vector."""
        x_low, x_high, y_low, y_high, r_low, r_high = Action.circleBounds(params, w, h)
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
    def logGlobalParameterVector(logs: list[str], params: dict, w: int, h: int, *, label: str) -> None:
        vector = GlobalParameterVector.fromParams(params)
        bounds = Action.globalParameterVectorBounds(params, w, h)

        def fmtValue(value: float | None) -> str:
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
    def stochasticSurvivorScalar(
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
        cur = float(snap(float(Action.clipScalar(current_value, low, high))))
        best_value = cur
        best_err = float(evaluate(best_value))
        if not math.isfinite(best_err):
            return best_value, best_err, False

        rng = Action.makeRng(int(seed) + int(Action.STOCHASTIC_SEED_OFFSET))
        span = max(0.5, abs(high - low) * 0.22)
        improved = False
        stable_rounds = 0

        for _ in range(max(1, iterations)):
            candidates = [best_value]
            for _j in range(2):
                sample = float(Action.clipScalar(rng.normal(best_value, span), low, high))
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
    def optimizeCirclePoseStochasticSurvivor(
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
        Action.logGlobalParameterVector(logs, params, w, h, label="circle: survivor-start")
        x_low, x_high, y_low, y_high, r_low, r_high = Action.circleBounds(params, w, h)
        current = (
            Action.snapHalf(float(params.get("cx", (w - 1) / 2.0))),
            Action.snapHalf(float(params.get("cy", (h - 1) / 2.0))),
            Action.snapHalf(float(params.get("r", max(1.0, min(w, h) * 0.3)))),
        )
        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))
        rng = Action.makeRng(835 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))

        def evalPose(candidate: tuple[float, float, float]) -> float:
            cx, cy, rad = candidate
            return float(
                Action.elementErrorForCirclePose(
                    img_orig,
                    params,
                    cx_value=cx,
                    cy_value=cy,
                    radius_value=rad,
                )
            )

        best = current
        best_err = evalPose(best)
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
                    cx = Action.snapHalf(float(Action.clipScalar(rng.normal(best[0], spread_xy), x_low, x_high)))
                if lock_cy:
                    cy = best[1]
                else:
                    cy = Action.snapHalf(float(Action.clipScalar(rng.normal(best[1], spread_xy), y_low, y_high)))
                rad = Action.snapHalf(float(Action.clipScalar(rng.normal(best[2], spread_r), r_low, r_high)))
                cand = (cx, cy, rad)
                candidates.append((cand, evalPose(cand)))

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

        updated_vector = GlobalParameterVector.fromParams(params)
        updated_vector = dataclasses.replace(updated_vector, cx=best[0], cy=best[1], r=best[2])
        params.update(updated_vector.applyToParams(params))
        if params.get("arm_enabled"):
            Action.reanchorArmToCircleEdge(params, best[2])
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best[2]
        Action.logGlobalParameterVector(logs, params, w, h, label="circle: survivor-final")
        logs.append(
            f"circle: Stochastic-Survivor übernommen (cx={best[0]:.3f}, cy={best[1]:.3f}, r={best[2]:.3f}, err={best_err:.3f})"
        )
        return True

    @staticmethod
    def optimizeCirclePoseAdaptiveDomain(
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
        Action.logGlobalParameterVector(logs, params, w, h, label="circle: adaptive-start")
        x_low, x_high, y_low, y_high, r_low, r_high = Action.circleBounds(params, w, h)
        lock_cx = bool(params.get("lock_circle_cx", False))
        lock_cy = bool(params.get("lock_circle_cy", False))

        current = (
            Action.snapHalf(float(params.get("cx", (w - 1) / 2.0))),
            Action.snapHalf(float(params.get("cy", (h - 1) / 2.0))),
            Action.snapHalf(float(params.get("r", max(1.0, min(w, h) * 0.3)))),
        )

        def clampPose(candidate: tuple[float, float, float]) -> tuple[float, float, float]:
            cx, cy, rad = candidate
            if lock_cx:
                cx = current[0]
            else:
                cx = Action.snapHalf(float(Action.clipScalar(cx, x_low, x_high)))
            if lock_cy:
                cy = current[1]
            else:
                cy = Action.snapHalf(float(Action.clipScalar(cy, y_low, y_high)))
            rad = Action.snapHalf(float(Action.clipScalar(rad, r_low, r_high)))
            return cx, cy, rad

        cache: dict[tuple[float, float, float], float] = {}

        def evalPose(candidate: tuple[float, float, float]) -> float:
            pose = clampPose(candidate)
            if pose not in cache:
                cache[pose] = float(
                    Action.elementErrorForCirclePose(
                        img_orig,
                        params,
                        cx_value=pose[0],
                        cy_value=pose[1],
                        radius_value=pose[2],
                    )
                )
            return cache[pose]

        best = clampPose(current)
        best_err = evalPose(best)
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

        rng = Action.makeRng(2027 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))
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
                pose = clampPose((cx, cy, rad))
                samples.append((pose, evalPose(pose)))

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
            plateau_mid = clampPose(((pmin_cx + pmax_cx) / 2.0, (pmin_cy + pmax_cy) / 2.0, (pmin_r + pmax_r) / 2.0))
            plateau_mid_err = evalPose(plateau_mid)

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
            round_vector = GlobalParameterVector.fromParams(params)
            round_vector = dataclasses.replace(round_vector, cx=best[0], cy=best[1], r=best[2])
            round_params = round_vector.applyToParams(params)
            Action.logGlobalParameterVector(logs, round_params, w, h, label=f"circle: Runde {_round + 1}")

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

        updated_vector = GlobalParameterVector.fromParams(params)
        updated_vector = dataclasses.replace(updated_vector, cx=best[0], cy=best[1], r=best[2])
        params.update(updated_vector.applyToParams(params))
        if params.get("arm_enabled"):
            Action.reanchorArmToCircleEdge(params, best[2])
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best[2]
        Action.logGlobalParameterVector(logs, params, w, h, label="circle: adaptive-final")

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
    def fullBadgeErrorForParams(img_orig: np.ndarray, params: dict) -> float:
        """Evaluate full-image error for an already prepared badge parameter dict."""
        h, w = img_orig.shape[:2]
        render = Action.fitToOriginalSize(
            img_orig,
            Action.renderSvgToNumpy(Action.generateBadgeSvg(w, h, params), w, h),
        )
        if render is None:
            return float("inf")
        return float(Action.calculateError(img_orig, render))

    @staticmethod
    def optimizeGlobalParameterVectorSampling(
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
        bounds = Action.globalParameterVectorBounds(params, w, h)
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
                clipped = float(Action.clipScalar(current_value, low, high))
                if key in {"cx", "cy", "r", "stem_x", "stem_width", "text_x", "text_y"}:
                    clipped = float(Action.snapHalf(clipped))
                data[key] = clipped
            return GlobalParameterVector(**data)

        def evalVector(candidate: GlobalParameterVector) -> float:
            probe = candidate.applyToParams(params)
            if probe.get("arm_enabled"):
                Action.reanchorArmToCircleEdge(probe, float(probe.get("r", 0.0)))
            if probe.get("stem_enabled"):
                probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe.get("r", 0.0))
                if bool(probe.get("lock_stem_center_to_circle", False)):
                    stem_w = float(probe.get("stem_width", 1.0))
                    probe["stem_x"] = Action.snapHalf(
                        max(0.0, min(float(w) - stem_w, float(probe.get("cx", 0.0)) - (stem_w / 2.0)))
                    )
            return Action.fullBadgeErrorForParams(img_orig, probe)

        def withinHardBounds(candidate: GlobalParameterVector) -> tuple[bool, str]:
            for key in active_keys:
                low, high, _locked, _source = bounds[key]
                value = float(getattr(candidate, key))
                if value < low - 1e-6 or value > high + 1e-6:
                    return False, f"{key}={value:.3f} außerhalb [{low:.3f}, {high:.3f}]"
            return True, "ok"

        rng = Action.makeRng(4099 + int(Action.STOCHASTIC_RUN_SEED) + int(Action.STOCHASTIC_SEED_OFFSET))
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
                    sample_data[key] = float(Action.clipScalar(rng.normal(float(sample_data[key]), sigma), low, high))
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
            Action.reanchorArmToCircleEdge(params, float(params.get("r", 0.0)))
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + float(params.get("r", 0.0))
        Action.logGlobalParameterVector(logs, params, w, h, label="global-search: final")
        logs.append(
            "global-search: übernommen "
            f"(best_err={best_err:.3f}, verbessert={', '.join(delta_labels) if delta_labels else 'keine sichtbare delta-liste'})"
        )
        return True

    @staticmethod
    def enforceSemanticConnectorExpectation(base_name: str, semantic_elements: list[str], params: dict, w: int, h: int) -> dict:
        """Restore mandatory connector geometry for directional semantic badges."""
        normalized_base = getBaseNameFromFile(str(base_name)).upper()
        normalized_elements = [str(elem).lower() for elem in (semantic_elements or [])]
        expects_left_arm = any("waagrechter strich links" in elem for elem in normalized_elements)
        expects_right_arm = any("waagrechter strich rechts" in elem for elem in normalized_elements)

        # AC0812/AC0837/AC0882 are directional left-arm families. If noisy element
        # extraction temporarily drops arm flags, regenerate canonical connector geometry
        # from the fitted circle before final SVG serialization.
        if normalized_base in {"AC0812", "AC0837", "AC0882"} or expects_left_arm:
            return Action.enforceLeftArmBadgeGeometry(params, w, h)
        if normalized_base in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"} or expects_right_arm:
            return Action.enforceRightArmBadgeGeometry(params, w, h)
        return params

    @staticmethod
    def elementWidthKeyAndBounds(
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
                    text_mask = Action.extractBadgeElementMask(img_orig, params, "text")
                    bbox = Action.maskBbox(text_mask) if text_mask is not None else None
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
    def elementErrorForWidth(img_orig: np.ndarray, params: dict, element: str, width_value: float) -> float:
        h, w = img_orig.shape[:2]
        probe = dict(params)
        info = Action.elementWidthKeyAndBounds(element, probe, w, h, img_orig=img_orig)
        if info is None:
            return float("inf")
        key, low, high = info
        probe[key] = float(Action.clipScalar(width_value, low, high))
        if key == "stem_width" and probe.get("stem_enabled"):
            probe["stem_x"] = float(probe.get("cx", probe.get("stem_x", 0.0))) - (probe["stem_width"] / 2.0)
        elem_svg = Action.generateBadgeSvg(w, h, Action.elementOnlyParams(probe, element))
        elem_render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")
        mask_orig = Action.extractBadgeElementMask(img_orig, probe, element)
        if mask_orig is None:
            return float("inf")
        return Action.elementMatchError(img_orig, elem_render, probe, element, mask_orig=mask_orig)

    @staticmethod
    def elementErrorForCircleRadius(img_orig: np.ndarray, params: dict, radius_value: float) -> float:
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
        probe["r"] = float(Action.clipScalar(radius_value, min_r, max_r))
        probe = Action.clampCircleInsideCanvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action.reanchorArmToCircleEdge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        elem_svg = Action.generateBadgeSvg(w, h, Action.elementOnlyParams(probe, "circle"))
        elem_render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(elem_svg, w, h))
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
            Action.reanchorArmToCircleEdge(source_mask_params, float(source_mask_params["r"]))
        if source_mask_params.get("stem_enabled"):
            source_mask_params["stem_top"] = float(source_mask_params.get("cy", 0.0)) + float(source_mask_params["r"])

        mask_orig = Action.extractBadgeElementMask(img_orig, source_mask_params, "circle")
        if mask_orig is None:
            return float("inf")
        mask_svg = Action.extractBadgeElementMask(elem_render, probe, "circle")
        if mask_svg is None:
            return float("inf")

        return Action.elementMatchError(
            img_orig,
            elem_render,
            probe,
            "circle",
            mask_orig=mask_orig,
            mask_svg=mask_svg,
        )

    @staticmethod
    def fullBadgeErrorForCircleRadius(img_orig: np.ndarray, params: dict, radius_value: float) -> float:
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
        probe["r"] = float(Action.clipScalar(radius_value, min_r, max_r))
        probe = Action.clampCircleInsideCanvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action.reanchorArmToCircleEdge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(Action.generateBadgeSvg(w, h, probe), w, h))
        if render is None:
            return float("inf")
        return float(Action.calculateError(img_orig, render))

    @staticmethod
    def selectCircleRadiusPlateauCandidate(
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
                full_err = float(Action.fullBadgeErrorForCircleRadius(img_orig, params, best_radius))
            except Exception:
                full_err = float("inf")
            return best_radius, best_err, full_err

        plateau_mid = Action.snapHalf((plateau[0][0] + plateau[-1][0]) / 2.0)
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
            float(Action.clipScalar(Action.snapHalf(float(radius)), min_r, max_r))
            for radius in candidate_radii
        )

        choice_pool: list[tuple[float, float, float, float]] = []
        for radius in bounded_candidates:
            if radius in evaluations:
                elem_err = float(evaluations[radius])
            else:
                try:
                    elem_err = float(Action.elementErrorForCircleRadius(img_orig, params, radius))
                except Exception:
                    elem_err = float("inf")
            try:
                full_err = float(Action.fullBadgeErrorForCircleRadius(img_orig, params, radius))
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
    def elementErrorForCirclePose(
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
        probe["cx"] = Action.snapHalf(float(Action.clipScalar(cx_value, 0.0, float(w - 1))))
        probe["cy"] = Action.snapHalf(float(Action.clipScalar(cy_value, 0.0, float(h - 1))))
        min_r = float(max(1.0, probe.get("min_circle_radius", 1.0)))
        probe["r"] = Action.snapHalf(float(Action.clipScalar(radius_value, min_r, max_r)))
        probe = Action.clampCircleInsideCanvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action.reanchorArmToCircleEdge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        elem_svg = Action.generateBadgeSvg(w, h, Action.elementOnlyParams(probe, "circle"))
        elem_render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        # See `_element_error_for_circle_radius`: use a stable source mask that
        # is independent from the tested candidate pose.
        mask_orig = Action.extractBadgeElementMask(img_orig, params, "circle")
        if mask_orig is None:
            return float("inf")
        mask_svg = Action.extractBadgeElementMask(elem_render, probe, "circle")
        if mask_svg is None:
            return float("inf")

        return Action.elementMatchError(
            img_orig,
            elem_render,
            probe,
            "circle",
            mask_orig=mask_orig,
            mask_svg=mask_svg,
        )

    @staticmethod
    def reanchorArmToCircleEdge(params: dict, radius: float) -> None:
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
    def optimizeCircleCenterBracket(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
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
        x_low = Action.snapHalf(max(0.0, current_cx - max_shift))
        x_high = Action.snapHalf(min(float(w - 1), current_cx + max_shift))
        y_low = Action.snapHalf(max(0.0, current_cy - max_shift))
        y_high = Action.snapHalf(min(float(h - 1), current_cy + max_shift))

        evaluations: dict[tuple[float, float], float] = {}

        def evalCenter(cx_value: float, cy_value: float) -> float:
            cx_snap = Action.snapHalf(float(Action.clipScalar(cx_value, 0.0, float(w - 1))))
            cy_snap = Action.snapHalf(float(Action.clipScalar(cy_value, 0.0, float(h - 1))))
            key = (cx_snap, cy_snap)
            if key not in evaluations:
                probe = dict(params)
                probe["cx"] = cx_snap
                probe["cy"] = cy_snap
                evaluations[key] = float(Action.elementErrorForCircleRadius(img_orig, probe, current_r))
            return evaluations[key]

        def optimizeAxis(low: float, high: float, fixed: float, axis: str) -> float:
            if high - low < 0.05:
                return Action.snapHalf((low + high) / 2.0)
            mid = Action.snapHalf((low + high) / 2.0)
            for _ in range(8):
                if axis == "x":
                    low_err = evalCenter(low, fixed)
                    mid_err = evalCenter(mid, fixed)
                    high_err = evalCenter(high, fixed)
                else:
                    low_err = evalCenter(fixed, low)
                    mid_err = evalCenter(fixed, mid)
                    high_err = evalCenter(fixed, high)

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
                next_mid = Action.snapHalf((low + high) / 2.0)
                if abs(next_mid - mid) < 0.02:
                    break
                mid = next_mid
            points = [low, mid, high]
            if axis == "x":
                return min(points, key=lambda v: evalCenter(v, fixed))
            return min(points, key=lambda v: evalCenter(fixed, v))

        best_cx = current_cx
        best_cy = current_cy
        if not lock_cx:
            best_cx = optimizeAxis(x_low, x_high, current_cy, "x")
        if not lock_cy:
            best_cy = optimizeAxis(y_low, y_high, best_cx, "y")

        best_err = evalCenter(best_cx, best_cy)
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
            Action.reanchorArmToCircleEdge(params, current_r)
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + current_r
            if bool(params.get("lock_stem_center_to_circle", False)):
                stem_w = float(params.get("stem_width", 1.0))
                params["stem_x"] = Action.snapHalf(max(0.0, min(float(w) - stem_w, best_cx - (stem_w / 2.0))))

        logs.append(
            f"circle: Mittelpunkt-Bracketing cx {current_cx:.3f}->{best_cx:.3f}, cy {current_cy:.3f}->{best_cy:.3f} (best_err={best_err:.3f})"
        )
        return True

    @staticmethod
    def optimizeCircleRadiusBracket(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
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
        low = float(Action.clipScalar(low, low_bound, high_bound))
        high = float(Action.clipScalar(high, low_bound, high_bound))
        mid = Action.snapHalf(float(Action.clipScalar(current, low, high)))
        mid = float(Action.clipScalar(mid, low, high))
        if high - low < 0.05:
            return False

        evaluations: dict[float, float] = {}

        def evalRadius(radius: float) -> float:
            clipped = float(Action.clipScalar(radius, low_bound, high_bound))
            snapped = float(round(clipped, 3))
            if snapped not in evaluations:
                try:
                    evaluations[snapped] = float(Action.elementErrorForCircleRadius(img_orig, params, snapped))
                except Exception:
                    evaluations[snapped] = float("inf")
            return evaluations[snapped]

        max_rounds = 12
        for _ in range(max_rounds):
            low_err = evalRadius(low)
            mid_err = evalRadius(mid)
            high_err = evalRadius(high)
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
            next_mid = Action.snapHalf((low + high) / 2.0)
            if abs(next_mid - mid) < 0.02:
                break
            mid = next_mid

        best_r, best_err, best_full_err = Action.selectCircleRadiusPlateauCandidate(img_orig, params, evaluations, current)
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
            Action.reanchorArmToCircleEdge(params, best_r)
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
    def optimizeCirclePoseMultistart(img_orig: np.ndarray, params: dict, logs: list[str]) -> bool:
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
        _x_low, _x_high, _y_low, _y_high, min_r, max_r = Action.circleBounds(params, w, h)

        fine_shift = min(1.0, shift)
        fine_radius = min(0.5, radius_span)

        if lock_cx:
            cx_candidates = [float(current_cx)]
        else:
            cx_candidates = [
                float(Action.clipScalar(current_cx + offset, 0.0, float(w - 1)))
                for offset in (-shift, -fine_shift, 0.0, fine_shift, shift)
            ]
        if lock_cy:
            cy_candidates = [float(current_cy)]
        else:
            cy_candidates = [
                float(Action.clipScalar(current_cy + offset, 0.0, float(h - 1)))
                for offset in (-shift, -fine_shift, 0.0, fine_shift, shift)
            ]

        r_candidates = [
            float(Action.clipScalar(current_r + offset, min_r, max_r))
            for offset in (-radius_span, -fine_radius, 0.0, fine_radius, radius_span)
        ]

        evaluations: dict[tuple[float, float, float], float] = {}

        def evalPose(cx: float, cy: float, rad: float) -> float:
            key = (cx, cy, rad)
            if key not in evaluations:
                evaluations[key] = float(
                    Action.elementErrorForCirclePose(
                        img_orig,
                        params,
                        cx_value=cx,
                        cy_value=cy,
                        radius_value=rad,
                    )
                )
            return evaluations[key]

        best = (float(current_cx), float(current_cy), float(current_r))
        best_err = evalPose(*best)

        for cx in cx_candidates:
            for cy in cy_candidates:
                for rad in r_candidates:
                    err = evalPose(cx, cy, rad)
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
            Action.reanchorArmToCircleEdge(params, best_r)
        if params.get("stem_enabled"):
            params["stem_top"] = float(params.get("cy", 0.0)) + best_r
            if bool(params.get("lock_stem_center_to_circle", False)):
                stem_w = float(params.get("stem_width", 1.0))
                params["stem_x"] = Action.snapHalf(max(0.0, min(float(w) - stem_w, best_cx - (stem_w / 2.0))))

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
            improved = Action.optimizeCirclePoseAdaptiveDomain(img_orig, params, logs)
            if not improved:
                logs.append("circle: Adaptive-Domain-Suche ohne Gewinn; fallback auf stochastic survivor")
                Action.optimizeCirclePoseStochasticSurvivor(img_orig, params, logs)
        return True

    @staticmethod
    def elementErrorForExtent(img_orig: np.ndarray, params: dict, element: str, extent_value: float) -> float:
        h, w = img_orig.shape[:2]
        probe = dict(params)

        if element == "stem" and probe.get("stem_enabled"):
            min_len = 1.0
            max_len = float(h)
            new_len = float(Action.clipScalar(extent_value, min_len, max_len))
            center = (float(probe.get("stem_top", 0.0)) + float(probe.get("stem_bottom", 0.0))) / 2.0
            half = new_len / 2.0
            probe["stem_top"] = float(Action.clipScalar(center - half, 0.0, float(h - 1)))
            probe["stem_bottom"] = float(Action.clipScalar(center + half, probe["stem_top"] + 1.0, float(h)))

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
            new_len = float(Action.clipScalar(extent_value, 1.0, float(max(w, h))))
            ux = dx / cur_len
            uy = dy / cur_len

            if probe.get("circle_enabled", True) and all(k in probe for k in ("cx", "cy", "r")):
                # Keep the endpoint at the circle edge fixed and optimize the free side
                # length only. Symmetric center-scaling shortens both ends and can make
                # AC0812/AC0814 horizontal connectors visibly too short.
                Action.reanchorArmToCircleEdge(probe, float(probe.get("r", 0.0)))
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
                    probe["arm_x2"] = float(Action.clipScalar(ix + (ux * new_len), 0.0, float(w - 1)))
                    probe["arm_y2"] = float(Action.clipScalar(iy + (uy * new_len), 0.0, float(h - 1)))
                else:
                    ix, iy = ax2, ay2
                    probe["arm_x1"] = float(Action.clipScalar(ix - (ux * new_len), 0.0, float(w - 1)))
                    probe["arm_y1"] = float(Action.clipScalar(iy - (uy * new_len), 0.0, float(h - 1)))
            else:
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                half = new_len / 2.0
                probe["arm_x1"] = float(Action.clipScalar(cx - (ux * half), 0.0, float(w - 1)))
                probe["arm_y1"] = float(Action.clipScalar(cy - (uy * half), 0.0, float(h - 1)))
                probe["arm_x2"] = float(Action.clipScalar(cx + (ux * half), 0.0, float(w - 1)))
                probe["arm_y2"] = float(Action.clipScalar(cy + (uy * half), 0.0, float(h - 1)))
        else:
            return float("inf")

        elem_svg = Action.generateBadgeSvg(w, h, Action.elementOnlyParams(probe, element))
        elem_render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        mask_orig = Action.extractBadgeElementMask(img_orig, probe, element)
        if mask_orig is None:
            return float("inf")

        return Action.elementMatchError(img_orig, elem_render, probe, element, mask_orig=mask_orig)

    @staticmethod
    def optimizeElementExtentBracket(img_orig: np.ndarray, params: dict, element: str, logs: list[str]) -> bool:
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
                Action.snapHalf(low),
                Action.snapHalf(low + (high - low) * 0.25),
                Action.snapHalf((low + high) / 2.0),
                Action.snapHalf(low + (high - low) * 0.75),
                Action.snapHalf(high),
                Action.snapHalf(Action.clipScalar(current, low, high)),
            }
        )
        candidate_errors = [Action.elementErrorForExtent(img_orig, params, element, v) for v in candidates]
        if not all(math.isfinite(e) for e in candidate_errors):
            logs.append(
                f"{element}: Längen-Bracketing abgebrochen ({key_label}) wegen nicht-finiten Fehlern "
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
            )
            return False

        best_idx = Action.argminIndex(candidate_errors)
        best_len = float(candidates[best_idx])

        boundary_best = abs(best_len - low) < 0.02 or abs(best_len - high) < 0.02
        if boundary_best:
            s_best, s_err, s_improved = Action.stochasticSurvivorScalar(
                current,
                low,
                high,
                lambda v: Action.elementErrorForExtent(img_orig, params, element, float(v)),
                snap=Action.snapHalf,
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
                    top = float(Action.clipScalar(bottom - best_len, 0.0, bottom - 1.0))
                    params["stem_top"] = top
                    params["stem_bottom"] = bottom
                else:
                    # Keep the stem attached to the circle edge and optimize only the free end.
                    top = float(Action.clipScalar(float(params.get("cy", 0.0)) + float(params.get("r", 0.0)), 0.0, float(h - 1)))
                    params["stem_top"] = top
                    params["stem_bottom"] = float(Action.clipScalar(top + best_len, top + 1.0, float(h)))
            else:
                center = (float(params.get("stem_top", 0.0)) + float(params.get("stem_bottom", 0.0))) / 2.0
                half = best_len / 2.0
                params["stem_top"] = float(Action.clipScalar(center - half, 0.0, float(h - 1)))
                params["stem_bottom"] = float(Action.clipScalar(center + half, params["stem_top"] + 1.0, float(h)))
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
                Action.reanchorArmToCircleEdge(params, float(params.get("r", 0.0)))
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
                    params["arm_x2"] = float(Action.clipScalar(ix + (ux * best_len), 0.0, float(w - 1)))
                    params["arm_y2"] = float(Action.clipScalar(iy + (uy * best_len), 0.0, float(h - 1)))
                    params["arm_x1"] = float(ix)
                    params["arm_y1"] = float(iy)
                else:
                    ix, iy = ax2, ay2
                    if abs(uy) <= 0.35:
                        iy = cy
                        ix = cx - float(params.get("r", 0.0)) if ix <= cx else cx + float(params.get("r", 0.0))
                    params["arm_x1"] = float(Action.clipScalar(ix - (ux * best_len), 0.0, float(w - 1)))
                    params["arm_y1"] = float(Action.clipScalar(iy - (uy * best_len), 0.0, float(h - 1)))
                    params["arm_x2"] = float(ix)
                    params["arm_y2"] = float(iy)
            else:
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                half = best_len / 2.0
                params["arm_x1"] = float(Action.clipScalar(cx - (ux * half), 0.0, float(w - 1)))
                params["arm_y1"] = float(Action.clipScalar(cy - (uy * half), 0.0, float(h - 1)))
                params["arm_x2"] = float(Action.clipScalar(cx + (ux * half), 0.0, float(w - 1)))
                params["arm_y2"] = float(Action.clipScalar(cy + (uy * half), 0.0, float(h - 1)))

        logs.append(
            f"{element}: Längen-Bracketing {key_label} {current:.3f}->{best_len:.3f}; Kandidaten="
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return True

    @staticmethod
    def optimizeElementWidthBracket(img_orig: np.ndarray, params: dict, element: str, logs: list[str]) -> bool:
        h, w = img_orig.shape[:2]
        info = Action.elementWidthKeyAndBounds(element, params, w, h, img_orig=img_orig)
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
                    Action.snapHalf(low),
                    Action.snapHalf(low + (high - low) * 0.25),
                    Action.snapHalf((low + high) / 2.0),
                    Action.snapHalf(low + (high - low) * 0.75),
                    Action.snapHalf(high),
                    Action.snapHalf(Action.clipScalar(current, low, high)),
                }
            )
        candidate_errors = [Action.elementErrorForWidth(img_orig, params, element, v) for v in candidates]
        if not all(math.isfinite(e) for e in candidate_errors):
            logs.append(
                f"{element}: Breiten-Bracketing abgebrochen ({key}) wegen nicht-finiten Fehlern "
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
            )
            return False

        best_idx = Action.argminIndex(candidate_errors)
        best_width = candidates[best_idx]

        boundary_best = abs(float(best_width) - low) < 0.02 or abs(float(best_width) - high) < 0.02
        if boundary_best:
            snap_fn = (lambda v: float(round(v, 3))) if key.endswith("_font_scale") else Action.snapHalf
            s_best, s_err, s_improved = Action.stochasticSurvivorScalar(
                current,
                low,
                high,
                lambda v: Action.elementErrorForWidth(img_orig, params, element, float(v)),
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
            best_width = Action.snapIntPx(best_width, minimum=1.0)
        elif key.endswith("_font_scale"):
            best_width = float(round(best_width, 3))
        else:
            best_width = Action.snapHalf(best_width)

        params[key] = best_width
        if key == "stem_width" and params.get("stem_enabled"):
            params["stem_x"] = Action.snapHalf(float(params.get("cx", params.get("stem_x", 0.0))) - (params["stem_width"] / 2.0))
        logs.append(
            f"{element}: Breiten-Bracketing {key} {old:.3f}->{best_width:.3f}; "
            f"Kandidaten="
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return True


    @staticmethod
    def elementColorKeys(element: str, params: dict) -> list[str]:
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
    def elementErrorForColor(
        img_orig: np.ndarray,
        params: dict,
        element: str,
        color_key: str,
        color_value: int,
        mask_orig: np.ndarray,
    ) -> float:
        probe = dict(params)
        probe[color_key] = int(Action.clipScalar(color_value, 0, 255))

        h, w = img_orig.shape[:2]
        elem_svg = Action.generateBadgeSvg(w, h, Action.elementOnlyParams(probe, element))
        elem_render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        if element == "circle":
            # Color-only circle probing should be photometric against a stable
            # source region. Do not let threshold-induced mask area changes in
            # candidate renders bias toward darker/larger-looking circles.
            return Action.maskedUnionErrorInBbox(img_orig, elem_render, mask_orig, mask_orig)

        return Action.elementMatchError(
            img_orig,
            elem_render,
            probe,
            element,
            mask_orig=mask_orig,
        )

    @staticmethod
    def optimizeElementColorBracket(
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
        local_gray = Action.meanGrayForMask(img_orig, mask_orig)
        sampled = int(round(local_gray)) if local_gray is not None else None

        for color_key in Action.elementColorKeys(element, params):
            current = int(round(float(params.get(color_key, 128))))
            low_limit = int(Action.clipScalar(int(params.get(f"{color_key}_min", 0)), 0, 255))
            high_limit = int(Action.clipScalar(int(params.get(f"{color_key}_max", 255)), 0, 255))
            if low_limit > high_limit:
                low_limit, high_limit = high_limit, low_limit
            candidates = {
                int(Action.clipScalar(current - 32, low_limit, high_limit)),
                int(Action.clipScalar(current - 16, low_limit, high_limit)),
                int(Action.clipScalar(current - 8, low_limit, high_limit)),
                int(Action.clipScalar(current, low_limit, high_limit)),
                int(Action.clipScalar(current + 8, low_limit, high_limit)),
                int(Action.clipScalar(current + 16, low_limit, high_limit)),
                int(Action.clipScalar(current + 32, low_limit, high_limit)),
            }
            if sampled is not None:
                candidates.add(int(Action.clipScalar(sampled, low_limit, high_limit)))
            if element == "circle" and color_key == "fill_gray":
                candidates.update(int(Action.clipScalar(v, low_limit, high_limit)) for v in {200, 210, 220, 230, 240})
            if color_key in {"stroke_gray", "stem_gray", "text_gray"}:
                candidates.update(int(Action.clipScalar(v, low_limit, high_limit)) for v in {96, 112, 128, 144, 152, 160, 171})

            values = sorted(v for v in candidates if low_limit <= v <= high_limit)
            errs = [
                Action.elementErrorForColor(img_orig, params, element, color_key, v, mask_orig)
                for v in values
            ]
            if not all(math.isfinite(e) for e in errs):
                logs.append(
                    f"{element}: Farb-Bracketing abgebrochen ({color_key}) wegen nicht-finiten Fehlern "
                    + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
                )
                continue

            best_idx = Action.argminIndex(errs)
            best_value = int(values[best_idx])

            if best_value == min(values) or best_value == max(values):
                s_best, s_err, s_improved = Action.stochasticSurvivorScalar(
                    float(current),
                    float(min(values)),
                    float(max(values)),
                    lambda v: Action.elementErrorForColor(
                        img_orig,
                        params,
                        element,
                        color_key,
                        int(Action.clipScalar(int(round(v)), low_limit, high_limit)),
                        mask_orig,
                    ),
                    snap=lambda v: int(Action.clipScalar(int(round(v)), low_limit, high_limit)),
                    seed=1301,
                )
                if s_improved:
                    best_value = int(Action.clipScalar(int(round(s_best)), low_limit, high_limit))
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
    def refineStemGeometryFromMasks(params: dict, mask_orig: np.ndarray, mask_svg: np.ndarray, w: int) -> tuple[bool, str | None]:
        """Refine stem width/position when validation detects a geometric mismatch."""
        orig_bbox = Action.maskBbox(mask_orig)
        svg_bbox = Action.maskBbox(mask_svg)
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
        est = Action.estimateVerticalStemFromMask(mask_orig, expected_cx, int(y_start), int(y_end))

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
                target_cx = float(Action.clipScalar(est_cx, circle_cx - max_offset, circle_cx + max_offset))
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
        target_width = Action.snapIntPx(target_width, minimum=1.0)
        old_x = float(params.get("stem_x", 0.0))
        old_w = float(params.get("stem_width", 1.0))
        new_x = Action.snapHalf(max(0.0, min(float(w) - target_width, target_cx - (target_width / 2.0))))
        if abs(target_width - old_w) < 0.05 and abs(new_x - old_x) < 0.05:
            return False, None
        params["stem_width"] = target_width
        params["stem_x"] = new_x
        return True, (
            f"stem: Breitenkorrektur mode={estimate_mode}, ratio={ratio:.3f}, "
            f"alt={old_width:.3f}, neu={target_width:.3f}"
        )

    @staticmethod
    def expectedSemanticPresence(semantic_elements: list[str]) -> dict[str, bool]:
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
    def semanticPresenceMismatches(expected: dict[str, bool], observed: dict[str, bool]) -> list[str]:
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
    def detectSemanticPrimitives(
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
        fg_mask = Action.foregroundMask(img_orig).astype(np.uint8)
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
            fallback_circle = Action.circleFromForegroundMask(fg_mask > 0)
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
                exp_r = float(Action.clipScalar(exp_r, 2.0, float(min_side) * 0.60))
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
    def validateSemanticDescriptionAlignment(
        img_orig: np.ndarray,
        semantic_elements: list[str],
        badge_params: dict,
    ) -> list[str]:
        expected = Action.expectedSemanticPresence(semantic_elements)
        expected_co2 = any("co_2" in str(elem).lower() or "co₂" in str(elem).lower() for elem in semantic_elements)
        try:
            structural = Action.detectSemanticPrimitives(img_orig, badge_params)
        except TypeError:
            # Test doubles may still patch the legacy one-argument variant.
            structural = Action.detectSemanticPrimitives(img_orig)
        circle_mask = Action.extractBadgeElementMask(img_orig, badge_params, "circle")
        stem_mask = Action.extractBadgeElementMask(img_orig, badge_params, "stem")
        arm_mask = Action.extractBadgeElementMask(img_orig, badge_params, "arm")
        text_mask = Action.extractBadgeElementMask(img_orig, badge_params, "text")

        def maskSupportsElement(mask: np.ndarray | None, element: str) -> bool:
            if mask is None:
                return False
            pixel_count = int(np.count_nonzero(mask))
            if pixel_count < 3:
                return False
            bbox = Action.maskBbox(mask)
            if bbox is None:
                return False
            x1, y1, x2, y2 = bbox
            width = max(1.0, (x2 - x1) + 1.0)
            height = max(1.0, (y2 - y1) + 1.0)
            area = width * height
            density = float(pixel_count) / max(1.0, area)
            small_variant = bool(badge_params.get("ac08_small_variant_mode", False))
            if element == "circle":
                if Action.maskSupportsCircle(mask):
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
            "circle": maskSupportsElement(circle_mask, "circle"),
            "stem": bool(
                maskSupportsElement(stem_mask, "stem")
                or (
                    vertical_connector_family
                    and bool(badge_params.get("arm_enabled", False))
                    and maskSupportsElement(arm_mask, "stem")
                )
            ),
            "arm": bool(
                not vertical_connector_family
                and maskSupportsElement(arm_mask, "arm")
            ),
            "text": maskSupportsElement(text_mask, "text"),
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
        issues = Action.semanticPresenceMismatches(expected, observed)
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
                    roi = Action.foregroundMask(img_orig)[y1 : y2 + 1, x1 : x2 + 1].astype(np.uint8)
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

        def stagnationFingerprint(current_params: dict) -> tuple[tuple[str, float], ...]:
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
            full_svg = Action.generateBadgeSvg(w, h, params)
            full_render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(full_svg, w, h))
            if full_render is None:
                logs.append("Abbruch: SVG konnte nicht gerendert werden")
                break

            if debug_out_dir:
                full_diff = Action.createDiffImage(img_orig, full_render)
                cv2.imwrite(os.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_full_diff.png"), full_diff)

            round_changed = False
            for element in elements:
                elem_svg = Action.generateBadgeSvg(w, h, Action.elementOnlyParams(params, element))
                elem_render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(elem_svg, w, h))
                if elem_render is None:
                    logs.append(f"{element}: Element-SVG konnte nicht gerendert werden")
                    continue

                mask_orig = Action.extractBadgeElementMask(img_orig, params, element)
                mask_svg = Action.extractBadgeElementMask(elem_render, params, element)
                if mask_orig is None or mask_svg is None:
                    logs.append(f"{element}: Element konnte nicht extrahiert werden")
                    continue

                if debug_out_dir:
                    elem_focus_mask = Action.elementRegionMask(h, w, params, element)
                    elem_diff = Action.createDiffImage(img_orig, elem_render, elem_focus_mask)
                    cv2.imwrite(
                        os.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_{element}_diff.png"),
                        elem_diff,
                    )

                elem_err = Action.elementMatchError(img_orig, elem_render, params, element, mask_orig=mask_orig, mask_svg=mask_svg)
                logs.append(f"{element}: Fehler={elem_err:.3f}")

                if element == "stem" and params.get("stem_enabled"):
                    changed, refine_log = Action.refineStemGeometryFromMasks(params, mask_orig, mask_svg, w)
                    if refine_log:
                        logs.append(refine_log)
                    if changed:
                        round_changed = True
                        logs.append("stem: Geometrie nach Elementabgleich aktualisiert")

                width_changed = Action.optimizeElementWidthBracket(img_orig, params, element, logs)
                if width_changed:
                    round_changed = True

                extent_changed = Action.optimizeElementExtentBracket(img_orig, params, element, logs)
                if extent_changed:
                    round_changed = True

                circle_geometry_penalty_active = apply_circle_geometry_penalty and not fallback_search_active
                if element == "circle" and circle_geometry_penalty_active:
                    center_changed = Action.optimizeCircleCenterBracket(img_orig, params, logs)
                    if center_changed:
                        round_changed = True
                    radius_changed = Action.optimizeCircleRadiusBracket(img_orig, params, logs)
                    if radius_changed:
                        round_changed = True

                # Color fitting is intentionally deferred to the end so
                # geometry convergence is not biased by temporary palette noise.

            global_search_changed = Action.optimizeGlobalParameterVectorSampling(
                img_orig,
                params,
                logs,
            )
            if global_search_changed:
                round_changed = True

            full_svg = Action.generateBadgeSvg(w, h, params)
            full_render = Action.fitToOriginalSize(img_orig, Action.renderSvgToNumpy(full_svg, w, h))
            full_err = Action.calculateError(img_orig, full_render)
            logs.append(f"Runde {round_idx + 1}: Gesamtfehler={full_err:.3f}")
            if math.isfinite(full_err) and full_err < best_full_err:
                best_full_err = full_err
                best_params = copy.deepcopy(params)

            current_round_state = (stagnationFingerprint(params), round(float(full_err), 6))
            if previous_round_state is not None:
                same_fingerprint = current_round_state[0] == previous_round_state[0]
                nearly_same_error = abs(current_round_state[1] - previous_round_state[1]) <= 1e-6
                if same_fingerprint and nearly_same_error:
                    logs.append(
                        "stagnation_detected: identischer Parameter-Fingerprint und praktisch unveränderter Gesamtfehler"
                    )
                    adaptive_unlock_applied = Action.activateAc08AdaptiveLocks(
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
                        Action.releaseAc08AdaptiveLocks(
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
                Action.releaseAc08AdaptiveLocks(
                    params,
                    logs,
                    reason="high_residual_error",
                    current_error=full_err,
                )

            if round_idx + 1 >= max_rounds:
                break

            if not round_changed:
                adaptive_unlock_applied = Action.activateAc08AdaptiveLocks(
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
                    Action.releaseAc08AdaptiveLocks(
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
            mask_orig = Action.extractBadgeElementMask(img_orig, params, element)
            if mask_orig is None:
                continue
            color_changed = Action.optimizeElementColorBracket(img_orig, params, element, mask_orig, logs)
            if color_changed:
                logs.append(f"{element}: Farboptimierung in Abschlussphase angewendet")

        params.update(Action.applyCanonicalBadgeColors(params))

        return logs


























































































































def harmonizationAnchorPriority(suffix: str, prefer_large: bool) -> int:
    """Return size-priority rank for L/M/S harmonization anchors."""
    if prefer_large:
        # For connector families we keep L authoritative to avoid undersized
        # large variants caused by propagating medium geometry upwards.
        return {"L": 0, "M": 1, "S": 2}.get(str(suffix), 3)
    # Plain circles remain more stable when M is used as anchor.
    return {"M": 0, "L": 1, "S": 2}.get(str(suffix), 3)























































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
















_MAINFILES_DIR = Path(__file__).resolve().parent








analyzeRange = loadMainfileFunction("analyze_range", "analyze_range.py")
loadDescriptionMapping = loadMainfileFunction("_load_description_mapping", "_load_description_mapping.py")
runSvgRenderSubprocessEntrypoint = loadMainfileFunction(
    "_run_svg_render_subprocess_entrypoint", "_run_svg_render_subprocess_entrypoint.py"
)
bootstrapRequiredImageDependencies = loadMainfileFunction(
    "_bootstrap_required_image_dependencies", "_bootstrap_required_image_dependencies.py"
)
buildLinuxVendorInstallCommand = loadMainfileFunction(
    "build_linux_vendor_install_command", "build_linux_vendor_install_command.py"
)
convertRange = loadMainfileFunction("convert_range", "convert_range.py")
exportModuleCallTreeCsv = loadMainfileFunction("export_module_call_tree_csv", "export_module_call_tree_csv.py")
parseArgs = loadMainfileFunction("parse_args", "parse_args.py")
optionalLogCapture = contextlib.contextmanager(
    loadMainfileFunction("_optional_log_capture", "_optional_log_capture.py")
)
resolveCliCsvAndOutput = loadMainfileFunction("_resolve_cli_csv_and_output", "_resolve_cli_csv_and_output.py")
formatUserDiagnostic = loadMainfileFunction("_format_user_diagnostic", "_format_user_diagnostic.py")
promptInteractiveRange = loadMainfileFunction("_prompt_interactive_range", "_prompt_interactive_range.py")
convertImage = loadMainfileFunction("convert_image", "convert_image.py")
convertImageVariants = loadMainfileFunction("convert_image_variants", "convert_image_variants.py")
