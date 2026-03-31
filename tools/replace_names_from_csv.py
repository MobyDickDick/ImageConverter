from __future__ import annotations

import argparse
import csv
import io
import keyword
import tokenize
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAPPING_CSV = REPO_ROOT / "artifacts" / "descriptions" / "replaceNames.csv"


@dataclass(frozen=True)
class PlannedRename:
    old_path: Path
    new_path: Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benennt Ordner und Dateien anhand einer CSV (old;new) um. "
            "Standardmäßig nur Dry-Run; mit --apply werden Renames ausgeführt."
        )
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_MAPPING_CSV,
        help="Pfad zur CSV mit old;new Basenamen",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Wurzelverzeichnis, in dem umbenannt wird",
    )
    parser.add_argument("--apply", action="store_true", help="Renames wirklich ausführen")
    return parser.parse_args()


def _load_name_map(csv_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        for row_number, row in enumerate(reader, start=1):
            if not row:
                continue
            if len(row) < 2:
                raise ValueError(f"Ungültige CSV-Zeile {row_number}: {row!r}")
            old_name = row[0].strip()
            new_name = row[1].strip()
            if not old_name or not new_name:
                continue
            if old_name in mapping and mapping[old_name] != new_name:
                raise ValueError(
                    "Mehrdeutiger Eintrag in CSV: "
                    f"{old_name!r} -> {mapping[old_name]!r} und {new_name!r}"
                )
            mapping[old_name] = new_name
    return mapping


def _planned_renames(root: Path, mapping: dict[str, str]) -> list[PlannedRename]:
    plans: list[PlannedRename] = []
    for path in sorted(root.rglob("*"), key=lambda current: len(current.as_posix()), reverse=True):
        if any(part == ".git" for part in path.parts):
            continue
        replacement = mapping.get(path.name)
        if not replacement or replacement == path.name:
            continue
        plans.append(PlannedRename(old_path=path, new_path=path.with_name(replacement)))
    return plans


def _validate_plans(plans: list[PlannedRename]) -> None:
    targets: dict[Path, Path] = {}
    for plan in plans:
        old_path = plan.old_path
        new_path = plan.new_path
        if new_path.exists() and new_path != old_path:
            raise FileExistsError(f"Ziel existiert bereits: {new_path}")
        conflict_origin = targets.get(new_path)
        if conflict_origin and conflict_origin != old_path:
            raise FileExistsError(
                f"Konflikt: {conflict_origin} und {old_path} würden beide nach {new_path} umbenannt"
            )
        targets[new_path] = old_path


def _apply_renames(plans: list[PlannedRename], apply: bool) -> None:
    for plan in plans:
        old_path = plan.old_path
        new_path = plan.new_path
        if not old_path.exists():
            continue
        if new_path.exists() and new_path != old_path:
            raise FileExistsError(f"Ziel existiert bereits: {new_path}")
        print(f"{old_path} -> {new_path}")
        if apply:
            old_path.rename(new_path)


def _identifier_rename_map(mapping: dict[str, str]) -> dict[str, str]:
    rename_map: dict[str, str] = {}
    for old_name, new_name in mapping.items():
        old_stem = old_name[:-3] if old_name.endswith(".py") else old_name
        new_stem = new_name[:-3] if new_name.endswith(".py") else new_name
        if not old_stem.isidentifier() or not new_stem.isidentifier():
            continue
        if keyword.iskeyword(old_stem) or keyword.iskeyword(new_stem):
            continue
        if old_stem == new_stem:
            continue
        rename_map[old_stem] = new_stem
    return rename_map


def _rewrite_python_source(source: str, rename_map: dict[str, str]) -> str:
    rebuilt: list[tokenize.TokenInfo] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NAME and token.string in rename_map:
            rebuilt.append(
                tokenize.TokenInfo(
                    type=token.type,
                    string=rename_map[token.string],
                    start=token.start,
                    end=token.end,
                    line=token.line,
                )
            )
            continue
        rebuilt.append(token)
    return tokenize.untokenize(rebuilt)


def _rewrite_python_sources(root: Path, mapping: dict[str, str], apply: bool) -> list[Path]:
    rename_map = _identifier_rename_map(mapping)
    if not rename_map:
        return []
    changed: list[Path] = []
    for path in sorted(root.rglob("*.py")):
        if any(part == ".git" for part in path.parts):
            continue
        source = path.read_text(encoding="utf-8")
        updated = _rewrite_python_source(source, rename_map)
        if source == updated:
            continue
        changed.append(path)
        if apply:
            path.write_text(updated, encoding="utf-8")
    return changed


def main() -> None:
    args = _parse_args()
    csv_path = args.csv if args.csv.is_absolute() else (REPO_ROOT / args.csv)
    root = args.root if args.root.is_absolute() else (REPO_ROOT / args.root)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV nicht gefunden: {csv_path}")
    if not root.exists() or not root.is_dir():
        raise NotADirectoryError(f"Ungültiges Root-Verzeichnis: {root}")

    mapping = _load_name_map(csv_path)
    plans = _planned_renames(root=root, mapping=mapping)
    _validate_plans(plans)
    changed_python_sources = _rewrite_python_sources(root=root, mapping=mapping, apply=args.apply)

    print(f"Mapping-Einträge: {len(mapping)}")
    print(f"Angepasste Python-Quellen: {len(changed_python_sources)}")
    print(f"Geplante Umbenennungen: {len(plans)}")

    if not args.apply:
        print("Dry-Run abgeschlossen. Mit --apply werden Änderungen ausgeführt.")
        return

    _apply_renames(plans, apply=True)
    print("Umbenennung abgeschlossen.")


if __name__ == "__main__":
    main()
