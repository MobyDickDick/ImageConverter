from __future__ import annotations

import os


_VALID_IMAGE_EXTENSIONS = (".bmp", ".jpg", ".png", ".gif")


def normalizeSelectedVariantsImpl(selected_variants: set[str] | None) -> set[str]:
    return {str(variant).upper() for variant in (selected_variants or set()) if str(variant).strip()}


def listRequestedImageFilesImpl(
    folder_path: str,
    start_ref: str,
    end_ref: str,
    *,
    selected_variants: set[str] | None,
    in_requested_range_fn,
) -> tuple[set[str], list[str]]:
    normalized_selected_variants = normalizeSelectedVariantsImpl(selected_variants)
    files = sorted(
        filename
        for filename in os.listdir(folder_path)
        if filename.lower().endswith(_VALID_IMAGE_EXTENSIONS)
        and in_requested_range_fn(filename, start_ref, end_ref)
        and (
            not normalized_selected_variants
            or os.path.splitext(filename)[0].upper() in normalized_selected_variants
        )
    )
    return normalized_selected_variants, files
