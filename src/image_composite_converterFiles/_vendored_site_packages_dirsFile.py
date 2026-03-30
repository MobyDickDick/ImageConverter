from __future__ import annotations

import os
from pathlib import Path

from src.image_composite_converterFiles._vendored_site_packages_dirsFiles._optional_dependency_base_dirFile import (
    _optional_dependency_base_dir,
)


def _vendored_site_packages_dirs() -> list[Path]:
    """Return repo-local site-packages directories that may contain bundled deps."""
    base = _optional_dependency_base_dir()
    linux_candidates = [
        base / "vendor" / "linux" / "site-packages",
        base / "vendor" / "linux-py310" / "site-packages",
        base / "vendor" / "linux-py311" / "site-packages",
        base / "vendor" / "linux-py312" / "site-packages",
        base / "vendor" / "linux-py313" / "site-packages",
        base / "vendor" / "linux-py314" / "site-packages",
    ]
    windows_candidates = [
        base / "vendor" / "win" / "site-packages",
        base / "vendor" / "win-py310" / "site-packages",
        base / "vendor" / "win-py311" / "site-packages",
        base / "vendor" / "win-py312" / "site-packages",
        base / "vendor" / "win-py313" / "site-packages",
        base / "vendor" / "win-py314" / "site-packages",
        base / ".venv" / "Lib" / "site-packages",
    ]
    posix_venv_candidates = [
        base / ".venv" / "lib" / "python3.10" / "site-packages",
        base / ".venv" / "lib" / "python3.11" / "site-packages",
        base / ".venv" / "lib" / "python3.12" / "site-packages",
        base / ".venv" / "lib" / "python3.13" / "site-packages",
        base / ".venv" / "lib" / "python3.14" / "site-packages",
    ]
    if os.name == "nt":
        candidates = windows_candidates + linux_candidates + posix_venv_candidates
    else:
        candidates = linux_candidates + posix_venv_candidates + windows_candidates

    seen: set[str] = set()
    existing: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            existing.append(candidate)
    return existing
