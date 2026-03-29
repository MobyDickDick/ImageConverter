                "stroke_gray": 152,
                "draw_text": False,
            }
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_semantic_badge_from_image(img, defaults))

        if name == "AC0811":
            defaults = Action._default_ac0811_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0811_params_from_image(img, defaults))

        if name == "AC0810":
            defaults = Action._default_ac0810_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0810_params_from_image(img, defaults))

        if name == "AC0812":
            defaults = Action._default_ac0812_params(w, h)
            if img is None:
                return Action._enforce_left_arm_badge_geometry(Action._finalize_ac08_style(name, defaults), w, h)
            return Action._enforce_left_arm_badge_geometry(
                Action._finalize_ac08_style(name, Action._fit_ac0812_params_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0813":
            defaults = Action._default_ac0813_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0813_params_from_image(img, defaults))

        if name == "AC0814":
            defaults = Action._default_ac0814_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_ac0814_params_from_image(img, defaults))

        if name == "AC0881":
            defaults = Action._default_ac0881_params(w, h)
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._fit_semantic_badge_from_image(img, defaults))

        if name == "AC0882":
            defaults = Action._default_ac0882_params(w, h)
            if img is None:
                return Action._enforce_left_arm_badge_geometry(Action._finalize_ac08_style(name, defaults), w, h)
            return Action._enforce_left_arm_badge_geometry(
                Action._finalize_ac08_style(name, Action._fit_semantic_badge_from_image(img, defaults)),
                w,
                h,
            )

        if name == "AC0820":
            defaults = Action._apply_co2_label(Action._default_ac0870_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._apply_co2_label(Action._fit_semantic_badge_from_image(img, defaults)))

        if name == "AC0831":
            defaults = Action._apply_co2_label(Action._default_ac0881_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, Action._tune_ac0831_co2_badge(defaults))
            return Action._finalize_ac08_style(
                name,
                Action._tune_ac0831_co2_badge(Action._fit_ac0811_params_from_image(img, defaults)),
            )

        if name == "AC0832":
            defaults = Action._apply_co2_label(Action._default_ac0812_params(w, h))
            if img is None:
                return Action._enforce_left_arm_badge_geometry(
                    Action._finalize_ac08_style(name, Action._tune_ac0832_co2_badge(defaults)),
                    w,
                    h,
                )
            return Action._enforce_left_arm_badge_geometry(
                Action._finalize_ac08_style(
                    name,
                    Action._tune_ac0832_co2_badge(Action._fit_ac0812_params_from_image(img, defaults)),
                ),
                w,
                h,
            )

        if name == "AC0833":
            defaults = Action._tune_ac0833_co2_badge(Action._apply_co2_label(Action._default_ac0813_params(w, h)))
            if img is None:
                return Action._finalize_ac08_style(name, defaults)
            return Action._finalize_ac08_style(name, Action._tune_ac0833_co2_badge(Action._fit_ac0813_params_from_image(img, defaults)))

        if name == "AC0834":
            defaults = Action._apply_co2_label(Action._default_ac0814_params(w, h))
            if img is None:
                return Action._finalize_ac08_style(name, Action._tune_ac0834_co2_badge(defaults, w, h))
            return Action._finalize_ac08_style(
