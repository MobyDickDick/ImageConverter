from src import image_composite_converter as _icc

globals().update(vars(_icc))

def convert_image_variants(*args, **kwargs):
    """Compatibility shim kept for tooling imports."""
    return convert_range(*args, **kwargs)
