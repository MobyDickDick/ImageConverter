from __future__ import annotations

import json
import subprocess
import sys
import types
from pathlib import Path


def test_fill_missing_parameters_updates_signature_and_calls(tmp_path: Path) -> None:
    module_path = tmp_path / "sample.py"
    module_path.write_text(
        """

def target(a):
    return a, b

def caller(a, b):
    return target(a)
""".lstrip(),
        encoding="utf-8",
    )

    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": str(module_path.relative_to(tmp_path)),
                        "functions": [
                            {
                                "name": "target",
                                "add_params": [{"name": "b", "default": "None"}],
                            }
                        ],
                        "calls": [
                            {
                                "callee": "target",
                                "caller": "caller",
                                "add_keywords": [{"name": "b", "value": "b"}],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            "tools/fill_missing_parameters.py",
            str(spec_path),
            "--root",
            str(tmp_path),
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[2],
    )

    updated = module_path.read_text(encoding="utf-8")
    assert "def target(a, b=None):" in updated
    assert "return target(a, b=b)" in updated

    module = types.ModuleType("sample")
    exec(compile(updated, str(module_path), "exec"), module.__dict__)
    assert module.target(5) == (5, None)
    assert module.caller(5, 7) == (5, 7)
