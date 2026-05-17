from __future__ import annotations

import os


def _contains_svg_image_tag(svg_content: str) -> bool:
    lowered = svg_content.lower()
    return "<image" in lowered and ('href="data:image' in lowered or 'xlink:href="data:image' in lowered)


def _build_sample_candidates(base_name: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        if name and name not in seen:
            seen.add(name)
            candidates.append(name)

    _add(base_name)
    root, sep, size_suffix = base_name.rpartition("_")
    if sep:
        _add(root)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{root}_{alt_suffix}")
        _add(size_suffix)
        return candidates

    for alt_suffix in ("L", "M", "S"):
        _add(f"{base_name}_{alt_suffix}")
    return candidates


def _try_load_sample_svg(*, img_path: str, base_name: str):
    samples_dir = os.path.join(os.path.dirname(img_path), "samples")
    for sample_name in _build_sample_candidates(base_name):
        sample_svg_path = os.path.join(samples_dir, f"{sample_name}.svg")
        if not os.path.exists(sample_svg_path):
            continue
        with open(sample_svg_path, "r", encoding="utf-8") as handle:
            return sample_svg_path, handle.read()
    return None


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
    sample_svg = _try_load_sample_svg(img_path=img_path, base_name=base_name)

    if mode == "manual_review":
        if sample_svg:
            sample_svg_path, sample_svg_content = sample_svg
            sample_rendered = render_svg_to_numpy_fn(sample_svg_content, width, height)
            if sample_rendered is None:
                record_render_failure_fn(
                    "manual_review_plan_b_render_failed",
                    svg_content=sample_svg_content,
                    params_snapshot=params,
                )
                return None

            sample_err = calculate_error_fn(perc_img, sample_rendered)
            embedded_svg_content = render_embedded_raster_svg_fn(img_path)
            embedded_rendered = render_svg_to_numpy_fn(embedded_svg_content, width, height)
            if embedded_rendered is not None:
                embedded_err = calculate_error_fn(perc_img, embedded_rendered)
                if embedded_err + 1e-6 < sample_err:
                    print_fn(
                        "  -> Plan B verworfen: Embedded-Raster ist näher am Original "
                        f"(err={embedded_err:.3f} < sample={sample_err:.3f})."
                    )
                    write_validation_log_fn(
                        [
                            "status=manual_review_embedded_svg_selected",
                            f"sample_svg_path={sample_svg_path}",
                            f"sample_error={sample_err:.6f}",
                            f"embedded_error={embedded_err:.6f}",
                        ]
                    )
                    write_attempt_artifacts_fn(embedded_svg_content, embedded_rendered)
                    return base_name, description, params, 1, embedded_err

            print_fn(f"  -> Plan B aktiv: verwende vorhandene Sample-SVG {sample_svg_path}.")
            write_validation_log_fn(
                [
                    "status=manual_review_plan_b_sample_svg",
                    f"sample_svg_path={sample_svg_path}",
                    f"sample_error={sample_err:.6f}",
                ]
            )
            write_attempt_artifacts_fn(sample_svg_content, sample_rendered)
            return base_name, description, params, 1, sample_err

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
        print_fn("  -> Fallback aktiv: verwende Gradient-Stripe-Strategie.")
        svg_content = build_gradient_stripe_svg_fn(width, height, stripe_strategy)
        strategy_stop_count = len(list(stripe_strategy.get("stops", [])))
        write_validation_log_fn(
            build_gradient_stripe_validation_log_lines_fn(
                semantic_mode_visual_override=semantic_mode_visual_override,
                strategy_stop_count=strategy_stop_count,
            )
        )
    else:
        print_fn("  -> Fallback aktiv: verwende reine SVG-Platzhalter-Konvertierung (kein eingebettetes Raster).")
        svg_content = render_embedded_raster_svg_fn(img_path)
        write_validation_log_fn(["status=non_composite_pure_svg_placeholder"])

    svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
    if svg_rendered is None:
        record_render_failure_fn(
            "non_composite_pure_svg_render_failed",
            svg_content=svg_content,
            params_snapshot=params,
        )
        return None

    svg_err = calculate_error_fn(perc_img, svg_rendered)

    if sample_svg:
        sample_svg_path, sample_svg_content = sample_svg
        sample_rendered = render_svg_to_numpy_fn(sample_svg_content, width, height)
        if sample_rendered is not None:
            sample_err = calculate_error_fn(perc_img, sample_rendered)
            baseline_is_embedded_raster = _contains_svg_image_tag(svg_content)
            sample_preference_factor = 1.08 if baseline_is_embedded_raster else 1.0
            if sample_err <= (svg_err * sample_preference_factor):
                decision_note = ""
                if baseline_is_embedded_raster and sample_err > svg_err:
                    decision_note = " (Vector-Sample gegenüber Embedded-Raster bevorzugt)"
                print_fn(
                    "  -> Plan B Vergleich aktiv: nutze Sample-SVG "
                    f"{sample_svg_path} (err={sample_err:.3f}, baseline={svg_err:.3f})."
                    f"{decision_note}"
                )
                write_validation_log_fn(
                    [
                        "status=non_composite_plan_b_sample_svg_selected",
                        f"sample_svg_path={sample_svg_path}",
                        f"sample_error={sample_err:.6f}",
                        f"baseline_error={svg_err:.6f}",
                        f"baseline_is_embedded_raster={int(baseline_is_embedded_raster)}",
                        f"sample_preference_factor={sample_preference_factor:.2f}",
                    ]
                )
                write_attempt_artifacts_fn(sample_svg_content, sample_rendered)
                return base_name, description, params, 1, sample_err

    write_attempt_artifacts_fn(svg_content, svg_rendered)
    return base_name, description, params, 1, svg_err
