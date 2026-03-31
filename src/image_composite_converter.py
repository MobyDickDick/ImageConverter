"""Thin CLI entrypoint for the image composite converter.

This module intentionally keeps only the `main` orchestration function and
re-exports the existing converter API from `image_composite_converter_core`.
"""

from __future__ import annotations

import importlib
import sys
import types

import src.imageCompositeConverterFs.mainFiles.image_composite_converter_core as _core
from src.imageCompositeConverterFs.convertRange import convertRange
from src.imageCompositeConverterFs.loadOptionalModule import loadOptionalModule
from src.imageCompositeConverterFs.main import main
from src.imageCompositeConverterFs.optionalDependencyBaseDir import optionalDependencyBaseDir
from src.imageCompositeConverterFs.syncCoreOverrides import syncCoreOverrides
from src.imageCompositeConverterFs.vendoredSitePackagesDirs import vendoredSitePackagesDirs

for _name in dir(_core):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_core, _name)

_optional_dependency_base_dir = optionalDependencyBaseDir
_vendored_site_packages_dirs = vendoredSitePackagesDirs
_load_optional_module = loadOptionalModule
_sync_core_overrides = syncCoreOverrides
convert_range = convertRange

_core._optional_dependency_base_dir = _optional_dependency_base_dir
_core._vendored_site_packages_dirs = _vendored_site_packages_dirs
_core._load_optional_module = _load_optional_module

np = _load_optional_module("numpy")
cv2 = _load_optional_module("cv2")
fitz = _load_optional_module("fitz")
_core.np = np
_core.cv2 = cv2
_core.fitz = fitz


class _CoreSyncModule(types.ModuleType):
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name in {"convert_range", "main", "_sync_core_overrides"}:
            return
        if hasattr(_core, name):
            setattr(_core, name, value)


sys.modules[__name__].__class__ = _CoreSyncModule


if __name__ == "__main__":
    raise SystemExit(main())
