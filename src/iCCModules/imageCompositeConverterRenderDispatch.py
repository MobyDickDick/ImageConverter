"""SVG render dispatch helper extracted from the converter monolith."""

from __future__ import annotations


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
    if svg_render_subprocess_enabled and not is_fitz_open_monkeypatched_fn():
        rendered = render_svg_to_numpy_via_subprocess_fn(svg_string, size_w, size_h)
        if rendered is not None:
            return rendered
        if under_pytest_runtime and not is_inprocess_renderer_monkeypatched_fn():
            # Avoid unstable in-process PyMuPDF fallback in long pytest
            # sessions; dedicated tests can still exercise fallback by
            # monkeypatching the in-process renderer helper.
            return None
    return render_svg_to_numpy_inprocess_fn(svg_string, size_w, size_h)
