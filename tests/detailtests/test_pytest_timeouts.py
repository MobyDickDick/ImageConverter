"""Exercise the Unix timeout branch through the real Pluggy hook protocol."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pluggy
import pytest


@pytest.fixture
def timeout_plugin(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "conftest.py"
    spec = importlib.util.spec_from_file_location("timeout_plugin_under_test", path)
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)
    previous_handler = object()
    calls = []

    def set_handler(sig, handler):
        calls.append(("signal", sig, handler))

    monkeypatch.setattr(plugin, "_SIGALRM", 14)
    monkeypatch.setattr(plugin, "_PER_TEST_TIMEOUT_SECONDS", 30)
    monkeypatch.setattr(plugin, "signal", SimpleNamespace(
        getsignal=lambda sig: previous_handler,
        signal=set_handler,
        alarm=lambda seconds: calls.append(("alarm", seconds)),
    ))
    return plugin, calls, previous_handler


def run_hook(plugin, callback, marker=None):
    class Hooks:
        @pytest.hookspec
        def pytest_runtest_call(self, item):
            """Run a test."""

    class TestCall:
        @pytest.hookimpl
        def pytest_runtest_call(self, item):
            return callback()

    manager = pluggy.PluginManager("pytest")
    manager.add_hookspecs(Hooks)
    manager.register(plugin)
    manager.register(TestCall())
    item = SimpleNamespace(
        nodeid="example::test_conversion",
        get_closest_marker=lambda name: marker if name == "per_test_timeout" else None,
    )
    return manager.hook.pytest_runtest_call(item=item)


@pytest.mark.parametrize("strict, seconds", [(False, 30), (True, 2100)])
def test_timeout_uses_hook_exception_protocol_and_restores_signal(timeout_plugin, strict, seconds):
    plugin, calls, previous_handler = timeout_plugin
    marker = pytest.mark.per_test_timeout(seconds, fail_on_timeout=True).mark if strict else None

    def expire():
        plugin._timeout_handler(14, None)

    expected = pytest.fail.Exception if strict else pytest.xfail.Exception
    with pytest.raises(expected, match=rf"Testlauf > {seconds}s.*example::test_conversion"):
        run_hook(plugin, expire, marker)
    assert calls == [
        ("signal", 14, plugin._timeout_handler),
        ("alarm", seconds),
        ("alarm", 0),
        ("signal", 14, previous_handler),
    ]


def test_success_preserves_hook_result_and_cancels_alarm(timeout_plugin):
    plugin, calls, previous_handler = timeout_plugin
    assert run_hook(plugin, lambda: "passed") == ["passed"]
    assert calls[-2:] == [("alarm", 0), ("signal", 14, previous_handler)]


def test_other_errors_remain_failures_and_cancel_alarm(timeout_plugin):
    plugin, calls, previous_handler = timeout_plugin

    def fail():
        raise ValueError("quality regression")

    with pytest.raises(ValueError, match="quality regression"):
        run_hook(plugin, fail)
    assert calls[-2:] == [("alarm", 0), ("signal", 14, previous_handler)]


def test_environment_timeout_remains_the_default(timeout_plugin, monkeypatch):
    plugin, calls, _ = timeout_plugin
    monkeypatch.setattr(plugin, "_PER_TEST_TIMEOUT_SECONDS", 120)
    run_hook(plugin, lambda: None)
    assert ("alarm", 120) in calls


@pytest.mark.parametrize("disable", ["platform", "default", "marker"])
def test_disabled_timeout_preserves_result_without_signal_calls(timeout_plugin, monkeypatch, disable):
    plugin, calls, _ = timeout_plugin
    marker = None
    if disable == "platform":
        monkeypatch.setattr(plugin, "_SIGALRM", None)
    elif disable == "default":
        monkeypatch.setattr(plugin, "_PER_TEST_TIMEOUT_SECONDS", 0)
    else:
        marker = pytest.mark.per_test_timeout(0).mark
    assert run_hook(plugin, lambda: "passed", marker) == ["passed"]
    assert calls == []


def test_archive_has_strict_timeout_for_both_conversion_modes():
    from tests.test_satisfactory_archive import (
        test_every_archived_satisfactory_image_is_reconverted_and_checked as archive_test,
    )

    marker = next(mark for mark in archive_test.pytestmark if mark.name == "per_test_timeout")
    assert marker.args == (2100,)
    assert marker.kwargs == {"fail_on_timeout": True}


def test_extended_ci_budget_includes_archive_and_remaining_suite():
    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/local-completion-checks.yml").read_text(encoding="utf-8")
    block = workflow.split("  pytest-profile-matrix:\n", 1)[1].split("  safe-baseline:\n", 1)[0]
    assert "timeout-minutes: ${{ matrix.timeout_minutes }}" in block
    assert "- profile: core-green\n            timeout_minutes: 15" in block
    assert "- profile: extended\n            timeout_minutes: 60" in block
