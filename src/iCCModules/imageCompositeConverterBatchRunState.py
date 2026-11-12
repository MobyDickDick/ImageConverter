"""Provenance and atomic persistence helpers for resumable catalog runs."""

from __future__ import annotations

from datetime import datetime, timezone
from contextlib import contextmanager
import hashlib
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
    with atomicTextFileImpl(path, newline="") as stream:
        stream.write(content)


@contextmanager
def atomicTextFileImpl(path, *, newline=None):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline=newline) as stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def atomicWriteJsonImpl(path: str | Path, payload: object) -> None:
    atomicWriteTextImpl(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


@contextmanager
def taskCheckpointImpl(checkpoint_fn, **meta):
    """Persist entry and every exit, including Python cancellation signals."""
    state = dict(meta, state="started")
    if checkpoint_fn is not None:
        checkpoint_fn(dict(state))
    state["state"] = "completed"
    try:
        yield state
    except BaseException as exc:
        state.update(state="failed" if isinstance(exc, Exception) else "interrupted",
                     reason=type(exc).__name__)
        raise
    finally:
        if checkpoint_fn is not None:
            checkpoint_fn(dict(state))


class RunArchive:
    """Append-only revisions; the checkpoint is the single commit pointer.

    Compatibility reports may be refreshed independently. Readers requiring a
    consistent snapshot follow the checkpoint into a sealed revision instead.
    Content-addressed objects avoid copying all SVGs on every state change.
    """

    def __init__(self, reports_dir, run_id, *, svg_dir, input_dir, descriptions_path=None):
        self.reports = Path(reports_dir)
        self.root = self.reports / "runs" / run_id
        self.svg_dir = Path(svg_dir)
        self.input_dir = Path(input_dir)
        self.bound_rows = {}
        self.bound_failures = {}
        self.descriptions = (self._object(descriptions_path)
                             if descriptions_path and Path(descriptions_path).is_file() else None)

    def _object(self, source):
        return self._store_bytes(Path(source).read_bytes())

    def _store_bytes(self, data):
        digest = hashlib.sha256(data).hexdigest()
        target = self.root / "objects" / digest
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{uuid.uuid4().hex}.tmp")
            try:
                with temporary.open("wb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        return {"path": target.relative_to(self.reports).as_posix(), "sha256": digest}

    def commit(self, payload, result_map, failures, *, completion=None):
        frozen_rows = {}
        for filename, row in result_map.items():
            serialized = json.dumps(row, sort_keys=True)
            cached = self.bound_rows.get(filename)
            if cached and cached[0] == serialized and payload.get("stage") != "complete":
                frozen_rows[filename] = cached[1]
                continue
            frozen = json.loads(serialized)
            stem = Path(filename).stem
            svg_source = self.svg_dir / f"{stem}.svg"
            if not svg_source.is_file() and row.get("status") == "quality_failed":
                svg_source = self.svg_dir.parent / "converted_svg_failed" / f"{stem.upper()}.svg"
            source_image = self.input_dir / filename
            if not source_image.is_file():
                source_image = self.input_dir / "succesessfulConvertedImages" / filename
            artifacts = {}
            for key, source in (
                ("svg", svg_source),
                ("source", source_image),
                ("validation_log", self.reports / f"{stem}_element_validation.log"),
            ):
                if source.is_file():
                    artifacts[key] = self._object(source)
            frozen["artifacts"] = artifacts
            if self.descriptions:
                artifacts["descriptions"] = self.descriptions
            expected = row.get("svg_sha256")
            actual = artifacts.get("svg", {}).get("sha256")
            source_expected = row.get("source_file_sha256")
            source_actual = artifacts.get("source", {}).get("sha256")
            frozen["artifact_binding"] = (
                "verified" if expected and actual == expected and source_expected and source_actual == source_expected
                else "unverified")
            if (expected and actual != expected) or (source_expected and source_actual != source_expected):
                frozen["artifact_binding"] = "mismatch"
                frozen["search_satisfactory"] = False
                frozen["status"] = "artifact_mismatch"
            elif not expected or not source_expected:
                # A historic row without a binding must never acquire a new proof.
                frozen["search_satisfactory"] = False
                frozen["status"] = "unverified"
            self.bound_rows[filename] = serialized, frozen
            frozen_rows[filename] = frozen

        frozen_failures = []
        for index, failure in enumerate(failures):
            identity = index, json.dumps(failure, sort_keys=True)
            if identity in self.bound_failures:
                frozen_failures.append(self.bound_failures[identity])
                continue
            frozen = dict(failure)
            frozen["artifacts"] = {}
            for key, directory in (("failed_svg", self.svg_dir), ("log_file", self.reports)):
                name = failure.get(key)
                if key == "failed_svg" and name and not (directory / Path(name).name).is_file():
                    directory = self.svg_dir.parent / "converted_svg_failed"
                    name = Path(name).name.removeprefix("Failed_")
                if name and (directory / Path(name).name).is_file():
                    frozen["artifacts"][key] = self._object(directory / Path(name).name)
            source = self.input_dir / str(failure.get("filename", ""))
            if source.is_file():
                frozen["artifacts"]["source"] = self._object(source)
            if self.descriptions:
                frozen["artifacts"]["descriptions"] = self.descriptions
            self.bound_failures[identity] = frozen
            frozen_failures.append(frozen)

        revision = self.root / "revisions" / uuid.uuid4().hex
        revision.mkdir(parents=True)
        # No published checkpoint can reference a half-written revision.
        # Large search histories belong to one row object, not to every later
        # checkpoint. An unchanged index is deduplicated as well (e.g. starts).
        row_index = {}
        for filename, row in frozen_rows.items():
            ref = self._store_bytes(json.dumps(row, ensure_ascii=False, sort_keys=True).encode("utf-8"))
            row_index[filename] = {"row_path": ref["path"], "row_sha256": ref["sha256"]}
        index_ref = self._store_bytes(json.dumps(row_index, sort_keys=True).encode("utf-8"))
        atomicWriteJsonImpl(revision / "failures.json", frozen_failures)
        summaries = {}
        for name in ("conversion_bestlist.csv", "batch_failure_summary.csv", "quality_tercile_passes.csv"):
            source = self.reports / name
            if source.is_file():
                summaries[name] = self._object(source)
        atomicWriteJsonImpl(revision / "reports.json", summaries)
        attempt_reports = {}
        if payload.get("filename") and payload.get("state") != "started":
            stem = Path(str(payload["filename"])).stem
            for source in self.reports.glob(stem + "_*"):
                if source.is_file():
                    attempt_reports[source.name] = self._object(source)
        atomicWriteJsonImpl(revision / "attempt_reports.json", attempt_reports)
        validated_count = sum(row.get("search_satisfactory") is True for row in frozen_rows.values())
        if completion is not None:
            completion = dict(completion, successful_count=validated_count, validated_count=validated_count,
                              draft_count=len(frozen_rows) - validated_count)
            atomicWriteJsonImpl(revision / "conversion_run_manifest.json", completion)
        committed = dict(payload, updated_at=utcNowImpl(),
                         schema_version="conversion_checkpoint_v2",
                         result_map_path=index_ref["path"], result_map_sha256=index_ref["sha256"],
                         failures_path=(revision / "failures.json").relative_to(self.reports).as_posix())
        committed["reports_path"] = (revision / "reports.json").relative_to(self.reports).as_posix()
        committed["attempt_reports_path"] = (revision / "attempt_reports.json").relative_to(self.reports).as_posix()
        committed["validated_count"] = validated_count
        committed["draft_count"] = len(frozen_rows) - committed["validated_count"]
        if completion is not None:
            committed["completion_manifest_path"] = (revision / "conversion_run_manifest.json").relative_to(self.reports).as_posix()
        atomicWriteJsonImpl(revision / "checkpoint.json", committed)
        atomicWriteJsonImpl(self.root / "latest_checkpoint.json", committed)
        atomicWriteJsonImpl(self.reports / "conversion_checkpoint.json", committed)
        return committed


def resolveArchivedRowsImpl(result_map, reports_dir):
    """Hydrate hash-bound row references; retain support for legacy full maps."""
    root = Path(reports_dir).resolve()
    resolved = {}
    for filename, row in result_map.items():
        if not isinstance(filename, str) or not isinstance(row, dict):
            continue
        if "row_path" not in row:
            resolved[filename] = dict(row)
            continue
        try:
            source = (root / row["row_path"]).resolve()
            if not source.is_relative_to(root / "runs"):
                continue
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != row["row_sha256"]:
                continue
            payload = json.loads(data)
            if isinstance(payload, dict):
                resolved[filename] = payload
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return resolved


def restoreCheckpointRowsImpl(rows, *, reports_dir, svg_dir, input_dir, descriptions_path):
    """Verify immutable objects and current inputs before restoring resumable rows.

    Active/failed attempts have no committed result and are requeued. A damaged
    archive or changed source/description also falls back to recomputation.
    """
    root = Path(reports_dir).resolve()
    restored = {}
    for filename, row in rows.items():
        artifacts = row.get("artifacts")
        if not artifacts or row.get("artifact_binding") != "verified":
            continue
        try:
            data = {}
            for key, artifact in artifacts.items():
                source = (root / artifact["path"]).resolve()
                if not source.is_relative_to(root / "runs"):
                    raise ValueError("Archive object outside run directory")
                data[key] = source.read_bytes()
                if hashlib.sha256(data[key]).hexdigest() != artifact["sha256"]:
                    raise ValueError("Archive object hash mismatch")
            for key, current in (("source", Path(input_dir) / filename),
                                 ("descriptions", Path(descriptions_path))):
                if key not in artifacts or hashlib.sha256(current.read_bytes()).hexdigest() != artifacts[key]["sha256"]:
                    raise ValueError("Conversion input changed")
            svg = Path(svg_dir) / (Path(filename).stem + ".svg")
            svg.parent.mkdir(parents=True, exist_ok=True)
            # Use bytes to retain the measured SVG's exact Windows newlines.
            _atomicWriteBytes(svg, data["svg"])
            if "validation_log" in data:
                _atomicWriteBytes(root / (Path(filename).stem + "_element_validation.log"), data["validation_log"])
            restored[filename] = dict(row)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return restored


def _atomicWriteBytes(target, data):
    temporary = target.with_name(f".{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def preserveLegacyRunImpl(reports_dir, *, svg_dir, input_dir, result_map):
    """Freeze pre-revision reports before a new invocation replaces them."""
    checkpoint = Path(reports_dir) / "conversion_checkpoint.json"
    try:
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if not isinstance(payload, dict) or str(payload.get("result_map_path", "")).startswith("runs/"):
        return
    # Keep the original checkpoint as provenance and do not invent validation.
    archive = RunArchive(reports_dir, newRunIdImpl() + "-legacy", svg_dir=svg_dir, input_dir=input_dir)
    archive.root.mkdir(parents=True)
    shutil.copy2(checkpoint, archive.root / "legacy_checkpoint.json")
    for source in Path(reports_dir).iterdir():
        if source.is_file():
            shutil.copy2(source, archive.root / source.name)
    archive.commit(dict(payload, legacy_snapshot=True), result_map, [])


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
    accounted = set(result_map) | {str(row.get("filename", "")) for row in failures if row.get("filename")}
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
        "successful_count": sum(row.get("search_satisfactory") is True for row in result_map.values()),
        "validated_count": sum(row.get("search_satisfactory") is True for row in result_map.values()),
        "draft_count": sum(row.get("search_satisfactory") is not True for row in result_map.values()),
        "domain_failure_count": len(failures) - technical_count,
        "technical_failure_count": technical_count,
        "timeout_count": timeout_count,
        "failure_count": len(failures),
        "pending_count": max(0, input_count - len(accounted)),
        "execution_status": "partial" if len(accounted) < input_count else "finished",
    }
