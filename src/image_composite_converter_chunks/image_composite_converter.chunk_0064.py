            max_r = max(max_r, min_r + 0.5)
        bounded_candidates = sorted(
            float(Action._clip_scalar(Action._snap_half(float(radius)), min_r, max_r))
            for radius in candidate_radii
        )

        choice_pool: list[tuple[float, float, float, float]] = []
        for radius in bounded_candidates:
            if radius in evaluations:
                elem_err = float(evaluations[radius])
            else:
                try:
                    elem_err = float(Action._element_error_for_circle_radius(img_orig, params, radius))
                except Exception:
                    elem_err = float("inf")
            try:
                full_err = float(Action._full_badge_error_for_circle_radius(img_orig, params, radius))
            except Exception:
                full_err = float("inf")
            if not math.isfinite(elem_err) and not math.isfinite(full_err):
                continue
            distance_to_mid = abs(radius - plateau_mid)
            choice_pool.append((radius, elem_err, full_err, distance_to_mid))

        if not choice_pool:
            return current_radius, best_err, float("inf")

        chosen_radius, chosen_elem_err, chosen_full_err, _distance_to_mid = min(
            choice_pool,
            key=lambda item: (
                round(item[2], 6),
                round(item[1], 6),
                item[3],
                abs(item[0] - current_radius),
            ),
        )
        return chosen_radius, chosen_elem_err, chosen_full_err


    @staticmethod
    def _element_error_for_circle_pose(
        img_orig: np.ndarray,
        params: dict,
        *,
        cx_value: float,
        cy_value: float,
        radius_value: float,
    ) -> float:
        h, w = img_orig.shape[:2]
        if not params.get("circle_enabled", True):
            return float("inf")

        probe = dict(params)
        max_r = max(1.0, (float(min(w, h)) * 0.48))
        probe["cx"] = Action._snap_half(float(Action._clip_scalar(cx_value, 0.0, float(w - 1))))
        probe["cy"] = Action._snap_half(float(Action._clip_scalar(cy_value, 0.0, float(h - 1))))
        min_r = float(max(1.0, probe.get("min_circle_radius", 1.0)))
        probe["r"] = Action._snap_half(float(Action._clip_scalar(radius_value, min_r, max_r)))
        probe = Action._clamp_circle_inside_canvas(probe, w, h)

        if probe.get("arm_enabled"):
            Action._reanchor_arm_to_circle_edge(probe, float(probe["r"]))

        if probe.get("stem_enabled"):
            probe["stem_top"] = float(probe.get("cy", 0.0)) + float(probe["r"])

        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, "circle"))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        # See `_element_error_for_circle_radius`: use a stable source mask that
        # is independent from the tested candidate pose.
        mask_orig = Action.extract_badge_element_mask(img_orig, params, "circle")
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
    def _reanchor_arm_to_circle_edge(params: dict, radius: float) -> None:
        """Keep arm orientation but snap the circle-side endpoint to the new radius."""
        if not params.get("arm_enabled"):
            return
        if not all(k in params for k in ("arm_x1", "arm_y1", "arm_x2", "arm_y2", "cx", "cy")):
            return

        cx = float(params.get("cx", 0.0))
        cy = float(params.get("cy", 0.0))
        x1 = float(params.get("arm_x1", cx))
