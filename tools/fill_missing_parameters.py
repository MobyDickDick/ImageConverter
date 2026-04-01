#!/usr/bin/env python3
"""Apply missing-parameter fixes to function signatures and call sites.

The tool consumes a JSON fix specification (typically produced from a prior analysis)
and updates Python source files in place.

Spec schema:
{
  "files": [
    {
      "path": "src/example.py",
      "functions": [
        {
          "name": "target_function",
          "add_params": [
            {"name": "foo", "default": "None"},
            {"name": "bar", "default": "0"}
          ]
        }
      ],
      "calls": [
        {
          "callee": "target_function",
          "caller": "optional_caller_scope",
          "add_keywords": [
            {"name": "foo", "value": "foo"},
            {"name": "bar", "value": "bar"}
          ]
        }
      ]
    }
  ]
}

Notes:
- "caller" is optional; when set, only call nodes inside that function are updated.
- Existing parameters/keywords are not duplicated.
- Rewrites are AST-position based and preserve surrounding code whenever possible.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParamSpec:
    name: str
    default: str = "None"


@dataclass(frozen=True)
class FunctionFix:
    name: str
    add_params: tuple[ParamSpec, ...]


@dataclass(frozen=True)
class KeywordSpec:
    name: str
    value: str


@dataclass(frozen=True)
class CallFix:
    callee: str
    caller: str | None
    add_keywords: tuple[KeywordSpec, ...]


@dataclass(frozen=True)
class FileFix:
    path: Path
    functions: tuple[FunctionFix, ...]
    calls: tuple[CallFix, ...]


def _line_offsets(text: str) -> list[int]:
    offs = [0]
    running = 0
    for line in text.splitlines(keepends=True):
        running += len(line)
        offs.append(running)
    return offs


def _abs_index(line_offsets: list[int], lineno: int, col: int) -> int:
    return line_offsets[lineno - 1] + col


def _find_matching_paren(src: str, open_idx: int) -> int:
    depth = 0
    in_string: str | None = None
    escaped = False
    for i in range(open_idx, len(src)):
        ch = src[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
            continue

        if ch in ('"', "'"):
            in_string = ch
            continue
        if ch == "#":
            while i < len(src) and src[i] != "\n":
                i += 1
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("Could not find matching ')' in function signature")


def _function_args_close_index(src: str, node: ast.FunctionDef | ast.AsyncFunctionDef, line_offsets: list[int]) -> int:
    def_start = _abs_index(line_offsets, node.lineno, node.col_offset)
    name_anchor = f"{node.name}("
    anchor = src.find(name_anchor, def_start)
    if anchor < 0:
        raise ValueError(f"Could not locate function signature for {node.name}")
    open_idx = anchor + len(node.name)
    return _find_matching_paren(src, open_idx)


def _parse_spec(path: Path) -> list[FileFix]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    files: list[FileFix] = []
    for file_raw in raw.get("files", []):
        functions = tuple(
            FunctionFix(
                name=f["name"],
                add_params=tuple(
                    ParamSpec(name=p["name"], default=p.get("default", "None"))
                    for p in f.get("add_params", [])
                ),
            )
            for f in file_raw.get("functions", [])
        )
        calls = tuple(
            CallFix(
                callee=c["callee"],
                caller=c.get("caller"),
                add_keywords=tuple(
                    KeywordSpec(name=k["name"], value=k["value"])
                    for k in c.get("add_keywords", [])
                ),
            )
            for c in file_raw.get("calls", [])
        )
        files.append(FileFix(path=Path(file_raw["path"]), functions=functions, calls=calls))
    return files


def _function_replacements(tree: ast.AST, src: str, line_offsets: list[int], fixes: tuple[FunctionFix, ...]) -> list[tuple[int, int, str]]:
    if not fixes:
        return []
    by_name = {f.name: f for f in fixes}
    reps: list[tuple[int, int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        fix = by_name.get(node.name)
        if not fix:
            continue
        args = node.args
        all_param_names = {a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]}
        if args.vararg:
            all_param_names.add(args.vararg.arg)
        if args.kwarg:
            all_param_names.add(args.kwarg.arg)

        to_add = [p for p in fix.add_params if p.name not in all_param_names]
        if not to_add:
            continue

        insert_at = _function_args_close_index(src, node, line_offsets)
        open_idx = src.rfind("(", _abs_index(line_offsets, node.lineno, node.col_offset), insert_at + 1)
        insert = ""
        if open_idx >= 0 and src[open_idx + 1:insert_at].strip():
            insert += ", "
        insert += ", ".join(f"{p.name}={p.default}" for p in to_add)
        reps.append((insert_at, insert_at, insert))

    return reps


def _call_replacements(tree: ast.AST, src: str, line_offsets: list[int], fixes: tuple[CallFix, ...]) -> list[tuple[int, int, str]]:
    if not fixes:
        return []
    reps: list[tuple[int, int, str]] = []

    func_stack: list[str] = []

    class V(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            func_stack.append(node.name)
            self.generic_visit(node)
            func_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            func_stack.append(node.name)
            self.generic_visit(node)
            func_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            callee_name = node.func.id if isinstance(node.func, ast.Name) else None
            if callee_name is None:
                self.generic_visit(node)
                return
            caller_name = func_stack[-1] if func_stack else None

            for fix in fixes:
                if fix.callee != callee_name:
                    continue
                if fix.caller and fix.caller != caller_name:
                    continue

                existing = {kw.arg for kw in node.keywords if kw.arg is not None}
                pending = [kw for kw in fix.add_keywords if kw.name not in existing]
                if not pending:
                    continue

                insert_at = _abs_index(line_offsets, node.end_lineno, node.end_col_offset) - 1
                has_any_args = bool(node.args or node.keywords)
                insert = (", " if has_any_args else "") + ", ".join(
                    f"{kw.name}={kw.value}" for kw in pending
                )
                reps.append((insert_at, insert_at, insert))
            self.generic_visit(node)

    V().visit(tree)
    return reps


def _apply_replacements(src: str, replacements: list[tuple[int, int, str]]) -> str:
    if not replacements:
        return src
    out = src
    for start, end, repl in sorted(replacements, key=lambda x: (x[0], x[1]), reverse=True):
        out = out[:start] + repl + out[end:]
    return out


def apply_fix(file_fix: FileFix, root: Path) -> bool:
    path = (root / file_fix.path).resolve()
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    line_offsets = _line_offsets(src)

    replacements: list[tuple[int, int, str]] = []
    replacements.extend(_function_replacements(tree, src, line_offsets, file_fix.functions))
    replacements.extend(_call_replacements(tree, src, line_offsets, file_fix.calls))

    updated = _apply_replacements(src, replacements)
    if updated == src:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to JSON fix specification")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    args = parser.parse_args()

    file_fixes = _parse_spec(args.spec)
    changed = 0
    for file_fix in file_fixes:
        if apply_fix(file_fix, args.root):
            changed += 1
            print(f"updated: {file_fix.path}")
        else:
            print(f"unchanged: {file_fix.path}")

    print(f"files_changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
