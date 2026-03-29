def _in_requested_range(filename: str, start_ref: str, end_ref: str) -> bool:
    matched, _reason = _in_requested_range_with_reason(filename, start_ref, end_ref)
    return matched


def _in_requested_range_with_reason(filename: str, start_ref: str, end_ref: str) -> tuple[bool, str]:
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
        return True, "exact_prefix_filter"
    if start_token and start_token == end_token:
        return False, "identical_partial_token_rejected"

    # If no parseable range bounds are provided, fall back to a shared partial
    # token filter. This keeps interactive batches small, e.g. AC08..A08 -> A08*.
    if start_parts is None and end_parts is None:
        if not (start_ref or end_ref):
            return True, "no_bounds_all_files"
        partial_match = _matches_partial_range_token(filename, start_ref, end_ref)
        return partial_match, "partial_token_match" if partial_match else "partial_token_miss"

    # Files that do not follow the usual XX0000 / XXX0000 naming scheme should
    # only pass through broad whole-folder spans, not exact family-specific
    # filters like AC0811..AC0811.
    if stem_parts is None:
        if start_parts is not None and end_parts is not None:
            start_key = start_parts
            end_key = end_parts
            if start_key > end_key:
                start_key, end_key = end_key, start_key
            cross_prefix = start_key[0] != end_key[0]
            return cross_prefix, "nonstandard_stem_cross_prefix_span" if cross_prefix else "nonstandard_stem_rejected"
        return False, "nonstandard_stem_rejected"

    # Support one-sided range filters if only one boundary can be parsed.
    if start_parts is None:
        matched = stem_parts <= end_parts  # type: ignore[operator]
        return matched, "upper_bound_match" if matched else "upper_bound_miss"
    if end_parts is None:
        matched = start_parts <= stem_parts
        return matched, "lower_bound_match" if matched else "lower_bound_miss"

    start_key = start_parts
    end_key = end_parts
    if start_key > end_key:
        start_key, end_key = end_key, start_key

    matched = start_key <= stem_parts <= end_key
    return matched, "range_match" if matched else "range_miss"


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
