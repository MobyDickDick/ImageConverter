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
