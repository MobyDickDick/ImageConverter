from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import replace_names_from_csv as rename_tool


@dataclass(frozen=True)
class HardConflict:
    old_path: Path
    new_path: Path
    old_hash: str
    new_hash: str
    csv_rows: list[int]


def _path_fingerprint(path: Path) -> str:
    if path.is_dir():
        items = sorted(str(item.relative_to(path)) for item in path.rglob("*"))
        digest = hashlib.sha256("\n".join(items).encode("utf-8"))
        return f"DIR:{digest.hexdigest()}"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"FILE:{digest.hexdigest()}"


def _csv_row_lookup(csv_path: Path) -> dict[str, list[int]]:
    rows_by_old_name: dict[str, list[int]] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        for row_number, row in enumerate(reader, start=1):
            if len(row) < 2:
                continue
            old_name = row[0].strip()
            if not old_name:
                continue
            rows_by_old_name.setdefault(old_name, []).append(row_number)
    return rows_by_old_name


def _hard_conflicts(plans: list[rename_tool.PlannedRename], row_lookup: dict[str, list[int]]) -> list[HardConflict]:
    old_paths = {plan.old_path for plan in plans}
    conflicts: list[HardConflict] = []
    for plan in plans:
        if not plan.new_path.exists() or plan.new_path in old_paths or plan.new_path == plan.old_path:
            continue
        conflicts.append(
            HardConflict(
                old_path=plan.old_path,
                new_path=plan.new_path,
                old_hash=_path_fingerprint(plan.old_path),
                new_hash=_path_fingerprint(plan.new_path),
                csv_rows=row_lookup.get(plan.old_path.name, []),
            )
        )
    return conflicts


def _write_safe_csv(csv_path: Path, output_csv: Path, conflicts: list[HardConflict]) -> None:
    blocked_old_names = {conflict.old_path.name for conflict in conflicts}
    with csv_path.open("r", encoding="utf-8", newline="") as source_handle, output_csv.open(
        "w", encoding="utf-8", newline=""
    ) as target_handle:
        reader = csv.reader(source_handle, delimiter=";")
        writer = csv.writer(target_handle, delimiter=";")
        for row in reader:
            old_name = row[0].strip() if row else ""
            if old_name in blocked_old_names:
                continue
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Analysiert harte Umbenennungs-Konflikte aus der konfigurierten replaceNames-CSV "
            "(z. B. replaceNames.save.csv/replaceNames.safe.csv) und erzeugt optional eine "
            "bereinigte CSV ohne konfliktträchtige old->new-Einträge."
        )
    )
    parser.add_argument("--csv", type=Path, default=rename_tool.DEFAULT_MAPPING_CSV)
    parser.add_argument("--root", type=Path, default=rename_tool.REPO_ROOT)
    parser.add_argument("--write-safe-csv", type=Path, default=None)
    args = parser.parse_args()

    csv_path = args.csv if args.csv.is_absolute() else rename_tool.REPO_ROOT / args.csv
    root = args.root if args.root.is_absolute() else rename_tool.REPO_ROOT / args.root

    mapping = rename_tool._load_name_map(csv_path)
    plans = rename_tool._planned_renames(root=root, mapping=mapping)
    row_lookup = _csv_row_lookup(csv_path)
    conflicts = _hard_conflicts(plans=plans, row_lookup=row_lookup)

    print(f"Planned renames: {len(plans)}")
    print(f"Hard conflicts: {len(conflicts)}")

    for conflict in conflicts:
        relation = "identical" if conflict.old_hash == conflict.new_hash else "DIFFERENT"
        rel_old = conflict.old_path.relative_to(root)
        rel_new = conflict.new_path.relative_to(root)
        row_hint = ", ".join(str(item) for item in conflict.csv_rows) if conflict.csv_rows else "n/a"
        print(f"- {rel_old} -> {rel_new} | csv rows: {row_hint} | content: {relation}")

    if args.write_safe_csv:
        output_csv = args.write_safe_csv if args.write_safe_csv.is_absolute() else rename_tool.REPO_ROOT / args.write_safe_csv
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        _write_safe_csv(csv_path=csv_path, output_csv=output_csv, conflicts=conflicts)
        print(f"Wrote safe CSV: {output_csv}")


if __name__ == "__main__":
    main()
