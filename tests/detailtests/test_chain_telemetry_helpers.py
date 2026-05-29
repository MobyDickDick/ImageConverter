from __future__ import annotations

from src.iCCModules import imageCompositeConverterChainTelemetry as telemetry_helpers
from src.iCCModules import imageCompositeConverterCompositeSvg as composite_svg_helpers


class _NoRefCv2:
    pass


def test_chain_telemetry_harmonizes_phase_terms_and_step_quality_metrics() -> None:
    params = {
        "geometry_phase_mode": "elementwise_geometry_ir",
        "policy_phase_decision": "geometry_wins",
        "geometry_ir_step_log": [
            {"accepted": True},
            {"accepted": False},
            {"accepted": True},
        ],
    }

    telemetry = telemetry_helpers.summarizeChainTelemetryImpl(params)

    assert telemetry["geometry_phase"] == "geometry_chain.elementwise"
    assert telemetry["policy_phase"] == "policy.geometry_selected"
    assert telemetry["step_count"] == 3
    assert telemetry["step_accepted_count"] == 2
    assert telemetry["step_success_rate"] == 0.666667
    assert telemetry["override_applied"] is False
    assert telemetry["placeholder_emergency_used"] is False


def test_chain_telemetry_tracks_overrides_and_placeholder_emergency_rate() -> None:
    geometry = telemetry_helpers.summarizeChainTelemetryImpl(
        {
            "geometry_phase_mode": "elementwise_geometry_ir",
            "policy_phase_decision": "geometry_wins",
            "geometry_ir_step_log": [{"accepted": True}],
        }
    )
    sample = telemetry_helpers.summarizeChainTelemetryImpl(
        {
            "geometry_phase_mode": "elementwise_geometry_ir",
            "policy_phase_decision": "sample_wins",
            "override_reason": "sample_error_not_worse_than_geometry",
            "fallback_render_mode": "pure_svg_placeholder",
        }
    )

    aggregate = telemetry_helpers.aggregateChainTelemetryImpl([geometry, sample])
    line = telemetry_helpers.formatChainTelemetryLineImpl(sample)

    assert sample["policy_phase"] == "policy.reference_selected"
    assert sample["override_applied"] is True
    assert sample["placeholder_emergency_used"] is True
    assert aggregate == {
        "conversion_count": 2,
        "mean_step_success_rate": 0.5,
        "override_frequency": 0.5,
        "placeholder_emergency_rate": 0.5,
    }
    assert "chain_telemetry:" in line
    assert "policy_phase=policy.reference_selected" in line
    assert "placeholder_emergency=True" in line


def test_composite_svg_records_r5_chain_telemetry_on_params(tmp_path) -> None:
    params = {
        "top_source_ref": None,
        "bottom_shape": "none",
        "geometry_ir": [{"kind": "RectBorder", "id": "rect", "bbox": [0.2, 0.2, 0.6, 0.6]}],
        "geometry_ir_step_log": [{"accepted": True}],
    }

    svg = composite_svg_helpers.generateCompositeSvgImpl(
        100,
        100,
        params,
        str(tmp_path),
        0.5,
        os_module=__import__("os"),
        cv2_module=_NoRefCv2(),
        trace_image_segment_fn=lambda *_args, **_kwargs: [],
    )

    assert "<rect" in svg
    assert params["chain_phase_telemetry"]["geometry_phase"] == "geometry_chain.elementwise"
    assert params["chain_phase_telemetry"]["policy_phase"] == "policy.geometry_selected"
    assert params["chain_phase_telemetry_line"].startswith("chain_telemetry:")
