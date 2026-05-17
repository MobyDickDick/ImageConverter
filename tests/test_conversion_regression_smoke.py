from __future__ import annotations

from pathlib import Path

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
