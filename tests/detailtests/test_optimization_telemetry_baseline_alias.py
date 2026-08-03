from pathlib import Path

import pytest

from tools.resolve_optimization_telemetry_baseline import resolve_baseline_alias


def test_resolve_baseline_alias_uses_complete_manual_override() -> None:
    alias = resolve_baseline_alias(
        input_run_id="456",
        input_artifact_name="optimization-render-telemetry-baseline-456-2",
        variable_run_id="123",
        variable_artifact_name="optimization-render-telemetry-baseline-123-1",
    )

    assert alias.run_id == "456"
    assert alias.artifact_name == "optimization-render-telemetry-baseline-456-2"


def test_resolve_baseline_alias_uses_repository_alias_without_overrides() -> None:
    alias = resolve_baseline_alias(
        variable_run_id="123",
        variable_artifact_name="optimization-render-telemetry-baseline-123-1",
    )

    assert alias.run_id == "123"
    assert alias.artifact_name == "optimization-render-telemetry-baseline-123-1"


@pytest.mark.parametrize(
    ("input_run_id", "input_artifact_name"),
    [
        ("456", ""),
        ("", "optimization-render-telemetry-baseline-456-1"),
    ],
)
def test_resolve_baseline_alias_rejects_partial_override(
    input_run_id: str, input_artifact_name: str
) -> None:
    with pytest.raises(ValueError, match="both baseline workflow overrides"):
        resolve_baseline_alias(
            input_run_id=input_run_id,
            input_artifact_name=input_artifact_name,
            variable_run_id="123",
            variable_artifact_name="optimization-render-telemetry-baseline-123-1",
        )


def test_resolve_baseline_alias_rejects_cross_run_artifact() -> None:
    with pytest.raises(ValueError, match="must belong to the resolved run ID"):
        resolve_baseline_alias(
            variable_run_id="123",
            variable_artifact_name="optimization-render-telemetry-baseline-456-1",
        )


def test_resolver_cli_writes_github_step_outputs(tmp_path: Path, monkeypatch) -> None:
    from tools.resolve_optimization_telemetry_baseline import main

    output_path = tmp_path / "github-output"
    monkeypatch.setattr(
        "sys.argv",
        [
            "resolve_optimization_telemetry_baseline.py",
            "--variable-run-id",
            "123",
            "--variable-artifact-name",
            "optimization-render-telemetry-baseline-123-1",
            "--github-output",
            str(output_path),
        ],
    )
    assert main() == 0

    assert output_path.read_text(encoding="utf-8") == (
        "run_id=123\nartifact_name=optimization-render-telemetry-baseline-123-1\n"
    )
