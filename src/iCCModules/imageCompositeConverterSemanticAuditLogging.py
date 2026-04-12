from __future__ import annotations


def buildSemanticAuditLogLinesImpl(
    semantic_audit_row: dict[str, object] | None,
    *,
    include_mismatch_reason: bool = False,
) -> list[str]:
    if semantic_audit_row is None:
        return []

    lines = [
        f"semantic_audit_status={semantic_audit_row.get('status', '')}",
        "semantic_audit_lookup_keys=" + " | ".join(
            str(value) for value in semantic_audit_row.get("description_lookup_keys", [])
        ),
        "semantic_audit_recognized_description_elements=" + " | ".join(
            str(value) for value in semantic_audit_row.get("recognized_description_elements", [])
        ),
        "semantic_audit_derived_elements=" + " | ".join(
            str(value) for value in semantic_audit_row.get("derived_elements", [])
        ),
        "semantic_audit_priority_order=" + " > ".join(
            str(value) for value in semantic_audit_row.get("semantic_priority_order", [])
        ),
        "semantic_audit_conflicts=" + " | ".join(
            str(value) for value in semantic_audit_row.get("semantic_conflicts", [])
        ),
    ]
    if include_mismatch_reason:
        lines.append(f"semantic_audit_mismatch_reason={semantic_audit_row.get('mismatch_reason', '')}")
    return lines
