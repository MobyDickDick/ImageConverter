from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_fake_python(path: Path) -> None:
    path.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$*\" == *\"tools/check_chain_telemetry_drift_gate.py\"* ]]; then\n"
        "  echo \"WARN chain telemetry drift gate: status=warn reasons=mean_delta2_above_limit,non_green_count_above_limit path=${@: -1}\"\n"
        "  exit 1\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def test_local_completion_checks_drift_warning_is_advisory_by_default(tmp_path: Path) -> None:
    fake_python = tmp_path / "fake-python"
    _write_fake_python(fake_python)
    summary_path = tmp_path / "chain_phase_telemetry_summary.txt"
    summary_path.write_text(
        "drift_status=warn\n"
        "drift_reasons=mean_delta2_above_limit,non_green_count_above_limit\n",
        encoding="utf-8",
    )

    env = {**os.environ, "PYTHON": str(fake_python)}
    result = subprocess.run(
        ["./tools/run_local_completion_checks.sh", "--summary", str(summary_path)],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "WARN chain telemetry drift gate" in result.stdout
    assert "WARN: advisory drift gate failed" in result.stdout


def test_local_completion_checks_required_drift_warning_remains_fatal(tmp_path: Path) -> None:
    fake_python = tmp_path / "fake-python"
    _write_fake_python(fake_python)
    summary_path = tmp_path / "chain_phase_telemetry_summary.txt"
    summary_path.write_text(
        "drift_status=warn\n"
        "drift_reasons=mean_delta2_above_limit,non_green_count_above_limit\n",
        encoding="utf-8",
    )

    env = {**os.environ, "PYTHON": str(fake_python)}
    result = subprocess.run(
        [
            "./tools/run_local_completion_checks.sh",
            "--summary",
            str(summary_path),
            "--require-drift-summary",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "WARN chain telemetry drift gate" in result.stdout
    assert "WARN: advisory drift gate failed" not in result.stdout


def test_run_test_evidence_records_pass_summary(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "pass.log"
    summary_path = tmp_path / "summary" / "pass.md"

    result = subprocess.run(
        [
            "./tools/run_test_evidence.sh",
            "--name",
            "unit-pass",
            "--log",
            str(log_path),
            "--summary",
            str(summary_path),
            "--",
            "bash",
            "-c",
            "echo ok",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "ok" in log_path.read_text(encoding="utf-8")
    summary = summary_path.read_text(encoding="utf-8")
    assert "# Test evidence: unit-pass" in summary
    assert "- Verdict: PASS" in summary
    assert "- Exit code: 0" in summary


def test_run_test_evidence_records_fail_summary(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "fail.log"
    summary_path = tmp_path / "summary" / "fail.md"

    result = subprocess.run(
        [
            "./tools/run_test_evidence.sh",
            "--name",
            "unit-fail",
            "--log",
            str(log_path),
            "--summary",
            str(summary_path),
            "--",
            "bash",
            "-c",
            "echo nope; exit 3",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 3
    assert "nope" in log_path.read_text(encoding="utf-8")
    summary = summary_path.read_text(encoding="utf-8")
    assert "# Test evidence: unit-fail" in summary
    assert "- Verdict: FAIL" in summary
    assert "- Exit code: 3" in summary
