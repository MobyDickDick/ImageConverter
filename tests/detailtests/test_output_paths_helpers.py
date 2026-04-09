from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterOutputPaths as output_path_helpers


def test_default_converted_symbols_root_impl_resolves_repo_relative_path() -> None:
    module_file = str(Path("src") / "imageCompositeConverter.py")

    resolved = output_path_helpers.defaultConvertedSymbolsRootImpl(module_file=module_file)

    assert resolved.endswith("artifacts/converted_images")


def test_output_subdir_helpers_use_expected_folder_names() -> None:
    output_root = "/tmp/image-converter"

    assert output_path_helpers.convertedSvgOutputDirImpl(output_root).endswith("/converterted_svgs")
    assert output_path_helpers.diffOutputDirImpl(output_root).endswith("/diff_pngs")
    assert output_path_helpers.reportsOutputDirImpl(output_root).endswith("/reports")
