from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _read_variants(path: Path) -> list[str]:
    variants: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        variants.append(line.split(";", 1)[0].strip())
    return sorted(set(variants))


def _move_or_copy(src: Path, dst: Path, *, move: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if move:
        if dst.exists():
            dst.unlink()
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(src, dst)


def _write_manifest(manifest: Path, variants: list[str], *, append: bool) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    existing: list[str] = []
    if append and manifest.exists():
        existing = _read_variants(manifest)
    merged = sorted(set(existing + variants))
    manifest.write_text("\n".join(merged) + ("\n" if merged else ""), encoding="utf-8")


def prepare_baseline_pairs(
    variants: list[str],
    *,
    images_dir: Path,
    svgs_dir: Path,
    baseline_dir: Path,
    move: bool = False,
    append_manifest: bool = False,
) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    prepared_variants: list[str] = []
    for variant in sorted(set(variants)):
        jpg_src = images_dir / f"{variant}.jpg"
        svg_src = svgs_dir / f"{variant}.svg"
        if not jpg_src.exists() or not svg_src.exists():
            missing.append(variant)
            continue
        _move_or_copy(jpg_src, baseline_dir / "images" / jpg_src.name, move=move)
        _move_or_copy(svg_src, baseline_dir / "svgs" / svg_src.name, move=move)
        prepared_variants.append(variant)

    _write_manifest(baseline_dir / "variants.txt", prepared_variants, append=append_manifest)
    return prepared_variants, missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Store satisfactory conversion pairs in a protected baseline folder.")
    parser.add_argument("--variants-file", type=Path, default=Path("successed_conversions.txt"))
    parser.add_argument("--images-dir", type=Path, default=Path("artifacts/images_to_convert"))
    parser.add_argument("--svgs-dir", type=Path, default=Path("artifacts/converted_images/converted_svgs"))
    parser.add_argument("--baseline-dir", type=Path, default=Path("artifacts/regression_baseline/satisfactory"))
    parser.add_argument("--move", action="store_true", help="Move files instead of copying them.")
    parser.add_argument("--append-manifest", action="store_true", help="Keep existing baseline variants and add the prepared variants.")
    args = parser.parse_args()

    variants = _read_variants(args.variants_file)
    prepared_variants, missing = prepare_baseline_pairs(
        variants,
        images_dir=args.images_dir,
        svgs_dir=args.svgs_dir,
        baseline_dir=args.baseline_dir,
        move=args.move,
        append_manifest=args.append_manifest,
    )

    print(f"Prepared baseline pairs: {len(prepared_variants)}")
    if missing:
        print(f"Missing pairs: {len(missing)}")
        for v in missing[:20]:
            print(f"  - {v}")
    manifest = args.baseline_dir / "variants.txt"
    print(f"Manifest written: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
