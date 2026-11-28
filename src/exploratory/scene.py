"""Immutable, description-independent scene values for structural search (AP 2).

Coordinates/sizes are canvas fractions, angles are turns. Object order is
paint order. IDs survive parameter/type edits. There is no object-count limit.
"""
from dataclasses import asdict, dataclass, replace
import math
from numbers import Real
import re
from xml.etree import ElementTree as ET

from . import adapters

KINDS = ("circle", "ellipse", "rect", "square", "triangle", "line")
RELATIONS = ("mirror", "parallel", "contact", "coincident")
ANCHORS = ("center", "left", "right", "top", "bottom", "start", "end",
           "apex", "base_left", "base_right", "corner_0", "corner_1",
           "corner_2", "corner_3")


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def _pair(value, name):
    values = tuple(value)
    if len(values) != 2:
        raise ValueError(f"{name} must have two coordinates")
    return tuple(_number(v, name) for v in values)


def _color(value):
    if value is None:
        return None
    values = tuple(value)
    if len(values) != 3 or any(isinstance(v, bool) or not isinstance(v, Real)
                               or not math.isfinite(v) or int(v) != v
                               or not 0 <= v <= 255 for v in values):
        raise ValueError("Colors must be RGB integer triples in [0, 255]")
    return tuple(int(v) for v in values)


@dataclass(frozen=True)
class Paint:
    fill: tuple[int, int, int] | None = (0, 0, 0)
    stroke: tuple[int, int, int] | None = None
    # Fraction of min(canvas width, canvas height); zero means no stroke.
    stroke_width: float = .01

    def __post_init__(self):
        object.__setattr__(self, "fill", _color(self.fill))
        object.__setattr__(self, "stroke", _color(self.stroke))
        width = _number(self.stroke_width, "stroke_width")
        if width < 0:
            raise ValueError("stroke_width must be nonnegative")
        object.__setattr__(self, "stroke_width", width)


@dataclass(frozen=True)
class Primitive:
    id: str
    kind: str
    center: tuple[float, float] = (.5, .5)
    size: tuple[float, float] = (.25, .25)
    angle: float = 0.
    paint: Paint = Paint()

    def __post_init__(self):
        if not isinstance(self.id, str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", self.id) is None:
            raise ValueError("Object IDs must be nonempty SVG identifiers")
        if self.kind not in KINDS:
            raise ValueError(f"Unsupported primitive kind: {self.kind}")
        object.__setattr__(self, "center", _pair(self.center, "center"))
        size = _pair(self.size, "size")
        if min(size) <= 0:
            raise ValueError("Both size coordinates must be positive")
        object.__setattr__(self, "size", size)
        object.__setattr__(self, "angle", _number(self.angle, "angle") % 1.)
        if not isinstance(self.paint, Paint):
            raise TypeError("paint must be Paint")

    def supports_anchor(self, name):
        if name == "center":
            return True
        if self.kind == "line":
            return name in {"start", "end"}
        if self.kind == "triangle":
            return name in {"apex", "base_left", "base_right"}
        if name in {"left", "right", "top", "bottom"}:
            return True
        return self.kind in {"rect", "square"} and name in {f"corner_{i}" for i in range(4)}


@dataclass(frozen=True)
class Relation:
    """A geometric hypothesis; not an implicit semantic release condition.

    Contact/coincident join selected anchors. Mirror uses a global axis at
    `offset`, measured as a fraction of canvas width/height.
    """
    kind: str
    objects: tuple[str, str]
    anchors: tuple[str, str] = ("center", "center")
    axis: str = "vertical"
    offset: float = .5

    def __post_init__(self):
        if self.kind not in RELATIONS:
            raise ValueError(f"Unsupported relation kind: {self.kind}")
        objects, anchors = tuple(self.objects), tuple(self.anchors)
        if len(objects) != 2 or any(not isinstance(v, str) for v in objects) or objects[0] == objects[1]:
            raise ValueError("A relation needs two distinct object IDs")
        if len(anchors) != 2 or any(v not in ANCHORS for v in anchors):
            raise ValueError("Unsupported relation anchors")
        if self.axis not in {"vertical", "horizontal"}:
            raise ValueError("Unsupported mirror axis")
        object.__setattr__(self, "objects", objects)
        object.__setattr__(self, "anchors", anchors)
        object.__setattr__(self, "offset", _number(self.offset, "offset"))


@dataclass(frozen=True)
class Scene:
    width: int
    height: int
    objects: tuple[Primitive, ...] = ()
    relations: tuple[Relation, ...] = ()
    background: tuple[int, int, int] | None = (255, 255, 255)

    def __post_init__(self):
        if any(type(v) is not int or v < 1 for v in (self.width, self.height)):
            raise ValueError("Canvas dimensions must be positive integers")
        objects, relations = tuple(self.objects), tuple(self.relations)
        if any(not isinstance(obj, Primitive) for obj in objects):
            raise TypeError("objects must contain Primitive values")
        by_id = {obj.id: obj for obj in objects}
        if len(by_id) != len(objects):
            raise ValueError("Duplicate object ID")
        for relation in relations:
            if not isinstance(relation, Relation):
                raise TypeError("relations must contain Relation values")
            if any(key not in by_id for key in relation.objects):
                raise ValueError("Relation references a missing object")
            if relation.kind in {"contact", "coincident"} and any(
                    not by_id[key].supports_anchor(anchor)
                    for key, anchor in zip(relation.objects, relation.anchors)):
                raise ValueError("Relation anchor is incompatible with its object")
        object.__setattr__(self, "objects", objects)
        object.__setattr__(self, "relations", relations)
        object.__setattr__(self, "background", _color(self.background))

    def add(self, obj):
        return replace(self, objects=(*self.objects, obj))

    def remove(self, object_id):
        """Remove an object and incident relations, preserving all other IDs."""
        self.object(object_id)
        return replace(self, objects=tuple(o for o in self.objects if o.id != object_id),
                       relations=tuple(r for r in self.relations if object_id not in r.objects))

    def object(self, object_id):
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        raise KeyError(object_id)

    def update(self, object_id, **changes):
        """Edit parameters/type; incompatible relations require an explicit edit."""
        if "id" in changes:
            raise ValueError("Object IDs are stable; remove/add to change an ID")
        updated = replace(self.object(object_id), **changes)
        return replace(self, objects=tuple(updated if o.id == object_id else o for o in self.objects))

    def reorder(self, object_ids):
        ids = tuple(object_ids)
        if len(ids) != len(self.objects) or set(ids) != {o.id for o in self.objects}:
            raise ValueError("Paint order must contain every object exactly once")
        return replace(self, objects=tuple(self.object(key) for key in ids))

    def with_relations(self, relations):
        return replace(self, relations=tuple(relations))

    def geometry(self):
        """Fresh shapes from the existing, description-independent math kernel."""
        return adapters.scene_geometry(self)

    def relation_errors(self):
        from .relations import relation_errors
        return relation_errors(self)

    def to_dict(self):
        """JSON-compatible checkpoint data; no executable payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        data["objects"] = tuple(Primitive(**dict(obj, paint=Paint(**obj["paint"])))
                                for obj in data.get("objects", ()))
        data["relations"] = tuple(Relation(**rel) for rel in data.get("relations", ()))
        return cls(**data)

    def to_svg(self):
        """Self-contained solid-paint SVG, accepted by the AP 1 vector gate."""
        def number(value):
            return format(float(value), ".12g")

        def color(value):
            return "none" if value is None else "#" + "".join(f"{v:02x}" for v in value)

        root = ET.Element("svg", xmlns="http://www.w3.org/2000/svg",
                          width=str(self.width), height=str(self.height),
                          viewBox=f"0 0 {self.width} {self.height}")
        if self.background is not None:
            ET.SubElement(root, "rect", width=str(self.width), height=str(self.height),
                          fill=color(self.background), **{"data-role": "background"})
        shapes = self.geometry()
        for obj in self.objects:
            shape = shapes[obj.id]
            cx, cy = shape["center"]
            sx, sy = shape["size"]
            attrs = dict(id=obj.id, fill=color(obj.paint.fill), stroke=color(obj.paint.stroke))
            attrs["stroke-width"] = number(obj.paint.stroke_width * min(self.width, self.height))
            attrs["stroke-linejoin"] = "round"
            if obj.kind == "circle":
                tag = "circle"
                attrs.update(cx=number(cx), cy=number(cy), r=number(sx / 2))
            elif obj.kind == "ellipse":
                tag = "ellipse"
                attrs.update(cx=number(cx), cy=number(cy), rx=number(sx / 2), ry=number(sy / 2))
            elif obj.kind in {"rect", "square"}:
                tag = "rect"
                attrs.update(x=number(cx - sx / 2), y=number(cy - sy / 2),
                             width=number(sx), height=number(sy))
            elif obj.kind == "line":
                tag = "line"
                (x1, y1), (x2, y2) = shape["points"]
                attrs.update(x1=number(x1), y1=number(y1), x2=number(x2), y2=number(y2))
            else:
                tag = "polygon"
                attrs["points"] = " ".join(f"{number(x)},{number(y)}" for x, y in shape["points"])
            if obj.kind in {"ellipse", "rect", "square"}:
                attrs["transform"] = f"rotate({number(obj.angle * 360)} {number(cx)} {number(cy)})"
            ET.SubElement(root, tag, attrs)
        return ET.tostring(root, encoding="unicode")
