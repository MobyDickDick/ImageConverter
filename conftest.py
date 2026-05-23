from __future__ import annotations

import os
from pathlib import Path

import pytest


HEAVY_TEST_MODULES = {
    "test_image_composite_converter.py",
    "test_satisfactory_regression_battery.py",
    "test_conversion_regression_smoke.py",
}


def _heavy_tests_enabled() -> bool:
    return os.environ.get("RUN_HEAVY_CONVERSION_TESTS", "0") == "1"


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool:  # type: ignore[override]
    """Keep long-running conversion suites as explicit follow-up tasks.

    Default profile skips collection of heavy conversion modules.
    Run them explicitly with RUN_HEAVY_CONVERSION_TESTS=1.
    """

    if _heavy_tests_enabled():
        return False
    return collection_path.name in HEAVY_TEST_MODULES


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _heavy_tests_enabled():
        return

    skip_blocking = pytest.mark.skip(
        reason=(
            "AUFGABE: blocking_conversion separat ausführen "
            "(setze RUN_HEAVY_CONVERSION_TESTS=1)."
        )
    )
    for item in items:
        if item.get_closest_marker("blocking_conversion") is not None:
            item.add_marker(skip_blocking)
