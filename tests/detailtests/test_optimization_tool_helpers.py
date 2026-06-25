from __future__ import annotations

import pytest

from src.iCCModules.imageCompositeConverterOptimizationTool import (
    OptimizationProblem,
    OptimizationVariable,
    evaluateCandidateGridImpl,
)


def test_evaluate_candidate_grid_finds_lowest_error() -> None:
    result = evaluateCandidateGridImpl(
        OptimizationProblem(
            variables=(OptimizationVariable("width", 1.0, 5.0, current=4.0),),
            error_fn=lambda params: abs(params["width"] - 2.5),
        ),
        {"width": [1.0, 2.5, 5.0]},
    )

    assert result.converged is True
    assert result.parameters == {"width": 2.5}
    assert result.error == 0.0
    assert result.evaluations == 4
    assert result.stop_reason == "grid_exhausted"


def test_evaluate_candidate_grid_rejects_unknown_variable() -> None:
    with pytest.raises(ValueError, match="Unknown candidate"):
        evaluateCandidateGridImpl(
            OptimizationProblem(
                variables=(OptimizationVariable("width", 1.0, 5.0),),
                error_fn=lambda _params: 0.0,
            ),
            {"height": [2.0]},
        )
