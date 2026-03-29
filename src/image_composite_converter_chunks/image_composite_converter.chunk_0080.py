            elements.append("text")
        best_params = copy.deepcopy(params)
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

        def _stagnation_fingerprint(current_params: dict) -> tuple[tuple[str, float], ...]:
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
            full_svg = Action.generate_badge_svg(w, h, params)
            full_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(full_svg, w, h))
            if full_render is None:
                logs.append("Abbruch: SVG konnte nicht gerendert werden")
                break

            if debug_out_dir:
                full_diff = Action.create_diff_image(img_orig, full_render)
                cv2.imwrite(os.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_full_diff.png"), full_diff)

            round_changed = False
            for element in elements:
                elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(params, element))
                elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
                if elem_render is None:
                    logs.append(f"{element}: Element-SVG konnte nicht gerendert werden")
                    continue

                mask_orig = Action.extract_badge_element_mask(img_orig, params, element)
                mask_svg = Action.extract_badge_element_mask(elem_render, params, element)
                if mask_orig is None or mask_svg is None:
                    logs.append(f"{element}: Element konnte nicht extrahiert werden")
                    continue

                if debug_out_dir:
                    elem_focus_mask = Action._element_region_mask(h, w, params, element)
                    elem_diff = Action.create_diff_image(img_orig, elem_render, elem_focus_mask)
                    cv2.imwrite(
                        os.path.join(debug_out_dir, f"round_{round_idx + 1:02d}_{element}_diff.png"),
                        elem_diff,
                    )

                elem_err = Action._element_match_error(img_orig, elem_render, params, element, mask_orig=mask_orig, mask_svg=mask_svg)
                logs.append(f"{element}: Fehler={elem_err:.3f}")

                if element == "stem" and params.get("stem_enabled"):
                    changed, refine_log = Action._refine_stem_geometry_from_masks(params, mask_orig, mask_svg, w)
                    if refine_log:
                        logs.append(refine_log)
                    if changed:
                        round_changed = True
                        logs.append("stem: Geometrie nach Elementabgleich aktualisiert")

                width_changed = Action._optimize_element_width_bracket(img_orig, params, element, logs)
                if width_changed:
                    round_changed = True

                extent_changed = Action._optimize_element_extent_bracket(img_orig, params, element, logs)
                if extent_changed:
                    round_changed = True

                circle_geometry_penalty_active = apply_circle_geometry_penalty and not fallback_search_active
                if element == "circle" and circle_geometry_penalty_active:
                    center_changed = Action._optimize_circle_center_bracket(img_orig, params, logs)
                    if center_changed:
                        round_changed = True
                    radius_changed = Action._optimize_circle_radius_bracket(img_orig, params, logs)
                    if radius_changed:
                        round_changed = True

