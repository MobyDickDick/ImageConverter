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
