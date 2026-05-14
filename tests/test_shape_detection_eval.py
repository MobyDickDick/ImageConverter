from pathlib import Path

import pytest


pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.shape_detection_eval import run_eval


def test_run_eval_writes_reports(tmp_path: Path):
    summary = run_eval(tmp_path)
    assert summary["samples"] == 10
    assert summary["accuracy"] >= 0.8
    assert (tmp_path / "shape_detection_eval_report.csv").exists()
    assert (tmp_path / "shape_detection_eval_summary.json").exists()
