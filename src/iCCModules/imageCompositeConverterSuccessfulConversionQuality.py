"""Successful-conversion quality metric helper functions."""

from __future__ import annotations

import csv
import os


def loadIterationLogRowsImpl(reports_out_dir: str) -> dict[str, dict[str, str]]:
    """Load Iteration_Log.csv keyed by uppercase filename stem."""
    path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    if not os.path.exists(path):
        return {}

    rows: dict[str, dict[str, str]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            filename = str(row.get("Dateiname", "")).strip()
            if not filename:
                continue
            rows[os.path.splitext(filename)[0].upper()] = dict(row)
    return rows


def findImagePathByVariantImpl(folder_path: str, variant: str) -> str | None:
    """Return the raster image path for ``variant`` if present."""
    for ext in (".jpg", ".png", ".bmp", ".gif"):
        candidate = os.path.join(folder_path, f"{variant}{ext}")
        if os.path.exists(candidate):
            return candidate
    return None


def collectSuccessfulConversionQualityMetricsImpl(
    *,
    folder_path: str,
    svg_out_dir: str,
    reports_out_dir: str,
    successful_variants: list[str] | tuple[str, ...],
    successful_conversions: list[str] | tuple[str, ...],
    load_iteration_log_rows_fn,
    find_image_path_by_variant_fn,
    read_validation_log_details_fn,
    render_svg_to_numpy_fn,
    cv2_module,
    np_module,
) -> list[dict[str, object]]:
    """Collect quality metrics for variants listed as successful conversions."""
    if cv2_module is None or np_module is None:
        missing = []
        if cv2_module is None:
            missing.append("cv2")
        if np_module is None:
            missing.append("numpy")
        raise RuntimeError("Required image dependencies are missing: " + ", ".join(missing))

    variants = [str(v).strip().upper() for v in (successful_variants or successful_conversions) if str(v).strip()]
    iteration_rows = load_iteration_log_rows_fn(reports_out_dir)
    metrics: list[dict[str, object]] = []
    seen: set[str] = set()
    for variant in variants:
        if variant in seen:
            continue
        seen.add(variant)
        image_path = find_image_path_by_variant_fn(folder_path, variant)
        svg_path = os.path.join(svg_out_dir, f"{variant}.svg")
        log_path = os.path.join(reports_out_dir, f"{variant}_element_validation.log")

        row: dict[str, object] = {
            "variant": variant,
            "image_found": os.path.exists(image_path) if image_path else False,
            "svg_found": os.path.exists(svg_path),
            "log_found": os.path.exists(log_path),
            "status": "",
            "best_iteration": "",
            "diff_score": float("nan"),
            "error_per_pixel": float("nan"),
            "pixel_count": 0,
            "total_delta2": float("nan"),
            "mean_delta2": float("nan"),
            "std_delta2": float("nan"),
        }

        details = read_validation_log_details_fn(log_path) if os.path.exists(log_path) else {}
        row["status"] = details.get("status", "")

        iteration = iteration_rows.get(variant, {})
        row["best_iteration"] = str(iteration.get("Beste Iteration", "")).strip()
        try:
            row["diff_score"] = float(str(iteration.get("Diff-Score", "")).strip().replace(",", "."))
        except ValueError:
            row["diff_score"] = float("nan")
        try:
            row["error_per_pixel"] = float(str(iteration.get("FehlerProPixel", "")).strip().replace(",", "."))
        except ValueError:
            row["error_per_pixel"] = float("nan")

        if not image_path or not os.path.exists(image_path) or not os.path.exists(svg_path):
            metrics.append(row)
            continue

        img_orig = cv2_module.imread(image_path)
        if img_orig is None:
            metrics.append(row)
            continue
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
        rendered = render_svg_to_numpy_fn(svg_content, img_orig.shape[1], img_orig.shape[0])
        if rendered is None:
            metrics.append(row)
            continue

        diff = img_orig.astype(np_module.float32) - rendered.astype(np_module.float32)
        delta2 = np_module.sum(diff * diff, axis=2)
        row["pixel_count"] = int(delta2.shape[0] * delta2.shape[1])
        row["total_delta2"] = float(np_module.sum(delta2))
        row["mean_delta2"] = float(np_module.mean(delta2))
        row["std_delta2"] = float(np_module.std(delta2))
        metrics.append(row)

    metrics.sort(key=lambda item: str(item.get("variant", "")))
    return metrics
