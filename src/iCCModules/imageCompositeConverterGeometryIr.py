"""Geometry-IR helpers for deterministic composite symbol reconstruction."""

from __future__ import annotations

import html
import re
from collections.abc import Iterable


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def _has_any(text: str, tokens: Iterable[str]) -> bool:
    return any(token in text for token in tokens)


def _extract_circle_badge_label(desc: str) -> str | None:
    if not _has_any(desc, ("kreis", "kreisring", "badge")):
        return None
    if _has_any(desc, ("ohne buchstabe", "ohne text", "ohne beschriftung", "ohne label", "kein buchstabe")):
        return ""
    label_patterns = (
        (r'(?:steht|text|label|buchstabe|beschriftung|glyph)[^\w]*(?:\"|\'|„|“)?(co2|co₂|voc|rf|rh|t|m)(?:\"|\'|“)?',),
        (r'(?:zentrierter|zentrierten|mittiger|mittigen)\s+(co2|co₂|voc|rf|rh|t|m)(?:-glyph|-text|-label|\b)',),
        (r'\b(co2|co₂|voc|rf|rh|t|m)\s+(?:im|in dem|innerhalb des|zentriert im|zentriert in dem)\s+kreis',),
    )
    for patterns in label_patterns:
        for pattern in patterns:
            match = re.search(pattern, desc)
            if match:
                raw = match.group(1)
                if raw == "co2":
                    return "CO₂"
                if raw == "co₂":
                    return "CO₂"
                if raw == "voc":
                    return "VOC"
                if raw in {"rf", "rh"}:
                    return "rF" if raw == "rf" else "rH"
                return raw.upper()
    return None

def buildGeometryIrFromDescriptionImpl(description: str) -> list[dict[str, object]]:
    """Map a normalized German image description to an ordered geometry IR chain.

    The IR intentionally stores normalized coordinates so later optimization can tune
    individual elements without depending on direct SVG snippets.
    """

    desc = _normalize_text(description)
    if not desc:
        return []

    elements: list[dict[str, object]] = []
    rect_hint = _has_any(desc, ("rechteck", "viereck", "kühlelement", "heizelement", "ac0120-bildbeschreibung"))
    gradient_hint = _has_any(desc, ("farbverlauf", "gradient")) and _has_any(desc, ("horizontal", "dunkel-hell-dunkel", "dunkel–hell–dunkel"))
    diagonal_hint = _has_any(desc, ("diagonal", "diagonale", "diagonalen", "andreaskreuz", "kreuz"))
    differential_pressure_hint = _has_any(desc, ("differenzdruckmessung", "dp")) and "doppelten grauen rand" in desc
    connector_free_hint = _has_any(desc, ("kreis", "kreisring")) and _has_any(
        desc,
        (
            "ohne anschluss",
            "ohne anschlusslinie",
            "anschlussfrei",
            "connector-frei",
            "connectorfrei",
            "keine griff-/leitungslinie außerhalb",
            "ohne außenanschluss",
            "ohne äussere griff",
            "ohne äußere griff",
        ),
    )
    circle_badge_label = _extract_circle_badge_label(desc)
    circle_badge_hint = (
        circle_badge_label is not None
        and _has_any(desc, ("kreis", "kreisring", "badge"))
        and (circle_badge_label != "" or connector_free_hint)
    )
    connector_free_rh_badge_hint = (
        _has_any(
            desc,
            ('steht "rh"', "steht 'rh'", "zentrierter rh-glyph", "zentrierten rh-glyph"),
        )
        and connector_free_hint
        and not circle_badge_hint
    )
    occluded_vertical_circle_connector_hint = _has_any(
        desc,
        (
            "teilweise verdeckt",
            "teilverdeckt",
            "verdeckt",
            "hinter dem kreis",
            "hinter der kreisfläche",
            "kreis überdeckt",
            "kreis verdeckt",
        ),
    )
    left_circle_connector_hint = (
        _has_any(desc, ("kreis", "kreisring"))
        and _has_any(desc, ("waagrecht", "horizontal", "linie", "strich", "anschluss", "connector"))
        and _has_any(
            desc,
            (
                "links vom kreis",
                "links neben dem kreis",
                "links an dem kreis",
                "links am kreis",
                "linker anschluss",
                "linke anschlusslinie",
                "linke linie",
                "kreis rechts von der linie",
                "kreis rechts vom strich",
                "kreis rechts vom anschluss",
                "left of the circle",
                "left connector",
            ),
        )
    )
    right_circle_connector_hint = (
        _has_any(desc, ("kreis", "kreisring"))
        and _has_any(desc, ("waagrecht", "horizontal", "linie", "strich", "anschluss", "connector"))
        and _has_any(
            desc,
            (
                "rechts vom kreis",
                "rechts neben dem kreis",
                "rechts an dem kreis",
                "rechts am kreis",
                "rechter anschluss",
                "rechte anschlusslinie",
                "rechte linie",
                "kreis links von der linie",
                "kreis links vom strich",
                "kreis links vom anschluss",
                "right of the circle",
                "right connector",
            ),
        )
    )
    top_circle_connector_hint = (
        _has_any(desc, ("kreis", "kreisring"))
        and _has_any(desc, ("senkrecht", "vertikal", "linie", "strich", "anschluss", "connector"))
        and _has_any(
            desc,
            (
                "oben vom kreis",
                "oben am kreis",
                "oberhalb des kreises",
                "oberhalb vom kreis",
                "oberer anschluss",
                "obere anschlusslinie",
                "obere linie",
                "kreis unter der linie",
                "kreis unter dem strich",
                "top of the circle",
                "top connector",
            ),
        )
    )
    bottom_circle_connector_hint = (
        _has_any(desc, ("kreis", "kreisring"))
        and _has_any(desc, ("senkrecht", "vertikal", "linie", "strich", "anschluss", "connector"))
        and _has_any(
            desc,
            (
                "unten vom kreis",
                "unten am kreis",
                "unterhalb des kreises",
                "unterhalb vom kreis",
                "unterer anschluss",
                "untere anschlusslinie",
                "untere linie",
                "kreis über der linie",
                "kreis ueber der linie",
                "kreis über dem strich",
                "kreis ueber dem strich",
                "bottom of the circle",
                "bottom connector",
            ),
        )
    )
    pump_symbol_hint = (
        "pumpensymbol" in desc and "kreis" in desc and "dreieck" in desc
    ) or _has_any(desc, ("ac0251", "ac0401"))
    pump_rotated_180_hint = pump_symbol_hint and _has_any(
        desc, ("180° gedreht", "180 grad gedreht", "um 180°", "um 180 grad")
    )
    darker_pump_circle_hint = pump_symbol_hint and _has_any(
        desc, ("kreis ein wenig dunkler", "kreis etwas dunkler")
    )
    upright_square_kelle_hint = (
        "kelle" in desc
        and _has_any(desc, ("quadrat", "viereck"))
        and not _has_any(
            desc,
            (
                "gedreht",
                "gredreht",
                "gespiegelt",
                "90°",
                "90 grad",
                "180°",
                "180 grad",
            ),
        )
    )
    vertically_mirrored_square_kelle_t_hint = (
        "kelle" in desc
        and _has_any(desc, ("vertikal gespiegelt", "senkrecht gespiegelt"))
        and _has_any(desc, ("quadrat", "viereck"))
    )
    left_rotated_square_kelle_t_hint = (
        "kelle" in desc
        and _has_any(desc, ("nach links gedreht", "90° nach links", "90 grad nach links"))
        and _has_any(desc, ("quadrat", "viereck"))
    )
    right_facing_square_kelle_p_hint = (
        _has_any(desc, ("ac0732", "ac072"))
        and _has_any(
            desc,
            (
                "nach rechts gedreht",
                "nach rechts gredreht",
                "90° nach rechts",
                "90 grad nach rechts",
            ),
        )
        and _has_any(desc, ('horizontal "p"', "horizontal 'p'", "text immer noch horizontal"))
    )
    right_rotated_square_kelle_p_hint = (
        "ac0733" in desc
        and _has_any(desc, ("nach rechts gedreht", "90° nach rechts", "90 grad nach rechts"))
        and _has_any(desc, ('horizontal "p"', "horizontal 'p'", "text immer noch horizontal"))
    )
    left_rotated_circular_damper_hint = "ac0521" in desc and _has_any(
        desc, ("nach links gedreht", "90° nach links", "90 grad nach links")
    )
    compressor_hint = _has_any(desc, ("kompressor", "kopressor"))
    upward_compressor_hint = compressor_hint and _has_any(desc, ("nach oben", "oben", "aufwärts", "aufwaerts"))
    grey_background_compressor_hint = upward_compressor_hint and _has_any(
        desc, ("grauer hintergrund", "grauem hintergrund", "grau hintergrund")
    )
    rightward_compressor_hint = compressor_hint and _has_any(desc, ("nach rechts", "rechts"))
    main_diagonal_mirrored_compressor_hint = rightward_compressor_hint and _has_any(
        desc, ("hauptdiagonal gespiegelt", "diagonal gespiegelt", "gespiegelt")
    )
    two_way_vertical_valve_hint = _has_any(desc, ("2-weg ventil", "2 weg ventil")) and _has_any(
        desc, ("kelle mit kreis", "horizontale verbindungslinie", "zwei spitze dreiecke")
    )
    left_rotated_two_way_valve_hint = two_way_vertical_valve_hint and _has_any(
        desc, ("90° nach links", "90° links", "90 grad nach links", "nach links gedreht")
    )
    rotated_180_two_way_valve_hint = two_way_vertical_valve_hint and _has_any(
        desc, ("180° gedreht", "180 grad gedreht", "um 180°", "um 180 grad")
    )
    no_m_top_kelle_hint = _has_any(
        desc, ("ohne \"m\"", "ohne 'm'", "ohne m", "kein \"m\"", "kein m")
    )
    top_kelle_family_hint = _has_any(
        desc, ("ac0231", "3-weg ventil", "3 wege ventil", "3. spitzes dreieck")
    )
    top_kelle_position_hint = _has_any(
        desc,
        (
            "kelle oben",
            "kreis oben",
            "kelle mit kreis",
            "symmetrieachse des kreises",
            "oben befindet sich eine kelle",
            "kelle mit senkrechtem",
            "kelle mit gedrehtem",
            "3. spitzes dreieck unten",
            "3. dreieck unten",
            "im uhrzeigersinn",
        ),
    )
    top_kelle_three_way_valve_hint = (
        top_kelle_family_hint and no_m_top_kelle_hint and top_kelle_position_hint
    )
    m_top_kelle_three_way_valve_hint = (
        top_kelle_family_hint
        and top_kelle_position_hint
        and not no_m_top_kelle_hint
        and _has_any(
            desc, ('"m"', "buchstaben `m`", "buchstaben m", "senkrecht geschrieben")
        )
    )
    right_rotated_top_kelle_three_way_valve_hint = top_kelle_three_way_valve_hint and _has_any(
        desc, ("90° nach rechts", "90° rechts", "90 grad nach rechts", "nach rechts gedreht")
    )
    left_rotated_m_top_kelle_three_way_valve_hint = m_top_kelle_three_way_valve_hint and _has_any(
        desc, ("90° nach links", "90° links", "90 grad nach links", "nach links gedreht")
    )
    rotated_180_m_top_kelle_three_way_valve_hint = m_top_kelle_three_way_valve_hint and _has_any(
        desc, ("180° gedreht", "180 grad gedreht", "um 180°", "um 180 grad")
    )
    main_diagonal_mirrored_m_top_kelle_three_way_valve_hint = (
        m_top_kelle_three_way_valve_hint
        and _has_any(desc, ("hauptdiagonal gespiegelt", "diagonal gespiegelt"))
    )

    if left_rotated_circular_damper_hint:
        elements.append(
            {
                "kind": "LeftRotatedCircularDamperGlyph",
                "id": "left_rotated_circular_damper",
                "circle": [0.500, 0.500, 0.455],
                "circle_fill": "#45aa5e",
                "circle_stroke": "#78957d",
                "stroke_width": 0.040,
                "blade_points": [[0.055, 0.500], [0.765, 0.155], [0.765, 0.845]],
                "blade_fill": "#f2f5f3",
                "blade_stroke": "#b4c9b8",
                "blade_stroke_width": 0.020,
            }
        )
        return elements

    if upright_square_kelle_hint:
        elements.append(
            {
                "kind": "UprightSquareKelleGlyph",
                "id": "upright_square_kelle",
                "body_bbox": [0.020, 0.040, 0.960, 0.560],
                "body_fill": "#e11e48",
                "body_stroke": "#a0a0a0",
                "body_stroke_width": 0.040,
                "connector": [[0.500, 0.600], [0.500, 1.000]],
                "connector_stroke": "#808080",
                "connector_width": 0.080,
            }
        )
        return elements

    if vertically_mirrored_square_kelle_t_hint:
        elements.append(
            {
                "kind": "VerticallyMirroredSquareKelleTGlyph",
                "id": "vertically_mirrored_square_kelle_t",
                "body_bbox": [0.020, 0.400, 0.960, 0.580],
                "body_fill": "#d92645",
                "body_stroke": "#a0a0a0",
                "body_stroke_width": 0.040,
                "connector": [[0.500, 0.000], [0.500, 0.400]],
                "connector_stroke": "#808080",
                "connector_width": 0.080,
                "label": "T",
                "label_center": [0.500, 0.660],
                "label_fill": "#dedede",
                "font_size": 0.440,
                "font_weight": "600",
            }
        )
        return elements

    if left_rotated_square_kelle_t_hint:
        elements.append(
            {
                "kind": "LeftRotatedSquareKelleTGlyph",
                "id": "left_rotated_square_kelle_t",
                "body_bbox": [0.378, 0.040, 0.467, 0.920],
                "body_fill": "#d92645",
                "body_stroke": "#a0a0a0",
                "body_stroke_width": 0.040,
                "connector": [[0.000, 0.500], [0.378, 0.500]],
                "connector_stroke": "#808080",
                "connector_width": 0.080,
                "label": "T",
                "label_center": [0.611, 0.520],
                "label_fill": "#dedede",
                "font_size": 0.440,
                "font_weight": "600",
            }
        )
        return elements

    if right_facing_square_kelle_p_hint:
        elements.append(
            {
                "kind": "RightFacingSquareKellePGlyph",
                "id": "right_facing_square_kelle_p",
                "body_bbox": [0.400, 0.040, 0.540, 0.920],
                "body_fill": "#d92645",
                "body_stroke": "#a0a0a0",
                "body_stroke_width": 0.040,
                "connector": [[0.000, 0.500], [0.400, 0.500]],
                "connector_stroke": "#808080",
                "connector_width": 0.080,
                "label": "P",
                "label_center": [0.640, 0.520],
                "label_fill": "#dedede",
                "font_size": 0.380,
                "font_weight": "600",
            }
        )
        return elements

    if right_rotated_square_kelle_p_hint:
        elements.append(
            {
                "kind": "RightRotatedSquareKellePGlyph",
                "id": "right_rotated_square_kelle_p",
                "body_bbox": [0.020, 0.389, 0.960, 0.511],
                "body_fill": "#d92645",
                "body_stroke": "#a0a0a0",
                "body_stroke_width": 0.040,
                "connector": [[0.500, 0.000], [0.500, 0.389]],
                "connector_stroke": "#808080",
                "connector_width": 0.080,
                "label": "P",
                "label_center": [0.460, 0.656],
                "label_fill": "#dedede",
                "font_size": 0.440,
                "font_weight": "600",
            }
        )
        return elements

    if main_diagonal_mirrored_m_top_kelle_three_way_valve_hint:
        elements.append(
            {
                "kind": "MainDiagonalMirroredTopKelleThreeWayValveGlyph",
                "id": "main_diagonal_mirrored_top_kelle_three_way_valve",
                "body_paths": [
                    [[0.610, 0.500], [0.455, 0.020], [0.765, 0.020]],
                    [[0.610, 0.500], [0.455, 0.980], [0.765, 0.980]],
                    [[0.610, 0.500], [0.960, 0.333], [0.960, 0.667]],
                ],
                "circle": [0.235, 0.500, 0.225],
                "connector": [[0.450, 0.500], [0.610, 0.500]],
                "label": "M",
                "label_center": [0.235, 0.500],
                "font_size": 0.320,
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.075,
            }
        )
        return elements

    if rotated_180_m_top_kelle_three_way_valve_hint:
        elements.append(
            {
                "kind": "Rotated180TopKelleThreeWayValveGlyph",
                "id": "rotated_180_top_kelle_three_way_valve",
                "body_paths": [
                    [[0.500, 0.390], [0.980, 0.545], [0.980, 0.235]],
                    [[0.500, 0.390], [0.020, 0.545], [0.020, 0.235]],
                    [[0.500, 0.390], [0.667, 0.040], [0.333, 0.040]],
                ],
                "circle": [0.500, 0.765, 0.225],
                "connector": [[0.500, 0.550], [0.500, 0.390]],
                "label": "M",
                "label_center": [0.500, 0.765],
                "font_size": 0.320,
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.075,
            }
        )
        return elements

    if left_rotated_m_top_kelle_three_way_valve_hint:
        elements.append(
            {
                "kind": "LeftRotatedTopKelleThreeWayValveGlyph",
                "id": "left_rotated_top_kelle_three_way_valve",
                "body_paths": [
                    [[0.610, 0.500], [0.455, 0.980], [0.765, 0.980]],
                    [[0.610, 0.500], [0.455, 0.020], [0.765, 0.020]],
                    [[0.610, 0.500], [0.960, 0.667], [0.960, 0.333]],
                ],
                "circle": [0.235, 0.500, 0.225],
                "connector": [[0.450, 0.500], [0.610, 0.500]],
                "label": "M",
                "label_center": [0.235, 0.500],
                "font_size": 0.320,
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.075,
            }
        )
        return elements

    if right_rotated_top_kelle_three_way_valve_hint:
        elements.append(
            {
                "kind": "RightRotatedTopKelleThreeWayValveGlyph",
                "id": "right_rotated_top_kelle_three_way_valve",
                "body_paths": [
                    [[0.610, 0.500], [0.455, 0.980], [0.765, 0.980]],
                    [[0.610, 0.500], [0.455, 0.020], [0.765, 0.020]],
                    [[0.610, 0.500], [0.960, 0.667], [0.960, 0.333]],
                ],
                # AC0224's unlabelled circular handle is substantially larger
                # than the motor-labelled handle inherited from AC0231.  Keep
                # its right edge aligned with the connector while extending the
                # circle to the left, matching the raster family at every size.
                "circle": [0.215, 0.500, 0.295],
                "connector": [[0.412, 0.500], [0.610, 0.500]],
                "label": "",
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.075,
            }
        )
        return elements

    if m_top_kelle_three_way_valve_hint:
        elements.append(
            {
                "kind": "TopKelleThreeWayValveGlyph",
                "id": "top_kelle_three_way_valve",
                "body_paths": [
                    [[0.500, 0.610], [0.020, 0.455], [0.020, 0.765]],
                    [[0.500, 0.610], [0.980, 0.455], [0.980, 0.765]],
                    [[0.500, 0.610], [0.333, 0.960], [0.667, 0.960]],
                ],
                "circle": [0.500, 0.235, 0.225],
                "connector": [[0.500, 0.450], [0.500, 0.610]],
                "label": "M",
                "label_center": [0.500, 0.235],
                "font_size": 0.320,
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.075,
            }
        )
        return elements

    if top_kelle_three_way_valve_hint:
        elements.append(
            {
                "kind": "TopKelleThreeWayValveGlyph",
                "id": "top_kelle_three_way_valve",
                "body_paths": [
                    [[0.500, 0.610], [0.020, 0.455], [0.020, 0.765]],
                    [[0.500, 0.610], [0.980, 0.455], [0.980, 0.765]],
                    [[0.500, 0.610], [0.333, 0.960], [0.667, 0.960]],
                ],
                "circle": [0.500, 0.235, 0.225],
                "connector": [[0.500, 0.450], [0.500, 0.610]],
                "label": "",
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.075,
            }
        )
        return elements

    if two_way_vertical_valve_hint:
        if rotated_180_two_way_valve_hint:
            elements.append(
                {
                    "kind": "Rotated180TwoWayValveMotorGlyph",
                    "id": "rotated_180_two_way_valve_motor",
                    "body_path": [
                        [0.975, 0.980],
                        [0.616, 0.980],
                        [0.793, 0.491],
                        [0.616, 0.020],
                        [0.975, 0.020],
                        [0.793, 0.491],
                    ],
                    "circle": [0.279, 0.499, 0.263],
                    "connector": [[0.787, 0.499], [0.540, 0.499]],
                    "label": "M",
                    "label_center": [0.279, 0.593],
                    "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                    "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                    "stroke": "#969696",
                    "connector_stroke": "#8f8f8f",
                    "text_fill": "#666666",
                    "stroke_width": 0.040,
                    "connector_width": 0.060,
                    "font_size": 0.540,
                    "font_weight": "700",
                }
            )
            return elements
        if left_rotated_two_way_valve_hint:
            elements.append(
                {
                    "kind": "LeftRotatedTwoWayValveMotorGlyph",
                    "id": "left_rotated_two_way_valve_motor",
                    "body_path": [
                        [0.980, 0.025],
                        [0.980, 0.384],
                        [0.491, 0.207],
                        [0.020, 0.384],
                        [0.020, 0.025],
                        [0.491, 0.207],
                    ],
                    "circle": [0.499, 0.721, 0.263],
                    "connector": [[0.499, 0.213], [0.499, 0.460]],
                    "label": "M",
                    "label_center": [0.499, 0.815],
                    "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                    "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                    "stroke": "#969696",
                    "connector_stroke": "#8f8f8f",
                    "text_fill": "#666666",
                    "stroke_width": 0.040,
                    "connector_width": 0.060,
                    "font_size": 0.415,
                    "font_weight": "700",
                }
            )
            return elements
        elements.append(
            {
                "kind": "VerticalTwoWayValveMotorGlyph",
                "id": "vertical_two_way_valve_motor",
                "body_path": [[0.025, 0.020], [0.384, 0.020], [0.207, 0.509], [0.384, 0.980], [0.025, 0.980], [0.207, 0.509]],
                "circle": [0.721, 0.501, 0.263],
                "connector": [[0.213, 0.501], [0.460, 0.501]],
                "label": "M",
                "label_center": [0.721, 0.595],
                "body_fill": "url(#vertical-two-way-valve-body-gradient)",
                "circle_fill": "url(#vertical-two-way-valve-circle-gradient)",
                "stroke": "#969696",
                "connector_stroke": "#8f8f8f",
                "text_fill": "#666666",
                "stroke_width": 0.040,
                "connector_width": 0.060,
                "font_size": 0.540,
                "font_weight": "700",
            }
        )
        return elements

    if circle_badge_hint:
        circle_bbox = [0.08, 0.08, 0.84, 0.84]
        if _has_any(desc, ("kleiner kreis", "kleines badge", "kleiner badge")):
            circle_bbox = [0.16, 0.16, 0.68, 0.68]
        elif _has_any(desc, ("großer kreis", "grosser kreis", "großes badge", "grosses badge")):
            circle_bbox = [0.035, 0.035, 0.93, 0.93]
        # Preserve the canonical IDs used by the established connector-free rH
        # badge path while still routing through the generic badge parser.
        canonical_rh_badge = connector_free_hint and circle_badge_label == "rH"
        circle_id = "rh_badge_circle" if canonical_rh_badge else "described_circle"
        text_id = "rh_badge_text" if canonical_rh_badge else "circle_badge_text"
        circle = {
            "kind": "CircleBackground",
            "id": circle_id,
            "bbox": circle_bbox,
            "fill": "#f2f2f2",
            "stroke": "#7f7f7f",
            "stroke_width": 0.055,
            "badge_role": "circle_text_badge",
        }
        if connector_free_hint:
            circle["connector_policy"] = "forbid"
        elements.append(circle)
        if circle_badge_label:
            font_size = 0.42 if len(circle_badge_label) <= 2 else 0.30
            elements.append(
                {
                    "kind": "TextGlyph",
                    "id": text_id,
                    "text": circle_badge_label,
                    "bbox_ref": circle_id,
                    "target_ref": circle_id,
                    "relation": "centered_in",
                    "text_position": "center",
                    "fill": "#666666",
                    "font_size": font_size,
                    "font_weight": "700",
                }
            )
        return elements

    if connector_free_rh_badge_hint:
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "rh_badge_circle",
                    "bbox": [0.035, 0.035, 0.93, 0.93],
                    "fill": "#f2f2f2",
                    "stroke": "#7f7f7f",
                    "stroke_width": 0.055,
                },
                {
                    "kind": "TextGlyph",
                    "id": "rh_badge_text",
                    "text": "rH",
                    "bbox_ref": "rh_badge_circle",
                    "fill": "#666666",
                    "font_size": 0.48,
                    "font_weight": "700",
                },
            ]
        )
        return elements

    if connector_free_hint:
        elements.append(
            {
                "kind": "CircleBackground",
                "id": "described_circle",
                "bbox": [0.08, 0.08, 0.84, 0.84],
                "fill": "#f2f2f2",
                "stroke": "#7f7f7f",
                "stroke_width": 0.055,
                "connector_policy": "forbid",
            }
        )
        return elements

    if left_circle_connector_hint:
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "described_circle",
                    "bbox": [0.30, 0.12, 0.58, 0.76],
                    "fill": "#f2f2f2",
                    "stroke": "#7f7f7f",
                    "stroke_width": 0.055,
                },
                {
                    "kind": "HorizontalRule",
                    "id": "left_circle_connector",
                    "bbox": [0.02, 0.48, 0.30, 0.08],
                    "target_ref": "described_circle",
                    "relation": "left_of",
                    "stroke": "#666666",
                    "stroke_width": 0.055,
                },
            ]
        )
        return elements

    if right_circle_connector_hint:
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "described_circle",
                    "bbox": [0.12, 0.12, 0.58, 0.76],
                    "fill": "#f2f2f2",
                    "stroke": "#7f7f7f",
                    "stroke_width": 0.055,
                },
                {
                    "kind": "HorizontalRule",
                    "id": "right_circle_connector",
                    "bbox": [0.68, 0.48, 0.30, 0.08],
                    "target_ref": "described_circle",
                    "relation": "right_of",
                    "stroke": "#666666",
                    "stroke_width": 0.055,
                },
            ]
        )
        return elements

    if top_circle_connector_hint:
        circle = {
            "kind": "CircleBackground",
            "id": "described_circle",
            "bbox": [0.18, 0.32, 0.64, 0.58],
            "fill": "#f2f2f2",
            "stroke": "#7f7f7f",
            "stroke_width": 0.055,
        }
        connector = {
            "kind": "VerticalRule",
            "id": "top_circle_connector",
            "bbox": [0.46, 0.02, 0.08, 0.42 if occluded_vertical_circle_connector_hint else 0.32],
            "target_ref": "described_circle",
            "relation": "top_of",
            "stroke": "#666666",
            "stroke_width": 0.055,
        }
        if occluded_vertical_circle_connector_hint:
            connector["continues_behind_ref"] = "described_circle"
            connector["z_order"] = "behind_target"
            elements.extend([connector, circle])
        else:
            elements.extend([circle, connector])
        return elements

    if bottom_circle_connector_hint:
        circle = {
            "kind": "CircleBackground",
            "id": "described_circle",
            "bbox": [0.18, 0.10, 0.64, 0.58],
            "fill": "#f2f2f2",
            "stroke": "#7f7f7f",
            "stroke_width": 0.055,
        }
        connector = {
            "kind": "VerticalRule",
            "id": "bottom_circle_connector",
            "bbox": [0.46, 0.56 if occluded_vertical_circle_connector_hint else 0.66, 0.08, 0.42 if occluded_vertical_circle_connector_hint else 0.32],
            "target_ref": "described_circle",
            "relation": "bottom_of",
            "stroke": "#666666",
            "stroke_width": 0.055,
        }
        if occluded_vertical_circle_connector_hint:
            connector["continues_behind_ref"] = "described_circle"
            connector["z_order"] = "behind_target"
            elements.extend([connector, circle])
        else:
            elements.extend([circle, connector])
        return elements

    if pump_symbol_hint:
        circle_fill = "#de2048" if darker_pump_circle_hint else "#e42a4f"
        triangle_points = (
            [[0.18, 0.24], [0.82, 0.24], [0.50, 0.90]]
            if pump_rotated_180_hint
            else [[0.18, 0.76], [0.82, 0.76], [0.50, 0.10]]
        )
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "pump_circle",
                    "bbox": [0.015, 0.015, 0.97, 0.97],
                    "fill": circle_fill,
                    "stroke": "#9a7d82",
                    "stroke_width": 0.018,
                },
                {
                    "kind": "PumpTriangleGlyph",
                    "id": "pump_triangle",
                    "circle_ref": "pump_circle",
                    "points": triangle_points,
                    "fill": "#e7e7e7",
                },
            ]
        )
        return elements

    if upward_compressor_hint:
        circle_fill = "#d8d8d8" if grey_background_compressor_hint else "#45aa5e"
        glyph_stroke = "#666666" if grey_background_compressor_hint else "#d7d7d7"
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "compressor_circle",
                    "bbox": [0.06, 0.06, 0.88, 0.88],
                    "fill": circle_fill,
                    "stroke": "#8d8d8d",
                    "stroke_width": 0.020,
                },
                {
                    "kind": "UpwardCompressorGlyph",
                    "id": "upward_compressor",
                    "circle_ref": "compressor_circle",
                    "left_line": [[0.28, 0.78], [0.42, 0.16]],
                    "right_line": [[0.72, 0.78], [0.58, 0.16]],
                    "stroke": glyph_stroke,
                    "stroke_width": 0.040,
                },
            ]
        )
        return elements

    if main_diagonal_mirrored_compressor_hint:
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "compressor_circle",
                    "bbox": [0.06, 0.06, 0.88, 0.88],
                    "fill": "#df2249",
                    "stroke": "#8d8d8d",
                    "stroke_width": 0.020,
                },
                {
                    "kind": "MainDiagonalMirroredCompressorGlyph",
                    "id": "main_diagonal_mirrored_compressor",
                    "circle_ref": "compressor_circle",
                    "left_line": [[0.09, 0.22], [0.39, 1.01]],
                    "right_line": [[0.91, 0.22], [0.61, 1.01]],
                    "stroke": "#f4f4f4",
                    "stroke_width": 0.032,
                },
            ]
        )
        return elements

    if rightward_compressor_hint:
        elements.extend(
            [
                {
                    "kind": "CircleBackground",
                    "id": "compressor_circle",
                    "bbox": [0.06, 0.06, 0.88, 0.88],
                    "fill": "#45aa5e",
                    "stroke": "#8d8d8d",
                    "stroke_width": 0.020,
                },
                {
                    "kind": "RightwardCompressorGlyph",
                    "id": "rightward_compressor",
                    "circle_ref": "compressor_circle",
                    "upper_line": [[0.22, 0.09], [1.01, 0.39]],
                    "lower_line": [[0.22, 0.91], [1.01, 0.61]],
                    "stroke": "#f4f4f4",
                    "stroke_width": 0.032,
                },
            ]
        )
        return elements

    if differential_pressure_hint:
        elements.extend(
            [
                {
                    "kind": "HalfDoubleRectBorder",
                    "id": "half_double_rect",
                    "bbox": [0.22, 0.38, 0.56, 0.34],
                    "fill": "none",
                    "stroke": "#777777",
                    "stroke_width": 0.024,
                    "inner_inset": 0.075,
                    "open_side": "left",
                },
                {
                    "kind": "LabelBox",
                    "id": "dp_label_box",
                    "bbox": [0.35, 0.16, 0.30, 0.20],
                    "fill": "#d7d7d7",
                    "stroke": "#777777",
                    "stroke_width": 0.020,
                },
                {
                    "kind": "TextGlyph",
                    "id": "dp_label_text",
                    "text": "dp",
                    "bbox_ref": "dp_label_box",
                    "fill": "#555555",
                    "font_size": 0.105,
                    "font_weight": "600",
                },
            ]
        )
        return elements

    if gradient_hint:
        elements.append(
            {
                "kind": "HorizontalGradient",
                "id": "background_gradient",
                "bbox": [0.18, 0.24, 0.64, 0.56],
                "stops": ["#8f8f8f", "#dedede", "#8f8f8f"],
                "constraint": "inside_rect_border",
            }
        )

    if rect_hint and "hochkant" in desc:
        for element in elements:
            if element.get("kind") == "HorizontalGradient":
                element["bbox"] = [0.32, 0.12, 0.36, 0.76]

    if rect_hint:
        rect_bbox = [0.32, 0.12, 0.36, 0.76] if "hochkant" in desc else [0.18, 0.24, 0.64, 0.56]
        elements.append(
            {
                "kind": "RectBorder",
                "id": "main_rect",
                "bbox": rect_bbox,
                "fill": "none" if gradient_hint else "#d8d8d8",
                "stroke": "#666666",
                "stroke_width": 0.035,
            }
        )

    has_horizontal_rules = _has_any(desc, ("horizontale linien", "horizontallinien")) or re.search(
        r"\bdrei\s+graue\s+horizontale\s+linien", desc
    )
    if has_horizontal_rules:
        elements.append(
            {
                "kind": "HorizontalRuleSet",
                "id": "horizontal_rule_set",
                "rect_ref": "main_rect",
                "positions": [0.30, 0.50, 0.70],
                "stroke": "#707070",
                "stroke_width": 0.026,
                "x_inset": 0.10,
            }
        )

    if re.search(r"oben[-\s]*mitte.*rechts[-\s]*mitte.*unten[-\s]*mitte", desc):
        elements.append(
            {
                "kind": "OrthogonalPolyline",
                "id": "right_side_orthogonal_line",
                "rect_ref": "main_rect",
                "points": [[0.50, 0.02], [1.02, 0.50], [0.50, 0.98]],
                "stroke": "#707070",
                "stroke_width": 0.034,
            }
        )

    directions: list[str] = []
    if diagonal_hint:
        both_diagonals = _has_any(desc, ("beiden diagonalen", "beide diagonalen", "andreaskreuz", "kreuz"))
        if both_diagonals or "ac0120-bildbeschreibung" in desc:
            directions = ["tl_br", "tr_bl"]
        elif re.search(r"oben\s+rechts.*unten\s+links|unten\s+links.*oben\s+rechts", desc):
            directions = ["tr_bl"]
        elif re.search(r"oben\s+links.*unten\s+rechts|unten\s+rechts.*oben\s+links", desc):
            directions = ["tl_br"]
        else:
            directions = ["tr_bl"]

    if _has_any(desc, ("zusätzliche", "zusätzlich", "dupliziert")) and "symmetrieachse" in desc and "tl_br" not in directions:
        directions.append("tl_br")

    for index, direction in enumerate(directions, start=1):
        elements.append(
            {
                "kind": "DiagonalBand",
                "id": f"diagonal_{index}_{direction}",
                "rect_ref": "main_rect",
                "direction": direction,
                "stroke": "#707070",
                "stroke_width": 0.045,
                "clip_to": "main_rect",
            }
        )

    glyph_position = "top_left" if "oben links" in desc else "top_center"
    has_plus = _has_any(desc, ("plus", "+", "plus-minus"))
    minus_count = len(re.findall(r'minus|["“]-["”]', desc))
    if has_plus:
        elements.append(
            {
                "kind": "PlusGlyph",
                "id": "plus_glyph",
                "position": glyph_position,
                "stroke": "#4f4f4f",
                "stroke_width": 0.025,
            }
        )
    if minus_count or _has_any(desc, ("plus-minus", "-zeichen")):
        elements.append(
            {
                "kind": "MinusGlyph",
                "id": "minus_glyph",
                "position": glyph_position,
                "stroke": "#4f4f4f",
                "stroke_width": 0.025,
            }
        )
        if "minus-minus" in desc:
            elements.append(
                {
                    "kind": "MinusGlyph",
                    "id": "minus_glyph_2",
                    "position": glyph_position,
                    "dy": 0.08,
                    "stroke": "#4f4f4f",
                    "stroke_width": 0.025,
                }
            )

    return elements


def _fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _scaled_bbox(element: dict[str, object], w: int, h: int) -> tuple[float, float, float, float]:
    raw_bbox = element.get("bbox", [0.18, 0.24, 0.64, 0.56])
    if not isinstance(raw_bbox, list) or len(raw_bbox) != 4:
        raw_bbox = [0.18, 0.24, 0.64, 0.56]
    x, y, bw, bh = [float(v) for v in raw_bbox]
    return x * w, y * h, bw * w, bh * h


def _find_rect(elements: list[dict[str, object]], w: int, h: int) -> tuple[float, float, float, float]:
    for element in elements:
        if element.get("kind") == "RectBorder":
            return _scaled_bbox(element, w, h)
    return 0.18 * w, 0.24 * h, 0.64 * w, 0.56 * h


def _find_circle(elements: list[dict[str, object]], circle_id: str, w: int, h: int) -> tuple[float, float, float, float]:
    for element in elements:
        if element.get("kind") == "CircleBackground" and str(element.get("id", "")) == circle_id:
            return _scaled_bbox(element, w, h)
    for element in elements:
        if element.get("kind") == "CircleBackground":
            return _scaled_bbox(element, w, h)
    return 0.06 * w, 0.06 * h, 0.88 * w, 0.88 * h



def _parse_hex_gray(color: str, fallback: int) -> int:
    value = str(color or "").strip().lstrip("#")
    if len(value) >= 6:
        try:
            r = int(value[0:2], 16)
            g = int(value[2:4], 16)
            b = int(value[4:6], 16)
            return int(round((r + g + b) / 3.0))
        except ValueError:
            return fallback
    return fallback


def _interpolate_gray(left: int, right: int, ratio: float) -> int:
    ratio = max(0.0, min(1.0, float(ratio)))
    return int(round(left * (1.0 - ratio) + right * ratio))


def _horizontal_gradient_rects(
    *,
    element_id: str,
    x: float,
    y: float,
    width: float,
    height: float,
    stops: list[object] | None = None,
    bands: int = 32,
) -> list[str]:
    """Approximate a horizontal 3-stop gradient with renderer-stable bands."""

    stop_values = list(stops or ["#8f8f8f", "#dedede", "#8f8f8f"])
    edge_left = _parse_hex_gray(str(stop_values[0]) if len(stop_values) >= 1 else "", 0x8F)
    center = _parse_hex_gray(str(stop_values[1]) if len(stop_values) >= 2 else "", 0xDE)
    edge_right = _parse_hex_gray(str(stop_values[2]) if len(stop_values) >= 3 else "", 0x8F)
    safe_bands = max(4, int(bands))
    rects: list[str] = [f'  <g id="{element_id}">']
    for index in range(safe_bands):
        t = (index + 0.5) / safe_bands
        if t <= 0.5:
            gray = _interpolate_gray(edge_left, center, t / 0.5)
        else:
            gray = _interpolate_gray(center, edge_right, (t - 0.5) / 0.5)
        band_x = x + width * index / safe_bands
        # A tiny overlap avoids anti-aliased seams between adjacent bands.
        band_w = width / safe_bands + max(0.02, width * 0.001)
        color = f"#{gray:02x}{gray:02x}{gray:02x}"
        rects.append(
            f'    <rect x="{_fmt(band_x)}" y="{_fmt(y)}" width="{_fmt(band_w)}" '
            f'height="{_fmt(height)}" fill="{color}" stroke="none"/>'
        )
    rects.append("  </g>")
    return rects

def renderGeometryIrToSvgElementsImpl(w: int, h: int, geometry_ir: list[dict[str, object]]) -> list[str]:
    """Render geometry IR elements as SVG fragments in their declared order."""

    svg: list[str] = []
    rect_x, rect_y, rect_w, rect_h = _find_rect(geometry_ir, w, h)
    needs_gradient = any(element.get("kind") == "HorizontalGradient" for element in geometry_ir)
    valve_gradient_kinds = {
        "VerticalTwoWayValveMotorGlyph",
        "LeftRotatedTwoWayValveMotorGlyph",
        "Rotated180TwoWayValveMotorGlyph",
        "TopKelleThreeWayValveGlyph",
        "LeftRotatedTopKelleThreeWayValveGlyph",
        "RightRotatedTopKelleThreeWayValveGlyph",
        "Rotated180TopKelleThreeWayValveGlyph",
        "MainDiagonalMirroredTopKelleThreeWayValveGlyph",
    }
    needs_vertical_valve_defs = any(element.get("kind") in valve_gradient_kinds for element in geometry_ir)
    if needs_gradient or needs_vertical_valve_defs:
        svg.append("  <defs>")
        if needs_gradient:
            svg.append('    <linearGradient id="geometry-ir-horizontal-gradient" x1="0%" y1="0%" x2="100%" y2="0%">')
            svg.append('      <stop offset="0%" stop-color="#8f8f8f"/>')
            svg.append('      <stop offset="50%" stop-color="#dedede"/>')
            svg.append('      <stop offset="100%" stop-color="#8f8f8f"/>')
            svg.append("    </linearGradient>")
        if needs_vertical_valve_defs:
            svg.append('    <linearGradient id="vertical-two-way-valve-body-gradient" x1="0%" y1="0%" x2="100%" y2="100%">')
            svg.append('      <stop offset="0%" stop-color="#a8a8a8"/>')
            svg.append('      <stop offset="100%" stop-color="#fbfbfb"/>')
            svg.append("    </linearGradient>")
            svg.append('    <linearGradient id="vertical-two-way-valve-circle-gradient" x1="0%" y1="0%" x2="100%" y2="100%">')
            svg.append('      <stop offset="0%" stop-color="#ffffff"/>')
            svg.append('      <stop offset="100%" stop-color="#f7f7f7"/>')
            svg.append("    </linearGradient>")
        svg.append("  </defs>")

    for element in geometry_ir:
        kind = str(element.get("kind", ""))
        element_id = html.escape(str(element.get("id", kind)))
        if kind == "LeftRotatedCircularDamperGlyph":
            raw_circle = element.get("circle", [0.500, 0.500, 0.455])
            if not isinstance(raw_circle, list) or len(raw_circle) != 3:
                raw_circle = [0.500, 0.500, 0.455]
            cx = float(raw_circle[0]) * w
            cy = float(raw_circle[1]) * h
            radius = float(raw_circle[2]) * min(w, h)
            circle_fill = html.escape(str(element.get("circle_fill", "#45aa5e")))
            circle_stroke = html.escape(str(element.get("circle_stroke", "#78957d")))
            circle_sw = float(element.get("stroke_width", 0.040)) * min(w, h)
            svg.append(
                f'  <circle id="{element_id}_circle" cx="{_fmt(cx)}" cy="{_fmt(cy)}" '
                f'r="{_fmt(radius)}" fill="{circle_fill}" stroke="{circle_stroke}" '
                f'stroke-width="{_fmt(circle_sw)}"/>'
            )
            raw_blade_points = element.get(
                "blade_points", [[0.055, 0.500], [0.765, 0.155], [0.765, 0.845]]
            )
            if isinstance(raw_blade_points, list) and len(raw_blade_points) == 3:
                blade_points = [
                    f"{_fmt(float(point[0]) * w)},{_fmt(float(point[1]) * h)}"
                    for point in raw_blade_points
                    if isinstance(point, list) and len(point) == 2
                ]
                if len(blade_points) == 3:
                    blade_fill = html.escape(str(element.get("blade_fill", "#f2f5f3")))
                    blade_stroke = html.escape(str(element.get("blade_stroke", "#b4c9b8")))
                    blade_sw = float(element.get("blade_stroke_width", 0.020)) * min(w, h)
                    svg.append(
                        f'  <polygon id="{element_id}_blade" points="{" ".join(blade_points)}" '
                        f'fill="{blade_fill}" stroke="{blade_stroke}" stroke-width="{_fmt(blade_sw)}" '
                        f'stroke-linejoin="round"/>'
                    )
        elif kind in {
            "UprightSquareKelleGlyph",
            "VerticallyMirroredSquareKelleTGlyph",
            "LeftRotatedSquareKelleTGlyph",
            "RightFacingSquareKellePGlyph",
            "RightRotatedSquareKellePGlyph",
        }:
            default_body_bbox = {
                "UprightSquareKelleGlyph": [0.020, 0.040, 0.960, 0.560],
                "VerticallyMirroredSquareKelleTGlyph": [0.020, 0.400, 0.960, 0.580],
                "LeftRotatedSquareKelleTGlyph": [0.378, 0.040, 0.467, 0.920],
                "RightFacingSquareKellePGlyph": [0.400, 0.040, 0.540, 0.920],
                "RightRotatedSquareKellePGlyph": [0.020, 0.389, 0.960, 0.511],
            }[kind]
            raw_body_bbox = element.get("body_bbox", default_body_bbox)
            if not isinstance(raw_body_bbox, list) or len(raw_body_bbox) != 4:
                raw_body_bbox = default_body_bbox
            body_x, body_y, body_w, body_h = (
                float(raw_body_bbox[0]) * w,
                float(raw_body_bbox[1]) * h,
                float(raw_body_bbox[2]) * w,
                float(raw_body_bbox[3]) * h,
            )
            body_fill = html.escape(str(element.get("body_fill", "#d92645")))
            body_stroke = html.escape(str(element.get("body_stroke", "#a0a0a0")))
            body_sw = float(element.get("body_stroke_width", 0.040)) * min(w, h)
            connector_stroke = html.escape(str(element.get("connector_stroke", "#808080")))
            connector_sw = float(element.get("connector_width", 0.080)) * min(w, h)
            default_connector = {
                "UprightSquareKelleGlyph": [[0.500, 0.600], [0.500, 1.000]],
                "VerticallyMirroredSquareKelleTGlyph": [[0.500, 0.000], [0.500, 0.400]],
                "LeftRotatedSquareKelleTGlyph": [[0.000, 0.500], [0.378, 0.500]],
                "RightFacingSquareKellePGlyph": [[0.000, 0.500], [0.400, 0.500]],
                "RightRotatedSquareKellePGlyph": [[0.500, 0.000], [0.500, 0.389]],
            }[kind]
            raw_connector = element.get("connector", default_connector)
            if isinstance(raw_connector, list) and len(raw_connector) == 2:
                points = [
                    (float(point[0]) * w, float(point[1]) * h)
                    for point in raw_connector
                    if isinstance(point, list) and len(point) == 2
                ]
                if len(points) == 2:
                    (x0, y0), (x1, y1) = points
                    svg.append(
                        f'  <path id="{element_id}_connector" d="M {_fmt(x0)} {_fmt(y0)} L {_fmt(x1)} {_fmt(y1)}" '
                        f'stroke="{connector_stroke}" stroke-width="{_fmt(connector_sw)}" fill="none" stroke-linecap="butt"/>'
                    )
            svg.append(
                f'  <rect id="{element_id}_body" x="{_fmt(body_x)}" y="{_fmt(body_y)}" '
                f'width="{_fmt(body_w)}" height="{_fmt(body_h)}" fill="{body_fill}" '
                f'stroke="{body_stroke}" stroke-width="{_fmt(body_sw)}"/>'
            )
            if kind == "UprightSquareKelleGlyph":
                continue
            default_label_center = {
                "VerticallyMirroredSquareKelleTGlyph": [0.500, 0.660],
                "LeftRotatedSquareKelleTGlyph": [0.611, 0.520],
                "RightFacingSquareKellePGlyph": [0.640, 0.520],
                "RightRotatedSquareKellePGlyph": [0.460, 0.656],
            }[kind]
            raw_label_center = element.get("label_center", default_label_center)
            if not isinstance(raw_label_center, list) or len(raw_label_center) != 2:
                raw_label_center = default_label_center
            default_label = (
                "P"
                if kind in {"RightFacingSquareKellePGlyph", "RightRotatedSquareKellePGlyph"}
                else "T"
            )
            label = html.escape(str(element.get("label", default_label)))
            label_fill = html.escape(str(element.get("label_fill", "#dedede")))
            font_size = float(element.get("font_size", 0.440)) * min(w, h)
            font_weight = html.escape(str(element.get("font_weight", "600")))
            svg.append(
                f'  <text id="{element_id}_label" x="{_fmt(float(raw_label_center[0]) * w)}" '
                f'y="{_fmt(float(raw_label_center[1]) * h)}" fill="{label_fill}" '
                f'font-family="Arial, Helvetica, sans-serif" font-size="{_fmt(font_size)}" '
                f'font-weight="{font_weight}" text-anchor="middle" dominant-baseline="middle">{label}</text>'
            )
        elif kind in valve_gradient_kinds:
            stroke = html.escape(str(element.get("stroke", "#969696")))
            connector_stroke = html.escape(str(element.get("connector_stroke", "#8f8f8f")))
            text_fill = html.escape(str(element.get("text_fill", "#666666")))
            body_fill = html.escape(str(element.get("body_fill", "url(#vertical-two-way-valve-body-gradient)")))
            circle_fill = html.escape(str(element.get("circle_fill", "url(#vertical-two-way-valve-circle-gradient)")))
            # PyMuPDF's SVG-to-PDF path renders paint-server fills in these compound
            # valve paths as black. Use stable grayscale fallbacks so the actual
            # conversion matches the light source artwork instead of a black glyph.
            rendered_body_fill = "#d7d7d7" if body_fill.startswith("url(") else body_fill
            rendered_circle_fill = "#fafafa" if circle_fill.startswith("url(") else circle_fill
            sw = float(element.get("stroke_width", 0.040)) * min(w, h)
            connector_sw = float(element.get("connector_width", 0.060)) * min(w, h)
            raw_connector = element.get("connector", [[0.213, 0.501], [0.460, 0.501]])
            if isinstance(raw_connector, list) and len(raw_connector) == 2:
                points = []
                for raw_point in raw_connector:
                    if isinstance(raw_point, list) and len(raw_point) == 2:
                        points.append((float(raw_point[0]) * w, float(raw_point[1]) * h))
                if len(points) == 2:
                    (x0, y0), (x1, y1) = points
                    svg.append(
                        f'  <path id="{element_id}_connector" d="M {_fmt(x0)} {_fmt(y0)} L {_fmt(x1)} {_fmt(y1)}" '
                        f'stroke="{connector_stroke}" stroke-width="{_fmt(connector_sw)}" fill="none" stroke-linecap="butt"/>'
                    )
            raw_body_paths = element.get("body_paths")
            body_path_groups = raw_body_paths if isinstance(raw_body_paths, list) else [element.get("body_path", [])]
            for body_idx, raw_body in enumerate(body_path_groups, start=1):
                body_points: list[str] = []
                if isinstance(raw_body, list):
                    for raw_point in raw_body:
                        if isinstance(raw_point, list) and len(raw_point) == 2:
                            body_points.append(f"{_fmt(float(raw_point[0]) * w)} {_fmt(float(raw_point[1]) * h)}")
                if body_points:
                    body_id = f"{element_id}_body" if len(body_path_groups) == 1 else f"{element_id}_body_{body_idx}"
                    svg.append(
                        f'  <path id="{body_id}" d="M {" L ".join(body_points)} Z" '
                        f'fill="{rendered_body_fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}" stroke-linejoin="miter"/>'
                    )
            raw_circle = element.get("circle", [0.721, 0.501, 0.263])
            if isinstance(raw_circle, list) and len(raw_circle) == 3:
                cx, cy, radius = [float(value) for value in raw_circle]
                center_x = cx * w
                center_y = cy * h
                scaled_radius = radius * min(w, h)
                if element.get("handle_shape") == "crossed_square":
                    square_x = center_x - scaled_radius
                    square_y = center_y - scaled_radius
                    square_size = scaled_radius * 2.0
                    svg.append(
                        f'  <rect id="{element_id}_square" x="{_fmt(square_x)}" y="{_fmt(square_y)}" '
                        f'width="{_fmt(square_size)}" height="{_fmt(square_size)}" fill="{rendered_circle_fill}" '
                        f'stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
                    )
                    svg.append(
                        f'  <path id="{element_id}_square_cross" '
                        f'd="M {_fmt(square_x)} {_fmt(square_y)} L {_fmt(square_x + square_size)} {_fmt(square_y + square_size)} '
                        f'M {_fmt(square_x + square_size)} {_fmt(square_y)} L {_fmt(square_x)} {_fmt(square_y + square_size)}" '
                        f'fill="none" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
                    )
                else:
                    svg.append(
                        f'  <circle id="{element_id}_circle" cx="{_fmt(center_x)}" cy="{_fmt(center_y)}" '
                        f'r="{_fmt(scaled_radius)}" fill="{rendered_circle_fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
                    )
            label = html.escape(str(element.get("label", "M")))
            raw_label_center = element.get("label_center", [0.721, 0.595])
            if label and isinstance(raw_label_center, list) and len(raw_label_center) == 2:
                font_size = float(element.get("font_size", 0.540)) * min(w, h)
                font_weight = html.escape(str(element.get("font_weight", "700")))
                svg.append(
                    f'  <text id="{element_id}_label" x="{_fmt(float(raw_label_center[0]) * w)}" '
                    f'y="{_fmt(float(raw_label_center[1]) * h)}" fill="{text_fill}" '
                    f'font-family="Arial, Helvetica, sans-serif" font-size="{_fmt(font_size)}" font-weight="{font_weight}" '
                    f'text-anchor="middle" dominant-baseline="middle">{label}</text>'
                )
        elif kind == "CircleBackground":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "#45aa5e")))
            stroke = html.escape(str(element.get("stroke", "#8d8d8d")))
            sw = float(element.get("stroke_width", 0.020)) * min(w, h)
            svg.append(
                f'  <ellipse id="{element_id}" cx="{_fmt(x + bw * 0.5)}" cy="{_fmt(y + bh * 0.5)}" '
                f'rx="{_fmt(bw * 0.5)}" ry="{_fmt(bh * 0.5)}" fill="{fill}" stroke="{stroke}" '
                f'stroke-width="{_fmt(sw)}"/>'
            )
        elif kind == "PumpTriangleGlyph":
            circle_ref = str(element.get("circle_ref", "pump_circle"))
            circle_x, circle_y, circle_w, circle_h = _find_circle(geometry_ir, circle_ref, w, h)
            fill = html.escape(str(element.get("fill", "#e7e7e7")))
            raw_points = element.get("points", [])
            points = []
            if isinstance(raw_points, list):
                for raw_point in raw_points:
                    if isinstance(raw_point, list) and len(raw_point) == 2:
                        points.append(
                            (
                                circle_x + circle_w * float(raw_point[0]),
                                circle_y + circle_h * float(raw_point[1]),
                            )
                        )
            if len(points) == 3:
                point_text = " ".join(f"{_fmt(px)},{_fmt(py)}" for px, py in points)
                svg.append(f'  <polygon id="{element_id}" points="{point_text}" fill="{fill}"/>')
        elif kind in {
            "UpwardCompressorGlyph",
            "RightwardCompressorGlyph",
            "MainDiagonalMirroredCompressorGlyph",
        }:
            circle_ref = str(element.get("circle_ref", "compressor_circle"))
            circle_x, circle_y, circle_w, circle_h = _find_circle(geometry_ir, circle_ref, w, h)
            stroke = html.escape(str(element.get("stroke", "#d7d7d7")))
            sw = float(element.get("stroke_width", 0.040)) * min(w, h)
            if kind == "RightwardCompressorGlyph":
                line_specs = (
                    ("upper_line", "rightward_compressor_upper_line"),
                    ("lower_line", "rightward_compressor_lower_line"),
                )
            elif kind == "MainDiagonalMirroredCompressorGlyph":
                line_specs = (
                    ("left_line", "mirrored_compressor_left_line"),
                    ("right_line", "mirrored_compressor_right_line"),
                )
            else:
                line_specs = (
                    ("left_line", "upward_compressor_left_line"),
                    ("right_line", "upward_compressor_right_line"),
                )
            for line_key, stable_id in line_specs:
                raw_line = element.get(line_key, [])
                if not isinstance(raw_line, list) or len(raw_line) != 2:
                    continue
                points = []
                for raw_point in raw_line:
                    if isinstance(raw_point, list) and len(raw_point) == 2:
                        px = circle_x + circle_w * float(raw_point[0])
                        py = circle_y + circle_h * float(raw_point[1])
                        points.append((px, py))
                if len(points) == 2:
                    (x0, y0), (x1, y1) = points
                    svg.append(
                        f'  <path id="{stable_id}" d="M {_fmt(x0)} {_fmt(y0)} L {_fmt(x1)} {_fmt(y1)}" '
                        f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="round"/>'
                    )
        elif kind == "HorizontalGradient":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            raw_stops = element.get("stops")
            stops = raw_stops if isinstance(raw_stops, list) else None
            svg.extend(
                _horizontal_gradient_rects(
                    element_id=element_id,
                    x=x,
                    y=y,
                    width=bw,
                    height=bh,
                    stops=stops,
                    bands=int(max(12, min(64, round(bw)))),
                )
            )
        elif kind == "RectBorder":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "none")))
            stroke = html.escape(str(element.get("stroke", "#666666")))
            sw = float(element.get("stroke_width", 0.035)) * min(w, h)
            svg.append(
                f'  <rect id="{element_id}" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bw)}" height="{_fmt(bh)}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
            )
        elif kind == "ColorPatch":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "#d8d8d8")))
            stroke = html.escape(str(element.get("stroke", "none")))
            svg.append(
                f'  <rect id="{element_id}" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bw)}" height="{_fmt(bh)}" '
                f'fill="{fill}" stroke="{stroke}"/>'
            )
        elif kind == "HalfDoubleRectBorder":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "none")))
            stroke = html.escape(str(element.get("stroke", "#777777")))
            sw = float(element.get("stroke_width", 0.024)) * min(w, h)
            inset = float(element.get("inner_inset", 0.075)) * min(bw, bh)
            svg.append(
                f'  <rect id="{element_id}_outer" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bw)}" height="{_fmt(bh)}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
            )
            svg.append(
                f'  <rect id="{element_id}_inner" x="{_fmt(x + inset)}" y="{_fmt(y + inset)}" '
                f'width="{_fmt(max(0.0, bw - 2 * inset))}" height="{_fmt(max(0.0, bh - 2 * inset))}" '
                f'fill="none" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
            )
            cut_w = max(sw * 1.6, bw * 0.20)
            svg.append(
                f'  <rect id="{element_id}_left_half_mask" x="{_fmt(x - sw)}" y="{_fmt(y - sw)}" '
                f'width="{_fmt(cut_w)}" height="{_fmt(bh + 2 * sw)}" fill="white" stroke="none"/>'
            )
        elif kind == "LabelBox":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            fill = html.escape(str(element.get("fill", "#d7d7d7")))
            stroke = html.escape(str(element.get("stroke", "#777777")))
            sw = float(element.get("stroke_width", 0.020)) * min(w, h)
            svg.append(
                f'  <rect id="{element_id}" x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(bw)}" height="{_fmt(bh)}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="{_fmt(sw)}"/>'
            )
        elif kind == "TextGlyph":
            raw_text = html.escape(str(element.get("text", "")))
            ref_id = str(element.get("bbox_ref", ""))
            ref_element = next((candidate for candidate in geometry_ir if str(candidate.get("id", "")) == ref_id), None)
            x, y, bw, bh = _scaled_bbox(ref_element or element, w, h)
            fill = html.escape(str(element.get("fill", "#555555")))
            font_size = float(element.get("font_size", 0.105)) * min(w, h)
            font_weight = html.escape(str(element.get("font_weight", "600")))
            svg.append(
                f'  <text id="{element_id}" x="{_fmt(x + bw * 0.50)}" y="{_fmt(y + bh * 0.55)}" '
                f'fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{_fmt(font_size)}" '
                f'font-weight="{font_weight}" text-anchor="middle" dominant-baseline="middle">{raw_text}</text>'
            )
        elif kind == "HorizontalRule":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            stroke = html.escape(str(element.get("stroke", "#4f4f4f")))
            sw = float(element.get("stroke_width", 0.025)) * min(w, h)
            cy = y + bh * 0.5
            svg.append(
                f'  <path id="{element_id}" d="M {_fmt(x)} {_fmt(cy)} L {_fmt(x + bw)} {_fmt(cy)}" '
                f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="square"/>'
            )
        elif kind == "VerticalRule":
            x, y, bw, bh = _scaled_bbox(element, w, h)
            stroke = html.escape(str(element.get("stroke", "#4f4f4f")))
            sw = float(element.get("stroke_width", 0.025)) * min(w, h)
            cx = x + bw * 0.5
            svg.append(
                f'  <path id="{element_id}" d="M {_fmt(cx)} {_fmt(y)} L {_fmt(cx)} {_fmt(y + bh)}" '
                f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="square"/>'
            )
        elif kind == "HorizontalRuleSet":
            stroke = html.escape(str(element.get("stroke", "#707070")))
            sw = float(element.get("stroke_width", 0.026)) * min(w, h)
            x_inset = float(element.get("x_inset", 0.10)) * rect_w
            raw_positions = element.get("positions", [0.30, 0.50, 0.70])
            if not isinstance(raw_positions, list) or not raw_positions:
                raw_positions = [0.30, 0.50, 0.70]
            for rule_index, raw_pos in enumerate(raw_positions, start=1):
                y = rect_y + rect_h * float(raw_pos)
                svg.append(
                    f'  <path id="{element_id}_{rule_index}" d="M {_fmt(rect_x + x_inset)} {_fmt(y)} '
                    f'L {_fmt(rect_x + rect_w - x_inset)} {_fmt(y)}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="butt"/>'
                )
        elif kind == "OrthogonalPolyline":
            stroke = html.escape(str(element.get("stroke", "#707070")))
            sw = float(element.get("stroke_width", 0.034)) * min(w, h)
            raw_points = element.get("points", [])
            if not isinstance(raw_points, list) or len(raw_points) < 2:
                raw_points = [[0.50, 0.02], [1.02, 0.50], [0.50, 0.98]]
            points: list[str] = []
            for raw_point in raw_points:
                if isinstance(raw_point, list) and len(raw_point) == 2:
                    px = rect_x + rect_w * float(raw_point[0])
                    py = rect_y + rect_h * float(raw_point[1])
                    points.append(f"{_fmt(px)} {_fmt(py)}")
            if len(points) >= 2:
                path_points = " L ".join(points)
                svg.append(
                    f'  <path id="{element_id}" d="M {path_points}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" '
                    'stroke-linejoin="round" stroke-linecap="butt"/>'
                )
        elif kind == "PolygonPath":
            stroke = html.escape(str(element.get("stroke", "#707070")))
            fill = html.escape(str(element.get("fill", "none")))
            sw = float(element.get("stroke_width", 0.020)) * min(w, h)
            raw_points = element.get("points", [])
            points: list[str] = []
            if isinstance(raw_points, list):
                for raw_point in raw_points:
                    if isinstance(raw_point, list) and len(raw_point) == 2:
                        points.append(f"{_fmt(float(raw_point[0]) * w)} {_fmt(float(raw_point[1]) * h)}")
            if len(points) >= 2:
                suffix = " Z" if bool(element.get("closed", False)) else ""
                svg.append(
                    f'  <path id="{element_id}" d="M {" L ".join(points)}{suffix}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="{fill}" '
                    'stroke-linejoin="round" stroke-linecap="butt"/>'
                )
        elif kind == "DiagonalBand":
            stroke = html.escape(str(element.get("stroke", "#707070")))
            sw = float(element.get("stroke_width", 0.045)) * min(w, h)
            direction = str(element.get("direction", "tr_bl"))
            inset = sw * 0.5
            if direction == "tl_br":
                x0, y0, x1, y1 = rect_x + inset, rect_y + inset, rect_x + rect_w - inset, rect_y + rect_h - inset
            else:
                x0, y0, x1, y1 = rect_x + rect_w - inset, rect_y + inset, rect_x + inset, rect_y + rect_h - inset
            svg.append(
                f'  <path id="{element_id}" d="M {_fmt(x0)} {_fmt(y0)} L {_fmt(x1)} {_fmt(y1)}" '
                f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="butt"/>'
            )
        elif kind in {"PlusGlyph", "MinusGlyph"}:
            stroke = html.escape(str(element.get("stroke", "#4f4f4f")))
            sw = float(element.get("stroke_width", 0.025)) * min(w, h)
            pos = str(element.get("position", "top_center"))
            dy = float(element.get("dy", 0.0)) * h
            if pos == "top_left":
                cx, cy = rect_x + rect_w * 0.18, rect_y - h * 0.08 + dy
            else:
                cx, cy = rect_x + rect_w * 0.50, rect_y - h * 0.08 + dy
            half = min(w, h) * 0.055
            if kind == "PlusGlyph":
                svg.append(
                    f'  <path id="{element_id}" d="M {_fmt(cx-half)} {_fmt(cy)} L {_fmt(cx+half)} {_fmt(cy)} '
                    f'M {_fmt(cx)} {_fmt(cy-half)} L {_fmt(cx)} {_fmt(cy+half)}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="square"/>'
                )
            else:
                svg.append(
                    f'  <path id="{element_id}" d="M {_fmt(cx-half)} {_fmt(cy)} L {_fmt(cx+half)} {_fmt(cy)}" '
                    f'stroke="{stroke}" stroke-width="{_fmt(sw)}" fill="none" stroke-linecap="square"/>'
                )
    return svg


def renderGeometryIrToSvgImpl(w: int, h: int, geometry_ir: list[dict[str, object]]) -> str:
    svg = [
        (
            f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            'xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">'
        )
    ]
    svg.extend(renderGeometryIrToSvgElementsImpl(w, h, geometry_ir))
    svg.append("</svg>")
    return "\n".join(svg)


def buildDescriptionConstraintsImpl(description: str) -> dict[str, object]:
    """Translate free-form descriptions into catalog-free Geometry-IR constraints.

    This is the parser-facing contract for IDO-06: descriptions contribute only
    declarative primitive/geometry/style constraints plus uncertainty metadata.
    Renderer selection, catalog family selection and output names intentionally do
    not appear in this structure.
    """

    desc = _normalize_text(description)
    elements = buildGeometryIrFromDescriptionImpl(description)
    constraints: list[dict[str, object]] = []
    relations: list[dict[str, object]] = []
    for index, element in enumerate(elements, start=1):
        if not isinstance(element, dict):
            continue
        constraint_id = f"description_element_{index}"
        normalized: dict[str, object] = {
            "id": constraint_id,
            "kind": str(element.get("kind", "UnknownPrimitive")),
            "source": "description",
            "confidence": 0.75,
        }
        explicit_relation = str(element.get("relation", "") or "")
        explicit_target = element.get("target_ref")
        for key, value in element.items():
            if key in {"id", "kind"}:
                continue
            normalized[key] = value
            if key.endswith("_ref") and isinstance(value, str):
                relations.append(
                    {
                        "type": key.removesuffix("_ref"),
                        "subject": constraint_id,
                        "object": value,
                        "source": "description",
                        "confidence": 0.75,
                    }
                )
        if explicit_relation and isinstance(explicit_target, str):
            relations.append(
                {
                    "type": explicit_relation,
                    "subject": constraint_id,
                    "object": explicit_target,
                    "source": "description",
                    "confidence": 0.75,
                }
            )
        constraints.append(normalized)

    uncertainty_reasons: list[str] = []
    if not desc:
        uncertainty_reasons.append("missing_description")
    if desc and not constraints:
        uncertainty_reasons.append("no_supported_geometry_constraint")

    return {
        "schema_version": "description_geometry_constraints_v1",
        "source": "description",
        "elements": constraints,
        "relations": relations,
        "uncertainty": {
            "status": "ok" if not uncertainty_reasons else "needs_review",
            "reasons": uncertainty_reasons,
            "confidence": 0.75 if constraints else 0.0,
        },
    }
