from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_tool(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(REPO_ROOT / "tools/extract_remaining_functions_batch.py"), *args]
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def test_extracts_only_non_delegating_functions_and_writes_logs(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    target = tmp_path / "helpers.py"
    log_json = tmp_path / "log.json"
    log_text = tmp_path / "log.log"

    source.write_text(
        (
            "import helpers as helper_mod\n\n"
            "def delegated(x: int) -> int:\n"
            "    return helper_mod.delegated(x)\n\n"
            "def main() -> int:\n"
            "    return 0\n\n"
            "def still_here(v: int) -> int:\n"
            "    return v + 7\n"
        ),
        encoding="utf-8",
    )

    proc = _run_tool(
        "--source",
        str(source),
        "--target-module",
        str(target),
        "--exclude",
        "main",
        "--import-line",
        "import helpers as helper_mod",
        "--module-alias",
        "helper_mod",
        "--verify-cmd",
        f"{sys.executable} -m py_compile source.py helpers.py",
        "--log-json",
        str(log_json),
        "--log-text",
        str(log_text),
        "--workdir",
        str(tmp_path),
        cwd=tmp_path,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr

    payload = json.loads(log_json.read_text(encoding="utf-8"))
    assert payload["planned_functions_count"] == 1
    assert payload["successful"] == 1
    assert payload["failed"] == 0
    assert payload["results"][0]["function"] == "still_here"

    text_log = log_text.read_text(encoding="utf-8")
    assert "[success] still_here" in text_log

    source_text = source.read_text(encoding="utf-8")
    assert "return helper_mod.still_here(v)" in source_text
    assert "return helper_mod.delegated(x)" in source_text
