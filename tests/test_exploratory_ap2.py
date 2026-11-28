"""AP 2: representation contracts and real rendering; run in GitHub Actions."""
from dataclasses import FrozenInstanceError
import json
import math
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.exploratory import Candidate, Paint, Primitive, Relation, Scene, convert
from src.exploratory import adapters
from src.exploratory.engine import _native_svg
from src.exploratory.scene import KINDS


def test_structure_edits_are_independent_and_have_no_inventory_cap():
    scene = Scene(160, 80)
    for i in range(24):
        scene = scene.add(Primitive(f"p{i}", KINDS[i % len(KINDS)]))
    related = scene.with_relations((Relation("parallel", ("p0", "p1")),
                                    Relation("mirror", ("p2", "p3"))))
    changed = related.update("p0", kind="line", center=(.1, .2))
    assert changed.object("p0").id == related.object("p0").id
    assert related.object("p0").kind == "circle"
    removed = changed.remove("p0")
    assert len(removed.objects) == 23
    assert removed.relations == (related.relations[1],)
    assert len(changed.objects) == 24 and len(changed.relations) == 2
    assert len(scene.geometry()) == 24
    for obj in tuple(removed.objects):
        removed = removed.remove(obj.id)
    assert removed.objects == removed.relations == ()
    assert removed.geometry() == {}


def test_roundtrip_preserves_geometry_paint_order_and_relations():
    objects = [Primitive(f"p{i}", kind, center=[.2 + i * .1, .5],
                         size=[.1, .3], angle=.125,
                         paint=Paint(fill=[30, 40, 50], stroke=[100, 120, 140]))
               for i, kind in enumerate(KINDS)]
    scene = Scene(200, 100, objects, [Relation("parallel", ["p0", "p1"])])
    restored = Scene.from_dict(json.loads(json.dumps(scene.to_dict(), allow_nan=False)))
    assert restored == scene
    assert restored.to_svg() == scene.to_svg()
    assert restored.relation_errors() == scene.relation_errors()
    objects.clear()
    assert len(scene.objects) == 6
    with pytest.raises(FrozenInstanceError):
        scene.objects[0].kind = "rect"
    shape = restored.geometry()["p0"]
    shape["center"][:] = 0
    np.testing.assert_allclose(restored.geometry()["p0"]["center"], [40, 50])


@pytest.mark.parametrize("kind", KINDS)
def test_native_geometry_export_on_non_square_canvas(kind):
    obj = Primitive("shape", kind, center=(.4, .6), size=(.2, .4), angle=.25,
                    paint=Paint((10, 20, 30), (70, 80, 90), .02))
    scene = Scene(200, 100, (obj,))
    svg = scene.to_svg()
    assert _native_svg(svg)
    nodes = {node.get("id"): node for node in ET.fromstring(svg)}
    shape = nodes["shape"]
    assert shape.get("stroke-width") == "2"
    assert shape.get("fill") == "#0a141e"
    if kind == "circle":
        assert float(shape.get("r")) == 20
    elif kind in {"square", "rect"}:
        assert float(shape.get("width")) == float(shape.get("height")) == 40
    elif kind == "ellipse":
        assert float(shape.get("rx")) == float(shape.get("ry")) == 20
    elif kind == "line":
        np.testing.assert_allclose([float(shape.get(k)) for k in ("x1", "y1", "x2", "y2")],
                                   [80, 40, 80, 80], atol=1e-10)
    else:
        points = np.array([[float(v) for v in p.split(",")] for p in shape.get("points").split()])
        np.testing.assert_allclose(points, [[80, 80], [60, 40], [100, 40]], atol=1e-10)


def test_no_parser_dependency_or_implicit_geometry_repair(monkeypatch):
    from src.iCCModules import imageCompositeConverterSceneProgram as legacy
    def forbidden(*args):
        raise AssertionError("Description parser must not be called")
    monkeypatch.setattr(legacy, "scene_program", forbidden)
    scene = Scene(100, 80, (Primitive("outside", "rect", center=(-.2, 1.2), size=(2., 3.),
                                     paint=Paint(stroke=(0, 0, 0), stroke_width=0)),))
    shape = scene.geometry()["outside"]
    np.testing.assert_allclose(shape["center"], [-20, 96])
    assert shape["stroke"] == 0
    assert 'stroke-width="0"' in scene.to_svg()


def test_relations_measure_hypotheses_without_moving_shapes():
    a = Primitive("a", "line", center=(.25, .4), size=(.2, .2), angle=.125)
    b = Primitive("b", "line", center=(.75, .4), size=(.2, .2), angle=.375)
    scene = Scene(200, 100, (a, b), (Relation("mirror", ("a", "b")),))
    assert scene.relation_errors() == pytest.approx((0.,), abs=1e-14)
    assert scene.update("b", center=(.7, .4)).relation_errors()[0] > 0
    assert scene.update("b", angle=.125).relation_errors()[0] > .9
    assert scene.objects == (a, b)
    horizontal = Scene(200, 100, (a, Primitive("b", "line", center=(.25, .6), angle=.875,
                                               size=(.2, .2))),
                       (Relation("mirror", ("a", "b"), axis="horizontal"),))
    assert horizontal.relation_errors() == pytest.approx((0.,), abs=1e-14)
    parallel = scene.with_relations((Relation("parallel", ("a", "b")),))
    assert parallel.relation_errors() == pytest.approx((1.,))
    assert parallel.update("b", angle=.625).relation_errors() == pytest.approx((0.,), abs=1e-14)


@pytest.mark.parametrize("kind", ["contact", "coincident"])
def test_shared_anchors_and_type_change_validation(kind):
    scene = Scene(100, 100, (Primitive("a", "line", center=(.3, .5), size=(.4, .4)),
                             Primitive("b", "line", center=(.7, .5), size=(.4, .4))),
                  (Relation(kind, ("a", "b"), ("end", "start")),))
    assert scene.relation_errors() == pytest.approx((0.,), abs=1e-14)
    assert scene.update("b", center=(.8, .5)).relation_errors() == pytest.approx((.01,))
    with pytest.raises(ValueError, match="anchor"):
        scene.update("a", kind="circle")
    assert scene.with_relations(()).update("a", kind="circle").object("a").kind == "circle"


def test_boundary_contact_and_triangle_apex():
    scene = Scene(200, 100, (Primitive("a", "circle", center=(.25, .5), size=(.2, .4)),
                             Primitive("b", "rect", center=(.45, .5), size=(.2, .4))),
                  (Relation("contact", ("a", "b"), ("right", "left")),))
    assert scene.relation_errors() == pytest.approx((0.,), abs=1e-14)
    triangle = Scene(100, 100, (Primitive("t", "triangle", size=(.4, .4)),
                                Primitive("l", "line", center=(.8, .5), size=(.2, .2))),
                     (Relation("coincident", ("t", "l"), ("apex", "start")),))
    assert triangle.relation_errors() == pytest.approx((0.,), abs=1e-14)


@pytest.mark.parametrize("factory", [
    lambda: Primitive("bad id", "circle"),
    lambda: Primitive("a", "path"),
    lambda: Primitive("a", "circle", center=(math.nan, .5)),
    lambda: Primitive("a", "circle", angle=math.inf),
    lambda: Primitive("a", "circle", size=(0, .5)),
    lambda: Paint(fill=(256, 0, 0)),
    lambda: Paint(stroke_width=-1),
    lambda: Scene(0, 100),
    lambda: Scene(100, 100, (Primitive("a", "line"), Primitive("a", "rect"))),
    lambda: Scene(100, 100, (), (Relation("parallel", ("a", "b")),)),
    lambda: Relation("unknown", ("a", "b")),
    lambda: Relation("parallel", ("a", "a")),
    lambda: Relation("mirror", ("a", "b"), offset=math.nan),
])
def test_invalid_scene_data_fails_early(factory):
    with pytest.raises(ValueError):
        factory()


def test_invalid_structure_edits_do_not_change_source():
    scene = Scene(100, 100, (Primitive("a", "rect"), Primitive("b", "circle")))
    with pytest.raises(ValueError):
        scene.add(Primitive("a", "ellipse"))
    with pytest.raises(ValueError):
        scene.reorder(("a", "a"))
    with pytest.raises(ValueError):
        scene.update("a", id="b")
    with pytest.raises(KeyError):
        scene.remove("missing")
    assert [o.id for o in scene.objects] == ["a", "b"]


def test_real_rendering_paint_order_and_all_primitives():
    objects = tuple(Primitive(f"p{i}", kind, center=(.1 + i * .16, .5), size=(.12, .5),
                              angle=.04, paint=Paint((200, 30, 40), (10, 80, 20), .02))
                    for i, kind in enumerate(KINDS))
    scene = Scene(180, 90, objects)
    raster = adapters.render(scene.to_svg(), 180, 90)
    assert raster.shape == (90, 180, 3) and raster.dtype == np.uint8
    # Every disjoint primitive must actually leave foreground pixels.
    for obj in objects:
        x = round(obj.center[0] * 180)
        assert np.any(raster[15:75, x-10:x+11] < 180)
    overlap = Scene(100, 100, (Primitive("red", "rect", size=(.8, .8), paint=Paint((255, 0, 0))),
                                Primitive("blue", "circle", size=(.4, .4), paint=Paint((0, 0, 255)))))
    np.testing.assert_array_equal(adapters.render(overlap.to_svg(), 100, 100)[50, 50], [255, 0, 0])
    np.testing.assert_array_equal(adapters.render(overlap.reorder(("blue", "red")).to_svg(), 100, 100)[50, 50],
                                  [0, 0, 255])


@pytest.mark.parametrize("description", ["", "unbekannte Satzstruktur mit neuen Formen"])
def test_structural_candidates_compete_and_poor_real_draft_survives(description):
    image = np.full((80, 100, 3), 255, dtype=np.uint8)
    image[20:60, 30:70] = (0, 0, 255)
    initial = Scene(100, 80, (Primitive("a", "ellipse", center=(.1, .1), size=(.1, .1)),))
    revised = initial.update("a", kind="rect").add(Primitive("b", "triangle", center=(.8, .8)))
    def source(*args):
        yield Candidate.from_scene(initial, "initial")
        yield Candidate.from_scene(revised, "structure_edit")
    improvements = []
    result = convert(image, description, sources=[source], seconds=60,
                     on_improvement=lambda candidate, quality: improvements.append(candidate))
    assert result.evaluated == result.renderings == 2, result.errors
    assert result.best.scene in (initial, revised)
    assert result.best.svg == result.best.scene.to_svg()
    assert not result.pixel_quality_passed and not result.released
    assert result.stop_reason == "sources_exhausted" and improvements


def test_canvas_mismatch_is_rejected_before_rendering():
    result = convert(np.zeros((10, 10, 3), dtype=np.uint8),
                     sources=[lambda *args: [Candidate.from_scene(Scene(20, 10))]])
    assert result.rejected == 1 and result.renderings == 0
    assert "canvas" in result.errors[0]
