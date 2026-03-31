from __future__ import annotations

from src.iccFs.sync_core_overrides import sync_core_overrides


def convert_range(*args, **kwargs):
    import src.imageCompositeConverter as module

    sync_core_overrides()
    return module._core.convert_range(*args, **kwargs)
