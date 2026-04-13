from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticPostValidation as helpers


def test_prepare_semantic_badge_post_validation_impl_applies_guard_redraw_and_log() -> None:
    calls: list[tuple[str, object]] = []

    def _enforce(base_name, elements, badge_params, width, height):
        calls.append(("enforce", (base_name, elements, dict(badge_params), width, height)))
        updated = dict(badge_params)
        updated["guarded"] = True
        updated["arm_enabled"] = True
        return updated

    def _redraw(badge_params, width, height):
        calls.append(("redraw", (dict(badge_params), width, height)))
        updated = dict(badge_params)
        updated["redrawn"] = True
        return updated, ["redraw-step"]

    def _append(*, validation_logs, badge_params):
        calls.append(("append", (list(validation_logs), dict(badge_params))))
        return list(validation_logs) + ["connector-guard-log"]

    badge_params, validation_logs, redraw_logs = helpers.prepareSemanticBadgePostValidationImpl(
        base_name="AC0812",
        elements=["SEMANTIC: Kreis mit Stiel"],
        badge_params={"mode": "semantic_badge"},
        width=200,
        height=120,
        validation_logs=["initial-log"],
        enforce_semantic_connector_expectation_fn=_enforce,
        apply_redraw_variation_fn=_redraw,
        append_semantic_connector_expectation_log_fn=_append,
    )

    assert badge_params["guarded"] is True
    assert badge_params["redrawn"] is True
    assert validation_logs == ["initial-log", "connector-guard-log"]
    assert redraw_logs == ["redraw-step"]
    assert [name for name, _ in calls] == ["enforce", "redraw", "append"]
