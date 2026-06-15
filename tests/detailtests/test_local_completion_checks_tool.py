from __future__ import annotations

import json
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


def test_local_completion_checks_runs_image_id_ratchet_before_tests(tmp_path: Path) -> None:
    fake_python = tmp_path / "fake-python"
    fake_python.write_text(
        "#!/usr/bin/env bash\n"
        "if [[ \"$*\" == *\"tools/check_no_new_image_id_hardcoding.py\"* ]]; then\n"
        "  echo 'synthetic ratchet failure'\n"
        "  exit 7\n"
        "fi\n"
        "echo \"unexpected later command: $*\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    result = subprocess.run(
        ["./tools/run_local_completion_checks.sh"],
        cwd=Path(__file__).resolve().parents[2],
        env={**os.environ, "PYTHON": str(fake_python)},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 7
    assert "==> image-ID hardcoding ratchet" in result.stdout
    assert "synthetic ratchet failure" in result.stdout
    assert "==> compileall" not in result.stdout


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
    assert "- Expected exit code: not specified" in summary
    assert "- Expectation: NOT_SPECIFIED" in summary
    assert "- Scenario ID: unit-pass" in summary
    assert "- Test context: not specified" in summary
    assert "- Run ID: not specified" in summary


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
    assert "- Expected exit code: not specified" in summary
    assert "- Expectation: NOT_SPECIFIED" in summary


def test_run_test_evidence_records_explicit_identity_metadata(tmp_path: Path) -> None:
    summary_path = tmp_path / "identity.md"
    result = subprocess.run(
        [
            "./tools/run_test_evidence.sh",
            "--name",
            "FP-D12 accepted-exception ac08-smoke",
            "--log",
            str(tmp_path / "identity.log"),
            "--summary",
            str(summary_path),
            "--scenario-id",
            "accepted-exception",
            "--test-context",
            "tests/detailtests/test_local_completion_checks_tool.py::test_release_candidate_gate_records_blockers_and_accepted_exceptions",
            "--run-id",
            "fp-d12-test-run",
            "--",
            "true",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Scenario ID: accepted-exception" in summary
    assert "- Test context: tests/detailtests/test_local_completion_checks_tool.py::test_release_candidate_gate_records_blockers_and_accepted_exceptions" in summary
    assert "- Run ID: fp-d12-test-run" in summary


def _run_expected_exit_evidence(
    tmp_path: Path,
    *,
    expected_exit: str,
    observed_exit: int,
) -> tuple[subprocess.CompletedProcess[str], str]:
    log_path = tmp_path / f"expected-{expected_exit}-{observed_exit}.log"
    summary_path = tmp_path / f"expected-{expected_exit}-{observed_exit}.md"
    result = subprocess.run(
        [
            "./tools/run_test_evidence.sh",
            "--name",
            "expected-exit",
            "--log",
            str(log_path),
            "--summary",
            str(summary_path),
            "--expected-exit",
            expected_exit,
            "--",
            "bash",
            "-c",
            f"exit {observed_exit}",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result, summary_path.read_text(encoding="utf-8")


def test_run_test_evidence_marks_expected_failure_as_met(tmp_path: Path) -> None:
    result, summary = _run_expected_exit_evidence(
        tmp_path,
        expected_exit="3",
        observed_exit=3,
    )

    assert result.returncode == 3
    assert "- Verdict: FAIL" in summary
    assert "- Exit code: 3" in summary
    assert "- Expected exit code: 3" in summary
    assert "- Expectation: MET" in summary


def test_run_test_evidence_marks_unexpected_success_as_unmet(tmp_path: Path) -> None:
    result, summary = _run_expected_exit_evidence(
        tmp_path,
        expected_exit="3",
        observed_exit=0,
    )

    assert result.returncode == 0
    assert "- Verdict: PASS" in summary
    assert "- Exit code: 0" in summary
    assert "- Expected exit code: 3" in summary
    assert "- Expectation: UNMET" in summary


def test_run_test_evidence_marks_wrong_failure_code_as_unmet(tmp_path: Path) -> None:
    result, summary = _run_expected_exit_evidence(
        tmp_path,
        expected_exit="3",
        observed_exit=5,
    )

    assert result.returncode == 5
    assert "- Verdict: FAIL" in summary
    assert "- Exit code: 5" in summary
    assert "- Expected exit code: 3" in summary
    assert "- Expectation: UNMET" in summary


def test_run_test_evidence_rejects_invalid_expected_exit(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "./tools/run_test_evidence.sh",
            "--name",
            "invalid-expected-exit",
            "--log",
            str(tmp_path / "invalid.log"),
            "--summary",
            str(tmp_path / "invalid.md"),
            "--expected-exit",
            "failure",
            "--",
            "true",
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 2
    assert "--expected-exit must be an integer from 0 to 255" in result.stdout


def _write_evidence_summary(
    path: Path,
    *,
    name: str,
    verdict: str,
    exit_code: int,
    expectation: str,
    scenario_id: str,
) -> None:
    path.write_text(
        f"# Test evidence: {name}\n\n"
        f"- Verdict: {verdict}\n"
        f"- Exit code: {exit_code}\n"
        f"- Expected exit code: {'not specified' if expectation == 'NOT_SPECIFIED' else exit_code}\n"
        f"- Expectation: {expectation}\n"
        f"- Scenario ID: {scenario_id}\n"
        "- Test context: test-context\n"
        "- Run ID: test-run\n"
        "- UTC time: 2026-06-13T00:00:00Z\n"
        "- Git ref: refs/heads/main\n"
        "- Git SHA: test-sha\n"
        f"- Log: {path.with_suffix('.log')}\n",
        encoding="utf-8",
    )


def test_aggregate_test_evidence_uses_completion_profile_for_overall_pass(tmp_path: Path) -> None:
    expected_failure = tmp_path / "expected-failure.md"
    completion = tmp_path / "completion.md"
    aggregate = tmp_path / "aggregate.md"
    aggregate_json = tmp_path / "aggregate.json"
    correction_task = tmp_path / "correction.md"
    _write_evidence_summary(
        expected_failure,
        name="negative-path",
        verdict="FAIL",
        exit_code=7,
        expectation="MET",
        scenario_id="accepted-exception",
    )
    _write_evidence_summary(
        completion,
        name="completion-profile",
        verdict="PASS",
        exit_code=0,
        expectation="NOT_SPECIFIED",
        scenario_id="completion-profile",
    )

    result = subprocess.run(
        [
            "python",
            "tools/aggregate_test_evidence.py",
            "--output",
            str(aggregate),
            "--json-output",
            str(aggregate_json),
            "--correction-task",
            str(correction_task),
            str(expected_failure),
            str(completion),
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0
    report = aggregate.read_text(encoding="utf-8")
    assert "## Scenario evidence" in report
    assert "| accepted-exception | FAIL | 7 | MET | COVERED |" in report
    assert "## Completion verdict" in report
    assert "- Overall verdict: PASS" in report
    assert not correction_task.exists()
    assert json.loads(aggregate_json.read_text(encoding="utf-8"))["overall_verdict"] == "PASS"


def test_aggregate_test_evidence_creates_task_for_failed_completion(tmp_path: Path) -> None:
    completion = tmp_path / "completion.md"
    aggregate = tmp_path / "aggregate.md"
    correction_task = tmp_path / "correction.md"
    _write_evidence_summary(
        completion,
        name="completion-profile",
        verdict="FAIL",
        exit_code=5,
        expectation="NOT_SPECIFIED",
        scenario_id="completion-profile",
    )

    result = subprocess.run(
        [
            "python",
            "tools/aggregate_test_evidence.py",
            "--output",
            str(aggregate),
            "--correction-task",
            str(correction_task),
            "--reproduction-command",
            "./tools/run_local_completion_checks.sh --require-drift-summary",
            str(completion),
        ],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "- Overall verdict: FAIL" in aggregate.read_text(encoding="utf-8")
    task = correction_task.read_text(encoding="utf-8")
    assert "Szenario-ID: completion-profile" in task
    assert "Tatsächlicher Exit-Code: 5" in task
    assert "Git-SHA: `test-sha`" in task
    assert "./tools/run_local_completion_checks.sh --require-drift-summary" in task


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
        "RC_GATE_SCENARIO_ID": "accepted-exception",
        "RC_GATE_RUN_ID": "fp-d12-accepted-exception",
        "RC_GATE_TEST_CONTEXT": "tests/detailtests/test_local_completion_checks_tool.py::test_release_candidate_gate_records_blockers_and_accepted_exceptions",
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
    smoke_summary = (evidence_dir / "ac08-smoke-summary.md").read_text(encoding="utf-8")
    assert "# Test evidence: FP-D12 accepted-exception ac08-smoke" in smoke_summary
    assert "- Scenario ID: accepted-exception" in smoke_summary
    assert "- Run ID: fp-d12-accepted-exception" in smoke_summary
    assert "test_release_candidate_gate_records_blockers_and_accepted_exceptions" in smoke_summary


def test_release_candidate_gate_fails_unaccepted_blocker(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_CORE_CMD": "echo core ok",
        "RC_GATE_AC08_SMOKE_CMD": "echo smoke blocker; exit 5",
        "RC_GATE_QUALITY_CMD": "echo quality ok",
        "RC_GATE_SCENARIO_ID": "unaccepted-blocker",
        "RC_GATE_TEST_CONTEXT": "tests/detailtests/test_local_completion_checks_tool.py::test_release_candidate_gate_fails_unaccepted_blocker",
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
        "RC_GATE_SCENARIO_ID": "stale-metrics-timeout",
        "RC_GATE_TEST_CONTEXT": "tests/detailtests/test_local_completion_checks_tool.py::test_release_candidate_gate_discards_stale_metrics_before_smoke",
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


def test_release_candidate_gate_propagates_paths_to_segmented_smoke(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "named-evidence"
    output_dir = tmp_path / "named-output"
    finalized = tmp_path / "finalized"
    segments_dir = tmp_path / "named-segments"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_OUTPUT_DIR": str(output_dir),
        "RC_GATE_AC08_SEGMENTS_DIR": str(segments_dir),
        "RC_GATE_CORE_CMD": "echo core ok",
        "RC_GATE_AC08_VARIANTS": "AC0800_L",
        "RC_GATE_AC08_SEGMENT_CMD_TEMPLATE": (
            "mkdir -p {output_dir}/reports; "
            "echo {variant} > {output_dir}/variant.txt; "
            "printf 'Dateiname;Fehler\n{variant}.jpg;1\n' > {output_dir}/reports/Iteration_Log.csv"
        ),
        "RC_GATE_AC08_FINALIZE_CMD": f"mkdir -p {output_dir}/reports; touch {finalized}",
        "RC_GATE_QUALITY_CMD": "echo quality ok",
        "RC_GATE_SCENARIO_ID": "path-propagation",
        "RC_GATE_TEST_CONTEXT": "tests/detailtests/test_local_completion_checks_tool.py::test_release_candidate_gate_propagates_paths_to_segmented_smoke",
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
    assert finalized.exists()
    segment_status = evidence_dir / "ac08_segment_status.csv"
    assert segment_status.exists()
    assert f"AC0800_L;0;PASS;{segments_dir}/AC0800_L" in segment_status.read_text(encoding="utf-8")


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
    assert "RC_GATE_SCENARIO_ID" in result.stdout
    assert "RC_GATE_RUN_ID" in result.stdout
    assert "RC_GATE_TEST_CONTEXT" in result.stdout


def test_segmented_ac08_smoke_withholds_aggregation_when_one_variant_fails(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    output_dir = tmp_path / "output"
    finalized = tmp_path / "finalized"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_OUTPUT_DIR": str(output_dir),
        "RC_GATE_AC08_VARIANTS": "AC0800_L,AC0800_M",
        "RC_GATE_AC08_SEGMENT_CMD_TEMPLATE": (
            "mkdir -p {output_dir}/reports; "
            "if test '{variant}' = AC0800_L; then "
            "printf 'Dateiname;Fehler\n{variant}.jpg;1\n' > {output_dir}/reports/Iteration_Log.csv; "
            "else exit 1; fi"
        ),
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


def test_segmented_ac08_smoke_rejects_exit_zero_without_expected_iteration_row(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    output_dir = tmp_path / "output"
    finalized = tmp_path / "finalized"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_OUTPUT_DIR": str(output_dir),
        "RC_GATE_AC08_VARIANTS": "AC0811_L",
        "RC_GATE_AC08_SEGMENT_CMD_TEMPLATE": "mkdir -p {output_dir}/reports; printf 'Dateiname;Fehler\n' > {output_dir}/reports/Iteration_Log.csv",
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
    assert not (output_dir.parent / f"{output_dir.name}.segments" / "AC0811_L" / ".segment-complete").exists()
    status = (evidence_dir / "ac08_segment_status.csv").read_text(encoding="utf-8")
    assert "AC0811_L;0;BLOCKER_MISSING_REPORT" in status


def test_segmented_ac08_smoke_runs_aggregation_after_all_segments_pass(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    output_dir = tmp_path / "output"
    finalized = tmp_path / "finalized"
    env = {
        **os.environ,
        "RC_GATE_EVIDENCE_DIR": str(evidence_dir),
        "RC_GATE_OUTPUT_DIR": str(output_dir),
        "RC_GATE_AC08_VARIANTS": "AC0800_L,AC0800_M",
        "RC_GATE_AC08_SEGMENT_CMD_TEMPLATE": (
            "mkdir -p {output_dir}/reports; "
            "echo {variant} > {output_dir}/variant.txt; "
            "printf 'Dateiname;Fehler\n{variant}.jpg;1\n' > {output_dir}/reports/Iteration_Log.csv"
        ),
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
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    result = subprocess.run(
        ["python", "tools/finalize_ac08_segmented_run.py", str(tmp_path / "segments"), str(tmp_path / "out")],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "incomplete AC08 segments" in result.stdout
    assert not (tmp_path / "out" / "reports" / "ac08_success_metrics.csv").exists()


def test_finalize_ac08_segmented_run_rejects_marker_without_expected_iteration_row(tmp_path: Path) -> None:
    from src.successfulConversions import AC08_REGRESSION_VARIANTS

    segments = tmp_path / "segments"
    output = tmp_path / "output"
    missing_variant = AC08_REGRESSION_VARIANTS[0]
    for variant in AC08_REGRESSION_VARIANTS:
        reports = segments / variant / "reports"
        reports.mkdir(parents=True)
        (segments / variant / ".segment-complete").touch()
        row = "" if variant == missing_variant else f"{variant}.jpg;1\n"
        (reports / "Iteration_Log.csv").write_text(f"Dateiname;Fehler\n{row}", encoding="utf-8")

    result = subprocess.run(
        ["python", "tools/finalize_ac08_segmented_run.py", str(segments), str(output)],
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert f"missing expected iteration row: {missing_variant}" in result.stdout
    assert not (output / "reports" / "ac08_success_metrics.csv").exists()


def test_finalize_ac08_segmented_run_writes_empty_optional_quality_report(tmp_path: Path) -> None:
    from src.successfulConversions import AC08_REGRESSION_VARIANTS

    segments = tmp_path / "segments"
    output = tmp_path / "output"
    for variant in AC08_REGRESSION_VARIANTS:
        reports = segments / variant / "reports"
        reports.mkdir(parents=True)
        (segments / variant / ".segment-complete").touch()
        (reports / "Iteration_Log.csv").write_text(
            f"Dateiname;Fehler\n{variant}.jpg;1\n",
            encoding="utf-8",
        )
        (reports / f"{variant}_element_validation.log").write_text(
            "Runde 1: elementweise Validierung gestartet\nstatus=semantic_ok\n",
            encoding="utf-8",
        )

    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    result = subprocess.run(
        ["python", "tools/finalize_ac08_segmented_run.py", str(segments), str(output)],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    quality_report = (output / "reports" / "quality_tercile_passes.csv").read_text(encoding="utf-8")
    assert quality_report.splitlines() == [
        "pass;filename;old_error_per_pixel;new_error_per_pixel;old_mean_delta2;new_mean_delta2;improved;decision;iteration_budget;badge_validation_rounds"
    ]
    metrics = (output / "reports" / "ac08_success_metrics.csv").read_text(encoding="utf-8")
    assert "criterion_regression_set_improved;0" in metrics
    assert "overall_success;0" in metrics


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

    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    result = subprocess.run(
        ["python", "tools/finalize_ac08_segmented_run.py", str(segments), str(output)],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
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
