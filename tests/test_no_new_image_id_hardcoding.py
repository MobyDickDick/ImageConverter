import subprocess
import sys
from pathlib import Path

from tools.check_no_new_image_id_hardcoding import scan_source, violations


def test_runtime_source_contains_zero_image_ids() -> None:
    assert violations(scan_source()) == []


def test_cli_rejects_artificial_runtime_image_id(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    (source_root / "runtime.py").write_text('SPECIAL_CASE = "AC9999"\n', encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "tools/check_no_new_image_id_hardcoding.py",
            "--source-root",
            str(source_root),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 1
    assert "src/runtime.py: AC9999 occurs 1 time(s)" in result.stdout
