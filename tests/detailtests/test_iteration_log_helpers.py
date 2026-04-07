from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterIterationLog as helpers


def test_write_iteration_log_and_collect_semantic_rows(tmp_path: Path):
    log_path = tmp_path / "Iteration_Log.csv"
    files = ["AC0800_L.jpg", "AC0811_S.jpg", "AC9999_X.jpg"]
    result_map = {
        "AC0800_L.jpg": {
            "params": {"elements": ["circle"], "mode": "plain"},
            "best_iter": 2,
            "best_error": 12.3456,
            "error_per_pixel": 0.123456789,
            "base": "AC0800",
            "variant": "AC0800_L",
            "w": 100,
            "h": 100,
        },
        "AC0811_S.jpg": {
            "params": {"elements": ["circle", "stem"], "mode": "semantic_badge"},
            "best_iter": 5,
            "best_error": 8.0,
            "error_per_pixel": 0.05,
            "base": "AC0811",
            "variant": "AC0811_S",
            "w": 80,
            "h": 60,
        },
    }

    semantic_rows = helpers.writeIterationLogAndCollectSemanticImpl(
        files=files,
        result_map=result_map,
        log_path=str(log_path),
    )

    log_text = log_path.read_text(encoding="utf-8-sig")
    assert "Dateiname;Gefundene Elemente;Beste Iteration;Diff-Score;FehlerProPixel" in log_text
    assert "AC0800_L.jpg;circle;2;12.35;0.12345679" in log_text
    assert "AC0811_S.jpg;circle + stem;5;8.00;0.05000000" in log_text
    assert "AC9999_X.jpg" not in log_text
    assert semantic_rows == [
        {
            "filename": "AC0811_S.jpg",
            "base": "AC0811",
            "variant": "AC0811_S",
            "w": 80,
            "h": 60,
            "error": 8.0,
        }
    ]
