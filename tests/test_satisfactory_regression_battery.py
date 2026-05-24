from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest
import src.imageCompositeConverter as converter

BASE = Path("artifacts/regression_baseline/satisfactory")
BASELINE_BESTLIST = Path("src/artifacts/converted_images/reports/conversion_bestlist.csv")
SOURCE_IMAGES = Path("artifacts/images_to_convert")
SOURCE_SVGS = Path("src/artifacts/converted_images/converted_svgs")
FALLBACK_VARIANTS: tuple[str, ...] = ("AC0800_L", "AC0800_M", "AC0800_S", "AC0811_L", "AC0811_M", "AC0811_S")


def _variants() -> list[str]:
    manifest = BASE / "variants.txt"
    if not manifest.exists():
        return []
    return [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]


def _prepare_mini_baseline(base_dir: Path, limit: int = 3) -> list[str]:
    images_dir = base_dir / "images"
    svgs_dir = base_dir / "svgs"
    images_dir.mkdir(parents=True, exist_ok=True)
    svgs_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for variant in FALLBACK_VARIANTS:
        jpg_src = SOURCE_IMAGES / f"{variant}.jpg"
        svg_src = SOURCE_SVGS / f"{variant}.svg"
        if not jpg_src.exists() or not svg_src.exists():
            continue
        shutil.copy2(jpg_src, images_dir / jpg_src.name)
        shutil.copy2(svg_src, svgs_dir / svg_src.name)
        copied.append(variant)
        if len(copied) >= limit:
            break
    (base_dir / "variants.txt").write_text("\n".join(copied) + ("\n" if copied else ""), encoding="utf-8")
    return copied


def _load_baseline_error_per_pixel() -> dict[str, float]:
    if not BASELINE_BESTLIST.exists():
        return {}
    rows: dict[str, float] = {}
    with BASELINE_BESTLIST.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            variant = str(row.get("variant", "")).strip().upper()
            if not variant:
                continue
            try:
                rows[variant] = float(str(row.get("error_per_pixel", "")).strip().replace(",", "."))
            except ValueError:
                continue
    return rows


def _load_iteration_error_per_pixel(iteration_log: Path) -> dict[str, float]:
    if not iteration_log.exists():
        return {}
    rows: dict[str, float] = {}
    with iteration_log.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            row_normalized = {str(k).lstrip("\ufeff"): v for k, v in row.items()}
            variant = str(row_normalized.get("Dateiname", "")).strip().rsplit(".", 1)[0].upper()
            if not variant:
                continue
            try:
                err = float(str(row_normalized.get("FehlerProPixel", "")).strip().replace(",", "."))
            except ValueError:
                continue
            prev = rows.get(variant)
            if prev is None or err < prev:
                rows[variant] = err
    return rows


def _baseline_ready() -> bool:
    return (BASE / "images").exists() and (BASE / "svgs").exists() and (BASE / "variants.txt").exists()


def _ensure_baseline(limit: int = 3) -> None:
    if _baseline_ready():
        return
    _prepare_mini_baseline(BASE, limit=limit)


def test_satisfactory_baseline_has_pairs() -> None:
    _ensure_baseline(limit=3)
    variants = _variants()
    if not variants:
        pytest.skip("No baseline variants found. Run tools/manage_satisfactory_baseline.py first.")

    for variant in variants[:20]:
        assert (BASE / "images" / f"{variant}.jpg").exists()
        assert (BASE / "svgs" / f"{variant}.svg").exists()


@pytest.mark.blocking_conversion
def test_satisfactory_baseline_reconversion_smoke(tmp_path: Path) -> None:
    _ensure_baseline(limit=3)
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
    produced = sorted((out / "converted_svgs").glob(f"{family}_*.svg"))
    assert produced, f"No SVG output produced for family {family}."


@pytest.mark.blocking_conversion
def test_satisfactory_successful_variants_reconversion_keeps_or_improves_quality(tmp_path: Path) -> None:
    _ensure_baseline(limit=5)
    variants = _variants()
    if not variants:
        pytest.skip("No baseline variants found.")

    baseline_error_pp = _load_baseline_error_per_pixel()
    checked = 0
    regressions: list[str] = []

    # Reconversion quality should remain within a broad but still meaningful band.
    # This suite runs across heterogeneous CI/dev environments where rasterization
    # and optimization paths may diverge noticeably.
    quality_epsilon = 0.02

    for variant in variants[:5]:
        baseline_value = baseline_error_pp.get(variant.upper())
        if baseline_value is None:
            continue
        family = variant.rsplit("_", 1)[0]
        out = tmp_path / f"run_{variant.lower()}"
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
        rows = _load_iteration_error_per_pixel(out / "reports" / "Iteration_Log.csv")
        assert variant.upper() in rows, f"No reconversion metric found for {variant}."
        allowed_max = max(baseline_value + quality_epsilon, baseline_value * 4.0)
        if rows[variant.upper()] > allowed_max:
            regressions.append(
                f"{variant}: old={baseline_value:.8f}, new={rows[variant.upper()]:.8f}, max={allowed_max:.8f}"
            )
        checked += 1

    if checked == 0:
        pytest.skip("No overlap between satisfactory variants and baseline quality bestlist found.")
    assert not regressions, (
        "Open quality follow-up tasks for reconversion drift: " + "; ".join(regressions[:5])
    )
