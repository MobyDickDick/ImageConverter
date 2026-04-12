"""Best-list helpers for all converted image variants."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


BESTLIST_COLUMNS = (
    "variant",
    "filename",
    "status",
    "best_iter",
    "best_error",
    "error_per_pixel",
    "mean_delta2",
    "std_delta2",
)


def conversionBestlistManifestPathImpl(reports_out_dir: str) -> Path:
    return Path(reports_out_dir) / "conversion_bestlist.csv"


def conversionBestlistSnapshotDirImpl(reports_out_dir: str) -> Path:
    return Path(reports_out_dir) / "conversion_bestlist_snapshots"


def conversionBestlistSnapshotPathsImpl(reports_out_dir: str, variant: str) -> dict[str, Path]:
    base = conversionBestlistSnapshotDirImpl(reports_out_dir)
    base.mkdir(parents=True, exist_ok=True)
    return {
        "svg": base / f"{variant}.svg",
        "log": base / f"{variant}_element_validation.log",
        "row": base / f"{variant}.json",
    }


def _as_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("inf")


def readConversionBestlistMetricsImpl(manifest_path: Path) -> dict[str, dict[str, object]]:
    if not manifest_path.exists():
        return {}

    rows: dict[str, dict[str, object]] = {}
    with manifest_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for raw in reader:
            variant = str(raw.get("variant", "")).strip().upper()
            if not variant:
                continue
            row: dict[str, object] = {
                "variant": variant,
                "filename": str(raw.get("filename", "")).strip(),
                "status": str(raw.get("status", "")).strip(),
                "best_iter": int(float(raw.get("best_iter", 0) or 0)),
                "best_error": _as_float(raw.get("best_error", "")),
                "error_per_pixel": _as_float(raw.get("error_per_pixel", "")),
                "mean_delta2": _as_float(raw.get("mean_delta2", "")),
                "std_delta2": _as_float(raw.get("std_delta2", "")),
            }
            rows[variant] = row
    return rows


def pruneConversionBestlistRowsWithoutSvgImpl(
    rows: dict[str, dict[str, object]],
    svg_out_dir: str,
) -> dict[str, dict[str, object]]:
    svg_dir = Path(svg_out_dir)
    if not rows:
        return {}

    pruned: dict[str, dict[str, object]] = {}
    for variant, row in rows.items():
        normalized_variant = str(variant).strip().upper()
        if not normalized_variant:
            continue
        if (svg_dir / f"{normalized_variant}.svg").exists():
            pruned[normalized_variant] = row
    return pruned


def writeConversionBestlistMetricsImpl(manifest_path: Path, rows: dict[str, dict[str, object]]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(BESTLIST_COLUMNS)
        for variant in sorted(rows):
            row = rows[variant]
            writer.writerow(
                [
                    variant,
                    str(row.get("filename", "")).strip(),
                    str(row.get("status", "")).strip(),
                    int(float(row.get("best_iter", 0) or 0)),
                    "" if not math.isfinite(_as_float(row.get("best_error"))) else f"{_as_float(row.get('best_error')):.6f}",
                    "" if not math.isfinite(_as_float(row.get("error_per_pixel"))) else f"{_as_float(row.get('error_per_pixel')):.8f}",
                    "" if not math.isfinite(_as_float(row.get("mean_delta2"))) else f"{_as_float(row.get('mean_delta2')):.6f}",
                    "" if not math.isfinite(_as_float(row.get("std_delta2"))) else f"{_as_float(row.get('std_delta2')):.6f}",
                ]
            )


def storeConversionBestlistSnapshotImpl(
    variant: str,
    row: dict[str, object],
    svg_out_dir: str,
    reports_out_dir: str,
) -> None:
    paths = conversionBestlistSnapshotPathsImpl(reports_out_dir, variant)
    svg_path = Path(svg_out_dir) / f"{variant}.svg"
    if svg_path.exists():
        paths["svg"].write_text(svg_path.read_text(encoding="utf-8"), encoding="utf-8")

    log_path = Path(reports_out_dir) / f"{variant}_element_validation.log"
    if log_path.exists():
        paths["log"].write_text(log_path.read_text(encoding="utf-8"), encoding="utf-8")

    paths["row"].write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def restoreConversionBestlistSnapshotImpl(
    variant: str,
    svg_out_dir: str,
    reports_out_dir: str,
) -> dict[str, object] | None:
    paths = conversionBestlistSnapshotPathsImpl(reports_out_dir, variant)
    restored = False
    svg_path = Path(svg_out_dir) / f"{variant}.svg"
    if paths["svg"].exists():
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(paths["svg"].read_text(encoding="utf-8"), encoding="utf-8")
        restored = True

    log_path = Path(reports_out_dir) / f"{variant}_element_validation.log"
    if paths["log"].exists():
        log_path.write_text(paths["log"].read_text(encoding="utf-8"), encoding="utf-8")
        restored = True

    if not restored or not paths["row"].exists():
        return None
    try:
        payload = json.loads(paths["row"].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def isConversionBestlistCandidateBetterImpl(
    previous_row: dict[str, object] | None,
    candidate_row: dict[str, object],
    evaluate_candidate_fn,
) -> bool:
    if previous_row is None:
        return True

    prev_status = str(previous_row.get("status", "")).strip().lower()
    cand_status = str(candidate_row.get("status", "")).strip().lower()
    if prev_status == "semantic_ok" and cand_status != "semantic_ok":
        return False
    if prev_status != "semantic_ok" and cand_status == "semantic_ok":
        return True

    def _has_ac0223_valve_head(row: dict[str, object] | None) -> bool:
        if not isinstance(row, dict):
            return False
        base = str(row.get("base", "")).upper()
        if base != "AC0223":
            return False
        params = row.get("params")
        if not isinstance(params, dict):
            return False
        return str(params.get("head_style", "")).lower() == "ac0223_triple_valve"

    if _has_ac0223_valve_head(candidate_row) and not _has_ac0223_valve_head(previous_row):
        # AC0223 ohne Ventilkopf ist semantisch falsch, selbst wenn der reine
        # Pixel-Fehler zufällig niedriger ausfällt.
        return True

    improved, *_ = evaluate_candidate_fn(previous_row, candidate_row)
    return bool(improved)


def chooseConversionBestlistRowImpl(
    candidate_row: dict[str, object],
    previous_row: dict[str, object] | None,
    restored_row: dict[str, object] | None,
) -> dict[str, object]:
    if previous_row is None:
        return dict(candidate_row)

    selected_row = dict(candidate_row)
    for key in ("best_iter", "best_error", "error_per_pixel", "mean_delta2", "std_delta2", "status"):
        if key in previous_row:
            selected_row[key] = previous_row[key]
    if isinstance(restored_row, dict):
        for key in ("best_iter", "best_error", "error_per_pixel", "mean_delta2", "std_delta2", "status"):
            if key in restored_row:
                selected_row[key] = restored_row[key]
    return selected_row


def repairAc0223BestlistArtifactsImpl(output_root: str) -> dict[str, object]:
    """Remove stale AC0223 bestlist artifacts that miss valve-head semantics."""
    root = Path(output_root)
    svg_out_dir = root / "converted_svgs"
    reports_out_dir = root / "reports"
    manifest_path = conversionBestlistManifestPathImpl(str(reports_out_dir))

    rows = readConversionBestlistMetricsImpl(manifest_path)
    targets = ("AC0223_L", "AC0223_M", "AC0223_S")
    removed_variants: list[str] = []

    for variant in targets:
        snapshot_paths = conversionBestlistSnapshotPathsImpl(str(reports_out_dir), variant)
        has_any_artifact = (
            variant in rows
            or snapshot_paths["svg"].exists()
            or snapshot_paths["log"].exists()
            or snapshot_paths["row"].exists()
            or (svg_out_dir / f"{variant}.svg").exists()
            or (reports_out_dir / f"{variant}_element_validation.log").exists()
            or (root / "diff_pngs" / f"{variant}_diff.png").exists()
        )
        if not has_any_artifact:
            continue

        snapshot_row = None
        try:
            if snapshot_paths["row"].exists():
                payload = json.loads(snapshot_paths["row"].read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    snapshot_row = payload
        except (OSError, json.JSONDecodeError):
            snapshot_row = None

        params = snapshot_row.get("params") if isinstance(snapshot_row, dict) else None
        has_valve_head = isinstance(params, dict) and str(params.get("head_style", "")).lower() == "ac0223_triple_valve"
        if has_valve_head:
            continue

        removed_variants.append(variant)
        rows.pop(variant, None)

        runtime_svg = svg_out_dir / f"{variant}.svg"
        runtime_log = reports_out_dir / f"{variant}_element_validation.log"
        runtime_diff = root / "diff_pngs" / f"{variant}_diff.png"
        for path in (
            snapshot_paths["svg"],
            snapshot_paths["log"],
            snapshot_paths["row"],
            runtime_svg,
            runtime_log,
            runtime_diff,
        ):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                # Keep repair resilient in partially locked local workdirs.
                pass

    if removed_variants:
        writeConversionBestlistMetricsImpl(manifest_path, rows)

    return {
        "output_root": str(root),
        "checked_variants": list(targets),
        "removed_variants": removed_variants,
        "removed_count": len(removed_variants),
    }
