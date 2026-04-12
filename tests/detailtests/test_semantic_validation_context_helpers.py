from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticValidationContext as helpers


def test_resolve_semantic_validation_debug_dir_impl_prefers_element_debug_dir(tmp_path) -> None:
    debug_dir = helpers.resolveSemanticValidationDebugDirImpl(
        debug_element_diff_dir=str(tmp_path / "elem"),
        debug_ac0811_dir=str(tmp_path / "ac0811"),
        filename="AC0811_S.jpg",
        base_name="AC0811",
    )

    assert debug_dir is not None
    assert debug_dir.endswith("elem/AC0811_S")
    assert (tmp_path / "elem" / "AC0811_S").is_dir()


def test_resolve_semantic_validation_debug_dir_impl_uses_ac0811_fallback(tmp_path) -> None:
    debug_dir = helpers.resolveSemanticValidationDebugDirImpl(
        debug_element_diff_dir=None,
        debug_ac0811_dir=str(tmp_path / "ac0811"),
        filename="ac0811_m.jpg",
        base_name="ac0811",
    )

    assert debug_dir is not None
    assert debug_dir.endswith("ac0811/ac0811_m")
    assert (tmp_path / "ac0811" / "ac0811_m").is_dir()


def test_build_non_composite_gradient_stripe_validation_log_lines_impl_marks_override() -> None:
    lines = helpers.buildNonCompositeGradientStripeValidationLogLinesImpl(
        semantic_mode_visual_override=True,
        strategy_stop_count=4,
    )

    assert lines == [
        "status=non_composite_gradient_stripe_visual_override",
        "strategy=gradient_stripe;stop_count=4",
    ]
