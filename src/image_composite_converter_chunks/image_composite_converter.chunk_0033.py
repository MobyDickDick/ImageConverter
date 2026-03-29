        return params

    @staticmethod
    def _tune_ac0832_co2_badge(params: dict) -> dict:
        """AC0832 has a compact circle; keep CO₂ comfortably inside the ring."""
        p = dict(params)
        r = float(p.get("r", 0.0))
        p["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        p["arm_stroke"] = Action.AC08_STROKE_WIDTH_PX
        p["stroke_circle"] = Action.AC08_STROKE_WIDTH_PX
        p["co2_font_scale"] = min(float(p.get("co2_font_scale", 0.82)), 0.74)
        p["co2_sub_font_scale"] = min(float(p.get("co2_sub_font_scale", 66.0)), 62.0)
        p["co2_index_mode"] = "superscript"
        p["co2_superscript_offset_scale"] = float(min(float(p.get("co2_superscript_offset_scale", 0.11)), 0.11))
        p["co2_dy"] = float(p.get("co2_dy", 0.0)) - (0.03 * r)
        p["text_gray"] = p["stroke_gray"]
        return p

    @staticmethod
    def _tune_ac0831_co2_badge(params: dict) -> dict:
        """Stabilize AC0831 text placement for vertically elongated CO² badges."""
        p = dict(params)
        r = float(p.get("r", 0.0))
        p["stroke_gray"] = 155
        p["fill_gray"] = 238
        p["text_gray"] = p["stroke_gray"]
        p["stroke_circle"] = Action.AC08_STROKE_WIDTH_PX
        p["stem_gray"] = p["stroke_gray"]
        # Vertical connector variants read closer to the source rasters when the
        # whole CO² cluster is centered as a unit instead of keeping only "CO"
        # centered. AC0831 follows the reference with a superscript 2 and a
        # slightly higher text position than the generic vertical CO₂ family.
        p["co2_anchor_mode"] = "cluster"
        p["co2_index_mode"] = "superscript"
        p["co2_optical_bias"] = float(p.get("co2_optical_bias", 0.08))
        p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.35))
        p["co2_font_scale"] = min(float(p.get("co2_font_scale", 0.82)), 0.74)
        p["co2_sub_font_scale"] = min(float(p.get("co2_sub_font_scale", 66.0)), 48.0)
        # Keep the raised "2" clearly detached from the "O" in AC0831_L and
        # sibling variants where JPEG antialiasing tends to visually merge both.
        p["co2_superscript_offset_scale"] = float(max(float(p.get("co2_superscript_offset_scale", 0.17)), 0.17))
        p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.19)), 0.19))
        min_dim = float(
            min(
                float(p.get("width", 0.0) or 0.0),
                float(p.get("height", 0.0) or 0.0),
            )
        )
        if min_dim <= 0.0:
            min_dim = max(1.0, r * 2.0)
        if 0.0 < min_dim <= 15.5:
            # Tiny vertical CO₂ badges compress the glyph cluster into a single
            # JPEG blob. Rendering them with the generic AC0831 scale makes the
            # label look too wide/high compared to the reference raster, so keep
            # the text slightly tighter while keeping the superscript readable.
            p["co2_font_scale"] = min(float(p.get("co2_font_scale", 0.74)), 0.74)
            p["co2_sub_font_scale"] = min(float(p.get("co2_sub_font_scale", 48.0)), 48.0)
            p["co2_optical_bias"] = max(float(p.get("co2_optical_bias", 0.10)), 0.10)
            p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.35))
            p["co2_superscript_offset_scale"] = float(max(float(p.get("co2_superscript_offset_scale", 0.17)), 0.17))
            p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.19)), 0.19))
        return p

    @staticmethod
    def _tune_ac0835_voc_badge(params: dict, w: int, h: int) -> dict:
        """Keep tiny AC0835 badges from rendering the VOC label too high."""
        p = dict(params)
        r = float(p.get("r", 0.0))
        p["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        p["text_gray"] = p["stroke_gray"]
        min_dim = float(min(max(0, w), max(0, h)))
        if 0.0 < min_dim <= 15.5:
            # The AC0835_S raster centers the VOC word slightly lower than the
            # generic AC0870-derived default. Preserve that optical bias up
            # front so the validator does not need to recover it from a
            # stagnating small-variant search.
            p["voc_dy"] = float(max(float(p.get("voc_dy", 0.0)), 0.13 * r))
        return p

    @staticmethod
    def _tune_ac0833_co2_badge(params: dict) -> dict:
        """Tune AC0833 CO² badges so the trailing index stays superscript."""
        p = Action._normalize_light_circle_colors(dict(params))
        p["co2_anchor_mode"] = str(p.get("co2_anchor_mode", "cluster"))
        p["co2_index_mode"] = "superscript"
        p["co2_superscript_offset_scale"] = float(max(float(p.get("co2_superscript_offset_scale", 0.16)), 0.16))
        p["co2_superscript_min_gap_scale"] = float(max(float(p.get("co2_superscript_min_gap_scale", 0.17)), 0.17))
        return p

    @staticmethod
    def _tune_ac0834_co2_badge(params: dict, w: int, h: int) -> dict:
        """Stabilize tiny AC0834 badges where fitting drifts the circle downward."""
        p = dict(params)
        p["stroke_gray"] = Action.LIGHT_CIRCLE_STROKE_GRAY
        p["text_gray"] = p["stroke_gray"]
        p["stroke_circle"] = Action.AC08_STROKE_WIDTH_PX
        p["arm_stroke"] = Action.AC08_STROKE_WIDTH_PX

        if min(w, h) <= 16:
            default_cy = float(h) / 2.0
