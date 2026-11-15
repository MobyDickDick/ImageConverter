"""Exercise the real GUI script with a DOM and HTTP stub, without a browser driver."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_gui_cancellation_and_seed_controls():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js is required for the GUI script regression tests')
    result = subprocess.run([node, '--test', str(Path(__file__).with_name('gui_app.test.cjs'))],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
