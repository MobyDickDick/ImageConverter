from __future__ import annotations


def buildSemanticTextModeValidationLogLineImpl(*, draw_text: bool, text_mode: object) -> str:
    if not draw_text:
        return "semantic-guard: Text bewusst deaktiviert (plain-ring Familie ohne Buchstabe)."
    return "semantic-guard: Textmodus aktiv (" + str(text_mode if text_mode is not None else "unknown") + ")."


def collectSemanticBadgeValidationLogsImpl(
    *,
    perc_img,
    badge_params: dict[str, object],
    badge_validation_rounds: int,
    debug_dir: str | None,
    validate_badge_by_elements_fn,
) -> list[str]:
    validation_logs: list[str] = [
        buildSemanticTextModeValidationLogLineImpl(
            draw_text=bool(badge_params.get("draw_text", False)),
            text_mode=badge_params.get("text_mode", "unknown"),
        )
    ]
    validation_logs.extend(
        validate_badge_by_elements_fn(
            perc_img,
            badge_params,
            max_rounds=max(1, int(badge_validation_rounds)),
            debug_out_dir=debug_dir,
        )
    )
    return validation_logs
