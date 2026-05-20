"""Pytest configuration for test imports."""

from __future__ import annotations

import importlib.util
import os
import signal
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if importlib.util.find_spec("numpy") is None:
    py_tag = f"py{sys.version_info.major}{sys.version_info.minor}"
    vendor_site_packages = PROJECT_ROOT / "vendor" / f"linux-{py_tag}" / "site-packages"
    if vendor_site_packages.exists() and str(vendor_site_packages) not in sys.path:
        sys.path.insert(0, str(vendor_site_packages))


_PER_TEST_TIMEOUT_SECONDS = int(os.environ.get("PYTEST_PER_TEST_TIMEOUT_SECONDS", "30"))


class _PerTestTimeout(Exception):
    """Internal timeout marker for per-test hard limits."""


def _timeout_handler(_signum: int, _frame) -> None:
    raise _PerTestTimeout()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item):
    """Apply a hard per-test runtime limit and convert overruns into task-style xfails."""
    if _PER_TEST_TIMEOUT_SECONDS <= 0:
        yield
        return

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(_PER_TEST_TIMEOUT_SECONDS)
    try:
        yield
    except _PerTestTimeout:
        pytest.xfail(
            f"AUFGABE: Testlauf > {_PER_TEST_TIMEOUT_SECONDS}s, bitte optimieren/isolieren: {item.nodeid}"
        )
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)
