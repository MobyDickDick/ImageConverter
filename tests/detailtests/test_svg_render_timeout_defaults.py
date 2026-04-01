from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_svg_render_subprocess_timeout_defaults_to_five_seconds_under_pytest_context() -> None:
    root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("IMAGE_CONVERTER_ISOLATE_SVG_RENDER_TIMEOUT_SEC", None)
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
