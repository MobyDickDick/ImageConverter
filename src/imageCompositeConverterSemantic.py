from __future__ import annotations

import re


SEMANTIC_BADGE_FAMILIES: set[str] = {
    "AR0100",
    "AC0800",
    "AC0811",
    "AC0810",
    "AC0812",
    "AC0813",
    "AC0814",
    "AC0820",
    "AC0831",
    "AC0832",
    "AC0833",
    "AC0834",
    "AC0835",
    "AC0836",
    "AC0837",
    "AC0838",
    "AC0839",
    "AC0870",
    "AC0881",
    "AC0882",
}


def extract_documented_alias_refs(text: str) -> set[str]:
    """Extract explicit "Wie AC0000" style alias references from descriptions."""
    if not text:
        return set()

    return {
        match.upper()
        for match in re.findall(r"\bwie(?:\s+in)?\s+([a-z]{2}\d{3,4})\b", text, flags=re.IGNORECASE)
    }


def parse_semantic_badge_layout_overrides(text: str) -> dict[str, float | str]:
    """Extract optional layout directives from semantic badge descriptions."""
    if not text:
        return {}

    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    overrides: dict[str, float | str] = {}

    if re.search(r"\bco\b[^.\n]*vertikal\s+zentriert", normalized):
        overrides["co2_dy"] = 0.0
        overrides["co2_optical_bias"] = 0.0

    if re.search(r"\bco(?:[_\s-]*2|₂)\b[^.\n]*horizontal\s+zentriert", normalized):
        overrides["co2_anchor_mode"] = "cluster"
        overrides["co2_dx"] = 0.0

    return overrides


def apply_semantic_badge_family_rules(
    *,
    base_upper: str,
    symbol_upper: str,
    desc: str,
    params: dict[str, object],
) -> bool:
    """Fill semantic-badge params for known AC08/AR0100 family descriptions."""
    if base_upper not in SEMANTIC_BADGE_FAMILIES:
        return False

    params["mode"] = "semantic_badge"
    family_elements: list[str] = []
    heuristic_elements: list[str] = []

    if base_upper in {"AC0800", "AC0810", "AC0811", "AC0812", "AC0813", "AC0814"}:
        family_elements.append("SEMANTIC: Kreis ohne Buchstabe")
        params["label"] = ""
    elif re.search(r"\bco(?:[_\s\-\^]*2|₂)\b", desc):
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO_2")
        params["label"] = "CO_2"
    elif re.search(r"\bco\b", desc):
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO")
        params["label"] = "CO"
    elif "voc" in desc:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe VOC")
        params["label"] = "VOC"
    elif "buchstabe" in desc:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
        params["label"] = "M" if symbol_upper == "AR0100" else "T"
    else:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
        params["label"] = "M" if base_upper == "AR0100" else "T"

    if base_upper in {"AC0810", "AC0814", "AC0834", "AC0838", "AC0839"}:
        family_elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")
    if base_upper in {"AC0811", "AC0881", "AC0831", "AC0836"}:
        family_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")
    if base_upper in {"AC0813", "AC0833"}:
        family_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
    if base_upper in {"AC0812", "AC0832", "AC0837", "AC0882"}:
        family_elements.append("SEMANTIC: waagrechter Strich links vom Kreis")

    if "waagrechter strich rechts" in desc:
        heuristic_elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")
    if "senkrechter strich oben" in desc:
        heuristic_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
    if "senkrechter strich hinter" in desc:
        heuristic_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")

    params["semantic_sources"] = {
        "family_rule": list(dict.fromkeys(family_elements)),
        "description_heuristic": list(dict.fromkeys(heuristic_elements)),
    }
    elements = params.setdefault("elements", [])
    if isinstance(elements, list):
        elements.extend(params["semantic_sources"]["family_rule"])
        for element in params["semantic_sources"]["description_heuristic"]:
            if element not in elements:
                elements.append(element)

    layout_overrides = parse_semantic_badge_layout_overrides(desc)
    if layout_overrides:
        params["badge_overrides"] = layout_overrides
        params["semantic_sources"]["layout_override"] = sorted(layout_overrides)
        if isinstance(elements, list):
            elements.append("SEMANTIC: Layout-Override für Badge-Text")

    return True
