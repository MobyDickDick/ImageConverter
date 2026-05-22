#!/usr/bin/env python3
"""Generate sha256 checksums for iteration input/output files."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = ROOT / "stabilization" / "evidence"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True, help="Iteration id")
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted([p for p in base.rglob("*") if p.is_file()])


def write_checksums(target: Path, files: list[Path], relative_to: Path) -> None:
    lines = []
    for path in files:
        checksum = file_sha256(path)
        rel = path.relative_to(relative_to).as_posix()
        lines.append(f"{checksum}  {rel}")
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> int:
    args = parse_args()
    iteration_dir = EVIDENCE_ROOT / args.id
    if not iteration_dir.exists():
        raise SystemExit(f"Missing iteration directory: {iteration_dir}")

    checksum_dir = iteration_dir / "checksums"
    checksum_dir.mkdir(parents=True, exist_ok=True)

    input_files = collect_files(iteration_dir / "input")
    output_files = collect_files(iteration_dir / "output")

    write_checksums(checksum_dir / "input.sha256", input_files, iteration_dir)
    write_checksums(checksum_dir / "output.sha256", output_files, iteration_dir)

    print(f"Wrote checksums for {len(input_files)} input and {len(output_files)} output files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
