        elif element == "arm" and probe.get("arm_enabled"):
            x1 = float(probe.get("arm_x1", 0.0))
            y1 = float(probe.get("arm_y1", 0.0))
            x2 = float(probe.get("arm_x2", 0.0))
            y2 = float(probe.get("arm_y2", 0.0))
            dx = x2 - x1
            dy = y2 - y1
            cur_len = float(math.hypot(dx, dy))
            if cur_len <= 1e-6:
                return float("inf")
            new_len = float(Action._clip_scalar(extent_value, 1.0, float(max(w, h))))
            ux = dx / cur_len
            uy = dy / cur_len

            if probe.get("circle_enabled", True) and all(k in probe for k in ("cx", "cy", "r")):
                # Keep the endpoint at the circle edge fixed and optimize the free side
                # length only. Symmetric center-scaling shortens both ends and can make
                # AC0812/AC0814 horizontal connectors visibly too short.
                Action._reanchor_arm_to_circle_edge(probe, float(probe.get("r", 0.0)))
                ax1 = float(probe.get("arm_x1", x1))
                ay1 = float(probe.get("arm_y1", y1))
                ax2 = float(probe.get("arm_x2", x2))
                ay2 = float(probe.get("arm_y2", y2))

                cx = float(probe.get("cx", 0.0))
                cy = float(probe.get("cy", 0.0))
                d1 = float(math.hypot(ax1 - cx, ay1 - cy))
                d2 = float(math.hypot(ax2 - cx, ay2 - cy))

                if d1 <= d2:
                    ix, iy = ax1, ay1
                    probe["arm_x2"] = float(Action._clip_scalar(ix + (ux * new_len), 0.0, float(w - 1)))
                    probe["arm_y2"] = float(Action._clip_scalar(iy + (uy * new_len), 0.0, float(h - 1)))
                else:
                    ix, iy = ax2, ay2
                    probe["arm_x1"] = float(Action._clip_scalar(ix - (ux * new_len), 0.0, float(w - 1)))
                    probe["arm_y1"] = float(Action._clip_scalar(iy - (uy * new_len), 0.0, float(h - 1)))
            else:
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                half = new_len / 2.0
                probe["arm_x1"] = float(Action._clip_scalar(cx - (ux * half), 0.0, float(w - 1)))
                probe["arm_y1"] = float(Action._clip_scalar(cy - (uy * half), 0.0, float(h - 1)))
                probe["arm_x2"] = float(Action._clip_scalar(cx + (ux * half), 0.0, float(w - 1)))
                probe["arm_y2"] = float(Action._clip_scalar(cy + (uy * half), 0.0, float(h - 1)))
        else:
            return float("inf")

        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, element))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        mask_orig = Action.extract_badge_element_mask(img_orig, probe, element)
        if mask_orig is None:
            return float("inf")

        return Action._element_match_error(img_orig, elem_render, probe, element, mask_orig=mask_orig)

    @staticmethod
    def _optimize_element_extent_bracket(img_orig: np.ndarray, params: dict, element: str, logs: list[str]) -> bool:
        h, w = img_orig.shape[:2]
        if element == "stem" and params.get("stem_enabled"):
            current = float(params.get("stem_bottom", 0.0)) - float(params.get("stem_top", 0.0))
            key_label = "stem_len"
            low_bound = 1.0
            high_bound = float(h)
            forced_abs_min = params.get("stem_len_min")
            if forced_abs_min is not None:
                low_bound = max(low_bound, float(forced_abs_min))
            forced_min_ratio = params.get("stem_len_min_ratio")
            if forced_min_ratio is not None:
                min_ratio = float(max(0.0, min(1.0, float(forced_min_ratio))))
                low_bound = max(low_bound, current * min_ratio)
            if h <= 15 and not bool(params.get("draw_text", True)):
                low_bound = max(low_bound, 5.5)
            # Keep bottom-anchored stem variants (e.g. AC0811_S) from collapsing
            # into near-invisible stubs when anti-aliased extraction under-segments
            # thin line pixels in element-only masks.
            is_bottom_anchored = float(params.get("stem_bottom", 0.0)) >= float(h) - 0.5
            if (
                forced_min_ratio is None
                and is_bottom_anchored
                and params.get("circle_enabled", True)
                and all(k in params for k in ("cy", "r"))
            ):
                min_ratio = float(params.get("stem_len_min_ratio", 0.65))
                low_bound = max(low_bound, current * max(0.0, min(1.0, min_ratio)))
                # Tiny AC0811-like badges need a visibly readable stem even when
                # contour extraction underestimates the semantic template length.
                if h <= 15 and not bool(params.get("draw_text", True)):
                    low_bound = max(low_bound, 5.5)
        elif element == "arm" and params.get("arm_enabled"):
            dx = float(params.get("arm_x2", 0.0)) - float(params.get("arm_x1", 0.0))
            dy = float(params.get("arm_y2", 0.0)) - float(params.get("arm_y1", 0.0))
            current = float(math.hypot(dx, dy))
            key_label = "arm_len"
            low_bound = 1.0
            high_bound = float(max(w, h))
            forced_abs_min = params.get("arm_len_min")
