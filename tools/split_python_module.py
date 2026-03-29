#!/usr/bin/env python3
"""Split a large Python module into <=N-line chunks plus a faithful loader module.

The generated loader reassembles all chunks in memory and executes the combined
source as one compiled unit. This keeps runtime behavior aligned with the
original module while storing the implementation in smaller files.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path


DEFAULT_MAX_LINES = 100


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


def _write_split_artifacts(
    source_path: Path,
    chunk_dir: Path,
    loader_path: Path,
    max_lines: int,
) -> tuple[int, list[str]]:
    source_text = source_path.read_text(encoding="utf-8")
    source_lines = source_text.splitlines(keepends=True)
    chunks = _chunk_lines(source_lines, max_lines)

    chunk_dir.mkdir(parents=True, exist_ok=True)

    chunk_files: list[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        chunk_name = f"{source_path.stem}.chunk_{idx:04d}.py"
        (chunk_dir / chunk_name).write_text("".join(chunk), encoding="utf-8")
        chunk_files.append(chunk_name)

    loader_text = _render_loader(chunk_dir.name, chunk_files, source_path.name)
    loader_path.write_text(loader_text, encoding="utf-8")
    return len(chunks), chunk_files


def split_python_module(source_path: Path, output_dir: Path, max_lines: int, loader_name: str) -> tuple[int, Path, Path]:
    loader_path = output_dir / loader_name
    chunk_dir = output_dir / f"{source_path.stem}_chunks"
    chunk_count, _ = _write_split_artifacts(source_path=source_path, chunk_dir=chunk_dir, loader_path=loader_path, max_lines=max_lines)
    return chunk_count, loader_path, chunk_dir


def deploy_split_in_place(
    source_path: Path,
    max_lines: int,
    backup_suffix: str,
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the large Python module")
    parser.add_argument("--output-dir", type=Path, default=Path("split_output"), help="Target directory for non-destructive split output")
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES, help=f"Maximum lines per chunk (default: {DEFAULT_MAX_LINES})")
    parser.add_argument("--loader-name", type=str, default="image_composite_converter.py", help="Loader filename for non-destructive output mode")
    parser.add_argument("--deploy-in-place", action="store_true", help="Replace source file with loader and write chunks next to it")
    parser.add_argument("--backup-suffix", type=str, default=".bak", help="Suffix used for in-place backup copies (default: .bak)")
    parser.add_argument("--chunk-dir-name", type=str, default=None, help="Custom chunk directory name for in-place deploy")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.deploy_in_place:
        chunk_count, loader_path, backup_path = deploy_split_in_place(
            source_path=args.source,
            max_lines=args.max_lines,
            backup_suffix=args.backup_suffix,
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
    )
    print(
        f"Split {args.source} into {chunk_count} chunks (<= {args.max_lines} lines), "
        f"loader {loader_path}, chunk dir {chunk_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
