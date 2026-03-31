from __future__ import annotations

import os
from pathlib import Path


def vendoredSitePackagesDirs() -> list[Path]:
    """Return repo-local site-packages directories that may contain bundled deps."""
    import src.imageCompositeConverter as module

    base = module._optional_dependency_base_dir()
    linuxCandidates = [
        base / "vendor" / "linux" / "site-packages",
        base / "vendor" / "linux-py310" / "site-packages",
        base / "vendor" / "linux-py311" / "site-packages",
        base / "vendor" / "linux-py312" / "site-packages",
        base / "vendor" / "linux-py313" / "site-packages",
        base / "vendor" / "linux-py314" / "site-packages",
    ]
    windowsCandidates = [
        base / "vendor" / "win" / "site-packages",
        base / "vendor" / "win-py310" / "site-packages",
        base / "vendor" / "win-py311" / "site-packages",
        base / "vendor" / "win-py312" / "site-packages",
        base / "vendor" / "win-py313" / "site-packages",
        base / "vendor" / "win-py314" / "site-packages",
        base / ".venv" / "Lib" / "site-packages",
    ]
    posixVenvCandidates = [
        base / ".venv" / "lib" / "python3.10" / "site-packages",
        base / ".venv" / "lib" / "python3.11" / "site-packages",
        base / ".venv" / "lib" / "python3.12" / "site-packages",
        base / ".venv" / "lib" / "python3.13" / "site-packages",
        base / ".venv" / "lib" / "python3.14" / "site-packages",
    ]
    if os.name == "nt":
        candidates = windowsCandidates + linuxCandidates + posixVenvCandidates
    else:
        candidates = linuxCandidates + posixVenvCandidates + windowsCandidates

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


def vendored_site_packages_dirs() -> list[Path]:
    """Backward-compatible snake_case alias."""
    return vendoredSitePackagesDirs()


__all__ = ["vendoredSitePackagesDirs", "vendored_site_packages_dirs"]
