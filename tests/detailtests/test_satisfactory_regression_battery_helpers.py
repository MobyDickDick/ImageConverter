from __future__ import annotations

from pathlib import Path

from tests.test_satisfactory_regression_battery import (
    _available_reconverted_svgs,
    _reconverted_svg_path,
    _require_reconverted_svg_path,
)


def test_reconverted_svg_path_falls_back_to_bestlist_snapshot(tmp_path: Path) -> None:
    family_out = tmp_path / "ac0800"
    snapshot_svg = family_out / "reports" / "conversion_bestlist_snapshots" / "AC0800_M.svg"
    snapshot_svg.parent.mkdir(parents=True)
    snapshot_svg.write_text("<svg />", encoding="utf-8")

    assert _reconverted_svg_path(family_out, "AC0800_M") == snapshot_svg
    assert _available_reconverted_svgs(family_out) == [
        "reports/conversion_bestlist_snapshots/AC0800_M.svg"
    ]


def test_reconverted_svg_path_prefers_final_converted_svg(tmp_path: Path) -> None:
    family_out = tmp_path / "ac0800"
    snapshot_svg = family_out / "reports" / "conversion_bestlist_snapshots" / "AC0800_M.svg"
    converted_svg = family_out / "converted_svgs" / "AC0800_M.svg"
    snapshot_svg.parent.mkdir(parents=True)
    converted_svg.parent.mkdir(parents=True)
    snapshot_svg.write_text("<svg id='snapshot' />", encoding="utf-8")
    converted_svg.write_text("<svg id='final' />", encoding="utf-8")

    assert _reconverted_svg_path(family_out, "AC0800_M") == converted_svg


def test_require_reconverted_svg_path_returns_fallback_path(tmp_path: Path) -> None:
    family_out = tmp_path / "ac0800"
    snapshot_svg = family_out / "reports" / "conversion_bestlist_snapshots" / "AC0800_L.svg"
    snapshot_svg.parent.mkdir(parents=True)
    snapshot_svg.write_text("<svg />", encoding="utf-8")

    assert _require_reconverted_svg_path(
        family_out,
        "AC0800_L",
        ["reports/conversion_bestlist_snapshots/AC0800_L.svg"],
    ) == snapshot_svg


def test_require_reconverted_svg_path_reports_available_outputs(tmp_path: Path) -> None:
    family_out = tmp_path / "ac0800"

    try:
        _require_reconverted_svg_path(family_out, "AC0800_X", ["converted_svgs/AC0800_L.svg"])
    except AssertionError as exc:
        message = str(exc)
    else:  # pragma: no cover - the helper must fail for missing outputs
        raise AssertionError("missing reconverted SVG unexpectedly passed")

    assert "AC0800_X" in message
    assert "converted_svgs/AC0800_L.svg" in message
