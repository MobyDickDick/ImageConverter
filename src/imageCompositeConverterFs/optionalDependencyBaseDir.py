from __future__ import annotations

from pathlib import Path


def optionalDependencyBaseDir() -> Path:
    """Return repository root used for vendored dependency discovery."""
    return Path(__file__).resolve().parents[2]
