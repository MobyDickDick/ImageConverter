from __future__ import annotations

from typing import Any, Callable


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
