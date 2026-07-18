from __future__ import annotations

from pathlib import Path

import src.imageCompositeConverter as converter
from src.iCCModules import imageCompositeConverterGradientStripeStrategy as helpers

np = converter._importWithVendoredFallback("numpy")


def test_detect_gradient_stripe_strategy_extracts_bbox_and_stops() -> None:
    img = np.full((20, 120, 3), 255, dtype=np.uint8)
    for x in range(10, 111):
        t = (x - 10) / 100.0
        # BGR layout
        img[4:9, x] = np.array(
            [
                int(230 - 55 * t),
                int(170 + 20 * t),
                int(160 + 35 * t),
            ],
            dtype=np.uint8,
        )

    strategy = helpers.detectGradientStripeStrategyImpl(img, np_module=np)

    assert strategy is not None
    assert strategy["bbox"] == {"x": 10.0, "y": 4.0, "width": 101.0, "height": 5.0}
    assert len(strategy["stops"]) >= 2
    assert strategy["stops"][0]["offset"] == 0.0
    assert strategy["stops"][-1]["offset"] == 1.0


def test_build_gradient_stripe_svg_renders_gradient_stops() -> None:
    strategy = {
        "bbox": {"x": 1.0, "y": 2.0, "width": 30.0, "height": 4.0},
        "vertical": False,
        "stops": [
            {"offset": 0.0, "color": "#112233"},
            {"offset": 0.4, "color": "#445566"},
            {"offset": 1.0, "color": "#778899"},
        ],
    }

    svg = helpers.buildGradientStripeSvgImpl(40, 10, strategy)

    assert 'linearGradient id="detectedStripeGradient"' in svg
    assert 'offset="0.000%" stop-color="#112233"' in svg
    assert 'offset="40.000%" stop-color="#445566"' in svg
    assert 'offset="100.000%" stop-color="#778899"' in svg
    assert 'rect x="1.0000" y="2.0000" width="30.0000" height="4.0000"' in svg


def test_detect_gradient_stripe_strategy_skips_tiny_canvas_height() -> None:
    img = np.full((6, 80, 3), 255, dtype=np.uint8)
    for x in range(8, 72):
        img[2:4, x] = np.array([170, 180, 190], dtype=np.uint8)

    strategy = helpers.detectGradientStripeStrategyImpl(img, np_module=np)

    assert strategy is None


def test_detect_gradient_strategy_handles_full_height_vertical_panel() -> None:
    img = np.full((30, 60, 3), 255, dtype=np.uint8)
    for y in range(30):
        if y <= 8:
            t = y / 8.0
            value = int(round(180 + (251 - 180) * t))
        elif y <= 11:
            value = 251
        else:
            t = (y - 11) / 18.0
            value = int(round(251 + (180 - 251) * t))
        img[y, :] = np.array([value, value, value], dtype=np.uint8)
    img[0, :] = np.array([173, 173, 173], dtype=np.uint8)
    img[-1, :] = np.array([173, 173, 173], dtype=np.uint8)
    img[:, 0] = np.array([173, 173, 173], dtype=np.uint8)
    img[:, -1] = np.array([173, 173, 173], dtype=np.uint8)

    strategy = helpers.detectGradientStripeStrategyImpl(img, np_module=np)

    assert strategy is not None
    assert strategy["vertical"] is True
    assert strategy["bbox"] == {"x": 0.0, "y": 0.0, "width": 60.0, "height": 30.0}
    assert len(strategy["stops"]) >= 3
    assert strategy["stops"][0]["color"] == "#adadad"


def test_ac0vr2_ab_m_sample_uses_smooth_gradients_not_stripe_columns() -> None:
    sample_path = Path("artifacts/images_to_convert/samples/AC0VR2_AB_M.svg")
    snapshot_path = Path("artifacts/converted_images/reports/conversion_bestlist_snapshots/AC0VR2_AB_M.svg")
    svg = sample_path.read_text(encoding="utf-8")

    assert snapshot_path.read_text(encoding="utf-8") == svg
    assert svg.count("<linearGradient") == 2
    assert svg.count("<rect") == 3
    assert svg.count("<path") == 4
    assert 'width="0.981"' not in svg
    assert 'fill="url(#verticalGrey)"' in svg
    assert 'fill="url(#horizontalSheen)"' in svg
