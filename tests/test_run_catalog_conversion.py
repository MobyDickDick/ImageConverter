import csv
import subprocess
import sys
from pathlib import Path

from tools import run_catalog_conversion
from tools.run_catalog_conversion import (
    completed_variants,
    conversion_environment,
    report_failure,
    selected_images,
)


def test_selected_images_partitions_supported_catalog_without_overlap(tmp_path: Path) -> None:
    for name in ("a.jpg", "b.PNG", "c.bmp", "d.jpeg", "ignored.svg"):
        (tmp_path / name).write_text("x", encoding="utf-8")

    shard_zero = selected_images(tmp_path, 0, 2)
    shard_one = selected_images(tmp_path, 1, 2)

    assert {path.name for path in shard_zero}.isdisjoint(path.name for path in shard_one)
    assert {path.name for path in shard_zero + shard_one} == {"a.jpg", "b.PNG", "c.bmp", "d.jpeg"}


def test_completed_variants_reads_resumable_result_csv(tmp_path: Path) -> None:
    report = tmp_path / "catalog_results.csv"
    report.write_text(
        "variant,filename,status,returncode,elapsed_seconds\n"
        "AC0010,AC0010.jpg,completed,0,1.2\n"
        "AC0020,AC0020.png,process_timeout,124,75.0\n",
        encoding="utf-8",
    )

    assert completed_variants(report) == {"AC0010", "AC0020"}


def test_report_failure_emits_github_error_annotation(monkeypatch, capsys) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    report_failure("AC0010", "converter_error", 1)

    assert capsys.readouterr().out == (
        "::error title=Catalog conversion failed::"
        "AC0010: converter_error (return code 1)\n"
    )


def test_conversion_environment_prepends_matching_vendor_bundle(tmp_path: Path, monkeypatch) -> None:
    vendor_site_packages = (
        tmp_path
        / "vendor"
        / f"linux-py{sys.version_info.major}{sys.version_info.minor}"
        / "site-packages"
    )
    vendor_site_packages.mkdir(parents=True)
    monkeypatch.setattr(run_catalog_conversion, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("PYTHONPATH", "/existing/packages")

    env = conversion_environment()

    assert env["PYTHONPATH"].split(run_catalog_conversion.os.pathsep) == [
        str(vendor_site_packages),
        "/existing/packages",
    ]


def test_main_returns_failure_when_a_converter_fails(tmp_path: Path, monkeypatch, capsys) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "AC0010.png").write_bytes(b"image")
    output_dir = tmp_path / "output"
    descriptions_path = input_dir / "descriptions.xml"
    descriptions_path.write_text("<forms/>", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_catalog_conversion.py",
            "--input-dir",
            str(input_dir),
            "--descriptions-path",
            str(descriptions_path),
            "--output-dir",
            str(output_dir),
        ],
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode=1),
    )

    assert run_catalog_conversion.main() == 1

    report_path = output_dir / "shard-00-of-01" / "catalog_results.csv"
    with report_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["status"] == "converter_error"
    captured = capsys.readouterr()
    assert "[CATALOG] ERROR: AC0010: converter_error (return code 1)" in captured.err
    assert "[CATALOG] finished=1 failed=1 succeeded=0" in captured.out
