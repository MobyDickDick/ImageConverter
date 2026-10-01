import json
from pathlib import Path

from src.iCCModules import imageCompositeConverterDebugTrace as debug_trace


def test_resolve_debug_trace_path_uses_reports_directory_for_auto(tmp_path: Path) -> None:
    assert debug_trace.resolveDebugTracePathImpl("auto", str(tmp_path)) == tmp_path / "conversion_debug_trace.jsonl"
    assert debug_trace.resolveDebugTracePathImpl(None, str(tmp_path)) is None


def test_debug_trace_emitter_writes_jsonl_and_normalizes_non_finite_values(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "trace.jsonl"
    emit = debug_trace.createDebugTraceEmitterImpl(path)

    emit("quality", score=float("inf"), candidates={"A", "B"})

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["event"] == "quality"
    assert payload["score"] is None
    assert sorted(payload["candidates"]) == ["A", "B"]
    assert payload["timestamp_utc"].endswith("+00:00")


def test_summarize_conversion_row_exposes_strategy_and_quality() -> None:
    summary = debug_trace.summarizeConversionRowImpl(
        {
            "variant": "SAMPLE_L",
            "base": "SAMPLE",
            "error_per_pixel": 12.5,
            "mean_delta2": 8.0,
            "params": {"mode": "geometry_ir", "geometry_ir": [{"kind": "Circle"}]},
        }
    )

    assert summary["strategy_mode"] == "geometry_ir"
    assert summary["geometry_ir_elements"] == 1
    assert summary["error_per_pixel"] == 12.5
