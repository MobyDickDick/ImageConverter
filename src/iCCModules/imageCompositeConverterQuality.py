"""Extracted semantic quality marker helpers for imageCompositeConverter."""

from __future__ import annotations

import re
from collections.abc import Callable


def semanticQualityFlagsImpl(
    base_name: str,
    validation_logs: list[str],
    get_base_name_fn: Callable[[str], str],
) -> list[str]:
    """Derive non-fatal quality markers from semantic element-validation logs."""
    if get_base_name_fn(base_name).upper() != "AC0811":
        return []

    error_pattern = re.compile(r"^(circle|stem|arm|text): Fehler=([0-9]+(?:\.[0-9]+)?)$")
    element_errors: dict[str, float] = {}
    for entry in validation_logs:
        match = error_pattern.match(str(entry).strip())
        if not match:
            continue
        element_errors[match.group(1)] = float(match.group(2))

    if not element_errors:
        return []

    highest_element, highest_error = max(element_errors.items(), key=lambda item: item[1])
    elevated = [name for name, value in element_errors.items() if value >= 8.0]

    if highest_error < 10.0 and len(elevated) < 2:
        return []

    markers = [
        "quality=borderline",
        (
            "quality_reason="
            f"semantic_ok_trotz_hohem_elementfehler:{highest_element}={highest_error:.3f}"
        ),
    ]
    if elevated:
        markers.append("quality_elevated_elements=" + ",".join(sorted(elevated)))
    return markers
