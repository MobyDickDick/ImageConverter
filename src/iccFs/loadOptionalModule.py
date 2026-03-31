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
        module._clear_partial_module_import(moduleName)

    for sitePackages in module._vendored_site_packages_dirs():
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
            module._clear_partial_module_import(moduleName)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    module.sys.path.remove(pathStr)

    module.OPTIONAL_DEPENDENCY_ERRORS[moduleName] = module._describe_optional_dependency_error(moduleName, lastExc, attemptedPaths)
    return None
