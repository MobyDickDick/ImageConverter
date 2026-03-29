                half = best_len / 2.0
                params["stem_top"] = float(Action._clip_scalar(center - half, 0.0, float(h - 1)))
                params["stem_bottom"] = float(Action._clip_scalar(center + half, params["stem_top"] + 1.0, float(h)))
        else:
            x1 = float(params.get("arm_x1", 0.0))
            y1 = float(params.get("arm_y1", 0.0))
            x2 = float(params.get("arm_x2", 0.0))
            y2 = float(params.get("arm_y2", 0.0))
            dx = x2 - x1
            dy = y2 - y1
            cur_len = float(math.hypot(dx, dy))
            if cur_len <= 1e-6:
                return False
            ux = dx / cur_len
            uy = dy / cur_len

            if params.get("circle_enabled", True) and all(k in params for k in ("cx", "cy", "r")):
                Action._reanchor_arm_to_circle_edge(params, float(params.get("r", 0.0)))
                ax1 = float(params.get("arm_x1", x1))
                ay1 = float(params.get("arm_y1", y1))
                ax2 = float(params.get("arm_x2", x2))
                ay2 = float(params.get("arm_y2", y2))

                cx = float(params.get("cx", 0.0))
                cy = float(params.get("cy", 0.0))
                d1 = float(math.hypot(ax1 - cx, ay1 - cy))
                d2 = float(math.hypot(ax2 - cx, ay2 - cy))

                if d1 <= d2:
                    ix, iy = ax1, ay1
                    if abs(uy) <= 0.35:
                        iy = cy
                        ix = cx - float(params.get("r", 0.0)) if ix <= cx else cx + float(params.get("r", 0.0))
                    params["arm_x2"] = float(Action._clip_scalar(ix + (ux * best_len), 0.0, float(w - 1)))
                    params["arm_y2"] = float(Action._clip_scalar(iy + (uy * best_len), 0.0, float(h - 1)))
                    params["arm_x1"] = float(ix)
                    params["arm_y1"] = float(iy)
                else:
                    ix, iy = ax2, ay2
                    if abs(uy) <= 0.35:
                        iy = cy
                        ix = cx - float(params.get("r", 0.0)) if ix <= cx else cx + float(params.get("r", 0.0))
                    params["arm_x1"] = float(Action._clip_scalar(ix - (ux * best_len), 0.0, float(w - 1)))
                    params["arm_y1"] = float(Action._clip_scalar(iy - (uy * best_len), 0.0, float(h - 1)))
                    params["arm_x2"] = float(ix)
                    params["arm_y2"] = float(iy)
            else:
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                half = best_len / 2.0
                params["arm_x1"] = float(Action._clip_scalar(cx - (ux * half), 0.0, float(w - 1)))
                params["arm_y1"] = float(Action._clip_scalar(cy - (uy * half), 0.0, float(h - 1)))
                params["arm_x2"] = float(Action._clip_scalar(cx + (ux * half), 0.0, float(w - 1)))
                params["arm_y2"] = float(Action._clip_scalar(cy + (uy * half), 0.0, float(h - 1)))

        logs.append(
            f"{element}: Längen-Bracketing {key_label} {current:.3f}->{best_len:.3f}; Kandidaten="
            + ", ".join(f"{v:.3f}->{e:.3f}" for v, e in zip(candidates, candidate_errors, strict=False))
        )
        return True

    @staticmethod
    def _optimize_element_width_bracket(img_orig: np.ndarray, params: dict, element: str, logs: list[str]) -> bool:
        h, w = img_orig.shape[:2]
        info = Action._element_width_key_and_bounds(element, params, w, h, img_orig=img_orig)
        if info is None:
            return False

        key, low_bound, high_bound = info
        current = float(params.get(key, 0.0))
        if current <= 0.0:
            return False

        # Breiteres Mehrpunkt-Bracketing über den gesamten plausiblen Bereich.
        low = float(low_bound)
        high = float(high_bound)
        if not (low < high):
            logs.append(
                f"{element}: Breiten-Bracketing übersprungen ({key}: current={current:.3f}, "
                f"Range={low_bound:.3f}..{high_bound:.3f})"
            )
            return False

        if key.endswith("_font_scale"):
            candidates = sorted(
                {
                    round(low, 3),
                    round(low + (high - low) * 0.15, 3),
                    round(low + (high - low) * 0.30, 3),
                    round(low + (high - low) * 0.50, 3),
                    round(low + (high - low) * 0.70, 3),
                    round(low + (high - low) * 0.85, 3),
                    round(high, 3),
                    round(max(low, min(high, current * 0.85)), 3),
                    round(max(low, min(high, current)), 3),
                    round(max(low, min(high, current * 1.15)), 3),
                }
            )
        else:
            candidates = sorted(
