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


def extractIterationInputRuntimeLocalsImpl(
    *,
    iteration_input_runtime_fields: dict[str, Any],
) -> dict[str, Any]:
    return {
        "folder_path": iteration_input_runtime_fields["folder_path"],
        "filename": iteration_input_runtime_fields["filename"],
        "perception": iteration_input_runtime_fields["perception"],
        "width": iteration_input_runtime_fields["width"],
        "height": iteration_input_runtime_fields["height"],
        "description": iteration_input_runtime_fields["description"],
        "params": iteration_input_runtime_fields["params"],
        "stripe_strategy": iteration_input_runtime_fields["stripe_strategy"],
        "semantic_audit_row": iteration_input_runtime_fields["semantic_audit_row"],
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


def extractIterationRuntimeCallbackLocalsImpl(
    *,
    iteration_runtime_callbacks: dict[str, Any],
) -> dict[str, Any]:
    return {
        "base_name": iteration_runtime_callbacks["base_name"],
        "write_validation_log": iteration_runtime_callbacks["write_validation_log"],
        "write_attempt_artifacts": iteration_runtime_callbacks["write_attempt_artifacts"],
        "record_render_failure": iteration_runtime_callbacks["record_render_failure"],
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


def extractIterationModeRuntimeLocalsImpl(
    *,
    iteration_mode_runtime_fields: dict[str, Any],
) -> dict[str, Any]:
    return {
        "params": iteration_mode_runtime_fields["params"],
        "semantic_mode_visual_override": iteration_mode_runtime_fields["semantic_mode_visual_override"],
        "mode_runners": iteration_mode_runtime_fields["mode_runners"],
    }


def extractRunIterationPipelineLocalsImpl(
    *,
    iteration_input_runtime_locals: dict[str, Any],
    iteration_runtime_callback_locals: dict[str, Any],
    iteration_mode_runtime_locals: dict[str, Any],
) -> dict[str, Any]:
    return {
        "folder_path": iteration_input_runtime_locals["folder_path"],
        "filename": iteration_input_runtime_locals["filename"],
        "perception": iteration_input_runtime_locals["perception"],
        "width": iteration_input_runtime_locals["width"],
        "height": iteration_input_runtime_locals["height"],
        "description": iteration_input_runtime_locals["description"],
        "params": iteration_mode_runtime_locals["params"],
        "stripe_strategy": iteration_input_runtime_locals["stripe_strategy"],
        "semantic_audit_row": iteration_input_runtime_locals["semantic_audit_row"],
        "base_name": iteration_runtime_callback_locals["base_name"],
        "write_validation_log": iteration_runtime_callback_locals["write_validation_log"],
        "write_attempt_artifacts": iteration_runtime_callback_locals["write_attempt_artifacts"],
        "record_render_failure": iteration_runtime_callback_locals["record_render_failure"],
        "semantic_mode_visual_override": iteration_mode_runtime_locals["semantic_mode_visual_override"],
        "mode_runners": iteration_mode_runtime_locals["mode_runners"],
    }
