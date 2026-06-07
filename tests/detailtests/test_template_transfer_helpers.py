from __future__ import annotations

from src.iCCModules import imageCompositeConverterTemplateTransfer as template_transfer_helpers


def test_valve_geometry_ir_is_description_driven_and_not_template_transferable() -> None:
    params = {
        "geometry_ir": [
            {
                "kind": "RightRotatedTopKelleThreeWayValveGlyph",
                "id": "right_rotated_top_kelle_three_way_valve",
                "handle_shape": "crossed_square",
            }
        ]
    }

    assert template_transfer_helpers._has_description_driven_geometry_ir(params) is True
