from __future__ import annotations

from typing import Any


def buildPreparedModeBuilderKwargsImpl(
    *,
    params: dict[str, Any],
    width: int,
    height: int,
    stripe_strategy: str,
    semantic_mode_visual_override: bool,
    folder_path: str,
    img_path: str,
    filename: str,
    base_name: str,
    description: str,
    perc_img,
    perc_base_name: str,
    semantic_audit_row: dict[str, Any] | None,
    max_iterations: int,
    badge_validation_rounds: int,
    debug_element_diff_dir: str | None,
    debug_ac0811_dir: str | None,
    write_validation_log_fn,
    write_attempt_artifacts_fn,
    record_render_failure_fn,
    mode_runners: dict[str, Any],
    calculate_error_fn,
    print_fn,
) -> dict[str, Any]:
    return {
        "params": params,
        "width": width,
        "height": height,
        "stripe_strategy": stripe_strategy,
        "semantic_mode_visual_override": semantic_mode_visual_override,
        "folder_path": folder_path,
        "img_path": img_path,
        "filename": filename,
        "base_name": base_name,
        "description": description,
        "perc_img": perc_img,
        "perc_base_name": perc_base_name,
        "semantic_audit_row": semantic_audit_row,
        "max_iterations": max_iterations,
        "badge_validation_rounds": badge_validation_rounds,
        "debug_element_diff_dir": debug_element_diff_dir,
        "debug_ac0811_dir": debug_ac0811_dir,
        "write_validation_log_fn": write_validation_log_fn,
        "write_attempt_artifacts_fn": write_attempt_artifacts_fn,
        "record_render_failure_fn": record_render_failure_fn,
        "mode_runners": mode_runners,
        "calculate_error_fn": calculate_error_fn,
        "print_fn": print_fn,
    }


def runPreparedIterationAndFinalizeImpl(
    *,
    params: dict[str, Any],
    prepared_mode_builder_kwargs: dict[str, Any],
    build_prepared_iteration_mode_kwargs_fn,
    run_prepared_iteration_mode_fn,
    finalize_iteration_result_fn,
    math_module,
) -> Any:
    prepared_mode_kwargs = build_prepared_iteration_mode_kwargs_fn(
        **prepared_mode_builder_kwargs,
    )
    mode_result = run_prepared_iteration_mode_fn(**prepared_mode_kwargs)
    return finalize_iteration_result_fn(
        mode=str(params.get("mode", "")),
        mode_result=mode_result,
        math_module=math_module,
    )
