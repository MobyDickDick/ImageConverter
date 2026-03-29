
                # Step 3: only if still necessary, shift cluster minimally left.
                overflow = x2 - inner_right
                if overflow > 0.0:
                    co_x -= overflow
                    x1 -= overflow
                    subscript_x -= overflow
                    x2 -= overflow

            # Keep the left side inside the inner circle as well.
            left_overflow = inner_left - x1
            if left_overflow > 0.0:
                co_x += left_overflow
                x1 += left_overflow
                subscript_x += left_overflow
                x2 += left_overflow

        # Capital glyphs usually appear slightly high when simply middle-anchored.
        # Apply a proportional optical correction so the label sits visually centered.
        # A stronger correction keeps the "CO" run from looking top-heavy in tiny
        # AC08xx badges where antialiasing exaggerates baseline drift.
        # Large variants (e.g. AC0820_L) can still look top-heavy with a fixed
        # correction. Nudge bigger badges slightly further down while keeping the
        # small-size behavior effectively unchanged.
        optical_bias = float(params.get("co2_optical_bias", 0.090 + (0.015 * min(1.0, r / 12.0))))
        y_base = cy + float(params.get("co2_dy", 0.0)) + (font_size * optical_bias)
        subscript_offset = font_size * float(params.get("co2_subscript_offset_scale", 0.18))
        height = font_size * 0.95

        # Keep text vertically within the circle's clear area.
        stroke = max(0.8, float(params.get("stroke_circle", 1.0)))
        inner_top = cy - max(1.0, r - stroke)
        inner_bottom = cy + max(1.0, r - stroke)
        top = y_base - (height / 2.0)
        bottom = y_base + (height / 2.0)
        if top < inner_top:
            delta = inner_top - top
            y_base += delta
        elif bottom > inner_bottom:
            delta = bottom - inner_bottom
            y_base -= delta

        # Keep the subscript readable and away from the border, but do not let it
        # drive the vertical centering of the main "CO" run.
        if index_mode == "superscript":
            min_index_offset = font_size * 0.10
            max_index_offset = font_size * 0.34
            index_offset = float(max(min_index_offset, min(max_index_offset, font_size * float(params.get("co2_superscript_offset_scale", 0.22)))))
            subscript_y = y_base - index_offset
            sub_top = subscript_y - (sub_font_px * 0.60)
            if sub_top < inner_top:
                max_offset = max(min_index_offset, y_base - inner_top - (sub_font_px * 0.60))
                index_offset = float(max(min_index_offset, min(max_index_offset, max_offset)))
                subscript_y = y_base - index_offset
            sub_bottom = subscript_y + (sub_font_px * 0.35)
            if sub_bottom > inner_bottom:
                min_offset = y_base - inner_bottom + (sub_font_px * 0.35)
                index_offset = float(max(min_index_offset, min(max_index_offset, min_offset)))
                subscript_y = y_base - index_offset
        else:
            min_subscript_offset = font_size * 0.08
            max_subscript_offset = font_size * 0.24
            subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, subscript_offset)))
            subscript_y = y_base + subscript_offset
            sub_bottom = subscript_y + (sub_font_px * 0.35)
            if sub_bottom > inner_bottom:
                max_offset = inner_bottom - y_base - (sub_font_px * 0.35)
                subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, max_offset)))
                subscript_y = y_base + subscript_offset

            sub_top = subscript_y - (sub_font_px * 0.60)
            if sub_top < inner_top:
                min_offset = inner_top - y_base + (sub_font_px * 0.60)
                subscript_offset = float(max(min_subscript_offset, min(max_subscript_offset, min_offset)))
                subscript_y = y_base + subscript_offset

        return {
            "anchor_mode": anchor_mode,
            "index_mode": index_mode,
            "width_scale": width_scale,
            "font_size": font_size,
            "sub_scale": sub_scale,
            "sub_font_px": sub_font_px,
            "co_x": co_x,
            "y_base": y_base,
            "subscript_x": subscript_x,
            "subscript_y": subscript_y,
            "x1": x1,
            "x2": x2,
            "height": height,
        }

    @staticmethod
    def _apply_voc_label(params: dict) -> dict:
        params["draw_text"] = True
        params["text_mode"] = "voc"
        params["text_gray"] = int(round(params.get("stroke_gray", Action.LIGHT_CIRCLE_STROKE_GRAY)))
        params["voc_font_scale"] = float(params.get("voc_font_scale", 0.52 * Action.SEMANTIC_TEXT_BASE_SCALE))
        params["voc_dy"] = float(params.get("voc_dy", -0.01 * float(params.get("r", 0.0))))
        params["voc_weight"] = int(params.get("voc_weight", 600))
