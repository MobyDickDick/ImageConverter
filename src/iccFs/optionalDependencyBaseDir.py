from __future__ import annotations

from pathlib import Path


def optionalDependencyBaseDir() -> Path:
    """Return repository root used for vendored dependency discovery."""
    return Path(__file__).resolve().parents[2]


def optional_dependency_base_dir() -> Path:
    """Backward-compatible snake_case alias."""
    return optionalDependencyBaseDir()


__all__ = ["optionalDependencyBaseDir", "optional_dependency_base_dir"]
