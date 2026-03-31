from __future__ import annotations


def syncCoreOverrides() -> None:
    """Mirror monkeypatched wrapper globals into the core module before calls."""
    import src.imageCompositeConverter as module

    skip_names = {"convert_range", "main", "_syncCoreOverrides", "syncCoreOverrides"}
    for name, value in module.__dict__.items():
        if name in skip_names:
            continue
        if not hasattr(module._core, name):
            continue
        if getattr(module._core, name) is value:
            continue
        setattr(module._core, name, value)

