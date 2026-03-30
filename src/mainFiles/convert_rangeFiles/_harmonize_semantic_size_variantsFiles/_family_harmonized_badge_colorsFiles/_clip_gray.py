from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _clip_gray(value: float) -> int:
    return int(max(0, min(255, round(float(value)))))
