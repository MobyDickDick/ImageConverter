from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _froeground_mask(img: np.ndarray) -> np.ndarray:
    """Backward-compatible typo alias for `_foreground_mask`."""
    return _foreground_mask(img)
