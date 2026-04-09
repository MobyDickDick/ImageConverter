"""Geometry helpers for dual-stem symbols with bottom isosceles triangles.

The module is named after AC0050, but the implementation is intentionally
shape-driven so similar icons can be measured/refined with the same logic.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Ac0050Geometry:
    left_x: float
    right_x: float
    line_top: float
    line_bottom: float
    line_width: float
    triangle_half_base: float
    triangle_height: float
    left_line_color: str = "#e85b57"
    right_line_color: str = "#4e93c1"
    left_triangle_color: str = "#fa0506"
    right_triangle_color: str = "#136fad"


@dataclass(frozen=True)
class Ac0050DetectionConfig:
    """Generalized detection config for AC0050-like geometries."""

    min_peak_separation_ratio: float = 0.18
    line_window_ratio: float = 0.03
    line_bottom_quantile: float = 0.95
    triangle_search_half_width_ratio: float = 0.20
    triangle_base_band_ratio: float = 0.04
    triangle_near_base_ratio: float = 0.02
    enforce_horizontal_symmetry: bool = True


def defaultAc0050GeometryImpl(width: int, height: int) -> Ac0050Geometry:
    w = max(8.0, float(width))
    h = max(12.0, float(height))
    line_width = max(1.0, round(w * 0.05, 2))
    line_top = 0.0
    line_bottom = round(h * 0.93, 2)
    triangle_height = max(2.0, round(h * 0.07, 2))
    left_x = round(w * 0.15, 2)
    right_x = round(w * 0.85, 2)
    triangle_half_base = max(line_width * 2.0, round(w * 0.12, 2))
    return Ac0050Geometry(
        left_x=left_x,
        right_x=right_x,
        line_top=line_top,
        line_bottom=line_bottom,
        line_width=line_width,
        triangle_half_base=triangle_half_base,
        triangle_height=triangle_height,
    )


def _foregroundMask(img, *, cv2_module, np_module):
    if img is None or getattr(img, "size", 0) == 0:
        return None
    if len(img.shape) == 2:
        gray = img
    else:
        gray = cv2_module.cvtColor(img, cv2_module.COLOR_BGR2GRAY)

    _, otsu_mask = cv2_module.threshold(gray, 0, 255, cv2_module.THRESH_BINARY_INV + cv2_module.THRESH_OTSU)
    adaptive_mask = cv2_module.adaptiveThreshold(
        gray,
        255,
        cv2_module.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2_module.THRESH_BINARY_INV,
        11,
        2,
    )
    mask = cv2_module.bitwise_or(otsu_mask, adaptive_mask)

    kernel = np_module.ones((3, 3), dtype=np_module.uint8)
    mask = cv2_module.morphologyEx(mask, cv2_module.MORPH_OPEN, kernel)
    mask = cv2_module.morphologyEx(mask, cv2_module.MORPH_CLOSE, kernel)
    return mask


def _pickTwoDistinctPeaks(column_mass, *, min_sep: int):
    indexed = sorted(enumerate(column_mass), key=lambda item: float(item[1]), reverse=True)
    if not indexed:
        return None
    first = indexed[0][0]
    second = None
    for idx, _score in indexed[1:]:
        if abs(int(idx) - int(first)) >= int(min_sep):
            second = idx
            break
    if second is None:
        second = max(0, min(len(column_mass) - 1, int(first) + int(max(1, min_sep))))
    return tuple(sorted((int(first), int(second))))


def _estimateLineWidth(mask, left_x: int, right_x: int, *, np_module) -> float:
    widths: list[float] = []
    for x_center in (left_x, right_x):
        x0 = max(0, x_center - 4)
        x1 = min(mask.shape[1], x_center + 5)
        strip = mask[:, x0:x1]
        ys = np_module.where(strip.max(axis=1) > 0)[0]
        for y in ys[:: max(1, len(ys) // 20)]:
            row = strip[y]
            xs = np_module.where(row > 0)[0]
            if xs.size > 0:
                widths.append(float(xs.max() - xs.min() + 1))
    if widths:
        return max(1.0, float(np_module.median(np_module.array(widths, dtype=np_module.float32))))
    return 1.0


def _sampleBgrAt(img, x: float, y: float, *, np_module) -> tuple[int, int, int] | None:
    if img is None or len(img.shape) != 3:
        return None
    h, w = img.shape[:2]
    xi = max(0, min(w - 1, int(round(x))))
    yi = max(0, min(h - 1, int(round(y))))
    bgr = img[yi, xi]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])


def _bgrToHex(bgr: tuple[int, int, int] | None, fallback_hex: str) -> str:
    if bgr is None:
        return fallback_hex
    b, g, r = bgr
    return f"#{r:02x}{g:02x}{b:02x}"


def _applySymmetryIfRequested(geometry: Ac0050Geometry, *, width: int, enabled: bool) -> Ac0050Geometry:
    if not enabled:
        return geometry
    center_x = (geometry.left_x + geometry.right_x) / 2.0
    dist = min(center_x, float(width - 1) - center_x, (geometry.right_x - geometry.left_x) / 2.0)
    left_x = center_x - dist
    right_x = center_x + dist
    return Ac0050Geometry(**{**geometry.__dict__, "left_x": float(round(left_x, 2)), "right_x": float(round(right_x, 2))})


def measureAndDrawAc0050Impl(
    img,
    *,
    cv2_module,
    np_module,
    config: Ac0050DetectionConfig | None = None,
) -> tuple[Ac0050Geometry, str, list[str]]:
    """Measure dual-stem + dual-triangle geometry and draw SVG directly.

    The detector uses only structural cues (foreground mask + column mass peaks)
    and therefore generalizes to symbols with similar geometry and different
    colors/sizes.
    """
    cfg = config or Ac0050DetectionConfig()
    h, w = img.shape[:2]
    default = defaultAc0050GeometryImpl(w, h)
    logs: list[str] = []
    mask = _foregroundMask(img, cv2_module=cv2_module, np_module=np_module)
    if mask is None:
        svg = generateAc0050SvgImpl(w, h, default)
        return default, svg, ["ac0050: fallback to defaults (empty image)"]

    col_mass = mask.sum(axis=0)
    peaks = _pickTwoDistinctPeaks(col_mass, min_sep=max(2, int(round(w * float(cfg.min_peak_separation_ratio)))))
    if peaks is None:
        svg = generateAc0050SvgImpl(w, h, default)
        return default, svg, ["ac0050: fallback to defaults (no peaks)"]

    left_x, right_x = peaks
    half_window = max(1, int(round(w * float(cfg.line_window_ratio))))

    def _line_bounds(center_x: int) -> tuple[int, int]:
        x0 = max(0, center_x - half_window)
        x1 = min(w, center_x + half_window + 1)
        strip = mask[:, x0:x1]
        ys = np_module.where(strip.max(axis=1) > 0)[0]
        if ys.size == 0:
            return int(default.line_top), int(default.line_bottom)
        q = max(0.5, min(0.999, float(cfg.line_bottom_quantile)))
        q_bottom = int(round(float(np_module.quantile(ys, q))))
        return int(ys.min()), max(int(ys.min()), q_bottom)

    left_top, left_bottom = _line_bounds(int(left_x))
    right_top, right_bottom = _line_bounds(int(right_x))

    line_top = float(min(left_top, right_top))
    line_bottom = float(max(left_bottom, right_bottom))

    base_band_top = max(0, int(line_bottom - max(2, round(h * float(cfg.triangle_base_band_ratio)))))
    bottom_band = mask[base_band_top:h, :]

    def _triangle_metrics(center_x: int) -> tuple[float, float]:
        local_half = max(2, int(round(w * float(cfg.triangle_search_half_width_ratio))))
        x0 = max(0, center_x - local_half)
        x1 = min(w, center_x + local_half + 1)
        local = bottom_band[:, x0:x1]
        ys, xs = np_module.where(local > 0)
        if ys.size == 0:
            return default.triangle_half_base, default.triangle_height
        apex_y = float(base_band_top + ys.max())
        near_base = np_module.where(ys <= max(1, int(round(h * float(cfg.triangle_near_base_ratio)))))[0]
        if near_base.size > 0:
            run = xs[near_base]
            half_base = max(1.0, float((run.max() - run.min() + 1) / 2.0))
        else:
            half_base = float(default.triangle_half_base)
        tri_h = max(1.0, apex_y - line_bottom)
        return half_base, tri_h

    left_half_base, left_tri_h = _triangle_metrics(int(left_x))
    right_half_base, right_tri_h = _triangle_metrics(int(right_x))
    line_width = _estimateLineWidth(mask, int(left_x), int(right_x), np_module=np_module)

    # Color sampling is also generalized: read line and triangle tones from the
    # measured image; fallback to canonical AC0050 colors when unavailable.
    sample_y_line = max(0.0, min(float(h - 1), (line_top + line_bottom) / 2.0))
    sample_y_tri = max(0.0, min(float(h - 1), line_bottom + max(1.0, (left_tri_h + right_tri_h) / 2.0)))

    measured = Ac0050Geometry(
        left_x=float(left_x),
        right_x=float(right_x),
        line_top=max(0.0, line_top),
        line_bottom=min(float(h - 2), line_bottom),
        line_width=max(1.0, float(round(line_width, 2))),
        triangle_half_base=max(1.0, float(round((left_half_base + right_half_base) / 2.0, 2))),
        triangle_height=max(1.0, float(round((left_tri_h + right_tri_h) / 2.0, 2))),
        left_line_color=_bgrToHex(_sampleBgrAt(img, float(left_x), sample_y_line, np_module=np_module), default.left_line_color),
        right_line_color=_bgrToHex(_sampleBgrAt(img, float(right_x), sample_y_line, np_module=np_module), default.right_line_color),
        left_triangle_color=_bgrToHex(_sampleBgrAt(img, float(left_x), sample_y_tri, np_module=np_module), default.left_triangle_color),
        right_triangle_color=_bgrToHex(_sampleBgrAt(img, float(right_x), sample_y_tri, np_module=np_module), default.right_triangle_color),
    )
    measured = _applySymmetryIfRequested(measured, width=w, enabled=bool(cfg.enforce_horizontal_symmetry))

    logs.append(
        "ac0050: measured left_x={:.2f}, right_x={:.2f}, line_bottom={:.2f}, tri_h={:.2f}, line_w={:.2f}".format(
            measured.left_x,
            measured.right_x,
            measured.line_bottom,
            measured.triangle_height,
            measured.line_width,
        )
    )
    return measured, generateAc0050SvgImpl(w, h, measured), logs


def _renderAc0050Mask(width: int, height: int, geometry: Ac0050Geometry, *, cv2_module, np_module):
    canvas = np_module.zeros((height, width), dtype=np_module.uint8)
    lw = max(1, int(round(geometry.line_width)))
    cv2_module.line(
        canvas,
        (int(round(geometry.left_x)), int(round(geometry.line_top))),
        (int(round(geometry.left_x)), int(round(geometry.line_bottom))),
        255,
        lw,
    )
    cv2_module.line(
        canvas,
        (int(round(geometry.right_x)), int(round(geometry.line_top))),
        (int(round(geometry.right_x)), int(round(geometry.line_bottom))),
        255,
        lw,
    )

    def _triangle(cx: float):
        base_y = float(geometry.line_bottom)
        apex_y = base_y + float(geometry.triangle_height)
        half_base = float(geometry.triangle_half_base)
        return np_module.array(
            [
                [int(round(cx - half_base)), int(round(base_y))],
                [int(round(cx + half_base)), int(round(base_y))],
                [int(round(cx)), int(round(apex_y))],
            ],
            dtype=np_module.int32,
        )

    cv2_module.fillPoly(canvas, [_triangle(geometry.left_x)], 255)
    cv2_module.fillPoly(canvas, [_triangle(geometry.right_x)], 255)
    return canvas


def _maskError(target_mask, candidate_mask, *, np_module) -> float:
    if target_mask is None or candidate_mask is None:
        return float("inf")
    diff = np_module.abs(target_mask.astype(np_module.int16) - candidate_mask.astype(np_module.int16))
    return float(diff.mean())


def _clampGeometry(geometry: Ac0050Geometry, *, width: int, height: int) -> Ac0050Geometry:
    g = geometry
    left_x = max(0.0, min(float(width - 2), float(g.left_x)))
    right_x = max(left_x + 1.0, min(float(width - 1), float(g.right_x)))
    line_top = max(0.0, min(float(height - 2), float(g.line_top)))
    line_bottom = max(line_top + 1.0, min(float(height - 2), float(g.line_bottom)))
    triangle_half_base = max(1.0, min(float(width / 2.0), float(g.triangle_half_base)))
    triangle_height = max(1.0, min(float(height - line_bottom - 1.0), float(g.triangle_height)))
    line_width = max(1.0, min(8.0, float(g.line_width)))
    return Ac0050Geometry(
        left_x=round(left_x, 2),
        right_x=round(right_x, 2),
        line_top=round(line_top, 2),
        line_bottom=round(line_bottom, 2),
        line_width=round(line_width, 2),
        triangle_half_base=round(triangle_half_base, 2),
        triangle_height=round(triangle_height, 2),
        left_line_color=g.left_line_color,
        right_line_color=g.right_line_color,
        left_triangle_color=g.left_triangle_color,
        right_triangle_color=g.right_triangle_color,
    )


def refineAc0050GeometryIterativeImpl(
    img,
    initial_geometry: Ac0050Geometry,
    *,
    cv2_module,
    np_module,
    rounds: int = 3,
    config: Ac0050DetectionConfig | None = None,
) -> tuple[Ac0050Geometry, str, list[str]]:
    """Coordinate-wise iterative refinement against a generic foreground mask."""
    cfg = config or Ac0050DetectionConfig()
    h, w = img.shape[:2]
    target_mask = _foregroundMask(img, cv2_module=cv2_module, np_module=np_module)
    best = _clampGeometry(initial_geometry, width=w, height=h)
    logs: list[str] = []

    def _err(g: Ac0050Geometry) -> float:
        cand = _renderAc0050Mask(w, h, g, cv2_module=cv2_module, np_module=np_module)
        return _maskError(target_mask, cand, np_module=np_module)

    best_err = _err(best)
    logs.append(f"ac0050: iterative start_err={best_err:.4f}")

    base_steps = {
        "left_x": max(0.5, w * 0.03),
        "right_x": max(0.5, w * 0.03),
        "line_bottom": max(0.5, h * 0.02),
        "triangle_half_base": max(0.5, w * 0.02),
        "triangle_height": max(0.5, h * 0.02),
        "line_width": 1.0,
    }

    keys = list(base_steps)
    for round_idx in range(max(1, int(rounds))):
        improved = False
        decay = 1.0 / (1.0 + (0.4 * round_idx))
        for key in keys:
            step = base_steps[key] * decay
            for direction in (-1.0, 1.0):
                value = float(getattr(best, key)) + (direction * step)
                candidate = Ac0050Geometry(**{**best.__dict__, key: float(round(value, 2))})
                if bool(cfg.enforce_horizontal_symmetry) and key in {"left_x", "right_x"}:
                    candidate = _applySymmetryIfRequested(candidate, width=w, enabled=True)
                candidate = _clampGeometry(candidate, width=w, height=h)
                err = _err(candidate)
                if err + 1e-6 < best_err:
                    best = candidate
                    best_err = err
                    improved = True
                    logs.append(f"ac0050: r{round_idx + 1} improved {key} -> {value:.2f}, err={err:.4f}")
        if not improved:
            logs.append(f"ac0050: r{round_idx + 1} no improvement")
            break

    return best, generateAc0050SvgImpl(w, h, best), logs


def generateAc0050SvgImpl(width: int, height: int, geometry: Ac0050Geometry) -> str:
    line_half = float(geometry.line_width) / 2.0
    line_top = float(geometry.line_top)
    line_bottom = float(geometry.line_bottom)

    def _line_path(x: float) -> str:
        return (
            f"M {x + line_half:.3f},{line_bottom:.3f} "
            f"H {x - line_half:.3f} "
            f"V {line_top:.3f} "
            f"H {x + line_half:.3f} "
            f"V {line_bottom:.3f} Z"
        )

    def _triangle_path(x: float) -> str:
        base_y = line_bottom
        apex_y = base_y + float(geometry.triangle_height)
        half_base = float(geometry.triangle_half_base)
        return (
            f"M {x - half_base:.3f},{base_y:.3f} "
            f"L {x + half_base:.3f},{base_y:.3f} "
            f"L {x:.3f},{apex_y:.3f} Z"
        )

    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            (
                f'<svg width="{int(width)}" height="{int(height)}" '
                f'viewBox="0 0 {int(width)} {int(height)}" version="1.1" '
                'xmlns="http://www.w3.org/2000/svg">'
            ),
            "  <g id=\"ac0050\">",
            f'    <path style="fill:{geometry.right_line_color}" d="{_line_path(float(geometry.right_x))}" />',
            f'    <path style="fill:{geometry.left_line_color}" d="{_line_path(float(geometry.left_x))}" />',
            f'    <path style="fill:{geometry.left_triangle_color}" d="{_triangle_path(float(geometry.left_x))}" />',
            f'    <path style="fill:{geometry.right_triangle_color}" d="{_triangle_path(float(geometry.right_x))}" />',
            "  </g>",
            "</svg>",
        ]
    )
