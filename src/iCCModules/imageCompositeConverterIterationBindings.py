from __future__ import annotations

from typing import Any


def extractIterationInputRuntimeFieldsImpl(
    *,
    iteration_input_bindings: dict[str, Any],
) -> dict[str, Any]:
    return {
        "folder_path": iteration_input_bindings["folder_path"],
        "filename": iteration_input_bindings["filename"],
        "perception": iteration_input_bindings["perception"],
        "width": iteration_input_bindings["width"],
        "height": iteration_input_bindings["height"],
        "description": iteration_input_bindings["description"],
        "params": iteration_input_bindings["params"],
        "stripe_strategy": iteration_input_bindings["stripe_strategy"],
        "semantic_audit_row": iteration_input_bindings["semantic_audit_row"],
    }


def extractIterationRuntimeCallbacksImpl(
    *,
    iteration_runtime_bindings: dict[str, Any],
) -> dict[str, Any]:
    return {
        "base_name": iteration_runtime_bindings["base_name"],
        "write_validation_log": iteration_runtime_bindings["write_validation_log"],
        "write_attempt_artifacts": iteration_runtime_bindings["write_attempt_artifacts"],
        "record_render_failure": iteration_runtime_bindings["record_render_failure"],
    }


def extractIterationModeRuntimeBindingsImpl(
    *,
    iteration_mode_runtime_bindings: dict[str, Any],
) -> dict[str, Any]:
    return {
        "params": iteration_mode_runtime_bindings["params"],
        "semantic_mode_visual_override": iteration_mode_runtime_bindings["semantic_mode_visual_override"],
        "mode_runners": iteration_mode_runtime_bindings["mode_runners"],
    }
