import json

import pytest

from tools.build_optimization_telemetry_baseline_alias import build_baseline_alias, main


def _provenance() -> dict[str, object]:
    return {
        "schema_version": "optimization_render_telemetry_baseline_provenance_v1",
        "source_sha": "abc123",
        "source_run_id": 456,
        "source_run_attempt": 2,
        "shard_start": "AC0100_S",
        "shard_end": "AC0100_S",
    }


def test_build_baseline_alias_maps_both_repository_variables() -> None:
    alias = build_baseline_alias(_provenance())
    assert alias["run_id"] == "456"
    assert alias["artifact_name"] == "optimization-render-telemetry-baseline-456-2"
    assert alias["repository_variables"] == {
        "OPTIMIZATION_RENDER_TELEMETRY_BASELINE_RUN_ID": "456",
        "OPTIMIZATION_RENDER_TELEMETRY_BASELINE_ARTIFACT_NAME": "optimization-render-telemetry-baseline-456-2",
    }
    assert alias["activation_commands"] == [
        "gh variable set OPTIMIZATION_RENDER_TELEMETRY_BASELINE_RUN_ID --body 456",
        "gh variable set OPTIMIZATION_RENDER_TELEMETRY_BASELINE_ARTIFACT_NAME "
        "--body optimization-render-telemetry-baseline-456-2",
    ]
    assert alias["verification_dispatch"] == {
        "workflow": "optimization-render-telemetry-gate-example.yml",
        "inputs": {
            "shard_start": "AC0100_S",
            "shard_end": "AC0100_S",
            "promote_baseline": False,
        },
    }


@pytest.mark.parametrize("field,value", [("source_run_id", 0), ("source_run_attempt", True)])
def test_build_baseline_alias_rejects_invalid_identity(field: str, value: object) -> None:
    provenance = _provenance()
    provenance[field] = value
    with pytest.raises(ValueError, match="positive integer"):
        build_baseline_alias(provenance)


@pytest.mark.parametrize("field,value", [("shard_start", ""), ("shard_end", None)])
def test_build_baseline_alias_rejects_invalid_shard(field: str, value: object) -> None:
    provenance = _provenance()
    provenance[field] = value
    with pytest.raises(ValueError, match="non-empty string"):
        build_baseline_alias(provenance)


def test_alias_cli_writes_manifest(tmp_path, monkeypatch) -> None:
    provenance_path = tmp_path / "provenance.json"
    output_path = tmp_path / "alias.json"
    provenance_path.write_text(json.dumps(_provenance()), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["build_alias.py", str(provenance_path), str(output_path)])
    assert main() == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["run_id"] == "456"
