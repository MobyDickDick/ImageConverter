#!/usr/bin/env python3
"""Automate safe function extraction from a monolith to a helper module.

Workflow:
1. Copy a selected top-level function into a target helper module.
2. Replace only the function body in the source with a delegating wrapper.
3. Run one or multiple verification commands.
4. If a verification command fails, restore all modified files.

This keeps the migration incremental and test-backed, so many small extractions
can be done with one repeatable command.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FunctionLocation:
    node: ast.FunctionDef | ast.AsyncFunctionDef
    start: int
    end: int
    body_start: int


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _find_top_level_function(source_text: str, function_name: str) -> FunctionLocation:
    tree = ast.parse(source_text)
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == function_name:
            if not stmt.body:
                raise ValueError(f"Function {function_name!r} has no body")
            return FunctionLocation(
                node=stmt,
                start=stmt.lineno,
                end=getattr(stmt, "end_lineno", stmt.lineno),
                body_start=stmt.body[0].lineno,
            )
    raise ValueError(f"Top-level function {function_name!r} not found")


def _call_arguments(args: ast.arguments) -> list[str]:
    forwarded: list[str] = []
    for arg in args.posonlyargs:
        forwarded.append(arg.arg)
    for arg in args.args:
        forwarded.append(arg.arg)
    if args.vararg:
        forwarded.append(f"*{args.vararg.arg}")
    for arg in args.kwonlyargs:
        forwarded.append(f"{arg.arg}={arg.arg}")
    if args.kwarg:
        forwarded.append(f"**{args.kwarg.arg}")
    return forwarded


def _detect_indent(lines: list[str], line_no: int) -> str:
    raw = lines[line_no - 1]
    return raw[: len(raw) - len(raw.lstrip())]


def _append_or_replace_function(module_text: str, function_text: str, function_name: str) -> str:
    if not module_text.strip():
        module_text = "from __future__ import annotations\n\n"

    try:
        module_tree = ast.parse(module_text)
    except SyntaxError as exc:
        raise ValueError(f"Target module is not valid Python: {exc}") from exc

    lines = module_text.splitlines()
    replacement_start = None
    replacement_end = None
    for stmt in module_tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == function_name:
            replacement_start = stmt.lineno
            replacement_end = getattr(stmt, "end_lineno", stmt.lineno)
            break

    function_block = function_text.rstrip() + "\n"
    if replacement_start is None or replacement_end is None:
        if module_text and not module_text.endswith("\n"):
            module_text += "\n"
        if not module_text.endswith("\n\n"):
            module_text += "\n"
        return module_text + function_block

    new_lines = lines[: replacement_start - 1] + function_block.splitlines() + lines[replacement_end:]
    return "\n".join(new_lines).rstrip() + "\n"


def _ensure_import(source_text: str, import_line: str) -> str:
    if import_line in source_text:
        return source_text

    lines = source_text.splitlines()
    insert_at = 0
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        tree = None

    if tree is not None:
        body = list(tree.body)
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
            if isinstance(body[0].value.value, str):
                insert_at = getattr(body[0], "end_lineno", body[0].lineno)
                body = body[1:]

        for stmt in body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                insert_at = getattr(stmt, "end_lineno", stmt.lineno)
                continue
            break
    else:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_at = i + 1
            elif insert_at and stripped and not stripped.startswith("#"):
                break

    lines.insert(insert_at, import_line)
    return "\n".join(lines) + "\n"


def _replace_function_body(
    source_text: str,
    location: FunctionLocation,
    module_alias: str,
) -> str:
    lines = source_text.splitlines()
    node = location.node
    call_args = ", ".join(_call_arguments(node.args))
    signature_call = f"{module_alias}.{node.name}({call_args})"

    body_indent = _detect_indent(lines, location.body_start)
    body_line = f"{body_indent}return {signature_call}" if not isinstance(node, ast.AsyncFunctionDef) else f"{body_indent}return await {signature_call}"

    new_lines = lines[: location.body_start - 1] + [body_line] + lines[location.end:]
    return "\n".join(new_lines).rstrip() + "\n"


def _run_checks(commands: list[str], workdir: Path) -> tuple[bool, str]:
    outputs: list[str] = []
    for command in commands:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(workdir),
            text=True,
            capture_output=True,
            check=False,
        )
        outputs.append(f"$ {command}\n{proc.stdout}{proc.stderr}")
        if proc.returncode != 0:
            return False, "\n".join(outputs)
    return True, "\n".join(outputs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Monolith source file path")
    parser.add_argument("--function", required=True, help="Top-level function name to extract")
    parser.add_argument("--target-module", type=Path, required=True, help="Destination helper module path")
    parser.add_argument(
        "--import-line",
        help="Import line inserted into source (defaults to src.iCCModules style)",
    )
    parser.add_argument(
        "--module-alias",
        help="Alias used in wrapper call (default derived from import line)",
    )
    parser.add_argument(
        "--verify-cmd",
        action="append",
        default=[],
        help="Verification command to run after extraction (repeatable)",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path.cwd(),
        help="Working directory for verification commands",
    )
    args = parser.parse_args()

    source_path = args.source
    target_module = args.target_module
    function_name = args.function

    source_original = _read_text(source_path)
    target_original = _read_text(target_module)

    location = _find_top_level_function(source_original, function_name)
    source_lines = source_original.splitlines()
    function_text = "\n".join(source_lines[location.start - 1 : location.end]) + "\n"

    default_stem = target_module.stem
    import_line = args.import_line or f"from src.iCCModules import {default_stem} as {default_stem}_helpers"
    module_alias = args.module_alias or import_line.split(" as ")[-1].strip()

    new_target = _append_or_replace_function(target_original, function_text, function_name)
    new_source = _replace_function_body(source_original, location, module_alias)
    new_source = _ensure_import(new_source, import_line)

    _write_text(target_module, new_target)
    _write_text(source_path, new_source)

    ok, check_output = _run_checks(args.verify_cmd, args.workdir) if args.verify_cmd else (True, "")
    if not ok:
        _write_text(source_path, source_original)
        _write_text(target_module, target_original)
        print("Extraction rolled back because verification failed.")
        print(check_output)
        return 1

    print(f"Extracted function {function_name} -> {target_module}")
    if args.verify_cmd:
        print(check_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
