from __future__ import annotations

import random
from dataclasses import dataclass

from src.iCCModules import imageCompositeConverterOptimizationElementSearch as helpers


@dataclass
class _Candidate:
    shape: str
    cx: float
    cy: float
    w: float
    h: float


def _iou(a: list[list[int]], b: list[list[int]]) -> float:
    inter = 0
    union = 0
    for y in range(len(a)):
        for x in range(len(a[0])):
            av = bool(a[y][x])
            bv = bool(b[y][x])
            if av and bv:
                inter += 1
            if av or bv:
                union += 1
    return float(inter) / float(union or 1)


def test_render_candidate_mask_and_score() -> None:
    candidate = _Candidate("rect", 3.0, 3.0, 4.0, 4.0)
    mask = helpers.renderCandidateMaskImpl(candidate, width=8, height=8)
    score = helpers.scoreCandidateImpl(mask, candidate, render_candidate_mask_fn=helpers.renderCandidateMaskImpl, iou_fn=_iou)
    assert sum(sum(row) for row in mask) > 0
    assert score == 1.0


def test_optimize_element_impl_improves_score() -> None:
    target = [[0 for _ in range(24)] for _ in range(24)]
    perfect = _Candidate("circle", 12.0, 12.0, 8.0, 8.0)
    target = helpers.renderCandidateMaskImpl(perfect, width=24, height=24)
    init = _Candidate("circle", 8.0, 8.0, 5.0, 5.0)

    best, best_score = helpers.optimizeElementImpl(
        target,
        init,
        max_iter=120,
        plateau_limit=15,
        seed=7,
        score_candidate_fn=lambda t, c: helpers.scoreCandidateImpl(
            t,
            c,
            render_candidate_mask_fn=helpers.renderCandidateMaskImpl,
            iou_fn=_iou,
        ),
        random_neighbor_fn=lambda base, scale, rng: helpers.randomNeighborImpl(
            base,
            scale,
            rng,
            candidate_factory=_Candidate,
        ),
    )

    assert best_score > 0.70
    assert isinstance(best, _Candidate)
    assert best.w >= 1.0 and best.h >= 1.0


def test_random_neighbor_impl_uses_factory() -> None:
    base = _Candidate("rect", 2.0, 2.0, 3.0, 5.0)
    rng = random.Random(1)
    neighbor = helpers.randomNeighborImpl(base, 1.5, rng, candidate_factory=_Candidate)
    assert isinstance(neighbor, _Candidate)
    assert neighbor.shape == "rect"
