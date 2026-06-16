import json
from pathlib import Path

from tools.define_holdout_rename_protocol import (
    METRIC_FAMILIES,
    anonymized_holdout_name,
    build_protocol,
    default_samples,
    write_protocol,
)


def test_holdout_names_are_deterministic_and_catalog_free():
    first = anonymized_holdout_name("AC0812_L.png", seed="fixed")
    second = anonymized_holdout_name("AC0812_L.png", seed="fixed")

    assert first == second
    assert first.startswith("holdout_")
    assert first.endswith(".png")
    assert "AC0812" not in first


def test_protocol_reports_required_metrics_for_development_and_holdout():
    protocol = build_protocol(default_samples(), seed="fixed")

    assert protocol["split_counts"] == {"development": 2, "holdout": 2}
    assert set(protocol["metric_contract"]) == set(METRIC_FAMILIES)
    for family in METRIC_FAMILIES:
        assert protocol["required_split_reports"]["development"][family]["required"] is True
        assert protocol["required_split_reports"]["holdout"][family]["required"] is True
        assert protocol["metric_contract"][family]["reported_per_split"] == ["development", "holdout"]

    holdout_records = [sample for sample in protocol["samples"] if sample["split"] == "holdout"]
    assert holdout_records
    assert all(sample["rename_required"] is True for sample in holdout_records)
    assert all(sample["evaluation_name"] != sample["original_name"] for sample in holdout_records)


def test_write_protocol_creates_machine_readable_report(tmp_path: Path):
    output = tmp_path / "protocol.json"
    protocol = write_protocol(output, seed="fixed")

    assert output.exists()
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded == protocol
    assert loaded["schema_version"] == "holdout_rename_protocol_v1"
