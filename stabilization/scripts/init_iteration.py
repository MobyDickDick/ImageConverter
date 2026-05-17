#!/usr/bin/env python3
"""Initialize evidence structure for a new iteration."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / "stabilization" / "evidence"
REPORT_TEMPLATE = ROOT / "stabilization" / "templates" / "report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True, help="Iteration id, e.g. iter-2026-05-17-a")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    iteration_dir = EVIDENCE_ROOT / args.id

    if iteration_dir.exists():
        raise SystemExit(f"Iteration already exists: {iteration_dir}")

    for folder in ("input", "output", "checksums", "config"):
        (iteration_dir / folder).mkdir(parents=True, exist_ok=False)

    report_target = iteration_dir / "report.md"
    shutil.copy2(REPORT_TEMPLATE, report_target)
    report_target.write_text(
        report_target.read_text(encoding="utf-8").replace("<ITERATION_ID>", args.id),
        encoding="utf-8",
    )

    print(f"Initialized iteration: {iteration_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
