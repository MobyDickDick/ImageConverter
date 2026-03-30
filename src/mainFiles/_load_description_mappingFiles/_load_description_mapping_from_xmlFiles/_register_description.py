from src import image_composite_converter as _icc

globals().update(vars(_icc))

def _register_description(raw_desc: dict[str, str], key: str, description: str) -> None:
    normalized_desc = str(description or "").strip()
    if not normalized_desc:
        return

    normalized_key = str(key or "").strip()
    stem = get_base_name_from_file(normalized_key)
    plain_stem = os.path.splitext(normalized_key)[0]
    for candidate in {
        normalized_key,
        normalized_key.upper(),
        normalized_key.lower(),
        stem,
        stem.upper(),
        stem.lower(),
        plain_stem,
        plain_stem.upper(),
        plain_stem.lower(),
    }:
        if candidate:
            raw_desc[candidate] = normalized_desc
