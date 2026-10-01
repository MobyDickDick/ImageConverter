"""Provenance and atomic persistence helpers for resumable catalog runs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import uuid


def utcNowImpl() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def newRunIdImpl() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"catalog-{timestamp}-{uuid.uuid4().hex[:8]}"


def atomicWriteTextImpl(path: str | Path, content: str) -> None:
    """Replace *path* atomically after flushing the sibling temporary file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def atomicWriteJsonImpl(path: str | Path, payload: object) -> None:
    atomicWriteTextImpl(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def readCheckpointIdentityImpl(checkpoint_path: str | Path) -> tuple[str, str]:
    try:
        payload = json.loads(Path(checkpoint_path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    return str(payload.get("run_id", "")).strip(), str(payload.get("started_at", "")).strip()


def snapshotResumeArtifactsImpl(reports_dir: str | Path, *, run_id: str) -> str:
    """Copy mutable resume inputs once before continuing an existing run."""
    root = Path(reports_dir)
    source_names = (
        "conversion_checkpoint.json",
        "conversion_result_map.json",
        "batch_failure_summary.csv",
        "optimization_render_telemetry_summary.json",
    )
    existing = [root / name for name in source_names if (root / name).is_file()]
    if not existing:
        return ""
    snapshot_root = root / "resume_snapshots"
    snapshot_dir = snapshot_root / run_id
    suffix = 1
    while snapshot_dir.exists():
        suffix += 1
        snapshot_dir = snapshot_root / f"{run_id}-{suffix}"
    snapshot_dir.mkdir(parents=True)
    for source in existing:
        shutil.copy2(source, snapshot_dir / source.name)
    return str(snapshot_dir)


def buildCompletionManifestImpl(
    *,
    run_id: str,
    started_at: str,
    input_count: int,
    result_map: dict[str, dict[str, object]],
    failures: list[dict[str, str]],
    run_seed: int,
    resumed_result_count: int,
) -> dict[str, object]:
    technical_statuses = {"render_failure", "batch_error"}
    timeout_count = sum(
        "timeout" in str(row.get("reason", "")).lower()
        or "timeout" in str(row.get("details", "")).lower()
        for row in failures
    )
    technical_count = sum(str(row.get("status", "")) in technical_statuses for row in failures)
    return {
        "schema_version": "conversion_run_manifest_v1",
        "run_id": run_id,
        "stage": "complete",
        "started_at": started_at,
        "completed_at": utcNowImpl(),
        "run_seed": int(run_seed),
        "input_count": int(input_count),
        "processed_result_count": len(result_map),
        "resumed_result_count": int(resumed_result_count),
        "successful_count": len(result_map),
        "domain_failure_count": len(failures) - technical_count,
        "technical_failure_count": technical_count,
        "timeout_count": timeout_count,
        "failure_count": len(failures),
    }
