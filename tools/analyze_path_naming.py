from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_BASE = "C:/work/ImageConverter/"

SKIP_ROOTS = {".git", ".venv", "vendor", "artifacts"}


def _iter_repo_files() -> list[str]:
    results: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.split("/", 1)[0] in SKIP_ROOTS:
            continue
        results.append(rel)
    return results


def longest_paths(windows_base: str, limit: int = 10) -> list[tuple[int, int, str]]:
    base = windows_base.rstrip("/\\")
    rows: list[tuple[int, int, str]] = []
    for rel in _iter_repo_files():
        repo_len = len(rel)
        win_len = len(f"{base}/{rel}")
        rows.append((win_len, repo_len, rel))
    rows.sort(reverse=True)
    return rows[:limit]


def files_notation_folders() -> list[str]:
    rows: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_dir():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if not rel:
            continue
        if rel.split("/", 1)[0] in SKIP_ROOTS:
            continue
        if "Files" in path.name:
            rows.append(rel)
    return sorted(rows)


def files_notation_without_prefix() -> list[str]:
    return [
        rel
        for rel in files_notation_folders()
        if not Path(rel).name.startswith("_")
    ]


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze long repository paths for Windows path limits.")
    parser.add_argument("--windows-base", default=WINDOWS_BASE, help="Base directory prefix to simulate on Windows")
    parser.add_argument("--limit", type=int, default=20, help="How many longest paths to print")
    parser.add_argument("--warning-threshold", type=int, default=260, help="Mark entries at or above this absolute path length")
    return parser.parseArgs()


def main() -> None:
    args = parseArgs()

    print("# Top lange Pfade")
    for win_len, repo_len, rel in longest_paths(args.windows_base, args.limit):
        marker = " !!!" if win_len >= args.warning_threshold else ""
        print(f"{win_len:>3} (repo {repo_len:>3}) {rel}{marker}")

    print("\n# Files-Ordner ohne führenden Unterstrich")
    missing = files_notation_without_prefix()
    for rel in missing:
        print(rel)
    print(f"Anzahl: {len(missing)}")


if __name__ == "__main__":
    main()
