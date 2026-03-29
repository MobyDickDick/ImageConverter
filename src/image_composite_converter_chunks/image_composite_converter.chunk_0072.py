                {
                    Action._snap_half(low),
                    Action._snap_half(low + (high - low) * 0.25),
                    Action._snap_half((low + high) / 2.0),
                    Action._snap_half(low + (high - low) * 0.75),
                    Action._snap_half(high),
                    Action._snap_half(Action._clip_scalar(current, low, high)),
                }
            )
        candidate_errors = [Action._element_error_for_width(img_orig, params, element, v) for v in candidates]
        if not all(math.isfinite(e) for e in candidate_errors):
            logs.append(
                f"{element}: Breiten-Bracketing abgebrochen ({key}) wegen nicht-finiten Fehlern "
                + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
            )
            return False

        best_idx = Action._argmin_index(candidate_errors)
        best_width = candidates[best_idx]

        boundary_best = abs(float(best_width) - low) < 0.02 or abs(float(best_width) - high) < 0.02
        if boundary_best:
            snap_fn = (lambda v: float(round(v, 3))) if key.endswith("_font_scale") else Action._snap_half
            s_best, s_err, s_improved = Action._stochastic_survivor_scalar(
                current,
                low,
                high,
                lambda v: Action._element_error_for_width(img_orig, params, element, float(v)),
                snap=snap_fn,
                seed=1201,
            )
            if s_improved:
                best_width = float(s_best)
                logs.append(
                    f"{element}: Breiten-Stochastic-Survivor aktiviert ({key}={best_width:.3f}, err={s_err:.3f})"
                )

        old = float(params.get(key, current))
        if abs(best_width - old) < 0.02:
            logs.append(
                f"{element}: Breiten-Bracketing keine relevante Änderung ({key}: {old:.3f}); "
                f"Kandidaten="
                + ", ".join(
                    f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False)
                )
            )
            return False

        if key in {"stroke_circle", "arm_stroke", "stem_width"}:
            best_width = Action._snap_int_px(best_width, minimum=1.0)
        elif key.endswith("_font_scale"):
            best_width = float(round(best_width, 3))
        else:
            best_width = Action._snap_half(best_width)

        params[key] = best_width
        if key == "stem_width" and params.get("stem_enabled"):
            params["stem_x"] = Action._snap_half(float(params.get("cx", params.get("stem_x", 0.0))) - (params["stem_width"] / 2.0))
        logs.append(
            f"{element}: Breiten-Bracketing {key} {old:.3f}->{best_width:.3f}; "
            f"Kandidaten="
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return True


    @staticmethod
    def _element_color_keys(element: str, params: dict) -> list[str]:
        if element == "circle" and params.get("circle_enabled", True):
            return ["fill_gray", "stroke_gray"]
        if element == "stem" and params.get("stem_enabled"):
            return ["stem_gray"]
        if element == "arm" and params.get("arm_enabled"):
            return ["stroke_gray"]
        if element == "text" and params.get("draw_text", True):
            return ["text_gray"]
        return []

    @staticmethod
    def _element_error_for_color(
        img_orig: np.ndarray,
        params: dict,
        element: str,
        color_key: str,
        color_value: int,
        mask_orig: np.ndarray,
    ) -> float:
        probe = dict(params)
        probe[color_key] = int(Action._clip_scalar(color_value, 0, 255))

        h, w = img_orig.shape[:2]
        elem_svg = Action.generate_badge_svg(w, h, Action._element_only_params(probe, element))
        elem_render = Action._fit_to_original_size(img_orig, Action.render_svg_to_numpy(elem_svg, w, h))
        if elem_render is None:
            return float("inf")

        if element == "circle":
            # Color-only circle probing should be photometric against a stable
            # source region. Do not let threshold-induced mask area changes in
            # candidate renders bias toward darker/larger-looking circles.
