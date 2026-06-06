from __future__ import annotations

import json
import math
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
import src.imageCompositeConverter as converter

BASE = Path("artifacts/regression_baseline/satisfactory")
SOURCE_IMAGES = Path("artifacts/images_to_convert")
SOURCE_SVGS = Path("src/artifacts/converted_images/converted_svgs")
FALLBACK_VARIANTS: tuple[str, ...] = ("AC0800_L", "AC0800_M", "AC0800_S", "AC0811_L", "AC0811_M", "AC0811_S")


def _debug_log(debug_log: Path, event: str, **fields: object) -> None:
    """Persist and print live milestones for the long reconversion battery."""

    debug_log.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "event": event,
        "monotonic_seconds": round(time.perf_counter(), 6),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    with debug_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    details = " ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[satisfactory-regression] {event} {details}".rstrip(), flush=True)


def _debug_log_path(tmp_path: Path, test_name: str) -> Path:
    debug_dir = Path(
        os.environ.get(
            "SATISFACTORY_REGRESSION_DEBUG_DIR",
            str(tmp_path / "satisfactory-regression-debug"),
        )
    )
    return debug_dir / f"{test_name}.jsonl"


def _variants() -> list[str]:
    manifest = BASE / "variants.txt"
    if not manifest.exists():
        return []
    return [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]


def _source_image_path(variant: str) -> Path:
    baseline_image = BASE / "images" / f"{variant}.jpg"
    if baseline_image.exists():
        return baseline_image
    return SOURCE_IMAGES / f"{variant}.jpg"


def _prepare_mini_baseline(base_dir: Path, limit: int = 3) -> list[str]:
    images_dir = base_dir / "images"
    svgs_dir = base_dir / "svgs"
    images_dir.mkdir(parents=True, exist_ok=True)
    svgs_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    requested_variants = _variants() or list(FALLBACK_VARIANTS)
    for variant in requested_variants:
        jpg_src = SOURCE_IMAGES / f"{variant}.jpg"
        svg_src = SOURCE_SVGS / f"{variant}.svg"
        if not jpg_src.exists() or not svg_src.exists():
            continue
        shutil.copy2(jpg_src, images_dir / jpg_src.name)
        shutil.copy2(svg_src, svgs_dir / svg_src.name)
        copied.append(variant)
        if len(copied) >= limit:
            break
    if not copied:
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


def _snapshot_source_images(variants: list[str], snapshot_dir: Path) -> dict[str, Path]:
    """Copy and validate immutable source images for a long reconversion run."""

    if converter.cv2 is None:
        pytest.skip("cv2 not available in this environment")

    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshots: dict[str, Path] = {}
    missing_or_unreadable: list[str] = []
    for variant in variants:
        source_path = _source_image_path(variant)
        image = converter.cv2.imread(str(source_path))
        if image is None:
            missing_or_unreadable.append(f"{variant} ({source_path})")
            continue
        snapshot_path = snapshot_dir / f"{variant.upper()}.jpg"
        shutil.copy2(source_path, snapshot_path)
        if converter.cv2.imread(str(snapshot_path)) is None:
            missing_or_unreadable.append(f"{variant} ({snapshot_path})")
            continue
        snapshots[variant.upper()] = snapshot_path

    assert not missing_or_unreadable, (
        "Missing or unreadable source images: " + ", ".join(missing_or_unreadable[:20])
    )
    return snapshots


def _rendered_mean_delta2(image_path: Path, svg_path: Path) -> float:
    if converter.cv2 is None or converter.np is None:
        pytest.skip("numpy/cv2 not available in this environment")

    image = converter.cv2.imread(str(image_path))
    assert image is not None, f"Could not read source image {image_path}."
    rendered = converter.Action.render_svg_to_numpy(
        svg_path.read_text(encoding="utf-8"),
        image.shape[1],
        image.shape[0],
    )
    if rendered is None:
        pytest.skip(f"SVG rendering not available for quality comparison: {svg_path}")

    diff = image.astype(converter.np.float32) - rendered.astype(converter.np.float32)
    delta2 = converter.np.sum(diff * diff, axis=2)
    return float(converter.np.mean(delta2))


def _reconverted_svg_path(family_out: Path, variant: str) -> Path | None:
    """Return the best available SVG emitted by a family reconversion run."""

    candidates = (
        family_out / "converted_svgs" / f"{variant}.svg",
        family_out / "reports" / "conversion_bestlist_snapshots" / f"{variant}.svg",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _available_reconverted_svgs(family_out: Path) -> list[str]:
    return sorted(
        str(path.relative_to(family_out))
        for root in (
            family_out / "converted_svgs",
            family_out / "reports" / "conversion_bestlist_snapshots",
        )
        if root.exists()
        for path in root.glob("*.svg")
    )


def _require_reconverted_svg_path(family_out: Path, variant: str, available_svgs: list[str]) -> Path:
    new_svg = _reconverted_svg_path(family_out, variant)
    assert new_svg is not None, (
        f"No reconverted SVG output produced for successful variant {variant}. "
        f"Available SVGs: {available_svgs}"
    )
    return new_svg


def _group_variants_by_family(variants: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for variant in variants:
        grouped.setdefault(variant.rsplit("_", 1)[0], []).append(variant)
    return grouped


def _copy_family_inputs(
    family: str,
    variants: list[str],
    input_dir: Path,
    source_paths: dict[str, Path] | None = None,
) -> Path:
    """Create a disposable input folder so conversion failures cannot move fixtures."""

    input_dir.mkdir(parents=True, exist_ok=True)
    for variant in variants:
        if variant.rsplit("_", 1)[0] != family:
            continue
        source_path = (source_paths or {}).get(variant.upper(), _source_image_path(variant))
        shutil.copy2(source_path, input_dir / f"{variant}.jpg")
    return input_dir


def _baseline_ready() -> bool:
    svgs_dir = BASE / "svgs"
    manifest = BASE / "variants.txt"
    if not (svgs_dir.exists() and manifest.exists()):
        return False
    variants = _variants()
    if not variants:
        return False
    return any(_source_image_path(variant).exists() and (svgs_dir / f"{variant}.svg").exists() for variant in variants)


def _ensure_baseline(limit: int = 3) -> None:
    if _baseline_ready():
        return
    _prepare_mini_baseline(BASE, limit=limit)


def test_satisfactory_baseline_has_pairs() -> None:
    _ensure_baseline(limit=3)
    variants = _variants()
    if not variants:
        pytest.skip("No baseline variants found. Run tools/manage_satisfactory_baseline.py first.")

    for variant in variants:
        assert _source_image_path(variant).exists()
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
    family_input = _copy_family_inputs(
        family, variants, tmp_path / "smoke-input"
    )
    exit_code = converter.main(
        [
            str(family_input),
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
def test_all_satisfactory_successful_variants_reconversion_keeps_or_improves_quality(
    tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    debug_log = _debug_log_path(tmp_path, request.node.name)
    start_time = time.perf_counter()
    _debug_log(debug_log, "test_start", nodeid=request.node.nodeid)

    _ensure_baseline(limit=5)
    variants = _variants()
    _debug_log(debug_log, "variants_loaded", variant_count=len(variants))
    if not variants:
        pytest.skip("No baseline variants found.")

    source_image_snapshots = _snapshot_source_images(
        variants, tmp_path / "source-image-snapshots"
    )
    _debug_log(
        debug_log,
        "source_images_snapshotted",
        snapshot_count=len(source_image_snapshots),
    )

    baseline_mean_delta2: dict[str, float] = {}
    missing_pairs: list[str] = []
    for variant in variants:
        _debug_log(debug_log, "baseline_metric_start", variant=variant)
        image_path = source_image_snapshots[variant.upper()]
        svg_path = BASE / "svgs" / f"{variant}.svg"
        if not svg_path.exists():
            missing_pairs.append(variant)
            continue
        baseline_mean_delta2[variant.upper()] = _rendered_mean_delta2(image_path, svg_path)
        _debug_log(
            debug_log,
            "baseline_metric_done",
            variant=variant,
            mean_delta2=f"{baseline_mean_delta2[variant.upper()]:.6f}",
        )

    assert not missing_pairs, "Missing baseline image/SVG pairs: " + ", ".join(missing_pairs[:20])
    if not baseline_mean_delta2:
        pytest.skip("No satisfactory baseline quality metrics could be rendered.")

    out = tmp_path / "all_successful_reconversion"
    reconverted_svg_paths: dict[str, Path] = {}
    grouped_variants = _group_variants_by_family(variants)
    _debug_log(debug_log, "family_groups_ready", family_count=len(grouped_variants))
    for family, family_variants in grouped_variants.items():
        family_start = time.perf_counter()
        _debug_log(
            debug_log,
            "family_conversion_start",
            family=family,
            variant_count=len(family_variants),
        )
        family_input = _copy_family_inputs(
            family,
            family_variants,
            tmp_path / "family-inputs" / family.lower(),
            source_image_snapshots,
        )
        exit_code = converter.main(
            [
                str(family_input),
                "--descriptions-path",
                "artifacts/images_to_convert/Finale_Wurzelformen_V3.xml",
                "--output-dir",
                str(out / family.lower()),
                "--start",
                family,
                "--end",
                family,
                "--deterministic-order",
            ]
        )
        _debug_log(
            debug_log,
            "family_conversion_done",
            family=family,
            exit_code=exit_code,
            duration_seconds=f"{time.perf_counter() - family_start:.3f}",
        )
        assert exit_code == 0
        family_out = out / family.lower()
        available_svgs = _available_reconverted_svgs(family_out)
        for variant in family_variants:
            _debug_log(debug_log, "output_check", family=family, variant=variant)
            reconverted_svg_paths[variant.upper()] = _require_reconverted_svg_path(
                family_out,
                variant,
                available_svgs,
            )

    regressions: list[str] = []
    checked = 0
    quality_epsilon = 1e-6
    for variant, previous_mean_delta2 in baseline_mean_delta2.items():
        _debug_log(debug_log, "quality_compare_start", variant=variant)
        new_svg = reconverted_svg_paths[variant.upper()]
        new_mean_delta2 = _rendered_mean_delta2(
            source_image_snapshots[variant.upper()], new_svg
        )
        allowed_max = previous_mean_delta2 + max(quality_epsilon, abs(previous_mean_delta2) * quality_epsilon)
        _debug_log(
            debug_log,
            "quality_compare_done",
            variant=variant,
            previous_mean_delta2=f"{previous_mean_delta2:.6f}",
            new_mean_delta2=f"{new_mean_delta2:.6f}",
            allowed_max=f"{allowed_max:.6f}",
        )
        if not math.isfinite(new_mean_delta2) or new_mean_delta2 > allowed_max:
            regressions.append(
                f"{variant}: previous_mean_delta2={previous_mean_delta2:.6f}, "
                f"new_mean_delta2={new_mean_delta2:.6f}, allowed_max={allowed_max:.6f}"
            )
        checked += 1

    _debug_log(
        debug_log,
        "test_done",
        checked=checked,
        regression_count=len(regressions),
        duration_seconds=f"{time.perf_counter() - start_time:.3f}",
    )
    assert checked == len(variants)
    assert not regressions, (
        "Successful-conversion quality regressed since the stored baseline conversion: "
        + "; ".join(regressions[:20])
    )


def test_snapshot_source_images_preserves_readable_image_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if converter.cv2 is None or converter.np is None:
        pytest.skip("numpy/cv2 not available in this environment")

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_path = source_dir / "AC9999_S.jpg"
    image = converter.np.full((3, 4, 3), 127, dtype=converter.np.uint8)
    assert converter.cv2.imwrite(str(source_path), image)
    monkeypatch.setattr(
        __import__(__name__, fromlist=["SOURCE_IMAGES"]),
        "SOURCE_IMAGES",
        source_dir,
    )

    snapshots = _snapshot_source_images(["AC9999_S"], tmp_path / "snapshots")

    snapshot_path = snapshots["AC9999_S"]
    assert snapshot_path != source_path
    source_bytes = source_path.read_bytes()
    assert snapshot_path.read_bytes() == source_bytes

    source_path.unlink()
    assert converter.cv2.imread(str(snapshot_path)) is not None
    assert snapshot_path.read_bytes() == source_bytes


def test_snapshot_source_images_reports_unreadable_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    monkeypatch.setattr(
        __import__(__name__, fromlist=["SOURCE_IMAGES"]),
        "SOURCE_IMAGES",
        source_dir,
    )

    with pytest.raises(AssertionError, match="AC9999_S"):
        _snapshot_source_images(["AC9999_S"], tmp_path / "snapshots")


def test_copy_family_inputs_uses_disposable_copies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_path = source_dir / "AC9999_S.jpg"
    source_path.write_bytes(b"source-image")
    monkeypatch.setattr(
        __import__(__name__, fromlist=["SOURCE_IMAGES"]),
        "SOURCE_IMAGES",
        source_dir,
    )

    input_dir = _copy_family_inputs(
        "AC9999", ["AC9999_S"], tmp_path / "conversion-input"
    )
    disposable_path = input_dir / source_path.name
    assert disposable_path.read_bytes() == b"source-image"

    disposable_path.unlink()
    assert source_path.read_bytes() == b"source-image"
