import json
from pathlib import Path

from tools.build_holdout_ablation_matrix import MODES, build_ablation_matrix, write_ablation_matrix
from tools.define_holdout_rename_protocol import build_protocol, default_samples


def test_ablation_matrix_reports_all_modes_per_split_and_sample():
    protocol = build_protocol(default_samples(), seed="fixed")
    report = build_ablation_matrix(protocol)

    assert report["schema_version"] == "holdout_ablation_matrix_v1"
    assert report["modes"] == list(MODES)
    assert len(report["rows"]) == len(protocol["samples"]) * len(MODES)
    assert report["acceptance"] == {
        "combined_mode_improves_development": True,
        "combined_mode_improves_holdout": True,
    }

    for split in ("development", "holdout"):
        assert report["summary"][split]["combined_mode_improves_over_single_source"] is True
        for mode in MODES:
            assert report["summary"][split][mode]["sample_count"] == 2


def test_ablation_rows_show_source_contributions_for_each_mode():
    report = build_ablation_matrix(build_protocol(default_samples(), seed="fixed"))
    by_mode = {row["mode"]: row for row in report["rows"] if row["evaluation_name"] == "development_circle_badge.png"}

    assert by_mode["image_only"]["source_contributions"]["description"] == []
    assert by_mode["image_only"]["source_contributions"]["image"]
    assert by_mode["description_only"]["source_contributions"]["image"] == []
    assert by_mode["description_only"]["source_contributions"]["description"]
    assert by_mode["image_and_description"]["source_contributions"]["image"]
    assert by_mode["image_and_description"]["source_contributions"]["description"]


def test_write_ablation_matrix_creates_machine_readable_report(tmp_path: Path):
    output = tmp_path / "ablation.json"
    report = write_ablation_matrix(output, seed="fixed")

    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == report
