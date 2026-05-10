from pathlib import Path

from src.weak_family_pipeline import load_ranking, select_top_variants, write_comparison


def test_select_top_variants_filters_prefix_and_sorts(tmp_path: Path) -> None:
    ranking = tmp_path / "ranking.csv"
    ranking.write_text(
        "image;mean_delta2;std_delta2\n"
        "AC0835_L.jpg;11170.0;18000\n"
        "ZZ0001_L.jpg;50000;1\n"
        "AC0820_L.jpg;9983.6;17000\n",
        encoding="utf-8",
    )

    rows = load_ranking(ranking)
    selected = select_top_variants(rows, top_n=2, prefix="AC08")

    assert [row.variant for row in selected] == ["AC0835_L", "AC0820_L"]


def test_write_comparison_marks_improvement(tmp_path: Path) -> None:
    before = tmp_path / "before.csv"
    after = tmp_path / "after.csv"
    out = tmp_path / "comparison.csv"
    before.write_text(
        "image;mean_delta2;std_delta2\n"
        "AC0835_L.jpg;11170.0;18000\n",
        encoding="utf-8",
    )
    after.write_text(
        "image;mean_delta2;std_delta2\n"
        "AC0835_L.jpg;9000.0;12000\n",
        encoding="utf-8",
    )

    before_rows = load_ranking(before)
    after_rows = load_ranking(after)
    write_comparison(before_rows, after_rows, before_rows, out)

    text = out.read_text(encoding="utf-8")
    assert "AC0835_L" in text
    assert "-2170.000000" in text
    assert ";1;" in text
