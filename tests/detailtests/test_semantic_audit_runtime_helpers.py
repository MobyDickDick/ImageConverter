from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticAuditRuntime as helpers


def test_should_create_semantic_audit_for_base_name_impl_normalizes_variant_suffix() -> None:
    enabled = helpers.shouldCreateSemanticAuditForBaseNameImpl(
        "ac0811_L_sia",
        get_base_name_from_file_fn=lambda value: "AC0811",
    )
    disabled = helpers.shouldCreateSemanticAuditForBaseNameImpl(
        "ac0882_M",
        get_base_name_from_file_fn=lambda value: "AC0882",
    )

    assert enabled is True
    assert disabled is False


def test_build_semantic_audit_record_kwargs_impl_collects_semantic_fields() -> None:
    params = {
        "description_fragments": [{"text": "text"}],
        "elements": ["circle", "arm"],
        "semantic_priority_order": ["circle"],
        "semantic_conflicts": ["none"],
        "semantic_sources": {"circle": "template"},
    }

    kwargs = helpers.buildSemanticAuditRecordKwargsImpl(
        filename="AC0811_L.jpg",
        params=params,
        status="semantic_mismatch",
        mismatch_reasons=["issue-a"],
    )

    assert kwargs == {
        "filename": "AC0811_L.jpg",
        "description_fragments": [{"text": "text"}],
        "semantic_elements": ["circle", "arm"],
        "status": "semantic_mismatch",
        "mismatch_reasons": ["issue-a"],
        "semantic_priority_order": ["circle"],
        "semantic_conflicts": ["none"],
        "semantic_sources": {"circle": "template"},
    }
