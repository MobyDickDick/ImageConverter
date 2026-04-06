"""Composite-SVG helper blocks extracted from imageCompositeConverter."""

from __future__ import annotations


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

            epsilon = epsilon_factor * cv2_module.arcLength(contour, True)
            approx = cv2_module.approxPolyDP(contour, epsilon, True)
            path_d = "M " + " L ".join(
                [
                    (
                        f"{(pt[0][0] * scale_x) + offset_x:.3f},"
                        f"{(pt[0][1] * scale_y) + offset_y:.3f}"
                    )
                    for pt in approx
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

    if params["bottom_shape"] == "square_cross":
        cx = w / 2
        cy = h * 0.75
        s = min(w, h) * 0.15
        sw = w * 0.02
        svg_elements.append(
            f'  <rect x="{cx-s}" y="{cy-s}" width="{s*2}" height="{s*2}" fill="#e6e6e6" stroke="#4d4d4d" stroke-width="{sw}"/>'
        )
        svg_elements.append(
            f'  <line x1="{cx-s}" y1="{cy-s}" x2="{cx+s}" y2="{cy+s}" stroke="#4d4d4d" stroke-width="{sw}"/>'
        )
        svg_elements.append(
            f'  <line x1="{cx+s}" y1="{cy-s}" x2="{cx-s}" y2="{cy+s}" stroke="#4d4d4d" stroke-width="{sw}"/>'
        )

    svg_elements.append("</svg>")
    return "\n".join(svg_elements)
