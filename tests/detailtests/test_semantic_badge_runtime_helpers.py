from src.iCCModules import imageCompositeConverterSemanticBadgeRuntime as semantic_badge_runtime_helpers


def test_run_semantic_badge_iteration_impl_returns_none_for_semantic_mismatch() -> None:
    captured = {"printed": [], "logged": []}

    result = semantic_badge_runtime_helpers.runSemanticBadgeIterationImpl(
        width=120,
        height=90,
        perc_img="img",
        perc_base_name="AC0800_S",
        filename="AC0800_S.jpg",
        base="AC0800_S",
        description="desc",
        params={"elements": ["SEMANTIC: Kreis ohne Buchstabe"]},
        semantic_audit_row=None,
        badge_validation_rounds=2,
        debug_element_diff_dir=None,
        debug_ac0811_dir=None,
        write_attempt_artifacts_fn=lambda *_args, **_kwargs: None,
        write_validation_log_fn=lambda lines: captured["logged"].extend(lines),
        record_render_failure_fn=lambda *_args, **_kwargs: None,
        make_badge_params_fn=lambda *_args, **_kwargs: {"mode": "semantic_badge"},
        generate_badge_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        validate_semantic_description_alignment_fn=lambda *_args, **_kwargs: ["issue"],
        detect_semantic_primitives_fn=lambda *_args, **_kwargs: {},
        build_semantic_connector_debug_line_fn=lambda *_args, **_kwargs: "debug",
        build_semantic_mismatch_console_lines_fn=lambda *_args, **_kwargs: ["console mismatch"],
        build_semantic_mismatch_validation_log_lines_fn=lambda *_args, **_kwargs: ["validation mismatch"],
        build_semantic_mismatch_outcome_fn=lambda **_kwargs: (None, ["console mismatch"], ["validation mismatch"]),
        build_semantic_audit_log_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_audit_record_kwargs_fn=lambda *_args, **_kwargs: {},
        semantic_audit_record_fn=lambda *_args, **_kwargs: None,
        resolve_semantic_validation_debug_dir_fn=lambda **_kwargs: None,
        collect_semantic_badge_validation_logs_fn=lambda **_kwargs: [],
        prepare_semantic_badge_post_validation_fn=lambda **_kwargs: ({}, [], []),
        append_semantic_connector_expectation_log_fn=lambda *_args, **_kwargs: None,
        build_semantic_ok_validation_outcome_fn=lambda **_kwargs: (None, []),
        semantic_quality_flags_fn=lambda *_args, **_kwargs: [],
        finalize_semantic_badge_run_fn=lambda **_kwargs: ("unexpected",),
        finalize_semantic_badge_iteration_result_fn=lambda **_kwargs: ("unexpected",),
        finalize_ac0223_badge_params_fn=lambda *_args, **_kwargs: None,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: None,
        calculate_error_fn=lambda *_args, **_kwargs: 0.0,
        enforce_semantic_connector_expectation_fn=lambda *_args, **_kwargs: None,
        apply_redraw_variation_fn=lambda *_args, **_kwargs: None,
        print_fn=lambda line: captured["printed"].append(line),
    )

    assert result is None
    assert captured["printed"] == ["console mismatch"]
    assert captured["logged"] == ["validation mismatch"]


def test_run_semantic_badge_iteration_impl_finalizes_semantic_ok() -> None:
    captured = {}

    result = semantic_badge_runtime_helpers.runSemanticBadgeIterationImpl(
        width=200,
        height=100,
        perc_img="img",
        perc_base_name="AC0811_S",
        filename="AC0811_S.jpg",
        base="AC0811_S",
        description="desc",
        params={"elements": ["SEMANTIC: Kreis mit Stiel"], "badge_overrides": {"cx": 44.0}},
        semantic_audit_row={"status": "pending"},
        badge_validation_rounds=3,
        debug_element_diff_dir=None,
        debug_ac0811_dir=None,
        write_attempt_artifacts_fn=lambda *_args, **_kwargs: None,
        write_validation_log_fn=lambda _lines: None,
        record_render_failure_fn=lambda *_args, **_kwargs: None,
        make_badge_params_fn=lambda *_args, **_kwargs: {"mode": "semantic_badge", "cx": 10.0},
        generate_badge_svg_fn=lambda *_args, **_kwargs: "<svg/>",
        validate_semantic_description_alignment_fn=lambda *_args, **_kwargs: [],
        detect_semantic_primitives_fn=lambda *_args, **_kwargs: {},
        build_semantic_connector_debug_line_fn=lambda *_args, **_kwargs: "debug",
        build_semantic_mismatch_console_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_mismatch_validation_log_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_mismatch_outcome_fn=lambda **_kwargs: (None, [], []),
        build_semantic_audit_log_lines_fn=lambda *_args, **_kwargs: [],
        build_semantic_audit_record_kwargs_fn=lambda *_args, **_kwargs: {},
        semantic_audit_record_fn=lambda *_args, **_kwargs: None,
        resolve_semantic_validation_debug_dir_fn=lambda **_kwargs: "/tmp/debug",
        collect_semantic_badge_validation_logs_fn=lambda **_kwargs: ["validation"],
        prepare_semantic_badge_post_validation_fn=lambda **kwargs: (kwargs["badge_params"], ["validation"], ["redraw"]),
        append_semantic_connector_expectation_log_fn=lambda *_args, **_kwargs: None,
        build_semantic_ok_validation_outcome_fn=lambda **_kwargs: ({"status": "ok"}, ["status=semantic_ok"]),
        semantic_quality_flags_fn=lambda *_args, **_kwargs: [],
        finalize_semantic_badge_run_fn=lambda **kwargs: captured.setdefault("badge_params", kwargs["badge_params"]) or ("AC0811_S", "desc", {"mode": "semantic_badge"}, 1, 0.5),
        finalize_semantic_badge_iteration_result_fn=lambda **_kwargs: ({"mode": "semantic_badge"}, 0.5),
        finalize_ac0223_badge_params_fn=lambda *_args, **_kwargs: None,
        render_svg_to_numpy_fn=lambda *_args, **_kwargs: None,
        calculate_error_fn=lambda *_args, **_kwargs: 0.0,
        enforce_semantic_connector_expectation_fn=lambda *_args, **_kwargs: None,
        apply_redraw_variation_fn=lambda *_args, **_kwargs: None,
        print_fn=lambda _line: None,
    )

    assert result == {"mode": "semantic_badge", "cx": 44.0, "width": 200.0, "height": 100.0}
