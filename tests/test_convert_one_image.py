import subprocess
import sys
from pathlib import Path

from tools import convert_one_image
from tools.manage_satisfactory_baseline import prepare_baseline_pairs


def test_existing_image_path_requires_exactly_one_supported_source(tmp_path: Path) -> None:
    (tmp_path / "AC0001_L.jpg").write_bytes(b"image")

    assert convert_one_image.existing_image_path(tmp_path, "AC0001_L") == tmp_path / "AC0001_L.jpg"


def test_build_converter_command_selects_single_variant(tmp_path: Path) -> None:
    command = convert_one_image.build_converter_command(
        input_dir=tmp_path / "images",
        descriptions_path=tmp_path / "descriptions.xml",
        output_dir=tmp_path / "out",
        variant="AC0001_L",
        iterations=7,
    )

    assert command[:3] == [sys.executable, "-m", "src.imageCompositeConverter"]
    assert command[command.index("--start") + 1] == "AC0001_L"
    assert command[command.index("--end") + 1] == "AC0001_L"
    assert "--deterministic-order" in command
    assert "--fail-on-batch-failures" in command


def test_prepare_baseline_pairs_can_append_to_manifest(tmp_path: Path) -> None:
    images = tmp_path / "images"
    svgs = tmp_path / "svgs"
    baseline = tmp_path / "baseline"
    images.mkdir()
    svgs.mkdir()
    (images / "AC0001_L.jpg").write_bytes(b"jpg")
    (svgs / "AC0001_L.svg").write_text("<svg/>", encoding="utf-8")
    (baseline / "variants.txt").parent.mkdir(parents=True)
    (baseline / "variants.txt").write_text("AC0000_L\n", encoding="utf-8")

    prepared, missing = prepare_baseline_pairs(
        ["AC0001_L"],
        images_dir=images,
        svgs_dir=svgs,
        baseline_dir=baseline,
        append_manifest=True,
    )

    assert prepared == ["AC0001_L"]
    assert missing == []
    assert (baseline / "images" / "AC0001_L.jpg").read_bytes() == b"jpg"
    assert (baseline / "variants.txt").read_text(encoding="utf-8") == "AC0000_L\nAC0001_L\n"


def test_main_freezes_baseline_after_successful_single_conversion(tmp_path: Path, monkeypatch) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "AC0001_L.jpg").write_bytes(b"jpg")
    descriptions = tmp_path / "descriptions.xml"
    descriptions.write_text("<forms/>", encoding="utf-8")
    output_dir = tmp_path / "runs"
    baseline = tmp_path / "baseline"

    def fake_run(command, **kwargs):
        run_out = Path(command[command.index("--output-dir") + 1])
        svg_dir = run_out / "converted_svgs"
        svg_dir.mkdir(parents=True)
        (svg_dir / "AC0001_L.svg").write_text("<svg/>", encoding="utf-8")
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "convert_one_image.py",
            "AC0001_L",
            "--input-dir",
            str(input_dir),
            "--descriptions-path",
            str(descriptions),
            "--output-dir",
            str(output_dir),
            "--baseline-dir",
            str(baseline),
            "--freeze-baseline",
        ],
    )

    assert convert_one_image.main() == 0
    assert (baseline / "images" / "AC0001_L.jpg").exists()
    assert (baseline / "svgs" / "AC0001_L.svg").exists()
    assert (baseline / "variants.txt").read_text(encoding="utf-8") == "AC0001_L\n"
