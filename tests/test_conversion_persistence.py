"""Durable progress and SVG/metric identity, including interrupted publication."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterBatchRunState as state
from src.iCCModules import imageCompositeConverterConversionExecution as execution
from src.iCCModules import imageCompositeConverterConversionInitialPass as initial
from src.iCCModules import imageCompositeConverterConversionQualityPass as quality


def read(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and any(isinstance(row, dict) and "row_path" in row for row in payload.values()):
        reports = next(parent for parent in Path(path).parents if parent.name == "reports")
        return state.resolveArchivedRowsImpl(payload, reports)
    return payload


@pytest.fixture
def archive_case(tmp_path):
    reports, svg, inputs = [tmp_path / name for name in ("reports", "svg", "inputs")]
    for folder in (reports, svg, inputs):
        folder.mkdir()
    (inputs / "neutral.png").write_bytes(b"source")
    descriptions = inputs / "descriptions.xml"
    descriptions.write_bytes(b"<root/>")
    content = b'<svg xmlns="http://www.w3.org/2000/svg">\r\n</svg>\r\n'
    (svg / "neutral.svg").write_bytes(content)
    row = dict(filename="neutral.png", variant="NEUTRAL", best_error=1.25, mean_delta2=3.5,
               search_satisfactory=True, status="validated", svg_sha256=hashlib.sha256(content).hexdigest(),
               source_file_sha256=hashlib.sha256(b"source").hexdigest())
    archive = state.RunArchive(reports, "run-one", svg_dir=svg, input_dir=inputs,
                               descriptions_path=descriptions)
    return archive, row, descriptions


def commit(archive, row, **meta):
    return archive.commit(dict(run_id=archive.root.name, stage="initial_pass", state="completed", **meta),
                          {"neutral.png": row}, [])


def test_later_runs_cannot_change_frozen_svg_metrics_or_status(archive_case):
    archive, row, descriptions = archive_case
    checkpoint = commit(archive, row)
    first_rows = read(archive.reports / checkpoint["result_map_path"])
    frozen = first_rows["neutral.png"]
    assert frozen["artifact_binding"] == "verified"
    assert frozen["status"] == "validated" and frozen["best_error"] == 1.25
    original_files = {str(p): p.read_bytes() for p in archive.root.rglob("*") if p.is_file()}
    (archive.svg_dir / "neutral.svg").write_bytes(b"other run")
    other = state.RunArchive(archive.reports, "run-two", svg_dir=archive.svg_dir,
                             input_dir=archive.input_dir, descriptions_path=descriptions)
    changed = dict(row, svg_sha256=hashlib.sha256(b"other run").hexdigest(),
                   status="draft", search_satisfactory=False, best_error=9.)
    commit(other, changed)
    assert {name: Path(name).read_bytes() for name in original_files} == original_files
    assert (archive.reports / frozen["artifacts"]["svg"]["path"]).read_bytes().endswith(b"\r\n")


def test_failed_commit_keeps_previous_consistent_checkpoint(archive_case, monkeypatch):
    archive, row, _ = archive_case
    checkpoint = commit(archive, row)
    before = (archive.reports / "conversion_checkpoint.json").read_bytes()
    original = state.atomicWriteJsonImpl

    def fail(path, payload):
        if Path(path).name == "failures.json":
            raise OSError("disk full")
        return original(path, payload)

    monkeypatch.setattr(state, "atomicWriteJsonImpl", fail)
    with pytest.raises(OSError, match="disk full"):
        commit(archive, dict(row, best_error=99.))
    assert (archive.reports / "conversion_checkpoint.json").read_bytes() == before
    assert read(archive.reports / checkpoint["result_map_path"])["neutral.png"]["best_error"] == 1.25


def test_legacy_snapshot_preserves_old_reports_without_inventing_proof(archive_case):
    archive, row, _ = archive_case
    state.atomicWriteJsonImpl(archive.reports / "conversion_checkpoint.json",
                             {"run_id": "old-run", "result_map_path": "conversion_result_map.json"})
    (archive.reports / "conversion_bestlist.csv").write_bytes(b"old summary")
    legacy_row = {key: value for key, value in row.items() if key not in {"svg_sha256", "source_file_sha256"}}
    state.preserveLegacyRunImpl(archive.reports, svg_dir=archive.svg_dir, input_dir=archive.input_dir,
                                result_map={"neutral.png": legacy_row})
    checkpoint = read(archive.reports / "conversion_checkpoint.json")
    frozen = read(archive.reports / checkpoint["result_map_path"])["neutral.png"]
    assert frozen["artifact_binding"] == "unverified" and not frozen["search_satisfactory"]
    snapshots = list((archive.reports / "runs").glob("*-legacy"))
    assert len(snapshots) == 1
    assert (snapshots[0] / "conversion_bestlist.csv").read_bytes() == b"old summary"


def test_finalized_draft_retains_its_quarantined_svg(archive_case):
    archive, row, _ = archive_case
    failed_dir = archive.svg_dir.parent / "converted_svg_failed"
    failed_dir.mkdir()
    (archive.svg_dir / "neutral.svg").replace(failed_dir / "NEUTRAL.svg")
    checkpoint = commit(archive, dict(row, status="quality_failed", search_satisfactory=False))
    frozen = read(archive.reports / checkpoint["result_map_path"])["neutral.png"]
    assert frozen["artifact_binding"] == "verified" and frozen["status"] == "quality_failed"
    assert frozen["artifacts"]["svg"]["sha256"] == row["svg_sha256"]


def test_atomic_csv_failure_retains_old_complete_summary(tmp_path):
    target = tmp_path / "report.csv"
    target.write_bytes(b"old;report\r\n")
    with pytest.raises(OSError):
        with state.atomicTextFileImpl(target, newline="") as handle:
            handle.write("partial")
            raise OSError("disk full")
    assert target.read_bytes() == b"old;report\r\n"
    assert not list(tmp_path.glob("*.tmp"))


def test_later_retry_cannot_rebind_an_earlier_failure_log(archive_case):
    archive, _, _ = archive_case
    log = archive.reports / "neutral_element_validation.log"
    log.write_bytes(b"first failure")
    failures = [dict(filename="neutral.png", reason="TimeoutError", log_file=log.name)]
    first = archive.commit(dict(stage="initial_pass", state="failed"), {}, failures)
    first_log = read(archive.reports / first["failures_path"])[0]["artifacts"]["log_file"]
    log.write_bytes(b"new attempt")
    second = archive.commit(dict(stage="complete", state="completed"), {}, failures)
    assert read(archive.reports / second["failures_path"])[0]["artifacts"]["log_file"] == first_log
    assert (archive.reports / first_log["path"]).read_bytes() == b"first failure"


def test_unchanged_search_histories_and_result_indices_are_stored_once(archive_case):
    archive, row, _ = archive_case
    row["params"] = {"search_history": "large diagnostic history" * 8192}
    first = commit(archive, row)
    objects = {p.name for p in (archive.root / "objects").iterdir()}
    second = commit(archive, row, filename="other.png")
    assert first["result_map_path"] == second["result_map_path"]
    assert {p.name for p in (archive.root / "objects").iterdir()} == objects
    index = json.loads((archive.reports / first["result_map_path"]).read_text(encoding="utf-8"))
    assert set(index["neutral.png"]) == {"row_path", "row_sha256"}
    assert (archive.reports / first["result_map_path"]).stat().st_size < 512


@pytest.mark.parametrize("damage", ["index", "row"])
def test_damaged_result_index_or_row_is_not_loaded_for_resume(archive_case, damage):
    from src.iCCModules.imageCompositeConverterBatchReporting import loadConversionCheckpointResultMapImpl
    archive, row, _ = archive_case
    first = commit(archive, row)
    index_path = archive.reports / first["result_map_path"]
    path = index_path
    if damage == "row":
        index = json.loads(index_path.read_text(encoding="utf-8"))
        path = archive.reports / index["neutral.png"]["row_path"]
    path.write_bytes(b"corrupt")
    assert loadConversionCheckpointResultMapImpl(str(archive.reports / "conversion_checkpoint.json")) == {}


@pytest.mark.parametrize("damage", ["svg", "source", "missing_svg"])
def test_mismatched_artifacts_do_not_keep_validation(archive_case, damage):
    archive, row, _ = archive_case
    if damage == "svg":
        (archive.svg_dir / "neutral.svg").write_bytes(b"corrupt")
    elif damage == "source":
        (archive.input_dir / "neutral.png").write_bytes(b"changed source")
    else:
        (archive.svg_dir / "neutral.svg").unlink()
    checkpoint = commit(archive, row)
    frozen = read(archive.reports / checkpoint["result_map_path"])["neutral.png"]
    assert frozen["artifact_binding"] == "mismatch"
    assert not frozen["search_satisfactory"] and frozen["status"] == "artifact_mismatch"
    assert checkpoint["validated_count"] == 0


@pytest.mark.parametrize("damage", [None, "source", "descriptions", "object"])
def test_resume_restores_bound_bytes_and_requeues_changed_inputs(archive_case, damage):
    archive, row, descriptions = archive_case
    checkpoint = commit(archive, row)
    rows = read(archive.reports / checkpoint["result_map_path"])
    original = (archive.svg_dir / "neutral.svg").read_bytes()
    (archive.svg_dir / "neutral.svg").write_bytes(b"overwritten live output")
    if damage == "source":
        (archive.input_dir / "neutral.png").write_bytes(b"new source")
    elif damage == "descriptions":
        descriptions.write_bytes(b"new description")
    elif damage == "object":
        (archive.reports / rows["neutral.png"]["artifacts"]["svg"]["path"]).write_bytes(b"corrupt")
    restored = state.restoreCheckpointRowsImpl(rows, reports_dir=archive.reports, svg_dir=archive.svg_dir,
        input_dir=archive.input_dir, descriptions_path=descriptions)
    assert bool(restored) == (damage is None)
    if damage is None:
        assert (archive.svg_dir / "neutral.svg").read_bytes() == original


@pytest.mark.parametrize("pass_kind", ["initial", "quality"])
@pytest.mark.parametrize("outcome", ["failed", "skipped", "completed", KeyboardInterrupt, SystemExit, ValueError])
def test_each_pass_persists_start_and_every_exit(pass_kind, outcome):
    events = []
    filename = "neutral.png"
    row = dict(filename=filename, variant="NEUTRAL", error_per_pixel=1., mean_delta2=2.)

    def convert(*args, **kwargs):
        assert events[-1]["state"] == "started"
        if isinstance(outcome, type):
            raise outcome("test interruption")
        return (row if outcome == "completed" else None), outcome == "failed"

    common = dict(result_map={filename: row} if pass_kind == "quality" else {}, conversion_bestlist_rows={},
        rng=None, deterministic_order=True, base_iterations=1, convert_one_fn=convert,
        store_conversion_bestlist_snapshot_fn=lambda *a: None,
        restore_conversion_bestlist_snapshot_fn=lambda *a: None, checkpoint_fn=events.append)

    def run():
        if pass_kind == "initial":
            return initial.runInitialConversionPassImpl(**common, process_files=[filename], existing_donor_rows=[],
                folder_path="unused", svg_out_dir="unused", diff_out_dir="unused",
                try_template_transfer_fn=lambda **kw: (None, None),
                is_conversion_bestlist_candidate_better_fn=lambda *a: True,
                choose_conversion_bestlist_row_fn=lambda r, *a: r)
        return quality.runQualityPassesImpl(**common, max_quality_passes=1, stop_after_failure=False,
            allowed_error_per_pixel=0., skip_variants=set(), quality_logs=[],
            select_open_quality_cases_fn=lambda rows, **kw: rows, select_middle_lower_tercile_fn=lambda rows: rows,
            iteration_strategy_for_pass_fn=lambda *a: (1, 1),
            adaptive_iteration_budget_for_quality_row_fn=lambda r, b: b,
            evaluate_quality_pass_candidate_fn=lambda *a: (False, "unchanged", 1., 1., 2., 2.))

    if isinstance(outcome, type):
        with pytest.raises(outcome):
            run()
        expected = "failed" if issubclass(outcome, Exception) else "interrupted"
    else:
        run()
        expected = outcome
    assert [event["state"] for event in events] == ["started", expected]
    assert events[-1]["filename"] == filename


def test_current_svg_error_replaces_stale_fit_return_without_granting_validation(tmp_path):
    image = np.full((4, 6, 3), 30, dtype=np.uint8)
    for name in ("svg", "diff", "reports", "png"):
        (tmp_path / name).mkdir()
    (tmp_path / "neutral.png").write_bytes(b"source")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="6" height="4"><rect width="6" height="4" fill="#202020"/></svg>'

    def pipeline(*args, **kwargs):
        (tmp_path / "svg/neutral.svg").write_text(svg, encoding="utf-8")
        return "neutral", "description", {"vector_continuation": {"improved": True}}, 1, 99.

    from types import SimpleNamespace
    row, failed = execution.convertOneImpl(filename="neutral.png", folder_path=str(tmp_path), csv_path="unused",
        iteration_budget=1, badge_rounds=1, svg_out_dir=str(tmp_path / "svg"), diff_out_dir=str(tmp_path / "diff"),
        png_out_dir=str(tmp_path / "png"), reports_out_dir=str(tmp_path / "reports"),
        debug_ac0811_dir=None, debug_element_diff_dir=None, run_iteration_pipeline_fn=pipeline,
        read_validation_log_details_fn=lambda *a: {}, render_svg_to_numpy_fn=lambda *a: image + 2,
        calculate_delta2_stats_fn=lambda a, b: (float(np.square(a.astype(float)-b).sum(axis=2).mean()), 0.),
        get_base_name_from_file_fn=lambda s: s, cv2_module=SimpleNamespace(imread=lambda *a: image),
        render_embedded_raster_svg_fn=lambda *a: svg, append_batch_failure_fn=lambda f: pytest.fail(str(f)),
        print_fn=lambda *a: None)
    assert not failed
    assert row["best_error"] == row["current_svg_mae"] == 2.
    assert row["optimizer_best_error"] == 99. and row["mean_delta2"] == 12.
    assert row["error_per_pixel"] == 2. / 24
    assert row["best_error_metric"] == "mean_absolute_error"
    assert row["status"] == "draft" and row["search_satisfactory"] is False
    assert row["svg_sha256"] == hashlib.sha256((tmp_path / "svg/neutral.svg").read_bytes()).hexdigest()


@pytest.mark.parametrize("error", [KeyboardInterrupt, SystemExit, ValueError])
def test_public_range_persists_cancellation_and_failure_before_next_image(tmp_path, monkeypatch, error):
    from src import imageCompositeConverter as app
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    for name in ("ZZ0001.png", "ZZ0002.png"):
        (inputs / name).write_bytes(b"source")
    descriptions = inputs / "descriptions.xml"
    descriptions.write_text("<root/>", encoding="utf-8")
    out = tmp_path / "out"
    reports = out / "reports"
    seen = []

    def convert(**kwargs):
        checkpoint = read(reports / "conversion_checkpoint.json")
        assert checkpoint["state"] == "started" and checkpoint["active_filename"] == kwargs["filename"]
        if kwargs["filename"] == "ZZ0001.png":
            kwargs["append_batch_failure_fn"](dict(filename="ZZ0001.png", status="batch_error", reason="TimeoutError"))
            return None, True
        failures = read(reports / checkpoint["failures_path"])
        assert failures[0]["filename"] == "ZZ0001.png" and checkpoint["batch_failure_count"] == 1
        assert "ZZ0001.png" in (reports / "batch_failure_summary.csv").read_text(encoding="utf-8")
        seen.append(kwargs["filename"])
        raise error("stop")

    monkeypatch.setattr(execution, "convertOneImpl", convert)
    monkeypatch.setenv("ICC_MAX_QUALITY_PASSES", "0")
    with pytest.raises(error):
        app.convertRange(str(inputs), str(descriptions), 1, start_ref="ZZ0001", end_ref="ZZ0002",
                         output_root=str(out), deterministic_order=True, semantic_only=True)
    checkpoint = read(reports / "conversion_checkpoint.json")
    assert seen == ["ZZ0002.png"]
    assert checkpoint["state"] == ("failed" if error is ValueError else "interrupted")
    assert checkpoint["filename"] == "ZZ0002.png" and checkpoint["last_event"]["reason"] == error.__name__
    assert checkpoint["batch_failure_count"] == 1
    assert read(reports / checkpoint["result_map_path"]) == {}
    assert read(reports / "conversion_run_manifest.json")["run_id"] == checkpoint["run_id"]
    assert app.Action.STOCHASTIC_RUN_SEED == app.Action.STOCHASTIC_SEED_OFFSET == 0
