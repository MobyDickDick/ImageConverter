"""Deprecated flat-gradient detection helpers.

The former implementation detected thin raster bands and rebuilt them from sampled
column/row stops.  That routinely turned smooth panels into visible stripe-like
SVG output, so the strategy is intentionally disabled: callers keep the public
function names for compatibility, but no stripe/pixel-fit SVG is generated.
"""

from __future__ import annotations

from typing import Any


def detectGradientStripeStrategyImpl(
    img,
    *,
    np_module,
    white_threshold: int = 245,
    min_relative_width: float = 0.30,
    max_relative_height: float = 0.45,
    max_stops: int = 6,
    min_canvas_height: int = 8,
) -> dict[str, Any] | None:
    """Disable the legacy band-to-stop strategy.

    Smooth gradients must be handled by the framed-panel/semantic renderers, not
    by a detector that quantizes raster evidence into stripe-like stop columns.
    The parameters remain accepted so existing dependency wiring does not break.
    """
    return None


def buildGradientStripeSvgImpl(width: int, height: int, strategy: dict[str, Any]) -> str:
    """Return a smooth full-panel gradient instead of a quantized band fit."""
    stops = list(strategy.get("stops", [])) if isinstance(strategy, dict) else []
    first = str(stops[0].get("color", "#d9d9d9")) if stops and isinstance(stops[0], dict) else "#d9d9d9"
    last = str(stops[-1].get("color", "#f0f0f0")) if stops and isinstance(stops[-1], dict) else "#f0f0f0"
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        '  <defs>\n'
        '    <linearGradient id="smoothPanelGradient" x1="0%" y1="0%" x2="0%" y2="100%">\n'
        f'      <stop offset="0%" stop-color="{first}"/>\n'
        f'      <stop offset="100%" stop-color="{last}"/>\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        f'  <rect x="0" y="0" width="{safe_w}" height="{safe_h}" fill="url(#smoothPanelGradient)"/>\n'
        '</svg>\n'
    )
