                name,
                Action._tune_ac0834_co2_badge(
                    Action._fit_ac0814_params_from_image(img, defaults),
                    w,
                    h,
                ),
            )

        if name == "AC0835":
            # AC0835 belongs to the right-arm VOC connector family.
            defaults = Action._apply_voc_label(Action._default_ac0814_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, Action._tune_ac0835_voc_badge(defaults, w, h))
            return Action._finalize_ac08_style(
                name,
                Action._tune_ac0835_voc_badge(
                    Action._fit_ac0814_params_from_image(img, defaults),
                    w,
                    h,
                ),
            )

        if name == "AC0836":
            defaults = Action._apply_voc_label(Action._default_ac0881_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0811_params_from_image(img, defaults))

        if name == "AC0837":
            defaults = Action._apply_voc_label(Action._default_ac0812_params(w, h))
            if img is None:
                return Action._enforce_left_arm_badge_geometry(Action._finalize_ac08_style(name, defaults), w, h)
            return Action._enforce_left_arm_badge_geometry(
                Action._finalize_ac08_style(name, Action._fit_ac0812_params_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0838":
            # AC0838 is part of the right-arm VOC family (same geometry class as
            # AC0814/AC0839), not the top-stem family.
            defaults = Action._apply_voc_label(Action._default_ac0814_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0814_params_from_image(img, defaults))

        if name == "AC0839":
            defaults = Action._apply_voc_label(Action._default_ac0814_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0814_params_from_image(img, defaults))

        return None

    @staticmethod
    def generate_badge_svg(w: int, h: int, p: dict) -> str:
        p = Action._align_stem_to_circle_center(dict(p))
        p = Action._quantize_badge_params(p, w, h)
        elements = [
            f'<svg width="{w}px" height="{h}px" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
        ]

        background_fill = p.get("background_fill")
        if background_fill:
            elements.append(
                f'  <rect x="0" y="0" width="{float(w):.4f}" height="{float(h):.4f}" fill="{background_fill}"/>'
            )

        if p.get("arm_enabled"):
            arm_x1 = float(Action._clip_scalar(float(p.get("arm_x1", 0.0)), 0.0, float(w)))
            arm_y1 = float(Action._clip_scalar(float(p.get("arm_y1", p.get("arm_y", 0.0))), 0.0, float(h)))
            arm_x2 = float(Action._clip_scalar(float(p.get("arm_x2", 0.0)), 0.0, float(w)))
            arm_y2 = float(Action._clip_scalar(float(p.get("arm_y2", p.get("arm_y", arm_y1))), 0.0, float(h)))
            arm_stroke = float(p["arm_stroke"])

            elements.append(
                (
                    f'  <line x1="{arm_x1:.4f}" y1="{arm_y1:.4f}" '
                    f'x2="{arm_x2:.4f}" y2="{arm_y2:.4f}" '
                    f'stroke="{Action.grayhex(p.get("stroke_gray", 152))}" '
                    f'stroke-width="{arm_stroke:.4f}" stroke-linecap="round"/>'
                )
            )

        if p.get("stem_enabled"):
            stem_x = float(Action._clip_scalar(float(p.get("stem_x", 0.0)), 0.0, float(w)))
            stem_top = float(Action._clip_scalar(float(p.get("stem_top", 0.0)), 0.0, float(h)))
            stem_width = max(0.0, min(float(p.get("stem_width", 0.0)), max(0.0, float(w) - stem_x)))
            stem_bottom = float(Action._clip_scalar(float(p.get("stem_bottom", 0.0)), stem_top, float(h)))
            elements.append(
                (
                    f'  <rect x="{stem_x:.4f}" y="{stem_top:.4f}" '
                    f'width="{stem_width:.4f}" height="{max(0.0, stem_bottom - stem_top):.4f}" '
                    f'fill="{Action.grayhex(p.get("stem_gray", p["stroke_gray"]))}"/>'
                )
            )

        if p.get("circle_enabled", True):
            elements.append(
                (
