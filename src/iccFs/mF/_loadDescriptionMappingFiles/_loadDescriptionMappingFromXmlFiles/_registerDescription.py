def _register_description(raw_desc: dict[str, str], key: str, description: str) -> None:
    normalized_desc = str(description or "").strip()
    if not normalized_desc:
        return

    stripped_key = str(key or "").strip()
    key_base = get_base_name_from_file(stripped_key)
    key_stem = os.path.splitext(stripped_key)[0]

    for candidate in {
        stripped_key,
        stripped_key.upper(),
        stripped_key.lower(),
        key_base,
        key_base.upper(),
        key_base.lower(),
        key_stem,
        key_stem.upper(),
        key_stem.lower(),
    }:
        if candidate:
            raw_desc[candidate] = normalized_desc
