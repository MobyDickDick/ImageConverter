"""Conversion execution helpers used by the range pipeline."""

from __future__ import annotations

import json
import os
import re
import signal
from contextlib import contextmanager

_ONE_BY_ONE_TRANSPARENT_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc`\x00\x02\x00\x00\x05\x00\x01"
    b"z^\xab?\x00\x00\x00\x00IEND\xaeB`\x82"
)


@contextmanager
def _wallClockTimeout(timeout_sec: float | int | None):
    """Raise ``TimeoutError`` when a block exceeds ``timeout_sec`` on Unix hosts."""
    if timeout_sec is None:
        yield
        return
    timeout_value = float(timeout_sec)
    if timeout_value <= 0:
        yield
        return
    if not hasattr(signal, "setitimer"):
        yield
        return
    previous_handler = signal.getsignal(signal.SIGALRM)

    def _raise_timeout(_signum, _frame):  # pragma: no cover - signal callback.
        raise TimeoutError(f"Conversion exceeded wall-clock timeout ({timeout_value:.1f}s).")

    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_value)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)


def _ensureOutputArtifacts(
    *,
    svg_path: str,
    diff_path: str,
    create_svg_fallback: bool = True,
) -> None:
    if create_svg_fallback and not os.path.exists(svg_path):
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


def _ensureEmbeddedSvgAtPath(
    *,
    svg_path: str,
    image_path: str,
    render_embedded_raster_svg_fn,
    print_fn=print,
) -> bool:
    if os.path.exists(svg_path) and not _svgIsTrivialFallbackArtifact(svg_path):
        return True
    try:
        svg_content = render_embedded_raster_svg_fn(image_path)
    except Exception as exc:  # noqa: BLE001 - skipped variants must not break the batch flow.
        print_fn(f"[WARN] {os.path.basename(image_path)}: Konnte Embedded-SVG für Skip-Status nicht erzeugen ({type(exc).__name__}: {exc})")
        return False
    try:
        with open(svg_path, "w", encoding="utf-8") as svg_file:
            svg_file.write(svg_content)
        return True
    except OSError as exc:
        print_fn(f"[WARN] {os.path.basename(image_path)}: Konnte Embedded-SVG für Skip-Status nicht schreiben ({type(exc).__name__}: {exc})")
        return False


def _resolveFailureSvgPath(default_svg_path: str, failed_svg_path: str | None) -> str:
    """Use canonical failed SVG path when a failed artifact already exists."""
    if failed_svg_path and os.path.exists(failed_svg_path):
        return failed_svg_path
    return default_svg_path


def _normalizeSvgToFailedPrefixIfRasterArtifact(
    *,
    svg_out_dir: str,
    base_name: str,
    svg_path: str,
) -> str:
    """Rename ``<variant>.svg`` to ``Failed_<variant>.svg`` when SVG is raster-only/trivial."""
    failed_svg_path = os.path.join(svg_out_dir, f"Failed_{base_name}.svg")
    has_svg = os.path.exists(svg_path)
    should_use_failed_name = has_svg and (
        _svgContainsEmbeddedRasterArtifact(svg_path) or _svgIsTrivialFallbackArtifact(svg_path)
    )
    if should_use_failed_name and svg_path != failed_svg_path:
        if os.path.exists(failed_svg_path):
            os.unlink(failed_svg_path)
        os.rename(svg_path, failed_svg_path)
        return failed_svg_path
    return svg_path


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


def _svgContainsEmbeddedRasterArtifact(svg_path: str) -> bool:
    try:
        with open(svg_path, "r", encoding="utf-8") as svg_file:
            content = svg_file.read().lower()
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


def _svgIsTrivialFallbackArtifact(svg_path: str) -> bool:
    try:
        with open(svg_path, "r", encoding="utf-8") as svg_file:
            content = svg_file.read().lower()
    except OSError:
        return False

    compact = re.sub(r"\s+", "", content)
    has_minimal_canvas = 'width="1"' in compact and 'height="1"' in compact and "viewbox=\"0011\"" in compact
    has_white_rect = "<rect" in compact and "fill='#ffffff'" in compact and "width='100%'" in compact and "height='100%'" in compact
    return has_minimal_canvas and has_white_rect


def _safeReadTextFile(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def _emitVariantDebugDump(
    *,
    debug_root_dir: str | None,
    base_name: str,
    variant: str,
    stage: str,
    payload: dict[str, object],
    print_fn=print,
) -> None:
    if not debug_root_dir:
        return
    if str(base_name).upper() != "AC0811":
        return
    variant_name = str(variant).upper()
    debug_dir = os.path.join(debug_root_dir, variant_name)
    os.makedirs(debug_dir, exist_ok=True)
    dump_path = os.path.join(debug_dir, f"{variant_name}_conversion_debug.json")
    data = dict(payload)
    data.setdefault("variant", variant_name)
    data.setdefault("base_name", str(base_name).upper())
    data.setdefault("stage", stage)
    try:
        with open(dump_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
    except OSError as exc:
        print_fn(f"[WARN] {variant_name}: Debug-Dump konnte nicht geschrieben werden ({type(exc).__name__}: {exc})")


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
    run_timeout_sec: float | int | None = None,
    print_fn=print,
) -> tuple[dict[str, object] | None, bool]:
    image_path = os.path.join(folder_path, filename)
    base = os.path.splitext(filename)[0]
    base_name = str(get_base_name_from_file_fn(base)).upper()
    svg_path = os.path.join(svg_out_dir, f"{base}.svg")
    diff_path = os.path.join(diff_out_dir, f"{base}_diff.png")
    log_file = os.path.join(reports_out_dir, f"{base}_element_validation.log")
    current_test_id = str(os.environ.get("PYTEST_CURRENT_TEST", ""))
    anchor_test_active = "test_ac08_semantic_anchor_variants_convert_without_failed_svg" in current_test_id
    attempt_idx = int(os.environ.get("ICC_ANCHOR_ATTEMPT_IDX", "1") or "1")

    def _emit_anchor_variant_event(event: str, **fields: object) -> None:
        if not anchor_test_active:
            return
        extras = " ".join(f"{key}={value}" for key, value in fields.items())
        suffix = f" {extras}" if extras else ""
        print_fn(f"[ANCHOR_DEBUG] {event} name={base}{suffix}")

    if anchor_test_active:
        _emit_anchor_variant_event("variant_start", attempt_idx=attempt_idx)
    try:
        with _wallClockTimeout(run_timeout_sec):
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
        _emitVariantDebugDump(
            debug_root_dir=debug_ac0811_dir,
            base_name=base_name,
            variant=base,
            stage="exception",
            payload={
                "filename": filename,
                "image_path": image_path,
                "log_file": log_file,
                "run_timeout_sec": float(run_timeout_sec or 0.0),
                "iteration_budget": int(iteration_budget),
                "badge_rounds": int(badge_rounds),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "validation_log_text": _safeReadTextFile(log_file),
            },
            print_fn=print_fn,
        )
        _ensureOutputArtifacts(
            svg_path=_resolveFailureSvgPath(svg_path, failed_svg_path),
            diff_path=diff_path,
        )
        print_fn(f"[WARN] {filename}: Batchlauf setzt nach Fehler fort ({type(exc).__name__}: {exc})")
        _emit_anchor_variant_event("variant_done", status="exception", reason=type(exc).__name__)
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
            _ensureOutputArtifacts(
                svg_path=_resolveFailureSvgPath(svg_path, failed_svg_path),
                diff_path=diff_path,
            )
            print_fn(f"[WARN] {filename}: Fehler protokolliert, Batchlauf wird fortgesetzt ({status}).")
            _emit_anchor_variant_event("variant_done", status=status or "render_failure")
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
            _ensureOutputArtifacts(
                svg_path=_resolveFailureSvgPath(svg_path, failed_svg_path),
                diff_path=diff_path,
            )
            print_fn(f"[WARN] {filename}: Semantischer Fehlmatch, Batchlauf stoppt nach diesem Fehler.")
            _emit_anchor_variant_event("variant_done", status="semantic_mismatch")
            return None, True
        if status.startswith("skipped_"):
            _ensureEmbeddedSvgAtPath(
                svg_path=svg_path,
                image_path=image_path,
                render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
                print_fn=print_fn,
            )
            svg_path = _normalizeSvgToFailedPrefixIfRasterArtifact(
                svg_out_dir=svg_out_dir,
                base_name=base,
                svg_path=svg_path,
            )
            _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path, create_svg_fallback=False)
            _emit_anchor_variant_event("variant_done", status=status)
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
        _ensureOutputArtifacts(
            svg_path=_resolveFailureSvgPath(svg_path, failed_svg_path),
            diff_path=diff_path,
        )
        print_fn(f"[WARN] {filename}: Kein verwertbares Konvertierungsergebnis, als Fehler protokolliert ({failure_status}).")
        _emitVariantDebugDump(
            debug_root_dir=debug_ac0811_dir,
            base_name=base_name,
            variant=base,
            stage="no_result",
            payload={
                "filename": filename,
                "image_path": image_path,
                "log_file": log_file,
                "status": failure_status,
                "reason": failure_reason,
                "validation_details": details,
                "validation_log_text": _safeReadTextFile(log_file),
            },
            print_fn=print_fn,
        )
        _emit_anchor_variant_event("variant_done", status=failure_status)
        return None, True

    _base, _desc, params, best_iter, best_error = res
    details = read_validation_log_details_fn(log_file)
    status = str(details.get("status", ""))
    if status.startswith("skipped_"):
        _ensureEmbeddedSvgAtPath(
            svg_path=svg_path,
            image_path=image_path,
            render_embedded_raster_svg_fn=render_embedded_raster_svg_fn,
            print_fn=print_fn,
        )
        svg_path = _normalizeSvgToFailedPrefixIfRasterArtifact(
            svg_out_dir=svg_out_dir,
            base_name=base,
            svg_path=svg_path,
        )
        _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path, create_svg_fallback=False)
        _emit_anchor_variant_event("variant_done", status=status)
        return None, False
    svg_path = _normalizeSvgToFailedPrefixIfRasterArtifact(
        svg_out_dir=svg_out_dir,
        base_name=base,
        svg_path=svg_path,
    )
    if _svgIsTrivialFallbackArtifact(svg_path):
        append_batch_failure_fn(
            {
                "filename": filename,
                "status": "poor_conversion_placeholder_svg",
                "reason": "trivial_placeholder_svg",
                "details": "Detected 1x1 white placeholder SVG output.",
                "log_file": os.path.basename(log_file),
                "failed_svg": os.path.basename(svg_path),
            }
        )
        _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path)
        print_fn(f"[WARN] {filename}: Triviale 1x1-Placeholder-SVG erkannt, als fehlgeschlagen markiert.")
        _emit_anchor_variant_event("variant_done", status="poor_conversion_placeholder_svg")
        return None, True
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
    row = {
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
        "base": base_name,
        "variant": os.path.splitext(filename)[0].upper(),
    }
    _emitVariantDebugDump(
        debug_root_dir=debug_ac0811_dir,
        base_name=base_name,
        variant=base,
        stage="success",
        payload={
            "filename": filename,
            "image_path": image_path,
            "svg_path": svg_path,
            "diff_path": diff_path,
            "log_file": log_file,
            "status": status,
            "convergence": str(details.get("convergence", "")).strip().lower(),
            "iteration_budget": int(iteration_budget),
            "badge_rounds": int(badge_rounds),
            "best_iter": int(best_iter),
            "best_error": float(best_error),
            "result_row": row,
            "validation_details": details,
            "validation_log_text": _safeReadTextFile(log_file),
        },
        print_fn=print_fn,
    )
    _emit_anchor_variant_event("variant_done", status="ok")
    return row, False
