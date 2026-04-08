"""Conversion execution helpers used by the range pipeline."""

from __future__ import annotations

import os


def convertOneImpl(
    *,
    filename: str,
    folder_path: str,
    csv_path: str,
    iteration_budget: int,
    badge_rounds: int,
    svg_out_dir: str,
    diff_out_dir: str,
    reports_out_dir: str,
    debug_ac0811_dir: str | None,
    debug_element_diff_dir: str | None,
    run_iteration_pipeline_fn,
    read_validation_log_details_fn,
    render_svg_to_numpy_fn,
    calculate_delta2_stats_fn,
    get_base_name_from_file_fn,
    cv2_module,
    append_batch_failure_fn,
    print_fn=print,
) -> tuple[dict[str, object] | None, bool]:
    image_path = os.path.join(folder_path, filename)
    base = os.path.splitext(filename)[0]
    log_file = os.path.join(reports_out_dir, f"{base}_element_validation.log")
    try:
        res = run_iteration_pipeline_fn(
            image_path,
            csv_path,
            max(1, int(iteration_budget)),
            svg_out_dir,
            diff_out_dir,
            reports_out_dir,
            debug_ac0811_dir,
            debug_element_diff_dir,
            badge_validation_rounds=max(1, int(badge_rounds)),
        )
    except Exception as exc:  # noqa: BLE001 - keeps batch execution resilient per image.
        append_batch_failure_fn(
            {
                "filename": filename,
                "status": "batch_error",
                "reason": type(exc).__name__,
                "details": str(exc),
                "log_file": os.path.basename(log_file),
            }
        )
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"status=batch_error\nfilename={filename}\nreason={type(exc).__name__}\ndetails={exc}\n")
        print_fn(f"[WARN] {filename}: Batchlauf setzt nach Fehler fort ({type(exc).__name__}: {exc})")
        return None, True
    if not res:
        details = read_validation_log_details_fn(log_file)
        status = details.get("status", "")
        if status in {"render_failure", "batch_error"}:
            append_batch_failure_fn(
                {
                    "filename": filename,
                    "status": status,
                    "reason": details.get("failure_reason", details.get("reason", "unknown")),
                    "details": details.get("params_snapshot", details.get("details", "")),
                    "log_file": os.path.basename(log_file),
                }
            )
            print_fn(f"[WARN] {filename}: Fehler protokolliert, Batchlauf wird fortgesetzt ({status}).")
            return None, True
        if status == "semantic_mismatch":
            append_batch_failure_fn(
                {
                    "filename": filename,
                    "status": status,
                    "reason": "semantic_mismatch",
                    "details": details.get("issue", ""),
                    "log_file": os.path.basename(log_file),
                }
            )
            print_fn(f"[WARN] {filename}: Semantischer Fehlmatch, Batchlauf stoppt nach diesem Fehler.")
            return None, True
        return None, False

    _base, _desc, params, best_iter, best_error = res
    details = read_validation_log_details_fn(log_file)
    img = cv2_module.imread(image_path)
    pixel_count = 1.0
    width = 0
    height = 0
    mean_delta2 = float("inf")
    std_delta2 = float("inf")
    if img is not None:
        height, width = img.shape[:2]
        pixel_count = float(max(1, width * height))
        svg_path = os.path.join(svg_out_dir, f"{os.path.splitext(filename)[0]}.svg")
        if os.path.exists(svg_path):
            try:
                with open(svg_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()
            except OSError:
                svg_content = ""
            if svg_content:
                rendered = render_svg_to_numpy_fn(svg_content, width, height)
                mean_delta2, std_delta2 = calculate_delta2_stats_fn(img, rendered)

    return {
        "filename": filename,
        "params": params,
        "best_iter": int(best_iter),
        "best_error": float(best_error),
        "convergence": str(details.get("convergence", "")).strip().lower(),
        "error_per_pixel": float(best_error) / pixel_count,
        "mean_delta2": float(mean_delta2),
        "std_delta2": float(std_delta2),
        "w": int(width),
        "h": int(height),
        "base": get_base_name_from_file_fn(os.path.splitext(filename)[0]).upper(),
        "variant": os.path.splitext(filename)[0].upper(),
    }, False
