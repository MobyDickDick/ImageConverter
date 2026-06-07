"""Incremental batch helpers for reusing fresh conversion artifacts."""

from __future__ import annotations

import math
from pathlib import Path


def partitionReusableConversionsImpl(
    *,
    filenames: list[str],
    existing_rows: list[dict[str, object]],
    folder_path: str,
    svg_out_dir: str,
    descriptions_path: str | None,
    force_reconvert: bool = False,
) -> tuple[list[str], dict[str, dict[str, object]]]:
    """Split a batch into stale inputs and reusable, already converted rows.

    A row is reusable only when its successful SVG is at least as new as both
    the source raster and the optional descriptions file. Failed/missing
    artifacts and non-finite report rows are always converted again.
    """
    if force_reconvert:
        return list(filenames), {}

    rows_by_filename = {
        str(row.get("filename", "")): row
        for row in existing_rows
        if str(row.get("filename", ""))
    }
    descriptions_mtime_ns = _mtimeNs(Path(descriptions_path)) if descriptions_path else 0
    pending: list[str] = []
    reusable: dict[str, dict[str, object]] = {}

    for filename in filenames:
        row = rows_by_filename.get(filename)
        if row is None or not _hasFiniteError(row):
            pending.append(filename)
            continue

        source_path = Path(folder_path) / filename
        source_stem = Path(filename).stem
        variant = str(row.get("variant", "")).strip().upper() or source_stem.upper()
        svg_path = Path(svg_out_dir) / f"{source_stem}.svg"
        if not svg_path.exists() and source_stem != variant:
            svg_path = Path(svg_out_dir) / f"{variant}.svg"
        source_mtime_ns = _mtimeNs(source_path)
        svg_mtime_ns = _mtimeNs(svg_path)
        if source_mtime_ns <= 0 or svg_mtime_ns < max(source_mtime_ns, descriptions_mtime_ns):
            pending.append(filename)
            continue

        reusable[filename] = dict(row)

    return pending, reusable


def _mtimeNs(path: Path) -> int:
    try:
        return int(path.stat().st_mtime_ns)
    except OSError:
        return 0


def _hasFiniteError(row: dict[str, object]) -> bool:
    try:
        return math.isfinite(float(row.get("error_per_pixel", float("inf"))))
    except (TypeError, ValueError):
        return False
