from __future__ import annotations

import argparse
import ast
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


def _iter_docstring_nodes(tree: ast.AST) -> set[ast.Constant]:
    docstring_nodes: set[ast.Constant] = set()
    module_and_defs = [tree]
    module_and_defs.extend(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    )
    for node in module_and_defs:
        body = getattr(node, "body", None)
        if not body:
            continue
        first_stmt = body[0]
        if (
            isinstance(first_stmt, ast.Expr)
            and isinstance(first_stmt.value, ast.Constant)
            and isinstance(first_stmt.value.value, str)
        ):
            docstring_nodes.add(first_stmt.value)
    return docstring_nodes


def _collect_excluded_string_nodes(tree: ast.AST) -> set[ast.Constant]:
    excluded: set[ast.Constant] = set()
    excluded.update(_iter_docstring_nodes(tree))

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            for keyword in node.keywords:
                if keyword.arg not in {"help", "description", "epilog"}:
                    continue
                if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    excluded.add(keyword.value)
    return excluded


def _iter_string_nodes(tree: ast.AST) -> Iterable[ast.Constant]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node


def collect_form_code_hits(source_root: Path) -> list[FormCodeHit]:
    hits: list[FormCodeHit] = []
    for path in sorted(source_root.rglob("*.py")):
        rel = path.as_posix()
        if "/__pycache__/" in rel:
            continue

        source_text = path.read_text(encoding="utf-8")
        source_lines = source_text.splitlines()
        tree = ast.parse(source_text, filename=rel)
        excluded_string_nodes = _collect_excluded_string_nodes(tree)

        for node in _iter_string_nodes(tree):
            if node in excluded_string_nodes:
                continue
            if node.lineno is None or node.col_offset is None:
                continue
            value = node.value
            if not isinstance(value, str):
                continue
            for match in FORM_CODE_PATTERN.finditer(value):
                line_index = node.lineno - 1
                if line_index >= len(source_lines):
                    continue
                hits.append(
                    FormCodeHit(
                        code=match.group(0),
                        file=rel,
                        line=node.lineno,
                        column=node.col_offset + 1 + match.start(),
                        line_text=source_lines[line_index].strip(),
                    )
                )
    return sorted(hits, key=lambda hit: (hit.file, hit.line, hit.column, hit.code))


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
