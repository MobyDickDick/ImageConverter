"""Image-to-composite-SVG conversion pipeline.

Ported from the user-provided prototype and exposed as a Python helper module
for direct CLI and module-based execution.
"""

from __future__ import annotations

import argparse
import ast
import base64
import copy
import contextlib
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
import io
import struct
import statistics
from src.mainFiles.overview_tiles import generate_conversion_overviews
from src.mainFiles.image_composite_converter_regions import (
    ANNOTATION_COLORS,
    analyze_range_impl,
    annotate_image_regions_impl,
    detect_relevant_regions_impl,
)
from src.mainFiles._clip_scalar import clip_scalar
from src.mainFiles.image_composite_converter_dependencies import (
    bootstrap_required_image_dependencies,
    missing_required_image_dependencies,
)
from src.mainFiles.description_mapping import (
    load_description_mapping,
    load_description_mapping_from_csv,
    load_description_mapping_from_xml,
    resolve_description_xml_path,
)
from src.image_composite_converter_semantic_presence import (
    expected_semantic_presence_impl,
    semantic_presence_mismatches_impl,
)
from src.mainFiles._optional_module_loader import (
    OPTIONAL_DEPENDENCY_ERRORS,
    _import_with_vendored_fallback,
    _load_optional_module,
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

_svg_render_isolation_env = os.environ.get("IMAGE_CONVERTER_ISOLATE_SVG_RENDER", "").strip().lower()
_svg_render_isolation_explicit = _svg_render_isolation_env in {"0", "false", "no", "off", "1", "true", "yes", "on"}
_running_under_pytest = any("pytest" in (arg or "").lower() for arg in sys.argv[:1]) or "PYTEST_CURRENT_TEST" in os.environ
_running_svg_worker = "--_render-svg-subprocess" in sys.argv
SVG_RENDER_SUBPROCESS_ENABLED = _svg_render_isolation_env in {"1", "true", "yes", "on"} or (
    not _svg_render_isolation_explicit and _running_under_pytest and not _running_svg_worker
)
try:
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = max(
        1.0,
        float(os.environ.get("IMAGE_CONVERTER_ISOLATE_SVG_RENDER_TIMEOUT_SEC", "20").strip() or "20"),
    )
except ValueError:
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = 20.0
