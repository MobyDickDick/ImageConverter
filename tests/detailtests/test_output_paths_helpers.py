from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterOutputPaths as output_path_helpers


def test_default_converted_symbols_root_impl_resolves_repo_relative_path() -> None:
    module_file = str(Path("src") / "iCCModules" / "imageCompositeConverterOutputPaths.py")

    resolved = output_path_helpers.defaultConvertedSymbolsRootImpl(module_file=module_file)

    expected = Path(module_file).resolve().parents[2] / "artifacts" / "converted_images"
    assert Path(resolved) == expected


def test_output_subdir_helpers_use_expected_folder_names() -> None:
    output_root = "/tmp/image-converter"

    assert output_path_helpers.convertedSvgOutputDirImpl(output_root).endswith("/converted_svgs")
    assert output_path_helpers.diffOutputDirImpl(output_root).endswith("/diff_pngs")
    assert output_path_helpers.reportsOutputDirImpl(output_root).endswith("/reports")
