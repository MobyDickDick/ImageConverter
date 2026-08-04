import copy
import json

from tools.check_optimization_telemetry_alias_verification import (
    main,
    verification_errors,
)
from tools.record_optimization_telemetry_alias_verification import (
    build_verification_receipt,
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


def test_passed_receipt_matches_alias() -> None:
    alias = _alias()
    receipt = build_verification_receipt(
        alias,
        workflow_run_id=987,
        workflow_run_attempt=2,
        gate_status="passed",
        verification_source_sha="abc123",
    )
    assert verification_errors(alias, receipt) == []


def test_checker_reports_failed_gate_and_tampered_provenance() -> None:
    alias = _alias()
    receipt = build_verification_receipt(
        alias,
        workflow_run_id=987,
        workflow_run_attempt=2,
        gate_status="failed",
        verification_source_sha="abc123",
    )
    receipt["baseline_source_sha"] = "different"
    assert verification_errors(alias, receipt) == [
        "receipt baseline_source_sha does not match alias",
        "verification gate did not pass",
        "receipt is not marked as verified",
    ]


def test_checker_rejects_verified_flag_inconsistent_with_status() -> None:
    alias = _alias()
    receipt = build_verification_receipt(
        alias,
        workflow_run_id=987,
        workflow_run_attempt=2,
        gate_status="cancelled",
        verification_source_sha="abc123",
    )
    receipt["verified"] = True
    assert "verification gate did not pass" in verification_errors(alias, receipt)


def test_checker_rejects_tampered_verification_source_revision() -> None:
    alias = _alias()
    receipt = build_verification_receipt(
        alias,
        workflow_run_id=987,
        workflow_run_attempt=2,
        gate_status="passed",
        verification_source_sha="abc123",
    )
    receipt["verification_source_sha"] = "different"
    assert verification_errors(alias, receipt) == [
        "verification source SHA does not match alias"
    ]


def test_checker_rejects_missing_verification_run_attempt() -> None:
    alias = _alias()
    receipt = build_verification_receipt(
        alias,
        workflow_run_id=987,
        workflow_run_attempt=2,
        gate_status="passed",
        verification_source_sha="abc123",
    )
    del receipt["verification_workflow_run_attempt"]
    assert verification_errors(alias, receipt) == [
        "verification workflow run attempt is not a positive integer"
    ]


def test_cli_returns_nonzero_for_receipt_from_other_alias(
    tmp_path, monkeypatch, capsys
) -> None:
    alias = _alias()
    other_alias = copy.deepcopy(alias)
    other_alias["run_id"] = "789"
    receipt = build_verification_receipt(
        other_alias,
        workflow_run_id=987,
        workflow_run_attempt=2,
        gate_status="passed",
        verification_source_sha="abc123",
    )
    alias_path = tmp_path / "alias.json"
    receipt_path = tmp_path / "receipt.json"
    alias_path.write_text(json.dumps(alias), encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check.py", str(alias_path), str(receipt_path)])

    assert main() == 1
    assert "baseline_run_id does not match alias" in capsys.readouterr().out


def test_cli_reports_all_document_loading_errors(tmp_path, monkeypatch, capsys) -> None:
    alias_path = tmp_path / "alias.json"
    receipt_path = tmp_path / "receipt.json"
    alias_path.write_text("{not-json", encoding="utf-8")
    receipt_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check.py", str(alias_path), str(receipt_path)])

    assert main() == 1
    output = capsys.readouterr().out
    assert "Telemetry alias verification: FAIL" in output
    assert "alias is not valid JSON: line 1 column 2" in output
    assert "receipt root must be a JSON object" in output


def test_cli_reports_missing_documents_as_gate_failure(
    tmp_path, monkeypatch, capsys
) -> None:
    alias_path = tmp_path / "missing-alias.json"
    receipt_path = tmp_path / "missing-receipt.json"
    monkeypatch.setattr("sys.argv", ["check.py", str(alias_path), str(receipt_path)])

    assert main() == 1
    output = capsys.readouterr().out
    assert output.count("cannot read") == 2
