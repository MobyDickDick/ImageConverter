from __future__ import annotations

import contextlib
import importlib
import sys
from pathlib import Path

from src.iccFs.vendoredSitePackagesDirs import vendoredSitePackagesDirs


def loadOptionalModule(moduleName: str):
    """Import optional dependencies, including repo-vendored site-packages."""
    attemptedPaths: list[Path] = []
    try:
        return importlib.import_module(moduleName)
    except Exception as exc:  # pragma: no cover
        lastExc: BaseException = exc
        sys.modules.pop(moduleName, None)

    for sitePackages in vendoredSitePackagesDirs():
        attemptedPaths.append(sitePackages)
        pathStr = str(sitePackages)
        added = False
        if pathStr not in sys.path:
            sys.path.insert(0, pathStr)
            added = True
        try:
            return importlib.import_module(moduleName)
        except Exception as exc:  # pragma: no cover
            lastExc = exc
            sys.modules.pop(moduleName, None)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(pathStr)

    core = sys.modules.get("src.iccFs.mF.imageCompositeConverterCore")
    if core is not None and hasattr(core, "OPTIONAL_DEPENDENCY_ERRORS"):
        attempted = ", ".join(str(p) for p in attemptedPaths) or "<none>"
        core.OPTIONAL_DEPENDENCY_ERRORS[moduleName] = f"{type(lastExc).__name__}: {lastExc} (paths: {attempted})"
    return None


load_optional_module = loadOptionalModule


__all__ = ["loadOptionalModule", "load_optional_module"]
