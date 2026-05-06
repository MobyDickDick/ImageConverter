"""Simple environment diagnostics for ImageConverter dependencies."""

from __future__ import annotations

import importlib
import platform
import sys
from dataclasses import dataclass


@dataclass
class ModuleCheck:
    label: str
    module_name: str
    attr: str | None = None


def _read_version(module, attr: str | None) -> str:
    if attr and hasattr(module, attr):
        return str(getattr(module, attr))
    return str(getattr(module, "__version__", "n/a"))


def main() -> int:
    checks = [
        ModuleCheck("PyMuPDF", "fitz", "VersionBind"),
        ModuleCheck("NumPy", "numpy"),
        ModuleCheck("Pillow", "PIL"),
        ModuleCheck("OpenCV", "cv2"),
    ]

    print("ImageConverter environment check")
    print(f"Python: {sys.version.split()[0]} ({platform.system()} {platform.machine()})")
    print(f"Executable: {sys.executable}")
    print()

    has_error = False
    for check in checks:
        try:
            module = importlib.import_module(check.module_name)
            version = _read_version(module, check.attr)
            module_path = getattr(module, "__file__", "n/a")
            print(f"[OK]  {check.label:<8} version={version} path={module_path}")
        except Exception as exc:  # deliberate broad catch for diagnostics
            has_error = True
            print(f"[ERR] {check.label:<8} module={check.module_name} error={exc}")

    print()
    if has_error:
        print("Result: FAILED")
        print(
            "Hint: Verify Python version/ABI compatibility (e.g. vendored linux-py310 packages under Python 3.12+ will fail)."
        )
        return 1

    print("Result: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
