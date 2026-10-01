"""Structured, opt-in diagnostics for converter decisions.

The regular console log is intended for humans following a running batch.  The
JSON Lines trace produced here is deliberately stable and machine readable so
that a bad conversion can be reconstructed without scraping console text.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


def resolveDebugTracePathImpl(requested_path: str | None, reports_out_dir: str) -> Path | None:
    """Resolve the CLI value; ``auto`` places the trace alongside other reports."""
    value = str(requested_path or "").strip()
    if not value:
        return None
    if value.lower() == "auto":
        return Path(reports_out_dir) / "conversion_debug_trace.jsonl"
    return Path(value).expanduser()


def _jsonSafe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _jsonSafe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonSafe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def createDebugTraceEmitterImpl(path: Path | None) -> Callable[..., None]:
    """Create a small append-only event writer, or a no-op when tracing is off."""
    if path is None:
        return lambda _event, **_fields: None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")

    def emit(event: str, **fields: object) -> None:
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event": str(event),
            **fields,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonSafe(record), ensure_ascii=False, sort_keys=True) + "\n")

    return emit


def summarizeConversionRowImpl(row: dict[str, object] | None) -> dict[str, object]:
    """Select the fields that explain the chosen strategy and resulting quality."""
    if row is None:
        return {}
    params = row.get("params")
    params_dict = params if isinstance(params, dict) else {}
    geometry_ir = params_dict.get("optimized_geometry_ir", params_dict.get("geometry_ir", []))
    return {
        "variant": row.get("variant", ""),
        "base": row.get("base", ""),
        "strategy_mode": params_dict.get("mode", "unknown"),
        "geometry_ir_elements": len(geometry_ir) if isinstance(geometry_ir, list) else 0,
        "best_error": row.get("best_error"),
        "error_per_pixel": row.get("error_per_pixel"),
        "mean_delta2": row.get("mean_delta2"),
        "std_delta2": row.get("std_delta2"),
        "spatial_quality_score": row.get("spatial_quality_score"),
    }
