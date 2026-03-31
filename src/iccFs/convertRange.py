from __future__ import annotations

from src.iccFs.syncCoreOverrides import syncCoreOverrides


def convertRange(*args, **kwargs):
    import src.image_composite_converter as module

    syncCoreOverrides()
    return module._core.convert_range(*args, **kwargs)
