"""Output-path helper functions extracted from the converter monolith."""

from __future__ import annotations

import os


def _output_subdir(output_root: str, folder_name: str) -> str:
    trimmed_root = output_root.rstrip("/\\")
    return f"{trimmed_root}/{folder_name}"


def defaultConvertedSymbolsRootImpl(*, module_file: str) -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(module_file))))
    return os.path.join(repo_root, "artifacts", "converted_images")


def convertedSvgOutputDirImpl(output_root: str) -> str:
    # Keep the historical folder name with the current typo because downstream
    # adjustment tooling expects this exact directory.
    return _output_subdir(output_root, "converted_svgs")


def diffOutputDirImpl(output_root: str) -> str:
    return _output_subdir(output_root, "diff_pngs")


def convertedPngOutputDirImpl(output_root: str) -> str:
    return _output_subdir(output_root, "converted_images_png")


def reportsOutputDirImpl(output_root: str) -> str:
    return _output_subdir(output_root, "reports")


def failedSvgOutputDirImpl(output_root: str) -> str:
    return _output_subdir(output_root, "converted_svg_failed")


def failedPngOutputDirImpl(output_root: str) -> str:
    return _output_subdir(output_root, "converted_images_png_failed")
