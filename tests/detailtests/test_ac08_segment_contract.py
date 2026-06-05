from __future__ import annotations

from pathlib import Path

from tools.ac08_segment_contract import iteration_report_contains_variant, resolve_variant_input_dir


def test_resolve_variant_input_dir_prefers_root_and_finds_quarantined_variant(tmp_path: Path) -> None:
    quarantine = tmp_path / "nonconvertable"
    quarantine.mkdir()
    (tmp_path / "AC0800_L.jpg").write_bytes(b"root")
    (quarantine / "AC0800_L.jpg").write_bytes(b"duplicate")
    (quarantine / "AC0811_L.jpg").write_bytes(b"nested")

    assert resolve_variant_input_dir(tmp_path, "AC0800_L") == tmp_path
    assert resolve_variant_input_dir(tmp_path, "ac0811_l") == quarantine
    assert resolve_variant_input_dir(tmp_path, "AC0899_X") == tmp_path


def test_iteration_report_requires_expected_variant_row(tmp_path: Path) -> None:
    report = tmp_path / "Iteration_Log.csv"
    report.write_text("Dateiname;Fehler\nAC0811_L.jpg;1\n", encoding="utf-8")

    assert iteration_report_contains_variant(report, "AC0811_L")
    assert not iteration_report_contains_variant(report, "AC0811_M")
    assert not iteration_report_contains_variant(tmp_path / "missing.csv", "AC0811_L")
