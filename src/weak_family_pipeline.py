"""Automate weak-family targeting runs and before/after comparisons.

This helper selects the top-N weakest variants from a ranking CSV, stores the
selection, optionally runs a converter command, and writes a before/after
comparison report.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RankingRow:
    image: str
    mean_delta2: float
    std_delta2: float

    @property
    def variant(self) -> str:
        return Path(self.image).stem.upper()


def load_ranking(path: Path) -> list[RankingRow]:
    rows: list[RankingRow] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            try:
                mean_delta2 = float(row.get("mean_delta2", ""))
            except (TypeError, ValueError):
                continue
            try:
                std_delta2 = float(row.get("std_delta2", "") or 0.0)
            except (TypeError, ValueError):
                std_delta2 = 0.0
            image = str(row.get("image", "")).strip()
            if not image:
                continue
            rows.append(RankingRow(image=image, mean_delta2=mean_delta2, std_delta2=std_delta2))
    return sorted(rows, key=lambda item: item.mean_delta2, reverse=True)


def select_top_variants(rows: list[RankingRow], *, top_n: int, prefix: str) -> list[RankingRow]:
    normalized_prefix = prefix.strip().upper()
    selected: list[RankingRow] = []
    for row in rows:
        if normalized_prefix and not row.variant.startswith(normalized_prefix):
            continue
        selected.append(row)
        if len(selected) >= max(1, top_n):
            break
    return selected


def write_selection(rows: list[RankingRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(row.variant for row in rows) + "\n", encoding="utf-8")


def write_comparison(before_rows: list[RankingRow], after_rows: list[RankingRow], selected: list[RankingRow], out_path: Path) -> None:
    after_map = {row.variant: row for row in after_rows}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            delimiter=";",
            fieldnames=["variant", "before_mean_delta2", "after_mean_delta2", "delta", "improved", "before_std_delta2", "after_std_delta2"],
        )
        writer.writeheader()
        for before in selected:
            after = after_map.get(before.variant)
            after_mean = after.mean_delta2 if after is not None else ""
            after_std = after.std_delta2 if after is not None else ""
            delta = ""
            improved = ""
            if after is not None:
                diff = after.mean_delta2 - before.mean_delta2
                delta = f"{diff:.6f}"
                improved = "1" if diff < 0 else "0"
            writer.writerow(
                {
                    "variant": before.variant,
                    "before_mean_delta2": f"{before.mean_delta2:.6f}",
                    "after_mean_delta2": f"{after_mean:.6f}" if isinstance(after_mean, float) else "",
                    "delta": delta,
                    "improved": improved,
                    "before_std_delta2": f"{before.std_delta2:.6f}",
                    "after_std_delta2": f"{after_std:.6f}" if isinstance(after_std, float) else "",
                }
            )


def run() -> int:
    parser = argparse.ArgumentParser(description="Weak-family automation helper")
    parser.add_argument("--before-ranking", type=Path, required=True)
    parser.add_argument("--after-ranking", type=Path, default=None)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--prefix", type=str, default="AC08")
    parser.add_argument("--selection-out", type=Path, required=True)
    parser.add_argument("--comparison-out", type=Path, default=None)
    parser.add_argument("--run-command", type=str, default="")
    args = parser.parse_args()

    before_rows = load_ranking(args.before_ranking)
    selected = select_top_variants(before_rows, top_n=args.top_n, prefix=args.prefix)
    if not selected:
        print("No matching variants found for selection.")
        return 1
    write_selection(selected, args.selection_out)
    print(f"Selected {len(selected)} weak variants -> {args.selection_out}")

    if args.run_command.strip():
        command = args.run_command.format(variants_file=str(args.selection_out))
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, check=False)
        if result.returncode != 0:
            print(f"Converter command failed with exit code {result.returncode}")
            return result.returncode

    if args.comparison_out is not None:
        if args.after_ranking is None:
            print("--comparison-out requires --after-ranking")
            return 2
        after_rows = load_ranking(args.after_ranking)
        write_comparison(before_rows, after_rows, selected, args.comparison_out)
        print(f"Wrote comparison report -> {args.comparison_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
