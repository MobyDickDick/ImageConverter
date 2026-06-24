import json
from pathlib import Path

from tools.run_end_to_end_holdout_acceptance import (
    build_end_to_end_holdout_acceptance,
    write_end_to_end_holdout_acceptance,
)


def test_end_to_end_holdout_acceptance_uses_only_renamed_holdout_names():
    report = build_end_to_end_holdout_acceptance(seed="unit-seed")

    assert report["schema_version"] == "end_to_end_holdout_acceptance_v1"
    assert report["summary"]["accepted"] is True
    assert report["summary"]["rename_invariance_passed"] is True
    assert report["leakage"] == {"holdout_original_names": [], "catalog_tokens": []}
    assert report["conversions"]
    assert all(row["evaluation_name"].startswith("holdout_") for row in report["conversions"])
    serialized = json.dumps(report["conversions"], ensure_ascii=False)
    assert "strict_holdout_ring_top_stem" not in serialized
    assert "strict_holdout_plain_valve" not in serialized


def test_end_to_end_holdout_acceptance_passes_gate_and_uncertainty_calibration():
    report = build_end_to_end_holdout_acceptance(seed="unit-seed")

    assert report["summary"]["quality_gate_passed"] is True
    assert report["summary"]["uncertainty_calibration_passed"] is True
    for row in report["conversions"]:
        assert row["mode"] == "image_and_description"
        assert row["quality_gate"]["passed"] is True
        assert row["uncertainty"]["schema_version"] == "fusion_uncertainty_v1"
        assert row["uncertainty"]["status"] == "resolved"
        assert row["uncertainty"]["review_required"] is False


def test_write_end_to_end_holdout_acceptance_creates_machine_readable_report(tmp_path: Path):
    output = tmp_path / "acceptance.json"
    report = write_end_to_end_holdout_acceptance(output, seed="unit-seed")

    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded == report
    assert loaded["summary"]["holdout_sample_count"] == 2
