def _matches_exact_prefix_filter(filename: str, start_ref: str, end_ref: str) -> bool:
    start_token = _normalize_range_token(start_ref)
    end_token = _normalize_range_token(end_ref)
    if not start_token or start_token != end_token:
        return False
    stem = _normalize_range_token(get_base_name_from_file(os.path.splitext(filename)[0]))
    if not stem:
        return False
    match = re.match(r"^([A-Z]{2,3})(\d{3})$", start_token)
    if match and match.group(2).endswith("0"):
        return stem == f"{match.group(1)}{match.group(2)}0"
    return stem.startswith(start_token)
""" End move to File mainFiles/convert_rangeFiles/_in_requested_rangeFiles/_matches_exact_prefix_filter.py """


""" Start move to File mainFiles/convert_rangeFiles/_in_requested_range.py
import src
"""
def _in_requested_range(filename: str, start_ref: str, end_ref: str) -> bool:
    start_ref = re.sub(r"^\s*[-–—]+\s*", "", str(start_ref or "")).strip()
    end_ref = re.sub(r"^\s*[-–—]+\s*", "", str(end_ref or "")).strip()
    if not str(end_ref or "").strip():
        match = re.match(r"^\s*(.+?)\s*-\s*(.+?)\s*$", str(start_ref or ""))
        if match:
            start_ref, end_ref = match.group(1).strip(), match.group(2).strip()

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
""" End move to File mainFiles/convert_rangeFiles/_in_requested_range.py """




""" Start move to File mainFiles/convert_rangeFiles/_conversion_random.py
import src
"""
def _conversion_random() -> random.Random:
    """Return run-local RNG (seedable via env) for non-deterministic search order."""
    seed_raw = os.environ.get("TINY_ICC_RANDOM_SEED")
    if seed_raw is not None and str(seed_raw).strip() != "":
        try:
            return random.Random(int(str(seed_raw).strip()))
        except ValueError:
            pass
    return random.Random(time.time_ns())
""" End move to File mainFiles/convert_rangeFiles/_conversion_random.py """

""" Start move to File mainFiles/convert_rangeFiles/_default_converted_symbols_root.py
import src
"""
def _default_converted_symbols_root() -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(repo_root, "artifacts", "converted_images")
""" End move to File mainFiles/convert_rangeFiles/_default_converted_symbols_root.py """


""" Start move to File mainFiles/convert_rangeFiles/_converted_svg_output_dir.py
import src
"""
def _converted_svg_output_dir(output_root: str) -> str:
    return os.path.join(output_root, "converted_svgs")
""" End move to File mainFiles/convert_rangeFiles/_converted_svg_output_dir.py """
