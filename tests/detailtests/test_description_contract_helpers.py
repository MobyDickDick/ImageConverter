from src.iCCModules.imageCompositeConverterGeometryIr import runtime as geometry_runtime
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection


def _parse(desc: str):
    mapping = {"AC9999": desc}
    return Reflection(mapping).parse_description("AC9999", "AC9999_L.jpg")

def test_description_contract_complete_description_marks_ok() -> None:
    _desc, params = _parse("Wie AC0030, Kreis mit Rechteck und Kreuz, nur oben verwenden.")
    contract = params["description_contract"]
    assert contract["has_reference"] is True
    assert contract["has_geometry_terms"] is True
    assert contract["has_conditions"] is True
    assert contract["status"] == "ok"
    assert params["contract_status"] == "ok"

def test_description_contract_recursive_alias_keeps_contract() -> None:
    mapping = {
        "AC9998": "Wie AC9997, Kreis mit Linie",
        "AC9997": "Wie AC0030, Kreis mit Linie",
    }
    _desc, params = Reflection(mapping).parse_description("AC9998", "AC9998_L.jpg")
    assert params["contract_status"] == "ok"

def test_description_contract_empty_description_is_insufficient() -> None:
    _desc, params = _parse("")
    assert params["contract_status"] == "insufficient_description"
    assert params["mode"] == "insufficient_description"
    assert "missing_description" in params["description_contract"]["deficits"]

def test_description_contract_alias_only_marks_reference_without_geometry_terms() -> None:
    _desc, params = _parse("Wie AC0030")
    contract = params["description_contract"]
    assert contract["has_reference"] is True
    assert contract["has_geometry_terms"] is False
    assert params["contract_status"] == "ok"

def test_description_parser_attaches_geometry_ir_for_ac0120_like_description() -> None:
    _desc, params = _parse(
        "Wie AC0030: Kühlelement, graues Rechteck, Minus-Minus-Zeichen oben Mitte, "
        "Farbverlauf horizontal dunkel-hell-dunkel, graue Linien in beiden Diagonalen."
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]][:4] == [
        "HorizontalGradient",
        "RectBorder",
        "DiagonalBand",
        "DiagonalBand",
    ]

def test_description_parser_attaches_geometry_ir_for_ac0160_like_description() -> None:
    _desc, params = _parse(
        'Differenzdruckmessung oben kleines graues Rechteck mit "dp" geschrieben, '
        'vor halbem Rechteck mit doppelten grauen Rand'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "HalfDoubleRectBorder",
        "LabelBox",
        "TextGlyph",
    ]

def test_description_parser_attaches_geometry_ir_for_ac0201_upward_compressor() -> None:
    _desc, params = _parse("Kompressor grau nach oben")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "UpwardCompressorGlyph",
    ]

def test_description_parser_attaches_geometry_ir_for_ac0202_rightward_compressor() -> None:
    _desc, params = _parse("Kompressor grau nach rechts")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "RightwardCompressorGlyph",
    ]

def test_description_parser_attaches_geometry_ir_for_ac0203_main_diagonal_mirrored_compressor() -> None:
    _desc, params = _parse(
        "Wie AC0202: Kompressor grau nach rechts. Geometrische Variante: Hauptdiagonal gespiegelt."
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "MainDiagonalMirroredCompressorGlyph",
    ]


def test_description_parser_attaches_geometry_ir_for_ac0211_typo_upward_compressor() -> None:
    _desc, params = _parse("Kopressor grau nach oben")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "UpwardCompressorGlyph",
    ]


def test_description_parser_attaches_geometry_ir_for_ac0222_grey_background_upward_compressor() -> None:
    _desc, params = _parse("Kompressor grauer Hintergrund nach oben.")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "UpwardCompressorGlyph",
    ]
    assert params["geometry_ir"][0]["fill"] == "#d8d8d8"
    assert params["geometry_ir"][1]["stroke"] == "#666666"


def test_description_parser_derives_left_circle_connector_without_catalog_id() -> None:
    _desc, params = _parse("Grauer Kreis mit waagrechtem Strich links vom Kreis.")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "HorizontalRule",
    ]
    assert params["geometry_ir"][1]["relation"] == "left_of"
    assert params["geometry_ir"][1]["target_ref"] == "described_circle"


def test_left_circle_connector_description_is_filename_invariant() -> None:
    description = "Grauer Kreis mit waagrechtem Strich links vom Kreis."
    mapping = {
        "neutral_symbol_alpha": description,
        "renamed_holdout_delta": description,
    }
    reflection = Reflection(mapping)

    _first_desc, first = reflection.parse_description(
        "neutral_symbol_alpha", "neutral_symbol_alpha.png"
    )
    _second_desc, second = reflection.parse_description(
        "renamed_holdout_delta", "renamed_holdout_delta.png"
    )

    assert first["description_constraints"] == second["description_constraints"]
    assert first["geometry_ir"] == second["geometry_ir"]


def test_description_parser_derives_right_circle_connector_without_catalog_id() -> None:
    _desc, params = _parse("Grauer Kreis mit waagrechtem Strich rechts vom Kreis.")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "HorizontalRule",
    ]
    assert params["geometry_ir"][1]["relation"] == "right_of"
    assert params["geometry_ir"][1]["target_ref"] == "described_circle"


def test_right_circle_connector_description_is_filename_invariant() -> None:
    description = "Grauer Kreis mit rechter Anschlusslinie."
    mapping = {
        "neutral_symbol_gamma": description,
        "renamed_holdout_theta": description,
    }
    reflection = Reflection(mapping)

    _first_desc, first = reflection.parse_description(
        "neutral_symbol_gamma", "neutral_symbol_gamma.png"
    )
    _second_desc, second = reflection.parse_description(
        "renamed_holdout_theta", "renamed_holdout_theta.png"
    )

    assert first["description_constraints"] == second["description_constraints"]
    assert first["geometry_ir"] == second["geometry_ir"]
    assert first["description_constraints"]["relations"][-1]["type"] == "right_of"


def test_description_parser_derives_top_circle_connector_without_catalog_id() -> None:
    _desc, params = _parse("Grauer Kreis mit senkrechtem Strich oben vom Kreis.")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "VerticalRule",
    ]
    assert params["geometry_ir"][1]["relation"] == "top_of"
    assert params["geometry_ir"][1]["target_ref"] == "described_circle"
    assert params["description_constraints"]["relations"][-1]["type"] == "top_of"


def test_description_parser_derives_bottom_circle_connector_without_catalog_id() -> None:
    _desc, params = _parse("Grauer Kreis mit unterer Anschlusslinie unterhalb des Kreises.")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "VerticalRule",
    ]
    assert params["geometry_ir"][1]["relation"] == "bottom_of"
    assert params["geometry_ir"][1]["target_ref"] == "described_circle"
    assert params["description_constraints"]["relations"][-1]["type"] == "bottom_of"


def test_vertical_circle_connector_description_is_filename_invariant() -> None:
    description = "Grauer Kreis mit oberer Anschlusslinie."
    mapping = {
        "neutral_symbol_iota": description,
        "renamed_holdout_kappa": description,
    }
    reflection = Reflection(mapping)

    _first_desc, first = reflection.parse_description(
        "neutral_symbol_iota", "neutral_symbol_iota.png"
    )
    _second_desc, second = reflection.parse_description(
        "renamed_holdout_kappa", "renamed_holdout_kappa.png"
    )

    assert first["description_constraints"] == second["description_constraints"]
    assert first["geometry_ir"] == second["geometry_ir"]
    assert first["description_constraints"]["relations"][-1]["type"] == "top_of"


def test_description_parser_marks_partly_occluded_top_connector_z_order() -> None:
    _desc, params = _parse(
        "Grauer Kreis mit teilweise verdeckter vertikaler Anschlusslinie oberhalb des Kreises."
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "VerticalRule",
        "CircleBackground",
    ]
    connector = params["geometry_ir"][0]
    assert connector["relation"] == "top_of"
    assert connector["z_order"] == "behind_target"
    assert connector["continues_behind_ref"] == "described_circle"
    relations = params["description_constraints"]["relations"]
    assert {relation["type"] for relation in relations} >= {"top_of", "continues_behind"}


def test_description_parser_marks_partly_occluded_bottom_connector_z_order() -> None:
    _desc, params = _parse(
        "Grauer Kreis über der Linie; der untere Anschluss ist teilweise verdeckt."
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "VerticalRule",
        "CircleBackground",
    ]
    connector = params["geometry_ir"][0]
    assert connector["relation"] == "bottom_of"
    assert connector["z_order"] == "behind_target"
    relations = params["description_constraints"]["relations"]
    assert {relation["type"] for relation in relations} >= {"bottom_of", "continues_behind"}


def test_description_parser_keeps_connector_free_circle_without_vertical_rule() -> None:
    _desc, params = _parse("Grauer Kreis ohne Anschluss und ohne Buchstabe.")

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == ["CircleBackground"]
    assert params["geometry_ir"][0]["connector_policy"] == "forbid"
    assert params["description_constraints"]["relations"] == []

def test_description_parser_attaches_geometry_ir_for_ac0232_left_rotated_m_top_kelle_three_way_valve() -> None:
    _desc, params = _parse(
        'Wie AC0231: 3-Weg Ventil ähnlich AC0211, um 90° im Uhrzeigersinn gedreht, '
        '"M" wird immer noch senkrecht geschrieben. Noch ein 3. spitzes Dreieck unten. '
        'Wieder Farbwechsel von Dunkelgrau nach hellgrau (von links unten nach rechts oben). '
        'Geometrische Variante: 90° nach links gedreht. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "LeftRotatedTopKelleThreeWayValveGlyph"
    ]
    assert params["geometry_ir"][0]["label"] == "M"


def test_description_parser_attaches_geometry_ir_for_ac0234_main_diagonal_mirrored_m_top_kelle_three_way_valve() -> None:
    _desc, params = _parse(
        'Wie AC0231: 3-Weg Ventil ähnlich AC0211, um 90° im Uhrzeigersinn gedreht, '
        '"M" wird immer noch senkrecht geschrieben. Noch ein 3. spitzes Dreieck unten. '
        'Wieder Farbwechsel von Dunkelgrau nach hellgrau (von links unten nach rechts oben). '
        'Geometrische Variante: Hauptdiagonal gespiegelt.'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "MainDiagonalMirroredTopKelleThreeWayValveGlyph"
    ]
    assert params["geometry_ir"][0]["label"] == "M"


def test_description_parser_attaches_geometry_ir_for_ac0233_180_rotated_m_top_kelle_three_way_valve() -> None:
    _desc, params = _parse(
        'Wie AC0231: 3-Weg Ventil ähnlich AC0211, um 90° im Uhrzeigersinn gedreht, '
        '"M" wird immer noch senkrecht geschrieben. Noch ein 3. spitzes Dreieck unten. '
        'Wieder Farbwechsel von Dunkelgrau nach hellgrau (von links unten nach rechts oben). '
        'Geometrische Variante: 180° gedreht.'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "Rotated180TopKelleThreeWayValveGlyph"
    ]
    assert params["geometry_ir"][0]["label"] == "M"
    assert params["geometry_ir"][0]["transform"] == {
        "schema_version": "generic_geometry_transform_v1",
        "rotation_deg": 180,
    }


def test_description_parser_attaches_geometry_ir_for_ac0231_m_top_kelle_three_way_valve() -> None:
    _desc, params = _parse(
        '3-Weg Ventil ähnlich AC0211, um 90° im Uhrzeigersinn gedreht, '
        '"M" wird immer noch senkrecht geschrieben. Noch ein 3. spitzes Dreieck unten. '
        'Wieder Farbwechsel von Dunkelgrau nach hellgrau (von links unten nach rechts oben)'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == ["TopKelleThreeWayValveGlyph"]
    assert params["geometry_ir"][0]["label"] == "M"
    assert params["geometry_ir"][0]["primitive_decomposition"]["primitives"] == [
        {"role": "valve_body", "kind": "PolygonPath", "count": 3},
        {"role": "handle_circle", "kind": "CircleBackground"},
        {"role": "handle_connector", "kind": "LineSegment"},
        {"role": "handle_label", "kind": "TextGlyph", "text": "M"},
    ]


def test_description_parser_decomposes_neutral_rotated_kelle_valve_without_catalog_id() -> None:
    _desc, params = _parse(
        '3-Weg Ventil mit Kelle oben, Kreis-Griff, drei Dreiecke als Ventilkörper, '
        'senkrechtem Griff und "M" im Kreis. Geometrische Variante: 180° gedreht.'
    )

    assert params["contract_status"] == "ok"
    element = params["geometry_ir"][0]
    assert element["kind"] == "Rotated180TopKelleThreeWayValveGlyph"
    assert element["transform"] == {
        "schema_version": "generic_geometry_transform_v1",
        "rotation_deg": 180,
    }
    assert element["primitive_decomposition"] == {
        "schema_version": "kelle_valve_primitive_decomposition_v1",
        "orientation": "bottom",
        "primitives": [
            {"role": "valve_body", "kind": "PolygonPath", "count": 3},
            {"role": "handle_circle", "kind": "CircleBackground"},
            {"role": "handle_connector", "kind": "LineSegment"},
            {"role": "handle_label", "kind": "TextGlyph", "text": "M"},
        ],
    }


def test_description_parser_attaches_geometry_ir_for_ac0221_top_kelle_three_way_valve() -> None:
    _desc, params = _parse(
        'Wie AC0231, jedoch ohne "M" in der Kelle oben. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == ["TopKelleThreeWayValveGlyph"]



def test_description_parser_attaches_geometry_ir_for_ac0224_right_rotated_top_kelle_three_way_valve() -> None:
    _desc, params = _parse(
        'Wie AC0221: Wie AC0231, jedoch ohne "M" in der Kelle oben. '
        'Geometrische Variante: 90° nach rechts gedreht. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "RightRotatedTopKelleThreeWayValveGlyph"
    ]

def test_description_parser_attaches_geometry_ir_for_ac0212_vertical_two_way_valve_motor() -> None:
    _desc, params = _parse(
        '2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == ["VerticalTwoWayValveMotorGlyph"]


def test_description_parser_decomposes_neutral_two_way_valve_without_catalog_id() -> None:
    _desc, params = _parse(
        '2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        'M als Motor-Text im Kreis und zwei spitze Dreiecke, die sich in der Mitte berühren.'
    )

    assert params["contract_status"] == "ok"
    element = params["geometry_ir"][0]
    assert element["kind"] == "VerticalTwoWayValveMotorGlyph"
    assert element["transform"] == {
        "schema_version": "generic_geometry_transform_v1",
        "rotation_deg": 0,
    }
    assert element["primitive_decomposition"] == {
        "schema_version": "two_way_valve_primitive_decomposition_v1",
        "orientation": "right",
        "primitives": [
            {"role": "valve_body", "kind": "PolygonPath", "count": 2},
            {"role": "handle_circle", "kind": "CircleBackground"},
            {"role": "handle_connector", "kind": "LineSegment"},
            {"role": "handle_label", "kind": "TextGlyph", "text": "M"},
        ],
    }


def test_description_parser_decomposes_neutral_rotated_two_way_valve_without_catalog_id() -> None:
    _desc, params = _parse(
        '2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        'M als Motor-Text im Kreis und zwei spitze Dreiecke, die sich in der Mitte berühren. '
        'Geometrische Variante: 180° gedreht.'
    )

    assert params["contract_status"] == "ok"
    element = params["geometry_ir"][0]
    assert element["kind"] == "Rotated180TwoWayValveMotorGlyph"
    assert element["transform"] == {
        "schema_version": "generic_geometry_transform_v1",
        "rotation_deg": 180,
    }
    assert element["primitive_decomposition"]["orientation"] == "left"


def test_description_parser_attaches_geometry_ir_for_ac0213_left_rotated_two_way_valve_motor() -> None:
    _desc, params = _parse(
        'Wie AC0212: 2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Geometrische Variante: 90° nach links gedreht. Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == ["LeftRotatedTwoWayValveMotorGlyph"]

def test_description_parser_attaches_geometry_ir_for_ac0214_180_rotated_two_way_valve_motor() -> None:
    _desc, params = _parse(
        'Wie AC0212: 2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Geometrische Variante: 180° gedreht. Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == ["Rotated180TwoWayValveMotorGlyph"]


def test_description_parser_emits_catalog_free_constraints_for_neutral_names() -> None:
    desc = 'Kompressor grau nach oben mit Kreis und zwei diagonalen Linien.'
    _desc_a, params_a = Reflection({"NEUTRAL_ALPHA": desc}).parse_description(
        "NEUTRAL_ALPHA", "neutral_alpha.svg.png"
    )
    _desc_b, params_b = Reflection({"NEUTRAL_BETA": desc}).parse_description(
        "NEUTRAL_BETA", "neutral_beta.svg.png"
    )

    assert params_a["description_constraints"] == params_b["description_constraints"]
    constraints = params_a["description_constraints"]
    assert constraints["schema_version"] == "description_geometry_constraints_v1"
    assert constraints["source"] == "description"
    assert constraints["uncertainty"]["status"] == "ok"
    serialized = repr(constraints).lower()
    assert "neutral_alpha" not in serialized
    assert "neutral_beta" not in serialized
    assert "semantic_badge" not in serialized
    assert "mode" not in serialized


def test_description_constraints_report_uncertainty_without_renderer_choice() -> None:
    _desc, params = Reflection({"RANDOM_SYMBOL": "Unbekannter technischer Hinweis."}).parse_description(
        "RANDOM_SYMBOL", "renamed_holdout_input.png"
    )

    constraints = params["description_constraints"]
    assert constraints["elements"] == []
    assert constraints["relations"] == []
    assert constraints["uncertainty"] == {
        "status": "needs_review",
        "reasons": ["no_supported_geometry_constraint"],
        "confidence": 0.0,
    }
    assert "mode" not in constraints

def test_left_circle_connector_constraints_include_explicit_relation() -> None:
    _desc, params = _parse("Grauer Kreis mit Linie links vom Kreis.")

    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "HorizontalRule",
    ]
    assert {
        "type": "left_of",
        "subject": "description_element_2",
        "object": "described_circle",
        "source": "description",
        "confidence": 0.75,
    } in params["description_constraints"]["relations"]


def test_left_circle_connector_constraints_accept_inverse_relation_text() -> None:
    _desc, params = _parse("Grauer Kreis rechts von der Linie, linker Anschluss ohne Buchstabe.")

    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "HorizontalRule",
    ]
    assert params["geometry_ir"][1]["target_ref"] == "described_circle"
    assert params["geometry_ir"][1]["relation"] == "left_of"
    assert {
        "type": "left_of",
        "subject": "description_element_2",
        "object": "described_circle",
        "source": "description",
        "confidence": 0.75,
    } in params["description_constraints"]["relations"]


def test_description_parser_generalizes_circle_badge_label_content_and_centering() -> None:
    _desc, params = _parse('Grauer Kreis; zentrierter VOC-Glyph im Kreis, ohne Anschlusslinie.')

    assert [element["kind"] for element in params["geometry_ir"]] == [
        "CircleBackground",
        "TextGlyph",
    ]
    circle, text = params["geometry_ir"]
    assert circle["badge_role"] == "circle_text_badge"
    assert circle["connector_policy"] == "forbid"
    assert text["text"] == "VOC"
    assert text["text_position"] == "center"
    assert text["relation"] == "centered_in"
    assert {
        "type": "centered_in",
        "subject": "description_element_2",
        "object": "described_circle",
        "source": "description",
        "confidence": 0.75,
    } in params["description_constraints"]["relations"]



def test_description_parser_exposes_circle_badge_glyph_evidence() -> None:
    _desc, params = _parse('Grauer Kreis; Text "CO2" zentriert im Kreis, ohne Anschlusslinie.')

    text = params["geometry_ir"][1]
    assert text["text"] == "CO₂"
    assert text["text_anchor"] == [0.5, 0.5]
    assert text["glyph_evidence"] == {
        "source": "description_text",
        "normalized_text": "CO₂",
        "position": "center",
    }


def test_description_parser_supports_non_center_circle_badge_text_positions() -> None:
    _desc, params = _parse('Grauer Kreis; T oben im Kreis, ohne Anschlusslinie.')

    text = params["geometry_ir"][1]
    assert text["text"] == "T"
    assert text["text_position"] == "top"
    assert text["relation"] == "top_inside"
    assert text["text_anchor"] == [0.5, 0.32]
    assert {
        "type": "top_inside",
        "subject": "description_element_2",
        "object": "described_circle",
        "source": "description",
        "confidence": 0.75,
    } in params["description_constraints"]["relations"]

def test_description_parser_generalizes_co2_rf_and_empty_circle_badges() -> None:
    examples = [
        ('Kleiner Kreis mit Text "CO2" zentriert im Kreis.', "CO₂", [0.16, 0.16, 0.68, 0.68]),
        ("Großer Kreis, Label rF in dem Kreis.", "rF", [0.035, 0.035, 0.93, 0.93]),
    ]

    for description, label, bbox in examples:
        _desc, params = _parse(description)
        assert params["geometry_ir"][0]["bbox"] == bbox
        assert params["geometry_ir"][1]["text"] == label
        assert params["geometry_ir"][1]["target_ref"] == "described_circle"

    _desc, params = _parse("Grauer Kreis ohne Buchstabe und ohne Anschluss.")
    assert [element["kind"] for element in params["geometry_ir"]] == ["CircleBackground"]
    assert params["geometry_ir"][0]["connector_policy"] == "forbid"
    assert params["description_constraints"]["relations"] == []

def test_description_parser_attaches_generic_checkmark_geometry_ir() -> None:
    description = (
        "Weißer quadratischer Hintergrund; rechts oben ein grüner Haken aus zwei dicken, "
        "schrägen Liniensegmenten: ein kurzer Schenkel steigt von links unten zur Mitte, "
        "ein langer Schenkel steigt von der Mitte nach rechts oben. Unter dem grünen Haken "
        "liegt eine feine graue Kontur beziehungsweise ein grauer Schatten entlang der linken "
        "und unteren Außenkante."
    )

    _desc, params = _parse(description)

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "ColorPatch",
        "PolygonPath",
        "PolygonPath",
    ]
    assert params["geometry_ir"][2]["role"] == "checkmark"
    assert params["geometry_ir"][2]["primitive_decomposition"]["schema_version"] == "checkmark_primitive_decomposition_v1"


def test_description_parser_attaches_generic_checkbox_checkmark_geometry_ir() -> None:
    description = (
        "Weißer quadratischer Hintergrund mit Haken vor Checkbox: grauer Rand, weiss gefüllt. "
        "Der Haken hat eine grüne Füllung, einen vertikalen Farbverlauf und eine dunkelgraue Umrandung "
        "aus zwei schrägen Liniensegmenten."
    )

    _desc, params = _parse(description)

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "ColorPatch",
        "RectBorder",
        "PolygonPath",
        "PolygonPath",
    ]
    checkbox = params["geometry_ir"][1]
    assert checkbox["role"] == "checkbox"
    assert checkbox["primitive_decomposition"]["schema_version"] == "checkbox_primitive_decomposition_v1"
    assert params["geometry_ir"][3]["role"] == "checkmark"
    assert params["geometry_ir"][3]["stroke_gradient"]["id"] == "checkmark-green-vertical-gradient"
    assert params["geometry_ir"][3]["stroke_gradient"]["stops"][-1]["color"] == "#c8d0c3"


def test_description_parser_attaches_dlg_style_checkbox_checkmark_geometry_ir() -> None:
    description = (
        "Haken vor Checkbox (grauer Rand, weiss gefüllt). Haken: Füllung grüner "
        "Farbverlauf oben dunkel, unten hellgrau. Dunkelgraue Umrandung"
    )

    _desc, params = _parse(description)

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "ColorPatch",
        "RectBorder",
        "PolygonPath",
        "PolygonPath",
    ]
    checkbox = params["geometry_ir"][1]
    shadow = params["geometry_ir"][2]
    checkmark = params["geometry_ir"][3]
    assert checkbox["role"] == "checkbox"
    assert checkbox["bbox"] == [0.250, 0.250, 0.580, 0.600]
    assert shadow["points"] == [[0.285, 0.590], [0.510, 0.800], [0.880, 0.025]]
    assert shadow["stroke_width"] == 0.105
    assert checkmark["role"] == "checkmark"
    assert checkmark["points"] == [[0.310, 0.545], [0.530, 0.730], [0.855, 0.005]]
    assert checkmark["stroke_width"] == 0.075
    assert checkmark["stroke_gradient"]["stops"][0]["color"] == "#176f28"


def test_geometry_ir_renderer_emits_checkmark_stroke_gradient() -> None:
    description = "Haken vor Checkbox: grauer Rand, weiss gefüllt. Haken: Füllung grüner Farbverlauf oben dunkel, unten hellgrau."
    _desc, params = _parse(description)

    svg = geometry_runtime.renderGeometryIrToSvgImpl(80, 80, params["geometry_ir"])

    assert '<linearGradient id="checkmark-green-vertical-gradient" x1="0%" y1="0%" x2="0%" y2="100%">' in svg
    assert 'stop-color="#176f28"' in svg
    assert 'stop-color="#c8d0c3"' in svg
    assert 'id="checkmark_green_stroke"' in svg
    assert 'stroke="url(#checkmark-green-vertical-gradient)"' in svg


def test_description_parser_checkmark_geometry_ir_is_filename_invariant() -> None:
    description = "Weißer Hintergrund mit grünem Haken aus zwei schrägen Schenkeln und grauem Schatten."
    mapping = {"NEUTRAL_A": description, "NEUTRAL_B": description}
    reflection = Reflection(mapping)

    _first_desc, first = reflection.parse_description("NEUTRAL_A", "neutral-alpha.png")
    _second_desc, second = reflection.parse_description("NEUTRAL_B", "renamed-random-input.png")

    assert first["geometry_ir"] == second["geometry_ir"]


def test_description_parser_attaches_generic_chart_triangle_pair_geometry_ir() -> None:
    description = (
        "Diagrammlinie (x-/y-Achse schwarz), graue horizontale Linie, zwei Dreiecke, "
        "welche sich in einer Spitze zusammen mit der grauen treffen. Oberes Dreieck "
        "ist rot, unteres Dreieck ist blau."
    )

    _desc, params = _parse(description)

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "ColorPatch",
        "PolygonPath",
        "PolygonPath",
        "PolygonPath",
        "PolygonPath",
        "PolygonPath",
    ]
    assert [element["role"] for element in params["geometry_ir"][1:]] == [
        "y_axis",
        "x_axis",
        "horizontal_reference_line",
        "upper_triangle",
        "lower_triangle",
    ]
    assert params["geometry_ir"][1]["stroke_width"] == 0.036
    assert params["geometry_ir"][3]["stroke_width"] == 0.036
    assert params["geometry_ir"][4]["points"] == [[0.280, 0.160], [0.720, 0.160], [0.480, 0.500]]
    assert params["geometry_ir"][4]["stroke_width"] == 0.024
    assert params["geometry_ir"][5]["points"] == [[0.480, 0.520], [0.280, 0.840], [0.720, 0.840]]
    assert params["geometry_ir"][5]["stroke_width"] == 0.024
    assert params["geometry_ir"][4]["primitive_decomposition"]["schema_version"] == "chart_triangle_pair_decomposition_v1"


def test_description_parser_chart_triangle_pair_geometry_ir_is_filename_invariant() -> None:
    description = "Diagramm mit schwarzer x-Achse und y-Achse, graue horizontale Linie, rotes oberes Dreieck und blaues unteres Dreieck."
    mapping = {"NEUTRAL_CHART_A": description, "NEUTRAL_CHART_B": description}
    reflection = Reflection(mapping)

    _first_desc, first = reflection.parse_description("NEUTRAL_CHART_A", "neutral-chart-alpha.png")
    _second_desc, second = reflection.parse_description("NEUTRAL_CHART_B", "renamed-chart-input.png")

    assert first["geometry_ir"] == second["geometry_ir"]


def test_description_parser_attaches_generic_yellow_u_loop_geometry_ir() -> None:
    description = (
        "Weißer schmaler Hintergrund mit gelber U-Form: zwei senkrechte gelbe Linien "
        "laufen links und rechts nach unten und sind unten durch einen runden gelben "
        "Bogen verbunden."
    )

    _desc, params = _parse(description)

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == [
        "ColorPatch",
        "PolygonPath",
    ]
    loop = params["geometry_ir"][1]
    assert loop["role"] == "u_loop"
    assert loop["primitive_decomposition"]["schema_version"] == "u_loop_primitive_decomposition_v1"
