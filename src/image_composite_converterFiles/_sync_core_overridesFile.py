from __future__ import annotations


def _sync_core_overrides() -> None:
    """Mirror monkeypatched wrapper globals into the core module before calls."""
    import src.image_composite_converter as _m

    skip_names = {"convert_range", "main", "_sync_core_overrides"}
    for name, value in _m.__dict__.items():
        if name in skip_names:
            continue
        if not hasattr(_m._core, name):
            continue
        if getattr(_m._core, name) is value:
            continue
        setattr(_m._core, name, value)
