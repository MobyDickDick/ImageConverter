            return Action._masked_union_error_in_bbox(img_orig, elem_render, mask_orig, mask_orig)

        return Action._element_match_error(
            img_orig,
            elem_render,
            probe,
            element,
            mask_orig=mask_orig,
        )

    @staticmethod
    def _optimize_element_color_bracket(
        img_orig: np.ndarray,
        params: dict,
        element: str,
        mask_orig: np.ndarray,
        logs: list[str],
    ) -> bool:
        if bool(params.get("lock_colors", False)):
            logs.append(f"{element}: Farb-Bracketing übersprungen (Farben gesperrt)")
            return False
        if mask_orig is None or int(mask_orig.sum()) == 0:
            return False

        changed_any = False
        local_gray = Action._mean_gray_for_mask(img_orig, mask_orig)
        sampled = int(round(local_gray)) if local_gray is not None else None

        for color_key in Action._element_color_keys(element, params):
            current = int(round(float(params.get(color_key, 128))))
            low_limit = int(Action._clip_scalar(int(params.get(f"{color_key}_min", 0)), 0, 255))
            high_limit = int(Action._clip_scalar(int(params.get(f"{color_key}_max", 255)), 0, 255))
            if low_limit > high_limit:
                low_limit, high_limit = high_limit, low_limit
            candidates = {
                int(Action._clip_scalar(current - 32, low_limit, high_limit)),
                int(Action._clip_scalar(current - 16, low_limit, high_limit)),
                int(Action._clip_scalar(current - 8, low_limit, high_limit)),
                int(Action._clip_scalar(current, low_limit, high_limit)),
                int(Action._clip_scalar(current + 8, low_limit, high_limit)),
                int(Action._clip_scalar(current + 16, low_limit, high_limit)),
                int(Action._clip_scalar(current + 32, low_limit, high_limit)),
            }
            if sampled is not None:
                candidates.add(int(Action._clip_scalar(sampled, low_limit, high_limit)))
            if element == "circle" and color_key == "fill_gray":
                candidates.update(int(Action._clip_scalar(v, low_limit, high_limit)) for v in {200, 210, 220, 230, 240})
            if color_key in {"stroke_gray", "stem_gray", "text_gray"}:
                candidates.update(int(Action._clip_scalar(v, low_limit, high_limit)) for v in {96, 112, 128, 144, 152, 160, 171})

            values = sorted(v for v in candidates if low_limit <= v <= high_limit)
            errs = [
                Action._element_error_for_color(img_orig, params, element, color_key, v, mask_orig)
                for v in values
            ]
            if not all(math.isfinite(e) for e in errs):
                logs.append(
                    f"{element}: Farb-Bracketing abgebrochen ({color_key}) wegen nicht-finiten Fehlern "
                    + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
                )
                continue

            best_idx = Action._argmin_index(errs)
            best_value = int(values[best_idx])

            if best_value == min(values) or best_value == max(values):
                s_best, s_err, s_improved = Action._stochastic_survivor_scalar(
                    float(current),
                    float(min(values)),
                    float(max(values)),
                    lambda v: Action._element_error_for_color(
                        img_orig,
                        params,
                        element,
                        color_key,
                        int(Action._clip_scalar(int(round(v)), low_limit, high_limit)),
                        mask_orig,
                    ),
                    snap=lambda v: int(Action._clip_scalar(int(round(v)), low_limit, high_limit)),
                    seed=1301,
                )
                if s_improved:
                    best_value = int(Action._clip_scalar(int(round(s_best)), low_limit, high_limit))
                    logs.append(
                        f"{element}: Farb-Stochastic-Survivor aktiviert ({color_key}={best_value}, err={s_err:.3f})"
                    )

            if best_value == current:
                logs.append(
                    f"{element}: Farb-Bracketing keine relevante Änderung ({color_key}: {current}); Kandidaten="
                    + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
                )
                continue

            params[color_key] = int(best_value)
            changed_any = True
            logs.append(
                f"{element}: Farb-Bracketing {color_key} {current}->{best_value}; Kandidaten="
                + ", ".join(f"{v}->{e:.3f}" for v, e in zip(values, errs, strict=False))
            )
