from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def pytest_configure(config: pytest.Config) -> None:
    # pytest normally retains the last three complete temporary test trees.
    # Own the default directory so failures also release their generated data.
    # An explicitly supplied --basetemp remains under the caller's control.
    if config.option.basetemp is None:
        parent = Path(__file__).resolve().parent/'.tmp'
        parent.mkdir(exist_ok=True)
        work = TemporaryDirectory(prefix='pytest-', dir=parent)
        config._imageconverter_temp = work
        config.option.basetemp = str(Path(work.name)/'tests')


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config: pytest.Config) -> None:
    work = getattr(config, '_imageconverter_temp', None)
    if work is not None:
        work.cleanup()


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
