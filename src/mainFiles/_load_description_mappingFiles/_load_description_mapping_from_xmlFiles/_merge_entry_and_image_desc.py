from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _merge_entry_and_image_desc(entry_desc: str, image_desc: str) -> str:
    entry_clean = str(entry_desc or "").strip()
    image_clean = str(image_desc or "").strip()
    if entry_clean and image_clean and entry_clean != image_clean:
        return f"{entry_clean} {image_clean}".strip()
    return image_clean or entry_clean
