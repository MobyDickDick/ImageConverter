#!/usr/bin/env python3
"""Find source files with identical content under a directory tree.

Default usage scans `src` for Python files and prints duplicate groups with a
suggested shared target path at the common ancestor directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DuplicateGroup:
    files: tuple[Path, ...]
    sha256: str

    @property
    def count(self) -> int:
        return len(self.files)

    def suggested_shared_path(self) -> Path:
        common_dir = Path(os.path.commonpath([str(f.parent) for f in self.files]))
        return common_dir / self.files[0].name



def _iter_files(root: Path, patterns: Iterable[str]) -> Iterable[Path]:
    for pattern in patterns:
        yield from root.rglob(pattern)


def find_duplicates(root: Path, patterns: Iterable[str]) -> list[DuplicateGroup]:
    buckets: dict[str, list[Path]] = defaultdict(list)
    for path in _iter_files(root, patterns):
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        buckets[digest].append(path)

    groups: list[DuplicateGroup] = []
    for digest, files in buckets.items():
        if len(files) > 1:
            groups.append(DuplicateGroup(tuple(sorted(files)), digest))
    groups.sort(key=lambda g: (-g.count, str(g.files[0])))
    return groups


def _to_json(groups: list[DuplicateGroup]) -> str:
    payload = []
    for g in groups:
        payload.append(
            {
                "count": g.count,
                "sha256": g.sha256,
                "suggested_shared_path": str(g.suggested_shared_path()),
                "files": [str(f) for f in g.files],
            }
        )
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="src", help="Root directory to scan (default: src)")
    parser.add_argument(
        "--pattern",
        action="append",
        default=["*.py"],
        help="Glob pattern relative to root; can be passed multiple times (default: *.py)",
    )
    parser.add_argument("--min-count", type=int, default=2, help="Only show groups with at least this many files")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    args = parser.parse_args()

    root = Path(args.root)
    groups = [g for g in find_duplicates(root, args.pattern) if g.count >= args.min_count]

    if args.json:
        print(_to_json(groups))
        return 0

    if not groups:
        print("No duplicate source files found.")
        return 0

    print(f"Found {len(groups)} duplicate group(s) under {root}.")
    for i, g in enumerate(groups, start=1):
        print(f"\n[{i}] {g.count} files, sha256={g.sha256[:12]}…")
        print(f"    Suggested shared file: {g.suggested_shared_path()}")
        for f in g.files:
            print(f"    - {f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
