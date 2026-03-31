#!/usr/bin/env python3
from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = ("src", "tools", "tests")
OUTPUT_PATH = ROOT / "docs" / "source_identifier_inventory.md"


@dataclass(frozen=True)
class FunctionRecord:
    file: str
    name: str
    lineno: int
    calls: tuple[str, ...]


@dataclass(frozen=True)
class VariableRecord:
    file: str
    scope: str
    name: str
    lineno: int


class _IdentifierVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.functions: list[FunctionRecord] = []
        self.variables: list[VariableRecord] = []
        self.class_stack: list[str] = []
        self.function_stack: list[str] = []

    def _scope(self) -> str:
        if self.function_stack:
            return f"function:{'.'.join(self.function_stack)}"
        if self.class_stack:
            return f"class:{'.'.join(self.class_stack)}"
        return "module"

    def _collect_target_names(self, node: ast.AST) -> list[str]:
        names: list[str] = []
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                names.extend(self._collect_target_names(elt))
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        return names

    def _record_target_names(self, targets: list[ast.AST] | tuple[ast.AST, ...], lineno: int) -> None:
        for target in targets:
            for name in self._collect_target_names(target):
                self.variables.append(
                    VariableRecord(file=self.rel_path, scope=self._scope(), name=name, lineno=lineno)
                )

    def _called_name(self, call: ast.Call) -> str | None:
        if isinstance(call.func, ast.Name):
            return call.func.id
        if isinstance(call.func, ast.Attribute):
            return call.func.attr
        return None

    def _calls_in_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
        calls: set[str] = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                called = self._called_name(child)
                if called:
                    calls.add(called)
        return tuple(sorted(calls))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_stack.append(node.name)
        for arg in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            self.variables.append(
                VariableRecord(file=self.rel_path, scope=self._scope(), name=arg.arg, lineno=arg.lineno)
            )
        if node.args.vararg is not None:
            self.variables.append(
                VariableRecord(file=self.rel_path, scope=self._scope(), name=node.args.vararg.arg, lineno=node.args.vararg.lineno)
            )
        if node.args.kwarg is not None:
            self.variables.append(
                VariableRecord(file=self.rel_path, scope=self._scope(), name=node.args.kwarg.arg, lineno=node.args.kwarg.lineno)
            )

        self.functions.append(
            FunctionRecord(
                file=self.rel_path,
                name=node.name,
                lineno=node.lineno,
                calls=self._calls_in_function(node),
            )
        )
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self._record_target_names(node.targets, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._record_target_names((node.target,), node.lineno)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._record_target_names((node.target,), node.lineno)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._record_target_names((node.target,), node.lineno)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._record_target_names((node.target,), node.lineno)
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                self._record_target_names((item.optional_vars,), node.lineno)
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                self._record_target_names((item.optional_vars,), node.lineno)
        self.generic_visit(node)



def _iter_source_files() -> list[Path]:
    files: list[Path] = []
    for root_name in SOURCE_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if path.name == "__init__.py":
                continue
            files.append(path)
    return sorted(files)


def _to_rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build_inventory() -> tuple[list[str], list[str], list[FunctionRecord], list[VariableRecord], list[str]]:
    source_files = _iter_source_files()
    folder_paths: set[str] = set()
    folder_names: set[str] = set()
    functions: list[FunctionRecord] = []
    variables: list[VariableRecord] = []
    extraction_hints: list[str] = []

    for source_file in source_files:
        rel = _to_rel(source_file)
        for parent in reversed(source_file.relative_to(ROOT).parents):
            if str(parent) == ".":
                continue
            folder_paths.add(parent.as_posix())
            folder_names.add(parent.name)

        source_text = source_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source_text)
        except SyntaxError:
            extraction_hints.append(f"- ⚠️ {rel}: SyntaxError beim Parsen – Datei manuell prüfen.")
            continue

        visitor = _IdentifierVisitor(rel)
        visitor.visit(tree)
        functions.extend(visitor.functions)
        variables.extend(visitor.variables)

        functions_by_name = {record.name for record in visitor.functions}
        for record in visitor.functions:
            nested_calls = sorted(c for c in record.calls if c in functions_by_name and c != record.name)
            if nested_calls:
                for callee in nested_calls:
                    extraction_hints.append(
                        "- "
                        f"{rel}: Funktion `{record.name}` ruft `{callee}` auf. "
                        f"Auslagerungsvorschlag: `{callee}File.py` in Ordner `{record.name}Fs/`."
                    )

    return (
        sorted(folder_paths),
        sorted(folder_names),
        sorted(functions, key=lambda item: (item.file, item.name, item.lineno)),
        sorted(variables, key=lambda item: (item.file, item.scope, item.name, item.lineno)),
        sorted(set(extraction_hints)),
    )


def render_markdown() -> str:
    folder_paths, folder_names, functions, variables, extraction_hints = build_inventory()

    lines: list[str] = []
    lines.append("# Sourcecode-Inventar")
    lines.append("")
    lines.append("Diese Liste erfasst Ordnerbezeichnungen, Sourcecodedateien, Funktionsbezeichner und Variablenbezeichner.")
    lines.append("")

    lines.append("## Ordnerpfade mit Sourcecodedateien")
    for item in folder_paths:
        lines.append(f"- `{item}`")
    lines.append(f"- **Anzahl:** {len(folder_paths)}")
    lines.append("")

    lines.append("## Eindeutige Ordnernamen")
    for item in folder_names:
        lines.append(f"- `{item}`")
    lines.append(f"- **Anzahl:** {len(folder_names)}")
    lines.append("")

    lines.append("## Sourcecodedateien")
    for source_file in _iter_source_files():
        lines.append(f"- `{_to_rel(source_file)}`")
    lines.append(f"- **Anzahl:** {len(_iter_source_files())}")
    lines.append("")

    lines.append("## Funktionen")
    for record in functions:
        lines.append(
            f"- `{record.name}` – Datei `{record.file}` (Zeile {record.lineno}); Aufrufe: {', '.join(record.calls) if record.calls else '-'}"
        )
    lines.append(f"- **Anzahl:** {len(functions)}")
    lines.append("")

    lines.append("## Variablen")
    for record in variables:
        lines.append(
            f"- `{record.name}` – Scope `{record.scope}`, Datei `{record.file}` (Zeile {record.lineno})"
        )
    lines.append(f"- **Anzahl:** {len(variables)}")
    lines.append("")

    lines.append("## Auslagerungsvorschläge nach Schema `{Funktionsname}File.py`")
    if extraction_hints:
        lines.extend(extraction_hints)
    else:
        lines.append("- Keine direkten Funktionsaufrufe zwischen Top-Level-Funktionen innerhalb derselben Datei gefunden.")

    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_markdown(), encoding="utf-8")
    print(f"Inventar geschrieben: {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
