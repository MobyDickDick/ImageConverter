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
