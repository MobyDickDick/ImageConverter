"""Successful-conversion quality metric helper functions."""

from __future__ import annotations

import csv
import os


def loadIterationLogRowsImpl(reports_out_dir: str) -> dict[str, dict[str, str]]:
    """Load Iteration_Log.csv keyed by uppercase filename stem."""
    path = os.path.join(reports_out_dir, "Iteration_Log.csv")
    if not os.path.exists(path):
        return {}

    rows: dict[str, dict[str, str]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            filename = str(row.get("Dateiname", "")).strip()
            if not filename:
                continue
            rows[os.path.splitext(filename)[0].upper()] = dict(row)
    return rows


def findImagePathByVariantImpl(folder_path: str, variant: str) -> str | None:
    """Return the raster image path for ``variant`` if present."""
    for ext in (".jpg", ".png", ".bmp", ".gif"):
        candidate = os.path.join(folder_path, f"{variant}{ext}")
        if os.path.exists(candidate):
            return candidate
    return None
