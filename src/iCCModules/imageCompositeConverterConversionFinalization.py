"""Finalization helpers for convertRange post-processing."""

from __future__ import annotations

import math
import os
from pathlib import Path
import re
import statistics


_FALLBACK_MAX_ERROR_PER_PIXEL = 18.0


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

    has_image_tag = "<image" in content
    if not has_image_tag:
        return False

    href_values = re.findall(r"(?:href|xlink:href)\s*=\s*['\"]([^'\"]+)['\"]", content)
    for href in href_values:
        if href.startswith("data:image/"):
            return True
        if re.search(r"\.(png|jpe?g|gif|webp|bmp|tiff?)(?:$|[?#])", href):
            return True
        if href.startswith("data:") and "base64," in href and "ivborw0kggo" in href:
            return True
    # Generic fallback: treat standalone SVG <image> payloads as raster artifacts
    # even when href does not expose a file extension/mime marker.
    return True


def _svgIsTrivialFallback(svg_path: Path) -> bool:
    try:
        content = svg_path.read_text(encoding="utf-8").lower()
    except OSError:
        return False

    compact = re.sub(r"\s+", "", content)
    has_minimal_canvas = 'width="1"' in compact and 'height="1"' in compact and "viewbox=\"0011\"" in compact
    rect_match = re.search(r"<rect([^>]*)>", compact)
    rect_attrs = rect_match.group(1) if rect_match else ""
    has_white_rect = bool(rect_match) and bool(
        re.search(r"width=(['\"])100%\1", rect_attrs)
    ) and bool(
        re.search(r"height=(['\"])100%\1", rect_attrs)
    ) and bool(
        re.search(r"fill=(['\"])#ffffff\1", rect_attrs)
    )
    return has_minimal_canvas and has_white_rect



def _svgIsLowInformationBlank(svg_path: Path) -> bool:
    """Return True for SVGs that contain only a pale canvas/frame and no symbol ink.

    This catches failed conversions that preserve a background rectangle while
    dropping all semantic foreground content (letters, stems, paths, etc.).
    The rule is deliberately structural and catalog-independent: any path,
    text, circle/ellipse, line, polygon/polyline, embedded image, or dark rect
    keeps the SVG out of this blank bucket.
    """
    try:
        content = svg_path.read_text(encoding="utf-8").lower()
    except OSError:
        return False

    if any(token in content for token in ("<path", "<text", "<circle", "<ellipse", "<line", "<polyline", "<polygon", "<image")):
        return False

    rect_attrs = re.findall(r"<rect\b([^>/]*)(?:/?>)", content)
    if not rect_attrs:
        return False

    def _channel_is_light(value: str) -> bool:
        value = value.strip().lower()
        if value in {"none", "transparent"}:
            return True
        if value.startswith("#"):
            hex_value = value[1:]
            if len(hex_value) == 3:
                hex_value = "".join(ch * 2 for ch in hex_value)
            if len(hex_value) == 6:
                try:
                    channels = [int(hex_value[idx : idx + 2], 16) for idx in (0, 2, 4)]
                except ValueError:
                    return False
                return min(channels) >= 200
        if value.startswith("rgb"):
            nums = [int(n) for n in re.findall(r"\d+", value)[:3]]
            return len(nums) == 3 and min(nums) >= 200
        return value in {"white", "whitesmoke"}

    for attrs in rect_attrs:
        style = dict(re.findall(r"([a-z-]+)\s*:\s*([^;]+)", attrs))
        attr_values = dict(re.findall(r'([a-z:-]+)\s*=\s*[\'\"]([^\'\"]+)[\'\"]', attrs))
        fill = style.get("fill", attr_values.get("fill", "#000000"))
        stroke = style.get("stroke", attr_values.get("stroke", "none"))
        if not (_channel_is_light(fill) and _channel_is_light(stroke)):
            return False
    return True

def _collectValidationStatusesByVariant(reports_out_dir: str) -> dict[str, str]:
    reports_dir = Path(reports_out_dir)
    if not reports_dir.exists():
        return {}

    statuses: dict[str, str] = {}
    for log_path in reports_dir.glob("*_element_validation.log"):
        stem = log_path.stem
        if not stem.endswith("_element_validation"):
            continue
        variant = stem[: -len("_element_validation")].strip().upper()
        if not variant:
            continue
        status = ""
        try:
            for raw_line in log_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if line.lower().startswith("status="):
                    status = line.split("=", 1)[1].strip().lower()
                    break
        except OSError:
            continue
        if status:
            statuses[variant] = status
    return statuses


def _markPoorConversionsWithFailedPrefix(
    *,
    svg_out_dir: str,
    result_map: dict[str, dict[str, object]],
    reports_out_dir: str,
) -> None:
    threshold = _computeDynamicAc08MeanDelta2Threshold(reports_out_dir)
    status_by_variant = _collectValidationStatusesByVariant(reports_out_dir)
    fallback_mode_active = Path(reports_out_dir, "fallback_mode.txt").exists()
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
    svg_paths_by_variant: dict[str, Path] = {}
    for svg_path in svg_dir.glob("*.svg"):
        stem = svg_path.stem
        if stem.lower().startswith("failed_"):
            stem = stem[len("failed_") :]
        normalized = stem.strip().upper()
        if normalized:
            variants_from_svg_names.add(normalized)
            svg_paths_by_variant[normalized] = svg_path

    if fallback_mode_active:
        for variant in sorted(variants_from_svg_names):
            failed_svg = svg_dir / f"Failed_{variant}.svg"
            base_svg = svg_dir / f"{variant}.svg"
            if failed_svg.exists():
                if base_svg.exists():
                    base_svg.unlink()
                failed_svg.rename(base_svg)
        return

    for variant in sorted(set(rows_by_variant) | variants_from_svg_names):
        row = rows_by_variant.get(variant, {})

        base_svg = svg_dir / f"{variant}.svg"
        failed_svg = svg_dir / f"Failed_{variant}.svg"
        existing_svg = svg_paths_by_variant.get(variant)
        svg_path = base_svg if base_svg.exists() else failed_svg
        if not svg_path.exists() and existing_svg is not None:
            svg_path = existing_svg
        if not svg_path.exists():
            continue

        mean_delta2 = float(row.get("mean_delta2", float("inf")))
        error_per_pixel = float(row.get("error_per_pixel", float("inf")))
        mean_delta2_fail = math.isfinite(mean_delta2) and math.isfinite(threshold) and mean_delta2 > threshold
        # Small local runs often do not have enough successful AC08 rows to build
        # a dynamic mean-delta threshold.  Without a fallback, visibly poor
        # vectorizations with a very high per-pixel error kept their normal SVG
        # name and looked like accepted conversions.  Keep the dynamic AC08 gate
        # when available, but always reject candidates that exceed the generic
        # per-pixel quality ceiling used by the ranking/reporting pipeline.
        error_per_pixel_fail = math.isfinite(error_per_pixel) and error_per_pixel > _FALLBACK_MAX_ERROR_PER_PIXEL
        quality_fail = mean_delta2_fail or error_per_pixel_fail
        raster_fail = (not fallback_mode_active) and _svgContainsEmbeddedRaster(svg_path)
        trivial_fail = (not fallback_mode_active) and (_svgIsTrivialFallback(svg_path) or _svgIsLowInformationBlank(svg_path))
        is_skipped_variant = str(status_by_variant.get(variant, "")).startswith("skipped_")
        if is_skipped_variant:
            # Skipped variants have no fresh quality metric from this run,
            # but existing fallback SVG payloads should still be normalized.
            quality_fail = False
        should_fail = bool(quality_fail or raster_fail or trivial_fail)
        has_run_metrics = variant in rows_by_variant

        if should_fail and svg_path != failed_svg:
            if failed_svg.exists():
                failed_svg.unlink()
            svg_path.rename(failed_svg)
        elif has_run_metrics and (not should_fail) and svg_path == failed_svg:
            if base_svg.exists():
                base_svg.unlink()
            failed_svg.rename(base_svg)
        elif has_run_metrics and (not should_fail) and base_svg.exists() and failed_svg.exists():
            failed_svg.unlink()


def _failedArtifactDirsForSvgDir(svg_out_dir: str) -> tuple[Path, Path]:
    """Return sibling directories for failed SVG and rendered PNG artifacts."""
    output_root = Path(svg_out_dir).parent
    return output_root / "converted_svg_failed", output_root / "converted_images_png_failed"


def _moveFailedConversionArtifactsToFailedDirs(
    *,
    svg_out_dir: str,
    result_map: dict[str, dict[str, object]],
) -> set[str]:
    """Move rejected conversion artifacts out of the successful output folders.

    Poor conversions are first normalized to ``Failed_<variant>.svg`` by
    ``_markPoorConversionsWithFailedPrefix``.  This helper then quarantines the
    rejected SVG and its rendered PNG preview in dedicated failed-artifact
    directories so the regular converted folders contain only acceptable
    candidates.
    """
    svg_dir = Path(svg_out_dir)
    if not svg_dir.exists():
        return set()

    failed_svg_dir, failed_png_dir = _failedArtifactDirsForSvgDir(svg_out_dir)
    failed_svg_dir.mkdir(parents=True, exist_ok=True)
    failed_png_dir.mkdir(parents=True, exist_ok=True)
    png_dir = svg_dir.parent / "converted_images_png"

    failed_variants: set[str] = set()
    for failed_svg in sorted(svg_dir.glob("Failed_*.svg")):
        variant = failed_svg.stem[len("Failed_") :].strip().upper()
        if not variant:
            continue
        failed_variants.add(variant)

        target_svg = failed_svg_dir / f"{variant}.svg"
        if target_svg.exists():
            target_svg.unlink()
        failed_svg.replace(target_svg)

        base_svg = svg_dir / f"{variant}.svg"
        if base_svg.exists():
            base_svg.unlink()

        source_png = png_dir / f"{variant}.png"
        if source_png.exists():
            target_png = failed_png_dir / source_png.name
            if target_png.exists():
                target_png.unlink()
            source_png.replace(target_png)

    if failed_variants:
        for row in result_map.values():
            variant = str(row.get("variant", "")).strip().upper()
            if variant in failed_variants:
                row["status"] = "quality_failed"
                row["failure_reason"] = "unsatisfactory_result"

    return failed_variants


def _archiveSuccessfulConversionArtifacts(*,
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    result_map: dict[str, dict[str, object]],
) -> None:
    """Archive successful source images and copy their SVGs into a bestlist folder."""
    reports_dir = Path(reports_out_dir)
    bestlist_dir = reports_dir / "successful_conversions_bestlist"
    # Keep accepted inputs beside the intake directory so the next batch cannot
    # reconvert them, while leaving rejected inputs in place for another pass.
    archive_dir = Path(folder_path) / "succesessfulConvertedImages"
    bestlist_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    for filename, row in result_map.items():
        status = str(row.get("status", "")).strip().lower()
        if status not in {"semantic_ok", "ok", "success", "passed"}:
            continue
        variant = str(row.get("variant", "")).strip().upper()
        if not variant:
            continue

        svg_path = Path(svg_out_dir) / f"{variant}.svg"
        failed_svg_path = Path(svg_out_dir) / f"Failed_{variant}.svg"
        if svg_path.exists():
            (bestlist_dir / svg_path.name).write_text(svg_path.read_text(encoding="utf-8"), encoding="utf-8")
        elif failed_svg_path.exists():
            # Failed SVGs are never bestlist candidates.
            continue

        source_path = Path(folder_path) / filename
        if source_path.exists():
            target_path = archive_dir / source_path.name
            if target_path.exists():
                target_path.unlink()
            source_path.replace(target_path)


def _findOpenTasksPathForReportsDir(reports_out_dir: str) -> Path | None:
    """Return the nearest repository ``docs/open_tasks.md`` for a reports directory."""
    reports_path = Path(reports_out_dir).resolve()
    for candidate in (reports_path, *reports_path.parents):
        open_tasks_path = candidate / "docs" / "open_tasks.md"
        if open_tasks_path.exists():
            return open_tasks_path
    return None


def _removeSuccessfulVariantsFromOpenTasks(*, reports_out_dir: str, result_map: dict[str, dict[str, object]]) -> None:
    """Remove successful variants from open checkbox task lines in docs/open_tasks.md."""
    open_tasks_path = _findOpenTasksPathForReportsDir(reports_out_dir)
    if open_tasks_path is None:
        return

    successful_variants: set[str] = set()
    for row in result_map.values():
        status = str(row.get("status", "")).strip().lower()
        if status in {"semantic_ok", "ok", "success", "passed"}:
            variant = str(row.get("variant", "")).strip().upper()
            if variant:
                successful_variants.add(variant)

    if not successful_variants:
        return

    lines = open_tasks_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    for line in lines:
        if line.lstrip().startswith("- [ ]") and any(variant in line.upper() for variant in successful_variants):
            continue
        updated_lines.append(line)
    open_tasks_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


def _appendFailureFollowUpTasks(*, reports_out_dir: str, batch_failures: list[dict[str, str]]) -> None:
    """Append open task entries for conversion failures that have no existing task line yet."""
    if not batch_failures:
        return

    open_tasks_path = _findOpenTasksPathForReportsDir(reports_out_dir)
    if open_tasks_path is None:
        return

    try:
        existing_content = open_tasks_path.read_text(encoding="utf-8")
    except OSError:
        return
    existing_upper = existing_content.upper()

    variants_to_add: list[tuple[str, str, str]] = []
    seen_variants: set[str] = set()
    for failure in batch_failures:
        filename = str(failure.get("filename", "")).strip()
        if not filename:
            continue
        variant = Path(filename).stem.strip().upper()
        if not variant or variant in seen_variants:
            continue
        seen_variants.add(variant)
        if variant in existing_upper:
            continue
        status = str(failure.get("status", "conversion_failed")).strip() or "conversion_failed"
        reason = str(failure.get("reason", "no_result")).strip() or "no_result"
        variants_to_add.append((variant, status, reason))

    if not variants_to_add:
        return

    lines = existing_content.splitlines()
    marker = "## Session-Log"
    insert_idx = len(lines)
    for idx, line in enumerate(lines):
        if line.strip() == marker:
            insert_idx = idx
            break

    new_lines: list[str] = []
    if insert_idx > 0 and lines[insert_idx - 1].strip():
        new_lines.append("")
    new_lines.append("## Automatisch erzeugte Folgeaufgaben (Konvertierungsfehler)")
    for variant, status, reason in variants_to_add:
        new_lines.append(
            f"- [ ] AUFGABE: Fehleranalyse `{variant}` (status={status}, reason={reason}) und Gegenmaßnahme ableiten."
        )
    new_lines.append("")

    updated_lines = lines[:insert_idx] + new_lines + lines[insert_idx:]
    open_tasks_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


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
        same_target = candidate == normalized
        if normalized.exists() and not same_target:
            normalized.unlink()
        if not same_target:
            candidate.rename(normalized)

    for candidate in svg_dir.glob("failed_*.svg"):
        variant = candidate.stem[len("failed_") :]
        if not variant:
            continue
        normalized = svg_dir / f"Failed_{variant}.svg"
        same_target = candidate == normalized
        if normalized.exists() and not same_target:
            normalized.unlink()
        if not same_target:
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
    write_chain_telemetry_batch_report_fn=None,
    write_optimization_render_telemetry_summary_fn=None,
) -> list[dict[str, object]]:
    """Write run artifacts and trigger semantic harmonization/reporting."""
    write_quality_pass_report_fn(reports_out_dir, quality_logs)
    write_conversion_bestlist_metrics_fn(conversion_bestlist_path, conversion_bestlist_rows)
    write_batch_failure_summary_fn(reports_out_dir, batch_failures)
    if write_optimization_render_telemetry_summary_fn is not None:
        write_optimization_render_telemetry_summary_fn(reports_out_dir, result_map)
    if strategy_logs:
        write_strategy_switch_template_transfers_report_fn(reports_out_dir, strategy_logs)
    if write_chain_telemetry_batch_report_fn is not None:
        write_chain_telemetry_batch_report_fn(reports_out_dir, result_map)

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
    _moveFailedConversionArtifactsToFailedDirs(
        svg_out_dir=svg_out_dir,
        result_map=result_map,
    )
    _archiveSuccessfulConversionArtifacts(
        folder_path=folder_path,
        svg_out_dir=svg_out_dir,
        reports_out_dir=reports_out_dir,
        result_map=result_map,
    )
    _removeSuccessfulVariantsFromOpenTasks(
        reports_out_dir=reports_out_dir,
        result_map=result_map,
    )
    _appendFailureFollowUpTasks(
        reports_out_dir=reports_out_dir,
        batch_failures=batch_failures,
    )
    return semantic_results
