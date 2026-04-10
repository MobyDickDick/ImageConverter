"""Conversion execution helpers used by the range pipeline."""

from __future__ import annotations

import os

_ONE_BY_ONE_TRANSPARENT_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc`\x00\x02\x00\x00\x05\x00\x01"
    b"z^\xab?\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _ensureOutputArtifacts(
    *,
    svg_path: str,
    diff_path: str,
) -> None:
    if not os.path.exists(svg_path):
        width = 1
        height = 1
        svg_fallback = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            "<rect width='100%' height='100%' fill='#ffffff'/></svg>"
        )
        with open(svg_path, "w", encoding="utf-8") as svg_file:
            svg_file.write(svg_fallback)
    if not os.path.exists(diff_path):
        with open(diff_path, "wb") as diff_file:
            diff_file.write(_ONE_BY_ONE_TRANSPARENT_PNG)


def _writeFailedEmbeddedSvgArtifact(
    *,
    svg_out_dir: str,
    filename: str,
    image_path: str,
    render_embedded_raster_svg_fn,
    print_fn=print,
) -> str | None:
    base = os.path.splitext(filename)[0]
    failed_svg_path = os.path.join(svg_out_dir, f"Failed_{base}.svg")
    try:
        svg_content = render_embedded_raster_svg_fn(image_path)
        with open(failed_svg_path, "w", encoding="utf-8") as failed_svg_file:
            failed_svg_file.write(svg_content)
        return failed_svg_path
    except Exception as exc:  # noqa: BLE001 - must not break batch flow when fallback artifact fails.
        print_fn(f"[WARN] {filename}: Konnte Failed-Embedded-SVG nicht schreiben ({type(exc).__name__}: {exc})")
        return None


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
    render_embedded_raster_svg_fn,
    append_batch_failure_fn,
    print_fn=print,
) -> tuple[dict[str, object] | None, bool]:
    image_path = os.path.join(folder_path, filename)
    base = os.path.splitext(filename)[0]
    svg_path = os.path.join(svg_out_dir, f"{base}.svg")
    diff_path = os.path.join(diff_out_dir, f"{base}_diff.png")
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
        failed_svg_path = _writeFailedEmbeddedSvgArtifact(
            svg_out_dir=svg_out_dir,
            filename=filename,
            image_path=image_path,
            render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
            print_fn=print_fn,
        )
        append_batch_failure_fn(
            {
                "filename": filename,
                "status": "batch_error",
                "reason": type(exc).__name__,
                "details": str(exc),
                "log_file": os.path.basename(log_file),
                "failed_svg": os.path.basename(failed_svg_path) if failed_svg_path else "",
            }
        )
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"status=batch_error\nfilename={filename}\nreason={type(exc).__name__}\ndetails={exc}\n")
        _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path)
        print_fn(f"[WARN] {filename}: Batchlauf setzt nach Fehler fort ({type(exc).__name__}: {exc})")
        return None, True
    if not res:
        details = read_validation_log_details_fn(log_file)
        status = details.get("status", "")
        if status in {"render_failure", "batch_error"}:
            failed_svg_path = _writeFailedEmbeddedSvgArtifact(
                svg_out_dir=svg_out_dir,
                filename=filename,
                image_path=image_path,
                render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
                print_fn=print_fn,
            )
            append_batch_failure_fn(
                {
                    "filename": filename,
                    "status": status,
                    "reason": details.get("failure_reason", details.get("reason", "unknown")),
                    "details": details.get("params_snapshot", details.get("details", "")),
                    "log_file": os.path.basename(log_file),
                    "failed_svg": os.path.basename(failed_svg_path) if failed_svg_path else "",
                }
            )
            _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path)
            print_fn(f"[WARN] {filename}: Fehler protokolliert, Batchlauf wird fortgesetzt ({status}).")
            return None, True
        if status == "semantic_mismatch":
            failed_svg_path = _writeFailedEmbeddedSvgArtifact(
                svg_out_dir=svg_out_dir,
                filename=filename,
                image_path=image_path,
                render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
                print_fn=print_fn,
            )
            append_batch_failure_fn(
                {
                    "filename": filename,
                    "status": status,
                    "reason": "semantic_mismatch",
                    "details": details.get("issue", ""),
                    "log_file": os.path.basename(log_file),
                    "failed_svg": os.path.basename(failed_svg_path) if failed_svg_path else "",
                }
            )
            _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path)
            print_fn(f"[WARN] {filename}: Semantischer Fehlmatch, Batchlauf stoppt nach diesem Fehler.")
            return None, True
        if status.startswith("skipped_"):
            _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path)
            return None, False

        failed_svg_path = _writeFailedEmbeddedSvgArtifact(
            svg_out_dir=svg_out_dir,
            filename=filename,
            image_path=image_path,
            render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
            print_fn=print_fn,
        )
        failure_status = status or "conversion_failed"
        failure_reason = details.get("failure_reason", details.get("reason", "no_result"))
        append_batch_failure_fn(
            {
                "filename": filename,
                "status": failure_status,
                "reason": failure_reason,
                "details": details.get("issue", details.get("details", "")),
                "log_file": os.path.basename(log_file),
                "failed_svg": os.path.basename(failed_svg_path) if failed_svg_path else "",
            }
        )
        if not os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(
                    f"status={failure_status}\n"
                    f"filename={filename}\n"
                    f"reason={failure_reason}\n"
                    "details=no_result_returned\n"
                )
        _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path)
        print_fn(f"[WARN] {filename}: Kein verwertbares Konvertierungsergebnis, als Fehler protokolliert ({failure_status}).")
        return None, True

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
        if os.path.exists(svg_path):
            try:
                with open(svg_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()
            except OSError:
                svg_content = ""
            if svg_content:
                rendered = render_svg_to_numpy_fn(svg_content, width, height)
                mean_delta2, std_delta2 = calculate_delta2_stats_fn(img, rendered)
    _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path)

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
