from __future__ import annotations

from pathlib import Path

from tools.evaluate_multi_objective_prototype import evaluate_prototype


def test_evaluate_prototype_applies_semantic_penalty_from_logs(tmp_path: Path) -> None:
    bestlist = tmp_path / "conversion_bestlist.csv"
    bestlist.write_text(
        "variant;filename;status;best_iter;best_error;error_per_pixel;mean_delta2;std_delta2\n"
        "AC0800_L;AC0800_L.jpg;;1;6.9;0.01;100.0;1.0\n"
        "AC0800_M;AC0800_M.jpg;;1;6.8;0.02;120.0;1.1\n",
        encoding="utf-8",
    )

    logs = tmp_path / "reports"
    logs.mkdir()
    (logs / "AC0800_L_element_validation.log").write_text("status=semantic_ok\n", encoding="utf-8")
    (logs / "AC0800_M_element_validation.log").write_text("status=semantic_mismatch\n", encoding="utf-8")

    rows = evaluate_prototype(
        bestlist,
        logs,
        weight_pixel_error=1.0,
        weight_geometry_penalty=0.35,
        weight_semantic_penalty=1.0,
    )

    by_variant = {row.variant: row for row in rows}
    assert by_variant["AC0800_L"].semantic_penalty == 0.0
    assert by_variant["AC0800_M"].semantic_penalty == 1.0
    assert by_variant["AC0800_M"].prototype_score > by_variant["AC0800_L"].prototype_score
