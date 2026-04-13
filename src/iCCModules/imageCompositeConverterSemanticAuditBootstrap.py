from __future__ import annotations


def buildPendingSemanticAuditRowImpl(
    *,
    base_name: str,
    filename: str,
    params: dict[str, object],
    should_create_semantic_audit_for_base_name_fn,
    get_base_name_from_file_fn,
    build_semantic_audit_record_kwargs_fn,
    semantic_audit_record_fn,
):
    if not should_create_semantic_audit_for_base_name_fn(
        base_name,
        get_base_name_from_file_fn=get_base_name_from_file_fn,
    ):
        return None

    return semantic_audit_record_fn(
        base_name=base_name,
        **build_semantic_audit_record_kwargs_fn(
            filename=filename,
            params=params,
            status="semantic_pending",
        ),
    )
