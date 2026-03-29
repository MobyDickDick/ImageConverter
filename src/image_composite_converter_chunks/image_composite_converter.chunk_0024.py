            p["co2_dy"] = float(max(-0.06 * template_r, min(0.16 * template_r, float(p.get("co2_dy", 0.03 * template_r)))))
            p["co2_font_scale_min"] = float(max(float(p.get("co2_font_scale_min", base_scale)), max(0.84, base_scale * 0.92)))
            p["co2_font_scale_max"] = float(min(float(p.get("co2_font_scale_max", 1.12)), min(1.12, base_scale * 1.18)))
        elif text_mode == "voc":
            base_scale = float(p.get("voc_font_scale", 0.52))
            p["lock_text_scale"] = False
            p["voc_dy"] = float(max(-0.06 * template_r, min(0.08 * template_r, float(p.get("voc_dy", 0.0)))))
            if min_dim <= 15.5:
                p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", base_scale)), max(0.50, base_scale * 0.96)))
                p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 0.92)), min(0.92, max(base_scale, 0.52) * 1.05)))
            else:
                p["voc_font_scale"] = float(max(base_scale, 0.60))
                p["voc_font_scale_min"] = float(max(float(p.get("voc_font_scale_min", p["voc_font_scale"])), 0.60))
                p["voc_font_scale_max"] = float(min(float(p.get("voc_font_scale_max", 1.02)), 1.02))
        else:
            p["s"] = float(max(float(p.get("s", 0.0100)), 0.0100))
            Action._center_glyph_bbox(p)

        return p

    @staticmethod
    def _finalize_ac08_style(name: str, params: dict) -> dict:
        """Apply AC08xx palette/stroke conventions globally for semantic conversions."""
        canonical_name = str(name).upper()
        symbol_name = canonical_name.split("_", 1)[0]
        if not symbol_name.startswith("AC08"):
            return params
        p = Action._capture_canonical_badge_colors(Action._normalize_light_circle_colors(dict(params)))
        p["badge_symbol_name"] = symbol_name
        # During geometry fitting we intentionally keep auto-estimated colors.
        # Canonical palette values are re-applied once fitting converged.
        p = Action._normalize_ac08_line_widths(p)
        p["lock_colors"] = True
        p = Action._normalize_centered_co2_label(p)
        if symbol_name == "AC0831" and str(p.get("text_mode", "")).lower() == "co2":
            p["fill_gray"] = 238
            p["stroke_gray"] = 155
            p["text_gray"] = 155
            if p.get("stem_enabled"):
                p["stem_gray"] = 155
        if symbol_name == "AC0833" and str(p.get("text_mode", "")).lower() == "co2":
            p = Action._tune_ac0833_co2_badge(p)
        if symbol_name == "AC0820" and str(p.get("text_mode", "")).lower() == "co2":
            # AC0820 variants (L/M/S): keep CO² superscript rendering, but do
            # not force a centered anchor mode. The optimizer may keep center_co
            # or drift via co2_dx/co2_dy to best match the source glyph raster.
            p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "center_co"))
            # AC0820 references render CO² with a raised "2" (superscript),
            # including AC0820_L where a subscript drifts visually too low.
            p["co2_index_mode"] = "superscript"
            p["co2_superscript_offset_scale"] = float(min(float(p.get("co2_superscript_offset_scale", 0.16)), 0.18))
            # Keep the raised "2" detached from the trailing "O" in AC0820_M/S
            # where antialiasing can visually merge both glyphs.
            p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.16)), 0.16))
            p["co2_optical_bias"] = 0.125
            r = max(1.0, float(p.get("r", 1.0)))
            # Keep AC0820 text close to the cap-height used by centered path
            # glyph labels (e.g. single C) so the leading "C" is no longer
            # undersized compared to the original badge family.
            if r >= 10.0:
                p["co2_font_scale"] = 0.82
            elif r >= 6.0:
                p["co2_font_scale"] = 0.84
            else:
                p["co2_font_scale"] = 0.86
            # Keep AC0820_M/S adjustable in validation: the tiny CO run can still
            # be slightly undersized after geometric fitting, but we do not want
            # unconstrained growth that reintroduces prior over-scaling regressions.
            base_scale = float(p["co2_font_scale"])
            p["co2_font_scale_min"] = float(max(0.84, base_scale * 0.92))
            p["co2_font_scale_max"] = float(min(1.12, base_scale * 1.22))
            # AC0820 references use a slightly narrower CO² wordmark than the
            # generic Arial fallback. Apply a mild horizontal squeeze so the
            # reconstructed text width tracks the source more closely.
            if r >= 10.0:
                p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.90)), 0.90))
            elif r >= 6.0:
                p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.92)), 0.92))
            else:
                p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.94)), 0.94))
            p["co2_sub_font_scale"] = float(p.get("co2_sub_font_scale", 66.0))
            p["co2_subscript_offset_scale"] = 0.27
            template_r = float(p.get("template_circle_radius", r))
            # AC0820_L can otherwise collapse to a tiny ring in unconstrained
            # rounds. Keep the rendered radius close to the source template
            # without reintroducing global min/max guardrail metadata.
            min_radius_ratio = 1.0 if template_r >= 10.0 else 0.95
            p["r"] = float(max(float(p.get("r", template_r)), template_r * min_radius_ratio))
            image_width = float(p.get("width", p.get("badge_width", 0.0)) or 0.0)
            # General large-badge tuning (not variant-specific): for centered
            # CO² labels without connectors, a mildly tighter/lower baseline
            # produces better visual agreement across anti-aliased inputs.
            large_centered_co2 = (
                bool(p.get("circle_enabled", True))
                and not bool(p.get("arm_enabled") or p.get("stem_enabled"))
                and str(p.get("co2_anchor_mode", "center_co")).lower() == "center_co"
                and template_r >= 10.0
            )
            if large_centered_co2:
                p["co2_width_scale"] = float(min(float(p.get("co2_width_scale", 0.89)), 0.89))
