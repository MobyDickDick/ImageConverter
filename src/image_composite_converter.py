"""Image-to-composite-SVG conversion pipeline.

Ported from the user-provided prototype and exposed as a Python helper module
for direct CLI and module-based execution.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import csv
from dataclasses import dataclass
import importlib
import json
import math
import os
import random
import re
import statistics
import struct
import subprocess
import sys
import tempfile
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

if __package__ in {None, ""}:
    # Allow direct CLI execution via ``python src/image_composite_converter.py``
    # from the repository root without requiring PYTHONPATH to be preset.
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from src.overview_tiles import generate_conversion_overviews
from src.image_composite_converter_regions import (
    ANNOTATION_COLORS,
    analyze_range_impl,
    annotate_image_regions_impl,
    detect_relevant_regions_impl,
)
from src.successful_conversions import (
    AC08_MITIGATION_STATUS,
    AC08_PREVIOUSLY_GOOD_VARIANTS,
    AC08_REGRESSION_CASES,
    AC08_REGRESSION_SET_NAME,
    AC08_REGRESSION_VARIANTS,
    SUCCESSFUL_CONVERSIONS,
    SUCCESSFUL_CONVERSIONS_MANIFEST,
    _load_successful_conversions,
)

# Keep regression variant list deterministic and duplicate-free for batch
# selection/tests even when upstream manifests accidentally repeat entries.
AC08_REGRESSION_VARIANTS = tuple(dict.fromkeys(AC08_REGRESSION_VARIANTS))
# Keep the historical "previously good" anchor subset stable for AC08 success
# criteria reports used by this converter/test suite.
AC08_PREVIOUSLY_GOOD_VARIANTS = ("AC0800_L", "AC0800_M", "AC0800_S", "AC0811_L")


@dataclass(frozen=True)
class SourceSpan:
    path: str
    line: int | None = None
    column: int | None = None

    def format(self) -> str:
        location = str(self.path)
        if self.line is not None:
            location = f"{location}:{self.line}"
            if self.column is not None:
                location = f"{location}:{self.column}"
        return location


class DescriptionMappingError(ValueError):
    def __init__(self, message: str, *, span: SourceSpan | None = None) -> None:
        super().__init__(message)
        self.message = str(message)
        self.span = span



DEFAULT_CALL_TREE_CSV_PATH = "artifacts/converted_images/reports/call_tree_image_composite_converter.csv"

OPTIONAL_DEPENDENCY_ERRORS: dict[str, str] = {}

def _optional_dependency_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def _vendored_site_packages_dirs() -> list[Path]:
    base_dir = _optional_dependency_base_dir()
    candidates: list[Path] = []

    linux_vendor = base_dir / "vendor" / "linux-py310" / "site-packages"
    if linux_vendor.exists():
        candidates.append(linux_vendor)

    vendor_root = base_dir / "vendor"
    if vendor_root.exists():
        for site_packages_dir in sorted(vendor_root.glob("*/site-packages")):
            if site_packages_dir.exists() and site_packages_dir not in candidates:
                candidates.append(site_packages_dir)

    venv_site_packages = base_dir / ".venv" / "Lib" / "site-packages"
    if venv_site_packages.exists():
        candidates.append(venv_site_packages)

    return candidates


def _describe_optional_dependency_error(module_name: str, error: BaseException, searched_dirs: list[Path]) -> str:
    message = str(error) or error.__class__.__name__
    if "add_dll_directory" in message and any("Lib/site-packages" in str(path) for path in searched_dirs):
        return (
            f"{module_name} konnte nicht geladen werden: offenbar wurde ein Windows-Wheel auf Linux gefunden "
            f"(add_dll_directory-Fehler)."
        )
    return f"{module_name} konnte nicht geladen werden: {message}"


def _load_optional_module(module_name: str):
    search_dirs = _vendored_site_packages_dirs()
    last_error: BaseException | None = None

    with contextlib.suppress(KeyError):
        del OPTIONAL_DEPENDENCY_ERRORS[module_name]

    for site_packages_dir in search_dirs:
        with contextlib.suppress(ValueError):
            sys.path.remove(str(site_packages_dir))
        sys.path.insert(0, str(site_packages_dir))
        try:
            module = importlib.import_module(module_name)
            return module
        except Exception as exc:  # pragma: no cover - diagnosis path
            last_error = exc
            for key in tuple(sys.modules.keys()):
                if key == module_name or key.startswith(f"{module_name}."):
                    sys.modules.pop(key, None)

    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        last_error = exc

    if last_error is not None:
        OPTIONAL_DEPENDENCY_ERRORS[module_name] = _describe_optional_dependency_error(module_name, last_error, search_dirs)
    return None


np = _load_optional_module("numpy")  # type: ignore
cv2 = _load_optional_module("cv2")  # type: ignore
fitz = _load_optional_module("fitz")  # type: ignore

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


_MAINFILES_DIR = Path(__file__).resolve().parent / "mainFiles"


def _load_mainfile_function(func_name: str, filename: str):
    """Lade eine ausgelagerte Funktionsdefinition aus src/mainFiles in dieses Modul."""
    source_path = _MAINFILES_DIR / filename
    namespace: dict[str, object] = {}
    code = compile(source_path.read_text(encoding="utf-8"), str(source_path), "exec")
    exec(code, globals(), namespace)
    loaded = namespace.get(func_name)
    if not callable(loaded):
        raise RuntimeError(f"Funktion {func_name!r} konnte aus {source_path} nicht geladen werden")
    globals()[func_name] = loaded
    return loaded


def _load_mainfile_tree() -> None:
    """Load split helper modules into this module namespace.

    The converter was split into many files under ``src/mainFiles`` where
    functions reference each other through module-level globals. Importing only
    top-level entry points is therefore not sufficient; runtime would otherwise
    fail with ``NameError`` for helper symbols.
    """

    for source_path in sorted(_MAINFILES_DIR.rglob("*.py")):
        code = compile(source_path.read_text(encoding="utf-8"), str(source_path), "exec")
        exec(code, globals(), globals())


def _bind_action_facade() -> type:
    """Provide backward-compatible ``Action`` access for split functions."""

    class Action:
        STOCHASTIC_RUN_SEED = 0
        STOCHASTIC_SEED_OFFSET = 0
        T_PATH_D = 'd="M{sx:.2f},{sy:.2f} L{ex:.2f},{ey:.2f}"'
        LIGHT_CIRCLE_FILL_GRAY = 216
        LIGHT_CIRCLE_STROKE_GRAY = 140
        LIGHT_CIRCLE_TEXT_GRAY = 128

        @staticmethod
        def make_badge_params(*_args, **_kwargs):
            return {}

        @staticmethod
        def validate_semantic_description_alignment(*_args, **_kwargs):
            return []

        @staticmethod
        def validate_badge_by_elements(*_args, **_kwargs):
            return []

        @staticmethod
        def _enforce_semantic_connector_expectation(*_args, **_kwargs):
            return {}

        @staticmethod
        def apply_redraw_variation(params, *_args, **_kwargs):
            return dict(params or {}), []

        @staticmethod
        def _default_ac0811_params(width, height):
            return {"mode": "semantic_badge", "width": float(width), "height": float(height)}

        @staticmethod
        def generate_badge_svg(width, height, _params):
            return f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}"/>'

        @staticmethod
        def render_svg_to_numpy(*_args, **_kwargs):
            return None

        @staticmethod
        def calculate_error(*_args, **_kwargs):
            return float("inf")

        @staticmethod
        def calculate_delta2_stats(*_args, **_kwargs):
            return float("inf"), float("inf")

        @staticmethod
        def create_diff_image(image, *_args, **_kwargs):
            return image

    for name, value in list(globals().items()):
        if callable(value) and (name.startswith("_") or name in {"generate_badge_svg", "calculate_error", "render_svg_to_numpy", "calculate_delta2_stats", "create_diff_image"}):
            setattr(Action, name, staticmethod(value))
    globals()["Action"] = Action
    return Action


def _bind_reflection_facade() -> type:
    """Provide backward-compatible ``Reflection`` placeholder access."""

    class Reflection:
        @staticmethod
        def parse_description(*_args, **_kwargs):
            return "", {}

    globals()["Reflection"] = Reflection
    return Reflection


_load_mainfile_tree()
_bind_action_facade()
_bind_reflection_facade()


def get_base_name_from_file(filename: str) -> str:
    name = os.path.splitext(str(filename or ""))[0]
    name = re.sub(r"(-\d+)$", "", name)
    while True:
        prev = name
        name = re.sub(r"_([1-9]|L|M|S|[1-9]S|W|X)$", "", name, flags=re.IGNORECASE)
        if name == prev:
            break
    return name


def _clip(value: float, low: float, high: float) -> float:
    return float(max(low, min(high, value)))


def _semantic_quality_flags(variant: str, element_lines: list[str] | tuple[str, ...] | None) -> list[str]:
    """Derive quality flags from element-level diagnostics.

    AC0811 variants are allowed to stay ``semantic_ok`` even with a slightly
    elevated single-element error. To keep reports machine-readable we emit
    explicit quality flags.
    """

    variant_norm = str(variant or "").strip().upper()
    if not variant_norm.startswith("AC0811"):
        return []

    if not element_lines:
        return []

    elevated: list[tuple[str, float]] = []
    for raw_line in element_lines:
        line = str(raw_line or "").strip()
        match = re.search(r"^\s*([^:]+)\s*:\s*Fehler\s*=\s*([0-9]+(?:\.[0-9]+)?)", line, flags=re.IGNORECASE)
        if not match:
            continue
        label = match.group(1).strip().lower()
        value = float(match.group(2))
        if value >= 10.0:
            elevated.append((label, value))

    if not elevated:
        return []

    elevated.sort(key=lambda item: item[1], reverse=True)
    lead_label, lead_value = elevated[0]
    labels = ",".join(label for label, _ in elevated)
    return [
        "quality=borderline",
        f"quality_reason=semantic_ok_trotz_hohem_elementfehler:{lead_label}={lead_value:.3f}",
        f"quality_elevated_elements={labels}",
    ]


_resolve_description_xml_path = _load_mainfile_function(
    "_resolve_description_xml_path",
    "_load_description_mappingFiles/_load_description_mapping_from_xmlFiles/_resolve_description_xml_path.py",
)
_load_description_mapping_from_csv = _load_mainfile_function(
    "_load_description_mapping_from_csv",
    "_load_description_mappingFiles/_load_description_mapping_from_csv.py",
)
_load_description_mapping_from_xml = _load_mainfile_function(
    "_load_description_mapping_from_xml",
    "_load_description_mappingFiles/_load_description_mapping_from_xml.py",
)
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if bool(getattr(args, "_render_svg_subprocess", False)):
        return _run_svg_render_subprocess_entrypoint()
    global SVG_RENDER_SUBPROCESS_ENABLED, SVG_RENDER_SUBPROCESS_TIMEOUT_SEC
    if bool(args.isolate_svg_render):
        SVG_RENDER_SUBPROCESS_ENABLED = True
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = max(1.0, float(args.isolate_svg_render_timeout_sec))
    log_path = str(args.log_file or "").strip()
    with _optional_log_capture(log_path):
        try:
            if args.ac08_regression_set:
                args.start = "AC0000"
                args.end = "ZZ9999"

            if args.print_linux_vendor_command:
                print(
                    " ".join(
                        build_linux_vendor_install_command(
                            vendor_dir=args.vendor_dir,
                            platform_tag=args.vendor_platform,
                            python_version=args.vendor_python_version,
                        )
                    )
                )
                return 0

            if args.export_call_tree_csv:
                path = export_module_call_tree_csv(output_csv_path=args.export_call_tree_csv)
                print(f"[INFO] Aufrufbaum-CSV geschrieben: {path}")
                return 0

            if args.interactive_range or args.start is None or args.end is None:
                args.start, args.end = _prompt_interactive_range(args)
            else:
                args.start = str(args.start or "").strip()
                args.end = str(args.end or "ZZZZZZ").strip() or args.start

            csv_path, output_dir = _resolve_cli_csv_and_output(args)

            if not csv_path:
                print("[WARN] Keine CSV/TSV/XML angegeben oder gefunden. Einige Symbole können ohne Beschreibung übersprungen werden.")
            elif not os.path.exists(csv_path):
                print(f"[WARN] CSV/TSV/XML-Datei nicht gefunden: {csv_path}")
            elif args.mode == "convert":
                # Validate user-supplied description data before the batch starts so
                # malformed files fail with a precise source location even when the
                # selected image range happens to be empty.
                _load_description_mapping(csv_path)

            if args.bootstrap_deps:
                try:
                    installed = _bootstrap_required_image_dependencies()
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
                out_dir = analyze_range(
                    args.folder_path,
                    output_root=output_dir,
                    start_ref=args.start,
                    end_ref=args.end,
                )
            else:
                out_dir = convert_range(
                    args.folder_path,
                    csv_path,
                    args.iterations,
                    args.start,
                    args.end,
                    args.debug_ac0811_dir,
                    args.debug_element_diff_dir,
                    output_dir,
                    selected_variants,
                )
            print(f"\nAbgeschlossen! Ausgaben unter: {out_dir}")
            return 0
        except DescriptionMappingError as exc:
            print(f"[ERROR] {_format_user_diagnostic(exc)}")
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
