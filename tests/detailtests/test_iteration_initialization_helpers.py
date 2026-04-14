from src.iCCModules import imageCompositeConverterIterationInitialization as iteration_initialization_helpers


class _SetupHelpers:
    def __init__(self):
        self.calls = []

    def emitIterationDescriptionHeaderImpl(self, *, filename, params, print_fn):
        self.calls.append(("header", filename, params, print_fn))

    def ensureIterationOutputDirsImpl(self, *, svg_out_dir, diff_out_dir, reports_out_dir):
        self.calls.append(("dirs", svg_out_dir, diff_out_dir, reports_out_dir))

    def buildIterationBaseAndLogPathImpl(self, *, filename, reports_out_dir):
        self.calls.append(("base", filename, reports_out_dir))
        return "AC0800_S", "reports/AC0800_S_element_validation.log"


class _RuntimeHelpers:
    def __init__(self):
        self.kwargs = None

    def buildIterationArtifactCallbacksImpl(self, **kwargs):
        self.kwargs = kwargs
        return {"write_validation_log": lambda _lines: None}


def test_prepare_iteration_runtime_impl_builds_base_and_callbacks() -> None:
    setup_helpers = _SetupHelpers()
    runtime_helpers = _RuntimeHelpers()

    result = iteration_initialization_helpers.prepareIterationRuntimeImpl(
        filename="AC0800_S.jpg",
        params={"mode": "semantic_badge"},
        reports_out_dir="reports",
        svg_out_dir="svg",
        diff_out_dir="diff",
        target_img=[[1]],
        width=64,
        height=32,
        run_seed=1,
        pass_seed_offset=2,
        iteration_setup_helpers=setup_helpers,
        iteration_runtime_helpers=runtime_helpers,
        time_ns_fn=lambda: 7,
        render_svg_to_numpy_fn=lambda _svg, _w, _h: None,
        create_diff_image_fn=lambda *_args, **_kwargs: None,
        cv2_module=None,
        print_fn=lambda _line: None,
    )

    assert result["base_name"] == "AC0800_S"
    assert result["log_path"] == "reports/AC0800_S_element_validation.log"
    assert callable(result["artifact_callbacks"]["write_validation_log"])
    assert setup_helpers.calls[0][0] == "header"
    assert setup_helpers.calls[1] == ("dirs", "svg", "diff", "reports")
    assert setup_helpers.calls[2] == ("base", "AC0800_S.jpg", "reports")
    assert runtime_helpers.kwargs["base_name"] == "AC0800_S"
    assert runtime_helpers.kwargs["log_path"] == "reports/AC0800_S_element_validation.log"


def test_extract_iteration_runtime_bindings_impl_exposes_runtime_callbacks() -> None:
    state = {
        "base_name": "AC0811_M",
        "artifact_callbacks": {
            "write_validation_log": "write-log",
            "write_attempt_artifacts": "write-artifacts",
            "record_render_failure": "record-failure",
        },
    }

    bindings = iteration_initialization_helpers.extractIterationRuntimeBindingsImpl(
        iteration_runtime_state=state
    )

    assert bindings["base_name"] == "AC0811_M"
    assert bindings["write_validation_log"] == "write-log"
    assert bindings["write_attempt_artifacts"] == "write-artifacts"
    assert bindings["record_render_failure"] == "record-failure"
