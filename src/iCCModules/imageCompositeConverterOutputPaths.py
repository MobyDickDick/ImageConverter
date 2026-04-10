"""Output-path helper functions extracted from the converter monolith."""

from __future__ import annotations

import os


def defaultConvertedSymbolsRootImpl(*, module_file: str) -> str:
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(module_file))))
    return os.path.join(repo_root, "artifacts", "converted_images")


def convertedSvgOutputDirImpl(output_root: str) -> str:
    # Keep the historical folder name with the current typo because downstream
    # adjustment tooling expects this exact directory.
    return os.path.join(output_root, "converted_svgs")


def diffOutputDirImpl(output_root: str) -> str:
    return os.path.join(output_root, "diff_pngs")


def reportsOutputDirImpl(output_root: str) -> str:
    return os.path.join(output_root, "reports")
