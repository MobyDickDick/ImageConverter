from __future__ import annotations

from tools.optimize_geometry_ir import optimize_geometry_ir


def _beam(*geometries):
    return {
        "status": "resolved",
        "hypotheses": [
            {
                "hypothesis_id": f"h{index}",
                "hard_constraints_satisfied": True,
                "geometry_ir": geometry,
            }
            for index, geometry in enumerate(geometries)
        ],
    }


def test_two_phase_optimizer_reduces_loss_and_logs_all_components() -> None:
    report = optimize_geometry_ir(
        _beam(
            [
                {
                    "id": "shape",
                    "kind": "rectangle",
                    "x": 0,
                    "y": 4,
                    "width": 10,
                    "stroke_width": 1,
                }
            ]
        ),
        [
            {
                "id": "shape",
                "kind": "rectangle",
                "x": 8,
                "y": 4,
                "width": 12,
                "stroke_width": 2,
            }
        ],
        hard_constraints={"required_kinds": ["rectangle"], "z_order": ["shape"]},
    )
    assert report["schema_version"] == "multi_objective_optimization_report_v1"
    assert report["status"] == "optimized"
    assert report["final_loss"]["total"] < report["initial_loss"]["total"]
    assert report["iterations"][0]["phase"] == "discrete"
    assert {"pixel", "edge", "structure", "semantic", "total"} == set(
        report["final_loss"]
    )
    assert all(
        not row["hard_violations"] for row in report["iterations"] if row["accepted"]
    )


def test_semantically_invalid_pixel_closer_hypothesis_cannot_win() -> None:
    beam = _beam(
        [{"id": "shape", "kind": "circle", "x": 10}],
        [{"id": "shape", "kind": "rectangle", "x": 0}],
    )
    report = optimize_geometry_ir(
        beam,
        [{"id": "shape", "kind": "circle", "x": 0}],
        hard_constraints={"required_kinds": ["circle"]},
    )
    assert report["selected_hypothesis_id"] == "h0"
    assert report["rejected_hypotheses"][0]["hypothesis_id"] == "h1"


def test_stagnation_is_canonical_and_does_not_oscillate() -> None:
    report = optimize_geometry_ir(
        _beam([{"kind": "circle", "x": 1}]),
        [{"kind": "circle", "x": 1}],
        stagnation_limit=2,
    )
    assert report["status"] == "unchanged"
    assert report["termination_reason"] == "converged"
    assert report["accepted_iterations"] == 0


def test_budget_overrun_has_canonical_reason() -> None:
    report = optimize_geometry_ir(
        _beam([{"kind": "circle", "x": 0, "y": 0}]),
        [{"kind": "circle", "x": 100, "y": 100}],
        budget=1,
    )
    assert report["termination_reason"] == "budget_exceeded"
    assert report["iterations_used"] == 1


def test_unresolved_beam_is_semantic_conflict() -> None:
    report = optimize_geometry_ir({"status": "semantic_conflict", "hypotheses": []}, [])
    assert report["status"] == "not_reachable"
    assert report["reason"] == "semantic_conflict"
