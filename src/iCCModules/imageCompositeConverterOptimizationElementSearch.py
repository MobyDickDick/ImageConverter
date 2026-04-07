"""Element-search optimization helpers for primitive candidate fitting."""

from __future__ import annotations

import random
from typing import Callable, Protocol


class CandidateLike(Protocol):
    shape: str
    cx: float
    cy: float
    w: float
    h: float


def renderCandidateMaskImpl(candidate: CandidateLike, width: int, height: int) -> list[list[int]]:
    mask = [[0 for _ in range(width)] for _ in range(height)]
    rx = max(1.0, (candidate.w + candidate.h) / 4.0) if candidate.shape == "circle" else max(1.0, candidate.w / 2.0)
    ry = rx if candidate.shape == "circle" else max(1.0, candidate.h / 2.0)
    inv_rx2 = 1.0 / (rx * rx)
    inv_ry2 = 1.0 / (ry * ry)
    for y in range(height):
        for x in range(width):
            if ((x - candidate.cx) ** 2) * inv_rx2 + ((y - candidate.cy) ** 2) * inv_ry2 <= 1.0:
                mask[y][x] = 1
    return mask


def scoreCandidateImpl(
    target: list[list[int]],
    candidate: CandidateLike,
    *,
    render_candidate_mask_fn: Callable[[CandidateLike, int, int], list[list[int]]],
    iou_fn: Callable[[list[list[int]], list[list[int]]], float],
) -> float:
    return iou_fn(target, render_candidate_mask_fn(candidate, len(target[0]), len(target)))


def randomNeighborImpl(
    base: CandidateLike,
    scale: float,
    rng: random.Random,
    *,
    candidate_factory: Callable[[str, float, float, float, float], CandidateLike],
) -> CandidateLike:
    return candidate_factory(
        base.shape,
        base.cx + rng.uniform(-scale, scale),
        base.cy + rng.uniform(-scale, scale),
        max(1.0, base.w + rng.uniform(-scale, scale) * 1.4),
        max(1.0, base.h + rng.uniform(-scale, scale) * 1.4),
    )


def optimizeElementImpl(
    target: list[list[int]],
    init: CandidateLike,
    *,
    max_iter: int,
    plateau_limit: int,
    seed: int,
    score_candidate_fn: Callable[[list[list[int]], CandidateLike], float],
    random_neighbor_fn: Callable[[CandidateLike, float, random.Random], CandidateLike],
) -> tuple[CandidateLike, float]:
    rng = random.Random(seed)
    best = init
    best_score = score_candidate_fn(target, best)
    scale = max(1.0, max(best.w, best.h) * 0.2)
    plateau = 0
    for _ in range(max_iter):
        cand = random_neighbor_fn(best, scale, rng)
        score = score_candidate_fn(target, cand)
        if score >= best_score:
            best, best_score, plateau = cand, score, 0
        else:
            plateau += 1
        if plateau > plateau_limit:
            scale = max(0.5, scale * 0.7)
            plateau = 0
    return best, best_score
