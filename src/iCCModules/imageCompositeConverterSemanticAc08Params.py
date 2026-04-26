"""AC08 badge-parameter dispatch extracted from the converter monolith."""

from __future__ import annotations

from typing import Any


def makeAc08BadgeParamsImpl(
    w: int,
    h: int,
    name: str,
    img: Any | None,
    *,
    default_ac0870_params_fn,
    default_ac0811_params_fn,
    default_ac0810_params_fn,
    default_ac0812_params_fn,
    default_ac0813_params_fn,
    default_ac0814_params_fn,
    default_ac0881_params_fn,
    default_ac0882_params_fn,
    fit_ac0870_params_from_image_fn,
    fit_semantic_badge_from_image_fn,
    fit_ac0811_params_from_image_fn,
    fit_ac0810_params_from_image_fn,
    fit_ac0812_params_from_image_fn,
    fit_ac0813_params_from_image_fn,
    fit_ac0814_params_from_image_fn,
    apply_co2_label_fn,
    apply_voc_label_fn,
    tune_ac0831_co2_badge_fn,
    tune_ac0832_co2_badge_fn,
    tune_ac0833_co2_badge_fn,
    tune_ac0834_co2_badge_fn,
    tune_ac0835_voc_badge_fn,
    finalize_ac08_style_fn,
    enforce_left_arm_badge_geometry_fn,
) -> dict | None:
    """Build semantic AC08 badge params for defaults and image-based fitting."""
    if name == "AC0870":
        defaults = default_ac0870_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0870_params_from_image_fn(img, defaults))

    if name == "AC0800":
        scale = min(w, h) / 30.0 if min(w, h) > 0 else 1.0
        defaults = {
            "cx": 15.0 * scale,
            "cy": 15.0 * scale,
            "r": 10.8 * scale,
            "stroke_circle": 1.5 * scale,
            "fill_gray": 220,
            "stroke_gray": 152,
            "draw_text": False,
        }
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_semantic_badge_from_image_fn(img, defaults))

    if name == "AC0811":
        defaults = default_ac0811_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0811_params_from_image_fn(img, defaults))

    if name == "AC0810":
        defaults = default_ac0810_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0810_params_from_image_fn(img, defaults))

    if name == "AC0812":
        defaults = default_ac0812_params_fn(w, h)
        if img is None:
            return enforce_left_arm_badge_geometry_fn(finalize_ac08_style_fn(name, defaults), w, h)
        return enforce_left_arm_badge_geometry_fn(
            finalize_ac08_style_fn(name, fit_ac0812_params_from_image_fn(img, defaults)),
            w,
            h,
        )

    if name == "AC0813":
        defaults = default_ac0813_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0813_params_from_image_fn(img, defaults))

    if name == "AC0814":
        defaults = default_ac0814_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0814_params_from_image_fn(img, defaults))

    if name == "AC0881":
        defaults = default_ac0881_params_fn(w, h)
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_semantic_badge_from_image_fn(img, defaults))

    if name == "AC0882":
        defaults = default_ac0882_params_fn(w, h)
        if img is None:
            return enforce_left_arm_badge_geometry_fn(finalize_ac08_style_fn(name, defaults), w, h)
        return enforce_left_arm_badge_geometry_fn(
            finalize_ac08_style_fn(name, fit_semantic_badge_from_image_fn(img, defaults)),
            w,
            h,
        )

    if name == "AC0820":
        defaults = apply_co2_label_fn(default_ac0870_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, apply_co2_label_fn(fit_semantic_badge_from_image_fn(img, defaults)))

    if name == "AC0831":
        defaults = apply_co2_label_fn(default_ac0881_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, tune_ac0831_co2_badge_fn(defaults))
        return finalize_ac08_style_fn(
            name,
            tune_ac0831_co2_badge_fn(fit_ac0811_params_from_image_fn(img, defaults)),
        )

    if name == "AC0832":
        defaults = apply_co2_label_fn(default_ac0812_params_fn(w, h))
        if img is None:
            return enforce_left_arm_badge_geometry_fn(
                finalize_ac08_style_fn(name, tune_ac0832_co2_badge_fn(defaults)),
                w,
                h,
            )
        return enforce_left_arm_badge_geometry_fn(
            finalize_ac08_style_fn(
                name,
                tune_ac0832_co2_badge_fn(fit_ac0812_params_from_image_fn(img, defaults)),
            ),
            w,
            h,
        )

    if name == "AC0833":
        defaults = tune_ac0833_co2_badge_fn(apply_co2_label_fn(default_ac0813_params_fn(w, h)))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, tune_ac0833_co2_badge_fn(fit_ac0813_params_from_image_fn(img, defaults)))

    if name == "AC0834":
        defaults = apply_co2_label_fn(default_ac0814_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, tune_ac0834_co2_badge_fn(defaults, w, h))
        return finalize_ac08_style_fn(
            name,
            tune_ac0834_co2_badge_fn(
                fit_ac0814_params_from_image_fn(img, defaults),
                w,
                h,
            ),
        )

    if name == "AC0835":
        # AC0835 belongs to the right-arm VOC connector family.
        defaults = apply_voc_label_fn(default_ac0814_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, tune_ac0835_voc_badge_fn(defaults, w, h))
        return finalize_ac08_style_fn(
            name,
            tune_ac0835_voc_badge_fn(
                fit_ac0814_params_from_image_fn(img, defaults),
                w,
                h,
            ),
        )

    if name == "AC0836":
        defaults = apply_voc_label_fn(default_ac0881_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0811_params_from_image_fn(img, defaults))

    if name == "AC0837":
        defaults = apply_voc_label_fn(default_ac0812_params_fn(w, h))
        if img is None:
            return enforce_left_arm_badge_geometry_fn(finalize_ac08_style_fn(name, defaults), w, h)
        return enforce_left_arm_badge_geometry_fn(
            finalize_ac08_style_fn(name, fit_ac0812_params_from_image_fn(img, defaults)),
            w,
            h,
        )

    if name == "AC0838":
        # AC0838 mirrors AC0836 into the "vertical connector above circle"
        # geometry class (same family as AC0813/AC0833) while keeping VOC text.
        defaults = apply_voc_label_fn(default_ac0813_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0813_params_from_image_fn(img, defaults))

    if name == "AC0839":
        defaults = apply_voc_label_fn(default_ac0814_params_fn(w, h))
        if img is None:
            return finalize_ac08_style_fn(name, defaults)
        return finalize_ac08_style_fn(name, fit_ac0814_params_from_image_fn(img, defaults))

    if name == "AC0842":
        # AC0842 follows the left-arm connector geometry (same arm placement as AC0812).
        defaults = default_ac0812_params_fn(w, h)
        defaults["draw_text"] = True
        defaults["text_mode"] = "rf"
        defaults["label"] = "rF"
        defaults["text_gray"] = int(round(defaults.get("stroke_gray", defaults.get("text_gray", 98))))
        defaults["rf_font_scale"] = float(defaults.get("rf_font_scale", 0.58))
        defaults["rf_dy"] = float(defaults.get("rf_dy", -0.02 * float(defaults.get("r", 0.0))))
        defaults["rf_weight"] = int(defaults.get("rf_weight", 600))
        if img is None:
            return enforce_left_arm_badge_geometry_fn(finalize_ac08_style_fn(name, defaults), w, h)
        return enforce_left_arm_badge_geometry_fn(
            finalize_ac08_style_fn(name, fit_ac0812_params_from_image_fn(img, defaults)),
            w,
            h,
        )

    return None
