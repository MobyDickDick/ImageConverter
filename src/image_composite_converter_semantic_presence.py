"""Semantic presence expectation/mismatch helpers extracted from the monolith."""

from __future__ import annotations


SEMANTIC_LABELS: dict[str, str] = {
    "circle": "Kreis",
    "stem": "senkrechter Strich",
    "arm": "waagrechter Strich",
    "text": "Buchstabe/Text",
}


def expected_semantic_presence_impl(semantic_elements: list[str]) -> dict[str, bool]:
    normalized = [str(elem).lower() for elem in semantic_elements]
    has_text = any(
        ("kreis + buchstabe" in elem)
        or (("buchstab" in elem) and ("ohne buchstabe" not in elem))
        or ("voc" in elem)
        or ("co_2" in elem)
        or ("co₂" in elem)
        for elem in normalized
    )
    has_circle = any("kreis" in elem for elem in normalized)
    return {
        "circle": has_circle,
        "stem": any("senkrechter strich" in elem for elem in normalized),
        "arm": any("waagrechter strich" in elem for elem in normalized),
        "text": has_text,
    }


def semantic_presence_mismatches_impl(expected: dict[str, bool], observed: dict[str, bool]) -> list[str]:
    issues: list[str] = []
    for key in ("circle", "stem", "arm", "text"):
        exp = bool(expected.get(key, False))
        obs = bool(observed.get(key, False))
        if exp and not obs:
            issues.append(f"Beschreibung erwartet {SEMANTIC_LABELS[key]}, im Bild aber nicht robust erkennbar")
        if obs and not exp:
            issues.append(f"Im Bild ist {SEMANTIC_LABELS[key]} erkennbar, aber nicht in der Beschreibung enthalten")
    return issues
