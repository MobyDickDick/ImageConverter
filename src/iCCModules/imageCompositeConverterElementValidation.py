"""Extracted element-validation helpers for imageCompositeConverter."""

from __future__ import annotations

def refineStemGeometryFromMasksImpl(
    params: dict,
    mask_orig,
    mask_svg,
    w: int,
    *,
    mask_bbox_fn,
    estimate_vertical_stem_from_mask_fn,
    clip_scalar_fn,
    snap_int_px_fn,
    snap_half_fn,
) -> tuple[bool, str | None]:
    """Refine stem width/position when validation detects a geometric mismatch."""
    orig_bbox = mask_bbox_fn(mask_orig)
    svg_bbox = mask_bbox_fn(mask_svg)
    if orig_bbox is None or svg_bbox is None:
        return False, None

    ox1, _oy1, ox2, _oy2 = orig_bbox
    sx1, _sy1, sx2, _sy2 = svg_bbox
    orig_w = max(1.0, (ox2 - ox1) + 1.0)
    svg_w = max(1.0, (sx2 - sx1) + 1.0)
    ratio = svg_w / orig_w

    expected_cx = float(params.get("cx", (ox1 + ox2) / 2.0))
    stroke = float(params.get("stroke_circle", 1.0))
    # Skip a small band right below the circle edge so anti-aliased ring/fill
    # pixels do not inflate stem width estimation.
    y_start = float(params.get("stem_top", 0.0)) + max(1.0, stroke * 2.0)
    y_end = float(params.get("stem_bottom", mask_orig.shape[0]))
    est = estimate_vertical_stem_from_mask_fn(mask_orig, expected_cx, int(y_start), int(y_end))

    if est is not None:
        est_cx, est_width = est
        min_w = max(1.0, float(params.get("stroke_circle", 1.0)) * 0.70)
        max_w = max(
            min_w,
            min(
                float(params.get("stem_width_max", float(w) * 0.18)),
                min(float(w) * 0.18, float(params.get("r", 1.0)) * 0.80),
            ),
        )
        target_width = max(min_w, min(est_width, max_w))
        if bool(params.get("lock_stem_center_to_circle", False)):
            circle_cx = float(params.get("cx", est_cx))
            max_offset = float(params.get("stem_center_lock_max_offset", max(0.35, target_width * 0.75)))
            target_cx = float(clip_scalar_fn(est_cx, circle_cx - max_offset, circle_cx + max_offset))
        else:
            target_cx = est_cx
        estimate_mode = "iter"
    else:
        if 0.95 <= ratio <= 1.05:
            return False, None
        target_width = float(params.get("stem_width", svg_w)) * (orig_w / svg_w)
        stem_width_cap = float(params.get("stem_width_max", float(w) * 0.20))
        target_width = max(1.0, min(target_width, min(float(w) * 0.20, stem_width_cap)))
        target_cx = (ox1 + ox2) / 2.0
        estimate_mode = "bbox"

    old_width = float(params.get("stem_width", svg_w))
    width_delta = abs(target_width - old_width)
    ratio_after = target_width / max(1.0, orig_w)

    if width_delta < 0.05 and 0.90 <= ratio_after <= 1.12:
        return False, None

    stem_width_cap = float(params.get("stem_width_max", float(w) * 0.20))
    target_width = min(target_width, stem_width_cap)
    target_width = snap_int_px_fn(target_width, minimum=1.0)
    old_x = float(params.get("stem_x", 0.0))
    old_w = float(params.get("stem_width", 1.0))
    new_x = snap_half_fn(max(0.0, min(float(w) - target_width, target_cx - (target_width / 2.0))))
    if abs(target_width - old_w) < 0.05 and abs(new_x - old_x) < 0.05:
        return False, None
    params["stem_width"] = target_width
    params["stem_x"] = new_x
    return True, (
        f"stem: Breitenkorrektur mode={estimate_mode}, ratio={ratio:.3f}, "
        f"alt={old_width:.3f}, neu={target_width:.3f}"
    )


def validateBadgeByElementsImpl(
    img_orig,
    params: dict,
    *,
    max_rounds: int,
    debug_out_dir: str | None,
    apply_circle_geometry_penalty: bool,
    stop_when_error_below_threshold: bool,
    cv2_module,
    copy_module,
    math_module,
    os_module,
    generate_badge_svg_fn,
    fit_to_original_size_fn,
    render_svg_to_numpy_fn,
    create_diff_image_fn,
    write_debug_image_fn,
    element_only_params_fn,
    extract_badge_element_mask_fn,
    element_region_mask_fn,
    element_match_error_fn,
    refine_stem_geometry_from_masks_fn,
    optimize_element_width_bracket_fn,
    optimize_element_extent_bracket_fn,
    optimize_circle_center_bracket_fn,
    optimize_circle_radius_bracket_fn,
    optimize_global_parameter_vector_sampling_fn,
    calculate_error_fn,
    activate_ac08_adaptive_locks_fn,
    release_ac08_adaptive_locks_fn,
    optimize_element_color_bracket_fn,
    apply_canonical_badge_colors_fn,
):
    h, w = img_orig.shape[:2]
    logs: list[str] = []
    elements = ["circle"]
    if params.get("stem_enabled"):
        elements.append("stem")
    if params.get("arm_enabled"):
        elements.append("arm")
    if params.get("draw_text", True):
        elements.append("text")
    best_params = copy_module.deepcopy(params)
    best_full_err = float("inf")
    previous_round_state: tuple[tuple[tuple[str, float], ...], float] | None = None
    fallback_search_active = False
    if bool(params.get("ac08_small_variant_mode", False)):
        logs.append(
            "small_variant_mode_active: "
            f"reason={params.get('ac08_small_variant_reason', 'unknown')}, "
            f"min_dim={float(params.get('ac08_small_variant_min_dim', 0.0)):.3f}, "
            f"mask_dilate_px={int(params.get('validation_mask_dilate_px', 0) or 0)}, "
            f"text_mode={params.get('text_mode', '')}, "
            f"arm_min_ratio={float(params.get('arm_len_min_ratio', 0.0)):.3f}, "
            f"stem_min_ratio={float(params.get('stem_len_min_ratio', 0.0)):.3f}"
        )

    def _stagnationFingerprint(current_params: dict) -> tuple[tuple[str, float], ...]:
        tracked_keys = (
            "cx",
            "cy",
            "r",
            "arm_len",
            "stem_width",
            "arm_stroke",
            "text_scale",
            "co2_font_scale",
            "voc_scale",
        )
        fingerprint: list[tuple[str, float]] = []
        for key in tracked_keys:
            value = current_params.get(key)
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            fingerprint.append((key, round(numeric_value, 4)))
        return tuple(fingerprint)

    for round_idx in range(max_rounds):
        logs.append(f"Runde {round_idx + 1}: elementweise Validierung gestartet")
        full_svg = generate_badge_svg_fn(w, h, params)
        full_render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(full_svg, w, h))
        if full_render is None:
            logs.append("Abbruch: SVG konnte nicht gerendert werden")
            break

        if debug_out_dir:
            full_diff = create_diff_image_fn(img_orig, full_render)
            write_debug_image_fn(os_module.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_full_diff.png"), full_diff)

        round_changed = False
        for element in elements:
            elem_svg = generate_badge_svg_fn(w, h, element_only_params_fn(params, element))
            elem_render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(elem_svg, w, h))
            if elem_render is None:
                logs.append(f"{element}: Element-SVG konnte nicht gerendert werden")
                continue

            mask_orig = extract_badge_element_mask_fn(img_orig, params, element)
            mask_svg = extract_badge_element_mask_fn(elem_render, params, element)
            if mask_orig is None or mask_svg is None:
                logs.append(f"{element}: Element konnte nicht extrahiert werden")
                continue

            if debug_out_dir:
                elem_focus_mask = element_region_mask_fn(h, w, params, element)
                elem_diff = create_diff_image_fn(img_orig, elem_render, elem_focus_mask)
                write_debug_image_fn(
                    os_module.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_{element}_diff.png"),
                    elem_diff,
                )

            elem_err = element_match_error_fn(img_orig, elem_render, params, element, mask_orig=mask_orig, mask_svg=mask_svg)
            logs.append(f"{element}: Fehler={elem_err:.3f}")

            if element == "stem" and params.get("stem_enabled"):
                changed, refine_log = refine_stem_geometry_from_masks_fn(params, mask_orig, mask_svg, w)
                if refine_log:
                    logs.append(refine_log)
                if changed:
                    round_changed = True
                    logs.append("stem: Geometrie nach Elementabgleich aktualisiert")

            width_changed = optimize_element_width_bracket_fn(img_orig, params, element, logs)
            if width_changed:
                round_changed = True

            extent_changed = optimize_element_extent_bracket_fn(img_orig, params, element, logs)
            if extent_changed:
                round_changed = True

            circle_geometry_penalty_active = apply_circle_geometry_penalty and not fallback_search_active
            if element == "circle" and circle_geometry_penalty_active:
                center_changed = optimize_circle_center_bracket_fn(img_orig, params, logs)
                if center_changed:
                    round_changed = True
                radius_changed = optimize_circle_radius_bracket_fn(img_orig, params, logs)
                if radius_changed:
                    round_changed = True

        global_search_changed = optimize_global_parameter_vector_sampling_fn(
            img_orig,
            params,
            logs,
        )
        if global_search_changed:
            round_changed = True

        full_svg = generate_badge_svg_fn(w, h, params)
        full_render = fit_to_original_size_fn(img_orig, render_svg_to_numpy_fn(full_svg, w, h))
        full_err = calculate_error_fn(img_orig, full_render)
        logs.append(f"Runde {round_idx + 1}: Gesamtfehler={full_err:.3f}")
        if math_module.isfinite(full_err) and full_err < best_full_err:
            best_full_err = full_err
            best_params = copy_module.deepcopy(params)

        current_round_state = (_stagnationFingerprint(params), round(float(full_err), 6))
        if previous_round_state is not None:
            same_fingerprint = current_round_state[0] == previous_round_state[0]
            nearly_same_error = abs(current_round_state[1] - previous_round_state[1]) <= 1e-6
            if same_fingerprint and nearly_same_error:
                logs.append(
                    "stagnation_detected: identischer Parameter-Fingerprint und praktisch unveränderter Gesamtfehler"
                )
                adaptive_unlock_applied = activate_ac08_adaptive_locks_fn(
                    params,
                    logs,
                    full_err=full_err,
                    reason="identical_fingerprint",
                )
                if adaptive_unlock_applied:
                    previous_round_state = None
                    fallback_search_active = True
                    if round_idx + 1 < max_rounds:
                        logs.append(
                            "switch_to_fallback_search: adaptive family-unlocks aktiviert und Circle-Geometry-Penalty deaktiviert"
                        )
                        continue
                if not fallback_search_active and round_idx + 1 < max_rounds:
                    release_ac08_adaptive_locks_fn(
                        params,
                        logs,
                        reason="stagnation_same_fingerprint",
                        current_error=full_err,
                    )
                    fallback_search_active = True
                    logs.append(
                        "switch_to_fallback_search: deaktiviere Circle-Geometry-Penalty für eine letzte Ausweichrunde"
                    )
                    previous_round_state = current_round_state
                    continue
                logs.append("stopped_due_to_stagnation: Validierung vorzeitig beendet")
                break
        previous_round_state = current_round_state

        if full_err <= 8.0:
            if stop_when_error_below_threshold:
                logs.append("Gesamtfehler unter Schwellwert, Validierung beendet")
                break
            logs.append("Gesamtfehler unter Schwellwert, Suche nach besserem Optimum wird fortgesetzt")
        elif round_idx >= 1:
            release_ac08_adaptive_locks_fn(
                params,
                logs,
                reason="high_residual_error",
                current_error=full_err,
            )

        if round_idx + 1 >= max_rounds:
            break

        if not round_changed:
            adaptive_unlock_applied = activate_ac08_adaptive_locks_fn(
                params,
                logs,
                full_err=full_err,
                reason="no_geometry_movement",
            )
            if adaptive_unlock_applied:
                previous_round_state = None
                fallback_search_active = True
                if round_idx + 1 < max_rounds:
                    logs.append(
                        "switch_to_fallback_search: adaptive family-unlocks aktiviert und Circle-Geometry-Penalty deaktiviert"
                    )
                    continue
            if not fallback_search_active and round_idx + 1 < max_rounds:
                release_ac08_adaptive_locks_fn(
                    params,
                    logs,
                    reason="stagnation_no_geometry_change",
                    current_error=full_err,
                )
                fallback_search_active = True
                logs.append(
                    "stagnation_detected: keine relevante Geometrieänderung in der letzten Validierungsrunde"
                )
                logs.append(
                    "switch_to_fallback_search: deaktiviere Circle-Geometry-Penalty für eine letzte Ausweichrunde"
                )
                continue
            logs.append("stopped_due_to_stagnation: keine weitere Parameterbewegung erkennbar")
            break

    if math_module.isfinite(best_full_err):
        params.clear()
        params.update(best_params)

    for element in elements:
        if element == "text" and not params.get("draw_text", True):
            continue
        mask_orig = extract_badge_element_mask_fn(img_orig, params, element)
        if mask_orig is None:
            continue
        color_changed = optimize_element_color_bracket_fn(img_orig, params, element, mask_orig, logs)
        if color_changed:
            logs.append(f"{element}: Farboptimierung in Abschlussphase angewendet")

    params.update(apply_canonical_badge_colors_fn(params))

    return logs
