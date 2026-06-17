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


def test_description_parser_attaches_geometry_ir_for_ac0231_m_top_kelle_three_way_valve() -> None:
    _desc, params = _parse(
        '3-Weg Ventil ähnlich AC0211, um 90° im Uhrzeigersinn gedreht, '
        '"M" wird immer noch senkrecht geschrieben. Noch ein 3. spitzes Dreieck unten. '
        'Wieder Farbwechsel von Dunkelgrau nach hellgrau (von links unten nach rechts oben)'
    )

    assert params["contract_status"] == "ok"
    assert [element["kind"] for element in params["geometry_ir"]] == ["TopKelleThreeWayValveGlyph"]
    assert params["geometry_ir"][0]["label"] == "M"


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
