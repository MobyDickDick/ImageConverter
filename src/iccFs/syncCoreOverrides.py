from __future__ import annotations


def sync_core_overrides() -> None:
    """Mirror monkeypatched wrapper globals into the core module before calls."""
    import src.imageCompositeConverter as module

    skipNames = {"convert_range", "main", "_sync_core_overrides", "syncCoreOverrides"}
    for name, value in module.__dict__.items():
        if name in skipNames:
            continue
        if not hasattr(module._core, name):
            continue
        if getattr(module._core, name) is value:
            continue
        setattr(module._core, name, value)


def syncCoreOverrides() -> None:
    """Backward-compatible camelCase alias."""
    sync_core_overrides()
