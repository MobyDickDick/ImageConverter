from __future__ import annotations

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as non_composite_runtime_helpers


def test_run_non_composite_iteration_impl_manual_review_writes_skip_log() -> None:
    logs: list[list[str]] = []
    prints: list[str] = []

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="manual_review",
        params={"mode": "manual_review", "review_reason": "Bitte prüfen"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=64,
        height=64,
        base_name="SE0082",
        description="desc",
        perc_img=object(),
        img_path="input.jpg",
        print_fn=prints.append,
        render_embedded_raster_svg_fn=lambda _path: "<svg />",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg />",
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: ["status=non_composite_gradient_stripe"],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: object(),
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda *_args, **_kwargs: None,
        calculate_error_fn=lambda *_args, **_kwargs: 0.0,
    )

    assert result is None
    assert logs == [["status=skipped_manual_review", "manual_review_reason=Bitte prüfen"]]
    assert prints == ["  -> Überspringe Bild: Bitte prüfen"]


def test_run_non_composite_iteration_impl_gradient_stripe_returns_iteration_tuple() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []

    result = non_composite_runtime_helpers.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy={"stops": [0, 1, 2]},
        semantic_mode_visual_override=True,
        width=32,
        height=12,
        base_name="Z_203",
        description="desc",
        perc_img="target",
        img_path="input.jpg",
        print_fn=lambda *_args, **_kwargs: None,
        render_embedded_raster_svg_fn=lambda _path: "<svg embedded/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg gradient/>",
        build_gradient_stripe_validation_log_lines_fn=lambda **kwargs: [
            f"status=non_composite_gradient_stripe_visual_override",
            f"stops={kwargs['strategy_stop_count']}",
        ],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: "rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda target, rendered: 1.25 if (target, rendered) == ("target", "rendered") else 99.0,
    )

    assert result == ("Z_203", "desc", {"mode": "non_composite"}, 1, 1.25)
    assert logs == [["status=non_composite_gradient_stripe_visual_override", "stops=3"]]
    assert artifacts == [("<svg gradient/>", "rendered")]
