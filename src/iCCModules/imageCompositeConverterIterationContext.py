from __future__ import annotations


def extractIterationInputBindingsImpl(
    *,
    iteration_inputs: dict[str, object],
) -> dict[str, object]:
    return {
        "folder_path": iteration_inputs["folder_path"],
        "filename": iteration_inputs["filename"],
        "perception": iteration_inputs["perception"],
        "width": iteration_inputs["width"],
        "height": iteration_inputs["height"],
        "description": iteration_inputs["description"],
        "params": iteration_inputs["params"],
        "stripe_strategy": iteration_inputs["stripe_strategy"],
        "semantic_audit_row": iteration_inputs["semantic_audit_row"],
    }


def extractIterationModeRuntimeBindingsImpl(
    *,
    mode_runtime: dict[str, object],
) -> dict[str, object]:
    return {
        "params": mode_runtime["params"],
        "semantic_mode_visual_override": mode_runtime["semantic_mode_visual_override"],
        "mode_runners": mode_runtime["mode_runners"],
    }


def buildPreparedIterationModeKwargsImpl(
    *,
    params: dict[str, object],
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
    semantic_audit_row: dict[str, object] | None,
    max_iterations: int,
    badge_validation_rounds: int,
    debug_element_diff_dir: str | None,
    debug_ac0811_dir: str | None,
    write_validation_log_fn,
    write_attempt_artifacts_fn,
    record_render_failure_fn,
    mode_runners: dict[str, object],
    calculate_error_fn,
    print_fn,
) -> dict[str, object]:
    return {
        "mode": str(params.get("mode", "")),
        "width": width,
        "height": height,
        "params": params,
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
        "run_semantic_badge_iteration_fn": mode_runners["run_semantic_badge_iteration"],
        "run_dual_arrow_badge_iteration_fn": mode_runners["run_dual_arrow_badge_iteration"],
        "run_non_composite_iteration_fn": mode_runners["run_non_composite_iteration"],
        "run_composite_iteration_fn": mode_runners["run_composite_iteration"],
        "calculate_error_fn": calculate_error_fn,
        "print_fn": print_fn,
    }
