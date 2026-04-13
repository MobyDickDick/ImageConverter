from __future__ import annotations

from src.iCCModules import imageCompositeConverterSemanticValidationRuntime as helpers


def test_build_semantic_text_mode_validation_log_line_impl_reports_plain_ring() -> None:
    assert helpers.buildSemanticTextModeValidationLogLineImpl(draw_text=False, text_mode="co2") == (
        "semantic-guard: Text bewusst deaktiviert (plain-ring Familie ohne Buchstabe)."
    )


def test_collect_semantic_badge_validation_logs_impl_uses_guard_line_and_round_floor() -> None:
    captured: dict[str, object] = {}

    def _validate(img, params, *, max_rounds: int, debug_out_dir: str | None):
        captured["img"] = img
        captured["params"] = params
        captured["max_rounds"] = max_rounds
        captured["debug_out_dir"] = debug_out_dir
        return ["semantic-check: ok"]

    badge_params = {"draw_text": True, "text_mode": "co2"}
    logs = helpers.collectSemanticBadgeValidationLogsImpl(
        perc_img="img",
        badge_params=badge_params,
        badge_validation_rounds=0,
        debug_dir="/tmp/sem-debug",
        validate_badge_by_elements_fn=_validate,
    )

    assert logs == [
        "semantic-guard: Textmodus aktiv (co2).",
        "semantic-check: ok",
    ]
    assert captured == {
        "img": "img",
        "params": badge_params,
        "max_rounds": 1,
        "debug_out_dir": "/tmp/sem-debug",
    }


def test_finalize_semantic_badge_iteration_result_impl_attaches_audit_and_error() -> None:
    captured: dict[str, object] = {}

    def _finalize(**kwargs):
        captured["finalize_kwargs"] = kwargs
        return {"finalized": True}

    def _record_failure(*args, **kwargs):
        raise AssertionError("render failure callback must not be called")

    params = {"mode": "semantic_badge"}
    semantic_audit_row = {"status": "semantic_ok"}
    result = helpers.finalizeSemanticBadgeIterationResultImpl(
        base_name="AC0223",
        filename="AC0223_M.jpg",
        width=128,
        height=64,
        badge_params={"cx": 12.0},
        params=params,
        semantic_audit_row=semantic_audit_row,
        target_img="target",
        finalize_ac0223_badge_params_fn=_finalize,
        generate_badge_svg_fn=lambda w, h, badge: f"svg-{w}x{h}-{badge['finalized']}",
        render_svg_to_numpy_fn=lambda svg, w, h: f"rendered:{svg}:{w}x{h}",
        write_attempt_artifacts_fn=lambda svg, rendered: captured.update({"svg": svg, "rendered": rendered}),
        record_render_failure_fn=_record_failure,
        calculate_error_fn=lambda target, rendered: 4.25 if target == "target" and "rendered:svg-128x64-True" in rendered else -1.0,
    )

    assert result == ({"mode": "semantic_badge", "semantic_audit": semantic_audit_row}, 4.25)
    assert params == {"mode": "semantic_badge"}
    assert captured["svg"] == "svg-128x64-True"
    assert captured["rendered"] == "rendered:svg-128x64-True:128x64"
    assert captured["finalize_kwargs"] == {
        "base_name": "AC0223",
        "filename": "AC0223_M.jpg",
        "width": 128,
        "height": 64,
        "badge_params": {"cx": 12.0},
    }


def test_finalize_semantic_badge_iteration_result_impl_records_render_failure() -> None:
    captured: dict[str, object] = {}

    result = helpers.finalizeSemanticBadgeIterationResultImpl(
        base_name="AC0831",
        filename="AC0831_S.jpg",
        width=96,
        height=96,
        badge_params={"r": 18.0},
        params={"mode": "semantic_badge"},
        semantic_audit_row=None,
        target_img="target",
        finalize_ac0223_badge_params_fn=lambda **kwargs: kwargs["badge_params"],
        generate_badge_svg_fn=lambda w, h, badge: "svg-content",
        render_svg_to_numpy_fn=lambda svg, w, h: None,
        write_attempt_artifacts_fn=lambda svg, rendered: captured.update({"unexpected_write": True}),
        record_render_failure_fn=lambda reason, **kwargs: captured.update({"reason": reason, **kwargs}),
        calculate_error_fn=lambda target, rendered: 0.0,
    )

    assert result is None
    assert "unexpected_write" not in captured
    assert captured["reason"] == "semantic_badge_final_render_failed"
    assert captured["svg_content"] == "svg-content"
    assert captured["params_snapshot"] == {"r": 18.0}
