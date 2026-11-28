"""AP 1: small synchronous search driver, independent of legacy dispatch.

Input and renderer output are uint8 BGR arrays. Time limits are cooperative:
a running provider or renderer cannot be interrupted in this debug-mode API.
"""
from dataclasses import dataclass, field
import math
import time
from xml.etree import ElementTree as ET

import numpy as np

from . import adapters
from .scene import Scene


@dataclass(frozen=True)
class Candidate:
    svg: str
    source: str
    scene: Scene | None = None

    @classmethod
    def from_scene(cls, scene, source="scene"):
        if not isinstance(scene, Scene):
            raise TypeError("scene must be Scene")
        return cls(scene.to_svg(), source, scene)


@dataclass
class ConversionResult:
    best: Candidate | None = None
    quality: dict | None = None
    score: float | None = None
    pixel_quality_passed: bool = False
    # AP 1 has no semantic release mechanism.
    released: bool = False
    stop_reason: str = ""
    elapsed_seconds: float = 0.0
    budget_seconds: float = 0.0
    generated: int = 0
    renderings: int = 0
    evaluated: int = 0
    duplicates: int = 0
    rejected: int = 0
    errors: list[str] = field(default_factory=list)
    description: str = ""


def _native_svg(svg):
    # AP 1 accepts self-contained primitive SVGs only, not arbitrary SVG files.
    root = ET.fromstring(svg)
    allowed = {"svg", "g", "rect", "circle", "ellipse", "line", "polygon", "polyline", "path"}
    def kind(node):
        return node.tag.rsplit("}", 1)[-1]
    if kind(root) != "svg":
        return False
    for node in root.iter():
        if kind(node) not in allowed:
            return False
        for key, value in node.attrib.items():
            key = key.rsplit("}", 1)[-1].lower()
            if key in {"href", "style"} or key.startswith("on") or "url(" in value.lower():
                return False
    return any(kind(node) not in {"svg", "g"} for node in root.iter())


def _seed_candidates(image, description):
    """Minimal raster baseline for AP 1; not the AP 3 perception engine."""
    height, width = image.shape[:2]
    border = np.concatenate((image[0], image[-1], image[:, 0], image[:, -1]))
    background = np.median(border, axis=0)
    def color(bgr):
        return "#" + "".join(f"{int(v):02x}" for v in np.clip(np.rint(bgr[::-1]), 0, 255))
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    bg = f'<rect width="{width}" height="{height}" fill="{color(background)}"/>'
    delta = np.max(abs(image.astype(float) - background), axis=2)
    y, x = np.where(delta > 0)
    if not len(x):
        yield Candidate(head + bg + "</svg>", "uniform_raster")
        return
    # Reject minor background noise only if stronger evidence exists.
    if np.any(delta > 25):
        y, x = np.where(delta > 25)
    x0, y0, x1, y1 = int(x.min()), int(y.min()), int(x.max())+1, int(y.max())+1
    w, h = x1-x0, y1-y0
    fill = color(np.median(image[y, x], axis=0))
    yield Candidate(head + bg + f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="{fill}"/></svg>', "raster_bbox")
    yield Candidate(head + bg + f'<ellipse cx="{x0+w/2}" cy="{y0+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}"/></svg>', "raster_ellipse")


def convert(image, description="", *, seconds=300.0, max_candidates=4096,
            sources=None, render=None, evaluate=None, clock=time.monotonic,
            on_improvement=None):
    """Evaluate competing SVG proposals fairly, without description gates.

    Each source is a callable (image, description) -> iterable of Candidates.
    An exhausted/failed source cannot block the others. Custom providers must
    yield in bounded time. No process, file output or legacy configuration
    is created here. Returned best is a draft, even when pixel quality passes.
    """
    if (not isinstance(image, np.ndarray) or image.dtype != np.uint8
            or image.ndim != 3 or image.shape[2] != 3 or min(image.shape[:2]) < 1):
        raise ValueError("Expected a nonempty uint8 BGR image")
    if not math.isfinite(seconds) or seconds <= 0 or type(max_candidates) is not int or max_candidates < 1:
        raise ValueError("Expected positive finite seconds and positive integer max_candidates")
    if not isinstance(description, str):
        raise TypeError("description must be a string")
    started = clock()
    deadline = started + seconds
    result = ConversionResult(description=description, budget_seconds=seconds)
    render = adapters.render if render is None else render
    evaluate = adapters.evaluate if evaluate is None else evaluate
    from collections import deque
    active = deque()
    # Provider construction is lazy and shares the same deadline.
    def proposals(source):
        yield from source(image, description)
    for source in ((_seed_candidates,) if sources is None else sources):
        active.append(proposals(source))
    seen = set()
    rank = None
    height, width = image.shape[:2]

    while active:
        if clock() >= deadline:
            result.stop_reason = "time_limit"
            break
        if result.generated >= max_candidates:
            result.stop_reason = "candidate_limit"
            break
        iterator = active.popleft()
        try:
            candidate = next(iterator)
        except StopIteration:
            continue
        except Exception as exc:
            result.errors.append(f"provider: {type(exc).__name__}: {exc}")
            continue
        active.append(iterator)
        result.generated += 1
        if clock() >= deadline:
            result.stop_reason = "time_limit"
            break
        try:
            if not isinstance(candidate, Candidate) or not _native_svg(candidate.svg):
                raise ValueError("Not a self-contained native vector candidate")
            if candidate.scene is not None and (candidate.scene.width, candidate.scene.height) != (width, height):
                raise ValueError("Scene canvas does not match the reference raster")
            if candidate.svg in seen:
                result.duplicates += 1
                continue
            seen.add(candidate.svg)
            result.renderings += 1
            raster = render(candidate.svg, width, height)
            if not isinstance(raster, np.ndarray) or raster.shape != image.shape or raster.dtype != np.uint8:
                raise ValueError("Renderer returned an invalid raster")
            quality, score = evaluate(image, raster, candidate.svg)
            if not math.isfinite(score) or type(quality.get("passed")) is not bool:
                raise ValueError("Evaluator returned invalid quality")
            result.evaluated += 1
            current = (not quality["passed"], score)
        except Exception as exc:
            result.rejected += 1
            result.errors.append(f"candidate {getattr(candidate, 'source', '?')}: {type(exc).__name__}: {exc}")
            continue
        if rank is None or current < rank:
            rank = current
            result.best, result.quality, result.score = candidate, quality, score
            result.pixel_quality_passed = quality["passed"]
            if on_improvement is not None:
                on_improvement(candidate, dict(quality))
        if clock() >= deadline:
            result.stop_reason = "time_limit"
            break
        if result.pixel_quality_passed:
            result.stop_reason = "pixel_target"
            break
    if not result.stop_reason:
        result.stop_reason = ("time_limit" if clock() >= deadline else
                              "no_candidate" if result.best is None else "sources_exhausted")
    result.elapsed_seconds = max(0.0, clock()-started)
    return result
