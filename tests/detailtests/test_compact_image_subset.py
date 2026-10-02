from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUBSET_MANIFEST = PROJECT_ROOT / "config" / "compact_image_subset.txt"


def _subset_entries() -> list[str]:
    return [
        line.strip()
        for line in SUBSET_MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def test_compact_image_subset_is_small_and_complete() -> None:
    entries = _subset_entries()

    assert entries == [
        "AC0800_M.jpg",
        "DLG0021.jpg",
        "GE1410_L.jpg",
        "SE0041_1.jpg",
        "GE9012_6M.jpg",
        "GE9013_1M.jpg",
        "AC0840_L.jpg",
        "AC0538_1L_sia.jpg",
        "nonconvertable/AC0881_M.jpg",
    ]
    assert len(entries) <= 10
    assert all((PROJECT_ROOT / "artifacts" / "images_to_convert" / entry).is_file() for entry in entries)


def test_eindampfen_builds_sparse_checkout_from_subset_manifest() -> None:
    script = (PROJECT_ROOT / "eindampfen.bat").read_text(encoding="utf-8")

    assert "!/artifacts/images_to_convert/*.jpg" in script
    assert "!/artifacts/images_to_convert/nonconvertable/*.jpg" in script
    assert "config/compact_image_subset.txt" in script
    assert "'/artifacts/images_to_convert/' + $_" in script
    assert "git sparse-checkout set --no-cone --stdin" in script
    assert "git sparse-checkout reapply" not in script


def test_eindampfen_verifies_that_excluded_files_are_physically_absent() -> None:
    script = (PROJECT_ROOT / "eindampfen.bat").read_text(encoding="utf-8")

    assert 'if exist "docs\\README.md" goto :sparse_failed' in script
    assert 'if exist "artifacts\\images_to_convert\\AC0010.jpg" goto :sparse_failed' in script
    assert 'echo Arbeitskopie wurde physisch eingedampft.' in script
    assert ':sparse_failed' in script


def test_eindampfen_applies_by_default_and_keeps_explicit_preview() -> None:
    script = (PROJECT_ROOT / "eindampfen.bat").read_text(encoding="utf-8")

    assert 'if "%~1"=="" goto :apply' in script
    assert 'if /I "%~1"=="--dry-run" goto :preview' in script
