"""Evaluation-only fault injection; never imported by ordinary conversions.

Two interchangeable providers call the real production renderer. Removing both
removes that capability. A third control adds measurable work without changing
the raster. These controls test attribution, not the value of production bots.
"""
import os
import time


def install():
    from src import imageCompositeConverter as app
    controls = [n for n in os.environ['ICC_COMPONENT_CONTROLS'].split(',') if n]
    render = app.Action.renderSvgToNumpy
    pending_overhead = 'overhead' in controls

    def controlled(*args, **kwargs):
        nonlocal pending_overhead
        if pending_overhead:
            pending_overhead = False
            time.sleep(2.)
        if 'provider_a' in controls:
            return render(*args, **kwargs)
        if 'provider_b' in controls:
            return render(*args, **kwargs)
        return None

    controlled._component_controls = controls
    app.Action.renderSvgToNumpy = staticmethod(controlled)
