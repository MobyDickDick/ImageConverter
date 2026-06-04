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
    "AC0223",
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
    "AC0842",
    "AC0844",
    "AC0850",
    "AC0861",
    "AC0862",
    "AC0863",
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

    if re.search(r"\bco(?:[_\s-]*2|[₂²])\b[^.\n]*horizontal\s+zentriert", normalized):
        overrides["co2_anchor_mode"] = "cluster"
        overrides["co2_dx"] = 0.0

    color_count_match = re.search(r"\b(?:farben|colors?)\s*[:=]?\s*(\d+)\b", normalized)
    if color_count_match:
        overrides["palette_color_count"] = str(int(color_count_match.group(1)))

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

    if base_upper in {"AC0800", "AC0810", "AC0811", "AC0812", "AC0813", "AC0814", "AC0223"}:
        family_elements.append("SEMANTIC: Kreis ohne Buchstabe")
        params["label"] = ""
    elif base_upper in {"AC0820"}:
        # AC0820 is the plain CO₂ family. Keep CO₂ as a robust default even when
        # the textual description omits the explicit label token.
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO_2")
        params["label"] = "CO_2"
    elif re.search(r"\bco(?:[_\s\-\^]*2|[₂²])\b", desc):
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO_2")
        params["label"] = "CO_2"
    elif re.search(r"\bco\b", desc):
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO")
        params["label"] = "CO"
    elif base_upper in {"AC0842", "AC0844", "AC0850", "AC0861", "AC0862", "AC0863"}:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe rF")
        params["label"] = "rF"
    elif re.search(r"\brf\b", desc) or "relative feuchtigkeit" in desc:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe rF")
        params["label"] = "rF"
    elif "voc" in desc:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe VOC")
        params["label"] = "VOC"
    elif "buchstabe" in desc:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
        params["label"] = "M" if symbol_upper == "AR0100" else "T"
    else:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
        params["label"] = "M" if base_upper == "AR0100" else "T"

    if base_upper in {"AC0810", "AC0814", "AC0834", "AC0839", "AC0844"}:
        family_elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")
    if base_upper in {"AC0811", "AC0881", "AC0831", "AC0836", "AC0861"}:
        family_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")
    if base_upper in {"AC0813", "AC0833", "AC0838", "AC0223", "AC0863"}:
        family_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
    if base_upper == "AC0223":
        family_elements.append("SEMANTIC: Ventilkopf mit drei Dreiecken oberhalb des Stiels")
        family_elements.append("SEMANTIC: Dreiecks-Spitzen treffen zentriert am oberen Stielende zusammen")
        family_elements.append("SEMANTIC: Drei Dreiecke sind zu einem Polygon vereint")
    if base_upper in {"AC0812", "AC0832", "AC0837", "AC0842", "AC0862", "AC0882"}:
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


def apply_semantic_badge_description_rules(*, desc: str, params: dict[str, object]) -> bool:
    """Infer semantic badge elements from free-form German descriptions."""
    normalized = re.sub(r"\s+", " ", str(desc or "").lower()).strip()
    if not normalized:
        return False

    geometry_ir = params.get("geometry_ir")
    if isinstance(geometry_ir, list) and any(
        str(element.get("kind", ""))
        in {
            "VerticalTwoWayValveMotorGlyph",
            "LeftRotatedTwoWayValveMotorGlyph",
            "Rotated180TwoWayValveMotorGlyph",
            "TopKelleThreeWayValveGlyph",
            "LeftRotatedTopKelleThreeWayValveGlyph",
            "RightRotatedTopKelleThreeWayValveGlyph",
            "Rotated180TopKelleThreeWayValveGlyph",
            "MainDiagonalMirroredTopKelleThreeWayValveGlyph",
        }
        for element in geometry_ir
        if isinstance(element, dict)
    ):
        return False

    has_badge_shape = any(token in normalized for token in ("kelle", "kreis", "badge"))
    has_orientation_hint = any(
        token in normalized
        for token in (
            "griff nach unten",
            "griff nach oben",
            "senkrecht nach unten",
            "senkrecht nach oben",
            "waagrecht nach links",
            "waagrecht nach rechts",
            "waagrechter strich links",
            "waagrechter strich rechts",
            "horizontale linie",
            "vertikale linie",
        )
    )
    if not has_badge_shape:
        return False

    elements: list[str] = []
    if "ohne buchstabe" in normalized:
        elements.append("SEMANTIC: Kreis ohne Buchstabe")
        params["label"] = ""
    elif any(token in normalized for token in ("\"m\"", " m ", "motor")):
        elements.append("SEMANTIC: Kreis + Buchstabe")
        params["label"] = "M"
    elif "voc" in normalized:
        elements.append("SEMANTIC: Kreis + Buchstabe VOC")
        params["label"] = "VOC"

    if "griff nach unten" in normalized or "senkrecht nach unten" in normalized:
        elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
    if "griff nach oben" in normalized or "senkrecht nach oben" in normalized:
        elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")
    if "waagrecht nach links" in normalized or "waagrechter strich links" in normalized:
        elements.append("SEMANTIC: waagrechter Strich links vom Kreis")
    if "waagrecht nach rechts" in normalized or "waagrechter strich rechts" in normalized:
        elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")

    if not elements and has_orientation_hint:
        elements.append("SEMANTIC: Kreis + Buchstabe")
        params.setdefault("label", "T")

    if not elements:
        return False

    params["mode"] = "semantic_badge"
    semantic_sources = params.setdefault("semantic_sources", {})
    if isinstance(semantic_sources, dict):
        semantic_sources["description_heuristic"] = list(dict.fromkeys(elements))

    params_elements = params.setdefault("elements", [])
    if isinstance(params_elements, list):
        for element in elements:
            if element not in params_elements:
                params_elements.append(element)
    return True
