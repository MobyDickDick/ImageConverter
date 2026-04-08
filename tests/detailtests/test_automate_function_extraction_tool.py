from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_tool(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(REPO_ROOT / "tools/automate_function_extraction.py"), *args]
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def test_extracts_function_and_replaces_with_wrapper(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    target = tmp_path / "helpers.py"
    source.write_text(
        """
from __future__ import annotations


def a(x: int) -> int:
    return x + 1


def b(value: int) -> int:
    temp = value * 2
    return temp + a(value)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    proc = _run_tool(
        "--source",
        str(source),
        "--function",
        "b",
        "--target-module",
        str(target),
        "--import-line",
        "import helpers as helper_mod",
        "--module-alias",
        "helper_mod",
        "--verify-cmd",
        f"{sys.executable} -c \"import source\"",
        cwd=tmp_path,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    source_text = source.read_text(encoding="utf-8")
    target_text = target.read_text(encoding="utf-8")

    assert "import helpers as helper_mod" in source_text
    assert "def b(value: int) -> int:" in source_text
    assert "return helper_mod.b(value)" in source_text
    assert "def b(value: int) -> int:" in target_text
    assert "temp = value * 2" in target_text


def test_rolls_back_when_verification_fails(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    target = tmp_path / "helpers.py"
    original = (
        "def do_work(x: int) -> int:\n"
        "    return x + 7\n"
    )
    source.write_text(original, encoding="utf-8")

    proc = _run_tool(
        "--source",
        str(source),
        "--function",
        "do_work",
        "--target-module",
        str(target),
        "--import-line",
        "import helpers as helper_mod",
        "--module-alias",
        "helper_mod",
        "--verify-cmd",
        f"{sys.executable} -c \"raise SystemExit(1)\"",
        cwd=tmp_path,
    )

    assert proc.returncode == 1
    assert source.read_text(encoding="utf-8") == original
    assert target.read_text(encoding="utf-8") == ""


def test_inserts_import_after_multiline_import_block(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    target = tmp_path / "helpers.py"
    source.write_text(
        """
from pkg import (
    first,
    second,
)


def move_me(x: int) -> int:
    return x + first() + second()
""".strip()
        + "\n",
        encoding="utf-8",
    )

    proc = _run_tool(
        "--source",
        str(source),
        "--function",
        "move_me",
        "--target-module",
        str(target),
        "--import-line",
        "import helpers as helper_mod",
        "--module-alias",
        "helper_mod",
        "--verify-cmd",
        f"{sys.executable} -m py_compile source.py helpers.py",
        cwd=tmp_path,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    source_text = source.read_text(encoding="utf-8")
    assert (
        "from pkg import (\n"
        "    first,\n"
        "    second,\n"
        ")\n"
        "import helpers as helper_mod\n"
    ) in source_text
