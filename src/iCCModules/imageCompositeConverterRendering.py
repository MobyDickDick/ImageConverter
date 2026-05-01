"""Rendering helpers extracted from the imageCompositeConverter monolith."""

from __future__ import annotations

import base64
import gc
import json
import os
import re
import subprocess
import sys
import time

_INPROCESS_RENDER_COUNT = 0
_INPROCESS_GC_PERIOD = 25
_SUBPROCESS_RENDER_CALL_ID = 0
_SUBPROCESS_RENDER_AGG = {
    "calls": 0,
    "slow_calls": 0,
    "timeouts": 0,
    "elapsed_sum": 0.0,
}


def render_svg_to_numpy_inprocess(
    svg_string: str,
    size_w: int,
    size_h: int,
    *,
    fitz_module,
    np_module,
    cv2_module,
):
    if fitz_module is None or np_module is None or cv2_module is None:
        return None

    svg_string = str(svg_string or "")
    if re.search(r"(?<![A-Za-z])(nan|inf)(?![A-Za-z])", svg_string, flags=re.IGNORECASE):
        return None

    attempts = [svg_string]
    normalized_svg = re.sub(r">\s+<", "><", svg_string.strip())
    if normalized_svg and normalized_svg != svg_string:
        attempts.append(normalized_svg)

    for candidate_svg in attempts:
        global _INPROCESS_RENDER_COUNT
        page = None
        pix = None
        try:
            with fitz_module.open("pdf", candidate_svg.encode("utf-8")) as doc:
                page = doc.load_page(0)
                zoom_x = size_w / page.rect.width if page.rect.width > 0 else 1
                zoom_y = size_h / page.rect.height if page.rect.height > 0 else 1
                mat = fitz_module.Matrix(zoom_x, zoom_y)
                pix = page.get_pixmap(matrix=mat, alpha=True)
            rgba = np_module.frombuffer(pix.samples, dtype=np_module.uint8).reshape(pix.h, pix.w, 4).astype(np_module.float32)
            rgb = rgba[:, :, :3]
            alpha = (rgba[:, :, 3:4] / 255.0)
            composited = rgb + (255.0 * (1.0 - alpha))
            composited = np_module.clip(composited, 0.0, 255.0)
            img = composited.astype(np_module.uint8)
            return cv2_module.cvtColor(img, cv2_module.COLOR_RGB2BGR)
        except Exception:
            continue
        finally:
            if pix is not None:
                del pix
            if page is not None:
                del page
            _INPROCESS_RENDER_COUNT += 1
            if _INPROCESS_RENDER_COUNT % _INPROCESS_GC_PERIOD == 0:
                gc.collect()
    return None


def render_svg_to_numpy_via_subprocess(
    svg_string: str,
    size_w: int,
    size_h: int,
    *,
    np_module,
    timeout_sec: float,
):
    if np_module is None:
        return None
    payload = json.dumps(
        {"svg": str(svg_string or ""), "w": int(size_w), "h": int(size_h)},
        ensure_ascii=False,
    ).encode("utf-8")
    cmd = [sys.executable, "-m", "src.imageCompositeConverter", "--_render-svg-subprocess"]
    anchor_test_active = "test_ac08_semantic_anchor_variants_convert_without_failed_svg" in str(
        os.environ.get("PYTEST_CURRENT_TEST", "")
    )
    global _SUBPROCESS_RENDER_CALL_ID
    _SUBPROCESS_RENDER_CALL_ID += 1
    call_id = int(_SUBPROCESS_RENDER_CALL_ID)
    debug_render_timeout = (
        os.environ.get("ICC_DEBUG_RENDER_TIMEOUT", "").strip().lower() in {"1", "true", "yes", "on"}
        or "pytest" in sys.modules
    )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            cmd,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - started
        _SUBPROCESS_RENDER_AGG["calls"] += 1
        _SUBPROCESS_RENDER_AGG["timeouts"] += 1
        _SUBPROCESS_RENDER_AGG["elapsed_sum"] += float(elapsed)
        if debug_render_timeout:
            print(
                (
                    "[ICC_RENDER_TIMEOUT] render subprocess exceeded timeout "
                    f"({elapsed:.2f}s > {timeout_sec:.2f}s, size={size_w}x{size_h}, payload_bytes={len(payload)})"
                ),
                file=sys.stderr,
                flush=True,
            )
        if anchor_test_active:
            print(
                "[ANCHOR_DEBUG] render_probe "
                f"call_id={call_id} status=timeout timeout_sec={timeout_sec:.2f} "
                f"size={size_w}x{size_h} payload_bytes={len(payload)} elapsed={elapsed:.2f}s",
                flush=True,
            )
        return None
    except Exception:
        return None
    elapsed = time.monotonic() - started
    _SUBPROCESS_RENDER_AGG["calls"] += 1
    _SUBPROCESS_RENDER_AGG["elapsed_sum"] += float(elapsed)
    if elapsed > 1.0:
        _SUBPROCESS_RENDER_AGG["slow_calls"] += 1
    if anchor_test_active:
        print(
            "[ANCHOR_DEBUG] render_probe "
            f"call_id={call_id} status=done returncode={completed.returncode} timeout_sec={timeout_sec:.2f} "
            f"size={size_w}x{size_h} payload_bytes={len(payload)} elapsed={elapsed:.2f}s",
            flush=True,
        )
    if _SUBPROCESS_RENDER_AGG["calls"] % 25 == 0 and anchor_test_active:
        calls = int(_SUBPROCESS_RENDER_AGG["calls"])
        mean_elapsed = float(_SUBPROCESS_RENDER_AGG["elapsed_sum"]) / float(max(1, calls))
        print(
            "[ANCHOR_DEBUG] render_probe_aggregate "
            f"calls={calls} slow_calls_gt_1s={int(_SUBPROCESS_RENDER_AGG['slow_calls'])} "
            f"timeouts={int(_SUBPROCESS_RENDER_AGG['timeouts'])} mean_elapsed={mean_elapsed:.2f}s",
            flush=True,
        )
    if completed.returncode != 0 or not completed.stdout:
        return None
    try:
        response = json.loads(completed.stdout.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(response, dict) or not response.get("ok", False):
        return None
    try:
        w = int(response["w"])
        h = int(response["h"])
        raw = base64.b64decode(str(response["data"]).encode("ascii"))
        return np_module.frombuffer(raw, dtype=np_module.uint8).reshape(h, w, 3).copy()
    except Exception:
        return None
