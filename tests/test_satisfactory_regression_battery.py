from __future__ import annotations

from pathlib import Path

import pytest
import src.imageCompositeConverter as converter

BASE = Path("artifacts/regression_baseline/satisfactory")


def _variants() -> list[str]:
    manifest = BASE / "variants.txt"
    if not manifest.exists():
        return []
    return [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_satisfactory_baseline_has_pairs() -> None:
    variants = _variants()
    if not variants:
        pytest.skip("No baseline variants found. Run tools/manage_satisfactory_baseline.py first.")

    for variant in variants[:20]:
        assert (BASE / "images" / f"{variant}.jpg").exists()
        assert (BASE / "svgs" / f"{variant}.svg").exists()


def test_satisfactory_baseline_reconversion_smoke(tmp_path: Path) -> None:
    variants = _variants()
    if not variants:
        pytest.skip("No baseline variants found.")
    first = variants[0]
    family = first.rsplit("_", 1)[0]
    out = tmp_path / "out"
    exit_code = converter.main(
        [
            str(BASE / "images"),
            "--descriptions-path",
            "artifacts/images_to_convert/Finale_Wurzelformen_V3.xml",
            "--output-dir",
            str(out),
            "--start",
            family,
            "--end",
            family,
        ]
    )
    assert exit_code == 0
    assert (out / "converted_svgs" / f"{first}.svg").exists()
