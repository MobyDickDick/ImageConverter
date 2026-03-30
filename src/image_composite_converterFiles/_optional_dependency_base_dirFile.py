from __future__ import annotations

from pathlib import Path


def _optional_dependency_base_dir() -> Path:
    """Return the repository root used for vendored dependency discovery."""
    return Path(__file__).resolve().parents[2]
