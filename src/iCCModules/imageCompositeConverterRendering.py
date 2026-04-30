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
        if debug_render_timeout:
            elapsed = time.monotonic() - started
            print(
                (
                    "[ICC_RENDER_TIMEOUT] render subprocess exceeded timeout "
                    f"({elapsed:.2f}s > {timeout_sec:.2f}s, size={size_w}x{size_h}, payload_bytes={len(payload)})"
                ),
                file=sys.stderr,
                flush=True,
            )
        return None
    except Exception:
        return None
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
