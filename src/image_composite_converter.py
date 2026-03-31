"""Backward-compatible wrapper for the Polish-notation module name.

New code should import ``src.imageCompositeConverter``.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Bootstrap attributes used while ``src.imageCompositeConverter`` is still importing.
OPTIONAL_DEPENDENCY_ERRORS: dict[str, str] = {}


def _optional_dependency_base_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _vendored_site_packages_dirs() -> list[Path]:
    from src.iccFs.vendored_site_packages_dirs import vendored_site_packages_dirs

    return vendored_site_packages_dirs()


def _clear_partial_module_import(module_name: str) -> None:
    for name in [n for n in tuple(sys.modules) if n == module_name or n.startswith(module_name + ".")]:
        sys.modules.pop(name, None)


def _describe_optional_dependency_error(module_name: str, exc: BaseException, _attempted_paths: list[Path]) -> str:
    return f"{module_name}: {exc}"


import src.imageCompositeConverter as _polish

for _name in dir(_polish):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_polish, _name)

main = _polish.main

if __name__ == "__main__":
    raise SystemExit(main())
