import json
import subprocess
import sys

from tools.evaluate_good_solution_gate import (
    SCHEMA_VERSION,
    _raster_dimensions,
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
        "semantic_score_below_min",
        "dimension_match_below_min",
    ]
    assert suboptimal["decision_tier"] == "primary"
    assert unreachable["status"] == "not_reachable"
    assert unreachable["reasons"] == [
        "source_status:conversion_failed",
        "missing_metric:semantic_score",
    ]
    assert unreachable["reachability"] == {
        "schema_version": "image_converter_reachability_v1",
        "reason": "stagnation",
        "report_code": "NR001",
        "exit_code": 20,
    }
    assert good["reachability"] is None
    assert good["decision_tier"] == "all"


def test_primary_metrics_cannot_be_compensated_by_an_excellent_pixel_score():
    result = evaluate_good_solution(
        {"error_per_pixel": 0.0, "semantic_score": 0.84, "dimension_match": 1.0}
    )

    assert result["status"] == "suboptimal"
    assert result["decision_tier"] == "primary"
    assert result["reasons"] == ["semantic_score_below_min"]
    assert result["metric_hierarchy"] == {
        "primary": ["semantic_score", "dimension_match"],
        "secondary": ["error_per_pixel"],
    }


def test_pixel_error_is_secondary_after_primary_metrics_pass():
    result = evaluate_good_solution(
        {"error_per_pixel": 0.051, "semantic_score": 0.85, "dimension_match": 0.99}
    )

    assert result["status"] == "suboptimal"
    assert result["decision_tier"] == "secondary"
    assert result["reasons"] == ["error_per_pixel_above_max"]


def test_report_exposes_status_thresholds_and_reasons_for_every_file():
    report = build_good_solution_report(
        {
            "b.jpg": {"error_per_pixel": 0.08, "semantic_score": 1.0, "dimension_match": 1.0},
            "a.jpg": {"error_per_pixel": 0.01, "semantic_score": 1.0, "dimension_match": 1.0},
        }
    )

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["metric_hierarchy"] == {
        "primary": ["semantic_score", "dimension_match"],
        "secondary": ["error_per_pixel"],
    }
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


def test_cli_returns_canonical_exit_code_when_requested(tmp_path):
    source = tmp_path / "conversion_result_map.json"
    source.write_text(
        json.dumps(
            {
                "sample.jpg": {
                    "status": "semantic_mismatch",
                    "error_per_pixel": 0.01,
                    "semantic_score": 0.9,
                    "dimension_match": 1.0,
                }
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "tools/evaluate_good_solution_gate.py", str(source), "--fail-on-not-reachable"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 23
    assert json.loads(result.stdout)["evaluations"][0]["reachability"]["report_code"] == "NR004"


def test_actual_wrong_svg_dimensions_are_a_hard_suboptimal_rule(tmp_path):
    image_dir = tmp_path / "images"
    svg_dir = tmp_path / "svgs"
    image_dir.mkdir()
    svg_dir.mkdir()
    # Only the PNG signature and IHDR dimensions are needed by the gate. Keeping
    # this fixture dependency-free also exercises the CI environment used by the CLI.
    png_header = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        + (40).to_bytes(4, "big")
        + (20).to_bytes(4, "big")
    )
    (image_dir / "wrong.png").write_bytes(png_header)
    (svg_dir / "wrong.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"/>',
        encoding="utf-8",
    )

    report = build_good_solution_report(
        {
            "wrong.png": {
                "error_per_pixel": 0.01,
                "semantic_score": 0.95,
                # A stale caller-supplied value must not bypass the physical check.
                "dimension_match": 1.0,
            }
        },
        image_dir=image_dir,
        svg_dir=svg_dir,
    )

    evaluation = report["evaluations"][0]
    assert evaluation["status"] == "suboptimal"
    assert evaluation["reasons"] == ["dimension_match_below_min"]
    assert evaluation["metrics"]["dimension_match"] == 0.5
    assert evaluation["dimension_evidence"]["width_match"] == 1.0
    assert evaluation["dimension_evidence"]["height_match"] == 0.5
    assert evaluation["dimension_evidence"]["aspect_ratio_match"] == 0.5


def test_raster_dimensions_support_jpeg_without_pillow(tmp_path):
    image_path = tmp_path / "sample.jpg"
    image_path.write_bytes(
        b"\xff\xd8"
        b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xc0\x00\x11\x08\x00\x14\x00\x28\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
        b"\xff\xd9"
    )

    assert _raster_dimensions(image_path) == (40, 20)
