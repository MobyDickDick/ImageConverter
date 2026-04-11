#!/usr/bin/env python3
"""Verify that OpenCV can be imported from repo-local vendor site-packages."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.iCCModules.imageCompositeConverterDependencies import (
    import_with_vendored_fallback,
    vendored_site_packages_dirs,
)


def main() -> int:
    vendor_dirs = vendored_site_packages_dirs()
    print("Discovered vendored site-packages directories:")
    if not vendor_dirs:
        print("  (none)")
    for path in vendor_dirs:
        print(f"  - {path}")

    cv2 = import_with_vendored_fallback("cv2")
    print(f"Imported cv2 version: {getattr(cv2, '__version__', 'unknown')}")
    print(f"Imported cv2 from: {getattr(cv2, '__file__', 'n/a')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
