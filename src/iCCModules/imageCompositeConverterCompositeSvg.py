"""Composite-SVG helper blocks extracted from imageCompositeConverter."""

from __future__ import annotations

from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers
from src.iCCModules import imageCompositeConverterGeometryIrOptimizer as geometry_ir_optimizer
from src.iCCModules import imageCompositeConverterPolicyPhase as policy_phase_helpers
from src.iCCModules import imageCompositeConverterChainTelemetry as chain_telemetry_helpers


def _approximate_contour_points(contour, *, cv2_module, np_module, ratio: float = 0.10):
    """Iteratively approximate a contour and target ~ratio of original points."""
    if contour is None or len(contour) < 4:
        return contour

    arc_len = float(cv2_module.arcLength(contour, True))
    if arc_len <= 1e-6:
        return contour

    raw_count = int(len(contour))
    target_count = max(4, int(round(raw_count * max(0.02, min(0.50, ratio)))))

    lo, hi = 0.0, 0.20
    best = contour
    best_distance = abs(raw_count - target_count)

    for _ in range(20):
        eps_factor = (lo + hi) * 0.5
        approx = cv2_module.approxPolyDP(contour, eps_factor * arc_len, True)
        count = int(len(approx))
        distance = abs(count - target_count)
        if distance <= best_distance:
            best, best_distance = approx, distance
        if count > target_count:
            lo = eps_factor
        else:
            hi = eps_factor
    return best


def _closed_catmull_rom_to_bezier_path(points_xy):
    """Create a smooth closed SVG path using cubic Bézier segments."""
    if len(points_xy) < 4:
        return ""

    path = [f"M {points_xy[0][0]:.3f},{points_xy[0][1]:.3f}"]
    n = len(points_xy)
    for i in range(n):
        p0 = points_xy[(i - 1) % n]
        p1 = points_xy[i % n]
        p2 = points_xy[(i + 1) % n]
        p3 = points_xy[(i + 2) % n]

        c1x = p1[0] + (p2[0] - p0[0]) / 6.0
        c1y = p1[1] + (p2[1] - p0[1]) / 6.0
        c2x = p2[0] - (p3[0] - p1[0]) / 6.0
        c2y = p2[1] - (p3[1] - p1[1]) / 6.0
        path.append(f"C {c1x:.3f},{c1y:.3f} {c2x:.3f},{c2y:.3f} {p2[0]:.3f},{p2[1]:.3f}")

    path.append("Z")
    return " ".join(path)


def traceImageSegmentImpl(
    img_segment,
    epsilon_factor: float,
    *,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    cv2_module,
    np_module,
    rgb_to_hex_fn,
) -> list[str]:
    if img_segment is None or img_segment.size == 0:
        return []

    data = np_module.float32(img_segment).reshape((-1, 3))
    criteria = (cv2_module.TERM_CRITERIA_EPS + cv2_module.TERM_CRITERIA_MAX_ITER, 20, 0.001)
    _, labels, centers = cv2_module.kmeans(
        data,
        4,
        None,
        criteria,
        10,
        cv2_module.KMEANS_RANDOM_CENTERS,
    )
    centers = np_module.uint8(centers)
    img_quant = centers[labels.flatten()].reshape(img_segment.shape)

    unique, counts = np_module.unique(img_quant.reshape(-1, 3), axis=0, return_counts=True)
    bg_color = unique[np_module.argmax(counts)]

    paths: list[str] = []
    for color in unique:
        if np_module.array_equal(color, bg_color):
            continue

        mask = cv2_module.inRange(img_quant, color, color)
        contours, _ = cv2_module.findContours(mask, cv2_module.RETR_CCOMP, cv2_module.CHAIN_APPROX_NONE)
        hex_color = rgb_to_hex_fn(color[::-1])

        for contour in contours:
            if cv2_module.contourArea(contour) < 10:
                continue

            # Plan-B: (1) pixel contour tracing is from CHAIN_APPROX_NONE,
            # (2) iterative point thinning (~10%) + smoothing into cubic Bézier segments.
            approx = _approximate_contour_points(contour, cv2_module=cv2_module, np_module=np_module, ratio=0.10)

            points_xy = [
                ((pt[0][0] * scale_x) + offset_x, (pt[0][1] * scale_y) + offset_y)
                for pt in approx
            ]

            path_d = ""
            if len(points_xy) >= 4:
                path_d = _closed_catmull_rom_to_bezier_path(points_xy)

            if not path_d:
                epsilon = epsilon_factor * cv2_module.arcLength(contour, True)
                fallback = cv2_module.approxPolyDP(contour, epsilon, True)
                path_d = "M " + " L ".join(
                    [
                        (
                            f"{(pt[0][0] * scale_x) + offset_x:.3f},"
                            f"{(pt[0][1] * scale_y) + offset_y:.3f}"
                        )
                        for pt in fallback
                    ]
                ) + " Z"

            paths.append(f'  <path d="{path_d}" fill="{hex_color}" stroke="none" />')
    return paths


def generateCompositeSvgImpl(
    w: int,
    h: int,
    params: dict,
    folder_path: str,
    epsilon: float,
    *,
    os_module,
    cv2_module,
    trace_image_segment_fn,
) -> str:
    svg_elements = [
        (
            f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">'
        )
    ]

    if params["top_source_ref"]:
        ref_path = None
        for ext in [".jpg", ".JPG", ".jpeg", ".JPEG", ".bmp", ".png", ".PNG"]:
            candidate = os_module.path.join(folder_path, params["top_source_ref"] + ext)
            if os_module.path.exists(candidate):
                ref_path = candidate
                break

        if ref_path:
            ref_img = cv2_module.imread(ref_path)
            ref_h, ref_w = ref_img.shape[:2]
            cut_ratio = 0.55
            cut_y = max(1, int(round(ref_h * cut_ratio)))
            top_half_img = ref_img[0:cut_y, 0:ref_w]
            target_top_h = max(1, int(round(h * cut_ratio)))
            scale_x = w / ref_w if ref_w > 0 else 1.0
            scale_y = target_top_h / cut_y if cut_y > 0 else 1.0
            svg_elements.extend(
                trace_image_segment_fn(
                    top_half_img,
                    epsilon,
                    scale_x=scale_x,
                    scale_y=scale_y,
                )
            )

    geometry_ir = geometry_ir_optimizer.selectGeometryIrForRenderingImpl(params)
    geometry_ir = policy_phase_helpers.applyPolicyPhaseAfterGeometryImpl(params, geometry_ir)
    params["chain_phase_telemetry"] = chain_telemetry_helpers.summarizeChainTelemetryImpl(params)
    params["chain_phase_telemetry_line"] = chain_telemetry_helpers.formatChainTelemetryLineImpl(
        params["chain_phase_telemetry"]
    )
    if geometry_ir:
        svg_elements.extend(geometry_ir_helpers.renderGeometryIrToSvgElementsImpl(w, h, geometry_ir))
    elif params["bottom_shape"] == "square_cross":
        square_cross_ir = [
            {
                "kind": "RectBorder",
                "id": "square_cross_rect",
                "bbox": [0.35, 0.60, 0.30, 0.30],
                "fill": "#e6e6e6",
                "stroke": "#4d4d4d",
                "stroke_width": 0.02,
            },
            {
                "kind": "DiagonalBand",
                "id": "square_cross_tl_br",
                "direction": "tl_br",
                "stroke": "#4d4d4d",
                "stroke_width": 0.02,
            },
            {
                "kind": "DiagonalBand",
                "id": "square_cross_tr_bl",
                "direction": "tr_bl",
                "stroke": "#4d4d4d",
                "stroke_width": 0.02,
            },
        ]
        svg_elements.extend(geometry_ir_helpers.renderGeometryIrToSvgElementsImpl(w, h, square_cross_ir))

    svg_elements.append("</svg>")
    return "\n".join(svg_elements)
