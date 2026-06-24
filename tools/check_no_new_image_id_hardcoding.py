#!/usr/bin/env python3
"""Forbid image/catalog IDs in converter runtime source code."""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


def violations(current: dict[str, dict[str, int]]) -> list[str]:
    problems: list[str] = []
    for path, identifiers in current.items():
        for identifier, count in identifiers.items():
            problems.append(f"{path}: {identifier} occurs {count} time(s)")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT / "src",
        help="Python source tree to scan (defaults to the repository src directory).",
    )
    args = parser.parse_args()
    problems = violations(scan_source(args.source_root))
    if problems:
        print("Image-ID hardcoding is forbidden in runtime source code:")
        print("\n".join(f"- {problem}" for problem in problems))
        return 1
    print("PASS: no image-ID hardcoding found in runtime source code (0 occurrences).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
