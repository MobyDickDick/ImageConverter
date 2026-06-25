from __future__ import annotations

from pathlib import Path

import pytest
import src.imageCompositeConverter as converter


INPUT_DIR = Path("artifacts/images_to_convert")
DESCRIPTIONS = INPUT_DIR / "Finale_Wurzelformen_V3.xml"


def test_ac08_regression_smoke_run_creates_expected_outputs(tmp_path: Path) -> None:
    """Run a tiny conversion slice to detect regressions in the conversion pipeline early."""
    output_dir = tmp_path / "converted"

    exit_code = converter.main(
        [
            str(INPUT_DIR),
            "--descriptions-path",
            str(DESCRIPTIONS),
            "--output-dir",
            str(output_dir),
            "--start",
            "AC0800",
            "--end",
            "AC0800",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "converted_svgs" / "AC0800_M.svg").exists()
    assert (output_dir / "reports" / "Iteration_Log.csv").exists()


@pytest.mark.blocking_conversion
def test_ac0100_quality_uses_algorithmic_elementwise_fit(tmp_path: Path) -> None:
    """AC0010/AC0100 must use an algorithmic fit, not samples or template transfer."""
    output_dir = tmp_path / "ac0100"

    variants = ("AC0010", "AC0100_L", "AC0100_M", "AC0100_S")
    for variant in variants:
        exit_code = converter.main(
            [
                str(INPUT_DIR),
                "--descriptions-path",
                str(DESCRIPTIONS),
                "--output-dir",
                str(output_dir),
                "--start",
                variant,
                "--end",
                variant,
                "--deterministic-order",
            ]
        )
        assert exit_code == 0

    bestlist = (output_dir / "reports" / "conversion_bestlist.csv").read_text(encoding="utf-8")
    rows = [line.split(";") for line in bestlist.splitlines()[1:] if line.strip()]
    assert {row[0] for row in rows} == set(variants)
    for row in rows:
        best_error = float(row[4])
        mean_delta2 = float(row[6])
        quality_limits = {
            "AC0010": (25.0, 3000.0),
            "AC0100_L": (18.0, 1800.0),
            "AC0100_M": (18.0, 1600.0),
            "AC0100_S": (18.0, 1600.0),
        }
        max_best_error, max_mean_delta2 = quality_limits[row[0]]
        assert best_error < max_best_error
        assert mean_delta2 < max_mean_delta2

    for variant in variants:
        log = (output_dir / "reports" / f"{variant}_element_validation.log").read_text(encoding="utf-8")
        if variant == "AC0010":
            assert "status=non_composite_description_geometry_ir" in log
        else:
            assert "status=non_composite_elementwise_symbol_fit" in log
        assert "status=non_composite_plan_b_sample_svg_selected" not in log
        assert "template_transfer" not in log
        if variant != "AC0010":
            fit_values = dict(
                line.split("=", 1)
                for line in log.splitlines()
                if line.startswith("fit_") and "=" in line
            )
            assert 0.05 <= float(fit_values["fit_glyph_y_ratio"]) <= 0.30
