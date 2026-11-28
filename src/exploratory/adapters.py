"""Narrow adapters to existing rendering and full-image quality metrics."""

def scene_geometry(scene):
    """Reuse the legacy math kernel, without parser or fixed inventory limits."""
    import numpy as np
    from src.iCCModules.imageCompositeConverterSceneProgram import STRIDE, geometry

    program = {"objects": [{"id": obj.id, "kind": obj.kind} for obj in scene.objects]}
    values = np.zeros((len(scene.objects), STRIDE))
    for row, obj in zip(values, scene.objects):
        row[:5] = (*obj.center, *obj.size, obj.angle)
    shapes = geometry(program, values, scene.width, scene.height)
    # Legacy geometry also supplies legacy paint/minimum-stroke metadata.
    # Replace that metadata with the actual, unconstrained scene paint.
    for obj in scene.objects:
        shapes[obj.id]["paint"] = obj.paint
        shapes[obj.id]["stroke"] = (obj.paint.stroke_width * min(scene.width, scene.height)
                                     if obj.paint.stroke is not None else 0.)
    return shapes


def render(svg, width, height):
    import cv2
    import fitz
    import numpy as np
    from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
    return render_svg_to_numpy_inprocess(
        svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def evaluate(reference, raster, svg):
    from src.iCCModules.imageCompositeConverterAdaptiveSearch import (
        vector_candidate_quality, vector_quality_score,
    )
    quality = vector_candidate_quality(reference, raster, svg)
    return quality, float(vector_quality_score(quality))
