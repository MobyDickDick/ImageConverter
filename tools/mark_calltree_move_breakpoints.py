#!/usr/bin/env python3
"""Annotate move breakpoints in a large module based on call-tree reachability.

Stage 1:
    Insert marker blocks around top-level functions in the source module:

    \"\"\" Start move to File mainFiles/<target.py>
    import <module_a>, <module_b>
    \"\"\"
    def target(...):
        ...
    \"\"\" End move to File mainFiles/<target.py> \"\"\"

The target file is inferred from files below ``src/mainFiles`` with the same
stem as the function name. If multiple files match, the shortest relative path
is selected (stable lexical tie-break).
"""

from __future__ import annotations

import argparse
import ast
import csv
from collections import defaultdict
from pathlib import Path


START_TMPL = '""" Start move to File mainFiles/{target}\nimport {imports}\n"""'
END_TMPL = '""" End move to File mainFiles/{target} """'


def _parse_edges(call_tree_csv: Path) -> dict[str, set[str]]:
    edges: dict[str, set[str]] = defaultdict(set)
    with call_tree_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            caller = (row.get("edge_caller") or "").strip()
            callee = (row.get("edge_callee") or "").strip()
            if caller and callee and caller != callee:
                edges[caller].add(callee)
    return edges


def _reachable(edges: dict[str, set[str]], root: str) -> set[str]:
    seen = {root}
    stack = [root]
    while stack:
        current = stack.pop()
        for callee in edges.get(current, ()):
            if callee in seen:
                continue
            seen.add(callee)
            stack.append(callee)
    seen.discard(root)
    return seen


def _collect_top_level_function_nodes(source_path: Path) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    nodes: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes[node.name] = node
    return nodes


def _imports_for_target_file(target_file: Path, main_files_root: Path) -> list[str]:
    source = target_file.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level > 0:
                current_rel = target_file.relative_to(main_files_root).parent
                if module:
                    module_parts = module.split(".")
                else:
                    module_parts = []
                if node.level - 1 > len(current_rel.parts):
                    # Clamp weird relative imports defensively.
                    base_parts = []
                else:
                    base_parts = list(current_rel.parts[: len(current_rel.parts) - (node.level - 1)])
                imports.add(".".join([*base_parts, *module_parts]).strip("."))
            else:
                imports.add(module)
    return sorted(item for item in imports if item)


def _target_map_for_functions(function_names: set[str], main_files_root: Path) -> dict[str, Path]:
    by_stem: dict[str, list[Path]] = defaultdict(list)
    for path in main_files_root.rglob("*.py"):
        by_stem[path.stem].append(path)

    selected: dict[str, Path] = {}
    for name in sorted(function_names):
        candidates = by_stem.get(name, [])
        if not candidates:
            continue
        candidates_sorted = sorted(
            candidates,
            key=lambda p: (
                len(p.relative_to(main_files_root).parts),
                str(p.relative_to(main_files_root)),
            ),
        )
        selected[name] = candidates_sorted[0]
    return selected


def annotate_breakpoints(
    source_path: Path,
    call_tree_csv: Path,
    main_files_root: Path,
    root_function: str,
) -> int:
    source_text = source_path.read_text(encoding="utf-8")
    lines = source_text.splitlines(keepends=True)
    function_nodes = _collect_top_level_function_nodes(source_path)
    reachable = _reachable(_parse_edges(call_tree_csv), root_function)
    candidates = set(function_nodes).intersection(reachable)
    target_map = _target_map_for_functions(candidates, main_files_root)

    insertions_before: dict[int, str] = {}
    insertions_after: dict[int, str] = {}

    for function_name in sorted(target_map):
        node = function_nodes[function_name]
        if node.lineno is None or node.end_lineno is None:
            continue
        target_rel = target_map[function_name].relative_to(main_files_root).as_posix()
        imports = _imports_for_target_file(target_map[function_name], main_files_root)
        import_text = ", ".join(imports) if imports else "<none>"
        start_block = START_TMPL.format(target=target_rel, imports=import_text) + "\n"
        end_block = END_TMPL.format(target=target_rel) + "\n"

        decorator_start = min((dec.lineno for dec in node.decorator_list), default=node.lineno)
        line_before = decorator_start - 1
        line_after = node.end_lineno
        existing_before = lines[line_before - 1] if line_before - 1 >= 0 else ""
        existing_after = lines[line_after] if line_after < len(lines) else ""
        if '""" Start move to File mainFiles/' in existing_before:
            continue
        if '""" End move to File mainFiles/' in existing_after:
            continue
        insertions_before[decorator_start] = start_block
        insertions_after[node.end_lineno] = end_block

    if not insertions_before and not insertions_after:
        return 0

    output_lines: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        if line_number in insertions_before:
            output_lines.append(insertions_before[line_number])
        output_lines.append(line)
        if line_number in insertions_after:
            output_lines.append(insertions_after[line_number])

    source_path.write_text("".join(output_lines), encoding="utf-8")
    return len(insertions_before)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--call-tree", type=Path, required=True)
    parser.add_argument("--main-files-root", type=Path, default=Path("src/mainFiles"))
    parser.add_argument("--root", default="main")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    count = annotate_breakpoints(
        source_path=args.source,
        call_tree_csv=args.call_tree,
        main_files_root=args.main_files_root,
        root_function=args.root,
    )
    print(f"Inserted breakpoint markers for {count} functions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
