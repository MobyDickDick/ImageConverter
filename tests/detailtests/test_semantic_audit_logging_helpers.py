from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticAuditLogging as helpers


def test_build_semantic_audit_log_lines_empty_for_none() -> None:
    assert helpers.buildSemanticAuditLogLinesImpl(None) == []


def test_build_semantic_audit_log_lines_includes_mismatch_reason_when_requested() -> None:
    row = {
        "status": "semantic_mismatch",
        "description_lookup_keys": ["AC0811_S", "AC0811"],
        "recognized_description_elements": ["kreis", "strich"],
        "derived_elements": ["vertical_connector"],
        "semantic_priority_order": ["family", "description"],
        "semantic_conflicts": ["orientation_conflict"],
        "mismatch_reason": "expected vertical connector",
    }

    lines = helpers.buildSemanticAuditLogLinesImpl(row, include_mismatch_reason=True)

    assert "semantic_audit_status=semantic_mismatch" in lines
    assert "semantic_audit_lookup_keys=AC0811_S | AC0811" in lines
    assert "semantic_audit_priority_order=family > description" in lines
    assert "semantic_audit_conflicts=orientation_conflict" in lines
    assert "semantic_audit_mismatch_reason=expected vertical connector" in lines
