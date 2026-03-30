from __future__ import annotations

from src.image_composite_converterFiles.convert_rangeFiles._sync_core_overridesFile import _sync_core_overrides


def convert_range(*args, **kwargs):
    import src.image_composite_converter as _m

    _sync_core_overrides()
    return _m._core.convert_range(*args, **kwargs)
