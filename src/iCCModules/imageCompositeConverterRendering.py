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
import xml.etree.ElementTree as ET

_INPROCESS_RENDER_COUNT = 0
_INPROCESS_GC_PERIOD = 25
_SUBPROCESS_RENDER_CALL_ID = 0
_SUBPROCESS_RENDER_AGG = {
    "calls": 0,
    "slow_calls": 0,
    "timeouts": 0,
    "elapsed_sum": 0.0,
}


def _expand_axis_aligned_linear_gradients_for_fitz(svg_string: str) -> str:
    """Expand gradient-filled rectangles only in the PyMuPDF render input.

    The bundled PyMuPDF build paints SVG linear gradients black.  Conversion
    output must nevertheless remain a native gradient, so this renderer adapter
    expands axis-aligned gradient rectangles in its private input document.  It
    is deliberately generic and keyed by SVG paint-server references, not image
    names or converter-specific gradient IDs.
    """
    if "linearGradient" not in svg_string or "url(#" not in svg_string:
        return svg_string
    try:
        root = ET.fromstring(svg_string)
    except ET.ParseError:
        return svg_string
    ET.register_namespace("", "http://www.w3.org/2000/svg")

    def local_name(element) -> str:
        return str(element.tag).rsplit("}", 1)[-1]

    def number(value: str | None, reference: float, default: float) -> float:
        text = str(value or "").strip()
        try:
            return reference * float(text[:-1]) / 100.0 if text.endswith("%") else float(text)
        except ValueError:
            return default

    def color(value: str) -> tuple[int, int, int] | None:
        text = value.strip()
        if len(text) == 7 and text.startswith("#"):
            try:
                return tuple(int(text[index:index + 2], 16) for index in (1, 3, 5))
            except ValueError:
                return None
        return None

    gradients = {
        element.get("id"): element
        for element in root.iter()
        if local_name(element) == "linearGradient" and element.get("id")
    }
    changed = False
    for parent in root.iter():
        for index, rectangle in reversed(list(enumerate(list(parent)))):
            if local_name(rectangle) != "rect":
                continue
            fill = rectangle.get("fill", "")
            match = re.fullmatch(r"url\(#([^)]+)\)", fill.strip())
            gradient = gradients.get(match.group(1)) if match else None
            if gradient is None:
                continue
            x = number(rectangle.get("x"), 1.0, 0.0)
            y = number(rectangle.get("y"), 1.0, 0.0)
            width = number(rectangle.get("width"), 1.0, 0.0)
            height = number(rectangle.get("height"), 1.0, 0.0)
            user_space = gradient.get("gradientUnits") == "userSpaceOnUse"
            x1 = number(gradient.get("x1"), width, x if user_space else 0.0)
            y1 = number(gradient.get("y1"), height, y if user_space else 0.0)
            x2 = number(gradient.get("x2"), width, x + width if user_space else width)
            y2 = number(gradient.get("y2"), height, y if user_space else 0.0)
            if not user_space:
                x1 += x
                x2 += x
                y1 += y
                y2 += y
            vertical = abs(y2 - y1) > abs(x2 - x1)
            reversed_axis = y2 < y1 if vertical else x2 < x1
            stops = []
            for stop in gradient:
                if local_name(stop) != "stop":
                    continue
                style = dict(
                    item.split(":", 1) for item in stop.get("style", "").split(";") if ":" in item
                )
                rgb = color(stop.get("stop-color", style.get("stop-color", "")))
                if rgb is not None:
                    stops.append((number(stop.get("offset"), 1.0, 0.0), rgb))
            stops.sort(key=lambda item: item[0])
            if width <= 0 or height <= 0 or len(stops) < 2:
                continue
            band_count = max(8, min(128, int(round(height if vertical else width)) * 2))
            inherited = {
                key: value for key, value in rectangle.attrib.items()
                if key not in {"x", "y", "width", "height", "fill", "stroke", "stroke-width"}
            }
            for band_index in range(band_count):
                position = (band_index + 0.5) / band_count
                if reversed_axis:
                    position = 1.0 - position
                left, right = stops[0], stops[-1]
                for stop_index in range(1, len(stops)):
                    if position <= stops[stop_index][0]:
                        left, right = stops[stop_index - 1], stops[stop_index]
                        break
                span = max(1e-9, right[0] - left[0])
                ratio = max(0.0, min(1.0, (position - left[0]) / span))
                rgb = tuple(round(a * (1.0 - ratio) + b * ratio) for a, b in zip(left[1], right[1]))
                band = ET.Element(rectangle.tag, inherited)
                if vertical:
                    band.set("x", f"{x:g}")
                    band.set("y", f"{y + height * band_index / band_count:g}")
                    band.set("width", f"{width:g}")
                    band.set("height", f"{height / band_count + 0.02:g}")
                else:
                    band.set("x", f"{x + width * band_index / band_count:g}")
                    band.set("y", f"{y:g}")
                    band.set("width", f"{width / band_count + 0.02:g}")
                    band.set("height", f"{height:g}")
                band.set("fill", "#" + "".join(f"{channel:02x}" for channel in rgb))
                band.set("stroke", "none")
                parent.insert(index + band_index, band)
            rectangle.set("fill", "none")
            parent.remove(rectangle)
            parent.insert(index + band_count, rectangle)
            changed = True
    return ET.tostring(root, encoding="unicode") if changed else svg_string


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

    renderer_svg = _expand_axis_aligned_linear_gradients_for_fitz(svg_string)
    attempts = [renderer_svg]
    normalized_svg = re.sub(r">\s+<", "><", renderer_svg.strip())
    if normalized_svg and normalized_svg != renderer_svg:
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
    child_env = os.environ.copy()
    pythonpath_entries: list[str] = []
    for entry in sys.path:
        if not entry:
            entry = os.getcwd()
        if entry and entry not in pythonpath_entries:
            pythonpath_entries.append(entry)
    existing_pythonpath = child_env.get("PYTHONPATH", "")
    if existing_pythonpath:
        for entry in existing_pythonpath.split(os.pathsep):
            if entry and entry not in pythonpath_entries:
                pythonpath_entries.append(entry)
    child_env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
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
            env=child_env,
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
