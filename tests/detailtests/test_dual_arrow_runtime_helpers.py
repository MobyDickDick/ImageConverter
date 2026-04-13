from __future__ import annotations

from src.iCCModules import imageCompositeConverterDualArrowRuntime as dual_arrow_runtime_helpers


def test_run_dual_arrow_badge_iteration_impl_uses_fallback_when_detection_fails() -> None:
    logs: list[list[str]] = []
    artifacts: list[tuple[str, object]] = []

    result = dual_arrow_runtime_helpers.runDualArrowBadgeIterationImpl(
        perc_img="target",
        filename="AR0110_2.jpg",
        base_name="AR0110_2",
        description="desc",
        params={"mode": "dual_arrow_badge"},
        width=64,
        height=64,
        detect_dual_arrow_badge_params_fn=lambda _img: None,
        generate_dual_arrow_badge_svg_fn=lambda *_args, **_kwargs: "<svg should-not-be-used/>",
        render_embedded_raster_svg_fn=lambda: "<svg embedded/>",
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: "rendered",
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, rendered: artifacts.append((svg, rendered)),
        calculate_error_fn=lambda target, rendered: 0.5 if (target, rendered) == ("target", "rendered") else 9.9,
    )

    assert result == ("AR0110_2", "desc", {"mode": "dual_arrow_badge"}, 1, 0.5)
    assert logs == [["status=dual_arrow_badge_detection_failed_fallback_embedded_svg"]]
    assert artifacts == [("<svg embedded/>", "rendered")]


def test_run_dual_arrow_badge_iteration_impl_records_render_failure_with_badge_params() -> None:
    render_failures: list[tuple[str, dict[str, object] | None]] = []

    result = dual_arrow_runtime_helpers.runDualArrowBadgeIterationImpl(
        perc_img="target",
        filename="AR0101.jpg",
        base_name="AR0101",
        description="desc",
        params={"mode": "dual_arrow_badge", "sentinel": True},
        width=80,
        height=40,
        detect_dual_arrow_badge_params_fn=lambda _img: {"foo": "bar"},
        generate_dual_arrow_badge_svg_fn=lambda *_args, **_kwargs: "<svg dual-arrow/>",
        render_embedded_raster_svg_fn=lambda: "<svg embedded/>",
        write_validation_log_fn=lambda _lines: None,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: None,
        record_render_failure_fn=lambda reason, **kwargs: render_failures.append((reason, kwargs.get("params_snapshot"))),
        write_attempt_artifacts_fn=lambda *_args, **_kwargs: None,
        calculate_error_fn=lambda *_args, **_kwargs: 0.0,
    )

    assert result is None
    assert render_failures == [
        (
            "dual_arrow_badge_final_render_failed",
            {"foo": "bar", "variant_name": "AR0101", "base_name": "AR0101"},
        )
    ]
