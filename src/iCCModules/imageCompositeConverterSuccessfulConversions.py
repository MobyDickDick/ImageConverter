"""Successful-conversion helper functions extracted from imageCompositeConverter."""

from __future__ import annotations

import contextlib
import csv
import json
import math
import os
from pathlib import Path


def parseSuccessfulConversionManifestLineImpl(raw_line: str) -> tuple[str, dict[str, object]]:
    """Parse one successful-conversions manifest line into variant plus metrics."""
    stripped = raw_line.split("#", 1)[0].strip()
    if not stripped:
        return "", {}

    parts = [part.strip() for part in stripped.split(";") if part.strip()]
    if not parts:
        return "", {}

    variant = parts[0].upper()
    metrics: dict[str, object] = {"variant": variant}
    for field in parts[1:]:
        if "=" not in field:
            continue
        key, value = [token.strip() for token in field.split("=", 1)]
        if not key:
            continue
        if key == "pixel_count":
            with contextlib.suppress(ValueError):
                metrics[key] = int(value)
            continue
        if key in {"diff_score", "error_per_pixel", "total_delta2", "mean_delta2", "std_delta2"}:
            with contextlib.suppress(ValueError):
                metrics[key] = float(value.replace(",", "."))
            continue
        metrics[key] = value
    return variant, metrics


def readSuccessfulConversionManifestMetricsImpl(
    manifest_path: Path,
    parse_manifest_line_fn=parseSuccessfulConversionManifestLineImpl,
) -> dict[str, dict[str, object]]:
    """Load persisted best-list metrics keyed by variant."""
    if not manifest_path.exists():
        return {}

    rows: dict[str, dict[str, object]] = {}
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        variant, metrics = parse_manifest_line_fn(raw_line)
        if variant:
            rows[variant] = metrics
    return rows


def successfulConversionSnapshotDirImpl(reports_out_dir: str) -> Path:
    """Directory used to persist best-of artifacts for successful conversions."""
    return Path(reports_out_dir) / "successful_conversions_bestlist"


def successfulConversionSnapshotPathsImpl(
    reports_out_dir: str,
    variant: str,
    snapshot_dir_fn=successfulConversionSnapshotDirImpl,
) -> dict[str, Path]:
    base_dir = snapshot_dir_fn(reports_out_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    return {
        "svg": base_dir / f"{variant}.svg",
        "log": base_dir / f"{variant}_element_validation.log",
        "metrics": base_dir / f"{variant}.json",
    }


def restoreSuccessfulConversionSnapshotImpl(
    variant: str,
    svg_out_dir: str,
    reports_out_dir: str,
    snapshot_paths_fn=successfulConversionSnapshotPathsImpl,
) -> bool:
    """Restore the previous best conversion for ``variant`` if a snapshot exists."""
    snapshot_paths = snapshot_paths_fn(reports_out_dir, variant)
    restored = False

    target_svg = Path(svg_out_dir) / f"{variant}.svg"
    if snapshot_paths["svg"].exists():
        target_svg.parent.mkdir(parents=True, exist_ok=True)
        target_svg.write_text(snapshot_paths["svg"].read_text(encoding="utf-8"), encoding="utf-8")
        restored = True

    target_log = Path(reports_out_dir) / f"{variant}_element_validation.log"
    if snapshot_paths["log"].exists():
        target_log.write_text(snapshot_paths["log"].read_text(encoding="utf-8"), encoding="utf-8")
        restored = True

    return restored


def storeSuccessfulConversionSnapshotImpl(
    variant: str,
    metrics: dict[str, object],
    svg_out_dir: str,
    reports_out_dir: str,
    snapshot_paths_fn=successfulConversionSnapshotPathsImpl,
) -> None:
    """Persist the current best conversion artifacts for later rollback/restoration."""
    snapshot_paths = snapshot_paths_fn(reports_out_dir, variant)
    target_svg = Path(svg_out_dir) / f"{variant}.svg"
    if target_svg.exists():
        snapshot_paths["svg"].write_text(target_svg.read_text(encoding="utf-8"), encoding="utf-8")

    target_log = Path(reports_out_dir) / f"{variant}_element_validation.log"
    if target_log.exists():
        snapshot_paths["log"].write_text(target_log.read_text(encoding="utf-8"), encoding="utf-8")

    snapshot_paths["metrics"].write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def isSuccessfulConversionCandidateBetterImpl(
    previous_metrics: dict[str, object] | None,
    candidate_metrics: dict[str, object],
    metrics_available_fn,
    evaluate_candidate_fn,
) -> bool:
    """Accept a new best-list candidate only when it improves quality."""
    if not metrics_available_fn(candidate_metrics):
        return False
    if not previous_metrics or not metrics_available_fn(previous_metrics):
        return True

    previous_status = str(previous_metrics.get("status", "")).strip().lower()
    candidate_status = str(candidate_metrics.get("status", "")).strip().lower()
    if previous_status == "semantic_ok" and candidate_status != "semantic_ok":
        return False
    if previous_status != "semantic_ok" and candidate_status == "semantic_ok":
        return True

    improved, _decision, _prev_error, _new_error, _prev_delta, _new_delta = evaluate_candidate_fn(
        previous_metrics,
        candidate_metrics,
    )
    return improved


def mergeSuccessfulConversionMetricsImpl(
    baseline: dict[str, object],
    override: dict[str, object],
) -> dict[str, object]:
    """Merge ``override`` into ``baseline`` while keeping row-level defaults."""
    merged = dict(baseline)
    for key, value in override.items():
        if key == "variant":
            continue
        merged[key] = value
    merged["variant"] = str(override.get("variant", baseline.get("variant", ""))).strip().upper()
    return merged


def formatSuccessfulConversionManifestLineImpl(
    existing_line: str,
    metrics: dict[str, object],
    metrics_available_fn,
) -> str:
    """Render one enriched successful-conversions manifest line."""
    if not metrics_available_fn(metrics):
        return existing_line.rstrip("\n")

    variant = str(metrics.get("variant", "")).strip().upper()
    prefix, comment = existing_line, ""
    if "#" in existing_line:
        prefix, comment = existing_line.split("#", 1)
        comment = "#" + comment.rstrip("\n").rstrip("\r").rstrip()
    prefix = prefix.strip()
    if not prefix:
        return existing_line.rstrip("\n")

    fields = [variant]
    status = str(metrics.get("status", "")).strip()
    if status:
        fields.append(f"status={status}")
    best_iteration = str(metrics.get("best_iteration", "")).strip()
    if best_iteration:
        fields.append(f"best_iteration={best_iteration}")
    for key, precision in (
        ("diff_score", 6),
        ("error_per_pixel", 8),
        ("total_delta2", 6),
        ("mean_delta2", 6),
        ("std_delta2", 6),
    ):
        value = float(metrics.get(key, float("nan")))
        if math.isfinite(value):
            fields.append(f"{key}={value:.{precision}f}")
    pixel_count = int(metrics.get("pixel_count", 0) or 0)
    if pixel_count > 0:
        fields.append(f"pixel_count={pixel_count}")

    line = " ; ".join(fields)
    if comment:
        line += "  " + comment
    return line


def latestFailedConversionManifestEntryImpl(reports_out_dir: str) -> dict[str, object] | None:
    """Return the most recent failed conversion as a manifest-like row."""
    summary_path = Path(reports_out_dir) / "batch_failure_summary.csv"
    if not summary_path.exists():
        return None

    latest_row: dict[str, str] | None = None
    try:
        with summary_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                filename = str(row.get("filename", "")).strip()
                status = str(row.get("status", "")).strip().lower()
                if not filename or status not in {"render_failure", "batch_error", "semantic_mismatch"}:
                    continue
                latest_row = row
    except OSError:
        return None

    if latest_row is None:
        return None

    variant = Path(str(latest_row.get("filename", "")).strip()).stem.upper()
    if not variant:
        return None

    return {
        "variant": variant,
        "status": "failed",
        "failure_reason": str(latest_row.get("reason", "")).strip(),
    }


def sortedSuccessfulConversionMetricsRowsImpl(
    metrics: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Sort successful-conversion rows by converted image name/variant."""
    return sorted(metrics, key=lambda row: str(row.get("variant", "")).upper())


def writeSuccessfulConversionCsvTableImpl(
    csv_path: str | os.PathLike[str],
    metrics: list[dict[str, object]],
    sorted_rows_fn=sortedSuccessfulConversionMetricsRowsImpl,
) -> str:
    """Write the successful-conversions leaderboard as a CSV table."""
    csv_path = os.fspath(csv_path)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "variant", "status", "image_found", "svg_found", "log_found", "best_iteration",
            "diff_score", "error_per_pixel", "pixel_count", "total_delta2", "mean_delta2", "std_delta2",
        ])
        for row in sorted_rows_fn(metrics):
            writer.writerow([
                row["variant"],
                row["status"],
                int(bool(row["image_found"])),
                int(bool(row["svg_found"])),
                int(bool(row["log_found"])),
                row["best_iteration"],
                "" if not math.isfinite(float(row["diff_score"])) else f"{float(row['diff_score']):.6f}",
                "" if not math.isfinite(float(row["error_per_pixel"])) else f"{float(row['error_per_pixel']):.8f}",
                int(row["pixel_count"]),
                "" if not math.isfinite(float(row["total_delta2"])) else f"{float(row['total_delta2']):.6f}",
                "" if not math.isfinite(float(row["mean_delta2"])) else f"{float(row['mean_delta2']):.6f}",
                "" if not math.isfinite(float(row["std_delta2"])) else f"{float(row['std_delta2']):.6f}",
            ])
    return csv_path
