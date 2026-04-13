from src.iCCModules import imageCompositeConverterSemanticAuditBootstrap as helpers


def test_build_pending_semantic_audit_row_impl_returns_none_when_base_not_targeted() -> None:
    result = helpers.buildPendingSemanticAuditRowImpl(
        base_name="AC0800_S",
        filename="AC0800_S.jpg",
        params={"mode": "semantic_badge"},
        should_create_semantic_audit_for_base_name_fn=lambda *_args, **_kwargs: False,
        get_base_name_from_file_fn=lambda name: name,
        build_semantic_audit_record_kwargs_fn=lambda **_kwargs: {"status": "semantic_pending"},
        semantic_audit_record_fn=lambda **_kwargs: {"status": "semantic_pending"},
    )

    assert result is None


def test_build_pending_semantic_audit_row_impl_builds_pending_row() -> None:
    captured: dict[str, object] = {}

    def _build_kwargs(*, filename: str, params: dict[str, object], status: str) -> dict[str, object]:
        captured["build"] = {"filename": filename, "params": params, "status": status}
        return {
            "variant": filename.rsplit(".", 1)[0],
            "status": status,
            "semantic_elements": ["circle"],
            "missing_elements": [],
            "unexpected_elements": [],
            "semantic_priority_order": [],
            "semantic_conflicts": [],
            "semantic_sources": {},
        }

    def _record(**kwargs):
        captured["record"] = kwargs
        return kwargs

    result = helpers.buildPendingSemanticAuditRowImpl(
        base_name="AC0811_S",
        filename="AC0811_S.jpg",
        params={"mode": "semantic_badge", "elements": ["circle"]},
        should_create_semantic_audit_for_base_name_fn=lambda *_args, **_kwargs: True,
        get_base_name_from_file_fn=lambda name: name,
        build_semantic_audit_record_kwargs_fn=_build_kwargs,
        semantic_audit_record_fn=_record,
    )

    assert captured["build"] == {
        "filename": "AC0811_S.jpg",
        "params": {"mode": "semantic_badge", "elements": ["circle"]},
        "status": "semantic_pending",
    }
    assert captured["record"]["base_name"] == "AC0811_S"
    assert result["status"] == "semantic_pending"
