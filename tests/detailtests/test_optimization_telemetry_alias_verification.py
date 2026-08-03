import json

import pytest

from tools.record_optimization_telemetry_alias_verification import (
    build_verification_receipt,
    main,
)


def _alias() -> dict[str, object]:
    return {
        "schema_version": "optimization_render_telemetry_baseline_alias_v1",
        "run_id": "456",
        "artifact_name": "optimization-render-telemetry-baseline-456-2",
        "source_sha": "abc123",
        "verification_dispatch": {
            "workflow": "optimization-render-telemetry-gate-example.yml",
            "inputs": {
                "shard_start": "AC0100_S",
                "shard_end": "AC0100_S",
                "promote_baseline": False,
            },
        },
    }


def test_build_verification_receipt_binds_passed_run_to_alias() -> None:
    receipt = build_verification_receipt(
        _alias(), workflow_run_id=987, gate_status="passed"
    )
    assert receipt == {
        "schema_version": "optimization_render_telemetry_alias_verification_v1",
        "verification_workflow_run_id": 987,
        "gate_status": "passed",
        "verified": True,
        "workflow": "optimization-render-telemetry-gate-example.yml",
        "verification_inputs": {
            "shard_start": "AC0100_S",
            "shard_end": "AC0100_S",
            "promote_baseline": False,
        },
        "baseline_run_id": "456",
        "baseline_artifact_name": "optimization-render-telemetry-baseline-456-2",
        "baseline_source_sha": "abc123",
    }


def test_failed_verification_is_recorded_without_being_verified() -> None:
    receipt = build_verification_receipt(
        _alias(), workflow_run_id=987, gate_status="failed"
    )
    assert receipt["gate_status"] == "failed"
    assert receipt["verified"] is False


@pytest.mark.parametrize("workflow_run_id", [0, -1, True])
def test_build_verification_receipt_rejects_invalid_run_id(workflow_run_id: int) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        build_verification_receipt(
            _alias(), workflow_run_id=workflow_run_id, gate_status="passed"
        )


def test_verification_receipt_cli_writes_machine_readable_result(
    tmp_path, monkeypatch
) -> None:
    alias_path = tmp_path / "alias.json"
    receipt_path = tmp_path / "receipt.json"
    alias_path.write_text(json.dumps(_alias()), encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "record_verification.py",
            str(alias_path),
            str(receipt_path),
            "--workflow-run-id",
            "987",
            "--gate-status",
            "passed",
        ],
    )
    assert main() == 0
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["verified"] is True
