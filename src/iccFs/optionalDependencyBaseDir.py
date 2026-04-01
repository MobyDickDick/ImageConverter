from __future__ import annotations

from pathlib import Path


def optionalDependencyBaseDir() -> Path:
    """Return repository root used to resolve bundled optional dependencies."""
    return Path(__file__).resolve().parents[2]




optional_dependency_base_dir = optionalDependencyBaseDir


__all__ = ["optionalDependencyBaseDir", "optional_dependency_base_dir"]
