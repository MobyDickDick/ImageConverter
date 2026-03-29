        # optimizer steps push co2_font_scale too high for anti-aliased rasters.
        max_font_size = max(
            4.0,
            inner_diameter * float(params.get("co2_max_inner_diameter_ratio", 0.50)),
        )
        inner_padding = max(0.0, float(params.get("co2_inner_padding_px", 0.35)))
        clear_span = max(1.0, inner_diameter - (2.0 * inner_padding))
        sub_scale = float(params.get("co2_sub_font_scale", 66.0))
        sub_ratio = max(0.20, sub_scale / 100.0)
        # Estimate the whole CO₂ cluster width and derive a scale that keeps
        # a small edge margin whenever geometry allows it.
        cluster_factor = 1.04 + 0.03 + (0.62 * sub_ratio)
        width_limited_font = clear_span / max(0.001, cluster_factor)
        # Preserve vertical clear-space as well.
        height_limited_font = clear_span / max(0.95, 0.95 + (0.24 * sub_ratio) + (0.35 * sub_ratio))
        auto_font_size = min(width_limited_font, height_limited_font)
        font_size = min(max_font_size, max(requested_font_size, auto_font_size))
        # Tiny badges can otherwise rasterize the subscript into a barely visible
        # blob or drop it entirely. Keep a conservative minimum pixel height.
        sub_font_px = max(4.0, font_size * (sub_scale / 100.0))
        anchor_mode = str(params.get("co2_anchor_mode", "center_co")).lower()
        index_mode = str(params.get("co2_index_mode", "subscript")).lower()

        width_scale = float(params.get("co2_width_scale", 1.0))
        width_scale = float(max(0.78, min(1.12, width_scale)))
        symbol_hint = str(params.get("badge_symbol_name", "")).upper()
        if not symbol_hint:
            symbol_hint = str(params.get("variant_name", "")).upper().split("_", 1)[0]
        if symbol_hint == "AC0820":
            # Keep AC0820 variants consistently narrower even when later
            # optimization passes try to widen the default fallback font.
            if r >= 10.0:
                width_scale = min(width_scale, 0.90)
            elif r >= 6.0:
                width_scale = min(width_scale, 0.92)
            else:
                width_scale = min(width_scale, 0.94)

        co_width = (font_size * 1.04) * width_scale
        gap = font_size * 0.03
        if index_mode == "superscript":
            # Raised CO² labels need a wider horizontal separation so the "2"
            # stays visibly detached from the "O" in all AC08 conversions.
            superscript_min_gap = font_size * float(params.get("co2_superscript_min_gap_scale", 0.130))
            gap = max(gap, superscript_min_gap)
        sub_w = (sub_font_px * 0.62) * width_scale

        if anchor_mode in {"cluster", "co"}:
            # Legacy mode: center the whole CO₂ cluster.
            cluster_shift = (gap + sub_w) / 2.0
            co_x = (cx + float(params.get("co2_dx", 0.0))) - cluster_shift
            x1 = co_x - (co_width / 2.0)
            subscript_x = co_x + (co_width / 2.0) + gap
            x2 = subscript_x + sub_w
        else:
            # Default mode: keep the "CO" run as the dominant anchor and only shift
            # if geometry constraints require it.
            # Prioritize matching the main "CO" glyphs first; if space is tight, shrink
            # or tuck the subscript before shifting the dominant "CO" run.
            visual_sub_w = (sub_font_px * float(params.get("co2_subscript_visual_width_factor", 0.62))) * width_scale
            visual_cluster_shift = (gap + visual_sub_w) / 2.0
            center_co_bias = float(params.get("co2_center_co_bias", 0.0))
            co_x = (cx + float(params.get("co2_dx", 0.0))) + (visual_cluster_shift * center_co_bias)
            x1 = co_x - (co_width / 2.0)

            local_gap = gap
            local_sub_font_px = sub_font_px
            local_sub_w = sub_w
            subscript_x = co_x + (co_width / 2.0) + local_gap
            x2 = subscript_x + local_sub_w

            stroke = max(0.8, float(params.get("stroke_circle", 1.0)))
            inner_right = cx + max(1.0, r - stroke) - inner_padding
            inner_left = cx - max(1.0, r - stroke) + inner_padding

            overflow = x2 - inner_right
            if overflow > 0.0:
                # Step 1: reduce spacing before moving CO.
                min_gap = font_size * 0.005
                if index_mode == "superscript":
                    min_gap = max(
                        min_gap,
                        font_size * float(params.get("co2_superscript_min_gap_scale", 0.130)),
                    )
                shrink_gap = min(overflow, max(0.0, local_gap - min_gap))
                local_gap -= shrink_gap
                overflow -= shrink_gap

                # Step 2: reduce subscript size (keep readable floor) before moving CO.
                if overflow > 0.0:
                    min_sub_font_px = max(4.0, font_size * 0.42)
                    max_shrink_px = max(0.0, local_sub_font_px - min_sub_font_px)
                    shrink_px = min(max_shrink_px, overflow / 0.62)
                    local_sub_font_px -= shrink_px
                    local_sub_w = (local_sub_font_px * 0.62) * width_scale

                # Recompute geometry with adjusted ₂ attachment.
                sub_font_px = local_sub_font_px
                subscript_x = co_x + (co_width / 2.0) + local_gap
                x2 = subscript_x + local_sub_w
