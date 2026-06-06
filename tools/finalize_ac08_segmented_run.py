#!/usr/bin/env python3
"""Aggregate completed AC08 segment outputs and publish full-set gate metrics."""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.ac08_segment_contract import iteration_report_contains_variant
from src.iCCModules.imageCompositeConverterAc08Reporting import (
    summarizePreviousGoodAc08VariantsImpl,
    writeAc08RegressionManifestImpl,
    writeAc08SuccessCriteriaReportImpl,
)
from src.successfulConversions import (
    AC08_PREVIOUSLY_GOOD_VARIANTS,
    AC08_REGRESSION_CASES,
    AC08_REGRESSION_SET_NAME,
    AC08_REGRESSION_VARIANTS,
)

MERGED_REPORTS = ("Iteration_Log.csv", "quality_tercile_passes.csv")
OPTIONAL_REPORT_HEADERS = {
    "quality_tercile_passes.csv": [
        "pass",
        "filename",
        "old_error_per_pixel",
        "new_error_per_pixel",
        "old_mean_delta2",
        "new_mean_delta2",
        "improved",
        "decision",
        "iteration_budget",
        "badge_validation_rounds",
    ],
}


def _merge_csv(inputs: list[Path], output: Path, *, empty_header: list[str] | None = None) -> None:
    header: list[str] | None = None
    rows: list[list[str]] = []
    for path in inputs:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=";")
            current_header = next(reader, None)
            if not current_header:
                continue
            if header is None:
                header = current_header
            elif current_header != header:
                raise ValueError(f"incompatible CSV header in {path}")
            rows.extend(reader)
    if header is None:
        if empty_header is None:
            raise FileNotFoundError(f"no segment report found for {output.name}")
        header = empty_header
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)


def _copy_segment_artifacts(segment_dir: Path, output_dir: Path) -> None:
    artifact_dirs = (
        "converted_svgs",
        "converted_images_png",
        "diff_pngs",
        "converted_svg_failed",
        "converted_images_png_failed",
    )
    for relative_dir in artifact_dirs:
        source = segment_dir / relative_dir
        if not source.exists():
            continue
        shutil.copytree(source, output_dir / relative_dir, dirs_exist_ok=True)
    reports_source = segment_dir / "reports"
    reports_target = output_dir / "reports"
    reports_target.mkdir(parents=True, exist_ok=True)
    for source in reports_source.iterdir():
        if source.name in MERGED_REPORTS or not source.is_file():
            continue
        shutil.copy2(source, reports_target / source.name)


def finalize(segments_root: Path, output_dir: Path, input_dir: str, descriptions_path: str, iterations: int) -> Path:
    expected = tuple(AC08_REGRESSION_VARIANTS)
    missing = [variant for variant in expected if not (segments_root / variant / ".segment-complete").is_file()]
    if missing:
        raise RuntimeError("incomplete AC08 segments: " + ",".join(missing))
    missing_reports = [
        variant
        for variant in expected
        if not iteration_report_contains_variant(
            segments_root / variant / "reports" / "Iteration_Log.csv",
            variant,
        )
    ]
    if missing_reports:
        raise RuntimeError("AC08 segments missing expected iteration row: " + ",".join(missing_reports))

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    for variant in expected:
        _copy_segment_artifacts(segments_root / variant, output_dir)

    reports_dir = output_dir / "reports"
    for report_name in MERGED_REPORTS:
        _merge_csv(
            [segments_root / variant / "reports" / report_name for variant in expected],
            reports_dir / report_name,
            empty_header=OPTIONAL_REPORT_HEADERS.get(report_name),
        )

    selected = sorted(expected)
    writeAc08RegressionManifestImpl(
        str(reports_dir),
        folder_path=input_dir,
        csv_path=descriptions_path,
        iterations=iterations,
        selected_variants=selected,
        ac08_regression_variants=expected,
        ac08_regression_cases=AC08_REGRESSION_CASES,
        ac08_regression_set_name=AC08_REGRESSION_SET_NAME,
    )
    result = writeAc08SuccessCriteriaReportImpl(
        str(reports_dir),
        selected_variants=selected,
        ac08_regression_variants=expected,
        ac08_regression_set_name=AC08_REGRESSION_SET_NAME,
        summarize_previous_good_fn=lambda path: summarizePreviousGoodAc08VariantsImpl(
            path,
            previous_good_variants=AC08_PREVIOUSLY_GOOD_VARIANTS,
        ),
    )
    if result is None:
        raise RuntimeError("AC08 aggregate metrics were not generated")
    return reports_dir / "ac08_success_metrics.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("segments_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--input-dir", default="artifacts/images_to_convert")
    parser.add_argument("--descriptions-path", default="artifacts/images_to_convert/Finale_Wurzelformen_V3.xml")
    parser.add_argument("--iterations", type=int, default=32)
    args = parser.parse_args()
    try:
        metrics = finalize(args.segments_root, args.output_dir, args.input_dir, args.descriptions_path, args.iterations)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"AC08 segmented aggregation failed: {exc}")
        return 1
    print(f"AC08 segmented aggregation complete: {metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
