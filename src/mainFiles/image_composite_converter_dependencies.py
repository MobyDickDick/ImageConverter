"""Dependency bootstrap helpers extracted from the monolith converter module."""

from __future__ import annotations

import subprocess
import sys


def missing_required_image_dependencies(*, cv2_module: object | None, np_module: object | None) -> list[str]:
    """Return pip package names required for runtime conversion."""
    missing: list[str] = []
    if cv2_module is None:
        missing.append("opencv-python-headless")
    if np_module is None:
        missing.append("numpy")
    return missing


def bootstrap_required_image_dependencies(*, cv2_module: object | None, np_module: object | None) -> tuple[list[str], object | None, object | None]:
    """Install missing runtime image dependencies and return updated modules."""
    missing = missing_required_image_dependencies(cv2_module=cv2_module, np_module=np_module)
    if not missing:
        return [], cv2_module, np_module

    cmd = [sys.executable, "-m", "pip", "install", *missing]
    print(f"[INFO] Fehlende Bild-Abhängigkeiten gefunden: {', '.join(missing)}")
    print(f"[INFO] Installiere via: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Automatische Installation fehlgeschlagen. "
            "Bitte Abhängigkeiten manuell installieren oder Proxy/Netzwerk prüfen."
        ) from exc

    if "opencv-python-headless" in missing:
        import cv2 as _cv2

        cv2_module = _cv2
    if "numpy" in missing:
        import numpy as _np

        np_module = _np

    return missing, cv2_module, np_module
