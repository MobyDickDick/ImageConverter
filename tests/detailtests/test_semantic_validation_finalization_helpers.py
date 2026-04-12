from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticValidationFinalization as helpers


def test_append_semantic_connector_expectation_log_impl_appends_guard_for_arm() -> None:
    lines = helpers.appendSemanticConnectorExpectationLogImpl(
        validation_logs=["semantic-guard: Textmodus aktiv"],
        badge_params={"arm_enabled": True},
    )

    assert lines == [
        "semantic-guard: Textmodus aktiv",
        "semantic-guard: Erwartete Arm-Geometrie bestätigt/wiederhergestellt (z.B. AC0812 links).",
    ]


def test_build_semantic_ok_validation_outcome_impl_updates_audit_and_lines() -> None:
    captured: dict[str, object] = {}

    def semantic_audit_record_fn(*, base_name: str, **kwargs):
        captured["base_name"] = base_name
        captured["status"] = kwargs.get("status")
        return {"status": kwargs.get("status")}

    def build_semantic_audit_record_kwargs_fn(*, filename: str, params: dict[str, object], status: str):
        captured["filename"] = filename
        captured["params"] = params
        return {"status": status}

    def semantic_quality_flags_fn(base_name: str, validation_logs: list[str]) -> list[str]:
        captured["quality_base_name"] = base_name
        captured["quality_logs"] = validation_logs
        return ["quality_flag=ok"]

    def build_semantic_audit_log_lines_fn(semantic_audit_row: dict[str, object] | None) -> list[str]:
        return [f"semantic_audit_status={semantic_audit_row['status']}"] if semantic_audit_row else []

    def build_semantic_ok_validation_log_lines_fn(*, semantic_audit_lines, quality_flags, redraw_variation_logs, validation_logs):
        return [
            "status=semantic_ok",
            *semantic_audit_lines,
            *quality_flags,
            *redraw_variation_logs,
            *validation_logs,
        ]

    updated_row, lines = helpers.buildSemanticOkValidationOutcomeImpl(
        base_name="AC0812_L",
        filename="AC0812_L.jpg",
        params={"mode": "semantic_badge"},
        semantic_audit_row={"status": "semantic_pending"},
        validation_logs=["semantic-guard: Textmodus aktiv"],
        redraw_variation_logs=["redraw_variation=none"],
        semantic_quality_flags_fn=semantic_quality_flags_fn,
        semantic_audit_record_fn=semantic_audit_record_fn,
        build_semantic_audit_record_kwargs_fn=build_semantic_audit_record_kwargs_fn,
        build_semantic_audit_log_lines_fn=build_semantic_audit_log_lines_fn,
        build_semantic_ok_validation_log_lines_fn=build_semantic_ok_validation_log_lines_fn,
    )

    assert updated_row == {"status": "semantic_ok"}
    assert captured["base_name"] == "AC0812_L"
    assert captured["filename"] == "AC0812_L.jpg"
    assert captured["status"] == "semantic_ok"
    assert captured["quality_base_name"] == "AC0812_L"
    assert captured["quality_logs"] == ["semantic-guard: Textmodus aktiv"]
    assert lines == [
        "status=semantic_ok",
        "semantic_audit_status=semantic_ok",
        "quality_flag=ok",
        "redraw_variation=none",
        "semantic-guard: Textmodus aktiv",
    ]
