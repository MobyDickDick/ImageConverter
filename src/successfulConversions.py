"""Manifest and regression metadata for successful conversion variants.

This module isolates data-heavy configuration from the main conversion script
so the core pipeline implementation can stay easier to navigate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SUCCESSFUL_CONVERSIONS_MANIFEST = Path("artifacts/converted_images/reports/successful_conversions.txt")
SUCCESSFUL_CONVERSIONS_SOURCE_DIR = Path("artifacts/images_to_convert")


AC08_REGRESSION_METADATA_PATH = Path("config/regression_metadata/ac08_regression_cases_v1.json")


def _loadAc08RegressionMetadata(
    metadata_path: Path = AC08_REGRESSION_METADATA_PATH,
) -> dict:
    """Load catalog-specific AC08 regression metadata from a non-runtime data file."""
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    if int(payload.get("schema_version", 0)) != 1:
        raise ValueError(f"Unsupported AC08 regression metadata schema: {payload.get('schema_version')!r}")
    return payload


AC08_REGRESSION_METADATA = _loadAc08RegressionMetadata()
AC08_STABLE_GOOD_REASON_OVERRIDES: dict[str, str] = dict(
    AC08_REGRESSION_METADATA.get("stable_good_reason_overrides", {})
)
AC08_PREVIOUSLY_GOOD_ANCHOR_COUNT = int(
    AC08_REGRESSION_METADATA.get("previously_good_anchor_count", 0) or 0
)
_AC08_BASE_REGRESSION_CASES: tuple[dict[str, str], ...] = tuple(
    dict(case) for case in AC08_REGRESSION_METADATA.get("base_regression_cases", ())
)
SUCCESSFUL_CONVERSIONS_FALLBACK: tuple[str, ...] = tuple(
    str(variant).strip().upper()
    for variant in AC08_REGRESSION_METADATA.get("successful_conversions_fallback", ())
    if str(variant).strip()
)


def _iterAvailableSuccessfulConversionVariants(
    source_dir: Path = SUCCESSFUL_CONVERSIONS_SOURCE_DIR,
) -> tuple[str, ...]:
    """Return known source-image variants that can back range expressions."""
    if not source_dir.exists() or not source_dir.is_dir():
        return ()
    variants = sorted(
        path.stem.upper()
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
    )
    return tuple(dict.fromkeys(variants))


def _expandSuccessfulConversionManifestEntry(
    entry: str,
    available_variants: tuple[str, ...],
) -> tuple[str, ...]:
    """Expand a manifest entry to one or more canonical variant IDs."""
    candidate = str(entry or "").strip().upper()
    if not candidate:
        return ()

    range_match = re.match(
        r"^(?P<start>[A-Z]{2,3}\d{4}_[A-Z])\s*(?:BIS|TO|\.\.|\.{3})\s*(?P<end>[A-Z]{2,3}\d{4}_[A-Z])$",
        candidate,
    )
    if not range_match:
        return (candidate,)

    start_variant = range_match.group("start")
    end_variant = range_match.group("end")
    if not available_variants:
        return (start_variant, end_variant) if start_variant != end_variant else (start_variant,)

    try:
        start_idx = available_variants.index(start_variant)
        end_idx = available_variants.index(end_variant)
    except ValueError:
        return (start_variant, end_variant) if start_variant != end_variant else (start_variant,)

    if start_idx <= end_idx:
        selected = available_variants[start_idx : end_idx + 1]
    else:
        selected = tuple(reversed(available_variants[end_idx : start_idx + 1]))
    return tuple(selected)


def _loadSuccessfulConversions(
    manifest_path: Path = SUCCESSFUL_CONVERSIONS_MANIFEST,
    source_dir: Path = SUCCESSFUL_CONVERSIONS_SOURCE_DIR,
) -> tuple[str, ...]:
    """Load the canonical successful-conversions manifest from disk."""
    if manifest_path.exists():
        variants: list[str] = []
        available_variants = _iterAvailableSuccessfulConversionVariants(source_dir)
        for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            entry = line.split(";", 1)[0].strip()
            if not entry:
                continue
            variants.extend(_expandSuccessfulConversionManifestEntry(entry, available_variants))
        normalized = tuple(dict.fromkeys(variants))
        if normalized:
            return normalized
    return SUCCESSFUL_CONVERSIONS_FALLBACK


SUCCESSFUL_CONVERSIONS = _loadSuccessfulConversions()
AC08_PREVIOUSLY_GOOD_VARIANTS = tuple(variant for variant in SUCCESSFUL_CONVERSIONS if variant.startswith("AC08"))


def _buildAc08RegressionCases() -> tuple[dict[str, str], ...]:
    stable_good_cases = [
        {
            "variant": variant,
            "focus": "stable_good",
            "reason": AC08_STABLE_GOOD_REASON_OVERRIDES.get(
                variant,
                f"Previously marked good AC08 variant {variant} that must stay semantic_ok after every future adjustment.",
            ),
        }
        for variant in AC08_PREVIOUSLY_GOOD_VARIANTS
    ]
    return tuple(stable_good_cases + list(_AC08_BASE_REGRESSION_CASES))


AC08_REGRESSION_CASES = _buildAc08RegressionCases()
AC08_REGRESSION_SET_NAME = f"ac08_core_{len(AC08_REGRESSION_CASES)}"
AC08_REGRESSION_VARIANTS = tuple(case["variant"] for case in AC08_REGRESSION_CASES)


AC08_MITIGATION_STATUS: dict[str, dict[str, str]] = {
    str(key): dict(value)
    for key, value in AC08_REGRESSION_METADATA.get("mitigation_status", {}).items()
}
