"""Compare curated sample SVGs with accepted best-list SVG snapshots.

The converter treats ``artifacts/images_to_convert/samples`` as optional fallback
or reference material.  Accepted best-list snapshots can therefore differ
substantially because they are generated/optimized against raster inputs, restored
from previous quality runs, or selected from a sample only when the validation log
records that decision.  This helper makes that provenance visible in a compact CSV.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

TAG_RE = re.compile(r"<\s*([a-zA-Z_:][\w:.-]*)\b")
STATUS_RE = re.compile(r"^status=(.*)$", re.MULTILINE)
SAMPLE_PATH_RE = re.compile(r"^sample_svg_path=(.*)$", re.MULTILINE)


def _svg_stats(path: Path | None) -> dict[str, object]:
    if path is None or not path.exists():
        return {
            "exists": False,
            "bytes": 0,
            "elements": 0,
            "image_tags": 0,
            "root": "",
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    tags = TAG_RE.findall(text)
    return {
        "exists": True,
        "bytes": len(text.encode("utf-8")),
        "elements": len(tags),
        "image_tags": sum(1 for tag in tags if tag.lower().endswith("image")),
        "root": tags[0] if tags else "",
    }


def _sample_candidates(variant: str) -> list[str]:
    candidates = [variant]
    for suffix in ("_S", "_M", "_L"):
        if variant.endswith(suffix):
            candidates.append(variant[: -len(suffix)])
    if variant.upper().endswith("_SIA"):
        candidates.append(variant[:-4] + "sia")
    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result


def _find_sample(samples_dir: Path, variant: str) -> Path | None:
    for candidate in _sample_candidates(variant):
        path = samples_dir / f"{candidate}.svg"
        if path.exists():
            return path
    return None


def _read_log_status(snapshot_dir: Path, variant: str) -> tuple[str, str]:
    log_path = snapshot_dir / f"{variant}_element_validation.log"
    if not log_path.exists():
        return "", ""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    status_match = STATUS_RE.search(text)
    sample_path_match = SAMPLE_PATH_RE.search(text)
    return (
        status_match.group(1).strip() if status_match else "",
        sample_path_match.group(1).strip() if sample_path_match else "",
    )


def _explain(*, sample: Path | None, bestlist: Path, same_content: bool, status: str, logged_sample_path: str) -> str:
    if same_content:
        return "identical: bestlist snapshot matches the sample SVG bytes"
    if status in {"non_composite_plan_b_sample_svg_selected", "manual_review_plan_b_sample_svg"}:
        if logged_sample_path and sample and Path(logged_sample_path).name != sample.name:
            return "different sample source: validation log selected another sample SVG"
        return "sample selected but bytes differ: likely sanitized or restored snapshot"
    if status:
        return f"generated/restored bestlist artifact: validation status is {status}"
    if not sample:
        return "no matching sample SVG found; bestlist is converter output or restored snapshot"
    return "different by design: samples are references/fallbacks, bestlist contains accepted converter output"


def build_rows(samples_dir: Path, snapshot_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for bestlist in sorted(snapshot_dir.glob("*.svg")):
        variant = bestlist.stem
        sample = _find_sample(samples_dir, variant)
        sample_stats = _svg_stats(sample)
        bestlist_stats = _svg_stats(bestlist)
        same_content = bool(sample and sample.read_bytes() == bestlist.read_bytes())
        status, logged_sample_path = _read_log_status(snapshot_dir, variant)
        rows.append(
            {
                "variant": variant,
                "sample_path": str(sample or ""),
                "bestlist_path": str(bestlist),
                "same_content": int(same_content),
                "sample_bytes": sample_stats["bytes"],
                "bestlist_bytes": bestlist_stats["bytes"],
                "sample_elements": sample_stats["elements"],
                "bestlist_elements": bestlist_stats["elements"],
                "sample_image_tags": sample_stats["image_tags"],
                "bestlist_image_tags": bestlist_stats["image_tags"],
                "status": status,
                "logged_sample_path": logged_sample_path,
                "explanation": _explain(
                    sample=sample,
                    bestlist=bestlist,
                    same_content=same_content,
                    status=status,
                    logged_sample_path=logged_sample_path,
                ),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-dir", type=Path, default=Path("artifacts/images_to_convert/samples"))
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path("artifacts/converted_images/reports/conversion_bestlist_snapshots"),
    )
    parser.add_argument("--output", type=Path, default=Path("artifacts/converted_images/reports/sample_bestlist_svg_comparison.csv"))
    args = parser.parse_args()

    rows = build_rows(args.samples_dir, args.snapshot_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else ["variant"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
