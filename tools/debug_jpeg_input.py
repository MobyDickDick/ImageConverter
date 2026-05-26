from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path



def _add_vendored_site_packages() -> None:
    root = Path(__file__).resolve().parents[1]
    vendor_root = root / "vendor"
    candidates = [
        vendor_root / "linux-py310" / "site-packages",
        vendor_root / "linux-py311" / "site-packages",
        vendor_root / "linux-py312" / "site-packages",
    ]
    for candidate in candidates:
        if candidate.exists():
            path_text = str(candidate)
            if path_text not in sys.path:
                sys.path.insert(0, path_text)


def inspect_image(path: Path) -> dict[str, object]:
    _add_vendored_site_packages()
    from PIL import Image, ImageFile

    result: dict[str, object] = {
        "path": str(path),
        "exists": path.exists(),
    }
    if not path.exists():
        return result

    result["size_bytes"] = path.stat().st_size
    result["suffix"] = path.suffix.lower()

    try:
        with Image.open(path) as img:
            result["format"] = img.format
            result["mode"] = img.mode
            result["size"] = {"width": img.width, "height": img.height}
            result["bands"] = list(img.getbands())
            result["info_keys"] = sorted(str(k) for k in img.info.keys())
            exif = img.getexif()
            result["exif_count"] = len(exif) if exif is not None else 0
            img.load()
            result["load_ok"] = True
    except Exception as exc:  # diagnostic helper
        result["load_ok"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"

    parser_enabled = ImageFile.LOAD_TRUNCATED_IMAGES
    result["pillow_load_truncated_images"] = bool(parser_enabled)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostik für JPG-Eingabedateien")
    parser.add_argument("image", type=Path, help="Pfad zur JPG-Datei")
    parser.add_argument("--out", type=Path, default=None, help="Optionaler JSON-Outputpfad")
    args = parser.parse_args()

    report = inspect_image(args.image)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
