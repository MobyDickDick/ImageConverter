from __future__ import annotations

import argparse
import io
import keyword
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIST_PATH = REPO_ROOT / "src" / "fileNames.txt"


@dataclass(frozen=True)
class PlannedRename:
    old_path: Path
    new_path: Path


def _camel_to_snake(name: str) -> str:
    stem, suffix = (name[:-3], ".py") if name.endswith(".py") else (name, "")
    converted = re.sub(r"(?<!^)(?=[A-Z])", "_", stem).replace("-", "_").lower()
    converted = re.sub(r"_+", "_", converted).strip("_")
    if stem.startswith("_"):
        converted = "_" + converted
    return converted + suffix


def _read_list_file(list_path: Path) -> list[Path]:
    rows: list[Path] = []
    for raw_line in list_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(Path(line))
    return rows


def _find_target_paths(repo_root: Path, list_entries: list[Path]) -> list[Path]:
    resolved: list[Path] = []
    for rel in list_entries:
        path = repo_root / "src" / rel
        if not path.exists():
            raise FileNotFoundError(f"Eintrag nicht gefunden: src/{rel.as_posix()}")
        resolved.append(path)
    return resolved


def _collect_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
    # unique + stable
    return sorted(set(files))


def _function_rename_map(py_files: list[Path]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for py_file in py_files:
        source = py_file.read_text(encoding="utf-8")
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.NAME and token.string in {"def", "async"}:
                continue
        tree_like = re.finditer(r"^\s*(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", source, re.MULTILINE)
        for match in tree_like:
            old_name = match.group(1)
            if keyword.iskeyword(old_name):
                continue
            new_name = _camel_to_snake(old_name)
            if old_name != new_name:
                mapping[old_name] = new_name
    return mapping


def _planned_path_renames(targets: list[Path]) -> list[PlannedRename]:
    plans: list[PlannedRename] = []
    for old_path in targets:
        new_name = _camel_to_snake(old_path.name)
        if new_name == old_path.name:
            continue
        plans.append(PlannedRename(old_path=old_path, new_path=old_path.with_name(new_name)))
    # deeper paths first to avoid invalidating parents too early
    plans.sort(key=lambda p: len(p.old_path.as_posix()), reverse=True)
    return plans


def _rename_identifiers_in_source(source: str, rename_map: dict[str, str]) -> str:
    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    rebuilt: list[tokenize.TokenInfo] = []
    for tok in tokens:
        if tok.type == tokenize.NAME and tok.string in rename_map:
            rebuilt.append(tokenize.TokenInfo(tok.type, rename_map[tok.string], tok.start, tok.end, tok.line))
        else:
            rebuilt.append(tok)
    return tokenize.untokenize(rebuilt)


def _module_stem_rename_map(path_plans: list[PlannedRename]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for plan in path_plans:
        if plan.old_path.suffix != ".py":
            continue
        mapping[plan.old_path.stem] = plan.new_path.stem
    return mapping


def _rewrite_python_sources(py_files: list[Path], function_map: dict[str, str], module_map: dict[str, str], apply: bool) -> list[Path]:
    changed: list[Path] = []
    rename_map = {**module_map, **function_map}
    for py_file in py_files:
        source = py_file.read_text(encoding="utf-8")
        updated = _rename_identifiers_in_source(source, rename_map)
        if source != updated:
            changed.append(py_file)
            if apply:
                py_file.write_text(updated, encoding="utf-8")
    return changed


def _apply_path_renames(plans: list[PlannedRename], apply: bool) -> None:
    for plan in plans:
        if plan.new_path.exists():
            raise FileExistsError(f"Ziel existiert bereits: {plan.new_path}")
        print(f"PATH: {plan.old_path.relative_to(REPO_ROOT)} -> {plan.new_path.relative_to(REPO_ROOT)}")
        if apply:
            plan.old_path.rename(plan.new_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benennt Ordner/Dateien/Funktionen in polnische Notation (snake_case) um "
            "und passt Python-Referenzen an."
        )
    )
    parser.add_argument("--list", type=Path, default=DEFAULT_LIST_PATH, help="Pfad zur Liste der Zielordner/-dateien")
    parser.add_argument("--apply", action="store_true", help="Änderungen wirklich schreiben/umbenennen")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    list_path = args.list if args.list.is_absolute() else REPO_ROOT / args.list
    if not list_path.exists():
        raise FileNotFoundError(
            f"Datei nicht gefunden: {list_path}. Bitte src/fileNames.txt mit Zielpfaden anlegen."
        )

    list_entries = _read_list_file(list_path)
    targets = _find_target_paths(REPO_ROOT, list_entries)
    py_files = _collect_python_files(targets)

    path_plans = _planned_path_renames(targets)
    module_rename_map = _module_stem_rename_map(path_plans)
    function_rename_map = _function_rename_map(py_files)

    changed_sources = _rewrite_python_sources(
        py_files=py_files,
        function_map=function_rename_map,
        module_map=module_rename_map,
        apply=args.apply,
    )

    print(f"Quell-Dateien mit Identifier-Änderungen: {len(changed_sources)}")
    print(f"Geplante Pfad-Umbenennungen: {len(path_plans)}")

    if not args.apply:
        print("Dry-Run fertig. Mit --apply werden Änderungen ausgeführt.")
        return

    _apply_path_renames(path_plans, apply=True)
    print("Fertig: Umbenennung + Referenzanpassung abgeschlossen.")


if __name__ == "__main__":
    main()
