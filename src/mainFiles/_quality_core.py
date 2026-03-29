def _quality_sort_key(row: dict[str, object]) -> tuple[float, float, str]:
    """Stable quality ordering from best to worst."""

    error_pp = float(row.get("error_per_pixel", float("inf")))
    mean_delta2 = float(row.get("mean_delta2", float("inf")))
    variant = str(row.get("variant", row.get("filename", ""))).upper()
    return error_pp, mean_delta2, variant


def render_svg_to_numpy(svg_content: str, width: int, height: int):
    if np is None or fitz is None:
        return None
    try:
        doc = fitz.open(stream=str(svg_content or "").encode("utf-8"), filetype="svg")
        page = doc[0]
        pix = page.get_pixmap(alpha=False, colorspace=fitz.csRGB)
        buf = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        img = buf[:, :, :3]
        if cv2 is not None and (pix.width != int(width) or pix.height != int(height)):
            img = cv2.resize(img, (int(width), int(height)), interpolation=cv2.INTER_AREA)
        return img
    except Exception:
        return None


def calculate_error(img_orig, img_rendered) -> float:
    if np is None or img_orig is None or img_rendered is None:
        return float("inf")
    if img_orig.shape[:2] != img_rendered.shape[:2]:
        if cv2 is None:
            return float("inf")
        img_rendered = cv2.resize(img_rendered, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
    diff = img_orig.astype(np.float32) - img_rendered.astype(np.float32)
    return float(np.mean(diff * diff))


def calculate_delta2_stats(img_orig, img_rendered) -> tuple[float, float]:
    if np is None or img_orig is None or img_rendered is None:
        return float("inf"), float("inf")
    if img_orig.shape[:2] != img_rendered.shape[:2]:
        if cv2 is None:
            return float("inf"), float("inf")
        img_rendered = cv2.resize(img_rendered, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
    diff = img_orig.astype(np.float32) - img_rendered.astype(np.float32)
    delta2 = np.mean(diff * diff, axis=2)
    return float(np.mean(delta2)), float(np.std(delta2))


def create_diff_image(img_orig, img_rendered):
    if np is None or img_orig is None or img_rendered is None:
        return img_orig
    if img_orig.shape[:2] != img_rendered.shape[:2] and cv2 is not None:
        img_rendered = cv2.resize(img_rendered, (img_orig.shape[1], img_orig.shape[0]), interpolation=cv2.INTER_AREA)
    diff = np.abs(img_orig.astype(np.int16) - img_rendered.astype(np.int16)).astype(np.uint8)
    return diff
