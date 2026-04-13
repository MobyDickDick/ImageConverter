"""Runtime helpers for iteration artifact/log callback wiring."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import imageCompositeConverterIterationArtifacts as iteration_artifact_helpers


class IterationArtifactCallbacks(dict):
    """Dictionary-like container for iteration callback functions."""


def buildIterationArtifactCallbacksImpl(
    *,
    filename: str,
    base_name: str,
    log_path: str | None,
    svg_out_dir: str,
    diff_out_dir: str,
    target_img,
    width: int,
    height: int,
    run_seed: int,
    pass_seed_offset: int,
    time_ns_fn: Callable[[], int],
    render_svg_to_numpy_fn: Callable[[str, int, int], Any],
    create_diff_image_fn,
    cv2_module,
) -> IterationArtifactCallbacks:
    """Build and return callback functions used by runIterationPipeline."""

    def write_validation_log(lines: list[str]) -> None:
        iteration_artifact_helpers.writeValidationLogImpl(
            log_path=log_path,
            lines=lines,
            run_seed=run_seed,
            pass_seed_offset=pass_seed_offset,
            time_ns_fn=time_ns_fn,
        )

    def write_attempt_artifacts(svg_content: str, rendered_img=None, diff_img=None, *, failed: bool = False) -> None:
        iteration_artifact_helpers.writeAttemptArtifactsImpl(
            svg_out_dir=svg_out_dir,
            diff_out_dir=diff_out_dir,
            base_name=base_name,
            svg_content=svg_content,
            target_img=target_img,
            render_svg_to_numpy_fn=lambda svg: render_svg_to_numpy_fn(svg, width, height),
            create_diff_image_fn=create_diff_image_fn,
            cv2_module=cv2_module,
            rendered_img=rendered_img,
            diff_img=diff_img,
            failed=failed,
        )

    def record_render_failure(
        reason: str,
        *,
        svg_content: str | None = None,
        params_snapshot: dict[str, object] | None = None,
    ) -> None:
        iteration_artifact_helpers.writeRenderFailureLogImpl(
            reason=reason,
            filename=filename,
            base_name=base_name,
            write_attempt_artifacts_fn=write_attempt_artifacts,
            write_validation_log_fn=write_validation_log,
            svg_content=svg_content,
            params_snapshot=params_snapshot,
        )

    return IterationArtifactCallbacks(
        write_validation_log=write_validation_log,
        write_attempt_artifacts=write_attempt_artifacts,
        record_render_failure=record_render_failure,
    )
