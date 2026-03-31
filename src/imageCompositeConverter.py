"""Thin CLI entrypoint for the image composite converter.

This module intentionally keeps only the `main` orchestration function and
re-exports the existing converter API from `image_composite_converter_core`.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.iccFs.mF.image_composite_converter_core as _core
from src.iccFs.convertRange import convert_range
from src.iccFs.loadOptionalModule import load_optional_module
from src.iccFs.main import main
from src.iccFs.optionalDependencyBaseDir import optional_dependency_base_dir
from src.iccFs.syncCoreOverrides import sync_core_overrides
from src.iccFs.vendoredSitePackagesDirs import vendored_site_packages_dirs

for _name in dir(_core):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_core, _name)

_optional_dependency_base_dir = optional_dependency_base_dir
_vendored_site_packages_dirs = vendored_site_packages_dirs
_load_optional_module = load_optional_module
_sync_core_overrides = sync_core_overrides
convert_range = convert_range

# Polish-notation compatibility aliases for public integration points.
optional_dependency_base_dir = _optional_dependency_base_dir
vendored_site_packages_dirs = _vendored_site_packages_dirs
load_optional_module = _load_optional_module
sync_core_overrides = _sync_core_overrides
convert_range = convert_range

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
        if name in {"convert_range", "convertRange", "main", "_sync_core_overrides", "syncCoreOverrides"}:
            return
        if hasattr(_core, name):
            setattr(_core, name, value)


sys.modules[__name__].__class__ = _CoreSyncModule


if __name__ == "__main__":
    raise SystemExit(main())
