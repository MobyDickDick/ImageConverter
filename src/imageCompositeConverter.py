"""Thin CLI entrypoint for the image composite converter.

This module intentionally keeps only the `main` orchestration function and
re-exports the existing converter API from `imageCompositeConverterCore`.
"""

from __future__ import annotations

import sys
import types
import re
import inspect
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.iccFs.mF.imageCompositeConverterCore as _core
from src.iccFs.convertRange import convertRange
from src.iccFs.loadOptionalModule import loadOptionalModule
from src.iccFs.main import main as _main
from src.iccFs.optionalDependencyBaseDir import optionalDependencyBaseDir
from src.iccFs.syncCoreOverrides import syncCoreOverrides
from src.iccFs.vendoredSitePackagesDirs import vendoredSitePackagesDirs

for _name in dir(_core):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_core, _name)

_optional_dependency_base_dir = optionalDependencyBaseDir
vendoredSitePackagesDirs = vendoredSitePackagesDirs
loadOptionalModule = loadOptionalModule
_syncCoreOverrides = syncCoreOverrides
convertRange = convertRange

# Polish-notation compatibility aliases for public integration points.
optionalDependencyBaseDir = _optional_dependency_base_dir
vendoredSitePackagesDirs = vendoredSitePackagesDirs
loadOptionalModule = loadOptionalModule
syncCoreOverrides = _syncCoreOverrides
convertRange = convertRange


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint wrapper kept local for call-tree export compatibility."""
    return _main(argv)

_core._optional_dependency_base_dir = _optional_dependency_base_dir
_core.vendoredSitePackagesDirs = vendoredSitePackagesDirs
_core.loadOptionalModule = loadOptionalModule

np = loadOptionalModule("numpy")
cv2 = loadOptionalModule("cv2")
fitz = loadOptionalModule("fitz")
_core.np = np
_core.cv2 = cv2
_core.fitz = fitz


def _camelToSnake(name: str) -> str:
    leading = len(name) - len(name.lstrip("_"))
    core = name[leading:]
    converted = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", core).lower()
    return ("_" * leading) + converted


def _snakeToCamel(name: str) -> str:
    leading = len(name) - len(name.lstrip("_"))
    core = name[leading:]
    parts = [part for part in core.split("_") if part]
    if not parts:
        return name
    return ("_" * leading) + parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _installSnakeAliases(namespace: dict[str, object]) -> None:
    for attr_name, value in list(namespace.items()):
        if attr_name.startswith("__") or not any(ch.isupper() for ch in attr_name):
            continue
        alias = _camelToSnake(attr_name)
        if alias not in namespace:
            namespace[alias] = value


def _installClassSnakeAliases(cls: type) -> None:
    for attr_name in dir(cls):
        if attr_name.startswith("__") or not any(ch.isupper() for ch in attr_name):
            continue
        alias = _camelToSnake(attr_name)
        if hasattr(cls, alias):
            continue
        setattr(cls, alias, getattr(cls, attr_name))


def _bridgeClassCamelCallsToSnake(cls: type) -> None:
    for attr_name in dir(cls):
        if attr_name.startswith("__") or not any(ch.isupper() for ch in attr_name):
            continue
        alias = _camelToSnake(attr_name)
        if not hasattr(cls, alias):
            continue
        attr_value = getattr(cls, attr_name)
        if not inspect.isfunction(attr_value):
            continue

        def _forwarder(*args, __alias=alias, **kwargs):
            target = getattr(cls, __alias)
            return target(*args, **kwargs)

        setattr(cls, attr_name, staticmethod(_forwarder))


_installSnakeAliases(globals())
_installClassSnakeAliases(_core.Action)
_bridgeClassCamelCallsToSnake(_core.Action)

# Prefer the contextmanager-wrapped variant when both naming styles exist.
if "_optionalLogCapture" in globals():
    _optional_log_capture = optionalLogCapture


class _CoreSyncModule(types.ModuleType):
    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        camel_name = _snakeToCamel(name)
        if camel_name != name and camel_name in self.__dict__:
            types.ModuleType.__setattr__(self, camel_name, value)
        snake_name = _camelToSnake(name)
        if snake_name != name and snake_name in self.__dict__:
            types.ModuleType.__setattr__(self, snake_name, value)
        if name in {"convert_range", "convertRange", "main", "_syncCoreOverrides", "syncCoreOverrides"}:
            return
        if hasattr(_core, name):
            setattr(_core, name, value)
            return
        if hasattr(_core, camel_name):
            setattr(_core, camel_name, value)
            return
        if hasattr(_core, snake_name):
            setattr(_core, snake_name, value)


sys.modules[__name__].__class__ = _CoreSyncModule


if __name__ == "__main__":
    raise SystemExit(main())
