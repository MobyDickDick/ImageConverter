from __future__ import annotations


def runNonCompositeIterationImpl(
    *,
    mode: str,
    params: dict[str, object],
    stripe_strategy: dict[str, object] | None,
    semantic_mode_visual_override: bool,
    width: int,
    height: int,
    base_name: str,
    description: str,
    perc_img,
    img_path: str,
    print_fn,
    render_embedded_raster_svg_fn,
    build_gradient_stripe_svg_fn,
    build_gradient_stripe_validation_log_lines_fn,
    write_validation_log_fn,
    render_svg_to_numpy_fn,
    record_render_failure_fn,
    write_attempt_artifacts_fn,
    calculate_error_fn,
) -> tuple[str, str, dict[str, object], int, float] | None:
    if mode == "manual_review":
        reason = str(params.get("review_reason", "Manuelle Prüfung erforderlich.")).strip()
        print_fn(f"  -> Überspringe Bild: {reason}")
        write_validation_log_fn(
            [
                "status=skipped_manual_review",
                f"manual_review_reason={reason}",
            ]
        )
        return None

    if stripe_strategy:
        print_fn("  -> Kein Compositing-Befehl erkannt: verwende Gradient-Stripe-Strategie.")
        svg_content = build_gradient_stripe_svg_fn(width, height, stripe_strategy)
        strategy_stop_count = len(list(stripe_strategy.get("stops", [])))
        write_validation_log_fn(
            build_gradient_stripe_validation_log_lines_fn(
                semantic_mode_visual_override=semantic_mode_visual_override,
                strategy_stop_count=strategy_stop_count,
            )
        )
    else:
        print_fn("  -> Kein Compositing-Befehl erkannt: verwende Einzelbild-Konvertierung (embedded raster SVG).")
        svg_content = render_embedded_raster_svg_fn(img_path)
        write_validation_log_fn(["status=non_composite_embedded_svg"])

    svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
    if svg_rendered is None:
        record_render_failure_fn(
            "non_composite_embedded_render_failed",
            svg_content=svg_content,
            params_snapshot=params,
        )
        return None

    write_attempt_artifacts_fn(svg_content, svg_rendered)
    return base_name, description, params, 1, calculate_error_fn(perc_img, svg_rendered)
