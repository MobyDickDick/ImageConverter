from __future__ import annotations


def createDiffImageImpl(
    img_orig,
    img_svg,
    *,
    cv2_module,
    np_module,
    focus_mask=None,
):
    """Return a signed, normalized RGB delta visualization.

    Pixels where the generated image is brighter are tinted cyan; pixels where
    it is darker are tinted red.  The tint is normalized by the strongest
    eligible absolute luminance delta so small and large symbols remain
    comparable, while zero-delta and out-of-focus pixels keep the source tone.
    """
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(
            img_svg,
            (img_orig.shape[1], img_orig.shape[0]),
            interpolation=cv2_module.INTER_AREA,
        )

    diff = img_svg.astype(np_module.float32) - img_orig.astype(np_module.float32)
    signed_delta = np_module.mean(diff, axis=2)

    eligible_mask = np_module.ones(signed_delta.shape, dtype=bool)
    if focus_mask is not None:
        if focus_mask.shape[:2] != img_orig.shape[:2]:
            focus_mask = cv2_module.resize(
                focus_mask.astype(np_module.uint8),
                (img_orig.shape[1], img_orig.shape[0]),
                interpolation=cv2_module.INTER_NEAREST,
            )
        eligible_mask = focus_mask > 0

    changed_mask = eligible_mask & (np_module.abs(signed_delta) > 0)
    if not bool(np_module.any(changed_mask)):
        return img_orig.copy()

    max_abs_delta = float(np_module.max(np_module.abs(signed_delta[changed_mask])))
    if max_abs_delta <= 0.0:
        return img_orig.copy()

    magnitude = np_module.zeros(signed_delta.shape, dtype=np_module.float32)
    magnitude[changed_mask] = np_module.clip(
        np_module.abs(signed_delta[changed_mask]) / max_abs_delta,
        0.0,
        1.0,
    )

    result = img_orig.astype(np_module.float32).copy()
    positive_tint = np_module.array([43.0, 43.0, 13.0], dtype=np_module.float32)
    negative_tint = np_module.array([-7.0, -7.0, 23.0], dtype=np_module.float32)

    positive_mask = changed_mask & (signed_delta > 0)
    negative_mask = changed_mask & (signed_delta < 0)
    if bool(np_module.any(positive_mask)):
        result[positive_mask] = (
            result[positive_mask] * 0.85
            + magnitude[positive_mask, None] * positive_tint
        )
    if bool(np_module.any(negative_mask)):
        result[negative_mask] = (
            result[negative_mask] * 0.85
            + magnitude[negative_mask, None] * negative_tint
        )

    return np_module.clip(np_module.rint(result), 0, 255).astype(np_module.uint8)


def _top_quartile_delta2_mask(delta2, *, np_module, eligible_mask=None):
    """Return a mask for the highest-delta² quartile of eligible pixels.

    The diagnostics are intentionally capped at the upper quartile: for 100
    eligible pixels exactly 25 pixels are selected (unless every delta² is 0).
    """
    flat_delta2 = delta2.reshape(-1)
    if eligible_mask is None:
        eligible_indices = np_module.arange(flat_delta2.size)
    else:
        eligible_indices = np_module.flatnonzero(eligible_mask.reshape(-1))
    selected_mask = np_module.zeros(flat_delta2.shape, dtype=bool)
    eligible_count = int(eligible_indices.size)
    if eligible_count == 0:
        return selected_mask.reshape(delta2.shape), 0
    eligible_delta2 = flat_delta2[eligible_indices]
    if not bool(np_module.any(eligible_delta2 > 0)):
        return selected_mask.reshape(delta2.shape), 0
    selection_count = max(1, int(np_module.ceil(float(eligible_count) * 0.25)))
    ranked_order = eligible_indices[
        np_module.argsort(eligible_delta2, kind="stable")[::-1][:selection_count]
    ]
    selected_mask[ranked_order] = True
    return selected_mask.reshape(delta2.shape), selection_count


def calculateErrorImpl(img_orig, img_svg, *, cv2_module, np_module) -> float:
    if img_svg is None:
        return float("inf")
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(
            img_svg,
            (img_orig.shape[1], img_orig.shape[0]),
            interpolation=cv2_module.INTER_AREA,
        )
    return float(np_module.mean(cv2_module.absdiff(img_orig, img_svg)))


def createDiffImageWithoutCv2Impl(input_path, svg_content, *, fitz_module):
    """Create a normalized signed red/cyan diff image when numpy/opencv are unavailable."""
    if fitz_module is None:
        raise RuntimeError("Fallback diff generation requires fitz (PyMuPDF).")

    with fitz_module.open(str(input_path)) as original_doc, fitz_module.open(
        "pdf", svg_content.encode("utf-8")
    ) as svg_doc:
        original_pix = original_doc[0].get_pixmap(alpha=False)

        # Render SVG with alpha and composite onto white so transparent
        # backgrounds do not appear black in the diff viewer.
        svg_pix = svg_doc[0].get_pixmap(alpha=True)
        if (svg_pix.width, svg_pix.height) != (original_pix.width, original_pix.height):
            svg_pix = fitz_module.Pixmap(
                svg_pix, original_pix.width, original_pix.height
            )

        original_samples = original_pix.samples
        svg_samples = svg_pix.samples
        diff_samples = bytearray(len(original_samples))

        for idx in range(0, len(diff_samples), 3):
            r0, g0, b0 = original_samples[idx : idx + 3]
            sidx = (idx // 3) * 4
            rs, gs, bs, sa = svg_samples[sidx : sidx + 4]
            alpha = float(sa) / 255.0
            # PyMuPDF delivers premultiplied RGB when alpha=True. Composite onto
            # white without multiplying RGB by alpha a second time.
            rs = int(round(min(255.0, max(0.0, float(rs) + (255.0 * (1.0 - alpha))))))
            gs = int(round(min(255.0, max(0.0, float(gs) + (255.0 * (1.0 - alpha))))))
            bs = int(round(min(255.0, max(0.0, float(bs) + (255.0 * (1.0 - alpha))))))
            dx = float(rs - r0) + float(gs - g0) + float(bs - b0)
            norm = max(-1.0, min(1.0, dx / (3.0 * 255.0)))
            magnitude = abs(norm)
            mean_tone = (
                float(r0) + float(g0) + float(b0) + float(rs) + float(gs) + float(bs)
            ) / 6.0
            up = int(round(mean_tone + magnitude * (255.0 - mean_tone)))
            down = int(round(mean_tone * (1.0 - magnitude)))
            if norm >= 0.0:
                # Positive delta (generated image brighter than source): cyan tint from base tone.
                diff_samples[idx] = down
                diff_samples[idx + 1] = up
                diff_samples[idx + 2] = up
            else:
                # Negative delta (generated image darker than source): red tint from base tone.
                diff_samples[idx] = up
                diff_samples[idx + 1] = down
                diff_samples[idx + 2] = down

        diff_pix = fitz_module.Pixmap(
            fitz_module.csRGB,
            original_pix.width,
            original_pix.height,
            bytes(diff_samples),
            0,
        )
        # Explicitly release temporary MuPDF objects before returning the diff
        # pixmap to reduce native-memory pressure in long AC08 batch runs.
        del svg_pix
        del original_pix
        return diff_pix


def diffPixelSummaryImpl(
    img_orig, img_svg, *, cv2_module, np_module
) -> dict[str, object]:
    """Return compact, deterministic pixel-difference diagnostics."""
    if img_svg is None:
        return {"status": "missing_render"}
    if img_svg.shape[:2] != img_orig.shape[:2]:
        img_svg = cv2_module.resize(
            img_svg,
            (img_orig.shape[1], img_orig.shape[0]),
            interpolation=cv2_module.INTER_AREA,
        )
    diff = img_svg.astype(np_module.int16) - img_orig.astype(np_module.int16)
    abs_diff = np_module.abs(diff).astype(np_module.int32)
    delta2 = np_module.sum(
        diff.astype(np_module.int32) * diff.astype(np_module.int32), axis=2
    )
    changed_mask = np_module.any(abs_diff > 0, axis=2)
    raw_changed_pixels = int(np_module.count_nonzero(changed_mask))
    pixel_count = int(img_orig.shape[0] * img_orig.shape[1])
    quartile_mask, quartile_pixel_count = _top_quartile_delta2_mask(
        delta2, np_module=np_module
    )
    if quartile_pixel_count:
        ys, xs = np_module.where(quartile_mask)
        max_index = int(np_module.argmax(delta2))
        max_y = int(max_index // img_orig.shape[1])
        max_x = int(max_index % img_orig.shape[1])
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        max_abs_channel_delta = int(abs_diff.max())
    else:
        bbox = None
        max_x = max_y = 0
        max_abs_channel_delta = 0
    return {
        "status": "ok",
        "pixel_count": pixel_count,
        # Backwards-compatible keys now describe the selected upper quartile, not
        # all non-identical pixels.  The raw count is still available separately.
        "changed_pixels": quartile_pixel_count,
        "changed_fraction": (
            (float(quartile_pixel_count) / float(pixel_count)) if pixel_count else 0.0
        ),
        "raw_changed_pixels": raw_changed_pixels,
        "raw_changed_fraction": (
            (float(raw_changed_pixels) / float(pixel_count)) if pixel_count else 0.0
        ),
        "quartile_pixel_count": quartile_pixel_count,
        "quartile_fraction": (
            (float(quartile_pixel_count) / float(pixel_count)) if pixel_count else 0.0
        ),
        "mean_abs_channel_delta": float(abs_diff.mean()) if pixel_count else 0.0,
        "mean_delta2": float(delta2.mean()) if pixel_count else 0.0,
        "max_delta2": int(delta2.max()) if pixel_count else 0,
        "max_abs_channel_delta": max_abs_channel_delta,
        "max_delta_position": (max_x, max_y),
        "changed_bbox": bbox,
    }


def createCommentedDiffImageImpl(
    diff_img, summary: dict[str, object], *, cv2_module, np_module, title: str = ""
):
    """Append a readable diagnostics panel below a pixel-difference image."""
    if diff_img is None:
        return None
    image = diff_img.copy()
    if len(image.shape) == 2:
        image = cv2_module.cvtColor(image, cv2_module.COLOR_GRAY2BGR)
    height, width = image.shape[:2]
    readable_width = max(width, 640)
    if readable_width > width:
        expanded = np_module.full((height, readable_width, 3), 255, dtype=image.dtype)
        x_offset = (readable_width - width) // 2
        expanded[:, x_offset : x_offset + width] = image
        image = expanded
        width = readable_width
    panel_height = 148
    panel = np_module.full((panel_height, width, 3), 255, dtype=image.dtype)
    bbox = summary.get("changed_bbox")
    pos = summary.get("max_delta_position")
    lines = [
        title or "Pixel difference diagnostics",
        f"upper_quartile_pixels={summary.get('quartile_pixel_count', summary.get('changed_pixels', 0))}/{summary.get('pixel_count', 0)} ({float(summary.get('quartile_fraction', summary.get('changed_fraction', 0.0))):.2%})",
        f"mean_abs_channel_delta={float(summary.get('mean_abs_channel_delta', 0.0)):.3f}",
        f"mean_delta2={float(summary.get('mean_delta2', 0.0)):.3f} max_delta2={summary.get('max_delta2', 0)}",
        f"max_abs_channel_delta={summary.get('max_abs_channel_delta', 0)} at={pos}",
        f"changed_bbox={bbox}",
    ]
    font = getattr(cv2_module, "FONT_HERSHEY_SIMPLEX", 0)
    if hasattr(cv2_module, "putText"):
        for idx, line in enumerate(lines):
            cv2_module.putText(
                panel,
                str(line),
                (10, 24 + idx * 24),
                font,
                0.58,
                (0, 0, 0),
                1,
                getattr(cv2_module, "LINE_AA", 8),
            )
    else:
        # Test doubles and minimal image backends may not expose text drawing;
        # keep the artifact visibly annotated by reserving one dark marker row
        # per would-be text line.
        for idx, _line in enumerate(lines):
            y = min(panel.shape[0] - 1, 24 + idx * 24)
            panel[max(0, y - 1) : y + 1, :] = 0
    return np_module.vstack([image, panel])
