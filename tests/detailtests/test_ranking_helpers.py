from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterRanking as ranking_helpers


class _Cv2Stub:
    def imread(self, _path: str):
        class _Img:
            shape = (5, 7, 3)

        return _Img()


def test_write_pixel_delta2_ranking_writes_expected_reports(tmp_path: Path) -> None:
    folder = tmp_path / "input"
    svg_out = tmp_path / "svg"
    reports = tmp_path / "reports"
    folder.mkdir()
    svg_out.mkdir()
    reports.mkdir()

    (folder / "AC0800_S.jpg").write_bytes(b"dummy")
    (svg_out / "AC0800_S.svg").write_text("<svg />", encoding="utf-8")

    ranking_helpers.writePixelDelta2RankingImpl(
        folder_path=str(folder),
        svg_out_dir=str(svg_out),
        reports_out_dir=str(reports),
        threshold=10.0,
        cv2_module=_Cv2Stub(),
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_delta2_stats_fn=lambda _orig, _rendered: (4.25, 1.5),
    )

    ranking_csv = (reports / "pixel_delta2_ranking.csv").read_text(encoding="utf-8")
    assert "AC0800_S.jpg;4.250000;1.500000" in ranking_csv

    summary_txt = (reports / "pixel_delta2_summary.txt").read_text(encoding="utf-8")
    assert "images_total=1" in summary_txt
    assert "images_with_mean_delta2_le_threshold=1" in summary_txt
