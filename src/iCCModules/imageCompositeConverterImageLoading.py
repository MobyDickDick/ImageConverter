from __future__ import annotations

from pathlib import Path


def loadGrayscaleImageImpl(path: Path, *, import_with_vendored_fallback_fn) -> list[list[int]]:
    image_module = import_with_vendored_fallback_fn("PIL.Image")
    gray = image_module.open(path).convert("L")
    w, h = gray.size
    px = gray.load()
    return [[int(px[x, y]) for x in range(w)] for y in range(h)]


def loadBinaryImageWithModeImpl(
    path: Path,
    *,
    threshold: int = 220,
    mode: str = "global",
    load_grayscale_image_fn,
    compute_otsu_threshold_fn,
    adaptive_threshold_fn,
) -> list[list[int]]:
    grayscale = load_grayscale_image_fn(path)
    selected_mode = str(mode).lower()
    if selected_mode == "global":
        return [[1 if value < threshold else 0 for value in row] for row in grayscale]
    if selected_mode == "otsu":
        otsu_threshold = compute_otsu_threshold_fn(grayscale)
        return [[1 if value < otsu_threshold else 0 for value in row] for row in grayscale]
    if selected_mode == "adaptive":
        return adaptive_threshold_fn(grayscale)
    raise ValueError(f"Unknown threshold mode '{mode}'.")
