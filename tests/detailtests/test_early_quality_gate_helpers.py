from __future__ import annotations

from src.iCCModules import imageCompositeConverterEarlyQualityGate as gate_helpers


def test_gate_uses_persisted_report_threshold_conservatively() -> None:
    gate = gate_helpers.resolveEarlyQualityGateImpl(
        {
            "allowed_error_per_pixel": 1.25,
            "early_abort": {"probe_iterations": 4, "threshold_multiplier": 6.0},
        },
        [],
        successful_threshold_fn=lambda _rows: float("inf"),
        environ={},
    )

    assert gate == {
        "enabled": True,
        "probe_iterations": 4,
        "baseline_error_per_pixel": 1.25,
        "threshold_multiplier": 6.0,
        "abort_error_per_pixel": 7.5,
        "source": "quality-config",
    }
    assert gate_helpers.shouldAbortAfterProbeImpl(
        {"error_per_pixel": 7.51}, requested_iterations=20, gate=gate
    )
    assert not gate_helpers.shouldAbortAfterProbeImpl(
        {"error_per_pixel": 7.5}, requested_iterations=20, gate=gate
    )


def test_gate_uses_successful_history_when_config_has_no_threshold() -> None:
    gate = gate_helpers.resolveEarlyQualityGateImpl(
        {},
        [{"variant": "AC0010", "error_per_pixel": 0.4}],
        successful_threshold_fn=lambda _rows: 0.5,
        environ={},
    )

    assert gate["enabled"] is True
    assert gate["baseline_error_per_pixel"] == 0.5
    assert gate["abort_error_per_pixel"] == 4.0
    assert gate["source"] == "successful-conversions-mean-plus-2std"


def test_gate_stays_disabled_without_trustworthy_report_history() -> None:
    gate = gate_helpers.resolveEarlyQualityGateImpl(
        {},
        [],
        successful_threshold_fn=lambda _rows: float("inf"),
        environ={},
    )

    assert gate["enabled"] is False
    assert not gate_helpers.shouldAbortAfterProbeImpl(
        {"error_per_pixel": 999.0}, requested_iterations=100, gate=gate
    )


def test_gate_can_be_disabled_by_environment() -> None:
    gate = gate_helpers.resolveEarlyQualityGateImpl(
        {"allowed_error_per_pixel": 1.0},
        [],
        successful_threshold_fn=lambda _rows: float("inf"),
        environ={"ICC_EARLY_QUALITY_ABORT": "0"},
    )

    assert gate["enabled"] is False


def test_zero_placeholder_threshold_does_not_enable_gate() -> None:
    gate = gate_helpers.resolveEarlyQualityGateImpl(
        {"allowed_error_per_pixel": 0.0},
        [],
        successful_threshold_fn=lambda _rows: float("inf"),
        environ={},
    )

    assert gate["enabled"] is False
    assert gate["source"] == "unavailable"
