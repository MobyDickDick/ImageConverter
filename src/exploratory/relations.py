"""Geometric relation residuals for diagnostics and future optimizers."""
import math

import numpy as np


def _anchor(shape, name):
    if name == "center":
        return shape["center"]
    indices = {"start": 0, "end": 1, "apex": 0, "base_left": 1,
               "base_right": 2, **{f"corner_{i}": i for i in range(4)}}
    if name in indices:
        return shape["points"][indices[name]]
    # Rotated, local bounding-box side midpoints; these are not contour fitting.
    sx, sy = shape["size"]
    offset = {"left": (-sx / 2, 0), "right": (sx / 2, 0),
              "top": (0, -sy / 2), "bottom": (0, sy / 2)}[name]
    a = shape["angle"]
    rotation = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return shape["center"] + rotation @ offset


def relation_errors(scene):
    """Nonnegative dimensionless residuals, in scene order; no hidden repairs.

    Contact/coincidence compare selected anchors, not arbitrary intersections.
    Stroke extent and occlusion are outside this geometric diagnostic.
    """
    shapes = scene.geometry()
    scale = np.array([scene.width, scene.height], dtype=float)
    errors = []
    for relation in scene.relations:
        first, second = (scene.object(key) for key in relation.objects)
        a, b = (shapes[key] for key in relation.objects)
        if relation.kind in {"contact", "coincident"}:
            delta = (_anchor(a, relation.anchors[0]) - _anchor(b, relation.anchors[1])) / scale
            error = float(delta @ delta)
        elif relation.kind == "parallel":
            error = math.sin(a["angle"] - b["angle"]) ** 2
        else:
            axis = 0 if relation.axis == "vertical" else 1
            center = a["center"].copy() / scale
            center[axis] = 2 * relation.offset - center[axis]
            delta = center - b["center"] / scale
            sizes = (np.asarray(a["size"]) - b["size"]) / scale
            error = float(delta @ delta + sizes @ sizes) + float(first.kind != second.kind)
            if first.kind != "circle":
                expected = math.pi - a["angle"] if axis == 0 else -a["angle"]
                period = 1 if first.kind == "triangle" else 4 if first.kind == "square" else 2
                error += (1 - math.cos(period * (b["angle"] - expected))) / 2
        errors.append(float(error))
    return tuple(errors)
