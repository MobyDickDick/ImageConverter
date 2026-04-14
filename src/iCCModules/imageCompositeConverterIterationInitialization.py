from __future__ import annotations

from collections.abc import Callable
from typing import Any


class IterationInitializationResult(dict):
    """Dictionary-like container for initialized iteration runtime artifacts."""


class IterationRuntimeBindingsResult(dict):
    """Dictionary-like container for extracted iteration runtime callback bindings."""


def prepareIterationRuntimeImpl(
    *,
    filename: str,
    params: dict[str, object],
    reports_out_dir: str | None,
    svg_out_dir: str,
    diff_out_dir: str,
    target_img,
    width: int,
    height: int,
    run_seed: int,
    pass_seed_offset: int,
    iteration_setup_helpers,
    iteration_runtime_helpers,
    time_ns_fn: Callable[[], int],
    render_svg_to_numpy_fn: Callable[[str, int, int], Any],
    create_diff_image_fn,
    cv2_module,
    print_fn=print,
) -> IterationInitializationResult:
    iteration_setup_helpers.emitIterationDescriptionHeaderImpl(
        filename=filename,
        params=params,
        print_fn=print_fn,
    )
    iteration_setup_helpers.ensureIterationOutputDirsImpl(
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        reports_out_dir=reports_out_dir,
    )
    base_name, log_path = iteration_setup_helpers.buildIterationBaseAndLogPathImpl(
        filename=filename,
        reports_out_dir=reports_out_dir,
    )
    artifact_callbacks = iteration_runtime_helpers.buildIterationArtifactCallbacksImpl(
        filename=filename,
        base_name=base_name,
        log_path=log_path,
        svg_out_dir=svg_out_dir,
        diff_out_dir=diff_out_dir,
        target_img=target_img,
        width=width,
        height=height,
        run_seed=run_seed,
        pass_seed_offset=pass_seed_offset,
        time_ns_fn=time_ns_fn,
        render_svg_to_numpy_fn=render_svg_to_numpy_fn,
        create_diff_image_fn=create_diff_image_fn,
        cv2_module=cv2_module,
    )
    return IterationInitializationResult(
        base_name=base_name,
        log_path=log_path,
        artifact_callbacks=artifact_callbacks,
    )


def extractIterationRuntimeBindingsImpl(
    *,
    iteration_runtime_state: dict[str, object],
) -> IterationRuntimeBindingsResult:
    artifact_callbacks = dict(iteration_runtime_state.get("artifact_callbacks") or {})
    return IterationRuntimeBindingsResult(
        base_name=str(iteration_runtime_state.get("base_name") or ""),
        write_validation_log=artifact_callbacks.get("write_validation_log"),
        write_attempt_artifacts=artifact_callbacks.get("write_attempt_artifacts"),
        record_render_failure=artifact_callbacks.get("record_render_failure"),
    )
