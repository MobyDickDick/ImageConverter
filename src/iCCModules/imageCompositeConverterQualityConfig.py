"""Quality pass config and SVG fallback helper functions."""

from __future__ import annotations

import base64
import json
import math
import os
from pathlib import Path


def svgHrefMimeTypeImpl(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
    }.get(ext, "application/octet-stream")


def renderEmbeddedRasterSvgImpl(
    input_path: str | Path,
    *,
    sniff_raster_size_fn,
) -> str:
    width, height = sniff_raster_size_fn(input_path)
    safe_w = max(1, int(width))
    safe_h = max(1, int(height))
    raw = Path(input_path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    mime_type = svgHrefMimeTypeImpl(input_path)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" '
        f'viewBox="0 0 {safe_w} {safe_h}">\n'
        f'  <image width="{safe_w}" height="{safe_h}" '
        f'href="data:{mime_type};base64,{encoded}" />\n'
        '</svg>\n'
    )


def qualityConfigPathImpl(reports_out_dir: str) -> str:
    return os.path.join(reports_out_dir, "quality_tercile_config.json")


def loadQualityConfigImpl(reports_out_dir: str, *, quality_config_path_fn) -> dict[str, object]:
    path = quality_config_path_fn(reports_out_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def writeQualityConfigImpl(
    reports_out_dir: str,
    *,
    allowed_error_per_pixel: float,
    skipped_variants: list[str],
    source: str,
    quality_config_path_fn,
) -> None:
    path = quality_config_path_fn(reports_out_dir)
    normalized_error_pp = float(allowed_error_per_pixel) if math.isfinite(allowed_error_per_pixel) else 0.0
    early_abort_config: dict[str, object] = {
        "enabled": True,
        "probe_iterations": 3,
        "threshold_multiplier": 8.0,
    }
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as existing_file:
                existing_payload = json.load(existing_file)
            existing_early_abort = existing_payload.get("early_abort", {}) if isinstance(existing_payload, dict) else {}
            if isinstance(existing_early_abort, dict):
                early_abort_config.update(existing_early_abort)
        except (json.JSONDecodeError, OSError):
            pass

    payload = {
        "allowed_error_per_pixel": float(max(0.0, normalized_error_pp)),
        "skip_variants": sorted(set(skipped_variants)),
        "early_abort": early_abort_config,
        "notes": (
            "Varianten in skip_variants werden in Folge-Pässen nicht erneut konvertiert. "
            "early_abort prueft einen kurzen Probelauf gegen die gespeicherte Erfolgsgrenze; "
            "threshold_multiplier ist bewusst konservativ, um aufholbare Starts nicht abzubrechen. "
            "Loeschen der Datei setzt den Ablauf zurueck, dann werden wieder alle Bitmaps bearbeitet."
        ),
        "source": source,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

GLOBAL_CONVERTER_CONFIG_SCHEMA_VERSION = "image_converter_global_config_v1"
_GLOBAL_CONFIG_TOP_LEVEL_KEYS = {
    "schema_version",
    "primitive_thresholds",
    "cost_function_weights",
    "budgets",
    "uncertainty_thresholds",
}
_GLOBAL_CONFIG_IMAGE_SCOPED_KEYS = {
    "image_id",
    "image_ids",
    "image_name",
    "variant",
    "variants",
    "variant_name",
    "base_name",
    "filename",
    "file_name",
    "catalog_id",
    "catalog_ids",
    "image_overrides",
    "variant_overrides",
    "per_image",
    "per_variant",
}


def globalConverterConfigPathImpl(root_dir: str) -> str:
    return os.path.join(root_dir, "config", "global_converter_config_v1.json")


def defaultGlobalConverterConfigV1Impl() -> dict[str, object]:
    return {
        "schema_version": GLOBAL_CONVERTER_CONFIG_SCHEMA_VERSION,
        "primitive_thresholds": {
            "min_circle_confidence": 0.55,
            "min_line_confidence": 0.50,
            "min_text_glyph_confidence": 0.45,
            "min_color_patch_confidence": 0.40,
        },
        "cost_function_weights": {
            "pixel_error": 1.0,
            "edge_alignment": 0.75,
            "structure_match": 1.25,
            "semantic_match": 1.5,
            "complexity_penalty": 0.15,
        },
        "budgets": {
            "validation_time_budget_sec": 90.0,
            "global_search_rounds": 3,
            "max_svg_elements": 64,
        },
        "uncertainty_thresholds": {
            "review_below_confidence": 0.65,
            "contradiction_cost": 0.80,
            "ambiguous_delta": 0.08,
        },
    }


def _collectGlobalConfigImageScopedKeys(payload: object, *, prefix: str = "") -> list[str]:
    if isinstance(payload, dict):
        findings: list[str] = []
        for key, value in payload.items():
            key_text = str(key)
            current = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in _GLOBAL_CONFIG_IMAGE_SCOPED_KEYS:
                findings.append(current)
            findings.extend(_collectGlobalConfigImageScopedKeys(value, prefix=current))
        return findings
    if isinstance(payload, list):
        findings = []
        for index, value in enumerate(payload):
            current = f"{prefix}[{index}]" if prefix else f"[{index}]"
            findings.extend(_collectGlobalConfigImageScopedKeys(value, prefix=current))
        return findings
    return []


def validateGlobalConverterConfigV1Impl(payload: object) -> dict[str, object]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["payload must be a JSON object"]}
    if payload.get("schema_version") != GLOBAL_CONVERTER_CONFIG_SCHEMA_VERSION:
        errors.append(f"schema_version must be {GLOBAL_CONVERTER_CONFIG_SCHEMA_VERSION}")
    unknown_keys = sorted(set(payload) - _GLOBAL_CONFIG_TOP_LEVEL_KEYS)
    if unknown_keys:
        errors.append("unknown top-level keys: " + ", ".join(unknown_keys))
    missing_keys = sorted(_GLOBAL_CONFIG_TOP_LEVEL_KEYS - set(payload))
    if missing_keys:
        errors.append("missing top-level keys: " + ", ".join(missing_keys))
    image_scoped_keys = _collectGlobalConfigImageScopedKeys(payload)
    if image_scoped_keys:
        errors.append("image-scoped keys are not allowed: " + ", ".join(sorted(image_scoped_keys)))
    for section in _GLOBAL_CONFIG_TOP_LEVEL_KEYS - {"schema_version"}:
        value = payload.get(section)
        if value is not None and not isinstance(value, dict):
            errors.append(f"{section} must be an object")
    return {"valid": not errors, "errors": errors}


def loadGlobalConverterConfigV1Impl(root_dir: str, *, global_config_path_fn) -> dict[str, object]:
    path = global_config_path_fn(root_dir)
    defaults = defaultGlobalConverterConfigV1Impl()
    if not os.path.exists(path):
        return {**defaults, "source": "defaults"}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        validation = {"valid": False, "errors": [str(exc)]}
        return {**defaults, "source": "defaults", "validation": validation}
    validation = validateGlobalConverterConfigV1Impl(payload)
    if not validation["valid"]:
        return {**defaults, "source": "defaults", "validation": validation}
    return {**payload, "source": "file", "validation": validation}
