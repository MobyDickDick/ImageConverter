#!/usr/bin/env python3
"""Split a Python module into call-tree folders based on a CSV export.

Example:
    python tools/split_module_by_call_tree.py \
      --source src/image_composite_converter.py \
      --call-tree artifacts/converted_images/reports/call_tree_image_composite_converter.csv \
      --root main \
      --output-dir split_by_call_tree
"""

from __future__ import annotations

import argparse
import ast
import csv
import re
from collections import defaultdict
from pathlib import Path


INVALID_NAME_CHARS = re.compile(r"[^0-9A-Za-z_]+")


def sanitize_name(name: str) -> str:
    sanitized = INVALID_NAME_CHARS.sub("_", name)
    return sanitized if sanitized else "unknown"


def parse_call_tree_edges(csv_path: Path) -> dict[str, set[str]]:
    edges: dict[str, set[str]] = defaultdict(set)
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            caller = (row.get("edge_caller") or "").strip()
            callee = (row.get("edge_callee") or "").strip()
            if not caller or not callee:
                continue
            if caller == callee:
                continue
            edges[caller].add(callee)
    return edges


def collect_function_sources(source_path: Path) -> dict[str, str]:
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    snippets: dict[str, str] = {}

    def capture(node: ast.AST, name: str) -> None:
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)
        if not start or not end:
            return
        snippets[name] = "".join(lines[start - 1 : end])

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            capture(node, node.name)
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    capture(child, f"{node.name}.{child.name}")
    return snippets


def write_function_file(path: Path, function_name: str, source_snippets: dict[str, str]) -> None:
    content = source_snippets.get(function_name)
    if content is None:
        content = (
            f"# Function body for '{function_name}' could not be extracted from the source module.\n"
            "# This placeholder is still created to keep the call-tree structure complete.\n"
        )
    path.write_text(content, encoding="utf-8")


def build_tree(
    root: str,
    edges: dict[str, set[str]],
    output_dir: Path,
    source_snippets: dict[str, str],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    def recurse(node: str, container_dir: Path, stack: tuple[str, ...]) -> None:
        children = sorted(edges.get(node, set()))
        for child in children:
            child_safe = sanitize_name(child)
            function_file = container_dir / f"{child_safe}.py"
            write_function_file(function_file, child, source_snippets)

            child_folder = container_dir / f"{child_safe}Files"
            if child in stack:
                cycle_note = (
                    f"# Cycle detected: {' -> '.join((*stack, child))}\n"
                    "# Recursion stopped here to avoid infinite nesting.\n"
                )
                child_folder.mkdir(parents=True, exist_ok=True)
                (child_folder / "CYCLE.txt").write_text(cycle_note, encoding="utf-8")
                continue

            child_folder.mkdir(parents=True, exist_ok=True)
            recurse(child, child_folder, (*stack, child))

    root_dir = output_dir / f"{sanitize_name(root)}Files"
    root_dir.mkdir(parents=True, exist_ok=True)
    recurse(root, root_dir, (root,))


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Path to the Python module source file")
    parser.add_argument("--call-tree", type=Path, required=True, help="Path to the exported call-tree CSV")
    parser.add_argument("--root", default="main", help="Root function to start from (default: main)")
    parser.add_argument("--output-dir", type=Path, default=Path("split_by_call_tree"), help="Output directory for generated tree")
    return parser.parseArgs()


def main() -> int:
    args = parseArgs()
    edges = parse_call_tree_edges(args.call_tree)
    snippets = collect_function_sources(args.source)
    build_tree(args.root, edges, args.output_dir, snippets)
    print(f"Generated call-tree split under: {args.output_dir / (sanitize_name(args.root) + 'Files')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
