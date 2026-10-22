"""Protect study provenance and prevent development pilots becoming acceptance."""
import csv
import json

import pytest
from PIL import Image

from tools import prepare_practical_benchmark as benchmark


@pytest.fixture
def preparation(tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    image = archive / "source.png"
    Image.new("RGB", (12, 10), "white").save(image)
    # A nonexistent vector path must never be read during input preparation.
    row = dict(variant="example", image="source.png", image_sha256=benchmark.digest(image),
               svg="must_not_read.svg", description="A rectangle.", evidence="historical-report.json",
               execution_mode="semantic-only")
    benchmark.write_json(archive / "index.json", dict(cases=[row]))
    selection = tmp_path / "selection.json"
    benchmark.write_json(selection, dict(cases=[dict(variant="example", family="panel",
                         outside_scene_contract=False)], manual_time_subset=["panel"]))
    output = tmp_path / "prepared"
    benchmark.prepare(output, selection, archive=archive)
    return output


def test_archived_candidates_are_exposed_and_times_are_missing_not_zero(preparation):
    audit = benchmark.verify(preparation)
    assert audit["candidate_cases"] == 1
    assert audit["sealed_test_families"] == audit["independently_reviewed_families"] == 0
    assert not audit["study_ready"]
    inputs = list((preparation / "inputs").iterdir())
    assert [p.name for p in inputs] == ["case_00.png"]
    with (preparation / "manual_times.template.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert {r["method"] for r in rows} == {"converter", "contour_pending", "structured_pending", "manual_redraw"}
    assert all(r["editing_seconds"] == r["accepted"] == "" for r in rows)


@pytest.mark.parametrize("file", ["inputs/case_00.png", "manifest.json", "annotations.template.json"])
def test_frozen_inputs_and_annotations_cannot_change_silently(preparation, file):
    with (preparation / file).open("ab") as handle:
        handle.write(b"changed")
    with pytest.raises(ValueError, match="changed"):
        benchmark.verify(preparation)


def test_archive_cannot_be_reclassified_as_unknown_even_after_rehash(preparation):
    manifest = json.loads((preparation / "manifest.json").read_text(encoding="utf-8"))
    manifest["cases"][0]["split"] = "holdout"
    benchmark.write_json(preparation / "manifest.json", manifest)
    frozen = json.loads((preparation / "freeze.json").read_text(encoding="utf-8"))
    frozen["manifest.json"] = benchmark.digest(preparation / "manifest.json")
    benchmark.write_json(preparation / "freeze.json", frozen)
    with pytest.raises(ValueError, match="cannot be relabeled"):
        benchmark.verify(preparation)


def test_pilot_refuses_changed_runtime_before_starting_any_conversion(preparation, tmp_path, monkeypatch):
    monkeypatch.setattr(benchmark, "runtime_hashes", lambda: {"changed.py": "other"})
    output = tmp_path / "pilot"
    with pytest.raises(ValueError, match="differs"):
        benchmark.pilot(preparation, output, ["case_00"])
    assert not output.exists()


def test_preparation_never_overwrites_existing_evidence(preparation):
    with pytest.raises(FileExistsError):
        benchmark.prepare(preparation)


@pytest.mark.parametrize("kind", ["directory", "file"])
def test_existing_output_is_rejected_before_reading_sources(preparation, kind):
    output = preparation if kind == "directory" else preparation.parent / "existing-file"
    if kind == "file":
        output.write_bytes(b"keep existing evidence")
    if output.is_dir():
        original = {p: p.read_bytes() for p in output.rglob("*") if p.is_file()}
    else:
        original = {output: output.read_bytes()}
    missing = preparation.parent / "missing-sources"
    with pytest.raises(FileExistsError):
        benchmark.prepare(output, missing / "selection.json", archive=missing / "archive")
    assert all(path.read_bytes() == data for path, data in original.items())


def test_existing_evidence_survives_missing_archive_candidate(preparation):
    selection = preparation.parent / "selection.json"
    choices = json.loads(selection.read_text(encoding="utf-8"))
    choices["cases"][0]["variant"] = "AC0840_L"
    benchmark.write_json(selection, choices)
    original = {p: p.read_bytes() for p in preparation.rglob("*") if p.is_file()}
    with pytest.raises(FileExistsError):
        benchmark.prepare(preparation, selection, archive=preparation.parent / "archive")
    assert {p: p.read_bytes() for p in preparation.rglob("*") if p.is_file()} == original


def test_missing_candidates_are_reported_before_creating_any_output(preparation):
    selection = preparation.parent / "selection.json"
    choices = json.loads(selection.read_text(encoding="utf-8"))
    choices["cases"].extend([
        dict(variant="AC0840_L", family="label", outside_scene_contract=True),
        dict(variant="missing_other", family="other", outside_scene_contract=True),
    ])
    benchmark.write_json(selection, choices)
    output = preparation.parent / "not-created" / "prepared"
    with pytest.raises(ValueError, match="missing from archive index: AC0840_L, missing_other"):
        benchmark.prepare(output, selection, archive=preparation.parent / "archive")
    assert not output.parent.exists()


def test_data_paths_must_stay_in_their_declared_root(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        benchmark.contained(tmp_path, "../reference.svg")


@pytest.fixture
def missing_output_pilot(preparation, tmp_path, monkeypatch):
    from tools import run_plan_b_variations

    def missing(case, output, **kwargs):
        benchmark.write_json(output / case["case_id"] / "reference_access.json", dict(blocked_svg_reads=[]))
        return dict(case, satisfactory=False, failures=["missing_or_ambiguous_output"],
                    returncode=0, elapsed_seconds=.1)

    monkeypatch.setattr(run_plan_b_variations, "run_case", missing)
    output = tmp_path / "pilot"
    benchmark.pilot(preparation, output, ["case_00"])
    return preparation, output


def test_missing_outputs_remain_in_pilot_denominator(missing_output_pilot):
    prepared, output = missing_output_pilot
    result = benchmark.verify_pilot(prepared, output)
    assert result["attempts"] == 1 and result["pixel_passes"] == result["accepted"] == 0
    assert not result["study_ready"]


@pytest.mark.parametrize("mutation", ["drop_record", "forge_acceptance", "change_description"])
def test_pilot_verification_rejects_false_evidence(missing_output_pilot, mutation):
    prepared, output = missing_output_pilot
    path = output / "pilot.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    if mutation == "drop_record":
        report["records"].clear()
    elif mutation == "forge_acceptance":
        report["records"][0]["accepted"] = True
    else:
        report["records"][0]["description"] = "Changed description."
    benchmark.write_json(path, report)
    with pytest.raises(ValueError):
        benchmark.verify_pilot(prepared, output)
