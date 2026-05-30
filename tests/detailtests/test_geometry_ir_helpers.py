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
