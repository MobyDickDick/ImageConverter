#!/usr/bin/env python3
"""Prune top-level Python functions under src/ that are not present in a callTree CSV.

The script reads a call tree export (default: artifacts/descriptions/callTree.csv),
collects function identities from the CSV (`root`, `node`, `parent`) and removes
all top-level `def` / `async def` definitions in `src/` that are not present.

Function identity format used by this script:
    <module_path>:<function_name>
Examples:
    src.iccFs.convertRange:convertRange
    src.__init__:__getattr__
"""

from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set


@dataclass(frozen=True)
class FuncRange:
    fq_name: str
    start: int
    end: int


def module_name_for_path(src_root: Path, path: Path) -> str:
    rel = path.relative_to(src_root).with_suffix("")
    return ".".join((src_root.name, *rel.parts))


def load_reachable_functions(call_tree_csv: Path) -> Set[str]:
    reachable: Set[str] = set()
    with call_tree_csv.open("r", encoding="utf-8", newline="") as handle:
        header = handle.readline()
        handle.seek(0)
        delimiter = ";" if header.count(";") > header.count(",") else ","
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            for key in ("root", "node", "parent"):
                value = (row.get(key) or "").strip()
                if ":" in value:
                    reachable.add(value)
    return reachable


def collect_top_level_functions(src_root: Path) -> Dict[Path, List[FuncRange]]:
    by_file: Dict[Path, List[FuncRange]] = {}
    for path in sorted(src_root.rglob("*.py")):
        if any(part in {"__pycache__", "vendor", "artifacts"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue

        module_name = module_name_for_path(src_root, path)
        funcs: List[FuncRange] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.append(
                    FuncRange(
                        fq_name=f"{module_name}:{node.name}",
                        start=node.lineno,
                        end=node.end_lineno,
                    )
                )
        if funcs:
            by_file[path] = funcs
    return by_file


def remove_line_ranges(text: str, ranges: List[FuncRange]) -> str:
    lines = text.splitlines(keepends=True)
    for item in sorted(ranges, key=lambda x: x.start, reverse=True):
        del lines[item.start - 1 : item.end]
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src-root", type=Path, default=Path("src"))
    parser.add_argument("--call-tree", type=Path, default=Path("artifacts/descriptions/callTree.csv"))
    parser.add_argument("--apply", action="store_true", help="Write removals to disk")
    args = parser.parse_args()

    src_root = args.src_root.resolve()
    call_tree = args.call_tree.resolve()

    reachable = load_reachable_functions(call_tree)
    file_map = collect_top_level_functions(src_root)

    removable_by_file: Dict[Path, List[FuncRange]] = {}
    for path, funcs in file_map.items():
        removable = [f for f in funcs if f.fq_name not in reachable]
        if removable:
            removable_by_file[path] = removable

    total_funcs = sum(len(v) for v in file_map.values())
    total_remove = sum(len(v) for v in removable_by_file.values())

    print(f"Scanned files: {len(file_map)}")
    print(f"Top-level functions found: {total_funcs}")
    print(f"Functions present in call tree: {total_funcs - total_remove}")
    print(f"Functions to remove: {total_remove}")

    for path in sorted(removable_by_file):
        print(f"\\n{path.relative_to(Path.cwd())}:")
        for func in removable_by_file[path]:
            print(f"  - {func.fq_name} (L{func.start}-L{func.end})")

    if not args.apply:
        return 0

    for path, ranges in removable_by_file.items():
        original = path.read_text(encoding="utf-8")
        updated = remove_line_ranges(original, ranges)
        path.write_text(updated, encoding="utf-8")

    print("\\nApplied removals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
