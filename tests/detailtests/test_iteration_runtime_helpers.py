from src.iCCModules import imageCompositeConverterIterationRuntime as iteration_runtime_helpers


def test_build_iteration_artifact_callbacks_impl_wires_validation_log_writer() -> None:
    captured: dict[str, object] = {}

    def _fake_write_validation_log_impl(**kwargs):
        captured.update(kwargs)

    original_write_validation = iteration_runtime_helpers.iteration_artifact_helpers.writeValidationLogImpl
    try:
        iteration_runtime_helpers.iteration_artifact_helpers.writeValidationLogImpl = _fake_write_validation_log_impl
        callbacks = iteration_runtime_helpers.buildIterationArtifactCallbacksImpl(
            filename="AC0800_S.jpg",
            base_name="AC0800_S",
            log_path="reports/AC0800_S_element_validation.log",
            svg_out_dir="svg",
            diff_out_dir="diff",
            target_img=[[1]],
            width=64,
            height=64,
            run_seed=5,
            pass_seed_offset=7,
            time_ns_fn=lambda: 123,
            render_svg_to_numpy_fn=lambda _svg, _w, _h: None,
            create_diff_image_fn=lambda *_args, **_kwargs: None,
            cv2_module=None,
        )
        callbacks["write_validation_log"](["status=semantic_ok"])
    finally:
        iteration_runtime_helpers.iteration_artifact_helpers.writeValidationLogImpl = original_write_validation

    assert captured["log_path"] == "reports/AC0800_S_element_validation.log"
    assert captured["lines"] == ["status=semantic_ok"]
    assert captured["run_seed"] == 5
    assert captured["pass_seed_offset"] == 7


def test_build_iteration_artifact_callbacks_impl_wires_attempt_artifacts_with_dimensions() -> None:
    captured: dict[str, object] = {}

    def _fake_write_attempt_artifacts_impl(**kwargs):
        captured.update(kwargs)

    render_calls: list[tuple[str, int, int]] = []

    def _fake_render(svg: str, width: int, height: int):
        render_calls.append((svg, width, height))
        return [[0]]

    original_write_attempt = iteration_runtime_helpers.iteration_artifact_helpers.writeAttemptArtifactsImpl
    try:
        iteration_runtime_helpers.iteration_artifact_helpers.writeAttemptArtifactsImpl = _fake_write_attempt_artifacts_impl
        callbacks = iteration_runtime_helpers.buildIterationArtifactCallbacksImpl(
            filename="AC0800_S.jpg",
            base_name="AC0800_S",
            log_path="reports/AC0800_S_element_validation.log",
            svg_out_dir="svg",
            diff_out_dir="diff",
            target_img=[[1]],
            width=80,
            height=40,
            run_seed=1,
            pass_seed_offset=0,
            time_ns_fn=lambda: 1,
            render_svg_to_numpy_fn=_fake_render,
            create_diff_image_fn=lambda *_args, **_kwargs: None,
            cv2_module=None,
        )
        callbacks["write_attempt_artifacts"]("<svg/>")
        captured["render_svg_to_numpy_fn"]("<svg-check/>")
    finally:
        iteration_runtime_helpers.iteration_artifact_helpers.writeAttemptArtifactsImpl = original_write_attempt

    assert captured["base_name"] == "AC0800_S"
    assert captured["svg_out_dir"] == "svg"
    assert captured["diff_out_dir"] == "diff"
    assert render_calls == [("<svg-check/>", 80, 40)]


def test_build_iteration_artifact_callbacks_impl_wires_render_failure_logger() -> None:
    captured: dict[str, object] = {}

    def _fake_write_render_failure_log_impl(**kwargs):
        captured.update(kwargs)

    original_write_render_failure = iteration_runtime_helpers.iteration_artifact_helpers.writeRenderFailureLogImpl
    try:
        iteration_runtime_helpers.iteration_artifact_helpers.writeRenderFailureLogImpl = _fake_write_render_failure_log_impl
        callbacks = iteration_runtime_helpers.buildIterationArtifactCallbacksImpl(
            filename="AC0838_S.jpg",
            base_name="AC0838_S",
            log_path="reports/AC0838_S_element_validation.log",
            svg_out_dir="svg",
            diff_out_dir="diff",
            target_img=[[1]],
            width=32,
            height=32,
            run_seed=2,
            pass_seed_offset=3,
            time_ns_fn=lambda: 1,
            render_svg_to_numpy_fn=lambda _svg, _w, _h: None,
            create_diff_image_fn=lambda *_args, **_kwargs: None,
            cv2_module=None,
        )
        callbacks["record_render_failure"]("render failed", svg_content="<svg/>")
    finally:
        iteration_runtime_helpers.iteration_artifact_helpers.writeRenderFailureLogImpl = original_write_render_failure

    assert captured["reason"] == "render failed"
    assert captured["filename"] == "AC0838_S.jpg"
    assert captured["base_name"] == "AC0838_S"
    assert callable(captured["write_attempt_artifacts_fn"])
    assert callable(captured["write_validation_log_fn"])
