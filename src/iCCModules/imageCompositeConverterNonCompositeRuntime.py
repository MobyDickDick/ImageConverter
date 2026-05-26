from __future__ import annotations

import os


def _build_vector_placeholder_svg(width: int, height: int, *, description: str = "") -> str:
    safe_w = max(1, int(width or 1))
    safe_h = max(1, int(height or 1))
    desc = (description or "Automatisch erzeugte Platzhalter-Vektorgrafik").strip()
    escaped_desc = (
        desc.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{safe_w}" height="{safe_h}" viewBox="0 0 {safe_w} {safe_h}">\n'
        f'  <desc>{escaped_desc}</desc>\n'
        '  <defs>\n'
        '    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="0%">\n'
        '      <stop offset="0%" stop-color="#6d6d6d"/>\n'
        '      <stop offset="50%" stop-color="#d7d7d7"/>\n'
        '      <stop offset="100%" stop-color="#6d6d6d"/>\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        f'  <rect x="0" y="0" width="{safe_w}" height="{safe_h}" fill="url(#bg)"/>\n'
        f'  <line x1="0" y1="0" x2="{safe_w}" y2="{safe_h}" stroke="#8e8e8e" stroke-width="1"/>\n'
        f'  <line x1="{safe_w}" y1="0" x2="0" y2="{safe_h}" stroke="#8e8e8e" stroke-width="1"/>\n'
        f'  <rect x="{max(1, safe_w//4)}" y="{max(1, safe_h//10)}" width="{max(2, safe_w//2)}" height="{max(2, safe_h//8)}" fill="#4a4a4a" rx="1"/>\n'
        f'  <line x1="{max(2, safe_w//2 - safe_w//8)}" y1="{max(2, safe_h//6)}" x2="{max(3, safe_w//2 - safe_w//20)}" y2="{max(2, safe_h//6)}" stroke="#f2f2f2" stroke-width="1"/>\n'
        f'  <line x1="{max(2, safe_w//2 + safe_w//20)}" y1="{max(2, safe_h//6)}" x2="{max(3, safe_w//2 + safe_w//8)}" y2="{max(2, safe_h//6)}" stroke="#f2f2f2" stroke-width="1"/>\n'
        '</svg>\n'
    )

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
    else:
        for alt_suffix in ("L", "M", "S"):
            _add(f"{base_name}_{alt_suffix}")

    family_name = root if sep else base_name

    if family_name.startswith("AC") and len(family_name) > 2:
        se_alias = f"SE{family_name[2:]}"
        _add(se_alias)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{se_alias}_{alt_suffix}")
    if family_name.startswith("SE") and len(family_name) > 2:
        ac_alias = f"AC{family_name[2:]}"
        _add(ac_alias)
        for alt_suffix in ("L", "M", "S"):
            _add(f"{ac_alias}_{alt_suffix}")

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

        if stripe_strategy:
            print_fn("  -> Plan B aktiv: nutze erkannte Gradient-Stripe-Strategie trotz Manual-Review.")
            svg_content = build_gradient_stripe_svg_fn(width, height, stripe_strategy)
            strategy_stop_count = len(list(stripe_strategy.get("stops", [])))
            write_validation_log_fn(
                build_gradient_stripe_validation_log_lines_fn(
                    semantic_mode_visual_override=semantic_mode_visual_override,
                    strategy_stop_count=strategy_stop_count,
                )
            )
            svg_rendered = render_svg_to_numpy_fn(svg_content, width, height)
            if svg_rendered is None:
                record_render_failure_fn(
                    "manual_review_gradient_stripe_render_failed",
                    svg_content=svg_content,
                    params_snapshot=params,
                )
                return None
            svg_err = calculate_error_fn(perc_img, svg_rendered)
            write_attempt_artifacts_fn(svg_content, svg_rendered)
            return base_name, description, params, 1, svg_err

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
        svg_content = _build_vector_placeholder_svg(width, height, description=description)
        write_validation_log_fn(["status=non_composite_pure_svg_placeholder_vector"])

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
            # Favor curated sample SVGs over generated placeholders when they are
            # in a similar quality range, because sample assets usually carry
            # richer semantic structure than our generic non-composite fallback.
            sample_preference_factor = 1.08 if baseline_is_embedded_raster else 1.25
            prefer_sample_svg = baseline_is_embedded_raster or sample_err <= (svg_err * sample_preference_factor)
            if prefer_sample_svg:
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
        else:
            if _contains_svg_image_tag(svg_content):
                print_fn(
                    "  -> Plan B Vergleich aktiv: nutze Sample-SVG "
                    f"{sample_svg_path} trotz fehlendem Raster-Render (Embedded-Raster vermeiden)."
                )
                write_validation_log_fn(
                    [
                        "status=non_composite_plan_b_sample_svg_selected",
                        f"sample_svg_path={sample_svg_path}",
                        "sample_render_failed=1",
                        f"baseline_error={svg_err:.6f}",
                        "baseline_is_embedded_raster=1",
                        "sample_preference_factor=forced",
                    ]
                )
                write_attempt_artifacts_fn(sample_svg_content, None)
                return base_name, description, params, 1, svg_err

    write_attempt_artifacts_fn(svg_content, svg_rendered)
    return base_name, description, params, 1, svg_err
