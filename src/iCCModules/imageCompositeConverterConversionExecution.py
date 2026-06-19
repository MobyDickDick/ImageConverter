"""Conversion execution helpers used by the range pipeline."""

from __future__ import annotations

import json
import math
import os
import re
import signal
import shutil
import time
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
    create_diff_fallback: bool = True,
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
    if create_diff_fallback and not os.path.exists(diff_path):
        with open(diff_path, "wb") as diff_file:
            diff_file.write(_ONE_BY_ONE_TRANSPARENT_PNG)


def _deleteDiffIfPresent(diff_path: str) -> None:
    if os.path.exists(diff_path):
        os.unlink(diff_path)


def _isMeaningfulDiffArtifact(diff_path: str, cv2_module) -> bool:
    if not os.path.exists(diff_path):
        return False
    try:
        with open(diff_path, "rb") as handle:
            if handle.read() == _ONE_BY_ONE_TRANSPARENT_PNG:
                return False
    except OSError:
        return False
    imread_flag = getattr(cv2_module, "IMREAD_UNCHANGED", None)
    try:
        img = cv2_module.imread(diff_path, imread_flag) if imread_flag is not None else cv2_module.imread(diff_path)
    except TypeError:
        img = cv2_module.imread(diff_path)
    if img is None:
        return False
    try:
        return bool((img != 0).any())
    except Exception:
        return True


def _svgQualityScore(
    *,
    image_path: str,
    svg_path: str,
    cv2_module,
    render_svg_to_numpy_fn,
    calculate_delta2_stats_fn,
    calculate_spatial_delta2_quality_fn=None,
) -> float:
    if not os.path.exists(svg_path):
        return float("inf")
    img = cv2_module.imread(image_path)
    if img is None:
        return float("inf")
    try:
        with open(svg_path, "r", encoding="utf-8") as handle:
            svg_content = handle.read()
    except OSError:
        return float("inf")
    if not svg_content.strip():
        return float("inf")
    height, width = img.shape[:2]
    rendered = render_svg_to_numpy_fn(svg_content, width, height)
    if calculate_spatial_delta2_quality_fn is not None:
        metrics = calculate_spatial_delta2_quality_fn(img, rendered)
        raw_score = metrics.get("spatial_quality_score", float("inf"))
    else:
        mean_delta2, _std_delta2 = calculate_delta2_stats_fn(img, rendered)
        raw_score = mean_delta2
    try:
        score = float(raw_score)
    except (TypeError, ValueError):
        return float("inf")
    return score if math.isfinite(score) else float("inf")




def _resolveSampleSvgPath(*, sample_svg_path: str, folder_path: str, reports_out_dir: str) -> str:
    candidate = str(sample_svg_path or '').strip()
    if not candidate:
        return ''
    probe_paths = [candidate]
    if not os.path.isabs(candidate):
        probe_paths.extend([
            os.path.abspath(candidate),
            os.path.abspath(os.path.join(folder_path, candidate)),
            os.path.abspath(os.path.join(os.path.dirname(folder_path), candidate)),
            os.path.abspath(os.path.join(reports_out_dir, candidate)),
            os.path.abspath(os.path.join(os.path.dirname(reports_out_dir), candidate)),
        ])
        normalized = candidate.replace("\\", "/")
        marker = "/samples/"
        if marker in normalized:
            sample_tail = normalized.split(marker, 1)[1].lstrip("/")
            probe_paths.append(os.path.abspath(os.path.join(folder_path, "samples", sample_tail)))
    for probe in probe_paths:
        if probe and os.path.exists(probe):
            return probe
    return ''

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
    if os.path.exists(failed_svg_path):
        try:
            os.unlink(failed_svg_path)
        except OSError:
            pass
    try:
        svg_content = render_embedded_raster_svg_fn(image_path)
    except Exception as exc:  # noqa: BLE001 - failure artifact should not break batch flow.
        print_fn(
            f"[WARN] {filename}: Konnte Failed-Embedded-SVG nicht erzeugen ({type(exc).__name__}: {exc})"
        )
        return None
    try:
        with open(failed_svg_path, "w", encoding="utf-8") as svg_file:
            svg_file.write(svg_content)
    except OSError as exc:
        print_fn(f"[WARN] {filename}: Konnte Failed-SVG nicht schreiben ({type(exc).__name__}: {exc})")
        return None
    return failed_svg_path


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


def _formatFailureTelemetry(details: dict[str, object] | None) -> str:
    if not details:
        return ""
    telemetry_keys = (
        "best_error",
        "error_per_pixel",
        "mean_delta2",
        "std_delta2",
        "best_iter",
        "last_iter",
        "params_snapshot",
    )
    parts: list[str] = []
    for key in telemetry_keys:
        raw = details.get(key)
        if raw is None:
            continue
        value = str(raw).strip()
        if not value:
            continue
        parts.append(f"{key}={value}")
    return "; ".join(parts)


def _formatCompactParams(params: object, *, max_items: int = 14, max_chars: int = 240) -> str:
    """Render only useful scalar conversion parameters as a short summary."""
    if not isinstance(params, dict) or not params:
        return "keine"

    priority = (
        "mode", "cx", "cy", "r", "stem_x", "stem_width", "stem_top", "stem_bottom",
        "arm_x1", "arm_y1", "arm_x2", "arm_y2", "arm_stroke", "text_mode",
        "text_scale", "co2_font_scale", "voc_scale",
    )
    excluded_fragments = ("description", "contract", "audit", "fragment", "semantic", "log", "reason", "status")

    def _is_useful(key: str, value: object) -> bool:
        return (
            value is not None
            and isinstance(value, (str, int, float, bool))
            and not any(fragment in key.lower() for fragment in excluded_fragments)
        )

    ordered_keys = [key for key in priority if key in params]
    ordered_keys.extend(sorted(str(key) for key in params if str(key) not in ordered_keys))
    parts: list[str] = []
    for key in ordered_keys:
        value = params.get(key)
        if not _is_useful(key, value):
            continue
        if isinstance(value, float):
            rendered_value = f"{value:.3f}"
        else:
            rendered_value = str(value)
        candidate = f"{key}={rendered_value}"
        if len(parts) >= max_items or len(", ".join([*parts, candidate])) > max_chars:
            parts.append("…")
            break
        parts.append(candidate)
    return ", ".join(parts) if parts else "keine skalaren Parameter"


def _formatQualityValue(value: object) -> str:
    """Format a quality metric compactly while preserving unavailable values."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if not math.isfinite(numeric):
        return "n/a"
    return f"{numeric:.6f}"


def _formatFailureTelemetryJson(details: dict[str, object] | None) -> str:
    if not details:
        return ""
    telemetry_keys = (
        "best_error",
        "error_per_pixel",
        "mean_delta2",
        "std_delta2",
        "best_iter",
        "last_iter",
        "params_snapshot",
    )
    payload: dict[str, str] = {}
    for key in telemetry_keys:
        raw = details.get(key)
        if raw is None:
            continue
        value = str(raw).strip()
        if not value:
            continue
        payload[key] = value
    if not payload:
        return ""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    png_out_dir: str,
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
    calculate_spatial_delta2_quality_fn=None,
) -> tuple[dict[str, object] | None, bool]:
    image_path = os.path.join(folder_path, filename)
    base = os.path.splitext(filename)[0]
    base_name = str(get_base_name_from_file_fn(base)).upper()
    svg_path = os.path.join(svg_out_dir, f"{base}.svg")
    diff_path = os.path.join(diff_out_dir, f"{base}_diff.png")
    previous_svg_content = _safeReadTextFile(svg_path) if os.path.exists(svg_path) else ""
    _deleteDiffIfPresent(diff_path)
    log_file = os.path.join(reports_out_dir, f"{base}_element_validation.log")
    current_test_id = str(os.environ.get("PYTEST_CURRENT_TEST", ""))
    anchor_test_active = "test_ac08_semantic_anchor_variants_convert_without_failed_svg" in current_test_id
    attempt_idx = int(os.environ.get("ICC_ANCHOR_ATTEMPT_IDX", "1") or "1")

    def _emit_anchor_variant_event(event: str, **fields: object) -> None:
        if not anchor_test_active:
            return
        run_context = str(os.environ.get("ICC_ANCHOR_RUN_CONTEXT", "") or "").strip()
        if run_context:
            fields.setdefault("context", run_context)
        extras = " ".join(f"{key}={value}" for key, value in fields.items())
        suffix = f" {extras}" if extras else ""
        print_fn(f"[ANCHOR_DEBUG] {event} name={base}{suffix}")

    if anchor_test_active:
        _emit_anchor_variant_event("variant_start", attempt_idx=attempt_idx)
    started_at = time.monotonic()
    print_fn(
        f"[INFO] Konvertiere {filename} | "
        f"Parameter: Iterationen={max(1, int(iteration_budget))}, "
        f"Validierungsrunden={max(1, int(badge_rounds))}"
    )
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
        details = read_validation_log_details_fn(log_file) if os.path.exists(log_file) else {}
        failure_telemetry = _formatFailureTelemetry(details)
        failure_telemetry_json = _formatFailureTelemetryJson(details)
        append_batch_failure_fn(
            {
                "filename": filename,
                "status": "batch_error",
                "reason": type(exc).__name__,
                "details": failure_telemetry_json or failure_telemetry or str(exc),
                "log_file": os.path.basename(log_file),
                "failed_svg": os.path.basename(failed_svg_path) if failed_svg_path else "",
            }
        )
        prior_log_text = _safeReadTextFile(log_file) if os.path.exists(log_file) else ""
        with open(log_file, "w", encoding="utf-8") as f:
            if prior_log_text:
                f.write(prior_log_text.rstrip() + "\n")
            f.write(f"status=batch_error\nfilename={filename}\nreason={type(exc).__name__}\ndetails={exc}\n")
            if failure_telemetry:
                f.write(f"failure_telemetry={failure_telemetry}\n")
            if failure_telemetry_json:
                f.write(f"failure_telemetry_json={failure_telemetry_json}\n")
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
                "failure_telemetry": failure_telemetry,
                "failure_telemetry_json": failure_telemetry_json,
                "validation_log_text": _safeReadTextFile(log_file),
            },
            print_fn=print_fn,
        )
        _ensureOutputArtifacts(
            svg_path=_resolveFailureSvgPath(svg_path, failed_svg_path),
            diff_path=diff_path,
            create_svg_fallback=False,
        )
        telemetry_suffix = f" | telemetry: {failure_telemetry}" if failure_telemetry else ""
        print_fn(f"[WARN] {filename}: Batchlauf setzt nach Fehler fort ({type(exc).__name__}: {exc}){telemetry_suffix}")
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
                create_svg_fallback=False,
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
                create_svg_fallback=False,
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
            _deleteDiffIfPresent(diff_path)
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
            create_svg_fallback=False,
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
    if status in {"non_composite_plan_b_sample_svg_selected", "non_composite_pure_svg_placeholder"}:
        print_fn(
            f"[WARN] {filename}: Keine echte Konvertierung; "
            "verwende Plan-B/Sample-SVG als Platzhalter."
        )
        sample_svg_path = _resolveSampleSvgPath(
            sample_svg_path=str(details.get("sample_svg_path", "")),
            folder_path=folder_path,
            reports_out_dir=reports_out_dir,
        )
        if not sample_svg_path:
            implicit_sample_svg = os.path.join(folder_path, "samples", f"{_base}.svg")
            if os.path.exists(implicit_sample_svg):
                sample_svg_path = implicit_sample_svg
        if not sample_svg_path:
            candidate_svg_path = os.path.join(svg_out_dir, f"{_base}.svg")
            if os.path.exists(candidate_svg_path):
                sample_svg_path = candidate_svg_path
        if sample_svg_path:
            try:
                shutil.copyfile(sample_svg_path, svg_path)
                failed_svg_path = os.path.join(svg_out_dir, f"Failed_{base}.svg")
                if os.path.exists(failed_svg_path):
                    os.unlink(failed_svg_path)
                reports_failed_svg_path = os.path.join(reports_out_dir, "converted_svgs", f"Failed_{base}.svg")
                if os.path.exists(reports_failed_svg_path):
                    os.unlink(reports_failed_svg_path)
            except OSError:
                pass
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
        _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path, create_svg_fallback=False, create_diff_fallback=False)
        _emit_anchor_variant_event("variant_done", status=status)
        return None, False
    svg_path = _normalizeSvgToFailedPrefixIfRasterArtifact(
        svg_out_dir=svg_out_dir,
        base_name=base,
        svg_path=svg_path,
    )
    if _svgContainsEmbeddedRasterArtifact(svg_path):
        append_batch_failure_fn(
            {
                "filename": filename,
                "status": "raster_embedded_svg",
                "reason": "embedded_raster_detected",
                "details": "Detected embedded raster payload in SVG output.",
                "log_file": os.path.basename(log_file),
                "failed_svg": os.path.basename(svg_path),
            }
        )
        _deleteDiffIfPresent(diff_path)
        print_fn(f"[ERROR] {filename}: Embedded-Raster-SVG erkannt, als fehlgeschlagen markiert.")
        _emit_anchor_variant_event("variant_done", status="raster_embedded_svg")
        return None, True
    if _svgIsTrivialFallbackArtifact(svg_path):
        svg_path = _normalizeSvgToFailedPrefixIfRasterArtifact(
            svg_out_dir=svg_out_dir,
            base_name=base,
            svg_path=svg_path,
        )
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
        _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path, create_svg_fallback=False, create_diff_fallback=False)
        print_fn(f"[WARN] {filename}: Triviale 1x1-Placeholder-SVG erkannt, als fehlgeschlagen markiert.")
        _emit_anchor_variant_event("variant_done", status="poor_conversion_placeholder_svg")
        return None, True

    if previous_svg_content.strip():
        previous_svg_path = os.path.join(svg_out_dir, f"{base}.__previous__.svg")
        try:
            with open(previous_svg_path, "w", encoding="utf-8") as handle:
                handle.write(previous_svg_content)
            previous_quality = _svgQualityScore(
                image_path=image_path,
                svg_path=previous_svg_path,
                cv2_module=cv2_module,
                render_svg_to_numpy_fn=render_svg_to_numpy_fn,
                calculate_delta2_stats_fn=calculate_delta2_stats_fn,
                calculate_spatial_delta2_quality_fn=calculate_spatial_delta2_quality_fn,
            )
        finally:
            if os.path.exists(previous_svg_path):
                os.unlink(previous_svg_path)
        new_quality = _svgQualityScore(
            image_path=image_path,
            svg_path=svg_path,
            cv2_module=cv2_module,
            render_svg_to_numpy_fn=render_svg_to_numpy_fn,
            calculate_delta2_stats_fn=calculate_delta2_stats_fn,
            calculate_spatial_delta2_quality_fn=calculate_spatial_delta2_quality_fn,
        )
        new_is_better = new_quality < previous_quality
        previous_contains_embedded_raster = "data:image/" in previous_svg_content.lower()
        new_contains_embedded_raster = _svgContainsEmbeddedRasterArtifact(svg_path)
        new_svg_content = _safeReadTextFile(svg_path)
        semantic_shape_upgrade = (
            "_square_cross" in new_svg_content
            and "_square_cross" not in previous_svg_content
        )
        if (previous_contains_embedded_raster and not new_contains_embedded_raster) or semantic_shape_upgrade:
            new_is_better = True
        if not new_is_better:
            # A quality retry must never erase the usable result from the
            # preceding pass.  The previous implementation treated a high
            # mean-delta2 baseline as a hard failure and deleted it whenever a
            # retry was not better.  This left families such as AC0224 without
            # their M/S outputs even though the initial conversion succeeded.
            with open(svg_path, "w", encoding="utf-8") as handle:
                handle.write(previous_svg_content)
    img = cv2_module.imread(image_path)
    pixel_count = 1.0
    width = 0
    height = 0
    mean_delta2 = float("inf")
    std_delta2 = float("inf")
    tile_std_delta2 = float("inf")
    localized_error_fraction = float("inf")
    spatial_quality_score = float("inf")
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
                if calculate_spatial_delta2_quality_fn is not None:
                    spatial_metrics = calculate_spatial_delta2_quality_fn(img, rendered)
                    tile_std_delta2 = float(spatial_metrics.get("tile_std_delta2", float("inf")))
                    localized_error_fraction = float(
                        spatial_metrics.get("localized_error_fraction", float("inf"))
                    )
                    spatial_quality_score = float(
                        spatial_metrics.get("spatial_quality_score", float("inf"))
                    )
    if not _isMeaningfulDiffArtifact(diff_path, cv2_module):
        _deleteDiffIfPresent(diff_path)
    _ensureOutputArtifacts(svg_path=svg_path, diff_path=diff_path, create_svg_fallback=True, create_diff_fallback=False)
    elapsed_sec = max(0.0, time.monotonic() - started_at)
    try:
        actual_iterations = int(details.get("actual_iterations", iteration_budget))
    except (TypeError, ValueError):
        actual_iterations = int(iteration_budget)
    row = {
        "filename": filename,
        "params": params,
        "best_iter": int(best_iter),
        "requested_iterations": int(iteration_budget),
        "actual_iterations": max(0, actual_iterations),
        "elapsed_seconds": float(elapsed_sec),
        "best_error": float(best_error),
        "convergence": str(details.get("convergence", "")).strip().lower(),
        "error_per_pixel": float(best_error) / pixel_count,
        "mean_delta2": float(mean_delta2),
        "std_delta2": float(std_delta2),
        "tile_std_delta2": float(tile_std_delta2),
        "localized_error_fraction": float(localized_error_fraction),
        "spatial_quality_score": float(spatial_quality_score),
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
    spatial_quality_text = (
        f"Raumscore={_formatQualityValue(row['spatial_quality_score'])}, "
        if math.isfinite(float(row["spatial_quality_score"]))
        else ""
    )
    print_fn(
        f"[INFO] Konvertiert {filename} | "
        f"Parameter: {_formatCompactParams(params)} | "
        f"Qualität: Fehler/Pixel={_formatQualityValue(row['error_per_pixel'])}, "
        f"Mean-Delta²={_formatQualityValue(row['mean_delta2'])}, "
        f"{spatial_quality_text}"
        f"beste Iteration={int(best_iter)}, "
        f"ausgeführt={row['actual_iterations']}/{row['requested_iterations']} | "
        f"Dauer={elapsed_sec:.1f}s"
    )
    _emit_anchor_variant_event("variant_done", status="ok")
    if os.path.exists(svg_path) and img is not None and hasattr(cv2_module, "imwrite"):
        try:
            with open(svg_path, "r", encoding="utf-8") as handle:
                png_svg_content = handle.read()
            png_rendered = render_svg_to_numpy_fn(png_svg_content, width, height)
            if png_rendered is not None:
                cv2_module.imwrite(os.path.join(png_out_dir, f"{base}.png"), png_rendered)
        except OSError:
            pass
    return row, False


def recordEarlyQualityAbortImpl(
    *,
    filename: str,
    row: dict[str, object],
    svg_out_dir: str,
    diff_out_dir: str,
    png_out_dir: str,
    reports_out_dir: str,
    gate: dict[str, object],
    append_batch_failure_fn,
    print_fn=print,
) -> None:
    """Preserve the probe SVG as a failed artifact and report a controlled abort."""
    base = os.path.splitext(filename)[0]
    svg_path = os.path.join(svg_out_dir, f"{base}.svg")
    failed_svg_path = os.path.join(svg_out_dir, f"Failed_{base}.svg")
    if os.path.exists(failed_svg_path):
        os.unlink(failed_svg_path)
    if os.path.exists(svg_path):
        os.replace(svg_path, failed_svg_path)
    _deleteDiffIfPresent(os.path.join(diff_out_dir, f"{base}_diff.png"))
    png_path = os.path.join(png_out_dir, f"{base}.png")
    if os.path.exists(png_path):
        os.unlink(png_path)

    error = float(row.get("error_per_pixel", float("inf")))
    threshold = float(gate.get("abort_error_per_pixel", float("inf")))
    probe_iterations = int(gate.get("probe_iterations", 3))
    details = (
        f"probe_error_per_pixel={error:.6f}; abort_threshold={threshold:.6f}; "
        f"probe_iterations={probe_iterations}; source={gate.get('source', '')}"
    )
    append_batch_failure_fn(
        {
            "filename": filename,
            "status": "early_quality_abort",
            "reason": "probe_far_above_success_threshold",
            "details": details,
            "log_file": f"{base}_element_validation.log",
            "failed_svg": os.path.basename(failed_svg_path) if os.path.exists(failed_svg_path) else "",
        }
    )
    log_path = os.path.join(reports_out_dir, f"{base}_element_validation.log")
    prior_log = _safeReadTextFile(log_path)
    with open(log_path, "w", encoding="utf-8") as handle:
        if prior_log:
            handle.write(prior_log.rstrip() + "\n")
        handle.write(
            "status=early_quality_abort\n"
            "reason=probe_far_above_success_threshold\n"
            f"{details}\n"
        )
    print_fn(
        f"[WARN] {filename}: Früher Qualitätsabbruch nach {probe_iterations} Probe-Iterationen "
        f"(Fehler/Pixel={error:.6f} > Abbruchgrenze={threshold:.6f})."
    )
