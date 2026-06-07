from __future__ import annotations

import os
from pathlib import Path

from src.iCCModules import imageCompositeConverterIncremental as incremental_helpers


def _touch(path: Path, timestamp_ns: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("data", encoding="utf-8")
    os.utime(path, ns=(timestamp_ns, timestamp_ns))


def test_partition_reuses_conversion_when_svg_is_fresh(tmp_path: Path) -> None:
    source = tmp_path / "input" / "AC0800_L.jpg"
    descriptions = tmp_path / "input" / "descriptions.xml"
    svg = tmp_path / "output" / "AC0800_L.svg"
    _touch(source, 1_000_000_000)
    _touch(descriptions, 2_000_000_000)
    _touch(svg, 3_000_000_000)
    row = {"filename": source.name, "variant": "AC0800_L", "error_per_pixel": 0.25}

    pending, reusable = incremental_helpers.partitionReusableConversionsImpl(
        filenames=[source.name],
        existing_rows=[row],
        folder_path=str(source.parent),
        svg_out_dir=str(svg.parent),
        descriptions_path=str(descriptions),
    )

    assert pending == []
    assert reusable == {source.name: row}
    assert reusable[source.name] is not row


def test_partition_reconverts_when_source_or_descriptions_are_newer(tmp_path: Path) -> None:
    source = tmp_path / "input" / "AC0800_L.jpg"
    descriptions = tmp_path / "input" / "descriptions.xml"
    svg = tmp_path / "output" / "AC0800_L.svg"
    _touch(svg, 2_000_000_000)
    _touch(source, 3_000_000_000)
    _touch(descriptions, 1_000_000_000)
    row = {"filename": source.name, "variant": "AC0800_L", "error_per_pixel": 0.25}

    pending, reusable = incremental_helpers.partitionReusableConversionsImpl(
        filenames=[source.name],
        existing_rows=[row],
        folder_path=str(source.parent),
        svg_out_dir=str(svg.parent),
        descriptions_path=str(descriptions),
    )

    assert pending == [source.name]
    assert reusable == {}


def test_partition_force_reconvert_disables_reuse(tmp_path: Path) -> None:
    pending, reusable = incremental_helpers.partitionReusableConversionsImpl(
        filenames=["AC0800_L.jpg"],
        existing_rows=[],
        folder_path=str(tmp_path),
        svg_out_dir=str(tmp_path),
        descriptions_path=None,
        force_reconvert=True,
    )

    assert pending == ["AC0800_L.jpg"]
    assert reusable == {}
