from src.iCCModules import imageCompositeConverterGeometryIr as geometry_ir


def test_diagonal_stripe_panel_descriptions_do_not_emit_stripe_panel_ir() -> None:
    ir = geometry_ir.buildGeometryIrFromDescriptionImpl(
        "Querformatiges rotes/oranges Rechteck-Icon mit grauem Rand und drei "
        "parallelen weissen Diagonalstreifen von links oben nach rechts unten."
    )

    assert all(element.get("kind") != "DiagonalStripePanel" for element in ir)


def test_diagonal_stripe_panel_renderer_emits_no_stripe_polygons() -> None:
    ir = geometry_ir.buildGeometryIrFromDescriptionImpl(
        "Rechteck mit Rand, rot orange Farbverlauf und drei weisse Diagonalstreifen."
    )

    svg = geometry_ir.renderGeometryIrToSvgImpl(80, 40, ir)

    assert "diagonal_stripe_panel" not in svg
    assert "<polygon" not in svg
    assert "linearGradient" not in svg or "diagonal_stripe_panel-gradient" not in svg


def test_rotated_three_horizontal_closing_surfaces_do_not_map_to_diagonal_panel() -> None:
    ir = geometry_ir.buildGeometryIrFromDescriptionImpl(
        "Graues Rechteck hochkant, graue Umrandung, drei graue horizontale Linien, "
        "Farbverlauf dunkel-hell-dunkel. Offene Klappe mit 3 Schliessflächen. "
        "Geometrische Variante: 90° nach rechts gedreht."
    )

    assert all(element.get("kind") != "DiagonalStripePanel" for element in ir)
