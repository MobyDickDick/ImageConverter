from __future__ import annotations

from typing import Any, Callable


def buildPrepareIterationInputRuntimeForRunKwargsImpl(
    *,
    img_path: str,
    csv_path: str,
    perception_cls,
    reflection_cls,
    detect_gradient_stripe_strategy_fn,
    build_pending_semantic_audit_row_fn,
    should_create_semantic_audit_for_base_name_fn,
    get_base_name_from_file_fn,
    build_semantic_audit_record_kwargs_fn,
    semantic_audit_record_fn,
    np_module,
    print_fn,
) -> dict[str, Any]:
    return {
        "img_path": img_path,
        "csv_path": csv_path,
        "perception_cls": perception_cls,
        "reflection_cls": reflection_cls,
        "detect_gradient_stripe_strategy_fn": detect_gradient_stripe_strategy_fn,
        "build_pending_semantic_audit_row_fn": build_pending_semantic_audit_row_fn,
        "should_create_semantic_audit_for_base_name_fn": should_create_semantic_audit_for_base_name_fn,
        "get_base_name_from_file_fn": get_base_name_from_file_fn,
        "build_semantic_audit_record_kwargs_fn": build_semantic_audit_record_kwargs_fn,
        "semantic_audit_record_fn": semantic_audit_record_fn,
        "np_module": np_module,
        "print_fn": print_fn,
    }


def buildPrepareIterationRuntimeCallbacksForRunKwargsImpl(
    *,
    filename: str,
    params: dict[str, Any],
    reports_out_dir: str | None,
    svg_out_dir: str,
    diff_out_dir: str,
    target_img,
    width: int,
    height: int,
    run_seed: int,
    pass_seed_offset: int,
    time_ns_fn,
    render_svg_to_numpy_fn,
    create_diff_image_fn,
    cv2_module,
    iteration_setup_helpers,
    iteration_runtime_helpers,
    print_fn,
) -> dict[str, Any]:
    return {
        "filename": filename,
        "params": params,
        "reports_out_dir": reports_out_dir,
        "svg_out_dir": svg_out_dir,
        "diff_out_dir": diff_out_dir,
        "target_img": target_img,
        "width": width,
        "height": height,
        "run_seed": run_seed,
        "pass_seed_offset": pass_seed_offset,
        "time_ns_fn": time_ns_fn,
        "render_svg_to_numpy_fn": render_svg_to_numpy_fn,
        "create_diff_image_fn": create_diff_image_fn,
        "cv2_module": cv2_module,
        "iteration_setup_helpers": iteration_setup_helpers,
        "iteration_runtime_helpers": iteration_runtime_helpers,
        "print_fn": print_fn,
    }


def prepareIterationInputRuntimeForRunImpl(
    *,
    prepare_iteration_inputs_fn: Callable[..., dict[str, Any] | None],
    extract_iteration_input_bindings_fn: Callable[..., dict[str, Any]],
    extract_iteration_input_runtime_fields_fn: Callable[..., dict[str, Any]],
    prepare_iteration_inputs_kwargs: dict[str, Any],
) -> dict[str, Any] | None:
    iteration_inputs = prepare_iteration_inputs_fn(**prepare_iteration_inputs_kwargs)
    if iteration_inputs is None:
        return None
    iteration_input_bindings = extract_iteration_input_bindings_fn(
        iteration_inputs=iteration_inputs,
    )
    return extract_iteration_input_runtime_fields_fn(
        iteration_input_bindings=iteration_input_bindings,
    )


def prepareIterationRuntimeCallbacksForRunImpl(
    *,
    prepare_iteration_runtime_fn: Callable[..., dict[str, Any]],
    extract_iteration_runtime_bindings_fn: Callable[..., dict[str, Any]],
    extract_iteration_runtime_callbacks_fn: Callable[..., dict[str, Any]],
    prepare_iteration_runtime_kwargs: dict[str, Any],
) -> dict[str, Any]:
    iteration_runtime_state = prepare_iteration_runtime_fn(
        **prepare_iteration_runtime_kwargs,
    )
    iteration_runtime_bindings = extract_iteration_runtime_bindings_fn(
        iteration_runtime_state=iteration_runtime_state,
    )
    return extract_iteration_runtime_callbacks_fn(
        iteration_runtime_bindings=iteration_runtime_bindings,
    )
