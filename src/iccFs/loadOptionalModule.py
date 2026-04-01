from __future__ import annotations

import contextlib
from pathlib import Path


def loadOptionalModule(moduleName: str):
    """Import optional dependencies, including repo-vendored site-packages."""
    import src.imageCompositeConverter as module

    attemptedPaths: list[Path] = []
    try:
        return module.importlib.import_module(moduleName)
    except Exception as exc:  # pragma: no cover
        lastExc: BaseException = exc
        module.clearPartialModuleImport(moduleName)

    for sitePackages in module.vendoredSitePackagesDirs():
        attemptedPaths.append(sitePackages)
        pathStr = str(sitePackages)
        added = False
        if pathStr not in module.sys.path:
            module.sys.path.insert(0, pathStr)
            added = True
        try:
            return module.importlib.import_module(moduleName)
        except Exception as exc:  # pragma: no cover
            lastExc = exc
            module.clearPartialModuleImport(moduleName)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    module.sys.path.remove(pathStr)

    module.OPTIONAL_DEPENDENCY_ERRORS[moduleName] = module.describeOptionalDependencyError(moduleName, lastExc, attemptedPaths)
    return None


load_optional_module = loadOptionalModule


__all__ = ["loadOptionalModule", "load_optional_module"]
