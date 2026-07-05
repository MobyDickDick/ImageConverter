from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir


def test_description_builds_generic_diagonal_stripe_panel_constraints() -> None:
    ir = geometry_ir.buildGeometryIrFromDescriptionImpl(
        "Querformatiges rotes/oranges Rechteck-Icon mit grauem Rand und drei "
        "parallelen weissen Diagonalstreifen von links oben nach rechts unten."
    )

    assert len(ir) == 1
    panel = ir[0]
    assert panel["kind"] == "DiagonalStripePanel"
    assert panel["stripe_count"] == 3
    assert panel["stripe_direction"] == "top_left_to_bottom_right"
    assert panel["gradient_axis"] == "vertical"
    assert panel["primitive_decomposition"]["primitives"] == [
        {"role": "panel_border", "kind": "RectBorder"},
        {"role": "panel_fill", "kind": "ColorPatch", "gradient_axis": "vertical"},
        {"role": "diagonal_stripes", "kind": "PolygonPath", "count": 3},
    ]


def test_diagonal_stripe_panel_renderer_emits_gradient_border_and_three_polygons() -> None:
    ir = geometry_ir.buildGeometryIrFromDescriptionImpl(
        "Rechteck mit Rand, rot orange Farbverlauf und drei weisse Diagonalstreifen."
    )

    svg = geometry_ir.renderGeometryIrToSvgImpl(80, 40, ir)

    assert '<linearGradient id="diagonal_stripe_panel-gradient" x1="0%" y1="0%" x2="0%" y2="100%">' in svg
    assert 'id="diagonal_stripe_panel_fill"' in svg
    assert 'id="diagonal_stripe_panel_border"' in svg
    assert svg.count("<polygon") == 3
    assert "diagonal_stripe_panel_stripe_1" in svg
    assert "diagonal_stripe_panel_stripe_2" in svg
    assert "diagonal_stripe_panel_stripe_3" in svg


def test_diagonal_stripe_panel_svg_scales_without_id_specific_coordinates() -> None:
    ir = geometry_ir.buildGeometryIrFromDescriptionImpl(
        "Panel/Rechteck mit grauem Rahmen, rot-orangenem Verlauf und drei parallelen Diagonalstreifen."
    )

    large = geometry_ir.renderGeometryIrToSvgImpl(120, 60, ir)
    small = geometry_ir.renderGeometryIrToSvgImpl(48, 24, ir)

    assert 'width="120" height="60"' in large
    assert 'width="48" height="24"' in small
    assert large.count("<polygon") == small.count("<polygon") == 3


def test_rotated_three_horizontal_closing_surfaces_map_to_diagonal_panel() -> None:
    ir = geometry_ir.buildGeometryIrFromDescriptionImpl(
        "Graues Rechteck hochkant, graue Umrandung, drei graue horizontale Linien, "
        "Farbverlauf dunkel-hell-dunkel. Offene Klappe mit 3 Schliessflächen. "
        "Geometrische Variante: 90° nach rechts gedreht."
    )

    assert ir[0]["kind"] == "DiagonalStripePanel"
    assert ir[0]["stripe_count"] == 3
    assert ir[0]["stripe_direction"] == "top_left_to_bottom_right"
