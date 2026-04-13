from __future__ import annotations

from collections.abc import Callable
from typing import Any


class IterationInitializationResult(dict):
    """Dictionary-like container for initialized iteration runtime artifacts."""


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
