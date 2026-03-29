            height = max(1.0, (y2 - y1) + 1.0)
            area = width * height
            density = float(pixel_count) / max(1.0, area)
            small_variant = bool(badge_params.get("ac08_small_variant_mode", False))
            if element == "circle":
                if Action._mask_supports_circle(mask):
                    return True
                if small_variant:
                    # `_S` AC08 crops frequently merge anti-aliased ring pixels into a
                    # compact blob. Keep a permissive geometric fallback so robust circle
                    # evidence from the local mask is not rejected only because contour
                    # circularity deteriorates at 15x25px scale.
                    aspect = width / max(1.0, height)
                    return (
                        0.58 <= aspect <= 1.55
                        and density >= 0.34
                        and pixel_count >= 10
                    )
                return False
            if element == "stem":
                ratio = height / max(1.0, width)
                connector_text_badge = str(badge_params.get("text_mode", "")).lower() in {"co2", "voc"}
                if small_variant or connector_text_badge:
                    return pixel_count >= 4 and ratio >= 1.30
                return pixel_count >= 5 and ratio >= 2.2
            if element == "arm":
                ratio = width / max(1.0, height)
                connector_text_badge = str(badge_params.get("text_mode", "")).lower() in {"co2", "voc"}
                if small_variant or connector_text_badge:
                    return pixel_count >= 4 and ratio >= 1.30
                return pixel_count >= 5 and ratio >= 2.2
            if element == "text":
                return pixel_count >= max(4, int(round(min(width, height) * 0.35))) and density >= 0.08
            return pixel_count >= 4

        connector_direction = str(badge_params.get("connector_family_direction", "")).lower()
        arm_is_vertical = bool(
            badge_params.get("arm_enabled", False)
            and abs(float(badge_params.get("arm_x2", 0.0)) - float(badge_params.get("arm_x1", 0.0)))
            <= abs(float(badge_params.get("arm_y2", 0.0)) - float(badge_params.get("arm_y1", 0.0)))
        )
        vertical_connector_family = bool(
            connector_direction == "vertical"
            or (
                expected.get("stem", False)
                and not expected.get("arm", False)
                and (
                    (bool(badge_params.get("stem_enabled", False)) and not bool(badge_params.get("arm_enabled", False)))
                    or arm_is_vertical
                )
            )
        )
        local_support = {
            "circle": _mask_supports_element(circle_mask, "circle"),
            "stem": bool(
                _mask_supports_element(stem_mask, "stem")
                or (
                    vertical_connector_family
                    and bool(badge_params.get("arm_enabled", False))
                    and _mask_supports_element(arm_mask, "stem")
                )
            ),
            "arm": bool(
                not vertical_connector_family
                and _mask_supports_element(arm_mask, "arm")
            ),
            "text": _mask_supports_element(text_mask, "text"),
        }
        allow_circle_mask_fallback = expected.get("circle", False) and not (
            expected.get("stem", False) or expected.get("arm", False) or expected.get("text", False)
        )
        connector_circle_mask_fallback = bool(
            expected.get("circle", False)
            and vertical_connector_family
            and local_support["circle"]
            and not local_support["arm"]
        )
        small_connector_circle_mask_fallback = bool(
            expected.get("circle", False)
            and bool(badge_params.get("ac08_small_variant_mode", False))
            and local_support["circle"]
            and (expected.get("stem", False) or expected.get("arm", False))
        )
        plain_circle_badge = bool(
            expected.get("circle", False)
            and not expected.get("stem", False)
            and not expected.get("arm", False)
            and not expected.get("text", False)
            and not bool(badge_params.get("stem_enabled", False))
            and not bool(badge_params.get("arm_enabled", False))
            and not bool(badge_params.get("draw_text", False))
        )
        require_circle_mask_confirmation = expected.get("circle", False) and not (
            allow_circle_mask_fallback or connector_circle_mask_fallback
        )
        suppress_structural_stem_for_horizontal_connector = bool(
            expected.get("arm", False)
            and not expected.get("stem", False)
            and local_support["arm"]
            and not local_support["stem"]
