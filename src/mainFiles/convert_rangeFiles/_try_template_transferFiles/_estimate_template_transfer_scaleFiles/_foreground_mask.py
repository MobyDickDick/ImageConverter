def _foreground_mask(img: np.ndarray) -> np.ndarray:
    """Return a robust foreground mask for badge-like dark strokes on bright backgrounds."""
    if img is None:
        return np.zeros((0, 0), dtype=bool)

    arr = np.asarray(img)
    if arr.ndim == 2:
        gray = arr.astype(np.uint8, copy=False)
    else:
        # BGR -> gray (OpenCV convention)
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)

    # Badge inputs are typically dark content on a bright background.
    # Otsu gives a stable split while keeping anti-aliased edge pixels.
    _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # Keep very faint anti-aliased edge pixels that Otsu may miss.
    soft_dark = gray <= int(min(250, max(0, np.percentile(gray, 97))))

    fg = (otsu_inv > 0) | soft_dark

    # Remove obvious speckle noise but preserve thin rings.
    if fg.any():
        kernel = np.ones((2, 2), dtype=np.uint8)
        fg_u8 = fg.astype(np.uint8)
        fg_u8 = cv2.morphologyEx(fg_u8, cv2.MORPH_OPEN, kernel)
        fg = fg_u8.astype(bool)

    return fg
