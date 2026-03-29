        "text_scale_delta": 0.10,
        "color_corridor": 10.0,
    },
}


def detect_relevant_regions(img) -> list[dict[str, object]]:
    return detect_relevant_regions_impl(img, cv2_module=cv2, np_module=np)


def annotate_image_regions(img, regions: list[dict[str, object]]):
    return annotate_image_regions_impl(img, regions, cv2_module=cv2)


def analyze_range(folder_path: str, output_root: str | None = None, start_ref: str = "", end_ref: str = "ZZZZZZ") -> str:
    return analyze_range_impl(
        folder_path=folder_path,
        output_root=output_root,
        start_ref=start_ref,
        end_ref=end_ref,
        default_output_root_fn=_default_converted_symbols_root,
        in_requested_range_fn=_in_requested_range,
        detect_regions_fn=detect_relevant_regions,
        annotate_regions_fn=annotate_image_regions,
        cv2_module=cv2,
        np_module=np,
    )


def _optional_dependency_base_dir() -> Path:
    """Return the repository root used for vendored dependency discovery."""
    return Path(__file__).resolve().parents[1]


def _vendored_site_packages_dirs() -> list[Path]:
    """Return repo-local site-packages directories that may contain bundled deps."""
    base = _optional_dependency_base_dir()
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


def _clear_partial_module_import(module_name: str) -> None:
    """Discard partially imported package state before the next fallback attempt."""
    for imported_name in [name for name in list(sys.modules) if name == module_name or name.startswith(f"{module_name}.")]:
        sys.modules.pop(imported_name, None)


def _describe_optional_dependency_error(module_name: str, exc: BaseException, attempted_paths: list[Path]) -> str:
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


