#!/usr/bin/env python3
"""Batch-extract remaining non-delegating top-level functions from a source module.

This tool calls tools/automate_function_extraction.py for each detected function and
writes a JSON+text log with per-function success/failure details.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ExtractionResult:
    function: str
    status: str
    returncode: int
    command: str
    stdout: str
    stderr: str


def _is_direct_same_name_delegate(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if len(node.body) != 1:
        return False
    stmt = node.body[0]
    call_expr: ast.Call | None = None
    if isinstance(stmt, ast.Return):
        call_expr = stmt.value if isinstance(stmt.value, ast.Call) else None
    elif isinstance(stmt, ast.Expr):
        call_expr = stmt.value if isinstance(stmt.value, ast.Call) else None
    if call_expr is None:
        return False
    if not isinstance(call_expr.func, ast.Attribute):
        return False
    return call_expr.func.attr == node.name


def _top_level_remaining_functions(source_text: str, *, exclude: set[str]) -> list[str]:
    tree = ast.parse(source_text)
    remaining: list[str] = []
    for stmt in tree.body:
        if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if stmt.name in exclude:
            continue
        if _is_direct_same_name_delegate(stmt):
            continue
        remaining.append(stmt.name)
    return remaining


def _write_json_log(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text_log(path: Path, payload: dict[str, object], results: list[ExtractionResult]) -> None:
    lines: list[str] = []
    lines.append(f"timestamp_utc: {payload['timestamp_utc']}")
    lines.append(f"source: {payload['source']}")
    lines.append(f"target_module: {payload['target_module']}")
    lines.append(f"verify_cmds: {payload['verify_cmds']}")
    lines.append(f"planned_functions: {payload['planned_functions_count']}")
    lines.append(f"successful: {payload['successful']}")
    lines.append(f"failed: {payload['failed']}")
    lines.append("")
    for result in results:
        lines.append(f"[{result.status}] {result.function}")
        lines.append(f"  command: {result.command}")
        lines.append(f"  returncode: {result.returncode}")
        if result.stdout.strip():
            lines.append("  stdout:")
            lines.extend(f"    {line}" for line in result.stdout.rstrip().splitlines())
        if result.stderr.strip():
            lines.append("  stderr:")
            lines.extend(f"    {line}" for line in result.stderr.rstrip().splitlines())
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target-module", type=Path, required=True)
    parser.add_argument("--exclude", action="append", default=["main"])
    parser.add_argument("--verify-cmd", action="append", default=[])
    parser.add_argument("--import-line")
    parser.add_argument("--module-alias")
    parser.add_argument("--log-json", type=Path, required=True)
    parser.add_argument("--log-text", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, default=Path.cwd())
    parser.add_argument("--stop-on-failure", action="store_true")
    args = parser.parse_args()

    source_text = args.source.read_text(encoding="utf-8")
    remaining_functions = _top_level_remaining_functions(source_text, exclude=set(args.exclude))

    tool_path = Path(__file__).with_name("automate_function_extraction.py")
    results: list[ExtractionResult] = []

    for function_name in remaining_functions:
        cmd: list[str] = [
            sys.executable,
            str(tool_path),
            "--source",
            str(args.source),
            "--function",
            function_name,
            "--target-module",
            str(args.target_module),
        ]
        if args.import_line:
            cmd.extend(["--import-line", args.import_line])
        if args.module_alias:
            cmd.extend(["--module-alias", args.module_alias])
        for verify in args.verify_cmd:
            cmd.extend(["--verify-cmd", verify])

        proc = subprocess.run(
            cmd,
            cwd=str(args.workdir),
            text=True,
            capture_output=True,
            check=False,
        )
        status = "success" if proc.returncode == 0 else "failed"
        results.append(
            ExtractionResult(
                function=function_name,
                status=status,
                returncode=proc.returncode,
                command=" ".join(cmd),
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        )
        if proc.returncode != 0 and args.stop_on_failure:
            break

    successful = sum(1 for r in results if r.status == "success")
    failed = sum(1 for r in results if r.status == "failed")
    payload: dict[str, object] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(args.source),
        "target_module": str(args.target_module),
        "verify_cmds": args.verify_cmd,
        "planned_functions_count": len(remaining_functions),
        "processed_functions_count": len(results),
        "successful": successful,
        "failed": failed,
        "results": [asdict(r) for r in results],
    }

    _write_json_log(args.log_json, payload)
    _write_text_log(args.log_text, payload, results)

    print(f"Processed {len(results)}/{len(remaining_functions)} functions. Success={successful}, failed={failed}")
    print(f"JSON log: {args.log_json}")
    print(f"Text log: {args.log_text}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
