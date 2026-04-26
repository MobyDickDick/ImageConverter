from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

FORM_CODE_PATTERN = re.compile(r"\b(?:AC|GE|AR)\d{4}(?:_[A-Za-z0-9]+)?\b")


@dataclass(frozen=True)
class FormCodeHit:
    code: str
    file: str
    line: int
    column: int
    line_text: str


def collect_form_code_hits(source_root: Path) -> list[FormCodeHit]:
    hits: list[FormCodeHit] = []
    for path in sorted(source_root.rglob("*.py")):
        rel = path.as_posix()
        if "/__pycache__/" in rel:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in FORM_CODE_PATTERN.finditer(line):
                hits.append(
                    FormCodeHit(
                        code=match.group(0),
                        file=rel,
                        line=line_number,
                        column=match.start() + 1,
                        line_text=line.strip(),
                    )
                )
    return hits


def write_inventory_csv(hits: Iterable[FormCodeHit], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["code", "file", "line", "column", "line_text"])
        for hit in hits:
            writer.writerow([hit.code, hit.file, hit.line, hit.column, hit.line_text])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a runtime form-code inventory by scanning Python runtime modules "
            "for hard-coded form identifiers like ACxxxx/GEyyyy/ARzzzz."
        )
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("src"),
        help="Root directory to scan for Python runtime modules (default: src).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/reports/form_code_inventory.csv"),
        help="CSV output path (default: artifacts/reports/form_code_inventory.csv).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.source_root.exists():
        parser.error(f"Source root does not exist: {args.source_root}")

    hits = collect_form_code_hits(args.source_root)
    write_inventory_csv(hits, args.output)
    print(f"Wrote {len(hits)} form-code hits to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
