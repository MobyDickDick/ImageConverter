from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path



def _with_vendor_pythonpath(env: dict[str, str], root: Path) -> dict[str, str]:
    env = env.copy()
    vendor = root / "vendor" / "linux-py310" / "site-packages"
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{vendor}:{existing}" if existing else str(vendor)
    return env


def test_svg_render_subprocess_timeout_defaults_to_five_seconds_under_pytest_context() -> None:
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("IMAGE_CONVERTER_ISOLATE_SVG_RENDER_TIMEOUT_SEC", None)
    env = _with_vendor_pythonpath(env, root)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.modules['pytest'] = object(); "
                "import src.imageCompositeConverter as m; "
                "print(m.SVG_RENDER_SUBPROCESS_TIMEOUT_SEC)"
            ),
        ],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.strip() == "5.0"


def test_svg_render_subprocess_defaults_activate_when_pytest_env_is_inherited() -> None:
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("IMAGE_CONVERTER_ISOLATE_SVG_RENDER", None)
    env.pop("IMAGE_CONVERTER_ISOLATE_SVG_RENDER_TIMEOUT_SEC", None)
    env = _with_vendor_pythonpath(env, root)
    env["PYTEST_CURRENT_TEST"] = "detailtests::test_svg_render_subprocess_defaults_activate_when_pytest_env_is_inherited"
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import src.imageCompositeConverter as m; "
                "print(int(m.SVG_RENDER_SUBPROCESS_ENABLED), m.SVG_RENDER_SUBPROCESS_TIMEOUT_SEC)"
            ),
        ],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.strip() == "1 5.0"


def test_svg_render_subprocess_inherits_runtime_pythonpath(monkeypatch) -> None:
    from src.iCCModules import imageCompositeConverterRendering as rendering

    np = __import__("numpy")
    captured: dict[str, object] = {}

    def fake_run(cmd, *, input, stdout, stderr, check, timeout, env):
        captured["cmd"] = cmd
        captured["env"] = env
        raw = bytes([1, 2, 3])
        payload = {
            "ok": True,
            "w": 1,
            "h": 1,
            "data": __import__("base64").b64encode(raw).decode("ascii"),
        }

        class Completed:
            returncode = 0
            stdout = __import__("json").dumps(payload).encode("utf-8")
            stderr = b""

        return Completed()

    monkeypatch.setattr(rendering.subprocess, "run", fake_run)
    monkeypatch.setattr(rendering.sys, "path", ["/runtime/vendor", "/workspace/project", ""])

    result = rendering.render_svg_to_numpy_via_subprocess(
        '<svg xmlns="http://www.w3.org/2000/svg"/>',
        1,
        1,
        np_module=np,
        timeout_sec=1.0,
    )

    assert result is not None
    child_env = captured["env"]
    assert isinstance(child_env, dict)
    pythonpath = str(child_env.get("PYTHONPATH", ""))
    assert "/runtime/vendor" in pythonpath.split(os.pathsep)
    assert "/workspace/project" in pythonpath.split(os.pathsep)
