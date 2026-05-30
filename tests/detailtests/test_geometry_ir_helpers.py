from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir_helpers

def test_build_geometry_ir_maps_ac0130_like_description_to_ordered_chain() -> None:
    description = (
        "Wie AC0030: Kühlelement, graues Rechteck, Minus-Minus-Zeichen oben Mitte, "
        "Farbverlauf horizontal dunkel-hell-dunkel, graue Linien in beiden Diagonalen. "
        "Das Andreaskreuz besteht aus zwei Geraden."
    )

    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)

    assert [element["kind"] for element in ir] == [
        "HorizontalGradient",
        "RectBorder",
        "DiagonalBand",
        "DiagonalBand",
        "MinusGlyph",
        "MinusGlyph",
    ]
    assert [element["direction"] for element in ir if element["kind"] == "DiagonalBand"] == ["tl_br", "tr_bl"]
    assert all(element.get("position") == "top_center" for element in ir if element["kind"] == "MinusGlyph")

def test_build_geometry_ir_maps_ac0120_self_description_to_plus_minus_chain() -> None:
    description = (
        "Wie AC0120-Bildbeschreibung, zusätzlich analog AC0VR2_M4.svg mit einer zusätzlichen "
        "an der vertikalen Symmetrieachse ausgerichteten Diagonale; außerdem werden oben auf "
        "der vertikalen Symmetrieachse ein \"+\"- und ein \"-\"-Zeichen eingefügt."
    )

    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)

    kinds = [element["kind"] for element in ir]
    assert "RectBorder" in kinds
    assert kinds.count("DiagonalBand") == 2
    assert kinds[-2:] == ["PlusGlyph", "MinusGlyph"]

def test_render_geometry_ir_to_svg_contains_centralized_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        "Heizelement, graues Rechteck, Plus-Minus-Zeichen oben links, "
        "Farbverlauf horizontal dunkel-hell-dunkel graue Diagonale oben rechts nach unten links"
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(100, 80, ir)

    assert 'id="geometry-ir-horizontal-gradient"' in svg
    assert 'id="main_rect"' in svg
    assert 'id="diagonal_1_tr_bl"' in svg
    assert 'id="plus_glyph"' in svg
    assert 'id="minus_glyph"' in svg
    assert svg.endswith("</svg>")

def test_build_geometry_ir_maps_ac0150_vertical_heat_exchanger_description() -> None:
    description = (
        "Graues Rechteck hochkant, graue Umrandung, drei graue horizontale Linien, "
        "Farbverlauf dunkel-hell-dunkel, Graue Linien Oben-Mitte nach Rechts-Mitte nach Unten-Mitte"
    )

    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)

    assert [element["kind"] for element in ir] == [
        "HorizontalGradient",
        "RectBorder",
        "HorizontalRuleSet",
        "OrthogonalPolyline",
    ]
    assert ir[0]["bbox"] == [0.32, 0.12, 0.36, 0.76]
    assert ir[2]["positions"] == [0.30, 0.50, 0.70]

def test_render_geometry_ir_to_svg_contains_ac0150_rule_and_polyline_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        "Graues Rechteck hochkant, graue Umrandung, drei graue horizontale Linien, "
        "Farbverlauf dunkel-hell-dunkel, Graue Linien Oben-Mitte nach Rechts-Mitte nach Unten-Mitte"
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(120, 200, ir)

    assert 'id="horizontal_rule_set_1"' in svg
    assert 'id="horizontal_rule_set_2"' in svg
    assert 'id="horizontal_rule_set_3"' in svg
    assert 'id="right_side_orthogonal_line"' in svg
    assert 'L' in svg

def test_build_geometry_ir_maps_ac0160_differential_pressure_description() -> None:
    description = (
        'Differenzdruckmessung oben kleines graues Rechteck mit "dp" geschrieben, '
        'vor halbem Rechteck mit doppelten grauen Rand'
    )

    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(description)

    assert [element["kind"] for element in ir] == ["HalfDoubleRectBorder", "LabelBox", "TextGlyph"]
    assert ir[0]["id"] == "half_double_rect"
    assert ir[2]["text"] == "dp"
    assert ir[2]["bbox_ref"] == "dp_label_box"

def test_render_geometry_ir_to_svg_contains_ac0160_box_and_dp_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        'Differenzdruckmessung oben kleines graues Rechteck mit "dp" geschrieben, '
        'vor halbem Rechteck mit doppelten grauen Rand'
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(400, 400, ir)

    assert 'id="half_double_rect_outer"' in svg
    assert 'id="half_double_rect_inner"' in svg
    assert 'id="half_double_rect_left_half_mask"' in svg
    assert 'id="dp_label_box"' in svg
    assert 'id="dp_label_text"' in svg
    assert '>dp</text>' in svg

def test_build_geometry_ir_maps_ac0201_upward_compressor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kompressor grau nach oben")

    assert [element["kind"] for element in ir] == ["CircleBackground", "UpwardCompressorGlyph"]
    assert ir[0]["id"] == "compressor_circle"
    assert ir[1]["id"] == "upward_compressor"
    assert ir[1]["circle_ref"] == "compressor_circle"

def test_render_geometry_ir_to_svg_contains_ac0201_compressor_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kompressor grau nach oben")

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(50, 50, ir)

    assert 'id="compressor_circle"' in svg
    assert 'id="upward_compressor_left_line"' in svg
    assert 'id="upward_compressor_right_line"' in svg
    assert "#45aa5e" in svg


def test_build_geometry_ir_maps_ac0204_identical_reference_compressor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        "Wie AC0201: Kompressor grau nach oben. Geometrische Variante: identisch zur Referenz."
    )

    assert [element["kind"] for element in ir] == ["CircleBackground", "UpwardCompressorGlyph"]
    assert ir[0]["id"] == "compressor_circle"
    assert ir[0]["fill"] == "#45aa5e"
    assert ir[1]["id"] == "upward_compressor"
    assert ir[1]["circle_ref"] == "compressor_circle"


def test_render_geometry_ir_to_svg_contains_ac0204_identical_reference_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        "Wie AC0201: Kompressor grau nach oben. Geometrische Variante: identisch zur Referenz."
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(25, 20, ir)

    assert 'id="compressor_circle"' in svg
    assert 'id="upward_compressor_left_line"' in svg
    assert 'id="upward_compressor_right_line"' in svg
    assert "#45aa5e" in svg


def test_build_geometry_ir_maps_ac0211_typo_upward_compressor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kopressor grau nach oben")

    assert [element["kind"] for element in ir] == ["CircleBackground", "UpwardCompressorGlyph"]
    assert ir[0]["id"] == "compressor_circle"
    assert ir[0]["fill"] == "#45aa5e"
    assert ir[1]["id"] == "upward_compressor"
    assert ir[1]["circle_ref"] == "compressor_circle"


def test_render_geometry_ir_to_svg_contains_ac0211_typo_upward_compressor_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kopressor grau nach oben")

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(20, 25, ir)

    assert 'id="compressor_circle"' in svg
    assert 'id="upward_compressor_left_line"' in svg
    assert 'id="upward_compressor_right_line"' in svg
    assert "#45aa5e" in svg


def test_build_geometry_ir_maps_ac0222_grey_background_upward_compressor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kompressor grauer Hintergrund nach oben.")

    assert [element["kind"] for element in ir] == ["CircleBackground", "UpwardCompressorGlyph"]
    assert ir[0]["id"] == "compressor_circle"
    assert ir[0]["fill"] == "#d8d8d8"
    assert ir[1]["id"] == "upward_compressor"
    assert ir[1]["circle_ref"] == "compressor_circle"
    assert ir[1]["stroke"] == "#666666"


def test_render_geometry_ir_to_svg_contains_ac0222_grey_background_compressor_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kompressor grauer Hintergrund nach oben.")

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(30, 20, ir)

    assert 'id="compressor_circle"' in svg
    assert 'id="upward_compressor_left_line"' in svg
    assert 'id="upward_compressor_right_line"' in svg
    assert "#d8d8d8" in svg
    assert "#666666" in svg


def test_build_geometry_ir_maps_ac0202_rightward_compressor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kompressor grau nach rechts")

    assert [element["kind"] for element in ir] == ["CircleBackground", "RightwardCompressorGlyph"]
    assert ir[0]["id"] == "compressor_circle"
    assert ir[1]["id"] == "rightward_compressor"
    assert ir[1]["circle_ref"] == "compressor_circle"

def test_render_geometry_ir_to_svg_contains_ac0202_compressor_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl("Kompressor grau nach rechts")

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(50, 50, ir)

    assert 'id="compressor_circle"' in svg
    assert 'id="rightward_compressor_upper_line"' in svg
    assert 'id="rightward_compressor_lower_line"' in svg
    assert "#f4f4f4" in svg

def test_build_geometry_ir_maps_ac0203_main_diagonal_mirrored_compressor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        "Wie AC0202: Kompressor grau nach rechts. Geometrische Variante: Hauptdiagonal gespiegelt."
    )

    assert [element["kind"] for element in ir] == ["CircleBackground", "MainDiagonalMirroredCompressorGlyph"]
    assert ir[0]["id"] == "compressor_circle"
    assert ir[0]["fill"] == "#df2249"
    assert ir[1]["id"] == "main_diagonal_mirrored_compressor"
    assert ir[1]["circle_ref"] == "compressor_circle"

def test_render_geometry_ir_to_svg_contains_ac0203_mirrored_compressor_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        "Wie AC0202: Kompressor grau nach rechts. Geometrische Variante: Hauptdiagonal gespiegelt."
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(50, 50, ir)

    assert 'id="compressor_circle"' in svg
    assert 'id="mirrored_compressor_left_line"' in svg
    assert 'id="mirrored_compressor_right_line"' in svg
    assert "#df2249" in svg



def test_build_geometry_ir_maps_ac0221_top_kelle_three_way_valve_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        'Wie AC0231, jedoch ohne "M" in der Kelle oben. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert [element["kind"] for element in ir] == ["TopKelleThreeWayValveGlyph"]
    assert ir[0]["id"] == "top_kelle_three_way_valve"
    assert ir[0]["label"] == ""


def test_render_geometry_ir_to_svg_contains_ac0221_top_kelle_three_way_valve_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        'Wie AC0231, jedoch ohne "M" in der Kelle oben. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(20, 30, ir)

    assert "vertical-two-way-valve-body-gradient" in svg
    assert "vertical-two-way-valve-circle-gradient" in svg
    assert 'id="top_kelle_three_way_valve_body_1"' in svg
    assert 'id="top_kelle_three_way_valve_body_2"' in svg
    assert 'id="top_kelle_three_way_valve_body_3"' in svg
    assert 'id="top_kelle_three_way_valve_connector"' in svg
    assert 'id="top_kelle_three_way_valve_circle"' in svg
    assert 'top_kelle_three_way_valve_label' not in svg

def test_build_geometry_ir_maps_ac0212_vertical_two_way_valve_motor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        '2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert [element["kind"] for element in ir] == ["VerticalTwoWayValveMotorGlyph"]
    assert ir[0]["id"] == "vertical_two_way_valve_motor"
    assert ir[0]["label"] == "M"


def test_render_geometry_ir_to_svg_contains_ac0212_vertical_two_way_valve_motor_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        '2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten.'
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(65, 50, ir)

    assert "vertical-two-way-valve-body-gradient" in svg
    assert "vertical-two-way-valve-circle-gradient" in svg
    assert 'id="vertical_two_way_valve_motor_body"' in svg
    assert 'id="vertical_two_way_valve_motor_connector"' in svg
    assert 'id="vertical_two_way_valve_motor_circle"' in svg
    assert 'id="vertical_two_way_valve_motor_label"' in svg
    assert ">M</text>" in svg


def test_build_geometry_ir_maps_ac0213_left_rotated_two_way_valve_motor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        'Wie AC0212: 2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Geometrische Variante: 90° nach links gedreht. Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert [element["kind"] for element in ir] == ["LeftRotatedTwoWayValveMotorGlyph"]
    assert ir[0]["id"] == "left_rotated_two_way_valve_motor"
    assert ir[0]["label"] == "M"


def test_render_geometry_ir_to_svg_contains_ac0213_left_rotated_two_way_valve_motor_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        'Wie AC0212: 2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Geometrische Variante: 90° nach links gedreht.'
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(50, 65, ir)

    assert "vertical-two-way-valve-body-gradient" in svg
    assert "vertical-two-way-valve-circle-gradient" in svg
    assert 'id="left_rotated_two_way_valve_motor_body"' in svg
    assert 'id="left_rotated_two_way_valve_motor_connector"' in svg
    assert 'id="left_rotated_two_way_valve_motor_circle"' in svg
    assert 'id="left_rotated_two_way_valve_motor_label"' in svg
    assert ">M</text>" in svg

def test_build_geometry_ir_maps_ac0214_180_rotated_two_way_valve_motor_description() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        'Wie AC0212: 2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Geometrische Variante: 180° gedreht. Der Griff liegt auf einer Symmetrieachse des Kreises.'
    )

    assert [element["kind"] for element in ir] == ["Rotated180TwoWayValveMotorGlyph"]
    assert ir[0]["id"] == "rotated_180_two_way_valve_motor"
    assert ir[0]["label"] == "M"


def test_render_geometry_ir_to_svg_contains_ac0214_180_rotated_two_way_valve_motor_primitives() -> None:
    ir = geometry_ir_helpers.buildGeometryIrFromDescriptionImpl(
        'Wie AC0212: 2-Weg Ventil vertikal: Kelle mit Kreis rechts, horizontale Verbindungslinie, '
        '"M" als Text (M = Motor), zwei spitze Dreiecke, welche sich in der Mitte berühren, '
        'graue Umrandung, Dreiecke besitzen emeinsamen Farübergang von dunkelgrau rechts oben nach hellgrau links unten. '
        'Geometrische Variante: 180° gedreht.'
    )

    svg = geometry_ir_helpers.renderGeometryIrToSvgImpl(65, 50, ir)

    assert "vertical-two-way-valve-body-gradient" in svg
    assert "vertical-two-way-valve-circle-gradient" in svg
    assert 'id="rotated_180_two_way_valve_motor_body"' in svg
    assert 'id="rotated_180_two_way_valve_motor_connector"' in svg
    assert 'id="rotated_180_two_way_valve_motor_circle"' in svg
    assert 'id="rotated_180_two_way_valve_motor_label"' in svg
    assert ">M</text>" in svg
