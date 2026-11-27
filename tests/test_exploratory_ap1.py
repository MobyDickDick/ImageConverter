"""AP 1 acceptance: deterministic driver tests plus real renderer smoke test."""
import numpy as np
import pytest

from src.exploratory import Candidate, convert


SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><circle cx="4" cy="4" r="2"/></svg>'
OTHER = SVG.replace('r="2"', 'r="3"')
IMAGE = np.full((8, 8, 3), 255, dtype=np.uint8)
IMAGE[2:6, 2:6] = (0, 0, 255)


def render(svg, w, h):
    return IMAGE.copy()


def poor(image, raster, svg):
    return {"passed": False}, 1.0 if svg == SVG else 0.5


@pytest.mark.parametrize("description", ["", "unbekanntes Symbol", "Kreis mit Linien"])
def test_optional_description(description):
    result = convert(IMAGE, description, render=render, evaluate=poor)
    assert result.evaluated == 2
    assert result.best is not None
    assert not result.released and not result.pixel_quality_passed
    assert result.stop_reason == "sources_exhausted"


def test_failed_provider_and_competing_candidates():
    def broken(*args):
        raise ValueError("unsupported description")
    def candidates(*args):
        yield Candidate(SVG, "first")
        yield Candidate(OTHER, "second")
    result = convert(IMAGE, sources=[broken, candidates], render=render, evaluate=poor)
    assert result.best.svg == OTHER
    assert result.evaluated == 2 and result.errors


def test_candidate_budget_and_duplicates():
    def candidates(*args):
        while True:
            yield Candidate(SVG, "repeat")
    result = convert(IMAGE, sources=[candidates], max_candidates=3, render=render, evaluate=poor)
    assert result.stop_reason == "candidate_limit"
    assert (result.generated, result.renderings, result.duplicates) == (3, 1, 2)


def test_deadline_preserves_completed_draft():
    now = [0.]
    def slow(svg, w, h):
        now[0] = 2.
        return IMAGE.copy()
    result = convert(IMAGE, seconds=1., clock=lambda: now[0], render=slow, evaluate=poor)
    assert result.stop_reason == "time_limit"
    assert result.evaluated == 1 and result.best is not None


def test_raster_payload_rejected():
    def candidates(*args):
        yield Candidate('<svg><image href="data:image/png;base64,abc"/></svg>', "invalid")
        yield Candidate(SVG, "valid")
    result = convert(IMAGE, sources=[candidates], render=render, evaluate=poor)
    assert result.rejected == 1 and result.renderings == 1
    assert result.best.svg == SVG


def test_pixel_pass_not_semantic_release():
    result = convert(IMAGE, render=render, evaluate=lambda *args: ({"passed": True}, 0.))
    assert result.stop_reason == "pixel_target"
    assert result.pixel_quality_passed and not result.released


def test_real_existing_renderer_and_metrics():
    pytest.importorskip("cv2")
    pytest.importorskip("fitz")
    result = convert(IMAGE, seconds=10)
    assert result.evaluated >= 1, result.errors
    assert result.best is not None
    assert result.quality["normalized_mse"] < 0.02
    assert not result.released
