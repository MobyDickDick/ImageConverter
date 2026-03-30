from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _find_image_path_by_variant(folder_path: str, variant: str) -> str | None:
    """Return the raster image path for ``variant`` if present."""
    for ext in ('.jpg', '.png', '.bmp', '.gif'):
        candidate = os.path.join(folder_path, f'{variant}{ext}')
        if os.path.exists(candidate):
            return candidate
    return None
