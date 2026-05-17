#!/usr/bin/env python3
"""Export a secured iteration to an external destination."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / "stabilization" / "evidence"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True, help="Iteration id")
    parser.add_argument("--dest", required=True, help="Export base directory")
    return parser.parse_args()


def current_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    args = parse_args()
    iteration_dir = EVIDENCE_ROOT / args.id
    if not iteration_dir.exists():
        raise SystemExit(f"Missing iteration directory: {iteration_dir}")

    dest_root = Path(args.dest).expanduser().resolve()
    export_dir = dest_root / args.id

    if export_dir.exists():
        raise SystemExit(f"Export target exists already: {export_dir}")

    export_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(iteration_dir, export_dir)

    metadata = {
        "iteration": args.id,
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": current_commit(),
    }
    lines = [f"{key}: {value}" for key, value in metadata.items()]
    (export_dir / "export-metadata.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Exported iteration to: {export_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
