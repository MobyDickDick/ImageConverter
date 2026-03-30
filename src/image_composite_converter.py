"""Thin CLI entrypoint for the image composite converter.

This module intentionally keeps only the `main` orchestration function and
re-exports the existing converter API from `image_composite_converter_core`.
"""

from __future__ import annotations

import contextlib
import importlib
import os
import sys
from pathlib import Path

import src.mainFiles.image_composite_converter_core as _core

for _name in dir(_core):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_core, _name)


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


def _load_optional_module(module_name: str):
    """Import optional dependencies, including repo-vendored site-packages."""
    attempted_paths: list[Path] = []
    try:
        return importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - exercised only in dependency-missing envs
        last_exc: BaseException = exc
        _clear_partial_module_import(module_name)

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
            _clear_partial_module_import(module_name)
        finally:
            if added:
                with contextlib.suppress(ValueError):
                    sys.path.remove(path_str)

    OPTIONAL_DEPENDENCY_ERRORS[module_name] = _describe_optional_dependency_error(module_name, last_exc, attempted_paths)
    return None


_core._optional_dependency_base_dir = _optional_dependency_base_dir
_core._vendored_site_packages_dirs = _vendored_site_packages_dirs
_core._load_optional_module = _load_optional_module

np = _load_optional_module("numpy")
cv2 = _load_optional_module("cv2")
_core.np = np
_core.cv2 = cv2


def _sync_core_overrides() -> None:
    """Mirror monkeypatched wrapper globals into the core module before calls."""
    skip_names = {"convert_range", "main", "_sync_core_overrides"}
    for name, value in globals().items():
        if name in skip_names:
            continue
        if not hasattr(_core, name):
            continue
        if getattr(_core, name) is value:
            continue
        setattr(_core, name, value)


def convert_range(*args, **kwargs):
    _sync_core_overrides()
    return _core.convert_range(*args, **kwargs)


def main(argv: list[str] | None = None) -> int:
    _sync_core_overrides()
    args = parse_args(argv)
    if bool(getattr(args, "_render_svg_subprocess", False)):
        return _run_svg_render_subprocess_entrypoint()
    global SVG_RENDER_SUBPROCESS_ENABLED, SVG_RENDER_SUBPROCESS_TIMEOUT_SEC
    if bool(args.isolate_svg_render):
        SVG_RENDER_SUBPROCESS_ENABLED = True
    SVG_RENDER_SUBPROCESS_TIMEOUT_SEC = max(1.0, float(args.isolate_svg_render_timeout_sec))
    log_path = str(args.log_file or "").strip()
    with _optional_log_capture(log_path):
        try:
            if args.ac08_regression_set:
                args.start = "AC0000"
                args.end = "ZZ9999"

            if args.print_linux_vendor_command:
                print(
                    " ".join(
                        build_linux_vendor_install_command(
                            vendor_dir=args.vendor_dir,
                            platform_tag=args.vendor_platform,
                            python_version=args.vendor_python_version,
                        )
                    )
                )
                return 0

            if args.export_call_tree_csv:
                path = export_module_call_tree_csv(output_csv_path=args.export_call_tree_csv)
                print(f"[INFO] Aufrufbaum-CSV geschrieben: {path}")
                return 0

            if args.interactive_range or args.start is None or args.end is None:
                args.start, args.end = _prompt_interactive_range(args)
            else:
                args.start = str(args.start or "").strip()
                args.end = str(args.end or "ZZZZZZ").strip() or args.start

            csv_path, output_dir = _resolve_cli_csv_and_output(args)

            if not csv_path:
                print("[WARN] Keine CSV/TSV/XML angegeben oder gefunden. Einige Symbole können ohne Beschreibung übersprungen werden.")
            elif not os.path.exists(csv_path):
                print(f"[WARN] CSV/TSV/XML-Datei nicht gefunden: {csv_path}")
            elif args.mode == "convert":
                # Validate user-supplied description data before the batch starts so
                # malformed files fail with a precise source location even when the
                # selected image range happens to be empty.
                _load_description_mapping(csv_path)

            if args.bootstrap_deps:
                try:
                    installed = _bootstrap_required_image_dependencies()
                except RuntimeError as exc:
                    print(f"[ERROR] {exc}")
                    return 2
                if installed:
                    print(f"[INFO] Installiert: {', '.join(installed)}")

            if args.ac08_regression_set:
                print(
                    "[INFO] Verwende festes AC08-Regression-Set "
                    f"{AC08_REGRESSION_SET_NAME}: {', '.join(AC08_REGRESSION_VARIANTS)}"
                )
            selected_variants = set(AC08_REGRESSION_VARIANTS) if args.ac08_regression_set else None

            if args.mode == "annotate":
                out_dir = analyze_range(
                    args.folder_path,
                    output_root=output_dir,
                    start_ref=args.start,
                    end_ref=args.end,
                )
            else:
                out_dir = convert_range(
                    args.folder_path,
                    csv_path,
                    args.iterations,
                    args.start,
                    args.end,
                    args.debug_ac0811_dir,
                    args.debug_element_diff_dir,
                    output_dir,
                    selected_variants,
                )
            print(f"\nAbgeschlossen! Ausgaben unter: {out_dir}")
            return 0
        except DescriptionMappingError as exc:
            print(f"[ERROR] {_format_user_diagnostic(exc)}")
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
