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


def test_ac08_success_metrics_gate_passes_for_complete_green_metrics(tmp_path: Path) -> None:
    metrics_path = tmp_path / "ac08_success_metrics.csv"
    metrics_path.write_text(
        "metric;value\n"
        "criterion_no_new_batch_aborts;1\n"
        "criterion_no_accepted_regressions;1\n"
        "criterion_validation_rounds_recorded;1\n"
        "criterion_regression_set_improved;1\n"
        "criterion_stable_families_not_worse;1\n"
        "overall_success;1\n"
        "mean_validation_rounds_per_file;2.000\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python", "tools/check_ac08_success_metrics_gate.py", str(metrics_path)],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "PASS AC08 quality gate" in result.stdout


def test_ac08_success_metrics_gate_fails_for_regression_criterion(tmp_path: Path) -> None:
    metrics_path = tmp_path / "ac08_success_metrics.csv"
    metrics_path.write_text(
        "metric;value\n"
        "criterion_no_new_batch_aborts;1\n"
        "criterion_no_accepted_regressions;1\n"
        "criterion_validation_rounds_recorded;1\n"
        "criterion_regression_set_improved;0\n"
        "criterion_stable_families_not_worse;1\n"
        "overall_success;0\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python", "tools/check_ac08_success_metrics_gate.py", str(metrics_path)],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "criterion_regression_set_improved=0" in result.stdout
    assert "overall_success=0" in result.stdout


def test_release_candidate_gate_records_blockers_and_accepted_exceptions(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_CORE_CMD": "echo core ok",
        "RC_GATE_AC08_SMOKE_CMD": "echo smoke deviation; exit 7",
        "RC_GATE_QUALITY_CMD": "echo quality ok",
        "RC_GATE_ACCEPTED_EXCEPTIONS": "ac08-smoke",
    }

    result = subprocess.run(
        ["./tools/run_release_candidate_gate.sh"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    status = (evidence_dir / "gate_status.csv").read_text(encoding="utf-8")
    assert "core-suite;0;PASS" in status
    assert "ac08-smoke;7;ACCEPTED_EXCEPTION" in status
    assert "quality-gate;0;PASS" in status


def test_release_candidate_gate_fails_unaccepted_blocker(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_CORE_CMD": "echo core ok",
        "RC_GATE_AC08_SMOKE_CMD": "echo smoke blocker; exit 5",
        "RC_GATE_QUALITY_CMD": "echo quality ok",
    }

    result = subprocess.run(
        ["./tools/run_release_candidate_gate.sh"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    status = (evidence_dir / "gate_status.csv").read_text(encoding="utf-8")
    assert "ac08-smoke;5;BLOCKER" in status


def test_release_candidate_gate_discards_stale_metrics_before_smoke(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    output_dir = tmp_path / "output"
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True)
    stale_metrics = reports_dir / "ac08_success_metrics.csv"
    stale_metrics.write_text(
        "metric;value\n"
        "criterion_no_new_batch_aborts;1\n"
        "criterion_no_accepted_regressions;1\n"
        "criterion_validation_rounds_recorded;1\n"
        "criterion_regression_set_improved;1\n"
        "criterion_stable_families_not_worse;1\n"
        "overall_success;1\n",
        encoding="utf-8",
    )
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_OUTPUT_DIR": str(output_dir),
        "RC_GATE_CORE_CMD": "echo core ok",
        "RC_GATE_AC08_SMOKE_CMD": "echo smoke blocker; exit 124",
    }

    result = subprocess.run(
        ["./tools/run_release_candidate_gate.sh"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert not stale_metrics.exists()
    status = (evidence_dir / "gate_status.csv").read_text(encoding="utf-8")
    assert "ac08-smoke;124;BLOCKER" in status
    assert "quality-gate;1;BLOCKER" in status
    quality_log = (evidence_dir / "quality-gate.log").read_text(encoding="utf-8")
    assert "missing metrics file" in quality_log


def test_release_candidate_gate_help_documents_hard_gate_controls() -> None:
    result = subprocess.run(
        ["./tools/run_release_candidate_gate.sh", "--help"],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert "RC_GATE_AC08_SEGMENT_TIMEOUT_SECONDS" in result.stdout
    assert "default: 240" in result.stdout
    assert "RC_GATE_WORK_PACKAGE" in result.stdout


def test_segmented_ac08_smoke_withholds_aggregation_when_one_variant_fails(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    output_dir = tmp_path / "output"
    finalized = tmp_path / "finalized"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_OUTPUT_DIR": str(output_dir),
        "RC_GATE_AC08_VARIANTS": "AC0800_L,AC0800_M",
        "RC_GATE_AC08_SEGMENT_CMD_TEMPLATE": "test '{variant}' = AC0800_L",
        "RC_GATE_AC08_FINALIZE_CMD": f"touch {finalized}",
    }

    result = subprocess.run(
        ["./tools/run_ac08_segmented_smoke.sh"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert not finalized.exists()
    status = (evidence_dir / "ac08_segment_status.csv").read_text(encoding="utf-8")
    assert "AC0800_L;0;PASS" in status
    assert "AC0800_M;1;BLOCKER" in status
    assert "aggregate metrics withheld" in result.stdout


def test_segmented_ac08_smoke_runs_aggregation_after_all_segments_pass(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    output_dir = tmp_path / "output"
    finalized = tmp_path / "finalized"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_OUTPUT_DIR": str(output_dir),
        "RC_GATE_AC08_VARIANTS": "AC0800_L,AC0800_M",
        "RC_GATE_AC08_SEGMENT_CMD_TEMPLATE": "echo {variant} > {output_dir}/variant.txt",
        "RC_GATE_AC08_FINALIZE_CMD": f"touch {finalized}",
    }

    result = subprocess.run(
        ["./tools/run_ac08_segmented_smoke.sh"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    assert finalized.exists()
    status = (evidence_dir / "ac08_segment_status.csv").read_text(encoding="utf-8")
    assert status.count(";PASS;") == 2


def test_finalize_ac08_segmented_run_requires_every_fixed_variant(tmp_path: Path) -> None:
    result = subprocess.run(
        ["python", "tools/finalize_ac08_segmented_run.py", str(tmp_path / "segments"), str(tmp_path / "out")],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "incomplete AC08 segments" in result.stdout
    assert not (tmp_path / "out" / "reports" / "ac08_success_metrics.csv").exists()


def test_finalize_ac08_segmented_run_merges_complete_artifact_chain(tmp_path: Path) -> None:
    from src.successfulConversions import AC08_REGRESSION_VARIANTS

    segments = tmp_path / "segments"
    output = tmp_path / "output"
    for index, variant in enumerate(AC08_REGRESSION_VARIANTS):
        segment = segments / variant
        reports = segment / "reports"
        svg = segment / "converted_svgs"
        reports.mkdir(parents=True)
        svg.mkdir()
        (segment / ".segment-complete").touch()
        (svg / f"{variant}.svg").write_text("<svg/>", encoding="utf-8")
        (reports / "Iteration_Log.csv").write_text(
            f"Dateiname;Fehler\n{variant}.jpg;1\n",
            encoding="utf-8",
        )
        quality_row = (
            "variant;decision;old_error_per_pixel;new_error_per_pixel;old_mean_delta2;new_mean_delta2\n"
            + (f"{variant};accepted_improvement;2;1;2;1\n" if index == 0 else "")
        )
        (reports / "quality_tercile_passes.csv").write_text(quality_row, encoding="utf-8")
        (reports / f"{variant}_element_validation.log").write_text(
            "Runde 1: elementweise Validierung gestartet\nstatus=semantic_ok\n",
            encoding="utf-8",
        )

    result = subprocess.run(
        ["python", "tools/finalize_ac08_segmented_run.py", str(segments), str(output)],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    metrics = (output / "reports" / "ac08_success_metrics.csv").read_text(encoding="utf-8")
    assert f"images_converted;{len(AC08_REGRESSION_VARIANTS)}" in metrics
    assert "images_missing;0" in metrics
    assert "overall_success;1" in metrics
    assert len(list((output / "converted_svgs").glob("*.svg"))) == len(AC08_REGRESSION_VARIANTS)
