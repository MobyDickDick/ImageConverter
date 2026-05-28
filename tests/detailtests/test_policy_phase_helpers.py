from __future__ import annotations

from src.iCCModules import imageCompositeConverterPolicyPhase as policy_helpers


def test_policy_phase_keeps_geometry_when_chain_wins() -> None:
    geometry_ir = [{"kind": "RectBorder", "id": "main_rect"}]
    params = {"geometry_phase_mode": "elementwise_geometry_ir", "contract_status": "ok"}

    selected = policy_helpers.applyPolicyPhaseAfterGeometryImpl(params, geometry_ir)

    assert selected == geometry_ir
    assert params["geometry_phase_result"] == {
        "mode": "elementwise_geometry_ir",
        "has_geometry_ir": True,
        "element_count": 1,
    }
    assert params["policy_phase_decision"] == "geometry_wins"
    assert params["override_reason"] is None


def test_policy_phase_lets_sample_win_after_geometry_comparison() -> None:
    geometry_ir = [{"kind": "RectBorder", "id": "main_rect"}]
    params = {
        "geometry_phase_mode": "elementwise_geometry_ir",
        "contract_status": "ok",
        "policy_sample_comparison": {"geometry_error": 42.0, "sample_error": 10.0},
    }

    selected = policy_helpers.applyPolicyPhaseAfterGeometryImpl(params, geometry_ir)

    assert selected == []
    assert params["geometry_phase_result"]["has_geometry_ir"] is True
    assert params["policy_phase_decision"] == "sample_wins"
    assert params["override_reason"] == "sample_error_not_worse_than_geometry"


def test_policy_phase_guard_blocks_only_after_geometry_result_is_logged() -> None:
    geometry_ir = [{"kind": "RectBorder", "id": "main_rect"}]
    params = {"geometry_phase_mode": "elementwise_geometry_ir", "contract_status": "insufficient_description"}

    selected = policy_helpers.applyPolicyPhaseAfterGeometryImpl(params, geometry_ir)

    assert selected == []
    assert params["geometry_phase_result"]["element_count"] == 1
    assert params["policy_phase_decision"] == "guard_blocks"
    assert params["override_reason"] == "description_contract_insufficient"
