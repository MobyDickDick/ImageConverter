#!/usr/bin/env python3
"""Prevent new image/catalog IDs from being embedded in converter source code."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "config" / "legacy_image_id_baseline.json"
ID_PATTERN = re.compile(r"\b(?:AC|AR|GE|DLG|SE)\d{3,4}\b", re.IGNORECASE)


def scan_source(source_root: Path | None = None) -> dict[str, dict[str, int]]:
    source_root = source_root or ROOT / "src"
    result: dict[str, dict[str, int]] = {}
    for path in sorted(source_root.rglob("*.py")):
        counts = Counter(match.upper() for match in ID_PATTERN.findall(path.read_text(encoding="utf-8")))
        if counts:
            try:
                report_path = path.relative_to(ROOT).as_posix()
            except ValueError:
                report_path = f"src/{path.relative_to(source_root).as_posix()}"
            result[report_path] = dict(sorted(counts.items()))
    return result


def violations(current: dict[str, dict[str, int]], baseline: dict[str, dict[str, int]]) -> list[str]:
    problems: list[str] = []
    for path, identifiers in current.items():
        allowed = baseline.get(path, {})
        for identifier, count in identifiers.items():
            previous = int(allowed.get(identifier, 0))
            if count > previous:
                problems.append(f"{path}: {identifier} occurs {count} time(s), baseline allows {previous}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT / "src",
        help="Python source tree to scan (defaults to the repository src directory).",
    )
    parser.add_argument("--update", action="store_true", help="Replace the migration baseline with the current inventory.")
    args = parser.parse_args()
    current = scan_source(args.source_root)
    if args.update:
        payload = {
            "schema_version": 1,
            "purpose": "Migration ratchet only; never loaded by converter runtime. Counts may decrease but not increase.",
            "files": current,
        }
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Updated {args.baseline}")
        return 0
    payload = json.loads(args.baseline.read_text(encoding="utf-8"))
    problems = violations(current, payload.get("files", {}))
    if problems:
        print("New image-ID hardcoding is forbidden:")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    total = sum(sum(ids.values()) for ids in current.values())
    print(f"PASS: no image-ID hardcoding above legacy baseline ({total} legacy occurrences remain).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
