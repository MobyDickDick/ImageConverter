import json
import subprocess
import sys

from tools.evaluate_good_solution_gate import (
    SCHEMA_VERSION,
    build_good_solution_report,
    evaluate_good_solution,
)


def test_good_solution_gate_classifies_all_three_statuses():
    good = evaluate_good_solution(
        {"error_per_pixel": 0.01, "semantic_score": 0.95, "dimension_match": 1.0}
    )
    suboptimal = evaluate_good_solution(
        {"error_per_pixel": 0.06, "semantic_score": 0.8, "dimension_match": 0.98}
    )
    unreachable = evaluate_good_solution(
        {"error_per_pixel": 0.01, "dimension_match": 1.0}, source_status="conversion_failed"
    )

    assert good["status"] == "good"
    assert good["reasons"] == ["all_thresholds_satisfied"]
    assert suboptimal["status"] == "suboptimal"
    assert suboptimal["reasons"] == [
        "error_per_pixel_above_max",
        "semantic_score_below_min",
        "dimension_match_below_min",
    ]
    assert unreachable["status"] == "not_reachable"
    assert unreachable["reasons"] == [
        "source_status:conversion_failed",
        "missing_metric:semantic_score",
    ]


def test_report_exposes_status_thresholds_and_reasons_for_every_file():
    report = build_good_solution_report(
        {
            "b.jpg": {"error_per_pixel": 0.08, "semantic_score": 1.0, "dimension_match": 1.0},
            "a.jpg": {"error_per_pixel": 0.01, "semantic_score": 1.0, "dimension_match": 1.0},
        }
    )

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["summary"] == {"file_count": 2, "good": 1, "suboptimal": 1, "not_reachable": 0}
    assert [row["filename"] for row in report["evaluations"]] == ["a.jpg", "b.jpg"]
    assert all(row["thresholds"] == report["thresholds"] for row in report["evaluations"])
    assert all(row["reasons"] for row in report["evaluations"])


def test_cli_writes_the_same_machine_readable_report(tmp_path):
    source = tmp_path / "conversion_result_map.json"
    output = tmp_path / "good_solution_gate.json"
    source.write_text(
        json.dumps(
            {"sample.jpg": {"error_per_pixel": 0.01, "semantic_score": 0.9, "dimension_match": 1.0}}
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "tools/evaluate_good_solution_gate.py", str(source), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == json.loads(output.read_text(encoding="utf-8"))
    assert json.loads(result.stdout)["evaluations"][0]["status"] == "good"
