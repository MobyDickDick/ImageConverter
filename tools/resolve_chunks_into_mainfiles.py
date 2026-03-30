#!/usr/bin/env python3
"""Resolve chunked runtime source into explicit mainFiles modules.

This script rebuilds ``src/mainFiles/image_composite_converter_runtime.py`` from its
chunk files, extracts top-level function definitions, and writes them into existing
``src/mainFiles/**/*.py`` files with explicit imports only.

Import style produced:
- ``from package.module import symbol``
- ``import package.module`` (fallback only when symbol name cannot be resolved)

It also prints a one-level call/import tree (caller -> direct callees).
"""

from __future__ import annotations

import argparse
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class RuntimeLayout:
    chunk_dir: Path
    chunk_files: list[str]


def _parse_runtime_loader(runtime_loader: Path) -> RuntimeLayout:
    text = runtime_loader.read_text(encoding="utf-8")
    base = runtime_loader.parent

    chunk_dir_match = re.search(r"_CHUNK_DIR\s*=\s*_BASE_DIR\s*/\s*['\"]([^'\"]+)['\"]", text)
    if not chunk_dir_match:
        raise ValueError(f"Could not parse _CHUNK_DIR in {runtime_loader}")
    chunk_dir = base / chunk_dir_match.group(1)

    files_match = re.search(r"_CHUNK_FILES\s*=\s*\[(.*?)\]", text, flags=re.S)
    if not files_match:
        raise ValueError(f"Could not parse _CHUNK_FILES in {runtime_loader}")
    chunk_files = re.findall(r"['\"]([^'\"]+\.py)['\"]", files_match.group(1))
    if not chunk_files:
        raise ValueError(f"No chunk files found in {runtime_loader}")

    return RuntimeLayout(chunk_dir=chunk_dir, chunk_files=chunk_files)


def _combined_chunk_source(layout: RuntimeLayout) -> str:
    return "".join((layout.chunk_dir / name).read_text(encoding="utf-8") for name in layout.chunk_files)


def _function_sources(source_text: str) -> dict[str, str]:
    tree = ast.parse(source_text)
    lines = source_text.splitlines(keepends=True)
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.lineno and node.end_lineno:
                out[node.name] = "".join(lines[node.lineno - 1 : node.end_lineno])
    return out


def _direct_callees(source_text: str) -> dict[str, set[str]]:
    tree = ast.parse(source_text)
    out: dict[str, set[str]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        names: set[str] = set()
        for inner in ast.walk(node):
            if isinstance(inner, ast.Call):
                fn = inner.func
                if isinstance(fn, ast.Name):
                    names.add(fn.id)
                elif isinstance(fn, ast.Attribute):
                    names.add(fn.attr)
        out[node.name] = names
    return out


def _module_path_for_file(file_path: Path, src_root: Path) -> str:
    rel = file_path.relative_to(src_root).with_suffix("")
    return ".".join(rel.parts)


def _target_files_by_stem(main_files_root: Path) -> dict[str, Path]:
    by_stem: dict[str, list[Path]] = {}
    for p in main_files_root.rglob("*.py"):
        if p.name == "__init__.py":
            continue
        by_stem.setdefault(p.stem, []).append(p)
    selected: dict[str, Path] = {}
    for stem, candidates in by_stem.items():
        candidates_sorted = sorted(
            candidates,
            key=lambda c: (len(c.relative_to(main_files_root).parts), str(c.relative_to(main_files_root))),
        )
        selected[stem] = candidates_sorted[0]
    return selected


def _replace_single_function(old_text: str, fn_name: str, new_fn_src: str) -> str:
    tree = ast.parse(old_text)
    lines = old_text.splitlines(keepends=True)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name:
            if not node.lineno or not node.end_lineno:
                continue
            start, end = node.lineno - 1, node.end_lineno
            return "".join(lines[:start]) + new_fn_src + "\n" + "".join(lines[end:])
    sep = "" if old_text.endswith("\n") else "\n"
    return old_text + sep + "\n" + new_fn_src + "\n"


def _clean_runtime_star_bridge(old_text: str) -> str:
    lines = old_text.splitlines()
    filtered: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("from src import image_composite_converter as _icc"):
            continue
        if stripped.startswith("globals().update(vars(_icc))"):
            continue
        filtered.append(line)
    cleaned = "\n".join(filtered).strip() + "\n"
    return cleaned


def _render_explicit_imports(
    fn_name: str,
    callee_table: dict[str, set[str]],
    stem_to_target: dict[str, Path],
    src_root: Path,
) -> list[str]:
    imports: list[str] = []
    for callee in sorted(callee_table.get(fn_name, set())):
        target = stem_to_target.get(callee)
        if not target:
            continue
        mod = _module_path_for_file(target, src_root)
        imports.append(f"from {mod} import {callee}")
    return sorted(set(imports))


def _process(
    src_root: Path,
    main_files_root: Path,
    runtime_loader: Path,
    only_callers: Iterable[str] | None,
    dry_run: bool,
) -> tuple[int, list[str]]:
    layout = _parse_runtime_loader(runtime_loader)
    combined = _combined_chunk_source(layout)
    function_sources = _function_sources(combined)
    callee_table = _direct_callees(combined)
    stem_to_target = _target_files_by_stem(main_files_root)

    selected = set(only_callers or [])
    changed = 0
    tree_lines: list[str] = []

    for fn_name, fn_source in sorted(function_sources.items()):
        if selected and fn_name not in selected:
            continue
        target = stem_to_target.get(fn_name)
        if target is None:
            continue

        imports = _render_explicit_imports(fn_name, callee_table, stem_to_target, src_root)
        tree_lines.append(f"{fn_name}")
        for imp in imports:
            tree_lines.append(f"  └─ {imp}")

        old_text = target.read_text(encoding="utf-8")
        new_text = _clean_runtime_star_bridge(old_text)
        new_text = _replace_single_function(new_text, fn_name, fn_source)

        # prepend explicit imports if missing
        if imports:
            header = "\n".join(imports) + "\n\n"
            if not all(imp in new_text for imp in imports):
                new_text = header + new_text

        if new_text != old_text:
            changed += 1
            if not dry_run:
                target.write_text(new_text, encoding="utf-8")

    return changed, tree_lines


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src-root", type=Path, default=Path("src"))
    p.add_argument("--main-files-root", type=Path, default=Path("src/mainFiles"))
    p.add_argument(
        "--runtime-loader",
        type=Path,
        default=Path("src/mainFiles/image_composite_converter_runtime.py"),
    )
    p.add_argument("--only", nargs="*", default=None, help="Optional list of function names to process")
    p.add_argument("--apply", action="store_true", help="Write files (default: dry-run)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    changed, tree_lines = _process(
        src_root=args.src_root,
        main_files_root=args.main_files_root,
        runtime_loader=args.runtime_loader,
        only_callers=args.only,
        dry_run=not args.apply,
    )
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] files that would change: {changed}")
    print("One-level import tree:")
    for line in tree_lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
