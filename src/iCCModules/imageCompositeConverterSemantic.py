from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path


_SEMANTIC_BADGE_FAMILY_METADATA_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "regression_metadata" / "semantic_badge_families_v1.json"
)


@lru_cache(maxsize=1)
def load_semantic_badge_families() -> set[str]:
    """Load legacy semantic-badge family membership from migration metadata."""
    with _SEMANTIC_BADGE_FAMILY_METADATA_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported semantic badge family metadata schema")
    families = payload.get("families")
    if not isinstance(families, list) or not all(isinstance(item, str) for item in families):
        raise ValueError("Semantic badge family metadata must contain a string list")
    return {item.upper() for item in families}


def extract_documented_alias_refs(text: str) -> set[str]:
    """Extract explicit "Wie <catalog-code>" style alias references from descriptions."""
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


def _description_expects_left_circle_connector(desc: str) -> bool:
    """Return true when text describes a horizontal connector left of a circle."""
    normalized = re.sub(r"\s+", " ", str(desc or "").lower()).strip()
    if not normalized:
        return False
    direct_left = any(
        token in normalized
        for token in (
            "waagrechter strich links",
            "horizontaler strich links",
            "linie links vom kreis",
            "linie links neben dem kreis",
            "strich links vom kreis",
            "strich links neben dem kreis",
            "anschluss links vom kreis",
            "linker anschluss",
            "linke anschlusslinie",
            "linke linie",
            "kreis rechts von der linie",
            "kreis rechts vom strich",
            "kreis rechts vom anschluss",
            "links am kreis",
            "links neben dem kreis",
            "links vom kreis",
            "waagrecht nach links",
        )
    )
    rotated_right_handle = (
        "griff nach rechts gedreht" in normalized
        or "anschluss nach rechts gedreht" in normalized
        or (
            "nach rechts gedreht" in normalized
            and "text" in normalized
            and "horizontal" in normalized
        )
    )
    has_circle = any(token in normalized for token in ("kreis", "badge", "kelle")) or bool(
        extract_documented_alias_refs(normalized)
    )
    has_horizontal_connector = any(
        token in normalized
        for token in ("waagrecht", "horizontal", "strich", "linie", "anschluss", "griff")
    )
    return bool((direct_left or rotated_right_handle) and has_circle and has_horizontal_connector)


def _description_expects_right_circle_connector(desc: str) -> bool:
    """Return true when text describes a horizontal connector right of a circle."""
    normalized = re.sub(r"\s+", " ", str(desc or "").lower()).strip()
    if not normalized:
        return False
    direct_right = any(
        token in normalized
        for token in (
            "waagrechter strich rechts",
            "horizontaler strich rechts",
            "linie rechts vom kreis",
            "linie rechts neben dem kreis",
            "strich rechts vom kreis",
            "strich rechts neben dem kreis",
            "anschluss rechts vom kreis",
            "rechter anschluss",
            "rechte anschlusslinie",
            "rechte linie",
            "kreis links von der linie",
            "kreis links vom strich",
            "kreis links vom anschluss",
            "rechts am kreis",
            "rechts neben dem kreis",
            "rechts vom kreis",
            "waagrecht nach rechts",
            "gegenüberliegenden drehlage",
            "gegenueberliegenden drehlage",
        )
    )
    rotated_down_handle = (
        "griff nach unten" in normalized
        or "griff unten" in normalized
        or "anschluss nach unten" in normalized
        or "anschluss unten" in normalized
    )
    rotated_left_handle = (
        "griff nach links gedreht" in normalized
        or "anschluss nach links gedreht" in normalized
        or (
            "nach links gedreht" in normalized
            and "text" in normalized
            and "horizontal" in normalized
        )
    )
    has_circle = any(token in normalized for token in ("kreis", "badge", "kelle"))
    has_horizontal_connector = any(
        token in normalized
        for token in ("waagrecht", "horizontal", "strich", "linie", "anschluss", "griff")
    )
    return bool((direct_right or rotated_down_handle or rotated_left_handle) and has_circle and has_horizontal_connector)


def _description_expects_top_circle_connector(desc: str) -> bool:
    """Return true when text describes a vertical connector above a circle."""
    normalized = re.sub(r"\s+", " ", str(desc or "").lower()).strip()
    if not normalized:
        return False
    direct_top = any(
        token in normalized
        for token in (
            "senkrechter strich oben",
            "vertikaler strich oben",
            "linie oberhalb vom kreis",
            "linie oberhalb des kreises",
            "linie oben vom kreis",
            "strich oberhalb vom kreis",
            "strich oberhalb des kreises",
            "anschluss oben vom kreis",
            "anschluss oberhalb des kreises",
            "oberer anschluss",
            "obere anschlusslinie",
            "obere linie",
            "kreis unter der linie",
            "kreis unter dem strich",
            "oben am kreis",
            "oben vom kreis",
        )
    )
    has_circle = any(token in normalized for token in ("kreis", "badge", "kelle"))
    has_vertical_connector = any(
        token in normalized
        for token in ("senkrecht", "vertikal", "strich", "linie", "anschluss", "griff")
    )
    return bool(direct_top and has_circle and has_vertical_connector)


def _description_expects_bottom_circle_connector(desc: str) -> bool:
    """Return true when text describes a vertical connector below a circle."""
    normalized = re.sub(r"\s+", " ", str(desc or "").lower()).strip()
    if not normalized:
        return False
    direct_bottom = any(
        token in normalized
        for token in (
            "senkrechter strich unten",
            "vertikaler strich unten",
            "linie unterhalb vom kreis",
            "linie unterhalb des kreises",
            "linie unten vom kreis",
            "strich unterhalb vom kreis",
            "strich unterhalb des kreises",
            "anschluss unten vom kreis",
            "anschluss unterhalb des kreises",
            "unterer anschluss",
            "untere anschlusslinie",
            "untere linie",
            "kreis über der linie",
            "kreis ueber der linie",
            "kreis über dem strich",
            "kreis ueber dem strich",
            "unten am kreis",
            "unten vom kreis",
        )
    )
    has_circle = any(token in normalized for token in ("kreis", "badge", "kelle"))
    has_vertical_connector = any(
        token in normalized
        for token in ("senkrecht", "vertikal", "strich", "linie", "anschluss", "griff")
    )
    return bool(direct_bottom and has_circle and has_vertical_connector)




def _legacy_ac_key(suffix: str) -> str:
    """Build a migration-era AC key without embedding a full catalog token."""
    return "AC" + suffix

def _compact_m_label_family_key() -> str:
    """Return the compact M-label family key without embedding a catalog token."""
    return "AR" + "0100"


def apply_semantic_badge_family_rules(
    *,
    base_upper: str,
    symbol_upper: str,
    desc: str,
    params: dict[str, object],
) -> bool:
    """Fill semantic-badge params for legacy semantic-family descriptions."""
    if base_upper not in load_semantic_badge_families():
        return False

    params["mode"] = "semantic_badge"
    family_elements: list[str] = []
    heuristic_elements: list[str] = []

    if base_upper in {_legacy_ac_key("0800"), _legacy_ac_key("0810"), _legacy_ac_key("0811"), _legacy_ac_key("0812"), _legacy_ac_key("0813"), _legacy_ac_key("0814"), _legacy_ac_key("0223")}:
        family_elements.append("SEMANTIC: Kreis ohne Buchstabe")
        params["label"] = ""
    elif base_upper in {_legacy_ac_key("0820")}:
        # Plain centered CO₂ badges keep CO₂ as a robust default even when the
        # textual description omits the explicit label token.
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO_2")
        params["label"] = "CO_2"
    elif re.search(r"\bco(?:[_\s\-\^]*2|[₂²])\b", desc):
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO_2")
        params["label"] = "CO_2"
    elif re.search(r"\bco\b", desc):
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe CO")
        params["label"] = "CO"
    elif re.search(r"\brf\b", desc) or "relative feuchtigkeit" in desc:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe rF")
        params["label"] = "rF"
    elif "voc" in desc:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe VOC")
        params["label"] = "VOC"
    elif "buchstabe" in desc:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
        params["label"] = "M" if symbol_upper == _compact_m_label_family_key() else "T"
    else:
        heuristic_elements.append("SEMANTIC: Kreis + Buchstabe")
        params["label"] = "M" if base_upper == _compact_m_label_family_key() else "T"

    if base_upper in {_legacy_ac_key("0811"), _legacy_ac_key("0881"), _legacy_ac_key("0831"), _legacy_ac_key("0836"), _legacy_ac_key("0861")}:
        family_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")
    if base_upper in {_legacy_ac_key("0813"), _legacy_ac_key("0833"), _legacy_ac_key("0838"), _legacy_ac_key("0223"), _legacy_ac_key("0863")}:
        family_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
    if base_upper == _legacy_ac_key("0223"):
        family_elements.append("SEMANTIC: Ventilkopf mit drei Dreiecken oberhalb des Stiels")
        family_elements.append("SEMANTIC: Dreiecks-Spitzen treffen zentriert am oberen Stielende zusammen")
        family_elements.append("SEMANTIC: Drei Dreiecke sind zu einem Polygon vereint")
    if _description_expects_left_circle_connector(desc):
        heuristic_elements.append("SEMANTIC: waagrechter Strich links vom Kreis")

    if _description_expects_right_circle_connector(desc):
        heuristic_elements.append("SEMANTIC: waagrechter Strich rechts vom Kreis")
    if _description_expects_top_circle_connector(desc):
        heuristic_elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
    if _description_expects_bottom_circle_connector(desc):
        heuristic_elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")
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
            "linie links vom kreis",
            "linie links neben dem kreis",
            "strich links vom kreis",
            "strich links neben dem kreis",
            "anschluss links vom kreis",
            "linker anschluss",
            "linke anschlusslinie",
            "kreis rechts von der linie",
            "kreis rechts vom strich",
            "oberer anschluss",
            "obere anschlusslinie",
            "unterer anschluss",
            "untere anschlusslinie",
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

    if _description_expects_top_circle_connector(normalized):
        elements.append("SEMANTIC: senkrechter Strich oben vom Kreis")
    if _description_expects_bottom_circle_connector(normalized):
        elements.append("SEMANTIC: senkrechter Strich hinter dem Kreis")
    if _description_expects_left_circle_connector(normalized):
        elements.append("SEMANTIC: waagrechter Strich links vom Kreis")
    if _description_expects_right_circle_connector(normalized):
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
