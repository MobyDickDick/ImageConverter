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
