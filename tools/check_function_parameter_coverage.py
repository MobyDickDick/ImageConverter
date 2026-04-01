#!/usr/bin/env python3
"""Check whether names used inside functions are covered by function parameters.

The script parses Python files with ``ast`` and reports, per function, names that are
loaded but are not:
- function parameters,
- locally assigned names,
- explicitly declared global/nonlocal names,
- imported module names,
- Python builtins.

This is a heuristic static analysis and may report false positives for dynamic code.
"""

from __future__ import annotations

import argparse
import ast
import builtins
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

BUILTIN_NAMES = set(dir(builtins))


@dataclass
class FunctionReport:
    file: Path
    function: str
    lineno: int
    parameters: set[str]
    unresolved_names: set[str]


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self, file: Path) -> None:
        self.file = file
        self.reports: list[FunctionReport] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        parameters = self._collect_parameters(node.args)
        assigned = set(parameters)
        imported: set[str] = set()
        global_names: set[str] = set()
        nonlocal_names: set[str] = set()
        used: set[str] = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if isinstance(child.ctx, ast.Load):
                    used.add(child.id)
                elif isinstance(child.ctx, (ast.Store, ast.Del)):
                    assigned.add(child.id)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                for alias in child.names:
                    imported.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(child, ast.Global):
                global_names.update(child.names)
            elif isinstance(child, ast.Nonlocal):
                nonlocal_names.update(child.names)
            elif isinstance(child, (ast.ExceptHandler,)) and child.name:
                assigned.add(child.name)
            elif isinstance(child, ast.comprehension):
                self._collect_target_names(child.target, assigned)
            elif isinstance(child, (ast.For, ast.AsyncFor, ast.With, ast.AsyncWith)):
                if hasattr(child, "target"):
                    self._collect_target_names(child.target, assigned)
                if hasattr(child, "items"):
                    for item in child.items:
                        if item.optional_vars:
                            self._collect_target_names(item.optional_vars, assigned)
            elif isinstance(child, ast.NamedExpr):
                self._collect_target_names(child.target, assigned)
            elif isinstance(child, ast.MatchAs) and child.name:
                assigned.add(child.name)

        allowed = assigned | imported | global_names | nonlocal_names | BUILTIN_NAMES
        unresolved = {name for name in used if name not in allowed and name != node.name}

        self.reports.append(
            FunctionReport(
                file=self.file,
                function=node.name,
                lineno=node.lineno,
                parameters=parameters,
                unresolved_names=unresolved,
            )
        )

    @staticmethod
    def _collect_parameters(args: ast.arguments) -> set[str]:
        parameters: set[str] = set()
        for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
            parameters.add(arg.arg)
        if args.vararg:
            parameters.add(args.vararg.arg)
        if args.kwarg:
            parameters.add(args.kwarg.arg)
        return parameters

    @staticmethod
    def _collect_target_names(target: ast.AST, sink: set[str]) -> None:
        if isinstance(target, ast.Name):
            sink.add(target.id)
            return

        for child in ast.iter_child_nodes(target):
            FunctionAnalyzer._collect_target_names(child, sink)


def iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*.py")):
                if "/vendor/" in f"/{child.as_posix()}/":
                    continue
                yield child


def analyze_paths(paths: Iterable[Path]) -> list[FunctionReport]:
    reports: list[FunctionReport] = []
    for file in iter_python_files(paths):
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
        except SyntaxError:
            continue

        analyzer = FunctionAnalyzer(file)
        analyzer.visit(tree)
        reports.extend(analyzer.reports)

    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("src"), Path("tools")],
        help="Files/directories to scan (defaults to src and tools)",
    )
    args = parser.parse_args()

    reports = analyze_paths(args.paths)

    problematic = [report for report in reports if report.unresolved_names]
    for report in problematic:
        unresolved = ", ".join(sorted(report.unresolved_names))
        print(f"{report.file}:{report.lineno} {report.function} -> {unresolved}")

    print(
        f"\nScanned {len(reports)} function(s). "
        f"Potential issues in {len(problematic)} function(s)."
    )

    return 1 if problematic else 0


if __name__ == "__main__":
    raise SystemExit(main())
