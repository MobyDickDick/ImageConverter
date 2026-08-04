from pathlib import Path

WORKFLOW = Path(".github/workflows/optimization-render-telemetry-gate-example.yml")


def test_workflow_records_checks_and_uploads_passed_alias_receipt() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    record_step = workflow.index("- name: Record and verify alias activation receipt")
    gate_assertion = workflow.index(
        'assert payload["regression_gate"]["status"] == "passed"'
    )
    upload_step = workflow.index("- name: Upload verified alias activation receipt")

    assert gate_assertion < record_step < upload_step
    assert "${{ github.run_id }}" in workflow[record_step:upload_step]
    assert "${{ github.run_attempt }}" in workflow[record_step:upload_step]
    assert "${{ github.sha }}" in workflow[record_step:upload_step]
    assert "tools/record_optimization_telemetry_alias_verification.py" in workflow
    assert "--gate-status passed" in workflow
    assert '--verification-source-sha "$VERIFICATION_SOURCE_SHA"' in workflow
    assert '--workflow-run-attempt "$VERIFICATION_WORKFLOW_RUN_ATTEMPT"' in workflow
    assert "tools/check_optimization_telemetry_alias_verification.py" in workflow
    assert "if-no-files-found: error" in workflow[upload_step:]
    assert "retention-days: 30" in workflow[upload_step:]
