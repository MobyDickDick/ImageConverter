from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterRemaining as remaining_helpers


def test_move_nonconvertable_sources_moves_failed_files(tmp_path: Path) -> None:
    (tmp_path / "AC0800_L.jpg").write_bytes(b"a")
    (tmp_path / "AC0801_M.jpeg").write_bytes(b"b")
    (tmp_path / "AC0802_S.png").write_bytes(b"c")

    moved = remaining_helpers._moveNonconvertableSources(
        folder_path=str(tmp_path),
        batch_failures=[
            {"filename": "AC0800_L.jpg", "status": "render_failure"},
            {"filename": "AC0801_M.jpeg", "status": "semantic_mismatch"},
            {"filename": "AC0802_S.png", "status": "ok"},
            {"filename": "AC0800_L.jpg", "status": "render_failure"},
        ],
    )

    assert moved == 2
    assert not (tmp_path / "AC0800_L.jpg").exists()
    assert not (tmp_path / "AC0801_M.jpeg").exists()
    assert (tmp_path / "AC0802_S.png").exists()
    assert (tmp_path / "nonconvertable" / "AC0800_L.jpg").exists()
    assert (tmp_path / "nonconvertable" / "AC0801_M.jpeg").exists()
