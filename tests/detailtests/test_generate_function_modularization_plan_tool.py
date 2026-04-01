from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_generate_function_modularization_plan(tmp_path: Path) -> None:
    src = tmp_path / "sample.py"
    src.write_text(
        """
import os

CONST = 7


def helper(v):
    return v + CONST


def top(x):
    y = helper(x)
    return os.path.join(str(y), str(CONST))
""".lstrip(),
        encoding="utf-8",
    )

    out_json = tmp_path / "plan.json"

    subprocess.run(
        [
            sys.executable,
            "tools/generate_function_modularization_plan.py",
            str(src),
            "--output-json",
            str(out_json),
            "--output-dir",
            "src/new_funcs",
            "--module-prefix",
            "src.new_funcs",
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
    )

    plan = json.loads(out_json.read_text(encoding="utf-8"))
    assert plan["function_count"] == 2
    assert "os" in plan["module_imports"]
    assert "CONST" in plan["module_constants"]

    top = next(entry for entry in plan["functions"] if entry["name"] == "top")
    assert top["depends_on_functions"] == ["helper"]
    assert "os" in top["depends_on_external_names"]
    assert top["suggested_module"] == "src.new_funcs.top"
    assert top["suggested_file"].endswith("src/new_funcs/top.py")
