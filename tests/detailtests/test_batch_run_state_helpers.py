import json
from pathlib import Path

from src.iCCModules import imageCompositeConverterBatchRunState as helpers


def test_atomic_json_write_replaces_complete_document(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    target.write_text('{"old": true}\n', encoding="utf-8")

    helpers.atomicWriteJsonImpl(target, {"new": [1, 2]})

    assert json.loads(target.read_text(encoding="utf-8")) == {"new": [1, 2]}
    assert not list(tmp_path.glob("*.tmp"))


def test_resume_snapshot_preserves_mutable_inputs(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "conversion_checkpoint.json").write_text('{"stage":"initial_pass"}', encoding="utf-8")
    (reports / "conversion_result_map.json").write_text('{"A.jpg":{}}', encoding="utf-8")

    snapshot = Path(helpers.snapshotResumeArtifactsImpl(reports, run_id="run-1"))

    assert (snapshot / "conversion_checkpoint.json").read_text(encoding="utf-8") == '{"stage":"initial_pass"}'
    assert (snapshot / "conversion_result_map.json").is_file()


def test_completion_manifest_separates_domain_technical_and_timeouts() -> None:
    manifest = helpers.buildCompletionManifestImpl(
        run_id="run-1",
        started_at="2026-10-01T00:00:00Z",
        input_count=4,
        result_map={"A.jpg": {}, "B.jpg": {}},
        failures=[
            {"status": "semantic_mismatch", "reason": "circle_missing"},
            {"status": "batch_error", "reason": "TimeoutError"},
        ],
        run_seed=529189183,
        resumed_result_count=1,
    )

    assert manifest["stage"] == "complete"
    assert manifest["successful_count"] == 2
    assert manifest["domain_failure_count"] == 1
    assert manifest["technical_failure_count"] == 1
    assert manifest["timeout_count"] == 1
