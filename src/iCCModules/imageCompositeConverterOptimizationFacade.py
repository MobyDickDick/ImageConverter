"""Optimization hook bundle for the conversion pipeline.

This module introduces a single architecture seam for optimization-related
callbacks so callers do not need to thread many function arguments manually.
"""

from __future__ import annotations

from dataclasses import dataclass

from .imageCompositeConverterGeometryBrackets import (
    optimizeCircleCenterBracketImpl,
    optimizeCircleRadiusBracketImpl,
)
from .imageCompositeConverterOptimizationColor import optimizeElementColorBracketImpl
from .imageCompositeConverterOptimizationGeometry import (
    optimizeElementExtentBracketImpl,
    optimizeElementWidthBracketImpl,
)
from .imageCompositeConverterOptimizationGlobalSearch import optimizeGlobalParameterVectorSamplingImpl


@dataclass(frozen=True)
class OptimizationHooks:
    optimize_element_width_bracket_fn: object
    optimize_element_extent_bracket_fn: object
    optimize_circle_center_bracket_fn: object
    optimize_circle_radius_bracket_fn: object
    optimize_global_parameter_vector_sampling_fn: object
    optimize_element_color_bracket_fn: object


def buildDefaultOptimizationHooksImpl() -> OptimizationHooks:
    """Return the default optimization callback set used by element validation."""
    return OptimizationHooks(
        optimize_element_width_bracket_fn=optimizeElementWidthBracketImpl,
        optimize_element_extent_bracket_fn=optimizeElementExtentBracketImpl,
        optimize_circle_center_bracket_fn=optimizeCircleCenterBracketImpl,
        optimize_circle_radius_bracket_fn=optimizeCircleRadiusBracketImpl,
        optimize_global_parameter_vector_sampling_fn=optimizeGlobalParameterVectorSamplingImpl,
        optimize_element_color_bracket_fn=optimizeElementColorBracketImpl,
    )
