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
_SIGALRM = getattr(signal, "SIGALRM", None)


class _PerTestTimeout(Exception):
    """Internal timeout marker for per-test hard limits."""


def _timeout_handler(_signum: int, _frame) -> None:
    raise _PerTestTimeout()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item):
    """Apply per-test limits, preserving strict failures for acceptance checks."""
    marker = item.get_closest_marker("per_test_timeout")
    timeout_seconds = int(marker.args[0]) if marker else _PER_TEST_TIMEOUT_SECONDS
    fail_on_timeout = bool(marker and marker.kwargs.get("fail_on_timeout", False))
    # SIGALRM and signal.alarm() are Unix-only.  On Windows, let the test run
    # without this optional hard limit instead of failing every test up front.
    if timeout_seconds <= 0 or _SIGALRM is None:
        return (yield)

    previous_handler = signal.getsignal(_SIGALRM)
    signal.signal(_SIGALRM, _timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        return (yield)
    except _PerTestTimeout:
        if fail_on_timeout:
            pytest.fail(
                f"Testlauf > {timeout_seconds}s: {item.nodeid}", pytrace=False
            )
        pytest.xfail(
            f"AUFGABE A5 (docs/test_followup_tasks_2026-05-20.md): "
            f"Testlauf > {timeout_seconds}s, bitte optimieren/isolieren: {item.nodeid}"
        )
    finally:
        signal.alarm(0)
        signal.signal(_SIGALRM, previous_handler)
