#!/usr/bin/env python3
"""Find and optionally deduplicate duplicated top-level functions.

Rule implemented from task:
- If a function exists in multiple files and at least one of those files contains exactly one
  top-level function, keep that single-function-module definition as canonical.
- Remove duplicate definitions from other files and import the canonical function instead.

Safety constraints for --apply:
- Only applies when function bodies are text-identical (ignoring surrounding whitespace).
- Only rewrites .py files under the provided root (default: src).
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class FuncDef:
    name: str
    path: Path
    start: int
    end: int
    source: str


def module_name(root: Path, path: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def load_functions(root: Path) -> Tuple[Dict[str, List[FuncDef]], Dict[Path, int]]:
    funcs: Dict[str, List[FuncDef]] = {}
    per_file_count: Dict[Path, int] = {}

    for path in sorted(root.rglob("*.py")):
        if any(part in {"vendor", "artifacts", "__pycache__"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        lines = text.splitlines(keepends=True)
        top_funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
        per_file_count[path] = len(top_funcs)
        for fn in top_funcs:
            seg = "".join(lines[fn.lineno - 1 : fn.end_lineno])
            funcs.setdefault(fn.name, []).append(
                FuncDef(
                    name=fn.name,
                    path=path,
                    start=fn.lineno,
                    end=fn.end_lineno,
                    source=seg.strip(),
                )
            )
    return funcs, per_file_count


def choose_canonical(cands: List[FuncDef], per_file_count: Dict[Path, int]) -> FuncDef | None:
    single_file_defs = [c for c in cands if per_file_count.get(c.path) == 1]
    if not single_file_defs:
        return None
    # Deterministic choice: shortest module path, then lexicographic.
    single_file_defs.sort(key=lambda c: (len(c.path.as_posix()), c.path.as_posix()))
    return single_file_defs[0]


def ensure_import(text: str, import_stmt: str) -> str:
    if import_stmt in text:
        return text
    lines = text.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    # Skip module docstring if present.
    joined = "".join(lines)
    try:
        tree = ast.parse(joined)
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
            insert_at = tree.body[0].end_lineno
    except SyntaxError:
        pass

    # After existing imports if any.
    try:
        tree = ast.parse(joined)
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                insert_at = max(insert_at, node.end_lineno)
            else:
                break
    except SyntaxError:
        pass

    lines.insert(insert_at, f"{import_stmt}\n")
    return "".join(lines)


def remove_range(text: str, start: int, end: int) -> str:
    lines = text.splitlines(keepends=True)
    del lines[start - 1 : end]
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="src", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    funcs, per_file_count = load_functions(root)

    planned: List[Tuple[FuncDef, FuncDef]] = []
    for name, defs in sorted(funcs.items()):
        if len(defs) < 2:
            continue
        canonical = choose_canonical(defs, per_file_count)
        if canonical is None:
            continue
        for d in defs:
            if d.path == canonical.path:
                continue
            if d.source == canonical.source:
                planned.append((d, canonical))

    if not planned:
        print("No safe deduplication opportunities found.")
        return 0

    print("Potential deduplications:")
    for dup, canon in planned:
        print(f"- {dup.name}: {dup.path.relative_to(root)} -> {canon.path.relative_to(root)}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to rewrite files.")
        return 0

    # Group edits per file.
    by_file: Dict[Path, List[Tuple[FuncDef, FuncDef]]] = {}
    for dup, canon in planned:
        by_file.setdefault(dup.path, []).append((dup, canon))

    for path, edits in by_file.items():
        text = path.read_text(encoding="utf-8")
        # Remove from bottom to top.
        for dup, _ in sorted(edits, key=lambda x: x[0].start, reverse=True):
            text = remove_range(text, dup.start, dup.end)
        for dup, canon in edits:
            mod = module_name(root, canon.path)
            text = ensure_import(text, f"from {mod} import {dup.name}")
        path.write_text(text, encoding="utf-8")

    print("Applied deduplication edits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
