        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        # Keep the source mask conservative across radius probes.
        # - For shrink probes, stay anchored to the current radius so we don't
        #   hide missing source pixels (collapse bias, observed on AC0833_L).
        # - For growth probes, expand the source mask context to the larger
        #   radius so underestimated starts (e.g. AC0812_L) can still move up.
        source_mask_params = dict(params)
        source_mask_params["r"] = max(float(params.get("r", 0.0)), float(probe["r"]))
        if source_mask_params.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(source_mask_params, float(source_mask_params["r"]))
        if source_mask_params.get("stem_enabled"):
            source_mask_params["stem_top"] = float(source_mask_params.get("cy", 0.0)) + float(source_mask_params["r"])

        mask_orig = Action.extract_badge_element_mask(img_orig, source_mask_params, "circle")
        if mask_orig is None:
            return float("inf")
        mask_svg = Action.extract_badge_element_mask(elem_render, probe, "circle")
        if mask_svg is None:
            return float("inf")

        return Action._element_match_error(
            img_orig,
            elem_render,
            probe,
            "circle",
            mask_orig=mask_orig,
            mask_svg=mask_svg,
        )

    @staticmethod
    def _full_badge_error_for_circle_radius(img_orig: np.ndarray, params: dict, radius_value: float) -> float:
        """Evaluate the full SVG roundtrip error for a specific circle radius."""
        h, w = img_orig.shape[:2]
        if not params.get("circle_enabled", True):
            return float("inf")

        probe = dict(params)
        min_r = float(
            max(
                1.0,
                float(probe.get("min_circle_radius", 1.0)),
                float(probe.get("circle_radius_lower_bound_px", 1.0)),
            )
        )
        max_r = max(min_r, (float(min(w, h)) * 0.48))
        if bool(probe.get("allow_circle_overflow", False)):
            max_r = max(max_r, float(max(w, h)) * 1.25, min_r + 0.5)
        probe["r"] = float(Action._clip_scalar(radius_value, min_r, max_r))
        probe = Action._clamp_circle_inside_canvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(Action.generate_badge_svg(w, h, probe), w, h))
        if render is None:
            return float("inf")
        return float(Action.calculate_error(img_orig, render))

    @staticmethod
    def _select_circle_radius_plateau_candidate(
        img_orig: np.ndarray,
        params: dict,
        evaluations: dict[float, float],
        current_radius: float,
    ) -> tuple[float, float, float]:
        """Pick a stable radius from a near-optimal plateau instead of a noisy local minimum."""
        finite = sorted((float(radius), float(err)) for radius, err in evaluations.items() if math.isfinite(err))
        if not finite:
            return current_radius, float("inf"), float("inf")

        best_radius, best_err = min(finite, key=lambda pair: pair[1])
        plateau_eps = max(0.06, best_err * 0.02)
        plateau = [(radius, err) for radius, err in finite if err <= best_err + plateau_eps]
        if not plateau:
            try:
                full_err = float(Action._full_badge_error_for_circle_radius(img_orig, params, best_radius))
            except Exception:
                full_err = float("inf")
            return best_radius, best_err, full_err

        plateau_mid = Action._snap_half((plateau[0][0] + plateau[-1][0]) / 2.0)
        candidate_radii = {best_radius, plateau_mid}
        if len(plateau) >= 2:
            candidate_radii.add(plateau[-1][0])

        min_r = float(
            max(
                1.0,
                params.get("min_circle_radius", 1.0),
                params.get("circle_radius_lower_bound_px", 1.0),
            )
        )
        max_r = float(params.get("max_circle_radius", max(radius for radius, _err in finite)))
        if bool(params.get("allow_circle_overflow", False)):
