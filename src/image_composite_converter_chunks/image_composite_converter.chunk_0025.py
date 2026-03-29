                p["co2_dy"] = float(max(float(p.get("co2_dy", 0.0)), 0.03 * template_r))
                p["co2_center_co_bias"] = float(min(float(p.get("co2_center_co_bias", -0.05)), -0.05))
            if _needs_large_circle_overflow_guard(p) and image_width > 0.0:
                # Generic large centered CO² rule: keep circle radius template-led
                # while enforcing the product constraint that the diameter stays
                # larger than half the badge width.
                #   2r > (w / 2)  =>  r > (w / 4)
                required_r = (image_width / 4.0) + 1e-3
                p["r"] = float(max(float(p.get("r", template_r)), template_r * 0.98, required_r))
                p["circle_radius_lower_bound_px"] = float(
                    max(float(p.get("circle_radius_lower_bound_px", 1.0)), required_r)
                )
        if p.get("circle_enabled", True):
            has_connector = bool(p.get("arm_enabled") or p.get("stem_enabled"))
            has_text = bool(p.get("draw_text", False))
            aspect_ratio = 1.0
            badge_w = float(p.get("badge_width", 0.0))
            badge_h = float(p.get("badge_height", 0.0))
            if badge_w <= 0.0 or badge_h <= 0.0:
                circle_diameter = max(1.0, float(p.get("r", 1.0)) * 2.0)
                extent_w = circle_diameter
                extent_h = circle_diameter
                if p.get("stem_enabled"):
                    stem_top = float(p.get("stem_top", float(p.get("cy", 0.0)) + float(p.get("r", 0.0))))
                    stem_bottom = float(p.get("stem_bottom", stem_top))
                    extent_h = max(extent_h, max(1.0, stem_bottom))
                if p.get("arm_enabled"):
                    arm_x1 = float(p.get("arm_x1", float(p.get("cx", 0.0)) - float(p.get("r", 0.0))))
                    arm_x2 = float(p.get("arm_x2", float(p.get("cx", 0.0)) + float(p.get("r", 0.0))))
                    arm_y1 = float(p.get("arm_y1", float(p.get("cy", 0.0))))
                    arm_y2 = float(p.get("arm_y2", float(p.get("cy", 0.0))))
                    extent_w = max(extent_w, abs(arm_x2 - arm_x1), max(abs(arm_x1), abs(arm_x2)))
                    extent_h = max(extent_h, abs(arm_y2 - arm_y1), max(abs(arm_y1), abs(arm_y2)))
                badge_w = extent_w
                badge_h = extent_h
            if badge_w > 0.0 and badge_h > 0.0:
                aspect_ratio = badge_w / badge_h

            # For all semantic AC08xx badges, keep a robust radius floor anchored
            # to the template geometry. This prevents degenerate late-stage fits
            # where noisy masks shrink circles far below their known base size.
            template_r = float(p.get("template_circle_radius", p.get("r", 1.0)))
            current_r = float(p.get("r", template_r))
            base_r = max(1.0, template_r, current_r)
            min_ratio = 0.88
            if has_text:
                # Text badges are especially sensitive to circle shrink because
                # the label scales relative to the interior diameter.
                min_ratio = 0.92 if symbol_name == "AC0820" else 0.90
            elif has_connector and (aspect_ratio >= 1.60 or aspect_ratio <= (1.0 / 1.60)):
                # Strongly elongated connector badges are vulnerable to the
                # circle-only mask under-estimating the ring and collapsing the
                # circle toward the connector. Keep them closer to the semantic
                # template while still allowing modest adaptation.
                min_ratio = 0.95
            p["min_circle_radius"] = float(max(float(p.get("min_circle_radius", 1.0)), base_r * min_ratio))

            # Plain centered badges should keep their circle optically centered.
            # Otherwise min-rect alignment may drift the ring into a corner,
            # which also makes CO/VOC labels look far too small.
            if not has_connector:
                p["lock_circle_cx"] = True
                p["lock_circle_cy"] = True

            # Connector-only and connector+text badges can both lose connector
            # extraction in noisy JPEGs. Without geometric anchors the circle
            # optimizer may collapse toward unrelated border blobs (for plain
            # symbols) or text blobs (for labeled symbols). Keep the center and
            # connector alignment locked to template semantics for all connector
            # families so rotations/reflections/scales remain stable.
            if has_connector:
                p["lock_circle_cx"] = True
                p["lock_circle_cy"] = True
                if p.get("stem_enabled"):
                    p["lock_stem_center_to_circle"] = True
                    p["stem_center_lock_max_offset"] = float(max(0.35, float(p.get("stroke_circle", 1.0)) * 0.6))
                    p["allow_stem_width_tuning"] = True
                    p["stem_width_tuning_px"] = 1.0
                if p.get("arm_enabled"):
                    p["lock_arm_center_to_circle"] = True

            geometry_reanchored_to_template = False
            if bool(p.get("lock_circle_cx", False)) and "template_circle_cx" in p:
                p["cx"] = float(p["template_circle_cx"])
                geometry_reanchored_to_template = True
            if bool(p.get("lock_circle_cy", False)) and "template_circle_cy" in p:
                p["cy"] = float(p["template_circle_cy"])
                geometry_reanchored_to_template = True
            if geometry_reanchored_to_template and p.get("circle_enabled", True):
                if p.get("stem_enabled"):
                    p = Action._align_stem_to_circle_center(p)
                if p.get("arm_enabled"):
                    Action._reanchor_arm_to_circle_edge(p, float(p.get("r", 0.0)))
        if p.get("stem_enabled"):
            Action._persist_connector_length_floor(p, "stem", default_ratio=0.65)
        if p.get("arm_enabled"):
            Action._persist_connector_length_floor(p, "arm", default_ratio=0.75)
        if str(p.get("text_mode", "")).lower() == "co2":
            min_dim = float(min(float(p.get("width", 0.0) or 0.0), float(p.get("height", 0.0) or 0.0)))
            if min_dim <= 0.0:
