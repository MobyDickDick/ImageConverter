def _in_requested_range(filename: str, start_ref: str, end_ref: str) -> bool:
    start_ref, end_ref = _normalize_range_bounds(start_ref, end_ref)
    stem = get_base_name_from_file(os.path.splitext(filename)[0]).upper()
    stem_parts = _extract_ref_parts(stem)
    start_parts = _extract_ref_parts(start_ref)
    end_parts = _extract_ref_parts(end_ref)
    start_token = _normalize_range_token(start_ref)
    end_token = _normalize_range_token(end_ref)

    # Identical start/end filters should also work as a prefix selector so an
    # input like AC081..AC081 includes AC0814_L, AC0813_M, etc.
    if _matches_exact_prefix_filter(filename, start_ref, end_ref):
        return True
    if start_token and start_token == end_token:
        return False

    # If no parseable range bounds are provided, fall back to a shared partial
    # token filter. This keeps interactive batches small, e.g. AC08..A08 -> A08*.
    if start_parts is None and end_parts is None:
        return _matches_partial_range_token(filename, start_ref, end_ref) if (start_ref or end_ref) else True

    # Files that do not follow the usual XX0000 / XXX0000 naming scheme should
    # only pass through broad whole-folder spans, not exact family-specific
    # filters like AC0811..AC0811.
    if stem_parts is None:
        if start_parts is not None and end_parts is not None:
            start_key = start_parts
            end_key = end_parts
            if start_key > end_key:
                start_key, end_key = end_key, start_key
            return start_key[0] != end_key[0]
        return False

    # Support one-sided range filters if only one boundary can be parsed.
    if start_parts is None:
        return stem_parts <= end_parts  # type: ignore[operator]
    if end_parts is None:
        return start_parts <= stem_parts

    start_key = start_parts
    end_key = end_parts
    if start_key > end_key:
        start_key, end_key = end_key, start_key

    return start_key <= stem_parts <= end_key


def _normalize_range_bounds(start_ref: str, end_ref: str) -> tuple[str, str]:
    start_value = str(start_ref or "").strip()
    end_value = str(end_ref or "").strip()

    # Accept shorthand console input such as "AC080 - AC080" entered in one field.
    if (not end_value) and start_value:
        split = re.split(r"\s*(?:-|–|—|BIS|TO|\.{2,3})\s*", start_value, maxsplit=1, flags=re.IGNORECASE)
        if len(split) == 2 and split[0].strip() and split[1].strip():
            start_value, end_value = split[0].strip(), split[1].strip()

    # Tolerate separators accidentally kept in one side (e.g. "- AC080").
    start_value = re.sub(r"^\s*(?:-|–|—|BIS|TO|\.{2,3})\s*", "", start_value, flags=re.IGNORECASE).strip()
    end_value = re.sub(r"^\s*(?:-|–|—|BIS|TO|\.{2,3})\s*", "", end_value, flags=re.IGNORECASE).strip()
    start_value = re.sub(r"\s*(?:-|–|—|BIS|TO|\.{2,3})\s*$", "", start_value, flags=re.IGNORECASE).strip()
    end_value = re.sub(r"\s*(?:-|–|—|BIS|TO|\.{2,3})\s*$", "", end_value, flags=re.IGNORECASE).strip()

    return start_value, end_value
