def _in_requested_range(filename: str, start_ref: str, end_ref: str) -> bool:
    stem = get_base_name_from_file(os.path.splitext(filename)[0]).upper()
    stem_parts = _extract_ref_parts(stem)
    start_parts = _extract_ref_parts(start_ref)
    end_parts = _extract_ref_parts(end_ref)

    # Identical start/end filters should also work as a prefix selector so an
    # input like AC081..AC081 includes AC0814_L, AC0813_M, etc.
    if _matches_exact_prefix_filter(filename, start_ref, end_ref):
        return True

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
