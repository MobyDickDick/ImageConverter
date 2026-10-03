import json
import subprocess
from pathlib import Path

import pytest

from tools.run_semantic_only_benchmark import SCHEMA_VERSION, run_benchmark
from tools.generate_semantic_only_png_fixtures import generate_fixtures


def _fixture(tmp_path: Path, *, extra: dict | None = None) -> Path:
    image = tmp_path / "sample.png"
    generated = generate_fixtures(tmp_path / "generated")
    image.write_bytes(next(path for path in generated if path.name == "polygon_line.png").read_bytes())
    case = {
        "case_id": "sample", "image_path": "sample.png",
        "semantic_description": "Ein Polygonpfad mit einer Linie.",
        "topology": "polygon_path+line",
    }
    case.update(extra or {})
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": SCHEMA_VERSION, "seed": 0, "cases": [case]}))
    return manifest


def test_runner_isolates_three_runs_and_proves_rename_invariance(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    commands = []

    def fake_runner(command):
        commands.append(list(command))
        stem = command[command.index("--start") + 1]
        input_dir = Path(command[command.index("--input-dir") + 1])
        assert [path.name for path in input_dir.iterdir()] == [f"{stem}.png"]
        output = Path(command[command.index("--output-dir") + 1]) / "converted_svgs"
        output.mkdir(parents=True)
        (output / f"{stem}.svg").write_text('<svg width="64" height="64"><path d="M 1 1"/></svg>')
        return subprocess.CompletedProcess(command, 0, "", "")

    report = run_benchmark(manifest, tmp_path / "work", runner=fake_runner)

    assert report["summary"]["passed"] is True
    assert report["input_contract"]["allowed_sources"] == ["png", "semantic_description"]
    assert len(commands) == 3
    assert all(command[command.index("--execution-mode") + 1] == "semantic-only" for command in commands)
    assert report["evaluations"][0]["rename_invariant"] is True
    assert report["evaluations"][0]["runs"][-1]["renamed_input"] is True


def test_runner_reports_changed_output_as_unstable(tmp_path: Path) -> None:
    invocation = 0

    def changing_runner(command):
        nonlocal invocation
        invocation += 1
        stem = command[command.index("--start") + 1]
        output = Path(command[command.index("--output-dir") + 1]) / "converted_svgs"
        output.mkdir(parents=True)
        (output / f"{stem}.svg").write_text(f'<svg width="{invocation}"/>')
        return subprocess.CompletedProcess(command, 0, "", "")

    report = run_benchmark(_fixture(tmp_path), tmp_path / "work", runner=changing_runner)
    assert report["summary"]["passed"] is False


@pytest.mark.parametrize("extra", [{"template_svg": "hidden.svg"}, {"image_path": "sample.jpg"}])
def test_manifest_rejects_forbidden_or_non_png_sources(tmp_path: Path, extra: dict) -> None:
    with pytest.raises(ValueError):
        run_benchmark(_fixture(tmp_path, extra=extra), tmp_path / "work")
