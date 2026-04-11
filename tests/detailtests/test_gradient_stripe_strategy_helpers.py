from __future__ import annotations

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
