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
