#!/usr/bin/env python3
"""Refresh conversion quality evidence and propose a bounded Plan-B rotation."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import cv2
import numpy as np

from src.imageCompositeConverter import Action

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_THRESHOLD = 0.045945679012345676
DEFAULT_MAX_CANDIDATES = 5
DEFAULT_TOP_ERROR_CASES = 5
DEFAULT_MAX_IMAGE_AREA = 3_200

IMAGE_DIRS = (
    Path("artifacts/images_to_convert"),
    Path("artifacts/images_to_convert/nonconvertable"),
    Path("artifacts/regression_baseline/satisfactory/images"),
)
SVG_DIRS = (
    Path("artifacts/converted_images/converted_svgs"),
    Path("src/artifacts/converted_images/converted_svgs"),
    Path("artifacts/regression_baseline/satisfactory/svgs"),
    Path("artifacts/converted_images/reports/conversion_bestlist_snapshots"),
)


@dataclass(frozen=True)
class QualityRecord:
    variant: str
    source: str
    image_path: str | None
    svg_path: str | None
    width: int | None
    height: int | None
    mean_delta2: float | None
    normalized_mse: float | None
    status: str

    @property
    def image_area(self) -> int | None:
        if self.width is None or self.height is None:
            return None
        return self.width * self.height


def normalized_mse(image: np.ndarray, rendered: np.ndarray) -> tuple[float, float]:
    """Return mean squared RGB distance and its normalization to [0, 1]."""
    if image.shape != rendered.shape:
        raise ValueError("image and rendered SVG must have the same shape")
    delta = image.astype(np.float32) - rendered.astype(np.float32)
    mean_delta2 = float(np.mean(np.sum(delta * delta, axis=2)))
    return mean_delta2, mean_delta2 / (3 * 255 * 255)


def _first_existing(root: Path, directories: Sequence[Path], filename: str) -> Path | None:
    for directory in directories:
        candidate = root / directory / filename
        if candidate.exists():
            return candidate
    return None


def _relative(path: Path | None, root: Path) -> str | None:
    return str(path.relative_to(root)) if path is not None else None


def review_variant(
    variant: str,
    *,
    source: str,
    root: Path = PROJECT_ROOT,
    image_dirs: Sequence[Path] = IMAGE_DIRS,
    svg_dirs: Sequence[Path] = SVG_DIRS,
) -> QualityRecord:
    image_path = _first_existing(root, image_dirs, f"{variant}.jpg")
    svg_path = _first_existing(root, svg_dirs, f"{variant}.svg")
    if image_path is None or svg_path is None:
        return QualityRecord(
            variant=variant,
            source=source,
            image_path=_relative(image_path, root),
            svg_path=_relative(svg_path, root),
            width=None,
            height=None,
            mean_delta2=None,
            normalized_mse=None,
            status="missing_pair",
        )

    image = cv2.imread(str(image_path))
    if image is None:
        return QualityRecord(
            variant=variant,
            source=source,
            image_path=_relative(image_path, root),
            svg_path=_relative(svg_path, root),
            width=None,
            height=None,
            mean_delta2=None,
            normalized_mse=None,
            status="image_read_failed",
        )

    height, width = image.shape[:2]
    rendered = Action.renderSvgToNumpy(
        svg_path.read_text(encoding="utf-8", errors="replace"), width, height
    )
    if rendered is None:
        return QualityRecord(
            variant=variant,
            source=source,
            image_path=_relative(image_path, root),
            svg_path=_relative(svg_path, root),
            width=width,
            height=height,
            mean_delta2=None,
            normalized_mse=None,
            status="render_failed",
        )

    mean_delta2, mse = normalized_mse(image, rendered)
    return QualityRecord(
        variant=variant,
        source=source,
        image_path=_relative(image_path, root),
        svg_path=_relative(svg_path, root),
        width=width,
        height=height,
        mean_delta2=mean_delta2,
        normalized_mse=mse,
        status="ok",
    )


def select_plan_b_candidates(
    successful_records: Iterable[QualityRecord],
    diff_records: Iterable[QualityRecord],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
    max_image_area: int = DEFAULT_MAX_IMAGE_AREA,
    excluded_variants: Iterable[str] = (),
) -> list[QualityRecord]:
    """Prioritize bad successful conversions, then compact high-error diff cases."""
    excluded = set(excluded_variants)
    selected: list[QualityRecord] = []

    successful = sorted(
        (
            record
            for record in successful_records
            if record.status != "ok"
            or (
                record.normalized_mse is not None
                and record.normalized_mse > threshold
            )
        ),
        key=lambda record: (
            record.status == "ok",
            -(record.normalized_mse or float("inf")),
            record.variant,
        ),
    )
    diff = sorted(
        (
            record
            for record in diff_records
            if record.status == "ok"
            and record.normalized_mse is not None
            and record.normalized_mse > threshold
            and record.image_area is not None
            and record.image_area <= max_image_area
            and "_sia" not in record.variant.lower()
        ),
        key=lambda record: (-(record.normalized_mse or 0.0), record.variant),
    )

    for record in [*successful, *diff]:
        if record.variant in excluded or any(
            existing.variant == record.variant for existing in selected
        ):
            continue
        selected.append(record)
        if len(selected) == max_candidates:
            break
    return selected


def _read_successful_variants(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_diff_variants(path: Path) -> list[str]:
    suffix = "_diff"
    return sorted(
        item.stem[: -len(suffix)]
        for item in path.glob("*_diff.png")
        if item.stem.endswith(suffix)
    )


def _record_dict(record: QualityRecord) -> dict[str, object]:
    data = asdict(record)
    data["image_area"] = record.image_area
    return data


def _variant_name(record: QualityRecord | Mapping[str, object]) -> str:
    """Return a variant name from an in-memory record or serialized summary row."""
    if isinstance(record, QualityRecord):
        return record.variant
    return str(record["variant"])


def variants_csv(records: Iterable[QualityRecord | Mapping[str, object]]) -> str:
    """Format variant names from live records or JSON-ready dictionaries."""
    return ",".join(_variant_name(record) for record in records)


def quality_sort_key(record: QualityRecord) -> tuple[int, float, str]:
    """Sort renderable records from best to worst while keeping failures last."""
    if record.status == "ok" and record.normalized_mse is not None:
        return (0, record.normalized_mse, record.variant)
    return (1, float("inf"), record.variant)


def build_quality_ranking(records: Iterable[QualityRecord]) -> list[QualityRecord]:
    """Return the complete quality order, lower normalized MSE first."""
    return sorted(records, key=quality_sort_key)


def select_threshold_boundary_triple(
    records: Iterable[QualityRecord],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[QualityRecord]:
    """Select last passing record and first two failing records in quality order."""
    ranking = build_quality_ranking(
        record
        for record in records
        if record.status == "ok" and record.normalized_mse is not None
    )
    passing = [record for record in ranking if (record.normalized_mse or 0.0) <= threshold]
    failing = [record for record in ranking if (record.normalized_mse or 0.0) > threshold]
    selected: list[QualityRecord] = []
    if passing:
        selected.append(passing[-1])
    selected.extend(failing[:2])
    return selected


def build_boundary_conversion_command(
    records: Sequence[QualityRecord],
    *,
    input_dir: Path = Path("artifacts/images_to_convert"),
    descriptions_path: Path = Path("artifacts/images_to_convert/Finale_Wurzelformen_V3.xml"),
    output_dir: Path = Path("artifacts/converted_images"),
    iterations: int = 64,
) -> str:
    """Build a single converter invocation constrained to the boundary variants."""
    variants = " ".join(record.variant for record in records)
    return (
        f"for variant in {variants}; do "
        "ICC_FORCE_RECONVERT=1 python -m src.imageCompositeConverter "
        f"{input_dir} --descriptions-path {descriptions_path} "
        f"--output-dir {output_dir} --iterations {iterations} "
        "--start $variant --end $variant --deterministic-order || exit $?; "
        "done"
    )

def select_top_error_cases(
    records: Iterable[QualityRecord],
    *,
    max_cases: int = DEFAULT_TOP_ERROR_CASES,
) -> list[QualityRecord]:
    """Return the largest reproducible renderable errors by primary metric."""
    return sorted(
        (record for record in records if record.status == "ok" and record.mean_delta2 is not None),
        key=lambda record: (-(record.mean_delta2 or 0.0), record.variant),
    )[:max_cases]


def write_reports(
    output_dir: Path,
    successful_records: Sequence[QualityRecord],
    diff_records: Sequence[QualityRecord],
    candidates: Sequence[QualityRecord],
    *,
    threshold: float,
    max_image_area: int,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
    top_error_cases: Sequence[QualityRecord] | None = None,
    boundary_records: Sequence[QualityRecord] | None = None,
    boundary_command: str | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = [*successful_records, *diff_records]
    csv_path = output_dir / "conversion_quality_records_v2.csv"
    fields = list(_record_dict(records[0]).keys()) if records else list(_record_dict(QualityRecord("", "", None, None, None, None, None, None, "")).keys())
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(_record_dict(record) for record in records)

    ranking = build_quality_ranking(records)
    ranking_path = output_dir / "conversion_quality_ranking_v1.csv"
    with ranking_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["rank", "meets_threshold", *fields],
            lineterminator="\n",
        )
        writer.writeheader()
        for rank, record in enumerate(ranking, start=1):
            meets_threshold = (
                record.status == "ok"
                and record.normalized_mse is not None
                and record.normalized_mse <= threshold
            )
            writer.writerow({"rank": rank, "meets_threshold": int(meets_threshold), **_record_dict(record)})

    top_error_cases = list(top_error_cases) if top_error_cases is not None else select_top_error_cases(records)
    boundary_records = list(boundary_records) if boundary_records is not None else select_threshold_boundary_triple(records, threshold=threshold)
    boundary_command = boundary_command if boundary_command is not None else build_boundary_conversion_command(boundary_records)

    boundary_path = output_dir / "plan_b_boundary_triple_v1.csv"
    with boundary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["boundary_role", *fields],
            lineterminator="\n",
        )
        writer.writeheader()
        failing_index = 0
        for record in boundary_records:
            if record.normalized_mse is not None and record.normalized_mse <= threshold:
                role = "last_passing"
            else:
                failing_index += 1
                role = "first_failing" if failing_index == 1 else "second_failing"
            writer.writerow({"boundary_role": role, **_record_dict(record)})

    command_path = output_dir / "plan_b_boundary_conversion_command.sh"
    command_path.write_text(boundary_command + "\n", encoding="utf-8")

    candidate_path = output_dir / "plan_b_candidate_triage_v1.csv"
    with candidate_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["priority", *fields],
            lineterminator="\n",
        )
        writer.writeheader()
        for priority, record in enumerate(candidates, start=1):
            writer.writerow({"priority": priority, **_record_dict(record)})

    top_errors_path = output_dir / "top_reproducible_error_cases_v1.csv"
    with top_errors_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["rank", *fields],
            lineterminator="\n",
        )
        writer.writeheader()
        for rank, record in enumerate(top_error_cases, start=1):
            writer.writerow({"rank": rank, **_record_dict(record)})

    summary = {
        "schema_version": "conversion_quality_review_v2",
        "threshold_normalized_mse": threshold,
        "max_plan_b_candidates": max_candidates,
        "max_top_error_cases": len(top_error_cases),
        "max_candidate_image_area": max_image_area,
        "metrics": {
            "successful_variants": len(successful_records),
            "successful_renderable_pairs": sum(record.status == "ok" for record in successful_records),
            "successful_above_threshold": sum(
                record.normalized_mse is not None and record.normalized_mse > threshold
                for record in successful_records
            ),
            "successful_missing_or_failed": sum(record.status != "ok" for record in successful_records),
            "diff_variants": len(diff_records),
            "diff_renderable_pairs": sum(record.status == "ok" for record in diff_records),
            "selected_candidates": len(candidates),
            "top_error_cases": len(top_error_cases),
            "ranked_records": len(ranking),
            "boundary_triple_records": len(boundary_records),
        },
        "selected_candidates": [_record_dict(record) for record in candidates],
        "top_reproducible_error_cases": [_record_dict(record) for record in top_error_cases],
        "boundary_triple": [_record_dict(record) for record in boundary_records],
        "boundary_conversion_command": boundary_command,
        "records_csv": _relative(csv_path, PROJECT_ROOT) if csv_path.is_relative_to(PROJECT_ROOT) else str(csv_path),
        "ranking_csv": _relative(ranking_path, PROJECT_ROOT) if ranking_path.is_relative_to(PROJECT_ROOT) else str(ranking_path),
        "candidate_triage_csv": _relative(candidate_path, PROJECT_ROOT) if candidate_path.is_relative_to(PROJECT_ROOT) else str(candidate_path),
        "boundary_triple_csv": _relative(boundary_path, PROJECT_ROOT) if boundary_path.is_relative_to(PROJECT_ROOT) else str(boundary_path),
        "boundary_conversion_command_path": _relative(command_path, PROJECT_ROOT) if command_path.is_relative_to(PROJECT_ROOT) else str(command_path),
        "top_error_cases_csv": _relative(top_errors_path, PROJECT_ROOT) if top_errors_path.is_relative_to(PROJECT_ROOT) else str(top_errors_path),
    }
    json_path = output_dir / "conversion_quality_review_v2.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/evaluation/conversion_quality_review_v2"),
    )
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--max-candidates", type=int, default=DEFAULT_MAX_CANDIDATES)
    parser.add_argument("--max-image-area", type=int, default=DEFAULT_MAX_IMAGE_AREA)
    parser.add_argument("--exclude", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    successful_variants = _read_successful_variants(PROJECT_ROOT / "successed_conversions.txt")
    diff_variants = _read_diff_variants(PROJECT_ROOT / "artifacts/converted_images/diff_pngs")
    successful_records = [
        review_variant(variant, source="successful_conversion")
        for variant in successful_variants
    ]
    diff_records = [
        review_variant(variant, source="diff_inventory") for variant in diff_variants
    ]
    candidates = select_plan_b_candidates(
        successful_records,
        diff_records,
        threshold=args.threshold,
        max_candidates=args.max_candidates,
        max_image_area=args.max_image_area,
        excluded_variants=args.exclude,
    )
    top_error_cases = select_top_error_cases([*successful_records, *diff_records])
    summary = write_reports(
        PROJECT_ROOT / args.output_dir,
        successful_records,
        diff_records,
        candidates,
        threshold=args.threshold,
        max_image_area=args.max_image_area,
        max_candidates=args.max_candidates,
        top_error_cases=top_error_cases,
    )
    print(json.dumps(summary["metrics"], sort_keys=True))
    print("selected=" + variants_csv(candidates))
    print("top_errors=" + variants_csv(top_error_cases))
    print("boundary_triple=" + variants_csv(summary["boundary_triple"]))
    print("boundary_command=" + str(summary["boundary_conversion_command"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
