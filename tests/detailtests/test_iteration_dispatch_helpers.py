from src.iCCModules import imageCompositeConverterIterationDispatch as iteration_dispatch_helpers


def test_run_prepared_iteration_mode_impl_routes_semantic_badge_with_core_fields() -> None:
    captured: dict[str, object] = {}

    def _fake_semantic_runtime(**kwargs):
        captured.update(kwargs)
        return ("AC0838_S", "desc", {"mode": "semantic_badge"}, 2, 0.42)

    result = iteration_dispatch_helpers.runPreparedIterationModeImpl(
        mode="semantic_badge",
        width=80,
        height=40,
        params={"mode": "semantic_badge"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        folder_path="input",
        img_path="input/AC0838_S.jpg",
        filename="AC0838_S.jpg",
        base_name="AC0838_S",
        description="desc",
        perc_img=[[1]],
        perc_base_name="AC0838_S",
        semantic_audit_row={"status": "pending"},
        max_iterations=3,
        badge_validation_rounds=7,
        debug_element_diff_dir="debug-elements",
        debug_ac0811_dir="debug-ac0811",
        write_validation_log_fn=lambda _lines: None,
        write_attempt_artifacts_fn=lambda _svg, _rendered=None: None,
        record_render_failure_fn=lambda _reason, **_kwargs: None,
        run_semantic_badge_iteration_fn=_fake_semantic_runtime,
        run_dual_arrow_badge_iteration_fn=lambda **_kwargs: None,
        run_non_composite_iteration_fn=lambda **_kwargs: None,
        run_composite_iteration_fn=lambda **_kwargs: None,
        calculate_error_fn=lambda _a, _b: 0.0,
        print_fn=lambda _message: None,
    )

    assert result == ("AC0838_S", "desc", {"mode": "semantic_badge"}, 2, 0.42)
    assert captured["base"] == "AC0838_S"
    assert captured["badge_validation_rounds"] == 7
    assert captured["debug_element_diff_dir"] == "debug-elements"


def test_run_prepared_iteration_mode_impl_routes_composite_with_iteration_context() -> None:
    captured: dict[str, object] = {}

    def _fake_composite_runtime(**kwargs):
        captured.update(kwargs)
        return ("AC0800_S", "desc", {"mode": "composite"}, 5, 0.11)

    result = iteration_dispatch_helpers.runPreparedIterationModeImpl(
        mode="composite",
        width=64,
        height=64,
        params={"mode": "composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        folder_path="input-folder",
        img_path="input/AC0800_S.jpg",
        filename="AC0800_S.jpg",
        base_name="AC0800_S",
        description="desc",
        perc_img=[[1]],
        perc_base_name="AC0800_S",
        semantic_audit_row=None,
        max_iterations=12,
        badge_validation_rounds=4,
        debug_element_diff_dir=None,
        debug_ac0811_dir=None,
        write_validation_log_fn=lambda _lines: None,
        write_attempt_artifacts_fn=lambda _svg, _rendered=None: None,
        record_render_failure_fn=lambda _reason, **_kwargs: None,
        run_semantic_badge_iteration_fn=lambda **_kwargs: None,
        run_dual_arrow_badge_iteration_fn=lambda **_kwargs: None,
        run_non_composite_iteration_fn=lambda **_kwargs: None,
        run_composite_iteration_fn=_fake_composite_runtime,
        calculate_error_fn=lambda _a, _b: 0.0,
        print_fn=lambda _message: None,
    )

    assert result == ("AC0800_S", "desc", {"mode": "composite"}, 5, 0.11)
    assert captured["max_iterations"] == 12
    assert captured["folder_path"] == "input-folder"
    assert callable(captured["write_attempt_artifacts_fn"])
