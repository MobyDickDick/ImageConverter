    if fitz is None:
        raise RuntimeError("Fallback diff generation requires fitz (PyMuPDF).")

    with fitz.open(str(input_path)) as original_doc, fitz.open("pdf", svg_content.encode("utf-8")) as svg_doc:
        original_pix = original_doc[0].get_pixmap(alpha=False)

        # Render SVG with alpha and composite onto white so transparent
        # backgrounds do not appear black in the diff viewer.
        svg_pix = svg_doc[0].get_pixmap(alpha=True)
        if (svg_pix.width, svg_pix.height) != (original_pix.width, original_pix.height):
            svg_pix = fitz.Pixmap(svg_pix, original_pix.width, original_pix.height)

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
            mean_tone = (float(r0) + float(g0) + float(b0) + float(rs) + float(gs) + float(bs)) / 6.0
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

        diff_pix = fitz.Pixmap(fitz.csRGB, original_pix.width, original_pix.height, bytes(diff_samples), 0)
        # Explicitly release temporary MuPDF objects before returning the diff
        # pixmap to reduce native-memory pressure in long AC08 batch runs.
        del svg_pix
        del original_pix
        return diff_pix


def _compute_otsu_threshold(grayscale: list[list[int]]) -> int:
    hist = [0] * 256
    total = 0
    for row in grayscale:
        for value in row:
            hist[value] += 1
            total += 1
    if total == 0:
        return 220
    sum_total = sum(i * hist[i] for i in range(256))
    sum_bg = 0.0
    weight_bg = 0
    max_var = -1.0
    threshold = 220
    for t in range(256):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        between_var = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if between_var > max_var:
            max_var = between_var
            threshold = t
    return threshold


def _adaptive_threshold(grayscale: list[list[int]], block_size: int = 15, c: int = 5) -> list[list[int]]:
    h = len(grayscale)
    w = len(grayscale[0]) if h else 0
    out = [[0] * w for _ in range(h)]
    r = block_size // 2
    for y in range(h):
        for x in range(w):
            y0, y1 = max(0, y-r), min(h, y+r+1)
            x0, x1 = max(0, x-r), min(w, x+r+1)
            vals = [grayscale[yy][xx] for yy in range(y0, y1) for xx in range(x0, x1)]
            thresh = (sum(vals) / max(1, len(vals))) - c
            out[y][x] = 1 if grayscale[y][x] < thresh else 0
    return out


def load_binary_image_with_mode(path: Path, *, threshold: int = 220, mode: str = "global") -> list[list[int]]:
    grayscale = load_grayscale_image(path)
    m = str(mode).lower()
