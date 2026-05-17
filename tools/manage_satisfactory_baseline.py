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


def main() -> int:
    parser = argparse.ArgumentParser(description="Store satisfactory conversion pairs in a protected baseline folder.")
    parser.add_argument("--variants-file", type=Path, default=Path("successed_conversions.txt"))
    parser.add_argument("--images-dir", type=Path, default=Path("artifacts/images_to_convert"))
    parser.add_argument("--svgs-dir", type=Path, default=Path("artifacts/converted_images/converted_svgs"))
    parser.add_argument("--baseline-dir", type=Path, default=Path("artifacts/regression_baseline/satisfactory"))
    parser.add_argument("--move", action="store_true", help="Move files instead of copying them.")
    args = parser.parse_args()

    variants = _read_variants(args.variants_file)
    missing: list[str] = []
    moved = 0
    prepared_variants: list[str] = []
    for variant in variants:
        jpg_src = args.images_dir / f"{variant}.jpg"
        svg_src = args.svgs_dir / f"{variant}.svg"
        if not jpg_src.exists() or not svg_src.exists():
            missing.append(variant)
            continue
        _move_or_copy(jpg_src, args.baseline_dir / "images" / jpg_src.name, move=args.move)
        _move_or_copy(svg_src, args.baseline_dir / "svgs" / svg_src.name, move=args.move)
        moved += 1
        prepared_variants.append(variant)

    print(f"Prepared baseline pairs: {moved}")
    if missing:
        print(f"Missing pairs: {len(missing)}")
        for v in missing[:20]:
            print(f"  - {v}")
    manifest = args.baseline_dir / "variants.txt"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("\n".join(prepared_variants) + "\n", encoding="utf-8")
    print(f"Manifest written: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
