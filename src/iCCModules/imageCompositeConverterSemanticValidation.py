"""Extracted semantic validation helpers for imageCompositeConverter."""

from __future__ import annotations

from typing import Any


def expectedSemanticPresenceImpl(semantic_elements: list[str]) -> dict[str, bool]:
    """Return expected primitive presence from normalized semantic element labels."""
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


def semanticPresenceMismatchesImpl(expected: dict[str, bool], observed: dict[str, bool]) -> list[str]:
    """Return mismatch diagnostics between expected and observed semantic primitives."""
    labels = {
        "circle": "Kreis",
        "stem": "senkrechter Strich",
        "arm": "waagrechter Strich",
        "text": "Buchstabe/Text",
    }
    issues: list[str] = []
    for key in ("circle", "stem", "arm", "text"):
        exp = bool(expected.get(key, False))
        obs = bool(observed.get(key, False))
        if exp and not obs:
            issues.append(f"Beschreibung erwartet {labels[key]}, im Bild aber nicht robust erkennbar")
        if obs and not exp:
            issues.append(f"Im Bild ist {labels[key]} erkennbar, aber nicht in der Beschreibung enthalten")
    return issues


def observedSemanticPresenceFromShapeDetectionImpl(img_orig: Any | None) -> dict[str, bool]:
    """Infer observable semantic primitives via shape-detection helpers (best effort)."""
    observed = {"circle": False, "stem": False, "arm": False, "text": False}
    if img_orig is None:
        return observed
    try:
        from tools.shape_detection_eval import detect_primitive_label
    except Exception:
        return observed

    try:
        primitive = str(detect_primitive_label(img_orig)).lower()
    except Exception:
        return observed

    if primitive == "circle":
        observed["circle"] = True
    elif primitive == "line":
        observed["stem"] = True
    elif primitive == "rectangle":
        observed["arm"] = True
    elif primitive == "arrow":
        observed["arm"] = True
    return observed
