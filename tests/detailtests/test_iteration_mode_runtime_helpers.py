from src.iCCModules import imageCompositeConverterIterationModeRuntime as helpers


def test_build_iteration_mode_runners_impl_wires_semantic_validation_collector() -> None:
    captured: dict[str, object] = {}

    def _run_semantic_badge_iteration_fn(**kwargs):
        collector = kwargs["collect_semantic_badge_validation_logs_fn"]
        collector(sample=1)
        kwargs["build_semantic_ok_validation_outcome_fn"](answer=42)
        captured.update(kwargs)
        return "semantic-ok"

    def _collect_semantic_badge_validation_logs_fn(**kwargs):
        captured["collector_kwargs"] = kwargs
        return ["ok"]

    def _build_semantic_ok_validation_outcome_fn(**kwargs):
        captured["semantic_ok_kwargs"] = kwargs
        return {"status": "ok"}

    mode_runners = helpers.buildIterationModeRunnersImpl(
        np_module=object(),
        make_badge_params_fn=lambda *_args, **_kwargs: {},
        generate_badge_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        validate_semantic_description_alignment_fn=lambda *_args, **_kwargs: True,
        detect_semantic_primitives_fn=lambda *_args, **_kwargs: {},
        build_semantic_connector_debug_line_fn=lambda *_args, **_kwargs: "debug",
        build_semantic_mismatch_console_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_mismatch_validation_log_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_mismatch_outcome_fn=lambda *_args, **_kwargs: {},
        build_semantic_audit_log_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_audit_record_kwargs_fn=lambda *_args, **_kwargs: {},
        semantic_audit_record_fn=lambda *_args, **_kwargs: None,
        resolve_semantic_validation_debug_dir_fn=lambda *_args, **_kwargs: None,
        collect_semantic_badge_validation_logs_fn=_collect_semantic_badge_validation_logs_fn,
        validate_badge_by_elements_fn=lambda *_args, **_kwargs: ("ok", []),
        prepare_semantic_badge_post_validation_fn=lambda *_args, **_kwargs: {},
        append_semantic_connector_expectation_log_fn=lambda *_args, **_kwargs: None,
        build_semantic_ok_validation_outcome_fn=_build_semantic_ok_validation_outcome_fn,
        build_semantic_ok_validation_log_lines_fn=lambda *_args, **_kwargs: [],
        semantic_quality_flags_fn=lambda *_args, **_kwargs: {},
        finalize_semantic_badge_run_fn=lambda *_args, **_kwargs: None,
        finalize_semantic_badge_iteration_result_fn=lambda *_args, **_kwargs: None,
        finalize_ac0223_badge_params_fn=lambda *_args, **_kwargs: {},
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: None,
        calculate_error_fn=lambda *_args, **_kwargs: 0.0,
        enforce_semantic_connector_expectation_fn=lambda *_args, **_kwargs: {},
        apply_redraw_variation_fn=lambda *_args, **_kwargs: {},
        print_fn=lambda _msg: None,
        run_semantic_badge_iteration_fn=_run_semantic_badge_iteration_fn,
        detect_dual_arrow_badge_params_fn=lambda *_args, **_kwargs: {},
        generate_dual_arrow_badge_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        run_dual_arrow_badge_iteration_fn=lambda **_kwargs: "dual",
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        build_gradient_stripe_validation_log_lines_fn=lambda *_args, **_kwargs: [],
        run_non_composite_iteration_fn=lambda **_kwargs: "non-composite",
        generate_composite_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        create_diff_image_fn=lambda *_args, **_kwargs: None,
        run_composite_iteration_fn=lambda **_kwargs: "composite",
    )

    result = mode_runners["run_semantic_badge_iteration"](base="AC0838_S")

    assert result == "semantic-ok"
    assert captured["collector_kwargs"]["sample"] == 1
    assert callable(captured["collector_kwargs"]["validate_badge_by_elements_fn"])
    assert captured["semantic_ok_kwargs"]["answer"] == 42
    assert callable(captured["semantic_ok_kwargs"]["build_semantic_ok_validation_log_lines_fn"])


def test_build_iteration_mode_runners_impl_wires_dual_arrow_detector_with_numpy_module() -> None:
    captured: dict[str, object] = {}
    sentinel_np = object()

    def _detect_dual_arrow_badge_params_fn(image, *, np_module):
        captured["detector"] = {"image": image, "np_module": np_module}
        return {"mode": "dual_arrow_badge"}

    def _run_dual_arrow_badge_iteration_fn(**kwargs):
        detect_fn = kwargs["detect_dual_arrow_badge_params_fn"]
        detect_fn("pixel-grid")
        kwargs["render_embedded_raster_svg_fn"]()
        captured["embedded_svg"] = kwargs["render_embedded_raster_svg_fn"]
        return "dual-ok"

    mode_runners = helpers.buildIterationModeRunnersImpl(
        np_module=sentinel_np,
        make_badge_params_fn=lambda *_args, **_kwargs: {},
        generate_badge_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        validate_semantic_description_alignment_fn=lambda *_args, **_kwargs: True,
        detect_semantic_primitives_fn=lambda *_args, **_kwargs: {},
        build_semantic_connector_debug_line_fn=lambda *_args, **_kwargs: "debug",
        build_semantic_mismatch_console_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_mismatch_validation_log_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_mismatch_outcome_fn=lambda *_args, **_kwargs: {},
        build_semantic_audit_log_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_audit_record_kwargs_fn=lambda *_args, **_kwargs: {},
        semantic_audit_record_fn=lambda *_args, **_kwargs: None,
        resolve_semantic_validation_debug_dir_fn=lambda *_args, **_kwargs: None,
        collect_semantic_badge_validation_logs_fn=lambda *_args, **_kwargs: [],
        validate_badge_by_elements_fn=lambda *_args, **_kwargs: ("ok", []),
        prepare_semantic_badge_post_validation_fn=lambda *_args, **_kwargs: {},
        append_semantic_connector_expectation_log_fn=lambda *_args, **_kwargs: None,
        build_semantic_ok_validation_outcome_fn=lambda *_args, **_kwargs: {},
        build_semantic_ok_validation_log_lines_fn=lambda *_args, **_kwargs: [],
        semantic_quality_flags_fn=lambda *_args, **_kwargs: {},
        finalize_semantic_badge_run_fn=lambda *_args, **_kwargs: None,
        finalize_semantic_badge_iteration_result_fn=lambda *_args, **_kwargs: None,
        finalize_ac0223_badge_params_fn=lambda *_args, **_kwargs: {},
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: None,
        calculate_error_fn=lambda *_args, **_kwargs: 0.0,
        enforce_semantic_connector_expectation_fn=lambda *_args, **_kwargs: {},
        apply_redraw_variation_fn=lambda *_args, **_kwargs: {},
        print_fn=lambda _msg: None,
        run_semantic_badge_iteration_fn=lambda **_kwargs: "semantic",
        detect_dual_arrow_badge_params_fn=_detect_dual_arrow_badge_params_fn,
        generate_dual_arrow_badge_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        run_dual_arrow_badge_iteration_fn=_run_dual_arrow_badge_iteration_fn,
        render_embedded_raster_svg_fn=lambda path: f"embedded:{path}",
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        build_gradient_stripe_validation_log_lines_fn=lambda *_args, **_kwargs: [],
        run_non_composite_iteration_fn=lambda **_kwargs: "non-composite",
        generate_composite_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        create_diff_image_fn=lambda *_args, **_kwargs: None,
        run_composite_iteration_fn=lambda **_kwargs: "composite",
    )

    result = mode_runners["run_dual_arrow_badge_iteration"](img_path="input/AC0831_S.jpg")

    assert result == "dual-ok"
    assert captured["detector"]["image"] == "pixel-grid"
    assert captured["detector"]["np_module"] is sentinel_np
