"""Narrow adapters to existing rendering and full-image quality metrics."""

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
