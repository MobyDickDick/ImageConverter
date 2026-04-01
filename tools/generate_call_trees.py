from __future__ import annotations

import ast
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]

MODULES: dict[str, list[str]] = {
    "src/imageCompositeConverter.py": ["main"],
    "src/imageCompositeConverterRegions.py": ["analyzeRangeImpl"],
    "src/overviewTiles.py": [
        "generateConversionOverviews",
        "createTiledOverviewImage",
        "_resolveOptionalDependencies",
        "_readPreview",
        "_readRaster",
    ],
}


@dataclass(frozen=True)
class Row:
    source_file: str
    entrypoint_from_main: str
    depth: int
    function: str
    function_camel_case: str
    called_by: str
    path_from_main: str


class CallExtractor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        name: str | None = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name:
            self.calls.append(name)
        self.generic_visit(node)


def analyze_module(path: Path) -> tuple[set[str], dict[str, list[str]]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    defined: set[str] = set()
    calls: dict[str, list[str]] = {}

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        defined.add(node.name)
        extractor = CallExtractor()
        for stmt in node.body:
            extractor.visit(stmt)
        calls[node.name] = extractor.calls

    return defined, calls


def snake_to_camel(name: str) -> str:
    if "_" not in name:
        return name[0].lower() + name[1:] if name else name
    parts = [p for p in name.split("_") if p]
    if not parts:
        return name
    out = parts[0] + "".join(p.capitalize() for p in parts[1:])
    return f"_{out}" if name.startswith("_") else out


def walk_rows(source_file: str, entrypoint: str, calls: dict[str, list[str]], defined: set[str]) -> list[Row]:
    occurrences: dict[str, list[list[str]]] = {}
    first_seen_order: list[str] = []

    def dfs_paths(current: str, path: list[str]) -> None:
        if current not in occurrences:
            first_seen_order.append(current)
        occurrences.setdefault(current, []).append(path)
        for callee in calls.get(current, []):
            if callee in defined and callee not in path:
                dfs_paths(callee, [*path, callee])

    dfs_paths(entrypoint, [entrypoint])

    def lca_node(paths: list[list[str]]) -> str:
        common = paths[0]
        for path in paths[1:]:
            max_len = min(len(common), len(path))
            i = 0
            while i < max_len and common[i] == path[i]:
                i += 1
            common = common[:i]
        return common[-1]

    parent_by_function: dict[str, str] = {entrypoint: ""}
    for function, seen_paths in occurrences.items():
        if function == entrypoint:
            continue
        parent_paths = [p[:-1] for p in seen_paths]
        parent_by_function[function] = lca_node(parent_paths)

    children: dict[str, list[str]] = {}
    for function in first_seen_order:
        children.setdefault(function, [])
    for function in first_seen_order:
        if function == entrypoint:
            continue
        parent = parent_by_function[function]
        if function not in children[parent]:
            children[parent].append(function)

    rows: list[Row] = []

    def emit(current: str, depth: int, path: list[str]) -> None:
        rows.append(
            Row(
                source_file,
                entrypoint,
                depth,
                current,
                snake_to_camel(current),
                parent_by_function[current],
                " > ".join(path),
            )
        )
        for child in children.get(current, []):
            emit(child, depth + 1, [*path, child])

    emit(entrypoint, 0, [entrypoint])
    return rows


def make_markdown(rows_by_module: dict[str, dict[str, list[Row]]]) -> str:
    lines = [
        "# Call Trees ab `main()`",
        "",
        "Automatisch erzeugte, **statische** Aufrufbäume (AST-basiert) ausgehend von den dokumentierten Einstiegspunkten.",
    ]
    for module, entrypoints in rows_by_module.items():
        lines += ["", f"## `{module}`"]
        for entry, rows in entrypoints.items():
            lines.append("")
            if module == "src/imageCompositeConverter.py" and entry == "main":
                lines.append(f"- `{entry}()`")
                offset = 0
            else:
                lines.append(f"- Einstieg über `{entry}()`")
                lines.append(f"  - `{entry}()`")
                offset = 1
            for row in rows[1:]:
                lines.append(f"{'  ' * (row.depth + offset)}- `{row.function}()`")
    lines.append("")
    return "\n".join(lines)


def write_csv(rows: Iterable[Row], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["source_file", "entrypoint_from_main", "depth", "function", "function_camel_case", "called_by", "path_from_main"])
        for r in rows:
            w.writerow([r.source_file, r.entrypoint_from_main, r.depth, r.function, r.function_camel_case, r.called_by, r.path_from_main])


def main() -> int:
    rows_by_module: dict[str, dict[str, list[Row]]] = {}
    all_rows: list[Row] = []
    for module, entrypoints in MODULES.items():
        defined, calls = analyze_module(ROOT / module)
        rows_by_module[module] = {}
        for entry in entrypoints:
            if entry not in defined:
                continue
            rows = walk_rows(module, entry, calls, defined)
            rows_by_module[module][entry] = rows
            all_rows.extend(rows)
    write_csv(all_rows, ROOT / "docs/call_trees_from_main.csv")
    (ROOT / "docs/call_trees_from_main.md").write_text(make_markdown(rows_by_module), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
