"""Runtime helpers for isolated SVG rendering and legacy bbox serialization."""

from __future__ import annotations

import base64
import json


def is_fitz_open_monkeypatched(*, fitz_module) -> bool:
    """Detect test monkeypatching so render failure tests can exercise in-process behavior."""
    if fitz_module is None:
        return False
    open_fn = getattr(fitz_module, "open", None)
    if open_fn is None:
        return False
    expected_module = getattr(fitz_module, "__name__", "")
    actual_module = getattr(open_fn, "__module__", "")
    if not actual_module:
        return False
    allowed_modules = {expected_module, "pymupdf", "fitz"}
    return actual_module not in allowed_modules


def is_inprocess_renderer_monkeypatched(*, inprocess_fn, module_name: str) -> bool:
    if inprocess_fn is None:
        return False
    inprocess_module_name = getattr(inprocess_fn, "__module__", "")
    return bool(inprocess_module_name) and inprocess_module_name != module_name


def bbox_to_dict(label: str, bbox: tuple[int, int, int, int], color: tuple[int, int, int]) -> dict[str, object]:
    x0, y0, x1, y1 = bbox
    return {
        "label": label,
        "bbox": {
            "x0": int(x0),
            "y0": int(y0),
            "x1": int(x1),
            "y1": int(y1),
            "width": int(x1 - x0 + 1),
            "height": int(y1 - y0 + 1),
        },
        "color_bgr": [int(color[0]), int(color[1]), int(color[2])],
    }


def run_svg_render_subprocess_entrypoint(*, stdin_bytes: bytes, render_svg_to_numpy_inprocess) -> tuple[int, str]:
    try:
        payload = json.loads(stdin_bytes.decode("utf-8"))
    except Exception:
        return 2, ""
    svg = str(payload.get("svg", ""))
    w = int(payload.get("w", 0))
    h = int(payload.get("h", 0))
    if w <= 0 or h <= 0:
        return 2, ""
    rendered = render_svg_to_numpy_inprocess(svg, w, h)
    if rendered is None:
        return 0, '{"ok": false}\n'
    response = {
        "ok": True,
        "w": int(rendered.shape[1]),
        "h": int(rendered.shape[0]),
        "data": base64.b64encode(rendered.tobytes()).decode("ascii"),
    }
    return 0, json.dumps(response, separators=(",", ":"))
