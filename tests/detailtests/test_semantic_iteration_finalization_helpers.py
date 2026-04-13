from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticIterationFinalization as helpers


def test_finalize_semantic_badge_run_impl_returns_iteration_tuple() -> None:
    captured: dict[str, object] = {}

    result = helpers.finalizeSemanticBadgeRunImpl(
        base="AC0811_S",
        desc="desc",
        perc_base_name="AC0811",
        filename="AC0811_S.jpg",
        width=64,
        height=64,
        badge_params={"cx": 1.0},
        params={"mode": "semantic_badge"},
        semantic_audit_row={"status": "semantic_ok"},
        semantic_ok_validation_lines=["status=semantic_ok"],
        perc_img="img",
        write_validation_log_fn=lambda lines: captured.update({"lines": lines}),
        finalize_semantic_badge_iteration_result_fn=lambda **kwargs: (
            captured.update({"finalize_kwargs": kwargs}) or ({"mode": "semantic_badge"}, 1.25)
        ),
    )

    assert result == ("AC0811_S", "desc", {"mode": "semantic_badge"}, 1, 1.25)
    assert captured["lines"] == ["status=semantic_ok"]
    assert captured["finalize_kwargs"] == {
        "base_name": "AC0811",
        "filename": "AC0811_S.jpg",
        "width": 64,
        "height": 64,
        "badge_params": {"cx": 1.0},
        "params": {"mode": "semantic_badge"},
        "semantic_audit_row": {"status": "semantic_ok"},
        "target_img": "img",
    }


def test_finalize_semantic_badge_run_impl_returns_none_on_failed_finalize() -> None:
    captured: dict[str, object] = {}

    result = helpers.finalizeSemanticBadgeRunImpl(
        base="AC0811_S",
        desc="desc",
        perc_base_name="AC0811",
        filename="AC0811_S.jpg",
        width=64,
        height=64,
        badge_params={"cx": 1.0},
        params={"mode": "semantic_badge"},
        semantic_audit_row=None,
        semantic_ok_validation_lines=["status=semantic_ok"],
        perc_img="img",
        write_validation_log_fn=lambda lines: captured.update({"lines": lines}),
        finalize_semantic_badge_iteration_result_fn=lambda **kwargs: None,
    )

    assert result is None
    assert captured["lines"] == ["status=semantic_ok"]
