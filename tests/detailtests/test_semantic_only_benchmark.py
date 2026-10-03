import json
import subprocess
from pathlib import Path

import pytest

from tools.run_semantic_only_benchmark import SCHEMA_VERSION, run_benchmark


def _fixture(tmp_path: Path, samples=None):
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    samples = samples or ["sample.jpg"]
    for sample in samples:
        (image_dir / sample).write_bytes(b"jpeg-source")
    descriptions = tmp_path / "descriptions.xml"
    descriptions.write_text("<descriptions/>", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "samples": samples}), encoding="utf-8"
    )
    return manifest, image_dir, descriptions


def test_benchmark_uses_only_isolated_jpeg_description_and_semantic_mode(tmp_path):
    manifest, image_dir, descriptions = _fixture(tmp_path)
    commands = []

    def fake_runner(command):
        commands.append(list(command))
        output = Path(command[command.index("--output-dir") + 1]) / "converted_svgs"
        output.mkdir(parents=True)
        (output / "sample.svg").write_text('<svg width="10" height="10"/>', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    report = run_benchmark(
        manifest, image_dir, descriptions, tmp_path / "work", runner=fake_runner
    )

    assert report["summary"] == {
        "sample_count": 1,
        "stable_count": 1,
        "unstable_count": 0,
        "passed": True,
    }
    assert report["input_contract"]["allowed_sources"] == ["jpeg", "description_table"]
    assert report["input_contract"]["output_variation"] is False
    assert len(commands) == 2
    assert all(command[command.index("--execution-mode") + 1] == "semantic-only" for command in commands)
    assert all("--deterministic-order" in command for command in commands)
    assert commands[0][commands[0].index("--input-dir") + 1] != commands[1][commands[1].index("--input-dir") + 1]
    assert report["evaluations"][0]["runs"][0]["svg_sha256"] == report["evaluations"][0]["runs"][1]["svg_sha256"]


def test_benchmark_reports_changed_output_as_unstable(tmp_path):
    manifest, image_dir, descriptions = _fixture(tmp_path)
    invocation = 0

    def changing_runner(command):
        nonlocal invocation
        invocation += 1
        output = Path(command[command.index("--output-dir") + 1]) / "converted_svgs"
        output.mkdir(parents=True)
        (output / "sample.svg").write_text(f"<svg data-run='{invocation}'/>", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    report = run_benchmark(
        manifest, image_dir, descriptions, tmp_path / "work", runner=changing_runner
    )

    assert report["summary"]["passed"] is False
    assert report["evaluations"][0]["stable"] is False


def test_benchmark_discards_stale_run_artifacts(tmp_path):
    manifest, image_dir, descriptions = _fixture(tmp_path)
    work_dir = tmp_path / "work"
    stale_output = work_dir / "sample" / "run-1" / "output" / "converted_svgs"
    stale_output.mkdir(parents=True)
    (stale_output / "sample.svg").write_text("<svg data-stale='true'/>", encoding="utf-8")
    (work_dir / "sample" / "run-1" / "input" / "donor.svg").parent.mkdir()
    (work_dir / "sample" / "run-1" / "input" / "donor.svg").write_text(
        "<svg/>", encoding="utf-8"
    )

    def clean_runner(command):
        input_dir = Path(command[command.index("--input-dir") + 1])
        assert sorted(path.name for path in input_dir.iterdir()) == ["sample.jpg"]
        output = Path(command[command.index("--output-dir") + 1]) / "converted_svgs"
        output.mkdir(parents=True)
        (output / "sample.svg").write_text("<svg data-current='true'/>", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    report = run_benchmark(
        manifest, image_dir, descriptions, work_dir, runner=clean_runner
    )

    assert report["summary"]["passed"] is True
    assert "data-stale" not in (stale_output / "sample.svg").read_text(encoding="utf-8")


@pytest.mark.parametrize("sample", ["../sample.jpg", "sample.png"])
def test_manifest_rejects_non_plain_jpeg_inputs(tmp_path, sample):
    manifest, image_dir, descriptions = _fixture(tmp_path)
    manifest.write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "samples": [sample]}), encoding="utf-8"
    )

    with pytest.raises(ValueError):
        run_benchmark(manifest, image_dir, descriptions, tmp_path / "work")
