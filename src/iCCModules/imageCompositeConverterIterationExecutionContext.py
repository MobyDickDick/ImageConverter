from __future__ import annotations

from typing import Any


def buildPreparedModeBuilderKwargsForRunImpl(
    *,
    run_locals: dict[str, Any],
    img_path: str,
    max_iterations: int,
    badge_validation_rounds: int,
    debug_element_diff_dir: str | None,
    debug_ac0811_dir: str | None,
    calculate_error_fn,
    print_fn,
) -> dict[str, Any]:
    return {
        "params": run_locals["params"],
        "width": run_locals["width"],
        "height": run_locals["height"],
        "stripe_strategy": run_locals["stripe_strategy"],
        "semantic_mode_visual_override": run_locals["semantic_mode_visual_override"],
        "folder_path": run_locals["folder_path"],
        "img_path": img_path,
        "filename": run_locals["filename"],
        "base_name": run_locals["base_name"],
        "description": run_locals["description"],
        "perc_img": run_locals["perception"].img,
        "perc_base_name": run_locals["perception"].base_name,
        "semantic_audit_row": run_locals["semantic_audit_row"],
        "max_iterations": max_iterations,
        "badge_validation_rounds": badge_validation_rounds,
        "debug_element_diff_dir": debug_element_diff_dir,
        "debug_ac0811_dir": debug_ac0811_dir,
        "write_validation_log_fn": run_locals["write_validation_log"],
        "write_attempt_artifacts_fn": run_locals["write_attempt_artifacts"],
        "record_render_failure_fn": run_locals["record_render_failure"],
        "mode_runners": run_locals["mode_runners"],
        "calculate_error_fn": calculate_error_fn,
        "print_fn": print_fn,
    }


def buildRunPreparedIterationAndFinalizeKwargsImpl(
    *,
    params: dict[str, Any],
    prepared_mode_builder_kwargs: dict[str, Any],
    build_prepared_iteration_mode_kwargs_fn,
    run_prepared_iteration_mode_fn,
    finalize_iteration_result_fn,
    math_module,
) -> dict[str, Any]:
    return {
        "params": params,
        "prepared_mode_builder_kwargs": prepared_mode_builder_kwargs,
        "build_prepared_iteration_mode_kwargs_fn": build_prepared_iteration_mode_kwargs_fn,
        "run_prepared_iteration_mode_fn": run_prepared_iteration_mode_fn,
        "finalize_iteration_result_fn": finalize_iteration_result_fn,
        "math_module": math_module,
    }


def buildPreparedModeBuilderKwargsForRunPipelineImpl(
    *,
    run_locals: dict[str, Any],
    img_path: str,
    max_iterations: int,
    badge_validation_rounds: int,
    debug_element_diff_dir: str | None,
    debug_ac0811_dir: str | None,
    calculate_error_fn,
    print_fn,
    build_prepared_mode_builder_kwargs_for_run_fn,
    build_prepared_mode_builder_kwargs_fn,
):
    return build_prepared_mode_builder_kwargs_fn(
        **build_prepared_mode_builder_kwargs_for_run_fn(
            run_locals=run_locals,
            img_path=img_path,
            max_iterations=max_iterations,
            badge_validation_rounds=badge_validation_rounds,
            debug_element_diff_dir=debug_element_diff_dir,
            debug_ac0811_dir=debug_ac0811_dir,
            calculate_error_fn=calculate_error_fn,
            print_fn=print_fn,
        )
    )


def runPreparedIterationAndFinalizeForRunImpl(
    *,
    params: dict[str, Any],
    prepared_mode_builder_kwargs: dict[str, Any],
    build_run_prepared_iteration_and_finalize_kwargs_fn,
    run_prepared_iteration_and_finalize_fn,
    build_prepared_iteration_mode_kwargs_fn,
    run_prepared_iteration_mode_fn,
    finalize_iteration_result_fn,
    math_module,
):
    return run_prepared_iteration_and_finalize_fn(
        **build_run_prepared_iteration_and_finalize_kwargs_fn(
            params=params,
            prepared_mode_builder_kwargs=prepared_mode_builder_kwargs,
            build_prepared_iteration_mode_kwargs_fn=build_prepared_iteration_mode_kwargs_fn,
            run_prepared_iteration_mode_fn=run_prepared_iteration_mode_fn,
            finalize_iteration_result_fn=finalize_iteration_result_fn,
            math_module=math_module,
        )
    )


def executeRunIterationPipelineImpl(
    *,
    run_locals: dict[str, Any],
    img_path: str,
    max_iterations: int,
    badge_validation_rounds: int,
    debug_element_diff_dir: str | None,
    debug_ac0811_dir: str | None,
    calculate_error_fn,
    print_fn,
    build_prepared_mode_builder_kwargs_for_run_pipeline_fn,
    build_prepared_mode_builder_kwargs_for_run_fn,
    build_prepared_mode_builder_kwargs_fn,
    run_prepared_iteration_and_finalize_for_run_fn,
    build_run_prepared_iteration_and_finalize_kwargs_fn,
    run_prepared_iteration_and_finalize_fn,
    build_prepared_iteration_mode_kwargs_fn,
    run_prepared_iteration_mode_fn,
    finalize_iteration_result_fn,
    math_module,
):
    prepared_mode_builder_kwargs = build_prepared_mode_builder_kwargs_for_run_pipeline_fn(
        run_locals=run_locals,
        img_path=img_path,
        max_iterations=max_iterations,
        badge_validation_rounds=badge_validation_rounds,
        debug_element_diff_dir=debug_element_diff_dir,
        debug_ac0811_dir=debug_ac0811_dir,
        calculate_error_fn=calculate_error_fn,
        print_fn=print_fn,
        build_prepared_mode_builder_kwargs_for_run_fn=build_prepared_mode_builder_kwargs_for_run_fn,
        build_prepared_mode_builder_kwargs_fn=build_prepared_mode_builder_kwargs_fn,
    )
    return run_prepared_iteration_and_finalize_for_run_fn(
        params=run_locals["params"],
        prepared_mode_builder_kwargs=prepared_mode_builder_kwargs,
        build_run_prepared_iteration_and_finalize_kwargs_fn=build_run_prepared_iteration_and_finalize_kwargs_fn,
        run_prepared_iteration_and_finalize_fn=run_prepared_iteration_and_finalize_fn,
        build_prepared_iteration_mode_kwargs_fn=build_prepared_iteration_mode_kwargs_fn,
        run_prepared_iteration_mode_fn=run_prepared_iteration_mode_fn,
        finalize_iteration_result_fn=finalize_iteration_result_fn,
        math_module=math_module,
    )
