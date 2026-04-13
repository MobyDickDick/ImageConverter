"""Optional dependency import helpers for the image composite converter."""

from __future__ import annotations

import contextlib
import importlib
import os
import subprocess
import sys
from pathlib import Path

OPTIONAL_DEPENDENCY_ERRORS: dict[str, str] = {}


def optional_dependency_base_dir() -> Path:
    """Return the repository root used for vendored dependency discovery."""
    return Path(__file__).resolve().parents[2]


def vendored_site_packages_dirs(*, base_dir_fn=optional_dependency_base_dir) -> list[Path]:
    """Return repo-local site-packages directories that may contain bundled deps."""
    base = base_dir_fn()
    linux_candidates = [
        base / "vendor" / "linux" / "site-packages",
        base / "vendor" / "linux-py310" / "site-packages",
        base / "vendor" / "linux-py311" / "site-packages",
        base / "vendor" / "linux-py312" / "site-packages",
        base / "vendor" / "linux-py313" / "site-packages",
        base / "vendor" / "linux-py314" / "site-packages",
    ]
    windows_candidates = [
        base / "vendor" / "win" / "site-packages",
        base / "vendor" / "win-py310" / "site-packages",
        base / "vendor" / "win-py311" / "site-packages",
        base / "vendor" / "win-py312" / "site-packages",
        base / "vendor" / "win-py313" / "site-packages",
        base / "vendor" / "win-py314" / "site-packages",
        base / ".venv" / "Lib" / "site-packages",
    ]
    posix_venv_candidates = [
        base / ".venv" / "lib" / "python3.10" / "site-packages",
        base / ".venv" / "lib" / "python3.11" / "site-packages",
        base / ".venv" / "lib" / "python3.12" / "site-packages",
        base / ".venv" / "lib" / "python3.13" / "site-packages",
        base / ".venv" / "lib" / "python3.14" / "site-packages",
    ]
    if os.name == "nt":
        candidates = windows_candidates + linux_candidates + posix_venv_candidates
    else:
        candidates = linux_candidates + posix_venv_candidates + windows_candidates

    seen: set[str] = set()
    existing: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            existing.append(candidate)
    return existing


def clear_partial_module_import(module_name: str) -> None:
    """Discard partially imported package state before the next fallback attempt."""
    for imported_name in [name for name in list(sys.modules) if name == module_name or name.startswith(f"{module_name}.")]:
        sys.modules.pop(imported_name, None)


def describe_optional_dependency_error(module_name: str, exc: BaseException, attempted_paths: list[Path]) -> str:
    detail = f"{type(exc).__name__}: {exc}"
    lower = detail.lower()
    if "add_dll_directory" in lower or ".pyd" in lower:
        return (
            f"{detail}. Repo-local Paket gefunden, aber es wirkt wie ein Windows-Build "
            f"und ist unter dieser Linux-Umgebung nicht ladbar"
        )
    if "elf" in lower or "wrong elf class" in lower:
        return f"{detail}. Repo-lokales Binary ist nicht mit dieser Laufzeit kompatibel"
    if attempted_paths:
        joined = ", ".join(str(path) for path in attempted_paths)
        return f"{detail}. Zusätzliche Importpfade geprüft: {joined}"
    return detail


def load_optional_module(module_name: str, *, vendored_dirs_fn=vendored_site_packages_dirs, import_module_fn=importlib.import_module):
    """Import optional dependencies, including repo-vendored site-packages."""
    attempted_paths: list[Path] = []
    try:
        return import_module_fn(module_name)
    except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
        last_exc: BaseException = exc
        clear_partial_module_import(module_name)

    for site_packages in vendored_dirs_fn():
        attempted_paths.append(site_packages)
        path_str = str(site_packages)
        added = False
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            added = True
        try:
            return import_module_fn(module_name)
        except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
            last_exc = exc
            clear_partial_module_import(module_name)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(path_str)

    OPTIONAL_DEPENDENCY_ERRORS[module_name] = describe_optional_dependency_error(module_name, last_exc, attempted_paths)
    return None


def import_with_vendored_fallback(
    module_name: str,
    *,
    vendored_dirs_fn=vendored_site_packages_dirs,
    import_module_fn=importlib.import_module,
):
    """Import a module, retrying with repo-vendored site-packages on sys.path."""
    try:
        return import_module_fn(module_name)
    except Exception as exc:
        last_exc: BaseException = exc
        clear_partial_module_import(module_name)

    for site_packages in vendored_dirs_fn():
        path_str = str(site_packages)
        added = False
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            added = True
        try:
            return import_module_fn(module_name)
        except Exception as exc:
            last_exc = exc
            clear_partial_module_import(module_name)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(path_str)

    raise last_exc


def missingRequiredImageDependenciesImpl(cv2_module, np_module) -> list[str]:
    """Return pip package names for currently missing image runtime dependencies."""
    missing: list[str] = []
    if cv2_module is None:
        missing.append("opencv-python-headless")
    if np_module is None:
        missing.append("numpy")
    return missing


def ensureConversionRuntimeDependenciesImpl(cv2_module, np_module, fitz_module) -> None:
    """Raise a stable runtime error when required conversion dependencies are unavailable."""
    missing_modules: list[str] = []
    if cv2_module is None:
        missing_modules.append("cv2")
    if np_module is None:
        missing_modules.append("numpy")
    if missing_modules:
        raise RuntimeError(
            "Required image dependencies are missing: " + ", ".join(missing_modules) + ". "
            "Install dependencies before running the conversion pipeline."
        )
    if fitz_module is None:
        raise RuntimeError(
            "Required SVG renderer dependency is missing: fitz (PyMuPDF). "
            "Install PyMuPDF before running the conversion pipeline."
        )


def bootstrapRequiredImageDependenciesImpl(
    *,
    missing: list[str],
    sys_executable: str,
    run_fn=subprocess.run,
    print_fn=print,
    load_cv2_fn=None,
    load_np_fn=None,
    set_modules_fn=None,
) -> list[str]:
    """Install and re-import missing image dependencies into the current process."""
    if not missing:
        return []

    cmd = [sys_executable, "-m", "pip", "install", *missing]
    print_fn(f"[INFO] Fehlende Bild-Abhängigkeiten gefunden: {', '.join(missing)}")
    print_fn(f"[INFO] Installiere via: {' '.join(cmd)}")
    try:
        run_fn(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Automatische Installation fehlgeschlagen. "
            "Bitte Abhängigkeiten manuell installieren oder Proxy/Netzwerk prüfen."
        ) from exc

    loaded_cv2 = load_cv2_fn() if "opencv-python-headless" in missing and callable(load_cv2_fn) else None
    loaded_np = load_np_fn() if "numpy" in missing and callable(load_np_fn) else None

    if callable(set_modules_fn):
        set_modules_fn(cv2_module=loaded_cv2, np_module=loaded_np)

    return missing
