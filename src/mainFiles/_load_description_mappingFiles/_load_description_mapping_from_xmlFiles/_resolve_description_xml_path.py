from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _resolve_description_xml_path(path: str) -> str | None:
    candidate = Path(path)
    if candidate.exists():
        return str(candidate)

    basename = candidate.name
    if not basename:
        return None

    fallback_candidates = [
        Path("artifacts/descriptions") / basename,
        Path("artifacts/images_to_convert") / basename,
    ]
    for fallback in fallback_candidates:
        if fallback.exists():
            return str(fallback)
    return None
