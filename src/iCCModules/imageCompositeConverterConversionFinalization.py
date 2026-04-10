"""Finalization helpers for convertRange post-processing."""

from __future__ import annotations

import math
import os
from pathlib import Path
import re
import statistics


def _parseSemicolonKeyValueLine(raw_line: str) -> tuple[str, dict[str, str]]:
    stripped = raw_line.split("#", 1)[0].strip()
    if not stripped:
        return "", {}
    parts = [part.strip() for part in stripped.split(";") if part.strip()]
    if not parts:
        return "", {}
    variant = parts[0].upper()
    payload: dict[str, str] = {}
    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        payload[key.strip()] = value.strip()
    return variant, payload


def _computeDynamicAc08MeanDelta2Threshold(reports_out_dir: str) -> float:
    """Build a dynamic AC08 quality threshold from report-listed good conversions."""
    manifest_path = Path(reports_out_dir) / "successful_conversions.txt"
    if not manifest_path.exists():
        return float("inf")

    mean_delta2_values: list[float] = []
    try:
        lines = manifest_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return float("inf")

    for raw_line in lines:
        variant, payload = _parseSemicolonKeyValueLine(raw_line)
        if not variant.startswith("AC08"):
            continue
        status = str(payload.get("status", "")).strip().lower()
        if status != "semantic_ok":
            continue
        raw_value = str(payload.get("mean_delta2", "")).strip().replace(",", ".")
        if not raw_value:
            continue
        try:
            value = float(raw_value)
        except ValueError:
            continue
        if math.isfinite(value):
            mean_delta2_values.append(value)

    if len(mean_delta2_values) < 3:
        return float("inf")

    # Robust outlier-tolerant threshold:
    # baseline = median(mean_delta2), spread = 1.5 * IQR.
    # This adapts to current run quality while remaining stable against a few outliers.
    quartiles = statistics.quantiles(mean_delta2_values, n=4, method="inclusive")
    q1 = float(quartiles[0])
    q3 = float(quartiles[2])
    iqr = max(0.0, q3 - q1)
    return max(0.0, statistics.median(mean_delta2_values) + (1.5 * iqr))


def _svgContainsEmbeddedRaster(svg_path: Path) -> bool:
    try:
        content = svg_path.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    if "data:image/" in content:
        return True

    if "<image" not in content:
        return False

    href_values = re.findall(r"(?:href|xlink:href)\s*=\s*['\"]([^'\"]+)['\"]", content)
    for href in href_values:
        if href.startswith("data:image/"):
            return True
        if re.search(r"\.(png|jpe?g|gif|webp|bmp|tiff?)(?:$|[?#])", href):
            return True
        if href.startswith("data:") and "base64," in href and "ivborw0kggo" in href:
            return True
    return False


def _markPoorConversionsWithFailedPrefix(
    *,
    svg_out_dir: str,
    result_map: dict[str, dict[str, object]],
    reports_out_dir: str,
) -> None:
    threshold = _computeDynamicAc08MeanDelta2Threshold(reports_out_dir)
    svg_dir = Path(svg_out_dir)
    if not svg_dir.exists():
        return

    rows_by_variant: dict[str, dict[str, object]] = {}
    for row in result_map.values():
        variant = str(row.get("variant", "")).strip().upper()
        if not variant:
            continue
        rows_by_variant[variant] = row

    variants_from_svg_names: set[str] = set()
    for svg_path in svg_dir.glob("*.svg"):
        stem = svg_path.stem
        if stem.lower().startswith("failed_"):
            stem = stem[len("failed_") :]
        normalized = stem.strip().upper()
        if normalized:
            variants_from_svg_names.add(normalized)

    for variant in sorted(set(rows_by_variant) | variants_from_svg_names):
        row = rows_by_variant.get(variant, {})

        base_svg = svg_dir / f"{variant}.svg"
        failed_svg = svg_dir / f"Failed_{variant}.svg"
        svg_path = base_svg if base_svg.exists() else failed_svg
        if not svg_path.exists():
            continue

        mean_delta2 = float(row.get("mean_delta2", float("inf")))
        quality_fail = math.isfinite(mean_delta2) and math.isfinite(threshold) and mean_delta2 > threshold
        raster_fail = _svgContainsEmbeddedRaster(svg_path)
        should_fail = bool(quality_fail or raster_fail)
        has_run_metrics = variant in rows_by_variant

        if should_fail and svg_path != failed_svg:
            if failed_svg.exists():
                failed_svg.unlink()
            base_svg.rename(failed_svg)
        elif has_run_metrics and (not should_fail) and svg_path == failed_svg:
            if base_svg.exists():
                base_svg.unlink()
            failed_svg.rename(base_svg)


def _canonicalizeFailedAttemptSvgNames(
    *,
    svg_out_dir: str,
) -> None:
    """Normalize failed-attempt SVG names to the canonical ``Failed_<variant>.svg`` format."""
    svg_dir = Path(svg_out_dir)
    if not svg_dir.exists():
        return

    for candidate in svg_dir.glob("*_failed.svg"):
        variant = candidate.stem[: -len("_failed")]
        if not variant:
            continue
        normalized = svg_dir / f"Failed_{variant}.svg"
        if normalized.exists():
            normalized.unlink()
        candidate.rename(normalized)

    for candidate in svg_dir.glob("failed_*.svg"):
        variant = candidate.stem[len("failed_") :]
        if not variant:
            continue
        normalized = svg_dir / f"Failed_{variant}.svg"
        if normalized.exists():
            normalized.unlink()
        candidate.rename(normalized)

def runConversionFinalizationImpl(
    *,
    reports_out_dir: str,
    quality_logs: list[dict[str, object]],
    conversion_bestlist_path,
    conversion_bestlist_rows: dict[str, dict[str, object]],
    batch_failures: list[dict[str, str]],
    strategy_logs: list[dict[str, object]],
    files: list[str],
    result_map: dict[str, dict[str, object]],
    folder_path: str,
    csv_path: str,
    iterations: int,
    svg_out_dir: str,
    diff_out_dir: str,
    normalized_selected_variants: set[str],
    write_quality_pass_report_fn,
    write_conversion_bestlist_metrics_fn,
    write_batch_failure_summary_fn,
    write_strategy_switch_template_transfers_report_fn,
    write_iteration_log_and_collect_semantic_results_fn,
    harmonize_semantic_size_variants_fn,
    run_post_conversion_reporting_fn,
) -> list[dict[str, object]]:
    """Write run artifacts and trigger semantic harmonization/reporting."""
    write_quality_pass_report_fn(reports_out_dir, quality_logs)
    write_conversion_bestlist_metrics_fn(conversion_bestlist_path, conversion_bestlist_rows)
    write_batch_failure_summary_fn(reports_out_dir, batch_failures)
    if strategy_logs:
        write_strategy_switch_template_transfers_report_fn(reports_out_dir, strategy_logs)

    log_path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    semantic_results = write_iteration_log_and_collect_semantic_results_fn(files, result_map, log_path)

    harmonize_semantic_size_variants_fn(semantic_results, folder_path, svg_out_dir, reports_out_dir)
    run_post_conversion_reporting_fn(
        folder_path=folder_path,
        csv_path=csv_path,
        iterations=iterations,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        reports_out_dir=reports_out_dir,
        normalized_selected_variants=normalized_selected_variants,
        result_map=result_map,
    )
    _canonicalizeFailedAttemptSvgNames(svg_out_dir=svg_out_dir)
    _markPoorConversionsWithFailedPrefix(
        svg_out_dir=svg_out_dir,
        result_map=result_map,
        reports_out_dir=reports_out_dir,
    )
    return semantic_results
