from src.iCCModules import imageCompositeConverterRenderDispatch as helpers


def test_render_svg_to_numpy_returns_subprocess_result_when_available() -> None:
    marker = object()

    result = helpers.renderSvgToNumpyImpl(
        '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
        10,
        5,
        svg_render_subprocess_enabled=True,
        under_pytest_runtime=False,
        is_fitz_open_monkeypatched_fn=lambda: False,
        render_svg_to_numpy_via_subprocess_fn=lambda *_a, **_k: marker,
        is_inprocess_renderer_monkeypatched_fn=lambda: False,
        render_svg_to_numpy_inprocess_fn=lambda *_a, **_k: None,
    )

    assert result is marker


def test_render_svg_to_numpy_skips_inprocess_fallback_during_pytest_when_unpatched() -> None:
    result = helpers.renderSvgToNumpyImpl(
        '<svg xmlns="http://www.w3.org/2000/svg"></svg>',
        1,
        1,
        svg_render_subprocess_enabled=True,
        under_pytest_runtime=True,
        is_fitz_open_monkeypatched_fn=lambda: False,
        render_svg_to_numpy_via_subprocess_fn=lambda *_a, **_k: None,
        is_inprocess_renderer_monkeypatched_fn=lambda: False,
        render_svg_to_numpy_inprocess_fn=lambda *_a, **_k: object(),
    )

    assert result is None
