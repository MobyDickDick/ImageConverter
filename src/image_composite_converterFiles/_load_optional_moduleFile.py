from __future__ import annotations

import contextlib
import importlib
import sys
from pathlib import Path

from src.image_composite_converterFiles._load_optional_moduleFiles._vendored_site_packages_dirsFile import (
    _vendored_site_packages_dirs,
)


def _load_optional_module(module_name: str):
    """Import optional dependencies, including repo-vendored site-packages."""
    import src.image_composite_converter as _m

    attempted_paths: list[Path] = []
    try:
        return importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
        last_exc: BaseException = exc
        _m._clear_partial_module_import(module_name)

    for site_packages in _vendored_site_packages_dirs():
        attempted_paths.append(site_packages)
        path_str = str(site_packages)
        added = False
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            added = True
        try:
            return importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
            last_exc = exc
            _m._clear_partial_module_import(module_name)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(path_str)

    _m.OPTIONAL_DEPENDENCY_ERRORS[module_name] = _m._describe_optional_dependency_error(module_name, last_exc, attempted_paths)
    return None
