"""SVG render dispatch helper extracted from the converter monolith."""

from __future__ import annotations

from collections import OrderedDict

_RENDER_CACHE_MAX_ENTRIES = 512
_RENDER_CACHE: OrderedDict[tuple[bool, int, int, str], object] = OrderedDict()


def renderSvgToNumpyImpl(
    svg_string: str,
    size_w: int,
    size_h: int,
    *,
    svg_render_subprocess_enabled: bool,
    under_pytest_runtime: bool,
    is_fitz_open_monkeypatched_fn,
    render_svg_to_numpy_via_subprocess_fn,
    is_inprocess_renderer_monkeypatched_fn,
    render_svg_to_numpy_inprocess_fn,
):
    """Render an SVG with optional isolated subprocess fallback semantics."""
    cache_key = (bool(svg_render_subprocess_enabled), int(size_w), int(size_h), svg_string)
    cached = _RENDER_CACHE.get(cache_key)
    if cached is not None:
        _RENDER_CACHE.move_to_end(cache_key)
        return cached.copy() if hasattr(cached, "copy") else cached

    if svg_render_subprocess_enabled and not is_fitz_open_monkeypatched_fn():
        rendered = render_svg_to_numpy_via_subprocess_fn(svg_string, size_w, size_h)
        if rendered is not None:
            _RENDER_CACHE[cache_key] = rendered
            _RENDER_CACHE.move_to_end(cache_key)
            if len(_RENDER_CACHE) > _RENDER_CACHE_MAX_ENTRIES:
                _RENDER_CACHE.popitem(last=False)
            return rendered.copy() if hasattr(rendered, "copy") else rendered
        if under_pytest_runtime and not is_inprocess_renderer_monkeypatched_fn():
            # Avoid unstable in-process PyMuPDF fallback in long pytest
            # sessions; dedicated tests can still exercise fallback by
            # monkeypatching the in-process renderer helper.
            return None
    rendered = render_svg_to_numpy_inprocess_fn(svg_string, size_w, size_h)
    if rendered is not None:
        _RENDER_CACHE[cache_key] = rendered
        _RENDER_CACHE.move_to_end(cache_key)
        if len(_RENDER_CACHE) > _RENDER_CACHE_MAX_ENTRIES:
            _RENDER_CACHE.popitem(last=False)
        return rendered.copy() if hasattr(rendered, "copy") else rendered
    return rendered
