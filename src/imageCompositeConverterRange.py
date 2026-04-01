"""Extracted range-filter helpers for imageCompositeConverter."""

from __future__ import annotations

import os
import re
from collections.abc import Callable


def extractRefPartsImpl(name: str) -> tuple[str, int] | None:
    match = re.match(r"^([A-Z]{2,3})(\d{3,4})$", name.upper())
    if not match:
        return None
    return match.group(1), int(match.group(2))


def normalizeRangeTokenImpl(value: str, get_base_name_fn: Callable[[str], str]) -> str:
    base = get_base_name_fn(str(value or "").upper())
    return re.sub(r"[^A-Z0-9]", "", base)


def normalizeExplicitRangeTokenImpl(value: str) -> str:
    raw = os.path.splitext(str(value or "").upper())[0]
    return re.sub(r"[^A-Z0-9]", "", raw)


def isExplicitSizeVariantTokenImpl(token: str) -> bool:
    return bool(re.match(r"^[A-Z]{2,3}\d{4}(?:[1-9]|[1-9]S|L|M|S|W|X)$", token))


def compactRangeTokenImpl(value: str, normalize_range_token_fn: Callable[[str], str]) -> str:
    token = normalize_range_token_fn(value)
    match = re.match(r"^([A-Z]+)(\d+)$", token)
    if not match:
        return token
    letters, digits = match.groups()
    return f"{letters[0]}{digits}"


def sharedPartialRangeTokenImpl(
    start_ref: str,
    end_ref: str,
    normalize_range_token_fn: Callable[[str], str],
    compact_range_token_fn: Callable[[str], str],
) -> str:
    start_token = normalize_range_token_fn(start_ref)
    end_token = normalize_range_token_fn(end_ref)
    compact_start = compact_range_token_fn(start_ref)
    compact_end = compact_range_token_fn(end_ref)
    if not start_token or not end_token:
        return ""
    for left, right in ((start_token, end_token), (compact_start, compact_end)):
        if left and left == right:
            return left
        if left and left in right:
            return left
        if right and right in left:
            return right

        max_len = min(len(left), len(right))
        for length in range(max_len, 2, -1):
            for idx in range(0, len(left) - length + 1):
                candidate = left[idx : idx + length]
                if candidate in right:
                    return candidate
    return ""


def matchesPartialRangeTokenImpl(
    filename: str,
    start_ref: str,
    end_ref: str,
    shared_partial_range_token_fn: Callable[[str, str], str],
    normalize_range_token_fn: Callable[[str], str],
    get_base_name_fn: Callable[[str], str],
) -> bool:
    token = shared_partial_range_token_fn(start_ref, end_ref)
    if not token:
        return False
    stem = normalize_range_token_fn(get_base_name_fn(os.path.splitext(filename)[0]))
    if not stem:
        return False
    if token in stem:
        return True

    pos = 0
    for char in stem:
        if pos < len(token) and char == token[pos]:
            pos += 1
    return pos == len(token)


def extractSymbolFamilyImpl(name: str) -> str | None:
    """Extract 2-3 letter corpus family prefixes such as AC, GE, DLG, or NAV."""
    match = re.match(r"^([A-Z]{2,3})\d{3,4}$", str(name).upper())
    if not match:
        return None
    return match.group(1)


def matchesExactPrefixFilterImpl(
    filename: str,
    start_ref: str,
    end_ref: str,
    normalize_range_token_fn: Callable[[str], str],
    normalize_explicit_range_token_fn: Callable[[str], str],
    is_explicit_size_variant_token_fn: Callable[[str], bool],
    get_base_name_fn: Callable[[str], str],
) -> bool:
    start_token = normalize_range_token_fn(start_ref)
    end_token = normalize_range_token_fn(end_ref)
    if not start_token or start_token != end_token:
        return False
    explicit_start = normalize_explicit_range_token_fn(start_ref)
    explicit_end = normalize_explicit_range_token_fn(end_ref)
    explicit_stem = normalize_explicit_range_token_fn(filename)
    if (
        explicit_start
        and explicit_start == explicit_end
        and is_explicit_size_variant_token_fn(explicit_start)
        and explicit_start != start_token
    ):
        return explicit_stem == explicit_start
    stem = normalize_range_token_fn(get_base_name_fn(os.path.splitext(filename)[0]))
    if not stem:
        return False
    return stem.startswith(start_token)


def inRequestedRangeImpl(
    filename: str,
    start_ref: str,
    end_ref: str,
    get_base_name_fn: Callable[[str], str],
    extract_ref_parts_fn: Callable[[str], tuple[str, int] | None],
    normalize_explicit_range_token_fn: Callable[[str], str],
    normalize_range_token_fn: Callable[[str], str],
    matches_exact_prefix_filter_fn: Callable[[str, str, str], bool],
    is_explicit_size_variant_token_fn: Callable[[str], bool],
    matches_partial_range_token_fn: Callable[[str, str, str], bool],
) -> bool:
    stem = get_base_name_fn(os.path.splitext(filename)[0]).upper()
    stem_parts = extract_ref_parts_fn(stem)
    start_parts = extract_ref_parts_fn(start_ref)
    end_parts = extract_ref_parts_fn(end_ref)
    explicit_start = normalize_explicit_range_token_fn(start_ref)
    explicit_end = normalize_explicit_range_token_fn(end_ref)
    normalized_start = normalize_range_token_fn(start_ref)

    exact_prefix_match = matches_exact_prefix_filter_fn(filename, start_ref, end_ref)
    if exact_prefix_match:
        return True
    if (
        explicit_start
        and explicit_start == explicit_end
        and is_explicit_size_variant_token_fn(explicit_start)
        and normalized_start
        and explicit_start != normalized_start
    ):
        return False

    if start_parts is None and end_parts is None:
        return matches_partial_range_token_fn(filename, start_ref, end_ref) if (start_ref or end_ref) else True

    if stem_parts is None:
        if start_parts is not None and end_parts is not None:
            start_key = start_parts
            end_key = end_parts
            if start_key > end_key:
                start_key, end_key = end_key, start_key
            return start_key[0] != end_key[0]
        return False

    if start_parts is None:
        return stem_parts <= end_parts  # type: ignore[operator]
    if end_parts is None:
        return start_parts <= stem_parts

    start_key = start_parts
    end_key = end_parts
    if start_key > end_key:
        start_key, end_key = end_key, start_key

    return start_key <= stem_parts <= end_key
