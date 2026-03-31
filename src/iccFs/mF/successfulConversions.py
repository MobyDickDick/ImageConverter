"""Manifest and regression metadata for successful conversion variants.

This module isolates data-heavy configuration from the main conversion script
so the core pipeline implementation can stay easier to navigate.
"""

from __future__ import annotations

import re
from pathlib import Path

SUCCESSFUL_CONVERSIONS_MANIFEST = Path("artifacts/converted_images/reports/successful_conversions.txt")
SUCCESSFUL_CONVERSIONS_SOURCE_DIR = Path("artifacts/images_to_convert")
SUCCESSFUL_CONVERSIONS_FALLBACK: tuple[str, ...] = (
    "AC0800_L",
    "AC0800_M",
    "AC0800_S",
    "AC0811_L",
    "AC0811_M",
    "AC0811_S",
)


AC08_STABLE_GOOD_REASON_OVERRIDES: dict[str, str] = {
    "AC0800_L": "Previously marked good plain-ring large variant that must stay semantic_ok after every AC08 adjustment.",
    "AC0800_M": "Previously marked good plain-ring medium variant that must stay semantic_ok after every AC08 adjustment.",
    "AC0800_S": "Previously marked good plain-ring small variant that must stay semantic_ok after every AC08 adjustment.",
    "AC0811_L": "Known regression-safe good conversion anchor for circle-with-stem semantics; must remain semantic_ok.",
    "AC0811_M": "Known regression-safe good conversion anchor for circle-with-stem semantics; must remain semantic_ok.",
    "AC0811_S": "Known regression-safe good conversion anchor for circle-with-stem semantics; must remain semantic_ok.",
}


_AC08_BASE_REGRESSION_CASES: tuple[dict[str, str], ...] = (
    {"variant": "AC0882_S", "focus": "stagnation", "reason": "Small left-connector outlier that previously burned many near-identical validation rounds."},
    {"variant": "AC0837_L", "focus": "stagnation", "reason": "Large left-connector case used to verify adaptive search still moves on stubborn families."},
    {"variant": "AC0839_S", "focus": "small_variant", "reason": "Small right-connector badge that tends to drift in geometry and text placement."},
    {"variant": "AC0820_L", "focus": "circle_text", "reason": "Plain circle/text badge used as a connector-free baseline for quality passes."},
    {"variant": "AC0831_L", "focus": "semantic_vertical", "reason": "Vertical connector family representative for stem alignment and text balance."},
    {"variant": "AC0834_S", "focus": "small_variant", "reason": "Small mirrored connector badge included to catch asymmetric regressions on _S variants."},
    {"variant": "AC0835_S", "focus": "small_variant", "reason": "Small circle/text family member that stresses compact text scaling without connectors."},
    {"variant": "AC0812_M", "focus": "semantic_horizontal", "reason": "Medium left-connector case that complements AC0811_L and covers family-specific semantic overrides."},
)


def _iter_available_successful_conversion_variants(
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


def _expand_successful_conversion_manifest_entry(
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


def _load_successful_conversions(
    manifest_path: Path = SUCCESSFUL_CONVERSIONS_MANIFEST,
    source_dir: Path = SUCCESSFUL_CONVERSIONS_SOURCE_DIR,
) -> tuple[str, ...]:
    """Load the canonical successful-conversions manifest from disk."""
    if manifest_path.exists():
        variants: list[str] = []
        available_variants = _iter_available_successful_conversion_variants(source_dir)
        for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            entry = line.split(";", 1)[0].strip()
            if not entry:
                continue
            variants.extend(_expand_successful_conversion_manifest_entry(entry, available_variants))
        normalized = tuple(dict.fromkeys(variants))
        if normalized:
            return normalized
    return SUCCESSFUL_CONVERSIONS_FALLBACK


SUCCESSFUL_CONVERSIONS = _load_successful_conversions()
AC08_PREVIOUSLY_GOOD_VARIANTS = tuple(variant for variant in SUCCESSFUL_CONVERSIONS if variant.startswith("AC08"))


def _build_ac08_regression_cases() -> tuple[dict[str, str], ...]:
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


AC08_REGRESSION_CASES = _build_ac08_regression_cases()
AC08_REGRESSION_SET_NAME = f"ac08_core_{len(AC08_REGRESSION_CASES)}"
AC08_REGRESSION_VARIANTS = tuple(case["variant"] for case in AC08_REGRESSION_CASES)


AC08_MITIGATION_STATUS: dict[str, dict[str, str]] = {
    "AC0882": {
        "family": "left_connector",
        "risk": "high",
        "implemented": "adaptive_locks,left_connector_family,small_variant_mode",
        "status": "Mitigated via adaptive fallback search, connector-family guardrails, and _S-specific tuning.",
    },
    "AC0837": {
        "family": "left_connector",
        "risk": "high",
        "implemented": "adaptive_locks,left_connector_family",
        "status": "Mitigated via adaptive fallback search plus shared left-connector geometry locks.",
    },
    "AC0839": {
        "family": "right_connector",
        "risk": "high",
        "implemented": "adaptive_locks,right_connector_family,small_variant_mode",
        "status": "Mitigated via mirrored connector guardrails with stagnation-triggered unlocks and _S handling.",
    },
    "AC0820": {
        "family": "circle_text",
        "risk": "medium",
        "implemented": "adaptive_locks,quality_pass_guardrails,co2_cluster_anchor",
        "status": "Mitigated via bounded quality-pass rollbacks, adaptive text scaling, and centered CO₂ layout.",
    },
    "AC0831": {
        "family": "semantic_vertical",
        "risk": "medium",
        "implemented": "adaptive_locks,semantic_vertical_family",
        "status": "Mitigated via semantic vertical-family tuning plus bounded fallback search on stubborn runs.",
    },
    "AC0834": {
        "family": "right_connector",
        "risk": "medium",
        "implemented": "right_connector_family,small_variant_mode",
        "status": "Mitigated via shared right-connector geometry enforcement and _S-specific connector/text floors.",
    },
    "AC0835": {
        "family": "circle_text",
        "risk": "medium",
        "implemented": "small_variant_mode,circle_text_family",
        "status": "Mitigated primarily through compact circle/text tuning for small variants.",
    },
    "AC0811": {
        "family": "semantic_vertical",
        "risk": "medium",
        "implemented": "semantic_audit,semantic_priority_rules,semantic_vertical_family",
        "status": "Mitigated via semantic audit output and strict family-priority rules for circle-with-stem badges.",
    },
    "AC0812": {
        "family": "semantic_horizontal",
        "risk": "medium",
        "implemented": "semantic_audit,semantic_priority_rules,left_connector_family",
        "status": "Mitigated via semantic conflict logging and shared left-connector family reconstruction.",
    },
}


# Backward-compatible aliases
_iter_available_successful_conversion_variants = _iter_available_successful_conversion_variants
_expand_successful_conversion_manifest_entry = _expand_successful_conversion_manifest_entry
_load_successful_conversions = _load_successful_conversions
_build_ac08_regression_cases = _build_ac08_regression_cases
