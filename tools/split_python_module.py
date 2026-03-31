#!/usr/bin/env python3
"""Split a large Python module into <=N-line chunks plus a faithful loader module.

The generated loader reassembles all chunks in memory and executes the combined
source as one compiled unit. This keeps runtime behavior aligned with the
original module while storing the implementation in smaller files.
"""

from __future__ import annotations

import argparse
import ast
import csv
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MAX_LINES = 100


@dataclass(frozen=True)
class CodeBlock:
    start: int
    end: int
    text: str
    function_names: tuple[str, ...]

    @property
    def line_count(self) -> int:
        return self.end - self.start + 1


def _chunk_lines(lines: list[str], max_lines: int) -> list[list[str]]:
    if max_lines < 1:
        raise ValueError("max_lines must be >= 1")
    return [lines[index : index + max_lines] for index in range(0, len(lines), max_lines)]


def _render_loader(chunk_dir_name: str, chunk_files: list[str], original_name: str) -> str:
    chunk_list = "\n".join(f'    "{chunk_file}",' for chunk_file in chunk_files)
    return f'''"""Auto-generated loader for split module chunks.

DO NOT EDIT MANUALLY. Re-run tools/split_python_module.py instead.
"""

from __future__ import annotations

from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_CHUNK_DIR = _BASE_DIR / {chunk_dir_name!r}
_CHUNK_FILES = [
{chunk_list}
]

_source_parts: list[str] = []
for _chunk_file in _CHUNK_FILES:
    _source_parts.append((_CHUNK_DIR / _chunk_file).read_text(encoding="utf-8"))

_COMBINED_SOURCE = "".join(_source_parts)
exec(compile(_COMBINED_SOURCE, {original_name!r}, "exec"), globals(), globals())
'''


def _sanitize_filename_part(text: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in text).strip("_").lower() or "part"


def _name_for_block(source_stem: str, block: CodeBlock, index: int) -> str:
    if not block.function_names:
        return f"{source_stem}.chunk_{index:04d}.py"
    if len(block.function_names) == 1:
        suffix = _sanitize_filename_part(block.function_names[0])
    else:
        suffix = "_to_".join(
            (_sanitize_filename_part(block.function_names[0]), _sanitize_filename_part(block.function_names[-1]))
        )
    return f"{source_stem}.chunk_{index:04d}_{suffix}.py"


def _top_level_blocks(source_text: str) -> list[CodeBlock]:
    tree = ast.parse(source_text)
    source_lines = source_text.splitlines(keepends=True)
    nodes = sorted(tree.body, key=lambda item: item.lineno)

    blocks: list[CodeBlock] = []
    next_expected_line = 1
    for idx, node in enumerate(nodes):
        node_start = node.lineno
        node_end = node.end_lineno or node.lineno

        if node_start > next_expected_line:
            text = "".join(source_lines[next_expected_line - 1 : node_start - 1])
            blocks.append(CodeBlock(start=next_expected_line, end=node_start - 1, text=text, function_names=()))

        function_names: tuple[str, ...] = ()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_names = (node.name,)

        # Keep decorators bound to the relevant node by using lineno/end_lineno slices.
        text = "".join(source_lines[node_start - 1 : node_end])
        blocks.append(CodeBlock(start=node_start, end=node_end, text=text, function_names=function_names))
        next_expected_line = node_end + 1

        # Add trailing content once we processed the final node.
        if idx == len(nodes) - 1 and next_expected_line <= len(source_lines):
            text = "".join(source_lines[next_expected_line - 1 :])
            blocks.append(
                CodeBlock(start=next_expected_line, end=len(source_lines), text=text, function_names=())
            )

    if not nodes and source_lines:
        blocks.append(CodeBlock(start=1, end=len(source_lines), text="".join(source_lines), function_names=()))

    return blocks


def _chunk_blocks(blocks: list[CodeBlock], max_lines: int) -> list[list[CodeBlock]]:
    if max_lines < 1:
        raise ValueError("max_lines must be >= 1")

    chunks: list[list[CodeBlock]] = []
    current: list[CodeBlock] = []
    current_size = 0
    for block in blocks:
        block_size = block.line_count
        if current and current_size + block_size > max_lines:
            chunks.append(current)
            current = [block]
            current_size = block_size
            continue
        current.append(block)
        current_size += block_size
    if current:
        chunks.append(current)
    return chunks


class _CallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
        self.generic_visit(node)


def _collect_call_table(source_text: str) -> list[tuple[str, str]]:
    tree = ast.parse(source_text)
    table: list[tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visitor = _CallVisitor()
            visitor.visit(node)
            for callee in sorted(visitor.calls):
                table.append((node.name, callee))
    return table


def _write_call_table(source_text: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = _collect_call_table(source_text)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("caller", "callee"))
        writer.writerows(rows)


def _write_split_artifacts(
    source_path: Path,
    chunk_dir: Path,
    loader_path: Path,
    max_lines: int,
    strategy: str,
    call_table_path: Path | None,
) -> tuple[int, list[str]]:
    source_text = source_path.read_text(encoding="utf-8")
    source_lines = source_text.splitlines(keepends=True)

    chunk_dir.mkdir(parents=True, exist_ok=True)

    chunk_files: list[str] = []
    if strategy == "functions":
        chunks = _chunk_blocks(_top_level_blocks(source_text), max_lines)
        for idx, chunk in enumerate(chunks, start=1):
            function_names = tuple(name for block in chunk for name in block.function_names)
            merged_block = CodeBlock(
                start=chunk[0].start,
                end=chunk[-1].end,
                text="".join(block.text for block in chunk),
                function_names=function_names,
            )
            chunk_name = _name_for_block(source_path.stem, merged_block, idx)
            (chunk_dir / chunk_name).write_text(merged_block.text, encoding="utf-8")
            chunk_files.append(chunk_name)
    else:
        chunks = _chunk_lines(source_lines, max_lines)
        for idx, chunk in enumerate(chunks, start=1):
            chunk_name = f"{source_path.stem}.chunk_{idx:04d}.py"
            (chunk_dir / chunk_name).write_text("".join(chunk), encoding="utf-8")
            chunk_files.append(chunk_name)

    if call_table_path is not None:
        _write_call_table(source_text=source_text, destination=call_table_path)

    if not chunk_files and source_lines:
        chunk_name = f"{source_path.stem}.chunk_0001.py"
        (chunk_dir / chunk_name).write_text("".join(source_lines), encoding="utf-8")
        chunk_files.append(chunk_name)

    loader_text = _render_loader(chunk_dir.name, chunk_files, source_path.name)
    loader_path.write_text(loader_text, encoding="utf-8")
    return len(chunk_files), chunk_files


def split_python_module(
    source_path: Path,
    output_dir: Path,
    max_lines: int,
    loader_name: str,
    strategy: str,
    call_table_path: Path | None,
) -> tuple[int, Path, Path]:
    loader_path = output_dir / loader_name
    chunk_dir = output_dir / f"{source_path.stem}_chunks"
    chunk_count, _ = _write_split_artifacts(
        source_path=source_path,
        chunk_dir=chunk_dir,
        loader_path=loader_path,
        max_lines=max_lines,
        strategy=strategy,
        call_table_path=call_table_path,
    )
    return chunk_count, loader_path, chunk_dir


def deploy_split_in_place(
    source_path: Path,
    max_lines: int,
    backup_suffix: str,
    strategy: str,
    call_table_path: Path | None,
    chunk_dir_name: str | None = None,
) -> tuple[int, Path, Path]:
    chunk_dir = source_path.parent / (chunk_dir_name or f"{source_path.stem}_chunks")
    loader_path = source_path
    backup_path = source_path.with_name(source_path.name + backup_suffix)

    with tempfile.TemporaryDirectory(prefix="split-module-") as temp_dir:
        temp_root = Path(temp_dir)
        temp_chunk_dir = temp_root / chunk_dir.name
        temp_loader_path = temp_root / source_path.name

        chunk_count, chunk_files = _write_split_artifacts(
            source_path=source_path,
            chunk_dir=temp_chunk_dir,
            loader_path=temp_loader_path,
            max_lines=max_lines,
            strategy=strategy,
            call_table_path=call_table_path,
        )

        if backup_path.exists():
            backup_path.unlink()
        shutil.copy2(source_path, backup_path)

        if chunk_dir.exists():
            shutil.rmtree(chunk_dir)
        shutil.move(str(temp_chunk_dir), str(chunk_dir))
        shutil.move(str(temp_loader_path), str(loader_path))

        # Sanity check: re-concatenated chunks must match the backup byte-for-byte.
        original = backup_path.read_text(encoding="utf-8")
        merged = "".join((chunk_dir / name).read_text(encoding="utf-8") for name in chunk_files)
        if original != merged:
            shutil.copy2(backup_path, source_path)
            raise RuntimeError("In-place deploy failed: chunk merge does not match original source")

    return chunk_count, loader_path, backup_path


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the large Python module")
    parser.add_argument("--output-dir", type=Path, default=Path("split_output"), help="Target directory for non-destructive split output")
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES, help=f"Maximum lines per chunk (default: {DEFAULT_MAX_LINES})")
    parser.add_argument("--loader-name", type=str, default="imageCompositeConverter.py", help="Loader filename for non-destructive output mode")
    parser.add_argument("--deploy-in-place", action="store_true", help="Replace source file with loader and write chunks next to it")
    parser.add_argument("--backup-suffix", type=str, default=".bak", help="Suffix used for in-place backup copies (default: .bak)")
    parser.add_argument("--chunk-dir-name", type=str, default=None, help="Custom chunk directory name for in-place deploy")
    parser.add_argument(
        "--strategy",
        choices=("lines", "functions"),
        default="functions",
        help="Split strategy: 'functions' keeps top-level functions intact, 'lines' uses strict line chunks",
    )
    parser.add_argument(
        "--call-table",
        type=Path,
        default=None,
        help="Optional CSV output containing caller/callee pairs discovered in top-level functions",
    )
    return parser.parseArgs()


def main() -> int:
    args = parseArgs()
    if args.deploy_in_place:
        chunk_count, loader_path, backup_path = deploy_split_in_place(
            source_path=args.source,
            max_lines=args.max_lines,
            backup_suffix=args.backup_suffix,
            strategy=args.strategy,
            call_table_path=args.call_table,
            chunk_dir_name=args.chunk_dir_name,
        )
        print(
            f"Deployed split in place: {args.source} -> loader {loader_path}, "
            f"{chunk_count} chunks, backup at {backup_path}"
        )
        return 0

    chunk_count, loader_path, chunk_dir = split_python_module(
        source_path=args.source,
        output_dir=args.output_dir,
        max_lines=args.max_lines,
        loader_name=args.loader_name,
        strategy=args.strategy,
        call_table_path=args.call_table,
    )
    print(
        f"Split {args.source} into {chunk_count} chunks (<= {args.max_lines} lines), "
        f"loader {loader_path}, chunk dir {chunk_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
