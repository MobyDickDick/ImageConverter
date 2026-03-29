                # Fallback for call sites that only pass geometry parameters.
                min_dim = max(1.0, float(p.get("r", 1.0)) * 2.0)

            # Keep AC0820 variants tunable (bounded via *_min/*_max overrides).
            # Very small CO₂ badges from other AC08xx families (e.g. AC0833_S)
            # can exhibit the same undersizing behavior after anti-aliased fitting,
            # so unlock bounded tuning for tiny variants in general.
            tiny_co2_variant = min_dim <= 15.5
            p["lock_text_scale"] = not (symbol_name == "AC0820" or tiny_co2_variant)
            if tiny_co2_variant:
                base_scale = float(p.get("co2_font_scale", 0.82))
                p["co2_font_scale_min"] = float(max(0.74, base_scale * 0.90))
                p["co2_font_scale_max"] = float(min(1.18, base_scale * 1.25))
        if str(p.get("text_mode", "")).lower() == "voc":
            min_dim = float(min(float(p.get("width", 0.0) or 0.0), float(p.get("height", 0.0) or 0.0)))
            if min_dim <= 0.0:
                min_dim = max(1.0, float(p.get("r", 1.0)) * 2.0)
            if symbol_name == "AC0835":
                # AC0835 variants use a freer VOC fitting policy than the CO₂
                # families: keep text scaling unlocked and bias the medium+
                # badges toward a readable baseline.
                p["lock_text_scale"] = False
                if min_dim <= 15.5:
                    # AC0835_S tends to over-scale VOC during text bracketing,
                    # producing a visibly heavy label compared to the source icon.
                    # Keep the historical small-badge cap stable regardless of
                    # global baseline uplifts so regression bounds remain intact.
                    legacy_base_scale = 0.52
                    p.setdefault("voc_font_scale_min", float(max(0.58, legacy_base_scale * 0.90)))
                    p.setdefault("voc_font_scale_max", float(min(0.92, legacy_base_scale * 1.05)))
                else:
                    # Medium/Large variants can start too small; pin a minimum
                    # readable baseline while still allowing upward tuning.
                    p["voc_font_scale"] = float(max(float(p.get("voc_font_scale", 0.52)), 0.60))
                    p.setdefault("voc_font_scale_min", 0.60)
                    p.pop("voc_font_scale_max", None)
        p = Action._configure_ac08_small_variant_mode(name, p)
        preserve_plain_ring_geometry = symbol_name == "AC0800"
        preserved_plain_ring_keys = {
            key: p[key]
            for key in ("lock_circle_cx", "lock_circle_cy", "min_circle_radius", "max_circle_radius")
            if preserve_plain_ring_geometry and key in p
        }
        for key in (
            "lock_circle_cx",
            "lock_circle_cy",
            "lock_stem_center_to_circle",
            "lock_arm_center_to_circle",
            "lock_text_scale",
            "lock_colors",
            "min_circle_radius",
            "max_circle_radius",
            "co2_font_scale_min",
            "co2_font_scale_max",
            "voc_font_scale_min",
            "voc_font_scale_max",
            "fill_gray_min",
            "fill_gray_max",
            "stroke_gray_min",
            "stroke_gray_max",
            "stem_gray_min",
            "stem_gray_max",
            "text_gray_min",
            "text_gray_max",
            "arm_len_min",
            "arm_len_min_ratio",
            "connector_family_group",
            "connector_family_direction",
        ):
            p.pop(key, None)
        if preserve_plain_ring_geometry:
            p.update(preserved_plain_ring_keys)
            if "template_circle_cx" in p:
                p["cx"] = float(p["template_circle_cx"])
            if "template_circle_cy" in p:
                p["cy"] = float(p["template_circle_cy"])
            template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
            min_radius_ratio = 0.96
            if bool(p.get("ac08_small_variant_mode", False)):
                # AC0800_S is visually very sensitive to anti-aliased radius
                # shrinkage. Keep the small plain-ring variant at least at the
                # template radius so later validation rounds cannot undershoot
                # the original circle diameter.
                min_radius_ratio = 1.0
            # AC0800 plain rings should derive the radius floor strictly from
            # the template, not from an overgrown fitted radius estimate.
            p["min_circle_radius"] = float(max(1.0, template_r * min_radius_ratio))
            cx = float(p.get("cx", p.get("template_circle_cx", template_r)))
            cy = float(p.get("cy", p.get("template_circle_cy", template_r)))
            canvas_w = float(p.get("width", p.get("badge_width", 0.0)) or 0.0)
            canvas_h = float(p.get("height", p.get("badge_height", 0.0)) or 0.0)
            if canvas_w <= 0.0:
                canvas_w = max(float(cx * 2.0), template_r * 2.0)
            if canvas_h <= 0.0:
                canvas_h = max(float(cy * 2.0), template_r * 2.0)
            canvas_fit_r = max(1.0, min(cx, canvas_w - cx, cy, canvas_h - cy) - 0.5)
            if bool(p.get("ac08_small_variant_mode", False)):
                p["max_circle_radius"] = float(max(template_r, template_r * 1.15, canvas_fit_r))
            else:
                p["max_circle_radius"] = float(max(template_r, template_r * 1.15))
