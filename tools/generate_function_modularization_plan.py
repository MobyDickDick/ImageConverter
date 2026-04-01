#!/usr/bin/env python3
"""Generate a per-function modularization plan for large Python modules.

The output helps prepare a future split where each function can move into its own file.
It captures:
- module-level imports,
- module-level constants,
- all functions with source ranges,
- direct intra-module call dependencies,
- a suggested target file path per function.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FunctionInfo:
    name: str
    lineno: int
    end_lineno: int
    is_async: bool
    parameters: list[str]
    reads: list[str]
    assigned: list[str]
    calls: list[str]


def _extract_names_from_target(node: ast.AST, sink: set[str]) -> None:
    if isinstance(node, ast.Name):
        sink.add(node.id)
        return
    for child in ast.iter_child_nodes(node):
        _extract_names_from_target(child, sink)


def _parameter_names(args: ast.arguments) -> list[str]:
    names: list[str] = []
    names.extend(arg.arg for arg in args.posonlyargs)
    names.extend(arg.arg for arg in args.args)
    if args.vararg:
        names.append(args.vararg.arg)
    names.extend(arg.arg for arg in args.kwonlyargs)
    if args.kwarg:
        names.append(args.kwarg.arg)
    return names


def _analyze_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
    reads: set[str] = set()
    assigned: set[str] = set(_parameter_names(node.args))
    calls: set[str] = set()

    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            if isinstance(child.ctx, ast.Load):
                reads.add(child.id)
            elif isinstance(child.ctx, (ast.Store, ast.Del)):
                assigned.add(child.id)
        elif isinstance(child, (ast.For, ast.AsyncFor)):
            _extract_names_from_target(child.target, assigned)
        elif isinstance(child, (ast.With, ast.AsyncWith)):
            for item in child.items:
                if item.optional_vars is not None:
                    _extract_names_from_target(item.optional_vars, assigned)
        elif isinstance(child, ast.NamedExpr):
            _extract_names_from_target(child.target, assigned)
        elif isinstance(child, ast.comprehension):
            _extract_names_from_target(child.target, assigned)
        elif isinstance(child, ast.ExceptHandler) and child.name:
            assigned.add(child.name)
        elif isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
            calls.add(child.func.id)

    unresolved_reads = sorted(name for name in reads if name not in assigned and name != node.name)

    end_lineno = getattr(node, "end_lineno", node.lineno)
    return FunctionInfo(
        name=node.name,
        lineno=node.lineno,
        end_lineno=end_lineno,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        parameters=_parameter_names(node.args),
        reads=unresolved_reads,
        assigned=sorted(assigned),
        calls=sorted(calls),
    )


def _module_level_bindings(tree: ast.Module) -> tuple[list[str], list[str]]:
    imports: list[str] = []
    constants: list[str] = []
    for stmt in tree.body:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                imports.append(alias.asname or alias.name)
        elif isinstance(stmt, ast.ImportFrom):
            module = stmt.module or ""
            for alias in stmt.names:
                name = alias.asname or alias.name
                imports.append(f"{module}.{name}" if module else name)
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    constants.append(target.id)
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            constants.append(stmt.target.id)
    return sorted(dict.fromkeys(imports)), sorted(dict.fromkeys(constants))


def build_plan(source_file: Path, output_dir: Path, module_prefix: str) -> dict[str, object]:
    text = source_file.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(source_file))

    imports, constants = _module_level_bindings(tree)

    functions: list[FunctionInfo] = []
    function_names: set[str] = set()
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info = _analyze_function(stmt)
            functions.append(info)
            function_names.add(info.name)

    entries: list[dict[str, object]] = []
    for f in functions:
        internal_calls = [name for name in f.calls if name in function_names and name != f.name]
        internal_reads = [name for name in f.reads if name in function_names and name != f.name]
        external_reads = [name for name in f.reads if name not in function_names]
        target_module = f"{module_prefix}.{f.name}"
        target_file = output_dir / f"{f.name}.py"
        entries.append(
            {
                "name": f.name,
                "source_range": {"start_line": f.lineno, "end_line": f.end_lineno},
                "is_async": f.is_async,
                "parameters": f.parameters,
                "depends_on_functions": sorted(dict.fromkeys(internal_calls + internal_reads)),
                "depends_on_external_names": external_reads,
                "suggested_module": target_module,
                "suggested_file": str(target_file),
            }
        )

    return {
        "source_file": str(source_file),
        "module_imports": imports,
        "module_constants": constants,
        "function_count": len(entries),
        "functions": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the source .py file to analyze")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/reports/function_modularization_plan.json"),
        help="Where to write the generated JSON plan",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("src/extracted_functions"),
        help="Suggested directory for one-function-per-file extraction",
    )
    parser.add_argument(
        "--module-prefix",
        default="src.extracted_functions",
        help="Suggested Python module prefix for generated function files",
    )
    args = parser.parse_args()

    plan = build_plan(args.source, args.output_dir, args.module_prefix)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote plan for {plan['function_count']} function(s): {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
