from pathlib import Path

from tools.run_catalog_conversion import completed_variants, selected_images


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
